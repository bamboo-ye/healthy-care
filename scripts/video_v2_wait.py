#!/usr/bin/env python3
"""Read-only monitor of the task started in the recorded UI; never initiates a run."""
import json,time
from pathlib import Path
from live_acceptance import Client
ROOT=Path(__file__).resolve().parents[1]
cfg=dict(x.split('=',1) for x in (ROOT/'.local/server-production.env').read_text().splitlines() if x and not x.startswith('#') and '=' in x)
origin=json.loads((ROOT/'.local/server-public-origin.json').read_text())['origin']
task=json.loads((ROOT/'output/video-v2/platform-task.json').read_text())
c=Client(origin);who=c.call('/v1/auth/login',{'email':cfg['RESEARCH_EMAIL'],'password':cfg['RESEARCH_PASSWORD']});c.csrf=who['csrf']
last=None
for _ in range(240):
 r=c.call('/v1/research/runs/'+task['run_id'])
 if r['status']!=last: print('Recorded SciencePal task:',r['status'],flush=True);last=r['status']
 if r['status']=='completed':
  assert r['result']['origin_verification']=='api-fetched-artifact'
  target=ROOT/'.local/video-v2-sciencepal-result.json';target.write_text(json.dumps(r,ensure_ascii=False,indent=2));target.chmod(0o600)
  safe={k:r.get(k) for k in ['id','snapshot_id','status','platform','external_run_id','external_thread_id','created_at','updated_at']}
  safe['result']={k:r['result'].get(k) for k in ['metrics','origin_verification','execution_platform','input_sha256','code_version','knowledge_version','rule_version']}
  (ROOT/'output/video-v2/platform-task-result.json').write_text(json.dumps(safe,ensure_ascii=False,indent=2))
  print('Artifact fetched and independently validated.',flush=True);break
 if r['status'] in ('failed','external_unknown','external_asked','awaiting_import','invalidated'):
  print('Needs inspection:',r['status'],r.get('error_code'),flush=True);break
 time.sleep(3)
else: print('Still running; retained original task, no new run created.',flush=True)
