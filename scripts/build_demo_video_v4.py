#!/usr/bin/env python3
"""Integrate the approved research approach clip and subtitle bridges.

Reuses unchanged genuine recording visuals. No product or account mutations.
"""
import copy, hashlib, json, subprocess
from pathlib import Path
import build_demo_video_v3 as previous
from build_research_idea_clip import CAPTIONS as IDEA_CAPTIONS

ROOT=Path(__file__).resolve().parents[1]
SOURCE=ROOT/'output/video-v3';OUT=ROOT/'output/video-v4';WORK=OUT/'render'
WORK.mkdir(parents=True,exist_ok=True)
STORY=copy.deepcopy(json.loads((SOURCE/'story.json').read_text()))
scenes={s['id']:s for s in STORY['scenes']}
scenes['intro']['duration']=24
scenes['intro']['captions']=[
 [.3,6,'许多小病没有进入医院，却经历了症状变化、自主用药和恢复。'],
 [6.3,12.5,'如何把零散自述，转成保留来源、缺失和不确定性的纵向研究数据？'],
 [12.8,17.8,'结构化追问能否补充信息？连续记录能否支持用药线索分析？'],
 [18.2,24.7,'先从用户端看起，观察一次新冠相关不适如何被记录。'],
]
scenes['user']['captions'][0][0]=.9
scenes['user']['captions'][-1]=[52.5,55.8,'用一句话安排提醒，核对时间后保存。']
scenes['user']['captions'].append([56.1,60.4,'当不适逐渐缓解，关照又会如何继续？'])
scenes['recovery']['captions']=[
 [.8,5.7,'结束跟进后，病程留在历史中，每日关照继续。'],
 [6,10.3,'这些个人记录，怎样才能用于研究？'],
]
scenes['consent']['captions']=[
 [.7,8.8,'研究用途由用户单独决定，可以在这里查看用途和授权状态。'],
 [9.1,15.2,'在进入科研端之前，先看连续记录如何形成研究线索。'],
]
idea={'id':'research-idea','kind':'animation','duration':20,'title':'科研端的研究思路','captions':[list(c) for c in IDEA_CAPTIONS],'source':'../video-v3/research-idea-preview/research-idea-20s.mp4'}
STORY['scenes'].insert(STORY['scenes'].index(scenes['research']),idea)
scenes['research']['captions']=[
 [.35,5.5,'带着这一思路，进入科研工作区，从数据概览开始。'],
 [5.8,14.5,'查看事件数量、记录覆盖情况和用药信息，了解当前队列。'],
 [15.5,29.5,'调整观察窗口，比较不同时间范围内的记录情况。'],
 [30.5,44.5,'明确使用、明确未用、记不清和没有记录，分别查看。'],
 [45.5,59.5,'进入用药待核对列表，查看成分重复等需要进一步核实的线索。'],
 [60.5,69,'打开一条候选，查看它所依据的病程记录。'],
 [69.5,75,'沿着观察日、评分、用药状态和来源，回查这段健康过程。'],
 [75.3,80.4,'再看科研任务，分析结果如何被查看与复核。'],
]
scenes['sciencepal']['captions']=[
 [.8,5.5,'这里换用一组独立演示记录，查看SciencePal的分析任务。'],
 [5.8,10,'先确认任务状态，再打开已经完成的结果。'],
 [10.5,20,'进入详情，查看纳入事件、记录完整率和用药待核对信息。'],
 [20.5,30,'继续检查执行记录和分析结果，让结果能够复核。'],
 [30.5,35.5,'研究者可以在科研端完成查看，也可以下载输入数据与任务包。'],
 [35.8,40.4,'接下来，回到新冠随访记录，复核数据本身。'],
]
scenes['review']['captions'][0][0]=.8
scenes['review']['captions'][-1]=[22.5,29.5,'结合实际评分与来源记录，形成可继续核实的研究线索。']
scenes['review']['captions'].append([30,35.4,'从个人关照，到可追溯的院外健康研究。'])
scenes['outro']['captions'][0][0]=.8

def main():
 total=sum(s['duration'] for s in STORY['scenes']);assert total==299
 (OUT/'story.json').write_text(json.dumps(STORY,ensure_ascii=False,indent=2))
 edits=json.loads((SOURCE/'edit-map.json').read_text())
 (OUT/'edit-map.json').write_text(json.dumps({'raw_source_root':'../video-v3/raw','scenes':edits},ensure_ascii=False,indent=2))
 intro=WORK/'intro-visual.mp4'
 previous.base.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',SOURCE/'render/intro-visual.mp4','-vf','setpts=(PTS-STARTPTS)*0.8,fps=30,trim=duration=24','-an','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',intro])
 visual_paths=[];timeline=[];cues=[];elapsed=0
 for scene in STORY['scenes']:
  sid=scene['id']
  visual=intro if sid=='intro' else (SOURCE/'research-idea-preview/render/research-idea-visual.mp4' if sid=='research-idea' else SOURCE/'render'/(sid+'-visual.mp4'))
  assert visual.is_file(),visual
  visual_paths.append(visual)
  for start,end,text in scene['captions']:
   assert 0<=start<end<=scene['duration']+.71 and len(text)<=48
   cues.append({'start':elapsed+start,'end':elapsed+end,'text':text,'scene':sid,'style':'Idea' if sid=='research-idea' else 'Default'})
  timeline.append({**scene,'start':elapsed,'end':elapsed+scene['duration'],'edit':edits.get(sid),'visual_source':str(visual)})
  elapsed+=scene['duration']
 assert all(a['end']<=b['start'] for a,b in zip(cues,cues[1:]))
 listing=WORK/'concat-visuals.txt';listing.write_text(''.join(f"file '{p}'\n" for p in visual_paths))
 joined=WORK/'joined-visuals.mp4'
 previous.base.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',listing,'-map','0:v:0','-an','-c:v','copy',joined])
 header=previous.ASS_HEADER.replace('[Events]','Style: Idea,Arial Unicode MS,31,&H00FFFFFF,&H00FFFFFF,&H4023422D,&H4023422D,0,0,0,0,100,100,0,0,3,9,0,2,70,70,21,1\n[Events]')
 ass=WORK/'complete.zh-CN.ass';ass.write_text(header+''.join(f"Dialogue: 0,{previous.base.timestamp(c['start'])},{previous.base.timestamp(c['end'])},{c['style']},,0,0,0,,{c['text']}\n" for c in cues))
 target=OUT/'healthy-care-demo-v4.mp4'
 print('Encoding integrated film',flush=True)
 previous.base.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',joined,'-vf',f"ass='{ass}':fontsdir='/System/Library/Fonts/Supplemental'",'-an','-t',total,'-r',30,'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-movflags','+faststart',target])
 (OUT/'healthy-care-demo-v4.zh-CN.srt').write_text('\n\n'.join(f"{i+1}\n{previous.srt_time(c['start'])} --> {previous.srt_time(c['end'])}\n{c['text']}" for i,c in enumerate(cues))+'\n')
 (OUT/'timeline.json').write_text(json.dumps({'duration_seconds':total,'resolution':[1920,1080],'fps':30,'audio':False,'fictional_cases':True,'real_product_recordings':True,'research_approach_integrated':True,'cross_module_subtitles':True,'scenes':timeline,'subtitle_cues':cues},ensure_ascii=False,indent=2))
 (OUT/'healthy-care-demo-v4.mp4.sha256').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
 print('Completed',target,flush=True)

if __name__=='__main__':main()
