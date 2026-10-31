"""API acceptance against a separate Docker stack. All user input is synthetic.

No browser automation and no real external model/platform calls are used here.
Run only with .local/acceptance.env and AGENT_PROVIDER=test.
"""
import base64
import io
import zipfile
import hashlib
import tempfile
import subprocess
import sys
import http.cookiejar
import json
import os
from pathlib import Path
import time
import struct
import zlib
import unittest
from urllib import request, error
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]
CONFIG=dict(line.split('=',1) for line in (ROOT/'.local/acceptance.env').read_text().splitlines() if line and not line.startswith('#'))
if CONFIG.get('COMPOSE_PROJECT_NAME')!='healthy-care-test' or CONFIG.get('AGENT_PROVIDER')!='test':
    raise RuntimeError('Acceptance tests require the isolated test stack.')
BASE='http://localhost:'+CONFIG['HTTP_PORT']

class Client:
    def __init__(self):
        self.cookies=http.cookiejar.CookieJar();self.opener=request.build_opener(request.ProxyHandler({}),request.HTTPCookieProcessor(self.cookies));self.csrf='';self.user=None
    def call(self,path,body=None,method=None,expected=200,headers=None,raw=False):
        h={'Origin':BASE};h.update(headers or {})
        if self.csrf:h['X-CSRF-Token']=self.csrf
        data=None
        if body is not None:
            data=body if isinstance(body,bytes) else json.dumps(body,ensure_ascii=False).encode()
            if not isinstance(body,bytes):h['Content-Type']='application/json'
        req=request.Request(BASE+path,data=data,method=method or ('POST' if body is not None else 'GET'),headers=h)
        try:
            with self.opener.open(req,timeout=30) as response:status=response.status;result=response.read()
        except error.HTTPError as exc:status=exc.code;result=exc.read()
        if status!=expected:raise AssertionError(f'{req.method} {path}: expected {expected}, received {status}: {result[:600].decode(errors="replace")}')
        return result if raw else json.loads(result)
    def register(self):
        self.user=self.call('/v1/auth/register',{'email':f'acceptance-{uuid4().hex}@example.test','password':'Acceptance-'+uuid4().hex})
        self.csrf=self.user['csrf'];return self
    def conversation(self):return self.call('/v1/health/conversation')
    def state(self):return self.call('/v1/health/state')
    def message(self,text,attachments=None,client_id=None):
        conv=self.conversation();return self.call(f'/v1/health/conversations/{conv["id"]}/messages',{'content':text,'attachments':attachments or [],'client_id':client_id or str(uuid4())},expected=202)
    def wait(self,run_id):
        for _ in range(120):
            value=self.call(f'/v1/health/runs/{run_id}')
            if value['status'] in ('succeeded','waiting_user','failed','cancelled'):
                if value['status']=='failed':raise AssertionError(f'Agent run failed: {value["error_code"]}')
                return value
            time.sleep(.15)
        raise AssertionError('Run did not reach a terminal state')
    def propose(self,text,kind):
        run=self.message(text);self.wait(run['run_id'])
        return next(a for a in self.state()['pending_actions'] if a['kind']==kind)
    def confirm(self,action,expected=200):return self.call(f'/v1/health/actions/{action["id"]}/confirm',{},expected=expected)
    def do(self,text,kind):a=self.propose(text,kind);self.confirm(a);return a
    def upload(self):
        def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
        image=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',2,2,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\x00'+b'\x80\xb0\x80'*2)*2))+chunk(b'IEND',b'')
        boundary='SyntheticBoundary'+uuid4().hex
        body=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="synthetic.png"\r\nContent-Type: image/png\r\n\r\n'.encode()+image+f'\r\n--{boundary}--\r\n'.encode())
        return self.call('/v1/health/attachments',body,expected=201,headers={'Content-Type':f'multipart/form-data; boundary={boundary}'})

