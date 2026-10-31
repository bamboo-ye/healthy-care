(() => {
  'use strict';
  const {icon,esc}=window.HealthUI;
  const root=document.getElementById('health-app');
  const main=document.getElementById('main');
  const modal=document.getElementById('modal');
  const TODAY='2026-10-18';
  const state={route:'today',messages:[],episodes:[],currentId:null,medications:[],consent:false,photoConsent:false,reminder:null,pending:[],busy:false,sequence:0,profile:{city:null,notes:[]}};
  const navs=[['today','home','每日健康','今日'],['chat','chat','健康对话','对话'],['history','calendar','我的病程','病程'],['medications','pill','我的用药','用药'],['signals','signal','历史线索','线索']];
  const channel=typeof BroadcastChannel!=='undefined'?new BroadcastChannel('health-prototype-demo'):null;
  const current=()=>state.episodes.find(item=>item.id===state.currentId&&item.status==='active');
  const key=()=>`local-${++state.sequence}`;
  const actions=(items)=>`<div class="messageActions">${items.map(item=>`<button data-say="${esc(item.text||item.label)}">${esc(item.label)}</button>`).join('')}</div>`;
  const header=(title,subtitle)=>`<header class="workspaceHeader"><div><p class="eyebrow">HEALTH COMPANION</p><h1>${title}</h1><p>${subtitle}</p></div>${state.route!=='chat'?'<button class="secondaryAction" data-route="chat">'+icon('chat')+'回到对话</button>':''}</header>`;
  const sectionHeading=(title,symbol,meta='')=>`<div class="sectionHeading"><div class="sectionTitle"><span class="sectionIcon">${icon(symbol)}</span><h2>${title}</h2></div>${meta}</div>`;
  const empty=(title,description,prompt)=>`<section class="card emptyCard">${icon('leaf')}<h2>${title}</h2><p>${description}</p>${prompt?`<button class="primaryAction" data-say="${esc(prompt)}">${icon('chat')}和健康伙伴聊聊</button>`:''}</section>`;
  function publishDemo(){channel?.postMessage({kind:'synthetic-demo-status',consent:state.consent,topic:'感冒鼻咽',days:[0,1,2,3,4,5]});}
  if(channel)channel.onmessage=event=>{if(event.data?.kind==='request-demo-status')publishDemo();};
  function message(role,text,card=null,images=[]){state.messages.push({id:key(),role,text,card,images});}
  function reply(text,card){message('assistant',text,card);}
  function cardHtml(card){
    if(!card)return '';
    return `<div class="conversationCard">${card.label?`<small>${esc(card.label)}</small>`:''}${card.title?`<h3>${esc(card.title)}</h3>`:''}${(card.rows||[]).map(row=>`<div><span>${esc(row[0])}</span><strong>${esc(row[1])}</strong></div>`).join('')}${card.note?`<p>${esc(card.note)}</p>`:''}${(card.sources||[]).map(source=>`<a href="${source.url}" target="_blank" rel="noopener noreferrer">${esc(source.label)} ↗</a>`).join('')}${card.actions?actions(card.actions):''}</div>`;
  }
  function bubble(item){return `<article class="conversationMessage ${item.role}" aria-label="${item.role==='user'?'你':'健康伙伴'}的消息">${item.role==='assistant'?'<img class="messageAvatar" src="assets/health-mascot-green.png" alt="健康伙伴">':''}<div class="messageContent"><small>${item.role==='user'?'你':'健康伙伴'}</small><div class="messageBubble"><p>${esc(item.text)}</p>${item.images.length?`<div class="messageImages">${item.images.map(file=>`<button data-preview="${esc(file.url)}" aria-label="放大图片：${esc(file.name)}"><img src="${file.url}" alt="${esc(file.name)}"></button>`).join('')}</div>`:''}${cardHtml(item.card)}</div></div></article>`;}
  function composer(){return `<form class="conversationComposer" id="chat-form"><div class="pendingImages" id="pending-images">${state.pending.map(file=>`<div><img src="${file.url}" alt="待发送：${esc(file.name)}"><button type="button" data-remove-image="${file.id}" aria-label="移除${esc(file.name)}">×</button><span>${esc(file.name)}</span></div>`).join('')}</div><label class="srOnly" for="chat-input">告诉健康伙伴你的情况</label><textarea id="chat-input" name="message" rows="2" maxlength="3000" placeholder="哪里不舒服、持续多久了？也可以先发一张图片……"></textarea><div class="composerBottom"><label class="chatImagePicker">${icon('camera')}<span>添加图片</span><input id="chat-images" type="file" accept="image/png,image/jpeg,image/webp" multiple></label><small>图片仅本地预览 · Shift + Enter 换行</small><button class="primaryAction" type="submit" ${state.busy?'disabled':''}>${icon('arrow')}发送</button></div></form>`;}

  const careReferences={
    '感冒鼻咽':{items:['留意休息、饮水与日常活动的变化。','核对复方产品的具体成分，避免重复使用同成分产品。'],url:'https://www.nhs.uk/conditions/common-cold/',label:'NHS感冒相关资料'},
    '皮肤不适':{items:['留意接触因素、范围变化和新出现的不适。','具体护理与用药需结合部位、产品与症状，不能仅凭外观判断病因。'],url:'https://www.nhs.uk/conditions/atopic-eczema/',label:'NHS相关皮肤护理资料'},
    '轻度过敏':{items:['记录可能接触的诱因与鼻眼症状变化。','按具体产品核对适用性、禁忌和可能影响日常活动的信息。'],url:'https://www.nhs.uk/conditions/allergic-rhinitis/',label:'NHS鼻部过敏相关资料'},
    '胃肠不适':{items:['留意饮水与补液、排便或呕吐情况。','不同胃肠症状的自主处理方式不同，先核对具体症状与产品。'],url:'https://www.nhs.uk/symptoms/diarrhoea-and-vomiting/',label:'NHS胃肠症状相关资料'},
    '轻微疼痛':{items:['记录疼痛部位、持续情况及对睡眠和活动的影响。','留意实际用药与重复成分；明显异常或加重时进一步求助。'],url:'https://www.nhs.uk/symptoms/headaches/',label:'NHS头痛相关资料'},
    '其他不适':{items:['继续补充开始时间、最明显的感觉与日常影响。','需要匹配具体知识和产品说明后，再核对自主处理信息。']}
  };

  function pastInsights(past){
    if(!past.length)return '';
    const counts=past.reduce((result,item)=>(result[item.topic]=(result[item.topic]||0)+1,result),{});
    const repeated=Object.entries(counts).filter(([,count])=>count>1).sort((a,b)=>b[1]-a[1]);
    const entries=past.flatMap(item=>item.observations);
    const rated=entries.filter(item=>item.score!==null);
    const medicines=state.medications.filter(item=>past.some(episode=>episode.id===item.episodeId));
    const insights=[repeated.length?`已结束的描述中，${repeated.map(([topic,count])=>`“${topic}”出现${count}段`).join('、')}。回顾共同的环境、作息和实际用药，有助于下次补充信息；这不是复发诊断。`:'目前还不足以判断反复出现的模式。保留每次发生、变化与结束的记录，能为后续回顾提供依据。'];
    if(rated.length)insights.push(`已有${rated.length}个按病程和日期记录的自评分。不同不适的分数含义可能不同，不把它们合成一个疾病风险分数。`);
    if(medicines.length)insights.push(`这些病程中有${medicines.length}条自述用药记录。下次有类似感觉时，先重新核对具体产品与当前情况；旧记录不代表可以重复使用。`);
    return `<section class="card insightCard">${sectionHeading('历史健康数据观察','chart',`<span class="tag neutral">${past.length}段已结束记录</span>`)}<ul class="dailyAdvice">${insights.map(text=>`<li>${esc(text)}</li>`).join('')}</ul><p class="subtle">依据为你主动提供的症状与实际使用记录，不将其视为经过医学确认的病理或诊断数据。</p><button class="textAction" data-say="帮我看看之前的病程">和健康伙伴一起回顾 →</button></section>`;
  }
  function wellness(){
    const past=state.episodes.filter(item=>item.status==='resolved');
    const latest=past.at(-1);
    const notes=state.profile.notes;
    const skinContext=notes.some(note=>/皮肤|干燥|瘙痒/.test(note))||past.some(item=>item.topic==='皮肤不适');
    const allergyContext=notes.some(note=>/过敏|花粉/.test(note))||past.some(item=>item.topic==='轻度过敏');
    const recovery={
      '感冒鼻咽':['按自身状态安排休息、饮水与日常活动。','如果不适再次出现或明显加重，重新描述新的变化，不自动沿用旧判断。'],
      '皮肤不适':['继续关注日常保湿与可能的刺激因素。','如果再次出现不适，记录部位、接触因素和变化；不自动重复上次用药。'],
      '轻度过敏':['对于已经明确的诱因，留意并尽量减少再次接触。','若症状再次出现，记录接触与变化，不把旧记录当作新的诊断。'],
      '胃肠不适':['关注饮食、饮水和日常活动是否恢复到平时状态。','如出现新的不适，再描述当前情况，不自动恢复旧用药方案。'],
      '轻微疼痛':['留意是否反复出现，或再次影响睡眠与日常活动。','新出现、异常或明显加重的疼痛需要重新评估。'],
      '其他不适':['关注日常状态是否恢复到平时水平。','有新的变化时再记录，不自动套用旧病程或用药。']
    };
    const tips=latest?(recovery[latest.topic]||recovery['其他不适']):['留意睡眠、饮食和日常活动是否接近平时的状态。','如正在自行用药，留意具体产品的说明与实际使用情况，不自动沿用上次的用药。'];
    const source=latest?careReferences[latest.topic]:null;
    const advice=tips.map((text,index)=>({text,basis:latest?'恢复记录':index===0?'日常状态':'用药习惯'}));
    if(skinContext){
      const item={text:'你曾提到皮肤或干燥相关情况。如果当地天气干燥或刺激增多，可留意皮肤保湿、接触因素与新的变化。',basis:'个人情况与环境'};
      if(latest?.topic==='皮肤不适')advice[0]=item;else advice.push(item);
    }
    if(allergyContext){
      const item={text:'结合你提到的过敏情况，留意已知诱因；如果当地出现高花粉等环境提示，可据此安排日常活动。',basis:'个人情况与环境'};
      if(latest?.topic==='轻度过敏')advice[0]=item;else advice.push(item);
    }
    const context=[...(latest?['近期恢复记录']:[]),...(notes.length?['已补充个人背景']:[]),...(state.profile.city?[state.profile.city]:[])];
    const careCard=`<section class="card dailyCareCard">${sectionHeading('今日关照','leaf',`<span class="tag neutral">${latest?'结合恢复与日常情况':notes.length?'结合你的个人情况':'从日常状态开始'}</span>`)}<div class="careContext"><p>${context.length?'结合'+context.map(item=>esc(item)).join('、')+'，整理今天值得留意的事。':'先从日常状态开始，补充个人情况后，关照也会更贴近你。'}</p><span class="careWeatherStatus">${icon('info')}实时天气待接入</span></div><ul class="personalCareAdvice">${advice.map(item=>`<li><small>${item.basis}</small><p>${esc(item.text)}</p></li>`).join('')}</ul>${notes.length?`<p class="profileContext"><span>你告诉我的情况</span>${notes.map(note=>esc(note)).join('；')}</p>`:''}<div class="careFooter ${source?.url?'':'actionsOnly'}">${source?.url?`<a class="textAction cardLink" href="${source.url}" target="_blank" rel="noopener noreferrer">恢复关照参考：${source.label} ↗</a>`:''}<div class="cardActions"><button class="secondaryAction" data-say="我想补充日常健康背景">${icon('chat')}补充我的情况</button>${!state.profile.city?'<button class="quietAction" data-say="我想补充所在城市">告诉你我的城市</button>':''}</div></div></section>`;
    const historyCard=latest?`<section class="card historyRecap">${sectionHeading('历史记录小结','calendar','<span class="tag neutral">已结束 · 非当前问题</span>')}<p class="recordQuote">${esc(latest.description.slice(0,130))}</p><div class="recordFacts"><div class="dataLine"><span>已归档病程</span><strong>${past.length}段</strong></div><div class="dataLine"><span>最近归档</span><strong>${latest.closed}</strong></div></div><p class="subtle">结束状态来自你的说明，仅作为历史回顾。</p><button class="textAction cardLink" data-review="${latest.id}">在对话里回顾这段记录 →</button></section>`:'';
    return header('每日健康','照顾当下，也关注恢复后的每一天。')+`
      <section class="dailyEntry" aria-label="和健康伙伴聊聊">
        <div class="dailyWelcome"><div class="dailyWelcomeCopy"><span class="tag statusTag">${icon('check')}暂无进行中的不适</span><h2>${latest?'恢复以后，也照顾好自己':'今天感觉怎么样？'}</h2><p>身体的小变化、想核对的用药，<br>都可以慢慢告诉我。</p></div><img src="assets/health-mascot-green.png" alt="健康伙伴向你挥手"></div>
        <div class="dailyConversation"><div class="entryHeading"><strong>想聊什么，从这里开始</strong><span>文字或图片都可以</span></div>${composer()}</div>
      </section>
      ${careCard}${latest?`<div class="wellnessGrid">${pastInsights(past)}${historyCard}</div>`:''}
      <p class="conversationFoot">历史关照与当前症状分开；天气建议在有来源与时间信息后才使用真实数据。</p>`;
  }
  function daily(){
    const episode=current();
    if(!episode)return wellness();
    const last=episode.observations.at(-1);
    const duration=episode.description.match(/(?:这|近|持续|已经|大概)?(?:[一二两三四五六七八九十]+|\d+)(?:天|周|小时|个月)/);
    const care=careReferences[episode.topic]||careReferences['其他不适'];
    const medication=state.medications.filter(item=>item.episodeId===episode.id);
    return header('每日健康','把当前情况、护理建议和观察重点放在一起。')+`
      <div class="activeHealthGrid">
        <section class="card currentSummary">${sectionHeading('当前情况分析','chat','<span class="tag">从对话整理</span>')}<p class="recordQuote">${esc(episode.description.slice(0,180))}${episode.description.length>180?'…':''}</p><div class="summaryMetrics">${duration?`<div><span>持续情况</span><strong>${esc(duration[0])}</strong></div>`:''}${last&&last.score!==null?`<div><span>最近不适自评分</span><strong>${last.score}<small> / 10</small></strong></div>`:''}</div><p class="subtle">依据来自你的自述，未知的部分不自动补全。</p></section>
        <section class="card observationCard">${sectionHeading('今天的观察','chart','<span class="tag neutral">实际记录</span>')}${chart(episode)}<p class="subtle">仅展示实际记录的日期与评分。</p></section>
        <section class="card careCard ${episode.urgent?'priorityCard':''}">${sectionHeading(episode.urgent?'当前优先建议':'护理与下一步建议',episode.urgent?'warning':'leaf',`<span class="tag ${episode.urgent?'orange':'neutral'}">${episode.urgent?'优先求助':'知识资料'}</span>`)}${episode.urgent?'<div class="noteBox orange">你提及了需要优先评估的变化，请联系医疗服务；若严重或迅速加重，应及时寻求紧急医疗帮助。</div>':`<ul class="dailyAdvice">${care.items.map(item=>`<li>${esc(item)}</li>`).join('')}</ul>${care.url?`<a class="textAction cardLink" href="${care.url}" target="_blank" rel="noopener noreferrer">${care.label} ↗</a>`:''}`}<div class="cardActions"><button class="secondaryAction" data-say="我想补充现在的情况">${icon('chat')}继续聊聊</button></div></section>
        <section class="card nextStepsCard">${sectionHeading('接下来关注什么','calendar')}<ul class="observationList"><li>最明显的症状有没有变化？</li><li>是否影响睡眠或日常活动？</li><li>今天实际用了什么产品？</li></ul>${state.reminder?`<div class="reminderHint">${icon('clock')}<span>每日记录站内计划</span><strong>${state.reminder}</strong></div>`:''}<div class="cardActions"><button class="primaryAction" data-say="我想记录今天的变化">${icon('chat')}聊聊今天的变化</button></div></section>
        ${medication.length?`<section class="card medicationNotice">${sectionHeading('当前用药需要核对','pill','<span class="tag orange">用户自报</span>')}<p class="bodyCopy">${medication.map(item=>esc(item.name)).join('、')}</p><p class="subtle">具体成分、规格和实际使用方式还需核对，不自动给出续用或停药决定。</p><button class="textAction cardLink" data-say="我想核对正在用的药能不能继续用">在对话里核对 →</button></section>`:''}
      </div><p class="conversationFoot">分析依据与资料参考分开呈现；真实AI与医学知识核验尚未接入。</p>`;
  }

  function chat(){
    const episode=current();
    return header('健康对话','慢慢说，我会陪你把情况理清楚。')+`<section class="conversationPanel"><header class="conversationHeader"><img src="assets/health-mascot-green.png" alt="绿色健康伙伴"><div><strong>健康伙伴</strong><small>${episode?'正在跟进你描述的不适':'今天，有什么想和我聊聊？'}</small></div><span class="tag ${episode?'':'neutral'}">${episode?'有记录在跟进':'暂无进行中的不适'}</span></header><div class="conversationBody" id="conversation-body" role="log" aria-live="polite" aria-relevant="additions">${state.messages.length?state.messages.map(bubble).join(''):`<div class="conversationWelcome"><img src="assets/health-mascot-green.png" alt="健康伙伴向你挥手"><h2>今天有什么不舒服的地方？</h2><p>也可以聊聊用药、身体的小变化，<br>或者你想了解的健康问题。<br>慢慢告诉我，发张图片也可以。</p><span>目前没有正在跟进的不适，我们从你想说的开始。</span></div>`}</div>${composer()}</section><p class="conversationFoot">本地交互原型，未连接真实AI；输入与图片不会上传。</p>`;
  }
  function chart(episode){
    const entries=episode.observations.filter(item=>item.score!==null);
    if(!entries.length)return '<div class="noteBox">还没有症状评分。你可以在对话里说“今天不适大约3分”，不需要补填过去的数据。</div>';
    const points=entries.map((item,i)=>({x:entries.length===1?170:40+i*260/(entries.length-1),y:135-item.score*10,date:item.date,score:item.score}));
    return `<svg class="trendChart" viewBox="0 0 340 180" role="img" aria-label="只展示你实际记录的自评分：${entries.map(item=>item.date+' '+item.score+'分').join('，')}">${[0,5,10].map(value=>`<line x1="35" y1="${135-value*10}" x2="315" y2="${135-value*10}" stroke="#e1e8da"/><text x="13" y="${139-value*10}">${value}</text>`).join('')}${points.length>1?`<path d="${points.map((p,i)=>(i?'L':'M')+p.x+','+p.y).join(' ')}" fill="none" stroke="#66965d" stroke-width="2"/>`:''}${points.map(p=>`<circle cx="${p.x}" cy="${p.y}" r="4" fill="#6e9d62"/><text x="${p.x}" y="${p.y-10}" text-anchor="middle">${p.score}分</text><text x="${p.x}" y="164" text-anchor="middle">${p.date.slice(5)}</text>`).join('')}</svg>`;
  }
  function history(){
    if(!state.episodes.length)return header('我的病程','这里只保留你主动描述和确认的记录。')+empty('还没有病程记录','当你在对话里描述不适后，我们再一起开始记录；不会预先为你建立疾病。','我想说说最近的身体情况');
    return header('我的病程','已结束的记录归档保存，不会自动变成当前的不适。')+`<div class="historyList">${[...state.episodes].reverse().map(episode=>`<section class="card episodeCard">${sectionHeading(esc(episode.title),'calendar',`<span class="tag ${episode.status==='active'?'':'neutral'}">${episode.status==='active'?'正在记录':'已归档'}</span>`)}<p class="recordQuote">${esc(episode.description)}</p><p class="subtle recordMeta">开始记录 ${episode.created}<span>用户自述 · 未作诊断</span></p><div class="episodeDetails"><div class="episodeChart"><h3 class="minorHeading">不适自评分</h3>${chart(episode)}</div><div class="episodeTimeline"><h3 class="minorHeading">记录与变化</h3><div class="timeline">${episode.observations.length?episode.observations.map(item=>`<article class="timelineItem"><time>${item.date} · 第${item.version}版记录</time><h3>${item.score===null?'症状描述':`不适自评分 ${item.score} / 10`}</h3><p>${esc(item.text)}</p></article>`).join(''):'<p class="subtle">还没有补充观察记录。</p>'}</div></div></div><div class="cardActions"><button class="secondaryAction" data-review="${episode.id}">${icon('chat')}在对话中回顾</button>${episode.status==='active'?'<button class="primaryAction" data-say="我想记录今天的变化">聊聊今天的变化</button>':''}</div></section>`).join('')}</div>`;
  }
  function medications(){return header('我的用药','实际使用先记清，适用性按具体产品与说明核对。')+(state.medications.length?`<div class="medicationGrid">${state.medications.map(item=>`<section class="card medicationCard">${sectionHeading(esc(item.name),'pill','<span class="tag orange">用户自报 · 待核对</span>')}<p class="bodyCopy">${esc(item.text)}</p><p class="subtle recordMeta">${item.date}<span>实际使用记录</span></p><div class="noteBox">成分、规格、途径和实际使用需要核对；记录并不表示系统建议继续、停止或改变用药。</div></section>`).join('')}</div><section class="queryActions">${actions([{label:'在对话里补充用药',text:'我想补充今天的用药记录'},{label:'核对能否继续使用',text:'我想核对正在用的药能不能继续用'}])}</section>`:empty('还没有用药记录','告诉我具体用了什么，或发送药盒照片。我们先把信息记清。','我想记录正在使用的药'));}
  function signals(){return header('历史线索','根据真实记录与知识来源，了解哪些变化值得进一步核实。')+`<div class="queryGrid"><section class="card">${sectionHeading(state.episodes.length?'已有的个人记录':'先从真实的记录开始','signal',`<span class="tag neutral">${state.episodes.length}段记录</span>`)}<p class="bodyCopy">${state.episodes.length?'你可以在对话里补充持续情况、其他不适和用药。原型不会将关键词命中当作疾病结论。':'目前没有足够的个人历史信息，不显示虚构病程或疾病风险。你可以直接说说最近的变化。'}</p><div class="noteBox">正式功能会检索个人历史记录、匹配经过审阅的知识条目，并展示依据、缺失信息与下一步行动。当前未连接真实知识匹配服务。</div><div class="cardActions"><button class="primaryAction" data-say="我想聊聊最近身体的变化">${icon('chat')}聊聊身体变化</button></div></section><section class="card supportingCard">${sectionHeading('了解这项功能','book')}<p class="bodyCopy">可以查看一个清楚标注的独立合成例子；它不会加入你的个人病程。</p><div class="cardActions"><button class="secondaryAction" data-say="演示历史线索匹配">在对话里看一个例子</button></div></section></div>`;}
  function privacy(){return header('我的与授权','个人健康服务与研究使用分别选择。')+`<div class="privacyGrid"><section class="card">${sectionHeading('当前选择','shield','<span class="tag neutral">页面内状态</span>')}<div class="privacyFacts"><div class="dataLine"><span>研究二次使用</span><strong>${state.consent?'已选择允许（演示）':'默认关闭'}</strong></div><div class="dataLine"><span>图片研究使用</span><strong>${state.photoConsent?'已选择允许（演示）':'关闭'}</strong></div><div class="dataLine"><span>实际对外上传</span><strong>当前没有</strong></div><div class="dataLine"><span>每日记录提醒</span><strong>${state.reminder?state.reminder+' · 站内计划':'未设置'}</strong></div></div><p class="subtle">研究授权只改变独立科研端的合成演示队列，不会把本次对话上传。</p>${actions([{label:'聊聊数据授权',text:'我想设置研究授权'},{label:'导出个人记录',text:'导出我的记录'},{label:'清除本次记录',text:'我想清除本次记录'}])}</section><section class="card supportingCard">${sectionHeading('记录由你掌控','user')}<p class="bodyCopy">不参与研究也可以使用个人服务。文字和图片保留在本页内，刷新会恢复空白状态。历史记录不会自动作为正在进行的不适展示。</p><div class="noteBox">设置与撤回都可以在对话中完成，选择始终由你决定。</div>${actions([{label:'设置记录提醒',text:'我想设置每天记录的提醒'},{label:'撤回研究授权',text:'撤回研究授权'}])}</section></div>`;}
  const pages={today:daily,chat,history,medications,signals,privacy};
  function render(){
    document.getElementById('nav').innerHTML=navs.map(([id,ico,label,short])=>`<button data-route="${id}" aria-label="${label}" class="${state.route===id?'active':''}" ${state.route===id?'aria-current="page"':''}>${icon(ico)}<span class="navLong">${label}</span><span class="navShort" aria-hidden="true">${short}</span></button>`).join('');
    main.dataset.view=state.route;
    main.innerHTML=(pages[state.route]||chat)();
    root.querySelectorAll('[data-route="privacy"]').forEach(element=>{
      element.classList.toggle('is-current',state.route==='privacy');
      if(state.route==='privacy')element.setAttribute('aria-current','page');else element.removeAttribute('aria-current');
    });
    root.querySelectorAll('[data-icon]').forEach(element=>element.innerHTML=icon(element.dataset.icon));
    const log=document.getElementById('conversation-body');if(log)log.scrollTop=log.scrollHeight;
  }
  function go(route){state.route=pages[route]?route:'chat';render();window.scrollTo({top:0,behavior:'instant'});}
  function hasPositive(text,expression){return text.split(/[，,。；;！!？?]/).some(clause=>{const match=clause.match(expression);return match&&!/(没有|并无|无|未出现|否认|不伴|不觉得).{0,4}$/.test(clause.slice(0,match.index));});}
  function guessTopic(text){if(/痒|皮肤|红疹|湿疹|皮疹|虫咬/.test(text))return '皮肤不适';if(/腹|胃|肚子|腹泻|拉肚子|便秘|呕吐/.test(text))return '胃肠不适';if(/过敏|喷嚏/.test(text))return '轻度过敏';if(/头痛|头疼|酸痛|疼/.test(text))return '轻微疼痛';if(/感冒|鼻|咽|喉|咳/.test(text))return '感冒鼻咽';return '其他不适';}
  function createEpisode(text){const episode={id:key(),title:'我描述的一次不适',description:text,topic:guessTopic(text),created:TODAY,status:'active',observations:[],images:[]};state.episodes.push(episode);state.currentId=episode.id;return episode;}
  function observe(episode,text){const scoreMatch=text.match(/(?:评分|大约|大概|程度|不适|疼痛|瘙痒)?\s*(10|[0-9])\s*分/);const score=scoreMatch?Number(scoreMatch[1]):null;let entry=episode.observations.find(item=>item.date===TODAY);if(entry){entry.text+='\n'+text;entry.version++;if(score!==null)entry.score=score;}else episode.observations.push({date:TODAY,text,score,version:1});return score;}
  function recordMedication(text,episode){const named=text.match(/(?:吃了|服用了|用了|涂了|在用|在吃|药名是|药名为|记录用药[:：])\s*([^，,。；;\n]{1,45})/);if(!named)return false;const raw=named[1].trim();if(!raw||/^(什么|哪些|多少|多久|药吗|过药吗|没有)/.test(raw))return false;state.medications.push({id:key(),episodeId:episode?.id||null,name:raw,text,date:TODAY});return raw;}
  function exportData(){const content={data_origin:'local-conversation-prototype',date:TODAY,episodes:state.episodes.map(item=>({...item,images:item.images.map(file=>({name:file.name}))})),medications:state.medications,research_consent:state.consent,photo_research_consent:state.photoConsent,reminder:state.reminder,profile:state.profile,limitations:['未接入真实AI、医学判断或后端','图片仅在本页中预览，导出不包含图片文件']};const blob=new Blob([JSON.stringify(content,null,2)],{type:'application/json'});const url=URL.createObjectURL(blob);const a=document.createElement('a');a.href=url;a.download='health-conversation-records.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
  function clearAll(){const urls=new Set([...state.pending.map(item=>item.url),...state.messages.flatMap(item=>item.images.map(image=>image.url)),...state.episodes.flatMap(item=>item.images.map(image=>image.url))]);urls.forEach(url=>URL.revokeObjectURL(url));state.episodes=[];state.currentId=null;state.medications=[];state.messages=[];state.pending=[];state.consent=false;state.photoConsent=false;state.reminder=null;state.profile={city:null,notes:[]};publishDemo();}
  function process(text,images){
    if(/^我想补充所在城市$/.test(text)){reply('如果方便，可以直接告诉我常住城市，例如“我在上海”。只保存在本页，不会自动定位或上传。当前原型尚未接入实时天气。');return;}
    if(/^我想补充日常健康背景$/.test(text)){reply('可以慢慢告诉我平时需要留意的情况，例如容易干燥、已知过敏、日常作息或常住城市。\n我会把这些当作日常背景，不自动建立正在进行的不适，也不把它们当作确诊。');return;}
    const city=text.match(/^(?:我在|我住在|我常住|我的城市是|我所在的城市是)\s*([^，,。\s]{2,12})$/);
    if(city){state.profile.city=city[1];reply('记下了，你告诉我的城市是'+city[1]+'。\n当前原型没有接入实时天气，不会编造温度或预警；这条信息先作为日常关照的背景。');return;}
    if(/^(我平时|我容易|我对.{1,15}过敏|我的皮肤容易|我的日常情况)/.test(text)&&!/(今天|现在|正在|这两天)/.test(text)){state.profile.notes.push(text);reply('这条日常背景已经记下了。\n它会帮助整理季节、环境或康复后的条件性建议，不会自动变成正在进行的症状。');return;}
    if(/^(确认清除本次记录|确认清除)$/.test(text)){clearAll();reply('本次记录和图片预览已经清除，研究授权也已撤回。\n现在没有正在跟进的不适。今天还有什么想和我聊聊的吗？');return;}
    if(/清除|删除.*记录/.test(text)){reply('可以。确认后，会清除本页的对话、病程、用药与图片预览，并撤回本次研究选择。已下载的文件不受影响。',{title:'清除本次页面记录',actions:[{label:'确认清除本次记录'},{label:'先保留',text:'先保留这些记录'}]});return;}
    if(/先保留/.test(text)){reply('好，记录先保留。你想继续聊哪一部分？');return;}
    if(/导出/.test(text)){exportData();reply('已经为你生成本地记录文件。它包括本页的文字记录与授权选择，不包含图片文件。下载后请自行保管。');return;}
    if(/撤回.*研究|不参与研究|暂不参与研究|关闭研究授权/.test(text)){state.consent=false;state.photoConsent=false;publishDemo();reply('好的，研究使用已关闭，影像研究选择也一起撤回。\n个人健康服务可以继续使用。这里的选择只作用于本地原型，不会上传你的对话。');return;}
    if(/^(允许去标识化研究|我同意将记录用于研究|同意研究使用)$/.test(text)){state.consent=true;publishDemo();reply('已记录你的研究使用选择。\n当前原型只联动科研端的合成样例，不会上传本次文字或图片。影像研究仍单独关闭。',{title:'你的选择',rows:[['去标识化研究','允许（演示）'],['图片研究','仍然关闭']],actions:[{label:'撤回研究授权'}]});return;}
    if(/^(允许图片研究|我同意图片用于研究)$/.test(text)){if(!state.consent){reply('影像研究需要单独、明确的用途授权。我们先聊清研究范围；你也可以继续保持关闭。',{actions:[{label:'我想设置研究授权'}]});return;}state.photoConsent=true;reply('已记录本页的影像研究选择。当前没有实际上传或研究图片，你也可以随时撤回。');return;}
    if(/授权|隐私|研究.*数据/.test(text)){reply('是否参与研究由你决定，默认不参与也不影响健康服务。\n研究应使用经过独立授权的数据，图片还需要另行同意。当前只是本地流程演示，没有真实上传。',{title:'研究数据使用',rows:[['当前研究选择',state.consent?'允许（演示）':'关闭'],['图片研究',state.photoConsent?'允许（演示）':'关闭']],actions:[{label:'允许去标识化研究'},{label:'暂不参与研究'},{label:'撤回研究授权'}]});return;}
    if(/关闭.*提醒|暂停.*提醒|不要.*提醒/.test(text)){state.reminder=null;reply('好，站内记录提醒计划已暂停。需要时可以再告诉我。');return;}
    if(/提醒/.test(text)){const time=text.match(/(\d{1,2})\s*(?:[:：点])\s*(半|\d{1,2})?/);if(!time){reply('想每天什么时候提醒你记录呢？\n可以直接说“每天晚上8点半提醒我记录”。当前原型会保存站内计划，不发送系统通知。');return;}let hour=Number(time[1]),minute=time[2]==='半'?30:Number(time[2]||0);if(/晚上|下午/.test(text)&&hour<12)hour+=12;if(hour>23||minute>59){reply('这个时间还需要核对一下。可以用“20:30”这样的格式再告诉我吗？');return;}state.reminder=String(hour).padStart(2,'0')+':'+String(minute).padStart(2,'0');reply(`已把每日记录的站内计划设为${state.reminder}。\n当前原型不会发送系统推送。没有进行中的不适时，也不会把旧病程当作新任务。`);return;}
    if(/演示.*历史线索|历史线索.*例子/.test(text)){reply('来看一个独立的合成例子，不是你的个人健康记录，也不会加入你的病程。\n如果历史记录里陆续出现口渴、尿频和非主动体重下降，系统会把日期与症状放在一起，对照相关知识资料，再说明还需要核实什么。它不能据此判断疾病或阶段。',{label:'独立合成样例 · 不属于你的记录',title:'症状组合与知识资料',rows:[['9月28日','自报持续口渴'],['10月5日','自报排尿增多'],['10月18日','自报非主动体重下降']],note:'这些表现可见于糖尿病相关资料；诊断需要进一步检查，组合规则未验证筛查效能。',sources:[{label:'NHS症状与诊断资料',url:'https://www.nhs.uk/conditions/type-2-diabetes/symptoms/'}]});return;}
    if(/历史线索|早期|大病|历史数据/.test(text)){reply(state.episodes.length?'可以一起梳理你已经记录的症状、持续情况和用药，再与知识资料核对。当前原型保留对话依据，但没有接入真实知识匹配服务，不会凭几个词给出疾病结论。':'现在还没有足够的个人历史记录，我不会替你补出一段病程或疾病风险。你可以先说说最近有没有持续出现的变化。',{actions:[{label:'看看一个明确标注的例子',text:'演示历史线索匹配'}]});return;}
    const active=current();
    if(/我的病程|查看.*病程|回顾.*记录|看看.*病程/.test(text)){reply(state.episodes.length?'可以，我把你主动记录过的病程整理在下面。归档的记录只用于回顾，不会自动恢复跟进。':'现在还没有病程记录，也没有正在跟进的不适。今天有什么不舒服的地方，慢慢告诉我就好。',state.episodes.length?{title:'你记录过的病程',rows:state.episodes.map(item=>[item.status==='active'?'正在记录':'已归档',item.description])}:null);return;}
    if(/我的用药|查看.*用药|看看.*用药/.test(text)){reply(state.medications.length?'这些是你主动告诉我的实际用药信息，尚未作为适用性判断。':'还没有实际用药记录。可以告诉我今天用了什么，或发药盒照片。',state.medications.length?{title:'自述用药记录',rows:state.medications.map(item=>[item.date,item.name])}:null);return;}
    if(/我好了|已经好了|已经恢复|已经痊愈|结束.*(记录|病程|跟进)|结束这次|症状消失/.test(text)){
      if(active){active.status='resolved';active.closed=TODAY;state.currentId=null;state.messages=[];reply('这次记录已经归档。\n现在没有正在跟进的不适。今天还有哪里不舒服，或有什么想了解的健康问题吗？\n需要时，你可以主动到“我的病程”回顾，不会自动恢复跟进。');}
      else reply('听起来目前没有需要跟进的不适。今天有什么健康问题想聊聊，或有什么小变化想记录吗？');return;
    }
    if(/继续(吃|用|服)|还能(吃|用)|停药|换药|用什么药|吃什么药/.test(text)){reply('我们先把具体产品核对清楚。请告诉我药盒上的完整名称、成分和规格，已经用了多久、实际怎么用，以及现在有什么变化；也可以发药盒照片。\n是否适合继续使用，需要对照这个产品的说明和你的情况，不能只看用了几天。当前原型不生成个体剂量、停药或续药决定。');return;}
    if(/我想记录.*药|补充.*用药|记录用药$/.test(text)){reply('好，慢慢告诉我：今天实际用了什么产品、多少、什么时候用的？\n记不清的地方可以直接说“不记得”。药盒照片也可以一起发来，我们先记录实际情况。');return;}
    const isKnowledge=/什么是|科普|介绍一下|有什么功能|能做什么|怎么使用/.test(text);
    if(isKnowledge){reply('我可以陪你梳理日常小病、自我护理、用药说明和身体变化，也能帮你连续记录。\n你可以直接用自己的话描述，不需要选病种。当前页面演示对话流程，真实资料检索与模型分析会在后端接入。');return;}
    const symptom=hasPositive(text,/不(?:太|很)?舒服|不适|疼|痛|痒|红疹|皮疹|湿疹|咳|鼻涕|鼻塞|感冒|咽|喉|嗓|腹泻|拉肚子|便秘|呕吐|过敏|发烧|发热|乏力|恶心|头晕/);
    const red=hasPositive(text,/呼吸困难|胸痛|突发剧烈|意识不清|呕血|便血|无法喝水|无法补液/);
    let episode=active;
    const isNewEpisode=!episode&&symptom&&!isKnowledge;
    if(isNewEpisode)episode=createEpisode(text);
    const med=recordMedication(text,episode);
    if(episode&&images.length)episode.images.push(...images);
    const shouldObserve=episode&&text&&!['我想记录今天的变化','我想补充现在的情况','聊聊今天的变化','每日记录'].includes(text)&&(symptom||med||/\d\s*分|今天|目前|现在|持续|睡眠|夜里|比之前|好一点|减轻|加重/.test(text));
    const score=shouldObserve?observe(episode,text):null;
    if(red){if(episode)episode.urgent=true;reply('你提到的变化需要优先联系医疗服务评估，不适合只按普通小病继续自主处理。\n先把求助放在前面；如果情况严重或正在迅速加重，请及时寻求紧急医疗帮助。这里的聊天不能代替当面评估。');return;}
    if(med){reply(`我先按你的原话记录了：“${med}”。\n这是一条实际使用记录，不是建议继续或改变用药。成分、规格和使用方式还需要核对；你可以继续补充，或发药盒照片。`,{title:'用户自述用药',rows:[['记录日期',TODAY],['产品描述',med]],note:'尚未核实成分与规格。'});return;}
    if(images.length){reply('图片已经附在这条消息里，可以点开看大图。\n也请说说图片对应哪里不舒服、从什么时候开始、最近有什么变化。照片需要结合你的描述看；当前原型只演示图片输入与对话，不会把图片识别为诊断。');return;}
    if(/我想记录今天|聊聊今天|每日记录|今天的变化/.test(text)&&!episode){reply('现在没有正在跟进的不适。今天有什么不舒服的地方，或者只是想记下身体的小变化？直接告诉我就好，不需要先选病种。');return;}
    if(episode){
      if(isNewEpisode){const duration=text.match(/(?:这|近|持续|已经|大概)?(?:[一二两三四五六七八九十]+|\d+)(?:天|周|小时|个月)/);reply('听到你说的了，我们先从最让你困扰的感觉开始。\n'+(duration?'最近有什么变化，是否影响睡眠或日常活动？':'大概从什么时候开始，是否影响睡眠或日常活动？')+'\n有没有新出现、让你特别担心的变化？我先保留你的原话，不把它直接当成诊断。',{label:'按对话整理 · 来源为用户自述',title:'本次记录',rows:[['你描述的情况',episode.description],...(duration?[['持续情况',duration[0]]]:[]),...(score!==null?[['自评分',score+' / 10']]:[]),['病程状态','正在补充信息']],actions:[{label:'补充今天的变化',text:'我想记录今天的变化'}]});}
      else if(score!==null){reply(`今天的不适自评分${score}分，已经和你这次描述记在一起了。\n和前一次相比有什么变化？今天实际有没有用药，也可以继续告诉我。记不清的部分留空就好。`,{title:'今天的记录',rows:[['日期',TODAY],['自评分',score+' / 10']],note:'同一天补充内容会更新当天记录，不增加观察天数。'});}
      else if(/我想记录今天|补充今天|每日记录/.test(text)){reply('好呀，今天和之前相比怎么样？\n可以说说最明显的症状、是否影响睡眠或活动、实际用了什么药。愿意的话，也可以用0到10分形容今天的不适，0是没有、10是最强。');}
      else reply('我把这条补充记下了。\n现在最困扰你的是什么？大概持续多久，今天比之前轻了还是重了？如果正在用药，把具体名称与实际使用情况一起告诉我，我们再逐项核对。');
      return;
    }
    if(/我很好|没有不舒服|没有不适|没事|状态不错/.test(text)){reply('那今天就先不建立不适记录。\n如果有用药问题、身体的小变化，或者想了解日常健康知识，随时慢慢聊。');return;}
    reply('我在，慢慢说就好。\n今天是哪里不舒服，还是有用药或日常健康的问题想了解？也可以先发一张图片，再告诉我你注意到了什么。');
  }
  function send(text,images=[]){if(state.busy)return;text=String(text||'').trim();if(!text&&!images.length)return;state.route='chat';message('user',text||'发来了一张图片',null,images);state.busy=true;try{process(text,images);}finally{state.busy=false;render();}}
  function showImage(url){document.getElementById('modal-title').textContent='图片预览';document.getElementById('modal-content').innerHTML=`<img class="largeImagePreview" src="${esc(url)}" alt="你发送的图片，本地预览">`;modal.showModal();}
  root.addEventListener('click',event=>{
    const element=event.target.closest('button');if(!element)return;
    if(element.dataset.route){go(element.dataset.route);return;}
    if(element.dataset.say){send(element.dataset.say);return;}
    if(element.dataset.preview){showImage(element.dataset.preview);return;}
    if(element.dataset.removeImage){const draft=document.getElementById('chat-input')?.value||'';const index=state.pending.findIndex(item=>item.id===element.dataset.removeImage);if(index>=0){URL.revokeObjectURL(state.pending[index].url);state.pending.splice(index,1);render();const input=document.getElementById('chat-input');if(input)input.value=draft;}return;}
    if(element.dataset.review){const episode=state.episodes.find(item=>item.id===element.dataset.review);if(episode){state.route='chat';message('user','帮我回顾这次记录');reply('这是一份历史回顾，不会自动开始或恢复随访。',{title:episode.title,rows:[['最初描述',episode.description],['状态',episode.status==='resolved'?'已归档':'正在记录'],['已记录日期',episode.observations.length+'天']],note:'内容来自你的自述，不是诊断。'});render();}return;}
    if(element.dataset.action==='close-dialog')modal.close();
  });
  root.addEventListener('submit',event=>{if(event.target.id!=='chat-form')return;event.preventDefault();const text=new FormData(event.target).get('message');const files=state.pending.splice(0);send(text,files);});
  root.addEventListener('keydown',event=>{if(event.target.id==='chat-input'&&event.key==='Enter'&&!event.shiftKey&&!event.isComposing){event.preventDefault();event.target.form.requestSubmit();}});
  root.addEventListener('change',event=>{
    if(event.target.id!=='chat-images')return;
    const text=document.getElementById('chat-input')?.value||'';
    const files=Array.from(event.target.files||[]);
    for(const file of files){if(state.pending.length>=4)break;if(!['image/png','image/jpeg','image/webp'].includes(file.type)||file.size>8*1024*1024){reply('这张图片暂时不能加入。请使用8MB以内的PNG、JPEG或WebP图片；每次最多4张。');continue;}state.pending.push({id:key(),name:file.name,url:URL.createObjectURL(file)});}
    render();const input=document.getElementById('chat-input');if(input)input.value=text;
  });
  modal.addEventListener('click',event=>{if(event.target===modal)modal.close();});
  render();publishDemo();
})();
