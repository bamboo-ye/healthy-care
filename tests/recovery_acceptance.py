"""Durability, cache-loss, checkpoint restart and clean restore acceptance.

Runs against explicitly disposable healthy-care-test with synthetic inputs only.
"""
import importlib.util
import hashlib
import hmac
import json
import os
from pathlib import Path
import subprocess
import sys
import time
from urllib import error
from uuid import uuid4
from api_acceptance import Client, ROOT, CONFIG

BASE=['docker','compose','--env-file',str(ROOT/'.local/acceptance.env'),'-p','healthy-care-test']
def compose(*args,**kwargs):return subprocess.run(BASE+list(args),cwd=ROOT,check=True,**kwargs)
def sql(query,project='healthy-care-test'):
    return subprocess.run(['docker','compose','--env-file',str(ROOT/'.local/acceptance.env'),'-p',project,'exec','-T','postgres','psql','-U','hc_owner','-d','healthycare','-At','-v','ON_ERROR_STOP=1','-c',query],cwd=ROOT,check=True,capture_output=True,text=True).stdout.strip()
def eventually(fn,timeout=40):
    end=time.monotonic()+timeout;last=None
    while time.monotonic()<end:
        try:
            result=fn()
            if result:return result
        except (AssertionError,error.URLError,ConnectionError) as exc:last=exc
        time.sleep(.3)
    raise AssertionError('Recovery condition timed out') from last

