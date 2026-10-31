"""Pure-standard-library scorer; runnable unchanged inside SciencePal."""
import argparse,hashlib,json,random,statistics
from pathlib import Path
VERSION='recording-benchmark-v1'
ARMS=['initial','generic','directed']
def evaluate(data):
    assert data['schema_version']==VERSION and data['data_origin']=='synthetic'
    cases=data['cases']; obs=data['observations']; fields=data['fields']
    assert len({c['id'] for c in cases})==len(cases) and cases
    expected={(c['id'],a) for c in cases for a in ARMS}
    assert {(o['case_id'],o['arm']) for o in obs}==expected and len(obs)==len(expected)
    records=[]
    for c in cases:
        for a in ARMS:
            o=next(x for x in obs if x['case_id']==c['id'] and x['arm']==a)
            disclosed=set(o['disclosed']); assert disclosed<=set(fields)
            pred=o.get('prediction') or {}; success=not o.get('error')
            if data.get('experiment') and success:
                calls=o['calls']; assert len(calls)==(1 if a=='initial' else 2)
                content=lambda call:call.get('response_content') if 'response_content' in call else call['response']['choices'][0]['message']['content']
                assert json.loads(content(calls[-1]))==pred, 'Prediction differs from actual response'
                asked=[] if a=='initial' else json.loads(content(calls[0]))['questions']
                assert len(asked)<=3 and len(set(asked))==len(asked) and set(asked)<=set(fields)
                assert disclosed==set(c['disclosed'])|set(asked), 'Disclosure differs from recorded questions'
                expected_messages=[{'role':'user','content':c['initial']}]
                if a!='initial':
                    expected_messages.extend([{'role':'assistant','content':json.dumps({'questions':asked},ensure_ascii=False)},{'role':'user','content':json.dumps({f:c['facts'][f] for f in asked},ensure_ascii=False)}])
                    assert calls[0]['request']['messages'][1:]==expected_messages[:1]
                assert calls[-1]['request']['messages'][1:]==expected_messages, 'Extraction input differs from disclosed facts'
            truth=c['facts']; known=[f for f in fields if truth[f] is not None]
            correct=sum(success and f in disclosed and type(pred.get(f)) is type(truth[f]) and pred.get(f)==truth[f] for f in known)
            outputs=[f for f in fields if pred.get(f) is not None] if success else []
            unknown=[f for f in fields if truth[f] is None]
            records.append({'case_id':c['id'],'cluster':c['cluster'],'topic':c['topic'],'arm':a,'recall':correct/len(known),'correct':correct,'known':len(known),'disclosed_known':sum(f in disclosed for f in known),'outputs':len(outputs),'unsupported':sum(f not in disclosed for f in outputs),'unknown_count':len(unknown),'unknown_preserved':sum(success and pred.get(f) is None for f in unknown),'failed':int(not success),'tokens':o.get('total_tokens'),'seconds':o.get('seconds')})
    summary={}
    for arm in ARMS:
        r=[v for v in records if v['arm']==arm]; total=lambda key:sum(x[key] for x in r)
        ratio=lambda n,d:total(n)/total(d) if total(d) else None
        summary[arm]={'events':len(r),'event_macro_recall':statistics.mean(x['recall'] for x in r),'precision':ratio('correct','outputs'),'disclosed_recall':ratio('correct','disclosed_known'),'unsupported_fraction':ratio('unsupported','outputs'),'unknown_preservation':ratio('unknown_preserved','unknown_count'),'failures':total('failed'),'reported_total_tokens':sum(x['tokens'] for x in r) if all(x['tokens'] is not None for x in r) else None,'mean_seconds':statistics.mean(x['seconds'] for x in r) if all(x['seconds'] is not None for x in r) else None}
    clusters=sorted({c['cluster'] for c in cases}); rng=random.Random(20261024); deltas=[]
    by={(r['case_id'],r['arm']):r for r in records}
    cluster_deltas={g:[by[c['id'],'directed']['recall']-by[c['id'],'generic']['recall'] for c in cases if c['cluster']==g] for g in clusters}
    for _ in range(2000):
        sample=[v for g in rng.choices(clusters,k=len(clusters)) for v in cluster_deltas[g]]; deltas.append(statistics.mean(sample))
    deltas.sort()
    canonical=json.dumps(data,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()
    return {'schema_version':VERSION,'data_origin':'synthetic','clinical_validation':False,'input_sha256':hashlib.sha256(canonical).hexdigest(),'summary':summary,'paired_directed_minus_generic':{'estimate':statistics.mean(v for ds in cluster_deltas.values() for v in ds),'cluster_bootstrap_95_interval':[deltas[49],deltas[1949]],'clusters':len(clusters),'resamples':2000},'records':records}
def main():
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();data=json.loads(a.input.read_text());result=evaluate(data);a.out.mkdir(parents=True,exist_ok=True);(a.out/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n');print(json.dumps({'input_sha256':result['input_sha256'],'summary':result['summary'],'paired':result['paired_directed_minus_generic']},ensure_ascii=False))
if __name__=='__main__':main()
