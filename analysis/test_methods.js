'use strict';
const assert=require('node:assert/strict');
const fs=require('node:fs'),os=require('node:os'),path=require('node:path');
const {spawnSync}=require('node:child_process');
const E=require('../prototype/research/engine.js'),M=require('../prototype/research/research-methods.js');
const observation=(day,score)=>({day,score,source_id:'fixture-day-'+day});
const subject=(observations,closed_day=null,expected_days=7)=>({id:'fixture',topic:'fixture',observations,closed_day,expected_days});
const sparse=subject([observation(0,null),observation(2,6),observation(6,3)]);
const before=JSON.stringify(sparse),a=M.trajectory([sparse]);
assert.equal(JSON.stringify(sparse),before);
assert.equal(a.paired,1);assert.equal(a.baseline_observed,0);
assert.equal(a.records[0].first_day,3);assert.equal(a.records[0].last_day,7);
assert.equal(a.records[0].change,-3);assert.equal(a.records[0].unmeasured_score_days,5);
assert.equal(a.records[0].recovery_event,'not_defined');
assert.equal(M.trajectory([subject([observation(0,8)])]).insufficient,1);
assert.equal(M.trajectory([subject([observation(0,2),observation(1,5)])]).directions.increase,1);
assert.equal(M.trajectory([subject([observation(0,5),observation(2,2)],4,3)]).archived_in_window,0);
assert.equal(M.trajectory([subject([observation(0,true),observation(1,Infinity),observation(2,3)])]).insufficient,1);
const r=M.baseRate(1,80,95);
assert(Math.abs(r.expected_true_positive-80)<1e-9);
assert(Math.abs(r.expected_false_positive-495)<1e-9);
assert(Math.abs(r.ppv_pct-80/575*100)<1e-9);
assert(Math.abs(r.expected_true_positive+r.expected_false_negative+r.expected_false_positive+r.expected_true_negative-10000)<1e-9);
assert.equal(M.baseRate(0,80,100).ppv_pct,null);
assert(M.baseRate(0.1,80,95).ppv_pct<r.ppv_pct);
assert.throws(()=>M.baseRate(-1,80,95));assert.throws(()=>M.baseRate(1,NaN,95));
const folder=fs.mkdtempSync(path.join(os.tmpdir(),'health-methods-'));
try{
 for(const config of [{},{window_days:3},{topic:'皮肤不适'}]){
  const input=E.snapshot(config),file=path.join(folder,'input.json');fs.writeFileSync(file,JSON.stringify(input));
  const p=spawnSync('python3',[path.join(__dirname,'../prototype/research/run_methods.py'),file,'--out',path.join(folder,'out')],{encoding:'utf8'});
  assert.equal(p.status,0,p.stderr);
  const out=JSON.parse(fs.readFileSync(path.join(folder,'out/methods.json'),'utf8'));
  assert.deepEqual(out.trajectory,M.trajectory(input.subjects));
  for(const condition of out.base_rate_scenarios){
   const js=M.baseRate(condition.prevalence_pct,80,95);
   for(const [key,value] of Object.entries(js))if(typeof value==='number')assert(Math.abs(condition[key]-value)<1e-9,key);
  }
 }
 console.log('PASS: sparse/unknown scores, no recovery inference, future closure isolation, base-rate limits and JS/Python parity.');
}finally{fs.rmSync(folder,{recursive:true,force:true});}
