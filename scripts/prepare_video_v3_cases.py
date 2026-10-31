#!/usr/bin/env python3
"""Enter author-approved fictional everyday cases through the real product API.

This is presentation data, not a clinical study. No images, test-provider calls,
SQL inserts, fabricated model responses, or real patient information are used.
"""
import concurrent.futures,json,secrets,time
from pathlib import Path
from live_acceptance import Client
ROOT=Path(__file__).resolve().parents[1]
ORIGIN=json.loads((ROOT/'.local/server-public-origin.json').read_text())['origin']
OUT=ROOT/'.local/video-v3-case-accounts';OUT.mkdir(exist_ok=True)
CASES=[
 {'age':28,'symptoms':'喉咙疼、鼻塞','scores':[6,4,2],'use':['unknown','used','not_used'],'meds':['补记10月27日晚上8点用过对乙酰氨基酚片，药盒成分写的是对乙酰氨基酚，具体用量和频次记不清了。','10月27日晚上8点还吃过复方氨酚烷胺片，成分中也有对乙酰氨基酚，具体用量记不清了。请补记这一种药。']},
 {'age':32,'symptoms':'咽痛、干咳','scores':[5,4,3],'use':['not_used','unknown','not_used'],'meds':[]},
 {'age':26,'symptoms':'鼻塞、头痛','scores':[6,4,3],'use':['used','used','unknown'],'meds':['补记10月27日晚上8点用过布洛芬片，药盒成分写的是布洛芬，用量和频次记不清了。']},
 {'age':35,'symptoms':'乏力、喉咙疼','scores':[5,4,2],'use':['unknown','not_used','not_used'],'meds':[]},
 {'age':29,'symptoms':'干咳、鼻塞','scores':[4,3,2],'use':['used','used','not_used'],'meds':[]},
 {'age':31,'symptoms':'咽痛、鼻塞、头痛','scores':[6,4,2],'use':['used','unknown','not_used'],'meds':['补记10月27日晚上8点用过对乙酰氨基酚片，成分是对乙酰氨基酚，用量和次数记不清了。']}
]
def enter(index,case):
 p=OUT/f'case-{index+1}.json'
 if p.exists() and json.loads(p.read_text()).get('completed'):return 'already recorded'
 data=json.loads(p.read_text()) if p.exists() else {'email':f'care-story-{int(time.time())}-{index+1}@example.test','password':secrets.token_urlsafe(24),'fictional':True,'steps':[]}
 def save():p.write_text(json.dumps(data,ensure_ascii=False,indent=2));p.chmod(0o600)
 save();c=Client(ORIGIN)
 if data.get('user_id'):who=c.call('/v1/auth/login',{'email':data['email'],'password':data['password']})
 else:who=c.call('/v1/auth/register',{'email':data['email'],'password':data['password']});data['user_id']=who['id'];save()
 c.csrf=who['csrf']
 def step(key,text,kind):
  if any(x['key']==key and x.get('confirmed') for x in data['steps']):return
  r=c.message(text);item={'key':key,'input':text,'reply':r['reply'],'run_id':r['run_id'],'actions':r['actions']};data['steps'].append(item);save()
  expected=[a for a in r['actions'] if a['kind']==kind]
  if len(expected)!=1:raise RuntimeError(f'{key}: expected {kind}, got {[a["kind"] for a in r["actions"]]}')
  c.call('/v1/health/actions/'+expected[0]['id']+'/confirm',{});item['confirmed']=True;save()
 step('episode',f'我{case["age"]}岁，2026年10月25日早上8点开始{case["symptoms"]}，当天新冠抗原阳性，目前没有呼吸困难。请帮我建立这次不适的病程，开始时间记为2026年10月25日早上8点。','create_episode')
 wording={'used':'当天用了药','not_used':'当天没有用药','unknown':'当天有没有用药记不清了'}
 for day,score,use in zip([25,27,29],case['scores'],case['use']):
  step(f'day-{day}',f'补记2026年10月{day}日的情况：{case["symptoms"]}，不适自评分{score}分，{wording[use]}，'+('有些影响睡眠和日常活动。' if score>=4 else '日常活动基本正常。')+'请记录这一天的变化。','checkin')
 for i,med in enumerate(case['meds']):step('medicine-'+str(i),med,'record_medication')
 step('consent','我同意健康记录研究授权，请处理这一项授权。','set_consent')
 data['completed']=True;save();return 'recorded'
if __name__=='__main__':
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  futures={pool.submit(enter,i,c):i for i,c in enumerate(CASES)}
  for f in concurrent.futures.as_completed(futures):
   i=futures[f]
   try:print(f'Fictional everyday case {i+1}: {f.result()}',flush=True)
   except Exception as e:print(f'Fictional everyday case {i+1}: needs attention {type(e).__name__}: {e}',flush=True)
