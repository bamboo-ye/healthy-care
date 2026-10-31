/* Deterministic synthetic research fixture and analysis. No clinical model. */
(() => {
  'use strict';
  const VERSION='research-2026.10.18.2', DATA_VERSION='synthetic-light-illness-v2';
  const KNOWLEDGE_VERSION='symptom-pattern-demo-1', RULE_VERSION='medication-context-1';
  const topics=['感冒鼻咽','皮肤不适','轻度过敏','胃肠不适','轻微疼痛','其他不适'];
  const categories=['复方与退热产品','自报抗菌药','皮肤外用产品','成分待核实','其他单一产品','明确未用药'];
  const fields=[
    {id:'chief',label:'主要不适'},{id:'onset',label:'开始与持续'},
    {id:'severity',label:'不适自评分'},{id:'impact',label:'日常活动影响'},
    {id:'medicine',label:'实际用药状态'},{id:'change',label:'变化描述',comparable:false}
  ];
  const ruleDefinitions=[
    {id:'duplicate',title:'同日重复成分线索',description:'同一观察日，两个不同产品含相同已知成分。',missing:'具体时间、剂量、是否遵循专业建议',source:'https://www.fda.gov/drugs/safe-use-over-counter-pain-relievers-and-fever-reducers/acetaminophen'},
    {id:'antibiotic',title:'抗菌药使用依据待补',description:'自述使用抗菌药，但使用依据未记录。',missing:'产品身份、使用依据和适用情境',source:'https://www.who.int/news-room/fact-sheets/detail/antimicrobial-resistance'},
    {id:'steroid',title:'外用激素适用信息缺口',description:'外用激素记录缺少强度或使用部位。',missing:'具体产品、强度、部位及已有使用计划',source:'https://www.guysandstthomas.nhs.uk/health-information/topical-steroids'},
    {id:'ingredient',title:'成分无法归一',description:'自述使用的产品没有可核实的成分。',missing:'完整产品名、包装或成分资料',source:null}
  ];
  const date=day=>'2026-10-'+String(day+12).padStart(2,'0');
  const pct=(n,d)=>d?Math.round(n*1000/d)/10:null;
  const products=(mode,i)=>{
    if(mode===0)return [
      {id:'cold-a',name:'合成复方产品A',ingredients:['对乙酰氨基酚'],kind:'otc',basis:'自述',strength:null,site:null},
      {id:'pain-b',name:'合成退热产品B',ingredients:['对乙酰氨基酚'],kind:'otc',basis:'自述',strength:null,site:null}
    ];
    if(mode===1)return [{id:'antibiotic-c',name:'自述抗菌药C（合成）',ingredients:['合成抗菌成分'],kind:'antibiotic',basis:null,strength:null,site:null}];
    if(mode===2)return [{id:'topical-d',name:'外用激素D（合成）',ingredients:['合成外用糖皮质激素'],kind:'topical_steroid',basis:'自述',strength:null,site:i%4===0?'手臂':null}];
    if(mode===3)return [{id:'unknown-e',name:'包装不完整的产品E（合成）',ingredients:[],kind:'unknown',basis:'自述',strength:null,site:null}];
    if(mode===4)return [{id:'single-f',name:'单一产品F（合成）',ingredients:['合成单一成分'],kind:'other',basis:'自述',strength:'已记录',site:null}];
    return [];
  };
  function makeSubject(i){
    const topic=topics[Math.floor(i/10)], mode=i%6;
    const closedDay=i>0&&i%8===0?4:null;
    const planned=closedDay===null?7:closedDay+1;
    const first={chief:true,onset:i%3!==0,severity:i%2===0,impact:i%4===0,medicine:i%3===1||mode===5,change:false};
    const observations=[];
    for(let day=0;day<planned;day++){
      if(day>0&&((i*3+day)%7===0||(i%9===0&&day>=3)))continue;
      const use=mode===5?'not_used':(i+day)%9===0?'unknown':(i+day)%4===0?'not_used':'used';
      const known={...first};
      if(day>0){known.onset=true;known.severity=true;known.impact=i%7!==0;known.medicine=use!=='unknown';known.change=true;}
      const score=known.severity?Math.max(0,Math.min(10,6-i%3+(i%10===0?Math.floor(day/2):-Math.floor(day/2)))):null;
      const names=['嗓子不舒服','皮肤有些痒','鼻痒和打喷嚏','肚子有点不舒服','轻微头痛','有些说不清的不适'];
      const values={chief:names[Math.floor(i/10)],onset:known.onset?'持续到今天约'+(day+2)+'天':null,severity:known.severity?'不适大约'+score+'分':null,impact:known.impact?(score>=4?'有些影响睡眠或活动':'睡眠和活动没有明显影响'):null,medicine:known.medicine?(use==='not_used'?'今天明确没有用药':use==='used'?'今天用了'+products(mode,i).map(p=>p.name).join('、'):null):null,change:known.change?'和开始时相比的变化已补充':null};
      const sourceText=Object.values(values).filter(Boolean).join('，')+(use==='unknown'?'，今天是否用药记不清':'')+'。（合成自述）';
      const sourceId='S'+String(i+1).padStart(3,'0')+'-D'+day;
      const usedProducts=use==='used'?products(mode,i):[];
      const medText=use==='used'?'今天明确使用：'+usedProducts.map(p=>p.name+'（成分：'+(p.ingredients.join('、')||'待核实')+(p.kind==='topical_steroid'?'；强度：'+(p.strength||'未补充')+'；部位：'+(p.site||'未补充'):'')+'）').join('、'):use==='not_used'?'今天明确没有用药':'今天是否用药记不清';
      known.medicine=use!=='unknown';
      values.medicine=known.medicine?medText:null;
      const medEvidence={source_id:sourceId+'-M',text:medText,assertion:use};
      const fieldSources=Object.fromEntries(Object.entries(known).filter(([,available])=>available).map(([field])=>[field,field==='medicine'?medEvidence.source_id:sourceId]));
      observations.push({day,date:date(day),score,use,known,field_values:values,field_sources:fieldSources,source_text:sourceText,medication_evidence:medEvidence,
        products:use==='used'?products(mode,i):[],
        symptom_text:topic+'的日常变化（合成自述）',
        source_id:'S'+String(i+1).padStart(3,'0')+'-D'+day,
        source_type:'synthetic-self-report',
        image_available:i%4===0&&day===1,image_research_consent:false});
    }
    return {id:'S'+String(i+1).padStart(3,'0'),index:i,topic,category:categories[mode],
      research_consent:i%5!==0,consent_version:'demo-consent-1',closed_day:closedDay,
      first_fields:first,observations};
  }
  const subjects=Array.from({length:60},(_,i)=>makeSubject(i));
  function select(config={},sampleConsent=false){
    const windowDays=Number(config.window_days)===3?3:7;
    return subjects.filter(s=>s.index===0?sampleConsent:s.research_consent)
      .filter(s=>(!config.topic||config.topic==='all'||s.topic===config.topic)&&(!config.category||config.category==='all'||s.category===config.category))
      .map(s=>({...s,research_consent:s.index===0?sampleConsent:s.research_consent,expected_days:Math.min(windowDays,s.closed_day===null?7:s.closed_day+1),
        observations:s.observations.filter(o=>o.day<windowDays)}));
  }
  function coverage(rows){
    let first=0,full=0;
    const common=fields.filter(f=>f.comparable!==false);
    const byField=fields.map(f=>({id:f.id,label:f.label,comparable:f.comparable!==false,first:0,full:0}));
    const paired=rows.map(s=>{
      const firstCount=common.filter(f=>s.first_fields[f.id]).length;
      const available=Object.fromEntries(fields.map(f=>[f.id,s.observations.some(o=>o.known[f.id])]));
      const fullCount=common.filter(f=>available[f.id]).length;
      first+=firstCount;full+=fullCount;
      byField.forEach(f=>{if(s.first_fields[f.id])f.first++;if(available[f.id])f.full++;});
      return {id:s.id,topic:s.topic,first:firstCount,full:fullCount,available,first_fields:s.first_fields};
    });
    const denominator=rows.length*common.length;
    return {first,full,denominator,first_pct:pct(first,denominator),full_pct:pct(full,denominator),
      difference_pp:denominator?Math.round((full-first)*1000/denominator)/10:null,by_field:byField,paired};
  }
  function candidates(rows){
    const result=[];
    for(const s of rows){
      const found=new Map();
      function add(rule,o,fact){
        if(!found.has(rule))found.set(rule,{participant_id:s.id,rule,topic:s.topic,date:o.date,source_id:o.medication_evidence?.source_id||o.source_id,facts:fact});
      }
      for(const o of s.observations){
        if(o.use!=='used')continue;
        const ingredientProducts=new Map();
        for(const p of o.products){
          for(const component of new Set(p.ingredients)){
            if(!ingredientProducts.has(component))ingredientProducts.set(component,new Set());
            ingredientProducts.get(component).add(p.id);
          }
          if(!p.ingredients.length)add('ingredient',o,[p.name,'未记录可归一的成分']);
          if(p.kind==='antibiotic'&&!p.basis)add('antibiotic',o,[p.name,'使用依据未记录']);
          if(p.kind==='topical_steroid'&&(!p.strength||!p.site))add('steroid',o,[p.name,'强度：'+(p.strength||'未知'),'部位：'+(p.site||'未知')]);
        }
        for(const [ingredient,ids] of ingredientProducts)if(ids.size>1)add('duplicate',o,[ingredient,'同日不同产品数：'+ids.size]);
      }
      result.push(...found.values());
    }
    return result;
  }
  function analyzeRows(rows){
    const expected=rows.reduce((n,s)=>n+s.expected_days,0);
    const observed=rows.reduce((n,s)=>n+s.observations.length,0);
    const use={used:0,not_used:0,unknown:0,missing:expected-observed};
    rows.forEach(s=>s.observations.forEach(o=>use[o.use]++));
    const found=candidates(rows),coverageResult=coverage(rows);
    const daily=Array.from({length:7},(_,day)=>{
      const eligible=rows.filter(s=>s.expected_days>day);
      return {day:day+1,expected:eligible.length,observed:eligible.filter(s=>s.observations.some(o=>o.day===day)).length};
    }).filter(d=>d.expected>0);
    return {n:rows.length,expected,observed,completeness_pct:pct(observed,expected),
      candidate_participants:new Set(found.map(c=>c.participant_id)).size,candidate_count:found.length,
      coverage:coverageResult,use,daily,candidates:found,
      lower_use_pct:pct(use.used,expected),upper_use_pct:pct(use.used+use.unknown+use.missing,expected)};
  }
  const signalCases=[
    {id:'pattern',title:'组合信息齐全',description:'三项自述在演示窗口内出现。',events:[
      {date:'2026-09-28',symptom:'thirst',assertion:'present',text:'最近持续觉得口渴'},
      {date:'2026-10-05',symptom:'urination',assertion:'present',text:'排尿比平时多'},
      {date:'2026-10-18',symptom:'weight',assertion:'present',text:'没有主动减重，但体重下降'}]},
    {id:'negated',title:'明确否定项',description:'尿频被明确否定，不能靠关键词命中。',events:[
      {date:'2026-09-28',symptom:'thirst',assertion:'present',text:'最近持续觉得口渴'},
      {date:'2026-10-05',symptom:'urination',assertion:'absent',text:'没有排尿增多'},
      {date:'2026-10-18',symptom:'weight',assertion:'present',text:'非主动体重下降'}]},
    {id:'missing',title:'信息不足',description:'没有体重变化记录，不能补为阳性或阴性。',events:[
      {date:'2026-09-28',symptom:'thirst',assertion:'present',text:'最近持续觉得口渴'},
      {date:'2026-10-05',symptom:'urination',assertion:'present',text:'排尿比平时多'}]},
    {id:'future',title:'未来信息隔离',description:'截点之后的体重记录不能进入当前判断。',events:[
      {date:'2026-10-12',symptom:'thirst',assertion:'present',text:'最近持续觉得口渴'},
      {date:'2026-10-15',symptom:'urination',assertion:'present',text:'排尿比平时多'},
      {date:'2026-10-22',symptom:'weight',assertion:'present',text:'后续才报告非主动体重下降'}]}
  ];
  function evaluateSignal(id='pattern',windowDays=28){
    const sample=signalCases.find(c=>c.id===id)||signalCases[0];
    const asOf='2026-10-18',end=Date.parse(asOf+'T00:00:00Z'),start=end-(windowDays-1)*86400000;
    const evidence=['thirst','urination','weight'].map(symptom=>{
      const events=sample.events.filter(e=>e.symptom===symptom&&Date.parse(e.date+'T00:00:00Z')<=end&&Date.parse(e.date+'T00:00:00Z')>=start).sort((a,b)=>b.date.localeCompare(a.date));
      return {symptom,event:events[0]||null,status:events[0]?.assertion||'missing'};
    });
    return {id:sample.id,as_of:asOf,window_days:windowDays,evidence,
      excluded:sample.events.filter(e=>Date.parse(e.date+'T00:00:00Z')>end||Date.parse(e.date+'T00:00:00Z')<start),
      status:evidence.some(e=>e.status==='absent')?'not_supported':evidence.every(e=>e.status==='present')?'review':'insufficient'};
  }
  const fixtureExpected={pattern:'review',negated:'not_supported',missing:'insufficient',future:'insufficient'};
  function evaluateFixtures(){return signalCases.map(c=>({id:c.id,expected:fixtureExpected[c.id],actual:evaluateSignal(c.id,28).status}));}
  function snapshot(config={},sampleConsent=false){
    const normalized={topic:config.topic||'all',category:config.category||'all',window_days:Number(config.window_days)===3?3:7};
    return {schema_version:'1.0',data_origin:'synthetic',data_version:DATA_VERSION,
      config:normalized,field_definitions:fields,rule_version:RULE_VERSION,knowledge_version:KNOWLEDGE_VERSION,
      subjects:select(normalized,sampleConsent)};
  }
  function makeReport(input,hash,platform='local-browser',runUrl=null){
    const a=analyzeRows(input.subjects);
    return {schema_version:'1.0',run_id:'analysis-20261018-'+hash.slice(0,10),platform,
      run_url:runUrl,data_origin:'synthetic',data_version:DATA_VERSION,input_sha256:hash,
      code_version:VERSION,rule_version:RULE_VERSION,knowledge_version:KNOWLEDGE_VERSION,
      config:input.config,metrics:{participants:a.n,expected_patient_days:a.expected,observed_patient_days:a.observed,
        completeness_pct:a.completeness_pct,first_field_coverage_pct:a.coverage.first_pct,
        longitudinal_field_coverage_pct:a.coverage.full_pct,coverage_difference_pp:a.coverage.difference_pp,
        medication_candidate_participants:a.candidate_participants,medication_candidate_count:a.candidate_count,
        documented_use_days:a.use.used,documented_nonuse_days:a.use.not_used,unknown_use_days:a.use.unknown,
        missing_patient_days:a.use.missing,lower_use_pct:a.lower_use_pct,upper_use_pct:a.upper_use_pct},
      limitations:['合成边界样例，不代表真实人群频率','字段覆盖改善不是诊断或疗效改善','候选不是滥用、药物不良反应或耐药结论','自评分不是经验证的临床结局量表'],
      artifacts:['input.json','report.json'],provenance:'self-declared-platform'};
  }
  function canonicalStringify(value){
    const normalize=item=>Array.isArray(item)?item.map(normalize):item&&typeof item==='object'?Object.fromEntries(Object.keys(item).sort().map(key=>[key,normalize(item[key])])):item;
    return JSON.stringify(normalize(value));
  }
  const api={canonicalStringify,VERSION,DATA_VERSION,KNOWLEDGE_VERSION,RULE_VERSION,topics,categories,fields,ruleDefinitions,subjects,
    select,coverage,candidates,analyzeRows,signalCases,evaluateSignal,evaluateFixtures,snapshot,makeReport,pct};
  if(typeof module!=='undefined'&&module.exports)module.exports=api;else window.ResearchEngine=api;
})();
