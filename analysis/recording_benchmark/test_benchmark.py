import copy, unittest
from build_dataset import build
from run_analysis import evaluate,ARMS,VERSION
class BenchmarkTests(unittest.TestCase):
    def fixture(self):
        ds=build();cases=[c for c in ds['cases'] if c['split']=='test'];obs=[]
        for c in cases:
            for arm in ARMS:
                disclosed=c['disclosed'] if arm=='initial' else list(c['facts'])
                obs.append({'case_id':c['id'],'arm':arm,'disclosed':disclosed,'prediction':{f:c['facts'][f] if f in disclosed else None for f in ds['fields']},'total_tokens':1,'seconds':1})
        return {'schema_version':VERSION,'data_origin':'synthetic','fields':ds['fields'],'cases':cases,'observations':obs}
    def test_split_cluster_disjoint_and_balanced(self):
        d=build();dev={c['cluster'] for c in d['cases'] if c['split']=='development'};test={c['cluster'] for c in d['cases'] if c['split']=='test'};self.assertFalse(dev&test);self.assertEqual(len(d['cases']),60)
        self.assertTrue(all(sum(c['topic']==t and c['split']=='test' for c in d['cases'])==16 for t in ['skin','respiratory','digestive']))
    def test_identical_arms_zero_difference(self):
        r=evaluate(self.fixture());self.assertEqual(r['paired_directed_minus_generic']['estimate'],0);self.assertEqual(r['paired_directed_minus_generic']['cluster_bootstrap_95_interval'],[0,0]);self.assertEqual(r['summary']['directed']['event_macro_recall'],1)
    def test_undisclosed_correct_guess_not_rewarded(self):
        d=self.fixture();o=d['observations'][0];c=d['cases'][0];f=next(f for f in d['fields'] if f not in o['disclosed'] and c['facts'][f] is not None);o['prediction'][f]=c['facts'][f];r=evaluate(d);self.assertGreater(r['summary']['initial']['unsupported_fraction'],0);self.assertLess(r['summary']['initial']['precision'],1)
    def test_failure_retained_and_missing_pairs_rejected(self):
        d=self.fixture();d['observations'][1]['error']='timeout';r=evaluate(d);self.assertEqual(r['summary']['generic']['events'],48);self.assertEqual(r['summary']['generic']['failures'],1);self.assertLess(r['summary']['generic']['event_macro_recall'],1)
        d['observations'].pop()
        with self.assertRaises(AssertionError):evaluate(d)
    def test_trace_tampering_rejected(self):
        import json
        d=self.fixture();d['cases']=d['cases'][:1];d['observations']=d['observations'][:3];d['experiment']={'method':'fixture'}
        c=d['cases'][0]
        for o in d['observations']:
            asked=[] if o['arm']=='initial' else ['onset_days','severity','impact']
            o['disclosed']=sorted(set(c['disclosed'])|set(asked))
            o['prediction']={f:c['facts'][f] if f in o['disclosed'] else None for f in d['fields']}
            messages=[{'role':'user','content':c['initial']}]
            o['calls']=[]
            if asked:
                q={'questions':asked};o['calls'].append({'request':{'messages':[{'role':'system','content':'fixture'},*messages]},'response_content':json.dumps(q)})
                messages.extend([{'role':'assistant','content':json.dumps(q,ensure_ascii=False)},{'role':'user','content':json.dumps({f:c['facts'][f] for f in asked},ensure_ascii=False)}])
            o['calls'].append({'request':{'messages':[{'role':'system','content':'fixture'},*messages]},'response_content':json.dumps(o['prediction'])})
        evaluate(d)
        d['observations'][0]['prediction']['severity']=999
        with self.assertRaises(AssertionError):evaluate(d)
    def test_trace_disclosure_tampering_rejected(self):
        # Extra field IDs cannot enter the scoring denominator unnoticed.
        d=self.fixture();d['observations'][0]['disclosed'].append('foreign_field')
        with self.assertRaises(AssertionError):evaluate(d)
    def test_posthoc_unknown_encoding_preserves_original(self):
        from unknown_sensitivity import analyze
        d=self.fixture();original=copy.deepcopy(d);r=analyze(d)
        self.assertEqual(d,original)
        self.assertIn('not primary',r['analysis'])
        self.assertTrue(any(x['excluded_unknown_fields'] for x in r['records']))
        self.assertEqual(r['directed_minus_generic'],0)
if __name__=='__main__':unittest.main()
