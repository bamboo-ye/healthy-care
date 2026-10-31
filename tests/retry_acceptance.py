"""Persistent message retry and idempotency on the isolated synthetic stack."""
from uuid import uuid4
from api_acceptance import Client
from recovery_acceptance import compose

def main():
    user=Client().register();other=Client().register();assert user.call('/v1/system/status')['test_provider']
    image=user.upload();client_id=str(uuid4());content='重试流程的合成输入，不创建病程'
    compose('stop','worker',stdout=None)
    try:
        first=user.message(content,[image['id']],client_id)
        user.call('/v1/health/runs/'+first['run_id']+'/cancel',{})
        other.call('/v1/health/runs/'+first['run_id']+'/retry',{},expected=404)
        retried=user.call('/v1/health/runs/'+first['run_id']+'/retry',{},expected=202)
        replay=user.call('/v1/health/runs/'+first['run_id']+'/retry',{},expected=202)
        assert retried['run_id']==replay['run_id'] and replay['replayed']
        assert retried['run_id']!=first['run_id'] and retried['message_id']==first['message_id']
        assert len([m for m in user.conversation()['messages'] if m['role']=='user'])==1
        assert user.message(content,[image['id']],client_id)['run_id']==retried['run_id']
        from concurrent.futures import ThreadPoolExecutor
        from urllib import request
        duplicate_id=str(uuid4());conversation=user.conversation()['id']
        def concurrent_send(_):
            copy=Client();copy.cookies=user.cookies;copy.opener=request.build_opener(request.ProxyHandler({}),request.HTTPCookieProcessor(copy.cookies));copy.csrf=user.csrf
            return copy.call(f'/v1/health/conversations/{conversation}/messages',{'content':'同一请求的并发合成重试','attachments':[],'client_id':duplicate_id},expected=202)
        with ThreadPoolExecutor(max_workers=2) as pool:duplicates=list(pool.map(concurrent_send,range(2)))
        assert duplicates[0]['run_id']==duplicates[1]['run_id']
    finally:compose('start','worker',stdout=None)
    user.wait(retried['run_id'])
    messages=user.conversation()['messages'];assert len([m for m in messages if m['role']=='user'])==2
    assert next(m for m in messages if m['role']=='user')['attachments']==[image['id']]
    assert user.state()['episodes']==[]
    user.call('/v1/health/runs/'+retried['run_id']+'/retry',{},expected=409)
    print('PASS: retry preserves one message and its image, starts a fresh run, replays idempotently and enforces ownership')

if __name__=='__main__':main()