def main():
    client=Client().register()
    assert client.call('/v1/system/status')['test_provider']
    compose('stop','worker',stdout=subprocess.DEVNULL)
    try:
        queued=client.message('恢复验收：喉咙不舒服（合成输入）')
        assert client.call('/v1/health/runs/'+queued['run_id'])['status']=='queued'
    finally:compose('start','worker',stdout=subprocess.DEVNULL)
    client.wait(queued['run_id'])
    action=next(a for a in client.state()['pending_actions'] if a['kind']=='create_episode')
    assert int(sql(f"SELECT count(*) FROM agent.checkpoints WHERE thread_id='{queued['run_id']}'"))>0
    compose('restart','agent-runtime',stdout=subprocess.DEVNULL)
    eventually(lambda:client.call('/v1/system/status')['agent_available'])
    client.confirm(action)
    eventually(lambda:client.call('/v1/health/runs/'+queued['run_id'])['status']=='succeeded')
    assert len(client.state()['episodes'])==1
    print('PASS: queued work and LangGraph interrupt survive worker/runtime restarts')

    compose('stop','redis',stdout=subprocess.DEVNULL)
    try:
        assert len(client.state()['episodes'])==1
        client.wait(client.message('今天2分，记不清用药（缓存失效合成输入）')['run_id'])
        other=Client();reply=other.call('/v1/auth/login',{'email':CONFIG['RESEARCH_EMAIL'],'password':CONFIG['RESEARCH_PASSWORD']});assert reply['role']=='researcher'
    finally:compose('start','redis',stdout=subprocess.DEVNULL)
    print('PASS: cache loss preserves records, model context and authentication')

    before=client.state()
    compose('restart','postgres',stdout=subprocess.DEVNULL)
    eventually(lambda:len(client.state()['episodes'])==len(before['episodes']))
    print('PASS: PostgreSQL restart reconnects without losing confirmed records')

    image=client.upload();raw=client.call('/v1/health/attachments/'+image['id'],raw=True)
    image_run=client.message('内部图文传输验收（合成图片）',[image['id']]);client.wait(image_run['run_id'])
    expires=str(int(time.time())+120)
    token=expires+'.'+hmac.new(CONFIG['RUN_SIGNING_KEY'].encode(),(image_run['run_id']+':'+expires).encode(),hashlib.sha256).hexdigest()
    program="""import json,os,sys,urllib.request,urllib.error
value=json.load(sys.stdin)
url='http://api:8080/internal/runs/'+value['run']+'/attachments/'+value['image']
def fetch(token):
 req=urllib.request.Request(url,headers={'Authorization':'Bearer '+os.environ['INTERNAL_TOKEN'],'X-Run-Access':token})
 try:
  with urllib.request.urlopen(req) as response:return response.status,json.load(response)
 except urllib.error.HTTPError as exc:return exc.code,{}
status,result=fetch(value['token']);assert status==200 and result['data_url'].startswith('data:image/png;base64,')
assert fetch('invalid')[0]==403
print('PASS: real private image transport enforces the signed run scope')
"""
    compose('exec','-T','agent-runtime','python','-c',program,input=json.dumps({'run':image_run['run_id'],'image':image['id'],'token':token}),text=True)
    counts=sql('SELECT (SELECT count(*) FROM users),(SELECT count(*) FROM episodes),(SELECT count(*) FROM agent.checkpoints);')
    sys.path.insert(0,str(ROOT/'scripts'))
    from backup import run_backup
    from restore import restore
    suffix=uuid4().hex[:10];target=ROOT/'.local/backups'/('acceptance-'+suffix)
    run_backup(ROOT/'.local/acceptance.env',target)
    project='healthy-care-restore-'+suffix
    try:
        restore(ROOT/'.local/acceptance.env',target,project)
        assert sql('SELECT (SELECT count(*) FROM users),(SELECT count(*) FROM episodes),(SELECT count(*) FROM agent.checkpoints);',project)==counts
        # Read the restored private file from the restore-only volume using the same nonroot app image.
        command=['docker','compose','--env-file',str(ROOT/'.local/acceptance.env'),'-p',project,'run','--rm','--no-deps','-T','--entrypoint','cat','api',f'/data/files/{client.user["id"]}/{image["id"]}']
        restored=subprocess.run(command,cwd=ROOT,check=True,capture_output=True).stdout
        assert restored==raw
        print('PASS: fresh initialization, database/checkpoints and private images restore exactly')
    finally:
        # Only the randomly named, explicitly disposable restore environment is removed.
        subprocess.run(['docker','compose','--env-file',str(ROOT/'.local/acceptance.env'),'-p',project,'down','-v'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    eventually(lambda:client.state()['episodes'])
    conversation=client.conversation()['id']
    client.do('删除所有健康记录（恢复验收产生的合成数据）','delete_records')
    eventually(lambda:sql(f"SELECT count(*) FROM deletion_jobs WHERE user_id='{client.user['id']}' AND status='completed'")=='1')
    assert sql(f"SELECT count(*) FROM agent.run_threads WHERE conversation_id='{conversation}'")=='0'
    assert sql(f"SELECT count(*) FROM agent.checkpoints WHERE thread_id='{image_run['run_id']}'")=='0'
    print('PASS: confirmed deletion clears the durable Agent checkpoint and thread mapping')
    deleting=Client().register();deleting.do('喉咙不舒服（并发删除合成验收）','create_episode')
    deletion=deleting.propose('删除所有健康记录（合成删除草案）','delete_records')
    in_flight=deleting.message('延迟验收：测试删除时仍在执行的运行')
    eventually(lambda:deleting.call('/v1/health/runs/'+in_flight['run_id'])['status']=='running')
    time.sleep(.3)
    deleting.confirm(deletion)
    eventually(lambda:sql(f"SELECT count(*) FROM deletion_jobs WHERE user_id='{deleting.user['id']}' AND status='completed'")=='1')
    time.sleep(3.2)
    assert sql(f"SELECT count(*) FROM agent.checkpoints WHERE thread_id='{in_flight['run_id']}'")=='0'
    assert sql(f"SELECT count(*) FROM agent.run_threads WHERE run_id='{in_flight['run_id']}'")=='0'
    print('PASS: deleting during model execution cannot recreate a checkpoint afterwards')
    print('Recovery acceptance completed; source environment is running. Backup retained privately.')

if __name__=='__main__':main()