class Acceptance(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.alice=Client().register();cls.bob=Client().register();cls.research=Client()
        r=cls.research.call('/v1/auth/login',{'email':CONFIG['RESEARCH_EMAIL'],'password':CONFIG['RESEARCH_PASSWORD']});cls.research.csrf=r['csrf']
        status=cls.alice.call('/v1/system/status')
        assert status['test_provider'] is True,'Refusing to run with a real model provider'

    def test_01_identity_and_workspace_isolation(self):
        Client().call('/v1/health/state',expected=401)
        self.alice.call('/v1/research/overview',expected=403)
        self.research.call('/v1/health/state',expected=403)
        self.alice.call('/v1/auth/register',{'email':'bad@example.test','password':'SyntheticPassword2026','role':'researcher'},expected=400)
        old=self.alice.csrf;self.alice.csrf='incorrect';self.alice.call('/v1/auth/logout',{},expected=403);self.alice.csrf=old
        self.assertEqual(self.alice.call('/v1/health/daily-summary')['mode'],'new')
        self.assertEqual(self.alice.state()['episodes'],[])
        unknown=Client().register();unknown.do('喉咙不舒服，开始时间未知（合成输入）','create_episode')
        self.assertFalse(unknown.state()['episodes'][0]['onset_known'],'Record creation must not imply known symptom onset')

    def test_02_message_confirmation_and_idempotency(self):
        run=self.alice.message('这两天喉咙不舒服（自动验收合成输入）');self.alice.wait(run['run_id'])
        metrics=self.alice.call('/v1/health/runs/'+run['run_id'])
        measured=[e for e in metrics['telemetry'] if e['kind']=='node_duration']
        self.assertEqual({e['node'] for e in measured},{'context','triage','model','validate','confirmation'})
        self.assertTrue(all(e['duration_ms']>=0 for e in measured))
        self.assertEqual(next(e for e in measured if e['node']=='confirmation')['status'],'waiting_user')
        attempt=next(e for e in metrics['telemetry'] if e['kind']=='attempt')
        self.assertIsNone(attempt['model_usage']['total_tokens'])
        self.assertIsNone(attempt['model_usage']['cost']['amount'])
        assistant=next(m for m in self.alice.conversation()['messages'] if m['role']=='assistant' and m['metadata'].get('run_id')==run['run_id'])
        self.assertEqual(assistant['metadata']['runtime_metrics']['duration_ms'],attempt['duration_ms'])
        self.assertEqual(self.alice.state()['episodes'],[],'An Agent proposal must not write a fact before confirmation')
        action=next(a for a in self.alice.state()['pending_actions'] if a['kind']=='create_episode')
        self.bob.call(f'/v1/health/actions/{action["id"]}/confirm',{},expected=404)
        self.alice.confirm(action);self.assertTrue(self.alice.confirm(action)['replayed'])
        self.assertEqual(len(self.alice.state()['episodes']),1)
        cid=str(uuid4());text='只是回顾这段对话'
        first=self.alice.message(text,client_id=cid);second=self.alice.message(text,client_id=cid)
        self.assertEqual(first['run_id'],second['run_id']);self.alice.wait(first['run_id'])
        conv=self.alice.conversation()['id']
        self.alice.call(f'/v1/health/conversations/{conv}/messages',{'content':'different','attachments':[],'client_id':cid},expected=409)
        self.bob.call(f'/v1/health/runs/{run["run_id"]}',expected=404)

    def test_03_followup_missing_score_and_version_conflict(self):
        self.alice.do('今天没有变化，没用药','checkin')
        obs=self.alice.state()['observations'];self.assertEqual(len(obs),1);self.assertNotIn('score',obs[0]['data'])
        first=self.alice.propose('今天3分','checkin')
        run=self.alice.message('今天4分');self.alice.wait(run['run_id'])
        actions=[a for a in self.alice.state()['pending_actions'] if a['kind']=='checkin'];second=next(a for a in actions if a['id']!=first['id'])
        self.alice.confirm(first);self.alice.confirm(second,expected=409)
        self.alice.call(f'/v1/health/actions/{second["id"]}/reject',{})
        obs=self.alice.state()['observations'];self.assertEqual(len(obs),1);self.assertEqual(obs[0]['data']['score'],3);self.assertGreaterEqual(obs[0]['version'],2)

    def test_04_images_and_private_access(self):
        attachment=self.alice.upload();self.assertTrue(attachment['metadata_removed'])
        self.assertGreater(len(self.alice.call('/v1/health/attachments/'+attachment['id'],raw=True)),0)
        self.bob.call('/v1/health/attachments/'+attachment['id'],expected=404)
        run=self.alice.message('这是自动验收图片，请先询问图片上下文',[attachment['id']]);self.alice.wait(run['run_id'])
        self.bob.call(f'/v1/health/conversations/{self.bob.conversation()["id"]}/messages',{'content':'test','attachments':[attachment['id']],'client_id':str(uuid4())},expected=404)

    def test_05_medication_reminder_and_archive(self):
        self.alice.do('记录用药产品A，成分甲（自动验收合成产品）','record_medication')
        original=self.alice.state()['medications'][0]
        self.alice.do('更正用药：我实际未用（合成更正输入）','update_medication')
        changed=self.alice.state()['medications'][0]
        self.assertEqual(changed['id'],original['id']);self.assertEqual(changed['data']['state'],'not_used');self.assertEqual(changed['version'],original['version']+1)
        self.assertEqual(len(self.alice.state()['medications']),1)
        self.alice.do('每天提醒我记录今天情况','create_task')
        self.assertEqual(len(self.alice.state()['tasks']),1)
        self.alice.do('暂停这个提醒','update_task');self.assertEqual(self.alice.state()['tasks'][0]['status'],'paused')
        self.alice.do('已经好了，结束跟进','archive_episode')
        daily=self.alice.call('/v1/health/daily-summary');self.assertEqual(daily['mode'],'history');self.assertEqual(daily['active'],[])

    def test_06_research_reference_filters_and_import(self):
        full=self.research.call('/v1/research/overview');self.assertEqual(full['metrics']['expected_patient_days'],324);self.assertEqual(full['metrics']['completeness_pct'],82.4)
        skin=self.research.call('/v1/research/overview?topic=%E7%9A%AE%E8%82%A4%E4%B8%8D%E9%80%82&window_days=3');self.assertEqual(skin['metrics']['expected_patient_days'],24);self.assertEqual(skin['metrics']['completeness_pct'],87.5)
        definition={'source':'synthetic','topic':'all','category':'all','window_days':7}
        snapshot=self.research.call('/v1/research/snapshots',definition,expected=201)
        run=self.research.call('/v1/research/runs',{'snapshot_id':snapshot['id'],'platform':'local-reference'},expected=202)
        result=None
        for _ in range(80):
            result=self.research.call('/v1/research/runs/'+run['id'])
            if result['status']=='completed':break
            time.sleep(.15)
        self.assertEqual(result['status'],'completed');self.assertEqual(result['result']['metrics']['medication_candidate_count'],32)
        report=result['result'];report['metrics']['participants']=999
        self.research.call('/v1/research/runs/'+run['id']+'/import',report,expected=400)
        report['metrics']['participants']=48
        imported=self.research.call('/v1/research/runs/'+run['id']+'/import',report)
        self.assertEqual(imported['origin_verification'],'imported-not-platform-authenticated')
        exported=self.research.call('/v1/research/export?format=csv',raw=True).decode()
        bundle=self.research.call('/v1/research/snapshots/'+snapshot['id']+'/bundle',raw=True)
        with tempfile.TemporaryDirectory() as directory:
            with zipfile.ZipFile(io.BytesIO(bundle)) as archive:archive.extractall(directory)
            folder=Path(directory);manifest=json.loads((folder/'manifest.json').read_text())
            self.assertEqual(hashlib.sha256((folder/'run_analysis.py').read_bytes()).hexdigest(),manifest['code_sha256'])
            self.assertEqual(manifest['snapshot_id'],snapshot['id']);self.assertTrue(manifest['cutoff_at']);self.assertIn('knowledge_version',manifest);self.assertEqual(manifest['analysis_window'],7);self.assertEqual(manifest['random_seed'],0)
            subprocess.run([sys.executable,str(folder/'run_analysis.py'),str(folder/'health-research-input.json'),'--out',str(folder/'output')],check=True,capture_output=True)
            independent=json.loads((folder/'output/report.json').read_text())
            self.assertEqual(independent['input_sha256'],report['input_sha256'])
            self.assertEqual(independent['metrics']['completeness_pct'],report['metrics']['completeness_pct'])
        self.assertIn('medication_state',exported);self.assertNotIn('password',exported);self.assertNotIn('@example.test',exported)
        external=self.research.call('/v1/research/runs',{'snapshot_id':snapshot['id'],'platform':'SciencePal'},expected=202)
        for _ in range(80):
            external_state=self.research.call('/v1/research/runs/'+external['id'])
            if external_state['status']=='failed':break
            time.sleep(.15)
        self.assertEqual(external_state['status'],'failed');self.assertEqual(external_state['error_code'],'sciencepal_not_configured')

    def test_07_consent_revocation_invalidates_snapshot(self):
        participants=[self.alice,self.bob]+[Client().register() for _ in range(3)]
        for client in participants:
            if not client.state()['episodes']:client.do('喉咙不舒服（合成研究样例）','create_episode')
            client.do('同意健康记录研究授权','set_consent')
        definition={'source':'consented','topic':'all','category':'all','window_days':7}
        snapshot=self.research.call('/v1/research/snapshots',definition,expected=201)
        self.research.call('/v1/research/snapshots/'+snapshot['id']+'/package')
        self.bob.do('撤回健康记录研究授权','set_consent')
        self.research.call('/v1/research/snapshots/'+snapshot['id']+'/package',expected=403)
        self.assertTrue(self.research.call('/v1/research/overview?source=consented')['suppressed'])

    def test_08_concurrent_messages_and_sse_replay(self):
        from concurrent.futures import ThreadPoolExecutor
        conv=self.bob.conversation()['id']
        messages=[{'content':f'合成并发对话{n}','attachments':[],'client_id':str(uuid4())} for n in range(2)]
        # Independent HTTP clients share only the session cookie, not a live connection.
        def send(body):
            client=Client();client.cookies=self.bob.cookies;client.opener=request.build_opener(request.ProxyHandler({}),request.HTTPCookieProcessor(client.cookies));client.csrf=self.bob.csrf
            return client.call(f'/v1/health/conversations/{conv}/messages',body,expected=202)
        with ThreadPoolExecutor(max_workers=2) as pool:runs=list(pool.map(send,messages))
        for run in runs:
            self.bob.wait(run['run_id'])
            events=self.bob.call(f'/v1/health/runs/{run["run_id"]}/events',raw=True).decode()
            self.assertIn('event: end',events);self.assertIn('event: delta',events)
            ids=[int(line[4:]) for line in events.splitlines() if line.startswith('id: ')]
            self.assertEqual(ids,sorted(set(ids)))
            resumed=self.bob.call(f'/v1/health/runs/{run["run_id"]}/events',headers={'Last-Event-ID':str(ids[-1])},raw=True).decode()
            self.assertNotIn('event: delta',resumed)

    def test_09_delete_health_records_and_replay(self):
        attachment=self.alice.upload()
        action=self.alice.propose('删除所有健康记录，请先说明范围','delete_records')
        self.alice.confirm(action)
        self.assertTrue(self.alice.confirm(action)['replayed'])
        state=self.alice.state();self.assertEqual(state['episodes'],[]);self.assertEqual(state['medications'],[]);self.assertEqual(state['tasks'],[])
        self.alice.call('/v1/health/attachments/'+attachment['id'],expected=404)
        new_file=self.alice.upload();time.sleep(1)
        self.assertGreater(len(self.alice.call('/v1/health/attachments/'+new_file['id'],raw=True)),0,'Cleanup must not remove files uploaded after deletion')

if __name__=='__main__':unittest.main(verbosity=2)
