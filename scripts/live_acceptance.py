#!/usr/bin/env python3
"""Opt-in real-provider technical acceptance, using synthetic inputs only.

Never imports private health data or substitutes a fake provider. Requires
configured credentials and a running deployment; may consume provider credits.
This is not a clinical effectiveness or professional content review.
"""
import argparse
import http.cookiejar
import json
from pathlib import Path
import secrets
import struct
import time
import zlib
from urllib import request, error
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1]

class Client:
    def __init__(self,origin):
        self.origin=origin;self.csrf='';self.last_run_id=None
        self.http=request.build_opener(request.ProxyHandler({}),request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
    def call(self,path,body=None):
        headers={'Origin':self.origin,'X-CSRF-Token':self.csrf}
        if body is not None:headers['Content-Type']='application/json'
        data=None if body is None else json.dumps(body,ensure_ascii=False).encode()
        try:
            with self.http.open(request.Request(self.origin+path,data=data,headers=headers),timeout=120) as response:return json.load(response)
        except error.HTTPError as exc:
            try:code=json.load(exc).get('error','unknown')
            except (ValueError,AttributeError):code='unreadable_error'
            raise RuntimeError(f'{path}: HTTP {exc.code}, error={code}') from None
    def register(self):
        value=self.call('/v1/auth/register',{'email':f'live-synthetic-{uuid4().hex}@example.test','password':secrets.token_urlsafe(24)})
        self.csrf=value['csrf'];return self
    def upload_synthetic_image(self):
        def chunk(kind,data):return struct.pack('!I',len(data))+kind+data+struct.pack('!I',zlib.crc32(kind+data)&0xffffffff)
        image=b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('!IIBBBBB',16,16,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\x00'+b'\x80\xb0\x80'*16)*16))+chunk(b'IEND',b'')
        boundary='Synthetic-'+uuid4().hex
        data=(f'--{boundary}\r\nContent-Disposition: form-data; name="file"; filename="synthetic.png"\r\nContent-Type: image/png\r\n\r\n'.encode()+image+f'\r\n--{boundary}--\r\n'.encode())
        headers={'Origin':self.origin,'X-CSRF-Token':self.csrf,'Content-Type':'multipart/form-data; boundary='+boundary}
        with self.http.open(request.Request(self.origin+'/v1/health/attachments',data=data,headers=headers),timeout=120) as response:return json.load(response)['id']
    def message(self,text,attachments=None):
        conv=self.call('/v1/health/conversation')
        run=self.call(f'/v1/health/conversations/{conv["id"]}/messages',{'content':text,'attachments':attachments or [],'client_id':str(uuid4())})
        self.last_run_id=run['run_id']
        end=time.monotonic()+150
        while time.monotonic()<end:
            value=self.call('/v1/health/runs/'+run['run_id'])
            if value['status'] in ('succeeded','waiting_user'):
                conversation=self.call('/v1/health/conversation')
                replies=[m for m in conversation['messages'] if m['role']=='assistant' and m['metadata'].get('run_id')==run['run_id']]
                assert replies and replies[-1]['metadata']['provider']=='openai_compatible'
                return {'run_id':run['run_id'],'status':value['status'],'sources':replies[-1]['metadata'].get('sources',[]),'model_config':replies[-1]['metadata'].get('model_config',{}),'reply':replies[-1]['content'],'actions':replies[-1]['metadata'].get('actions',[]),'urgency':replies[-1]['metadata'].get('urgency'),'telemetry':value.get('telemetry',[])}
            if value['status'] in ('failed','cancelled'):raise RuntimeError('Live model run failed: '+str(value.get('error_code')))
            time.sleep(.5)
        raise TimeoutError('Live model run timed out')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--synthetic-only',action='store_true',required=True);parser.add_argument('--only',choices=('model','sciencepal','both'),default='both');parser.add_argument('--env-file',type=Path,default=ROOT/'.env');parser.add_argument('--output',type=Path,default=ROOT/'.local/live-acceptance.json')
    args=parser.parse_args();cfg=dict(line.split('=',1) for line in args.env_file.read_text().splitlines() if line and not line.startswith('#'))
    want_model=args.only in ('model','both');want_platform=args.only in ('sciencepal','both')
    if want_model and (cfg.get('AGENT_PROVIDER')!='openai_compatible' or not cfg.get('MODEL_API_KEY') or not cfg.get('MODEL_NAME')):raise SystemExit('Blocked: configure the real model locally first. No request sent.')
    if want_platform and (not cfg.get('SCIENCEPAL_API_KEY') or not cfg.get('SCIENCEPAL_AGENT_ID')):raise SystemExit('Blocked: configure SciencePal locally first. No request sent.')
    origin=cfg.get('APP_ORIGIN','http://localhost:8780').rstrip('/')
    report={'schema_version':1,'started_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'data_origin':'synthetic','clinical_validation':False,'model_runs':[]}
    output=args.output;output.parent.mkdir(parents=True,exist_ok=True)
    output.touch(mode=0o600,exist_ok=True);output.chmod(0o600)
    try:
        if want_model:
            for scenario in ['成年合成样例：28岁，鼻塞两天，没有呼吸困难，想记录变化。','成年合成样例：皮肤有点痒两天，想了解需要补充哪些情况。','成年合成样例：鼻眼发痒一天，近期接触环境有变化，想整理信息。','成年合成样例：肚子不舒服一天，想先整理实际感受和观察重点。','成年合成样例：轻微头痛一天，想记录持续时间和活动影响。']:
                client=Client(origin).register();status=client.call('/v1/system/status')
                assert status['model_configured'] and not status['test_provider']
                report['model_runs'].append(client.message(scenario));output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
            report['model_technical_checks']='passed'
            vision=Client(origin).register()
            report['vision_run']=vision.message('这是一张合成测试色块。请描述可见内容，不作任何医学判断。',[vision.upload_synthetic_image()])
        if want_platform:
            researcher=Client(origin);identity=researcher.call('/v1/auth/login',{'email':cfg['RESEARCH_EMAIL'],'password':cfg['RESEARCH_PASSWORD']});researcher.csrf=identity['csrf']
            snapshot=researcher.call('/v1/research/snapshots',{'source':'synthetic','topic':'all','category':'all','window_days':7})
            run=researcher.call('/v1/research/runs',{'snapshot_id':snapshot['id'],'platform':'SciencePal'})
            report['sciencepal_run_id']=run['id'];output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
            deadline=time.monotonic()+900
            while time.monotonic()<deadline:
                result=researcher.call('/v1/research/runs/'+run['id'])
                if result['status']=='completed':
                    assert result['result'].get('origin_verification')=='api-fetched-artifact'
                    report['sciencepal']={'status':'passed','external_run_id':result['external_run_id'],'input_sha256':result['result']['input_sha256'],'artifact_verification':'api-fetched-artifact'};break
                if result['status'] in ('failed','external_unknown','external_asked','awaiting_import','invalidated'):
                    raise RuntimeError('SciencePal needs attention: '+result['status'])
                time.sleep(3)
            else:raise TimeoutError('SciencePal is still running; inspect the retained task before any new initiation.')
        report['technical_status']='passed'
    except Exception as exc:
        report['technical_status']='failed';report['error_type']=type(exc).__name__;raise
    finally:
        output.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');output.chmod(0o600)
    print('Real-provider technical checks passed on synthetic data. Professional content and clinical evaluation are separate.')

if __name__=='__main__':main()
