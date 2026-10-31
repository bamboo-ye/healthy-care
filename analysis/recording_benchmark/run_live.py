"""Explicit opt-in, synthetic-only component benchmark. No production records."""
import argparse,concurrent.futures,datetime,hashlib,json,os,time
from pathlib import Path
from urllib import request,error
from run_analysis import evaluate,VERSION
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
EXTRACT='你是记录提取器，不诊断或推荐药物。仅从已披露对话提取事实，未披露、记不清、明确未知填null。输出JSON对象，键为symptom,onset_days,severity,impact,medication_state,medication_name。onset_days和severity为整数或null；medication_state仅used/not_used/unknown/null；其余为原话字符串或null。否定用药为not_used。不要补造或把没有提及当否定。'
QUESTION='你帮助用户整理自主护理记录，不诊断或推荐用药。选择一轮最有帮助的最多3个不同字段追问。字段：symptom（不适描述）、onset_days（持续天数）、severity（自评分）、impact（活动影响）、medication_state（used/not_used/unknown）、medication_name（实际用品名称）。仅输出JSON：{"questions":[字段ID]}。'
STRATEGY='定向策略：优先询问尚未披露且对完整记录有用的字段，不重复已有字段；不要根据常识填补否定、未知或用品名称。'
def digest(v):return hashlib.sha256(json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def call(cfg,messages):
    body={'model':cfg['MODEL_NAME'],'messages':messages,'response_format':{'type':'json_object'},'max_tokens':450,'stream':False}
    raw=json.dumps(body,ensure_ascii=False).encode(); start=time.monotonic()
    req=request.Request(cfg['MODEL_BASE_URL'].rstrip('/')+'/chat/completions',data=raw,headers={'Authorization':'Bearer '+cfg['MODEL_API_KEY'],'Content-Type':'application/json'})
    with request.urlopen(req,timeout=120) as response: result=json.load(response)
    text=result['choices'][0]['message']['content']; parsed=json.loads(text)
    return parsed,{'request':body,'response':result,'seconds':time.monotonic()-start}
def run_case(c,cfg):
    observations=[]
    for arm in ['initial','generic','directed']:
        o={'case_id':c['id'],'arm':arm,'disclosed':list(c['disclosed']),'calls':[],'prediction':None,'error':None};start=time.monotonic()
        messages=[{'role':'user','content':c['initial']}]
        try:
            if arm!='initial':
                system=QUESTION+ ('\n'+STRATEGY if arm=='directed' else '')
                q,receipt=call(cfg,[{'role':'system','content':system},*messages]);o['calls'].append(receipt)
                fields=q.get('questions');assert isinstance(fields,list) and len(fields)<=3 and len(set(fields))==len(fields) and all(f in c['facts'] for f in fields),'invalid_questions'
                # This fixed responder is the only place hidden facts are accessed.
                answer={f:c['facts'][f] for f in fields};o['disclosed']=sorted(set(o['disclosed'])|set(fields))
                messages.extend([{'role':'assistant','content':json.dumps(q,ensure_ascii=False)},{'role':'user','content':json.dumps(answer,ensure_ascii=False)}])
            pred,receipt=call(cfg,[{'role':'system','content':EXTRACT},*messages]);o['calls'].append(receipt)
            assert isinstance(pred,dict) and set(pred)==set(c['facts']),'invalid_prediction_fields'
            for f in ['onset_days','severity']:assert pred[f] is None or type(pred[f]) is int,'invalid_numeric_type'
            assert pred['medication_state'] in (None,'used','not_used','unknown'),'invalid_medication_state'
            for f in ['symptom','impact','medication_name']:assert pred[f] is None or isinstance(pred[f],str),'invalid_text_type'
            o['prediction']=pred
        except Exception as exc:
            # No response headers, authentication material or URLs in public errors.
            o['error']=type(exc).__name__
        o['seconds']=time.monotonic()-start
        uses=[x['response'].get('usage',{}).get('total_tokens') for x in o['calls']]
        o['total_tokens']=sum(uses) if uses and all(type(x) is int for x in uses) and not o['error'] else None
        observations.append(o)
    return observations
def main():
    p=argparse.ArgumentParser();p.add_argument('--synthetic-only',required=True,action='store_true');p.add_argument('--out',required=True,type=Path);p.add_argument('--split',choices=['development','test'],default='test');p.add_argument('--workers',type=int,default=4);a=p.parse_args()
    assert not a.out.exists(),'Output must be a new directory; evidence is immutable'
    cfg=dict(line.split('=',1) for line in (ROOT/'.env').read_text().splitlines() if line and not line.startswith('#') and '=' in line)
    assert all(cfg.get(k) for k in ['MODEL_NAME','MODEL_BASE_URL','MODEL_API_KEY'])
    dataset=json.loads((HERE/'dataset.json').read_text());cases=[c for c in dataset['cases'] if c['split']==a.split]
    data={'schema_version':VERSION,'data_origin':'synthetic','fields':dataset['fields'],'cases':cases,'observations':[],'experiment':{'split':a.split,'model':cfg['MODEL_NAME'],'started_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'dataset_sha256':digest(dataset),'protocol_sha256':hashlib.sha256((HERE/'protocol.md').read_bytes()).hexdigest(),'prompt_sha256':digest([EXTRACT,QUESTION,STRATEGY]),'method':'one-round structured field query; deterministic synthetic respondent','clinical_validation':False}}
    a.out.mkdir(parents=True,mode=0o700)
    with concurrent.futures.ThreadPoolExecutor(max_workers=min(max(a.workers,1),6)) as pool:
        futures={pool.submit(run_case,c,cfg):c for c in cases}
        for future in concurrent.futures.as_completed(futures):
            data['observations'].extend(future.result());data['observations'].sort(key=lambda x:(x['case_id'],x['arm']));(a.out/'observations.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n');print(f'Completed {len(data["observations"])//3}/{len(cases)}',flush=True)
    data['experiment']['completed_at']=datetime.datetime.now(datetime.timezone.utc).isoformat();(a.out/'observations.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    report=evaluate(data);(a.out/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');print(json.dumps(report['summary'],ensure_ascii=False),flush=True)
if __name__=='__main__':main()
