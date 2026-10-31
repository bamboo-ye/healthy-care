
(() => {
'use strict';
const {icon,esc}=window.HealthUI, E=window.ResearchEngine, P=window.ResearchProgram, M=window.ResearchMethods;
const root=document.getElementById('research-app'),main=document.getElementById('main');
const state={route:'overview',study:'coverage',topic:'all',category:'all',window_days:7,sampleConsent:false,
  sample:null,focusSource:null,rule:'duplicate',signal:'pattern',signalWindow:28,report:null,reportInput:null,busy:false,epoch:0,runError:null,plan:'capture',sourceScope:'latest',prior:1,sensitivity:80,specificity:95};
const config=()=>({topic:state.topic,category:state.category,window_days:state.window_days});
const rows=()=>E.select(config(),state.sampleConsent);
const analysis=()=>E.analyzeRows(rows());
const fmt=(value,suffix='')=>value===null||value===undefined?'—':value+suffix;
const useLabels={used:'明确使用',not_used:'明确未用',unknown:'自述记不清',missing:'无当日记录'};
const signalLabels={review:'组合信息需进一步核实',not_supported:'当前组合不支持',insufficient:'信息不足，暂不判断'};
const sources=[
 {id:'dialogue',year:'2026',type:'原始研究 · Nature Health',title:'人机交互会影响症状报告质量',url:'https://www.nature.com/articles/s44360-026-00116-y',finding:'研究关注报告对象是AI或医生时，模拟症状描述的质量差异。',translation:'把信息采集质量列为研究终点，比较首次描述和追问后的同一组字段。',limit:'模拟情境与评估方式存在边界；不能直接外推本产品的临床效果。'},
 {id:'pro',year:'2025',type:'方法指南 · FDA',title:'患者自报数据需要适合测量目的',url:'https://www.fda.gov/regulatory-information/search-fda-guidance-documents/patient-focused-drug-development-selecting-developing-or-modifying-fit-purpose-clinical-outcome',finding:'指南讨论如何选择、开发或修改适合具体用途的临床结局评估。',translation:'明确字段定义、回忆期与分母；将随手记录的0—10分与经过验证的量表区分。',limit:'本项目借鉴方法，不声称成为监管级试验终点。'},
 {id:'longitudinal',year:'2026',type:'原始研究 · Nature',title:'对话AI从单次咨询走向多次管理',url:'https://www.nature.com/articles/s41586-026-10764-5',finding:'多次就诊上下文和长程管理成为对话医疗AI的研究方向。',translation:'保留事件时间、建议版本和跨次证据，先检验时序一致性与可追溯性。',limit:'该研究体系与自主用药小病场景不同，结果不能转移成本项目性能。'},
 {id:'multimodal',year:'2026',type:'原始研究 · Nature Medicine',title:'多模态对话需要联合证据评估',url:'https://www.nature.com/articles/s41591-026-04371-0',finding:'研究将图像等信息放入诊断对话，探索多模态推理。',translation:'图片保留质量、时间和独立授权；研究端展示出处，不把图片自动标成诊断真值。',limit:'当前原型没有运行图像模型；不能报告图片诊断准确率。'},
 {id:'amr',year:'2026',type:'公共卫生 · WHO',title:'抗菌药合理使用与社区信息缺口',url:'https://www.who.int/news-room/fact-sheets/detail/antimicrobial-resistance',finding:'WHO将抗微生物药物不当与过度使用列为耐药的重要驱动因素。',translation:'收集使用情境和依据缺口，形成待核实线索；与用药安全研究衔接。',limit:'没有微生物检测或确诊标签，不能把本平台记录解释为耐药率。'},
 {id:'rwd',year:'方法基础',type:'定义与方法 · FDA',title:'真实世界数据不自动成为真实世界证据',url:'https://www.fda.gov/science-research/science-and-research-special-topics/real-world-evidence',finding:'真实世界数据及其分析形成的证据具有不同含义。',translation:'每个结果关联研究问题、数据适用性、分析方法和局限；冻结可复现快照。',limit:'合成演示只验证计算和交互，尚未形成临床证据。'}
].concat(P.sources);
const studies=[
 {id:'coverage',code:'RQ01',title:'连续记录，究竟补充了什么？',short:'连续记录价值',icon:'chat',measure:'比较5项共用字段的可解释覆盖率',design:'同一合成病程内，首次描述与观察窗口内所有记录配对比较。变化描述作为纵向新增信息单列，不纳入共用字段改善率。',source:'dialogue',boundary:'不是随机对照，不区分追问和额外时间的作用；不表示诊断准确率或疗效提升。'},
 {id:'medication',code:'RQ02',title:'院外用药，哪些信息值得核实？',short:'用药安全线索',icon:'pill',measure:'按成分、产品、时间和适用信息追溯候选',design:'仅在明确使用的观察日运行固定规则，同一人同一规则只记一个候选，保留首条证据。',source:'amr',boundary:'候选不是已证实的滥用、不良反应或耐药；抗菌药记录不意味着本产品推荐其自主使用。'},
 {id:'missing',code:'RQ03',title:'没记录的日子，会怎样改变结论？',short:'缺失与敏感性',icon:'chart',measure:'分开未用、记不清与缺失，展示极端边界',design:'按仍应随访的患者日计算分母，归档之后不再增加应记录日；不把未知状态补成未用药。',source:'pro',boundary:'极端上下界不是置信区间；不能据此断定缺失机制或推广到总体。'},
 {id:'signals',code:'RQ04',title:'历史线索，经得起时序与否定检查吗？',short:'历史线索验证',icon:'signal',measure:'独立合成边界样例、来源核对与假设基率敏感性',design:'只使用截至分析日、演示窗口内的最近断言；核对明确否定、缺失和未来信息隔离。',source:'longitudinal',boundary:'窗口是工程演示参数，规则未验证临床筛查效能；基率计算使用研究者假设，不提供个体患病概率。'},
 {id:'trajectory',code:'RQ05',title:'评分降低，就能算作恢复吗？',short:'恢复轨迹',icon:'calendar',measure:'首末可用评分、观察机会与恢复事件分开',design:'同一合成事件中，仅比较已记录的首末有效自评分；保留起始日是否有评分及来源。',source:'rti-trajectories',boundary:'评分变化是描述性过程，不是药效或痊愈。没有预定义恢复事件与更长随访，不能估计恢复时间或复发率。'}
];
const study=()=>studies.find(s=>s.id===state.study)||studies[0];
const sourceLink=id=>{const s=sources.find(x=>x.id===id);return s?`<a href='${s.url}' target='_blank' rel='noopener noreferrer'>${esc(s.type)} · ${s.year} ↗</a>`:'';};
const header=(title,subtitle,action='')=>`<header class='workspaceHeader'><div><p class='eyebrow'>OUT-OF-CLINIC RESEARCH</p><h1>${title}</h1><p>${subtitle}</p></div><div class='headerActions'>${action}</div></header>`;
const button=(label,route,kind='secondaryAction',symbol='arrow')=>`<button class='${kind}' data-route='${route}'>${icon(symbol)}${label}</button>`;
const heading=(title,symbol,meta='')=>`<div class='sectionHeading'><div class='researchSectionTitle'><span>${icon(symbol)}</span><h2>${title}</h2></div>${meta}</div>`;
const foot=()=>`<p class='pageFoot'>${icon('shield')} 固定合成样例 · 方法与流程验证 · 不代表真实人群或临床效果</p>`;
const guarded=n=>n<5&&n!==0?'＜5':n;
function smallSample(){return `<section class='card smallSample'>${icon('shield')}<h2>当前队列不足5人</h2><p>聚合结果和导出已暂停。调整筛选后继续；独立教学样例仍可查看。</p></section>`;}
function filters(){
 return `<section class='researchFilters' aria-label='研究队列条件'><label>症状主题<select id='topic-filter'> <option value='all'>全部轻症主题</option>${E.topics.map(x=>`<option ${state.topic===x?'selected':''}>${x}</option>`).join('')}</select></label><label>样例产品类型<select id='category-filter'><option value='all'>全部产品类型</option>${E.categories.map(x=>`<option ${state.category===x?'selected':''}>${x}</option>`).join('')}</select></label><label>观察窗口<select id='window-filter'><option value='7' ${state.window_days===7?'selected':''}>开始后7天</option><option value='3' ${state.window_days===3?'selected':''}>开始后3天</option></select></label><span class='filterContext'>${icon('shield')}仅研究授权样例</span><button class='quietAction' data-action='reset-filters'>重置</button></section>`;
}
function stats(){
 const a=analysis(),hidden=a.n<5;
 const cards=[
 ['授权队列',hidden?'＜5':a.n,'人','60份合成记录中按授权与条件纳入'],
 ['患者日记录完整率',hidden?'隐藏':fmt(a.completeness_pct,'%'),'',hidden?'小样本隐藏':a.observed+' / '+a.expected+'个应记录日'],
 ['共用字段覆盖率',hidden?'隐藏':fmt(a.coverage.full_pct,'%'),'',hidden?'小样本隐藏':a.coverage.full+' / '+a.coverage.denominator+'个共用字段槽位'],
 ['有用药待核实线索',hidden?'隐藏':a.candidate_participants,'人','合成边界场景 · 不是滥用率']
 ];
 return `<div class='researchStats'>${cards.map(([name,value,unit,detail])=>`<section class='statCard'><small>${name}</small><strong>${value}<span>${unit}</span></strong><p>${detail}</p></section>`).join('')}</div>`;
}
function overview(){
 const a=analysis();
 return header('院外轻症研究总览','把日常健康记录，组织成有依据、可复现的研究问题。',button('研究依据','literature','quietAction','book'))+`
 <section class='researchHero'><div><span class='researchKicker'>PATIENT-GENERATED DATA · RESEARCH AGENT</span><h2>看见医院之外，<br>那些没有被连续记录的变化。</h2><p>关注轻症信息采集、自主用药情境与纵向线索。先回答数据是否足够、规则是否可靠，再讨论临床价值。</p><div class='heroActions'><button class='primaryAction' data-study='coverage'>${icon('chart')}进入分析工作台</button>${button('查看可复现流程','sciencepal','quietAction','flow')}</div></div><aside><span class='tag'>本次研究定位</span><h3>数据过程与方法验证</h3><dl><div><dt>观察对象</dt><dd>6类轻症主题 · 成年模拟记录</dd></div><div><dt>研究单元</dt><dd>参与者 / 病程 / 患者日</dd></div><div><dt>主要输出</dt><dd>字段覆盖、信息缺口、边界测试</dd></div><div><dt>当前数据</dt><dd>全量合成，未开展真实研究</dd></div></dl></aside></section>
 ${stats()}
 <div class='researchSectionIntro'><div><span class='eyebrow'>RESEARCH QUESTIONS</span><h2>从研究热点，落到可验证的问题</h2></div><span class='subtle'>检索更新：2026-10-18</span></div>
 <div class='questionGrid'>${studies.map(s=>`<article class='card questionCard'><div class='questionCode'>${icon(s.icon)}<span>${s.code}</span></div><h3>${s.title}</h3><p>${s.measure}</p><div class='questionSource'>${sourceLink(s.source)}</div><button class='textAction' data-study='${s.id}' aria-label='打开研究问题：${s.short}'>打开研究问题 ${icon('arrow')}</button></article>`).join('')}</div>
 <section class='card researchTakeaway'>${heading('从研究问题到参赛证据','flow')}<div class='evidenceColumns'><div><span class='researchKicker'>科学价值</span><h3>院外记录的信息缺口</h3><p>${sources.length}项研究与官方依据，${studies.length}个可验证问题；每项结果都有分母、出处和解释范围。</p></div><div><span class='researchKicker'>创新性 · 待验证假设</span><h3>把来源与时间带进对话</h3><p>以等时长对照、来源约束和历史消融，检验采集质量、成分理解与输出稳健性。</p></div><div><span class='researchKicker'>可行性</span><h3>从固定输入重跑结果</h3><p>本地计算、3组窗口与主题条件已运行；SciencePal任务包已备，平台核心执行待完成。</p></div></div><div class='cardActions'>${button('查看研究设计与赛事证据','design','secondaryAction','book')}</div></section>
 <section class='card researchTakeaway'>${heading('当前结果能支持什么','info')}<div class='takeawayGrid'><p><strong>可以验证</strong>授权过滤、分母计算、字段配对、规则证据和报告复现。</p><p><strong>尚不能回答</strong>真实滥用率、耐药率、疾病预测准确率或治疗效果。</p></div></section>${foot()}`;
}
function studyTabs(){return `<div class='studyTabs' role='group' aria-label='研究问题'>${studies.map(s=>`<button aria-pressed='${state.study===s.id}' data-study='${s.id}' class='${state.study===s.id?'active':''}'>${icon(s.icon)}<span>${s.short}</span></button>`).join('')}</div>`;}
function protocol(){
 const s=study();return `<section class='protocolStrip'><span>${s.code}</span><div><h2>${s.title}</h2><p>${s.design}</p></div>${sourceLink(s.source)}</section>`;
}
function numberCards(cards){
 return `<div class='analysisNumbers'>${cards.map(([label,value,detail])=>`<div><small>${label}</small><strong>${value}</strong><p>${detail}</p></div>`).join('')}</div>`;
}
function fieldBar(f,n){
 const first=f.first<5&&f.first!==0,full=f.full<5&&f.full!==0;
 return `<div class='fieldComparison'><div><strong>${f.label}</strong>${!f.comparable?"<span class='tag neutral'>纵向新增 · 不计入对照</span>":''}</div><div class='comparisonTrack'><i class='first' style='width:${!f.comparable||first?0:E.pct(f.first,n)}%'></i><i class='full' style='width:${full?0:E.pct(f.full,n)}%'></i></div><p><span>首次 ${f.comparable?guarded(f.first)+'/'+n:'不适用'}</span><span>窗口内 ${guarded(f.full)}/${n}</span></p></div>`;
}
function coverageView(){
 const a=analysis();if(a.n<5)return smallSample();
 return numberCards([
 ['首次描述覆盖率',fmt(a.coverage.first_pct,'%'),a.coverage.first+' / '+a.coverage.denominator+'个相同字段槽位'],
 ['连续记录覆盖率',fmt(a.coverage.full_pct,'%'),a.coverage.full+' / '+a.coverage.denominator+'个相同字段槽位'],
 ['覆盖差值',fmt(a.coverage.difference_pp,' pp'),'合成样例计算，尚非产品实测效果']
 ])+`<div class='researchTwoCols'><section class='card'>${heading('逐字段比较','chart',"<div class='chartLegend'><span class='first'>首次</span><span class='full'>窗口内</span></div>")}${a.coverage.by_field.map(f=>fieldBar(f,a.n)).join('')}<p class='subtle'>“可解释”指至少有一次明确记录；明确未知不补成已知。初始不可能存在的变化描述单列展示。</p></section><div class='stack'><section class='card'>${heading('配对记录溯源','calendar')}<div class='tableWrap'><table><thead><tr><th>合成病程</th><th>首次</th><th>窗口内</th><th>证据</th></tr></thead><tbody>${a.coverage.paired.slice(0,6).map(p=>`<tr><td>${p.id}</td><td>${p.first}/5</td><td>${p.full}/5</td><td><button class='tableAction' data-sample='${p.id}'>查看</button></td></tr>`).join('')}</tbody></table></div></section><section class='card methodCard'><h3>下一步如何做真实验证？</h3><p>预先定义字段和判定规则，用同一批病例比较自由记录与结构化追问；盲法双人标注，按参与者划分训练与测试。</p><p class='subtle'>本页没有执行语言模型，没有临床金标准，也不将额外记录时间带来的信息增量归因于AI。</p></section></div></div>`;
}
function medicationView(){
 const a=analysis();if(a.n<5)return smallSample();
 const rule=E.ruleDefinitions.find(r=>r.id===state.rule)||E.ruleDefinitions[0],found=a.candidates.filter(c=>c.rule===rule.id);
 return `<div class='ruleGrid'>${E.ruleDefinitions.map(r=>{
   const n=a.candidates.filter(c=>c.rule===r.id).length;
   return `<button class='ruleCard ${state.rule===r.id?'active':''}' data-rule='${r.id}'><span>${r.title}</span><strong>${guarded(n)}<small> 人</small></strong><p>${r.description}</p></button>`;
 }).join('')}</div><section class='card'>${heading(rule.title+' · 证据清单','pill',"<span class='tag orange'>候选，需核实</span>")}<p class='bodyCopy'>${rule.description}需要补充：${rule.missing}。</p>${found.length>=5?`<div class='tableWrap'><table><thead><tr><th>合成参与者</th><th>首条命中日期</th><th>触发依据</th><th>来源</th></tr></thead><tbody>${found.slice(0,8).map(c=>`<tr><td>${c.participant_id}</td><td>${c.date}</td><td>${c.facts.map(esc).join('；')}</td><td><button class='tableAction' data-sample='${c.participant_id}' data-source='${c.source_id}'>${c.source_id}</button></td></tr>`).join('')}</tbody></table></div>`:"<div class='noteBox'>当前规则的小单元不足5，证据清单隐藏；可调整筛选查看。</div>"}<div class='cardBottom'><p class='subtle'>同一人同一规则只计一次；不同规则可能重叠。数据专门包含边界场景，比例不能代表真实人群。</p>${rule.source?`<a href='${rule.source}' target='_blank' rel='noopener noreferrer'>规则依据 ↗</a>`:''}</div></section>`;
}
function missingView(){
 const a=analysis();if(a.n<5)return smallSample();
 const known=a.use.used+a.use.not_used,unknown=a.use.unknown+a.use.missing;
 return numberCards([
 ['仅已明确状态中的使用比例',fmt(E.pct(a.use.used,known),'%'),a.use.used+' / '+known+'个明确状态患者日'],
 ['全窗口的极端上下界',fmt(a.lower_use_pct,'%')+'—'+fmt(a.upper_use_pct,'%'),'未知全部未用 / 未知全部使用'],
 ['未明状态占应记录日',fmt(E.pct(unknown,a.expected),'%'),unknown+' / '+a.expected+'日，不等同未用']
 ])+`<div class='researchTwoCols'><section class='card'>${heading('把四种状态分开','chart')}<div class='statusStack' aria-label='用药记录状态分布'>${Object.entries(a.use).map(([key,n])=>`<span class='${key}' style='width:${E.pct(n,a.expected)}%' title='${useLabels[key]} ${n}日'></span>`).join('')}</div><div class='statusLegend'>${Object.entries(a.use).map(([key,n])=>`<div><i class='${key}'></i><span>${useLabels[key]}</span><strong>${guarded(n)}日</strong></div>`).join('')}</div><div class='rangeExplanation'><strong>为什么不直接报告一个比例？</strong><p>把${a.use.unknown}个“记不清”和${a.use.missing}个缺失日都当作未用，会得到${fmt(a.lower_use_pct,'%')}；排除它们，又会改变分母。上下界只是展示结论对未知状态的敏感程度。</p></div><p class='subtle'>不是置信区间，不进行症状插值，不据此证明缺失是随机的。</p></section><section class='card'>${heading('随访日与有效分母','calendar')}<div class='tableWrap'><table><thead><tr><th>观察日</th><th>应记录</th><th>已记录</th><th>完整率</th></tr></thead><tbody>${a.daily.map(d=>`<tr><td>第${d.day}日</td><td>${guarded(d.expected)}</td><td>${guarded(d.observed)}</td><td>${d.expected<5||d.observed<5?'隐藏':fmt(E.pct(d.observed,d.expected),'%')}</td></tr>`).join('')}</tbody></table></div><p class='subtle'>合成事件在用户标记结束后停止增加应记录日；当前${a.expected}日分母不机械等于${a.n}×${state.window_days}。</p></section></div>`;
}
function signalView(){
 const result=E.evaluateSignal(state.signal,state.signalWindow),labels={thirst:'口渴',urination:'排尿增多',weight:'非主动体重下降'},status={present:'明确自述',absent:'明确否定',missing:'未记录'};
 return `<div class='signalControls'><label>边界样例<select id='signal-case'>${E.signalCases.map(c=>`<option value='${c.id}' ${c.id===state.signal?'selected':''}>${c.title}</option>`).join('')}</select></label><label>演示窗口<select id='signal-window'><option value='28' ${state.signalWindow===28?'selected':''}>28天（演示参数）</option><option value='7' ${state.signalWindow===7?'selected':''}>7天（演示参数）</option></select></label><span class='tag neutral'>独立合成教学样例 · 不受队列筛选影响</span></div><div class='researchTwoCols'><section class='card'>${heading('截至2026-10-18的证据','signal')}<div class='signalVerdict ${result.status}'><small>规则检查结果</small><strong>${signalLabels[result.status]}</strong></div><div class='signalEvidence'>${result.evidence.map(e=>`<div><span class='assertion ${e.status}'>${status[e.status]}</span><div><h3>${labels[e.symptom]}</h3><p>${e.event?esc(e.event.text):'当前窗口没有可用记录'}</p><small>${e.event?e.event.date+' · 合成断言':''}</small></div></div>`).join('')}</div>${result.excluded.length?`<div class='noteBox spaced'>排除${result.excluded.length}条窗口外或分析日之后的信息：${result.excluded.map(e=>e.date).join('、')}。没有偷看后续信息。</div>`:''}</section><div class='stack'><section class='card'>${heading('知识条目与检查规则','book')}<p class='bodyCopy'>糖代谢相关资料中可见口渴、尿频和非主动体重下降。这里仅检查记录组合，诊断仍需要进一步检查。</p><ol class='methodList'><li>保留最近的明确肯定、否定或未知。</li><li>只使用分析截点之前、窗口内的信息。</li><li>未记录不补成否定，组合齐全也不输出疾病概率。</li></ol><a href='https://www.nhs.uk/conditions/type-2-diabetes/symptoms/' target='_blank' rel='noopener noreferrer'>NHS症状与诊断资料 ↗</a><p class='subtle'>28天和7天均为方法演示参数，不是该疾病的临床阈值。</p></section><section class='card'>${heading('固定边界测试','check')}<div class='fixtureResults'>${E.evaluateFixtures().map(t=>`<div><span>${E.signalCases.find(c=>c.id===t.id).title}</span><strong>${t.actual===t.expected?'通过':'不一致'}</strong></div>`).join('')}</div><p class='subtle'>只验证固定规则行为；不是临床敏感度、特异度或真实AI评测。</p></section></div></div>`;
}
function baseRatePanel(){
 const r=M.baseRate(state.prior,state.sensitivity,state.specificity),f=n=>n===null?'—':String(Math.round(n*10)/10);
 return `<section class='card researchTakeaway baseRatePanel'>${heading('历史预警也要回答：会产生多少误报？','chart',"<span class='tag neutral'>纯假设参数 · 数学敏感性演示</span>")}<p class='bodyCopy'>用固定10000人的假设人群说明基率的影响。下列参数由研究者假设，未从本项目、论文或真实疾病人群估计。</p><div class='assumptionControls'><label>目标结局基率（%）<input id='assumed-prior' type='number' min='0' max='100' step='0.1' value='${state.prior}'></label><label>假设敏感度（%）<input id='assumed-sensitivity' type='number' min='0' max='100' step='0.1' value='${state.sensitivity}'></label><label>假设特异度（%）<input id='assumed-specificity' type='number' min='0' max='100' step='0.1' value='${state.specificity}'></label></div><div class='cardActions assumptionActions'><button class='primaryAction' data-action='calculate-base-rate'>按当前假设计算</button><span class='subtle'>修改参数后计算；导出保存计算时的假设。</span></div><div class='assumptionOutput' aria-live='polite'><div><span>预期真阳性</span><strong>${f(r.expected_true_positive)}</strong></div><div><span>预期假阳性</span><strong>${f(r.expected_false_positive)}</strong></div><div><span>假设阳性预测值</span><strong>${f(r.ppv_pct)}${r.ppv_pct===null?'':'%'}</strong></div><div><span>每千人预期提示</span><strong>${f(r.alerts_per_1000)}</strong></div></div><p class='subtle'>预期漏提示${f(r.expected_false_negative)}人，预期真阴性${f(r.expected_true_negative)}人。数量是数学期望，可含小数；若没有阳性提示，阳性预测值无定义。</p><p class='subtle'>病例对照样本中的病例占比不代表目标人群基率。这个演示不表示本项目具有上述敏感度或特异度，也不对个人估计疾病概率。</p><div class='cardActions'><button class='quietAction' data-action='export-base-rate'>下载当前假设与计算</button><button class='quietAction' data-open-plan='early-signals'>${icon('book')}查看早期线索验证方案</button></div><div class='questionSource'>${sourceLink('diagnostic-window')}</div></section>`;
}
function signalStudy(){return signalView()+baseRatePanel();}
function calculateBaseRate(){
 const ids=['assumed-prior','assumed-sensitivity','assumed-specificity'];
 const values=ids.map(id=>document.getElementById(id)?.value??'');
 if(values.some(v=>v.trim()===''||!Number.isFinite(Number(v))||Number(v)<0||Number(v)>100)){toast('请填写0至100之间的假设百分比。');return false;}
 [state.prior,state.sensitivity,state.specificity]=values.map(Number);render();return true;
}
function trajectoryView(){
 const a=M.trajectory(rows());if(a.participants<5)return smallSample();
 const labels={decrease:'首末评分降低',same:'首末评分相同',increase:'首末评分升高'};
 return numberCards([['有首末可用评分',a.paired+' / '+a.participants,'至少两个有效观察日'],['配对中有起始日评分',a.baseline_observed+' / '+a.paired,'其余起点为后续首个可用日'],['可验证恢复事件','未定义','归档或评分降低不能补为痊愈']])+`<div class='researchTwoCols'><section class='card'>${heading('描述变化，保留观察机会','chart')}<div class='qualityRows'>${Object.entries(a.directions).map(([key,n])=>`<div><span>${labels[key]}</span><strong>${guarded(n)}人</strong></div>`).join('')}<div><span>窗口内已归档的配对事件</span><strong>${guarded(a.archived_in_window)}人</strong></div><div><span>评分不足，不能配对</span><strong>${guarded(a.insufficient)}人</strong></div></div><p class='subtle'>分母是有配对记录的合成事件，不是全部人群；小于5的细分隐藏。不连接缺失日，不对没有记录的改善作插值。</p></section><section class='card'>${heading('研究恢复，需要哪些额外证据','book')}<ul class='methodList'><li>先定义可验证恢复事件及是否由用户确认。</li><li>结束观察但未确认恢复时，保留删失状态。</li><li>比较轨迹时控制起点、主题与观察时长。</li><li>同一人的多段病程放在同一数据划分中。</li></ul><p class='subtle'>当前只做首末描述，没有恢复中位时间、复发率、潜在轨迹分类或药物效果分析。</p>${sourceLink('rti-trajectories')}</section></div><section class='card researchTakeaway'>${heading('配对依据示例','calendar',"<span class='tag neutral'>当前队列前6条可配对合成记录</span>")}<div class='tableWrap'><table><thead><tr><th>事件</th><th>首次可用评分</th><th>末次可用评分</th><th>未测评分日</th><th>末次依据</th></tr></thead><tbody>${a.records.slice(0,6).map(r=>`<tr><td>${r.participant_id}</td><td>第${r.first_day}日 · ${r.first_score}分</td><td>第${r.last_day}日 · ${r.last_score}分</td><td>${r.unmeasured_score_days}</td><td><button class='tableAction' data-sample='${r.participant_id}' data-source='${r.last_source_id}'>${r.last_source_id}</button></td></tr>`).join('')}</tbody></table></div><div class='cardActions'><button class='quietAction' data-action='export-trajectory'>${icon('download')}导出当前轨迹分析</button></div></section>`;
}
function workbench(){
 const views={coverage:coverageView,medication:medicationView,missing:missingView,signals:signalStudy,trajectory:trajectoryView};
 return header('研究分析工作台','每个结果都可以回到问题、分母和原始依据。',button('运行与复现','sciencepal','quietAction','flow'))+studyTabs()+protocol()+(state.study==='signals'?'':filters())+views[state.study]()+`<div class='interpretationNote'>${icon('info')}${study().boundary}</div>`+foot();
}
function cohortPage(){
 const a=analysis(),eligible=E.select({},state.sampleConsent).length;
 const productRows=a.n>=5?a.n&&rows().flatMap(s=>s.observations.flatMap(o=>o.products)):[];
 const known=productRows.filter(p=>p.ingredients.length).length;
 return header('研究队列与数据质量','先确认数据适合回答问题，再计算结果。',`<button class='quietAction' data-action='export-csv'>${icon('download')}导出合成患者日</button>`)+filters()+
 `<div class='cohortFlow'><div><small>固定样例库</small><strong>60</strong><span>份合成病程</span></div><b>→</b><div><small>研究授权可用</small><strong>${eligible}</strong><span>未授权记录被排除</span></div><b>→</b><div><small>筛选后纳入</small><strong>${a.n<5?'＜5':a.n}</strong><span>主题、产品与观察窗口</span></div></div>`+
 (a.n<5?smallSample():`<div class='researchTwoCols'><section class='card'>${heading('症状主题构成','people')}${E.topics.map(t=>{const n=rows().filter(s=>s.topic===t).length;return `<div class='researchBar'><span>${t}</span><div><i style='width:${n>=5?E.pct(n,a.n):0}%'></i></div><strong>${guarded(n)}人</strong></div>`;}).join('')}<p class='subtle'>固定样例覆盖六类轻症主题，并非人群抽样；不能据此描述疾病谱。</p></section><section class='card'>${heading('质量检查与适用性','shield')}<div class='qualityRows'><div><span>患者日可用</span><strong>${a.observed}/${a.expected}</strong></div><div><span>成分可归一的产品记录</span><strong>${known}/${productRows.length}</strong></div><div><span>有来源ID的观察记录</span><strong>${a.observed}/${a.observed}</strong></div><div><span>原始图片进入研究</span><strong>0份 · 独立授权关闭</strong></div></div><p class='subtle'>记录完整不代表内容真实；自评分尚未验证为临床结局量表。小单元抑制是演示策略，不是匿名保证。</p></section></div>`)+
 `<section class='card researchTakeaway'>${heading('研究设计需保留的偏差','info')}<div class='biasGrid'><div><strong>选择偏差</strong><p>愿意使用、愿意授权的人群可能不同。</p></div><div><strong>报告与回忆偏差</strong><p>“没有记录”与“没有发生”分开。</p></div><div><strong>额外关注效应</strong><p>追问和提醒本身可能改变记录与行为。</p></div></div></section>`+foot();
}

function traceChart(subject){
 const values=subject.observations.filter(o=>o.score!==null),maxDay=Math.max(subject.expected_days-1,1);
 if(!values.length)return "<p class='subtle'>当前样例没有可用自评分，不补造曲线。</p>";
 const points=values.map(o=>({x:35+o.day*285/maxDay,y:140-o.score*11,obs:o}));
 let path='';points.forEach((point,i)=>{path+=(i===0||point.obs.day!==points[i-1].obs.day+1?'M':'L')+point.x+','+point.y+' ';});
 return `<svg class='caseTrace' viewBox='0 0 345 180' role='img' aria-label='本段合成记录的不适自评分，仅连接连续观察日'>${[0,5,10].map(v=>`<line x1='30' y1='${140-v*11}' x2='325' y2='${140-v*11}'/><text x='12' y='${144-v*11}'>${v}</text>`).join('')}<path d='${path}'/>${points.map(p=>`<circle cx='${p.x}' cy='${p.y}' r='3.4'><title>${p.obs.date} · ${p.obs.score}分</title></circle>`).join('')}${Array.from({length:subject.expected_days},(_,day)=>`<text x='${35+day*285/maxDay}' y='166' text-anchor='middle'>${day+1}日</text>`).join('')}</svg><p class='subtle'>个人自述评分，尚非验证量表；未记录日不连线，不由变化推断药效。</p>`;
}

function examples(){
 const selected=rows(),s=selected.find(x=>x.id===state.sample)||selected[0];
 if(!s)return header('记录与证据溯源','当前筛选没有可用样例。')+smallSample()+foot();
 if(selected.length<5)return header('记录与证据溯源','当前小队列不展示个体明细。')+smallSample()+foot();
 const found=E.candidates([s]);
 return header('记录与证据溯源','人工构造的原文与字段配对；不冒充模型提取结果。')+
 `<div class='exampleControls'><label>合成病程<select id='sample-select'>${selected.map(x=>`<option value='${x.id}' ${s.id===x.id?'selected':''}>${x.id} · ${x.topic}</option>`).join('')}</select></label><span class='tag neutral'>合成自述 · 只读</span><span class='tag'>${s.observations.length}/${s.expected_days}个患者日</span></div>
 <div class='researchTwoCols'><section class='card'>${heading(s.id+' · '+s.topic,'calendar')}<div class='sourceTimeline'>${s.observations.map(o=>`<article id='evidence-${o.medication_evidence.source_id}' data-observation-source='${o.source_id}' tabindex='-1' class='${[o.source_id,o.medication_evidence.source_id].includes(state.focusSource)?'selectedEvidence':''}'><time>${o.date} <span>${o.source_id}</span></time><p>${esc(o.source_text)}</p><div class='sourceFields'>${E.fields.map(f=>`<span class='${o.known[f.id]?'known':'unknown'}'>${f.label} · ${o.known[f.id]?'已记录':'未明确'}</span>`).join('')}</div><div class='medicationEvidence'><small>结构化用药自述 · ${o.medication_evidence.source_id}</small><p>${esc(o.medication_evidence.text)}</p></div><small>用药状态：${useLabels[o.use]}${o.image_available?' · 有图片元数据，原图未获研究授权':''}</small></article>`).join('')}</div></section><div class='stack'><section class='card'>${heading('本段记录的变化','chart')}${traceChart(s)}</section><section class='card'>${heading('从记录到规则的连接','pill')}${found.length?found.map(c=>`<div class='sourceCandidate'><h3>${E.ruleDefinitions.find(r=>r.id===c.rule).title}</h3><p>${c.facts.map(esc).join('；')}</p><small>${c.date} · ${c.source_id}</small></div>`).join(''):"<p class='bodyCopy'>当前固定规则未产生候选；这不表示没有健康风险。</p>"}<p class='subtle'>来源、字段和规则版本一起保留，修正原文或窗口后重新计算。</p></section><section class='card methodCard'><h3>不从轨迹推断药效</h3><p>症状自评分的变化，与使用某种产品在时间上相邻，不足以证明因果。需要对照、混杂处理和可靠结局标签。</p>${button('查看研究设计','literature','quietAction','book')}</section></div></div>`+foot();
}
const dictionary={schema_version:'1.0',data_origin:'synthetic',units:{participant:'独立合成参与者',episode:'本版每人一段事件',patient_day:'仍应记录的一日',common_field_slot:'5个共用字段之一'},statuses:useLabels,fields:E.fields,
  provenance:['source_id','source_type','observed_date','record_version','consent_version','rule_version','knowledge_version','input_sha256'],
  excluded:['姓名与联系方式','身份映射','用户端真实对话与照片','未授权研究记录','分析截点后的知识匹配事件'],
  caveats:['自评分不是已验证的临床结局量表','缺失、未知与否定分开','影像用途需独立授权','小单元抑制不能替代服务端权限与审计']};
dictionary.proposed_event_mapping={status:'draft_not_integrated',fields:[
 {id:'raw_phrase',label:'患者原话',purpose:'保留原始表述与证据ID'},
 {id:'concept_candidate',label:'概念候选',purpose:'允许多个候选与无法映射'},
 {id:'assertion',label:'断言与确认',purpose:'肯定、否定、未知、用户更正分开'},
 {id:'event_time',label:'发生与记录时间',purpose:'不把追记时间当成症状起始时间'},
 {id:'drug_relation',label:'用药时间与关系',purpose:'保留先后与关系未知，不自动归因'},
 {id:'mapping_version',label:'词表与映射版本',purpose:'未来核对合法授权的词表、版本与审阅来源'}]};
function eventMappingPanel(){
 return `<section class='card researchTakeaway'>${heading('从患者原话到研究事件','database',"<span class='tag neutral'>字段草案 · 未接入术语服务</span>")}<p class='bodyCopy'>患者仍通过对话表达。科研接口保留原话与候选映射的差异，不能把系统猜测写成已确认医学编码。</p><div class='tableWrap'><table><thead><tr><th>字段</th><th>用途</th></tr></thead><tbody>${dictionary.proposed_event_mapping.fields.map(f=>`<tr><td>${f.label}<br><small>${f.id}</small></td><td>${f.purpose}</td></tr>`).join('')}</tbody></table></div><p class='subtle'>当前没有SNOMED CT、MedDRA服务或标准兼容声明；此草案已随数据字典导出，不包含受限完整词表。</p><div class='planSources'>${sourceLink('patient-language')}${sourceLink('ade-terminology')}</div></section>`;
}
function foundation(){
 return header('数据底座与研究治理','让每一次提取、修改、授权和计算都有出处。',`<button class='quietAction' data-action='export-dictionary'>${icon('download')}下载数据字典</button>`)+
 `<div class='researchTwoCols'><section class='card'>${heading('可追溯的数据层次','database')}<div class='dataLayers'>${[
 ['01','原始依据','自述原文与附件引用，保存事件时间和来源；身份映射分开。'],
 ['02','结构化事实','肯定、否定、未知、缺失分开；原文与字段的版本可追溯。'],
 ['03','用途与授权','研究使用默认排除；影像独立授权，不默认共享给医生。'],
 ['04','研究快照','冻结队列、分母、字段、规则与知识版本，计算输入SHA-256。'],
 ['05','分析产物','本地参考计算或SciencePal实际运行；报告需与输入快照匹配。']
 ].map(([id,title,description])=>`<div class='dataLayer'><span>${id}</span><div><strong>${title}</strong><p>${description}</p></div></div>`).join('')}</div></section><div class='stack'><section class='card'>${heading('当前授权边界','shield')}<div class='qualityRows'><div><span>研究可用样例</span><strong>${E.select({},state.sampleConsent).length}/60</strong></div><div><span>来自用户端的真实文字或照片</span><strong>0条</strong></div><div><span>原始图片研究</span><strong>默认关闭</strong></div><div><span>固定样例S001</span><strong>${state.sampleConsent?'演示授权开启':'演示授权关闭'}</strong></div></div><p class='subtle'>跨窗口只联动S001的合成授权开关，不读取用户健康内容。真实服务仍需身份、用途、撤回传播与访问审计。</p></section><section class='card'>${heading('数据质量不止完整率','check')}<ul class='methodList'><li>检查同日重复与修改版本，不重复累计患者日。</li><li>核实产品身份、成分与剂型，不按类别推断剂量。</li><li>检查缺失是否集中于特定主题或后期观察日。</li><li>真实研究预先定义分析计划和数据适用性。</li></ul>${sourceLink('rwd')}</section></div></div>`+eventMappingPanel()+foot();
}
function sciencepal(){
 const a=analysis();
 return header('运行、导入与复现','本地计算可执行，真实平台产物需要单独核验。',`<span class='tag ${state.report?'':'neutral'}'>${state.report?'已有当前快照报告':'尚无当前快照报告'}</span>`)+
 `<div class='runModeGrid'><section class='card'>${heading('本地参考分析','chart',"<span class='tag neutral'>实际计算 · 不是平台回放</span>")}<p class='bodyCopy'>对当前合成队列计算字段覆盖、患者日缺失和用药候选，生成与输入哈希绑定的报告。</p><div class='runSteps'>${['冻结授权与筛选条件','计算质量、覆盖和规则候选','绑定输入哈希与版本','保存可下载报告'].map((x,i)=>`<div><span>${i+1}</span>${x}</div>`).join('')}</div><div class='cardActions'><button class='primaryAction' data-action='run-local' ${state.busy||a.n<5?'disabled':''}>${icon('flow')}${state.busy?'正在计算':'运行本地分析'}</button><button class='quietAction' data-action='export-input' ${a.n<5?'disabled':''}>${icon('download')}导出分析输入</button></div></section>
 <section class='card platformCard'>${heading('SciencePal执行与结果导入','flow',"<span class='tag neutral'>平台尚未连接</span>")}<p class='bodyCopy'>把输入和项目内的Python参考脚本放入SciencePal实际执行，再导入输出的JSON报告。</p><div class='runCommand'>python run_analysis.py health-research-input.json<br>--platform SciencePal<br>--run-url &lt;真实运行链接&gt;</div><p class='subtle'>导入会校验输入哈希、知识版本和统计值。文件里的平台名称是来源声明，不能单独证明执行地点。</p><div class='cardActions'><label class='fileAction'>${icon('upload')}导入结果JSON<input id='report-import' type='file' accept='.json,application/json'></label><button class='quietAction' data-action='export-template'>下载报告契约</button><a class='quietAction' href='run_analysis.py' download='run_analysis.py'>下载参考脚本</a></div></section></div>
 ${state.runError?`<div class='analysisError' role='alert'>${esc(state.runError)}</div>`:''}
 ${state.report?reportView():`<section class='card reportEmpty'>${icon('book')}<h2>结果将和研究快照一起保存</h2><p>当前队列${a.n<5?'不足5':a.n}人，观察窗口${state.window_days}天。更改筛选或研究授权会使已有报告失效。</p></section>`}
 <section class='card researchTakeaway'>${heading('SciencePal核心研究任务包','flow',"<span class='tag neutral'>材料已备 · 平台尚待实跑</span>")}<p class='bodyCopy'>包内包含固定默认48人输入、参考分析、窗口敏感性及轨迹与基率脚本、研究方案和本地对照结果。请在SciencePal执行代码、核对文献和统计、保存真实日志，再将报告导回本页。此处下载的固定包不随当前队列筛选变化；自定义队列请另导出当前输入。</p><div class='cardActions'><a class='primaryAction' href='materials/sciencepal-research-pack.zip' download>${icon('download')}下载固定复现包 ZIP</a><a class='quietAction' href='materials/SCIENCEPAL_TASK.md' download>下载平台任务说明</a><a class='quietAction' href='https://sciencepal.ai/help' target='_blank' rel='noopener noreferrer'>SciencePal官方使用说明 ↗</a></div><p class='subtle'>平台承担文献核验、真实代码执行和结果复核；只生成介绍或润色文案不满足海报的核心使用要求。</p></section>
 <section class='card researchTakeaway'>${heading('赛事中需要提交的真实证据','check')}<div class='takeawayGrid'><p><strong>平台运行</strong>可访问的SciencePal项目或会话、执行日志和原始结果文件。</p><p><strong>可复现材料</strong>冻结输入、参考脚本、数据字典、输入哈希、版本与局限说明。</p></div></section>`+foot();
}
function reportView(){
 const r=state.report,m=r.metrics;
 return `<section class='card reportCard'>${heading('当前研究快照报告','book',`<span class='tag'>${esc(r.platform)} · 合成分析</span>`)}<div class='reportSummary'><div><span>参与者</span><strong>${m.participants}人</strong></div><div><span>患者日完整率</span><strong>${fmt(m.completeness_pct,'%')}</strong></div><div><span>覆盖率差值</span><strong>${fmt(m.coverage_difference_pp,' pp')}</strong></div><div><span>候选参与者</span><strong>${m.medication_candidate_participants}人</strong></div></div><dl class='reportMetadata'><div><dt>RUN ID</dt><dd>${esc(r.run_id)}</dd></div><div><dt>输入SHA-256</dt><dd>${esc(r.input_sha256)}</dd></div><div><dt>代码 / 知识版本</dt><dd>${esc(r.code_version)} / ${esc(r.knowledge_version)}</dd></div><div><dt>来源状态</dt><dd>${r.platform==='local-browser'?'本页实际计算':'文件声明的执行来源；统计已核对，平台身份未认证'}</dd></div></dl>${r.run_url?`<a href='${esc(r.run_url)}' target='_blank' rel='noopener noreferrer'>查看声明的运行链接 ↗</a>`:''}<div class='cardActions'><button class='primaryAction' data-action='export-report'>${icon('download')}下载当前报告</button></div></section>`;
}
function literature(){
 const topicOf=s=>s.topic||({dialogue:'dialogue',pro:'evaluation',longitudinal:'dialogue',multimodal:'evaluation',amr:'medication',rwd:'evaluation'}[s.id]);
 const visible=sources.filter(s=>state.sourceScope==='all'||(state.sourceScope==='latest'?s.round===2:state.sourceScope==='new'?P.sources.some(n=>n.id===s.id):topicOf(s)===state.sourceScope));
 const scopes=[['latest','本轮新增 · '+P.sources.filter(s=>s.round===2).length],['new','增补研究 · '+P.sources.length],['all','全部依据 · '+sources.length],['dialogue','对话与理解'],['medication','院外用药'],['followup','随访与负担'],['longitudinal','纵向表型'],['evaluation','评估方法'],['agents','可执行科研']];
 return header('研究依据与验证计划','每项来源说明研究设计、项目用途与不可外推的范围。',button('查看研究设计','design','quietAction','book'))+
 `<section class='card researchPosition'>${heading('本项目最适合的科学切口','book')}<h2>能否更完整地还原院外轻症过程，并保留可核实的自主用药情境？</h2><p>核心验证先聚焦信息质量和时序证据；“大病前期症状”只做有来源的线索匹配与边界测试。没有真实结局标签时，不展示预测准确率。</p></section>
 <div class='sourceFilters' role='group' aria-label='研究来源分类'>${scopes.map(([id,label])=>`<button data-source-scope='${id}' aria-pressed='${state.sourceScope===id}'>${label}</button>`).join('')}</div><p class='sourceCount' role='status'>当前${visible.length}项 · 检索截至2026-10-18 · 较早研究已标注为问题或方法基础</p>
 <div class='literatureGrid'>${visible.map(s=>`<article class='card literatureCard'><span class='researchKicker'>${s.year} · ${s.type}</span><h3>${s.title}</h3><p>${s.finding}</p><div><small>转化为项目设计</small><p>${s.translation}</p></div><p class='subtle'>${s.limit}</p><a href='${s.url}' target='_blank' rel='noopener noreferrer'>原始来源 ↗</a></article>`).join('')}</div>
 <section class='card'>${heading('下一阶段验证协议','check')}<div class='tableWrap'><table><thead><tr><th>研究问题</th><th>验证设计</th><th>报告内容</th></tr></thead><tbody><tr><td>采集是否更完整</td><td>同病例配对；进一步做等时长随机比较</td><td>预定义字段覆盖、负担与错误；双人盲评</td></tr><tr><td>用药线索是否可靠</td><td>明确产品与说明、人工构造边界、独立核实</td><td>证据引用、误报与信息不足处理</td></tr><tr><td>缺失如何影响分析</td><td>按活跃患者日分母，报告未知与缺失</td><td>完整病例与极端边界，主题分层</td></tr><tr><td>知识匹配是否稳健</td><td>按时间截点评估，包含否定与未来信息</td><td>规则一致性，不冒充临床筛查性能</td></tr></tbody></table></div><p class='subtle'>当前页面不声称已经完成真实受试者研究、模型评测或伦理审查。真实数据研究需要另行设计与实施。</p></section>`+foot();
}
function design(){
 const p=P.protocols.find(x=>x.id===state.plan)||P.protocols[0];
 const experiments=window.ResearchExperiments;
 return header('研究设计与验证','从已有计算基线，走向可比较、可复核的实验。',`<button class='quietAction' data-action='export-protocol'>${icon('download')}导出当前验证方案</button>`)+
 `<div class='studyTabs designTabs' role='group' aria-label='验证方案'>${P.protocols.map(x=>`<button data-plan='${x.id}' aria-pressed='${x.id===p.id}' class='${x.id===p.id?'active':''}'><span>${x.code}</span>${x.short}</button>`).join('')}</div>
 <section class='card planHero'><span class='researchKicker'>${p.code} · 拟开展的验证 · 尚无受试者或模型结果</span><h2>${p.question}</h2><p>${p.hypothesis}</p><div class='planSources'>${p.sources.map(sourceLink).join('')}</div></section>
 <div class='researchTwoCols planDetails'><section class='card'>${heading('比较什么，如何比较','flow')}<dl class='planDefinition'><div><dt>研究单元</dt><dd>${p.unit}</dd></div><div><dt>对照与控制</dt><dd>${p.control}</dd></div><div><dt>分析约定</dt><dd>${p.analysis}</dd></div></dl></section><section class='card'>${heading('预先定义要观察的结果','chart')}<dl class='planDefinition'><div><dt>主要指标</dt><dd>${p.primary}</dd></div><div><dt>次要与解释指标</dt><dd>${p.secondary}</dd></div><div><dt>当前实现</dt><dd>${p.status}</dd></div></dl></section></div>
 <section class='card sensitivityCard'>${heading('已有基线：观察窗口敏感性','chart',"<span class='tag neutral'>本地Python已运行 · 合成数据</span>")}<p class='bodyCopy'>同一份默认48人冻结输入，分别限制观察窗口和主题。下表是随包保存的固定结果，不随当前界面筛选变化。</p><div class='tableWrap'><table><thead><tr><th>条件</th><th>人数</th><th>患者日完整率</th><th>首次 / 窗口字段覆盖</th><th>覆盖差值</th></tr></thead><tbody>${experiments.conditions.map(c=>{const m=c.metrics;return c.suppressed?`<tr><td>${c.label}</td><td colspan='4'>小于5人，隐藏聚合</td></tr>`:`<tr><td>${c.label}</td><td>${m.participants}</td><td>${m.observed_patient_days}/${m.expected_patient_days} · ${m.completeness_pct}%</td><td>${m.first_field_coverage_pct}% / ${m.longitudinal_field_coverage_pct}%</td><td>${m.coverage_difference_pp} pp</td></tr>`;}).join('')}</tbody></table></div><p class='subtle'>这组样例在3天和7天时的共同字段覆盖均为97.9%，延长窗口未增加共同字段。患者日完整率的变化还受到分母影响；不能归因于AI或据此选择真实随访时长。</p><div class='cardActions'><button class='quietAction' data-action='export-experiments'>下载固定实验结果JSON</button><a class='quietAction' href='run_experiments.py' download>下载实验脚本</a></div></section>
 <section class='card researchTakeaway'>${heading('与赛事三项评审维度的对应','check',"<span class='tag neutral'>依据用户提供的海报 · 未公布权重</span>")}<div class='evidenceColumns'><div><span class='researchKicker'>科学价值</span><h3>清晰问题与可检验终点</h3><p>院外轻症的记录质量、成分理解和随访负担。用字段与任务结果验证，保留阴性结果及缺失情况。</p></div><div><span class='researchKicker'>创新性</span><h3>让AI参与采集与研究</h3><p>拟比较定向追问、历史检索和来源约束的贡献；SciencePal执行分析与复核。未验证前将创新表述为假设。</p></div><div><span class='researchKicker'>可行性</span><h3>可运行、可展示、可复现</h3><p>本地真实计算、输入哈希、版本和报告校验已具备。平台实际执行、临床标签与模型评测仍需分别完成。</p></div></div></section>
 <section class='card researchTakeaway'>${heading('SciencePal必须进入核心工作','flow',"<span class='tag neutral'>尚待平台执行</span>")}<ol class='executionList'><li><strong>核验问题与来源</strong><span>检查${P.sources.length}项增补研究是否支持拟定指标，记录采用与排除理由。</span></li><li><strong>执行研究计算</strong><span>对冻结输入运行参考分析与三条件实验，产出报告、CSV和真实命令日志。</span></li><li><strong>复核并回到产品</strong><span>检查差异、分母与失败情况；把真实生成的报告导入科研端，并保存平台可访问链接。</span></li></ol><div class='cardActions'><a class='primaryAction' href='materials/sciencepal-research-pack.zip' download>${icon('download')}下载固定SciencePal任务包</a>${button('运行与导入','sciencepal','quietAction','arrow')}</div><p class='subtle'>SciencePal实质执行是海报要求；任务包、本地报告或来源声明均不能代替真实平台使用证据。</p></section>
 <section class='card researchTakeaway'>${heading('演示与提交准备','book')}<div class='submissionRows'><div><strong>项目基本信息</strong><span>研究问题、目标用户与场景已定义；团队信息待填写。</span><em>部分已备</em></div><div><strong>可运行作品链接</strong><span>本地两端可展示；SciencePal真实项目或工作流链接待补。</span><em>待平台实跑</em></div><div><strong>3—5分钟演示 · 不超过5页说明</strong><span>建议4分钟：问题40秒、对话与依据60秒、分析与复现100秒、边界与计划40秒。</span><em>待录制整理</em></div><div><strong>原创性与资源使用声明</strong><span>列明模型、代码、数据、API与外部资料；区分既有成果与比赛期间贡献。</span><em>待团队核对</em></div></div><p class='subtle'>代码、技术报告、Agent配置、工作流导出和用户测试材料为海报鼓励提交项。页面状态反映当前交付，不代表已经提交或通过评审。</p></section>`+foot();
}
const navs=[['overview','home','研究总览','总览'],['workbench','chart','分析工作台','分析'],['design','check','研究设计','设计'],['cohort','people','队列与质量','队列'],['examples','calendar','记录溯源','溯源'],['foundation','database','数据底座','底座'],['sciencepal','flow','SciencePal运行','运行'],['literature','book','研究依据','依据']];
const pages={overview,workbench,design,cohort:cohortPage,examples,foundation,sciencepal,literature};
function render(){
 document.getElementById('nav').innerHTML=navs.map(([id,symbol,label,short])=>`<button data-route='${id}' aria-label='${label}' class='${state.route===id?'active':''}' ${state.route===id?"aria-current='page'":''}>${icon(symbol)}<span class='navLong'>${label}</span><span class='navShort' aria-hidden='true'>${short}</span></button>`).join('');
 main.dataset.view=state.route;main.innerHTML=(pages[state.route]||overview)();
 root.querySelectorAll('[data-icon]').forEach(el=>el.innerHTML=icon(el.dataset.icon));
}
function go(route){state.route=pages[route]?route:'overview';render();window.scrollTo({top:0,behavior:'instant'});main.focus({preventScroll:true});}
function invalidate(){state.epoch++;state.report=null;state.reportInput=null;state.busy=false;state.runError=null;}
let toastTimer;
function toast(text){const el=document.getElementById('toast');el.textContent=text;el.classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>el.classList.remove('visible'),3600);}
function download(name,value,type='application/json'){
 const content=typeof value==='string'?value:JSON.stringify(value,null,2);
 const url=URL.createObjectURL(new Blob([content],{type})),a=document.createElement('a');a.href=url;a.download=name;a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);
}
async function sha(input){const digest=await crypto.subtle.digest('SHA-256',new TextEncoder().encode(E.canonicalStringify(input)));return Array.from(new Uint8Array(digest),x=>x.toString(16).padStart(2,'0')).join('');}
async function runLocal(){
 if(analysis().n<5||state.busy)return;
 const epoch=++state.epoch,input=E.snapshot(config(),state.sampleConsent);state.busy=true;state.runError=null;render();
 try{const hash=await sha(input);const report=E.makeReport(input,hash);if(epoch!==state.epoch)return;state.report=report;state.reportInput=input;toast('本地分析完成，报告已绑定当前输入快照。');}
 catch(error){if(epoch===state.epoch)state.runError='分析未完成：'+error.message;}
 finally{if(epoch===state.epoch){state.busy=false;render();}}
}
async function importReport(file){
 if(!file)return;
 const epoch=state.epoch,input=E.snapshot(config(),state.sampleConsent);
 try{
  if(input.subjects.length<5)throw new Error('当前队列不足5人，请先调整筛选。');
  if(file.size>1024*1024)throw new Error('报告应为1MB以内的JSON文件。');
  const r=JSON.parse(await file.text()),hash=await sha(input);
  if(epoch!==state.epoch){toast('输入已变化，请重新选择报告。');return;}
  if(r.schema_version!=='1.0'||r.data_origin!=='synthetic')throw new Error('报告版本或数据来源不符合本演示契约。');
  if(!['local-browser','local-python','SciencePal'].includes(r.platform))throw new Error('平台来源声明不在允许范围。');
  if(r.code_version!==E.VERSION||E.canonicalStringify(r.config)!==E.canonicalStringify(input.config))throw new Error('代码版本或队列定义不匹配。');
  if(typeof r.run_id!=='string'||!r.run_id.length||r.run_id.length>120)throw new Error('报告缺少有效的run_id。');
  if(r.input_sha256!==hash)throw new Error('输入哈希不匹配。队列、授权或观察窗口可能已变化。');
  if(r.knowledge_version!==E.KNOWLEDGE_VERSION||r.rule_version!==E.RULE_VERSION||r.data_version!==E.DATA_VERSION)throw new Error('知识、规则或数据版本不一致。');
  if(r.run_url){const url=new URL(r.run_url);if(url.protocol!=='https:')throw new Error('运行链接必须是HTTPS。');if(r.platform==='SciencePal'&&!(url.hostname==='sciencepal.ai'||url.hostname.endsWith('.sciencepal.ai')))throw new Error('SciencePal来源需提供其域名内的运行链接。');}
  if(r.platform==='SciencePal'&&!r.run_url)throw new Error('SciencePal声明需附可核实运行链接。');
  const expected=E.makeReport(input,hash);
  if(!r.metrics||Object.entries(expected.metrics).some(([key,value])=>value===null?r.metrics[key]!==null:typeof r.metrics[key]!=='number'||Math.abs(r.metrics[key]-value)>0.000001))throw new Error('统计结果与当前固定输入的参考计算不一致。');
  state.report=r;state.reportInput=input;state.runError=null;toast('报告已通过输入与统计一致性检查；平台来源仍需人工核验。');render();
 }catch(error){if(epoch===state.epoch){state.runError='导入失败：'+error.message;render();}}
}
async function exportInput(){
 const input=E.snapshot(config(),state.sampleConsent);if(input.subjects.length<5){toast('当前队列不足5人，禁止导出。');return;}
 download('health-research-input.json',input);toast('已导出固定合成输入，可与Python参考脚本一起在SciencePal运行。');
}
async function exportTrajectory(){
 const input=E.snapshot(config(),state.sampleConsent);if(input.subjects.length<5){toast('当前队列不足5人，禁止导出。');return;}
 const epoch=state.epoch;
 try{const hash=await sha(input);if(epoch!==state.epoch){toast('队列已改变，请重新导出。');return;}download('synthetic-trajectory-analysis.json',{data_origin:'synthetic',input_sha256:hash,config:input.config,...M.trajectory(input.subjects)});}
 catch(error){toast('未完成轨迹导出：'+error.message);}
}
function exportCsv(){
 const selected=rows();if(selected.length<5){toast('当前队列不足5人，禁止导出。');return;}
 const lines=['data_origin,participant_id,topic,patient_day,observed_date,record_status,medication_status,source_id'];
 selected.forEach(s=>{for(let day=0;day<s.expected_days;day++){const o=s.observations.find(x=>x.day===day);lines.push(['synthetic',s.id,s.topic,day+1,o?o.date:'',o?'recorded':'missing',o?o.use:'missing',o?o.source_id:''].join(','));}});
 download('synthetic-patient-days.csv','\uFEFF'+lines.join('\n'),'text/csv;charset=utf-8');
}
root.addEventListener('click',event=>{
 const el=event.target.closest('button');if(!el)return;
 if(el.dataset.openPlan){state.plan=el.dataset.openPlan;go('design');return;}
 if(el.dataset.plan){state.plan=el.dataset.plan;render();return;}
 if(el.dataset.sourceScope){state.sourceScope=el.dataset.sourceScope;render();return;}
 if(el.dataset.route){go(el.dataset.route);return;}
 if(el.dataset.study){state.study=el.dataset.study;go('workbench');return;}
 if(el.dataset.rule){state.rule=el.dataset.rule;render();return;}
 if(el.dataset.sample){state.sample=el.dataset.sample;state.focusSource=el.dataset.source||null;go('examples');if(state.focusSource){const evidence=document.getElementById('evidence-'+state.focusSource)||main.querySelector('[data-observation-source="'+state.focusSource+'"]');evidence?.scrollIntoView({block:'center'});evidence?.focus({preventScroll:true});}return;}
 const action=el.dataset.action;
 if(action==='reset-filters'){invalidate();state.topic='all';state.category='all';state.window_days=7;render();}
 if(action==='export-dictionary')download('research-data-dictionary.json',dictionary);
 if(action==='export-protocol')download('research-protocol-'+state.plan+'.json',{program_version:P.version,status:'proposed_not_conducted',protocol:P.protocols.find(p=>p.id===state.plan),sources:P.sources.filter(s=>P.protocols.find(p=>p.id===state.plan).sources.includes(s.id)),limitations:'方案与文献，不是本产品的实验结果或临床证据'});
 if(action==='export-experiments')download('fixed-synthetic-experiments.json',window.ResearchExperiments);
 if(action==='export-trajectory')void exportTrajectory();
 if(action==='calculate-base-rate')calculateBaseRate();
 if(action==='export-base-rate'&&calculateBaseRate())download('hypothetical-base-rate.json',M.baseRate(state.prior,state.sensitivity,state.specificity));
 if(action==='export-csv')exportCsv();
 if(action==='run-local')void runLocal();
 if(action==='export-input')void exportInput();
 if(action==='export-report'&&state.report)download('health-research-report.json',state.report);
 if(action==='export-template')download('report-contract.json',{schema_version:'1.0',data_origin:'synthetic',platform:'SciencePal',run_id:'真实运行ID',run_url:'https://sciencepal.ai/实际项目或运行地址',input_sha256:'输入文件的规范JSON哈希',data_version:E.DATA_VERSION,code_version:E.VERSION,rule_version:E.RULE_VERSION,knowledge_version:E.KNOWLEDGE_VERSION,metrics:'由run_analysis.py从输入计算，模板不可直接导入'});
});
root.addEventListener('change',event=>{
 const el=event.target;
 if(['topic-filter','category-filter','window-filter'].includes(el.id)){invalidate();if(el.id==='topic-filter')state.topic=el.value;if(el.id==='category-filter')state.category=el.value;if(el.id==='window-filter')state.window_days=Number(el.value);render();}
 if(el.id==='sample-select'){state.sample=el.value;state.focusSource=null;render();}
 if(el.id==='signal-case'){state.signal=el.value;render();}
 if(el.id==='signal-window'){state.signalWindow=Number(el.value);render();}
 if(el.id==='report-import')void importReport(el.files?.[0]);
});
const channel=typeof BroadcastChannel!=='undefined'?new BroadcastChannel('health-prototype-demo'):null;
if(channel){channel.onmessage=event=>{if(event.data?.kind!=='synthetic-demo-status'||typeof event.data.consent!=='boolean')return;if(state.sampleConsent===event.data.consent)return;invalidate();state.sampleConsent=event.data.consent;render();};channel.postMessage({kind:'request-demo-status'});}
render();
})();
