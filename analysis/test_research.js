'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs');
const os=require('node:os');
const path=require('node:path');
const crypto=require('node:crypto');
const {spawnSync}=require('node:child_process');
const E=require('../prototype/research/engine.js');

assert.equal(E.select().length,48);
assert.equal(E.select({},true).length,49);
assert.equal(E.select({},true).find(s=>s.id==='S001').research_consent,true);
assert(!E.select().some(s=>s.id==='S001'));
for(const c of E.evaluateFixtures())assert.equal(c.actual,c.expected,c.id);
assert.equal(E.evaluateSignal('pattern',7).status,'insufficient');
const baseline=E.analyzeRows(E.select());
assert.equal(baseline.expected,324);
assert.equal(baseline.observed,267);
assert.equal(baseline.coverage.denominator,48*5);
for(const c of baseline.candidates){const subject=E.select().find(s=>s.id===c.participant_id);assert(subject.observations.some(o=>o.medication_evidence.source_id===c.source_id));}
assert.equal(Object.values(baseline.use).reduce((a,b)=>a+b,0),baseline.expected);
assert(baseline.lower_use_pct<=baseline.upper_use_pct);
const simple=(day,items,use='used')=>({day,date:'2026-10-'+(12+day),source_id:'fixture-'+day,use,products:items});
const product=id=>({id,name:id,ingredients:['same'],kind:'otc',basis:'self',strength:null,site:null});
const participant=obs=>({id:'unit',topic:'fixture',observations:obs});
assert.equal(E.candidates([participant([simple(0,[product('a'),product('b')])])]).filter(c=>c.rule==='duplicate').length,1);
assert.equal(E.candidates([participant([simple(0,[product('a')]),simple(1,[product('b')])])]).length,0);
assert.equal(E.candidates([participant([simple(0,[product('a'),product('b')],'unknown')])]).length,0);
assert.equal(E.canonicalStringify({b:1,a:2}),E.canonicalStringify({a:2,b:1}));
const temp=fs.mkdtempSync(path.join(os.tmpdir(),'health-research-check-'));
try{
 for(const config of [{},{window_days:3},{topic:'皮肤不适'}]){
  const input=E.snapshot(config),hash=crypto.createHash('sha256').update(E.canonicalStringify(input)).digest('hex');
  fs.writeFileSync(path.join(temp,'input.json'),JSON.stringify(input));
  const process=spawnSync('python3',[path.join(__dirname,'../prototype/research/run_analysis.py'),path.join(temp,'input.json'),'--out',path.join(temp,'out')],{encoding:'utf8'});
  assert.equal(process.status,0,process.stderr);
  const report=JSON.parse(fs.readFileSync(path.join(temp,'out','report.json'),'utf8'));
  assert.equal(report.input_sha256,hash);
  assert.deepEqual(report.metrics,E.makeReport(input,hash).metrics);
 }
 console.log('PASS: consent, denominators, medication-time boundaries, 4 signal fixtures, and JS/Python parity in 3 cohorts.');
} finally {fs.rmSync(temp,{recursive:true,force:true});}
