/* Descriptive software methods; no model, diagnosis, recovery criterion or real prevalence. */
(function (host) {
  'use strict';
  const VERSION='research-methods-2026.10.18.1';
  function trajectory(rows){
    const paired=[],insufficient=[];
    for(const subject of rows){
      const scores=subject.observations.filter(o=>Number.isFinite(o.score)&&o.score>=0&&o.score<=10&&o.day<subject.expected_days).sort((a,b)=>a.day-b.day);
      if(scores.length<2){insufficient.push(subject.id);continue;}
      const first=scores[0],last=scores[scores.length-1],change=last.score-first.score;
      paired.push({participant_id:subject.id,topic:subject.topic,first_day:first.day+1,last_day:last.day+1,
        first_score:first.score,last_score:last.score,change,direction:change<0?'decrease':change>0?'increase':'same',
        first_source_id:first.source_id,last_source_id:last.source_id,baseline_observed:first.day===0,
        score_observations:scores.length,unmeasured_score_days:subject.expected_days-scores.length,
        archived_in_window:subject.closed_day!==null&&subject.closed_day!==undefined&&subject.closed_day<subject.expected_days,
        recovery_event:'not_defined'});
    }
    return {method_version:VERSION,participants:rows.length,paired:paired.length,insufficient:insufficient.length,
      baseline_observed:paired.filter(p=>p.baseline_observed).length,
      directions:{decrease:paired.filter(p=>p.direction==='decrease').length,same:paired.filter(p=>p.direction==='same').length,increase:paired.filter(p=>p.direction==='increase').length},
      archived_in_window:paired.filter(p=>p.archived_in_window).length,records:paired,
      interpretation:'First/last available self-scores only; no interpolation, causal drug effect or recovery event.'};
  }
  function baseRate(prevalencePct,sensitivityPct,specificityPct,population=10000){
    if(![prevalencePct,sensitivityPct,specificityPct].every(x=>Number.isFinite(x)&&x>=0&&x<=100)||!Number.isFinite(population)||population<=0)throw new Error('假设比例应在0至100之间。');
    const p=prevalencePct/100,se=sensitivityPct/100,sp=specificityPct/100;
    const tp=population*p*se,fn=population*p*(1-se),fp=population*(1-p)*(1-sp),tn=population*(1-p)*sp;
    return {method_version:VERSION,assumption_only:true,population,prevalence_pct:prevalencePct,sensitivity_pct:sensitivityPct,specificity_pct:specificityPct,
      expected_true_positive:tp,expected_false_negative:fn,expected_false_positive:fp,expected_true_negative:tn,
      ppv_pct:tp+fp>0?tp/(tp+fp)*100:null,alerts_per_1000:(tp+fp)/population*1000};
  }
  const api={VERSION,trajectory,baseRate};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else host.ResearchMethods=api;
})(typeof window!=='undefined'?window:globalThis);
