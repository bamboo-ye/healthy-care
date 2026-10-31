"""Post-hoc sensitivity only; never replaces the frozen primary report."""
import argparse,json,statistics,random
from pathlib import Path

def analyze(data):
    fields=data['fields'];rows=[]
    for o in data['observations']:
        c=next(c for c in data['cases'] if c['id']==o['case_id']);facts=c['facts'];pred=o.get('prediction') or {};ok=not o.get('error')
        # An explicit unknown response is evidence, but not a known impact value.
        excluded=[f for f in fields if isinstance(facts[f],str) and facts[f] in ('记不清','不确定','未知')]
        known=[f for f in fields if facts[f] is not None and f not in excluded]
        correct=sum(ok and f in o['disclosed'] and type(pred.get(f)) is type(facts[f]) and pred.get(f)==facts[f] for f in known)
        rows.append({'case_id':c['id'],'cluster':c['cluster'],'arm':o['arm'],'recall':correct/len(known),'excluded_unknown_fields':excluded})
    summary={a:statistics.mean(r['recall'] for r in rows if r['arm']==a) for a in ['initial','generic','directed']}
    keys=sorted({r['cluster'] for r in rows});paired=[]
    for g in keys:
        ids=sorted({r['case_id'] for r in rows if r['cluster']==g});delta=[]
        for cid in ids:
            v={r['arm']:r['recall'] for r in rows if r['case_id']==cid};delta.append(v['directed']-v['generic'])
        paired.append(delta)
    rng=random.Random(20261024);samples=sorted(statistics.mean(x for group in rng.choices(paired,k=len(paired)) for x in group) for _ in range(2000))
    return {'analysis':'post-hoc unknown-impact sensitivity; not preregistered; not primary','clinical_validation':False,'unknown_code_rule':'记不清/不确定/未知 are explicit unknown text, excluded from nonempty known-field recall; original raw responses retained','summary_macro_recall':summary,'directed_minus_generic':summary['directed']-summary['generic'],'cluster_bootstrap_95_interval':[samples[49],samples[1949]],'records':rows}
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('input',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();a.out.write_text(json.dumps(analyze(json.loads(a.input.read_text())),ensure_ascii=False,indent=2)+'\n')
