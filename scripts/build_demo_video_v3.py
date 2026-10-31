#!/usr/bin/env python3
"""Subtitle-only film, using unmodified real product recordings and green motion cards."""
import argparse, hashlib, json, math, subprocess
from pathlib import Path
import build_demo_video_v2 as base
from PIL import ImageDraw, Image

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/video-v3';WORK=OUT/'render';WORK.mkdir(parents=True,exist_ok=True)
SPEC=json.loads((OUT/'story.json').read_text())
base.OUT=OUT;base.WORK=WORK;base.SPEC=SPEC
def animation(scene,t):
 im=base.BASE.copy();base.brand_header(im,'AI IN ACTION / SCIENCE FORWARD');d=ImageDraw.Draw(im)
 if scene['id']=='intro':
  if t<10:
   base.title(im,'发生在医院之外','症状变化、自主用药、逐渐恢复。','这些日常过程，如何成为可研究的连续记录？')
   rows=[('症状变化','今天的感受，明天的变化'),('自主用药','实际使用，记忆中的空白'),('恢复过程','日常活动，后续关照')]
   for i,(h,b) in enumerate(rows):
    e=base.ease((t-i*.6)/2);base.paste(im,base.card(h,b,510,245),100+i*590,450+(1-e)*90)
  elif t<21:
   base.title(im,'两个可验证的问题','从记录，到能够核实的研究。')
   rows=[('采集问题','结构化追问，能否补充\n有来源支持的信息？'),('分析问题','连续记录，能否支持窗口分析\n并定位待核实的用药信息？')]
   for i,(h,b) in enumerate(rows):
    e=base.ease((t-10-i*.65)/1.6);base.paste(im,base.card(h,b,785,300),105+i*885,410+(1-e)*70)
   base.badge(im,'来源',380,810,240);base.badge(im,'缺失',840,810,240);base.badge(im,'不确定性',1300,810,240)
  else:
   base.title(im,'伴AI·健康伙伴','一次日常求助，一条研究线索。','从实际使用流程，看见记录如何连接研究。')
   for i,(h,b) in enumerate([('自然对话','不适 · 变化 · 实际用药'),('连续记录','病程 · 观察 · 用户授权'),('科研工作区','发现问题 · 回查 · 复核')]):
    e=base.ease((t-21-i*.55)/1.6);base.paste(im,base.card(h,b,510,250),100+i*590,440+(1-e)*80)
   base.badge(im,'从个人健康空间开始',680,815,560)
 else:
  base.title(im,'从日常关照，到院外健康研究','日常有人关照，研究有据可循。')
  mascot=base.MASCOT.copy();mascot.thumbnail((385,385),Image.Resampling.LANCZOS)
  base.paste(im,mascot,120,440+6*math.sin(t))
  base.paste(im,base.card('个人健康空间','对话 · 病程 · 用药 · 提醒 · 每日关照',1100,195),610,415)
  base.paste(im,base.card('科研工作区','队列 · 观察窗口 · 来源核对 · SciencePal',1100,195),610,650)
 base.text(d,(1815,962),'虚构案例演示',22,base.MUTED,'ra')
 return im.convert('RGB')
base.animation=animation

ASS_HEADER='''[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: Default,Arial Unicode MS,30,&H00FFFFFF,&H00FFFFFF,&H4023422D,&H4023422D,0,0,0,0,100,100,0,0,3,9,0,2,70,70,21,1\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n'''
def subtitles(scene,visual):
 ass=WORK/(scene['id']+'.ass');lines=[]
 for start,end,text in scene['captions']:
  assert 0<=start<end<=scene['duration'];assert len(text)<=48
  lines.append(f'Dialogue: 0,{base.timestamp(start)},{base.timestamp(end)},Default,,0,0,0,,{text}')
 ass.write_text(ASS_HEADER+'\n'.join(lines)+'\n')
 dest=WORK/(scene['id']+'.mp4')
 base.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',visual,'-vf',f"ass='{ass}':fontsdir='/System/Library/Fonts/Supplemental'",'-an','-t',scene['duration'],'-r',30,'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',dest])
 return dest
def srt_time(seconds):
 ms=round(seconds*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--only',default='all');parser.add_argument('--reuse-visuals',action='store_true');parser.add_argument('--assemble-only',action='store_true');args=parser.parse_args()
 edits=json.loads((OUT/'edit-map.json').read_text()) if (OUT/'edit-map.json').exists() else {}
 selected=[] if args.assemble_only else [s for s in SPEC['scenes'] if args.only=='all' or (args.only=='animation' and s['kind']=='animation') or s['id'] in args.only.split(',')]
 for s in selected:
  print('Rendering',s['id'],flush=True);visual=WORK/(s['id']+'-visual.mp4')
  if not(args.reuse_visuals and visual.exists()):visual=base.render_animation(s) if s['kind']=='animation' else base.recording_visual(s,edits[s['id']])
  subtitles(s,visual);print('Ready',s['id'],flush=True)
 if args.only!='all':return
 listing=WORK/'concat.txt';listing.write_text(''.join(f"file '{WORK/(s['id']+'.mp4')}'\n" for s in SPEC['scenes']))
 target=OUT/'healthy-care-demo-v3.mp4'
 base.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',listing,'-map','0:v:0','-an','-c:v','copy','-movflags','+faststart',target])
 cues=[];timeline=[];elapsed=0
 for s in SPEC['scenes']:
  for start,end,text in s['captions']:cues.append((elapsed+start,elapsed+end,text))
  timeline.append({**s,'start':elapsed,'end':elapsed+s['duration'],'edit':edits.get(s['id'])});elapsed+=s['duration']
 (OUT/'healthy-care-demo-v3.zh-CN.srt').write_text('\n\n'.join(f'{i+1}\n{srt_time(a)} --> {srt_time(b)}\n{t}' for i,(a,b,t) in enumerate(cues))+'\n')
 (OUT/'timeline.json').write_text(json.dumps({'duration_seconds':base.duration(target),'resolution':[1920,1080],'fps':30,'audio':False,'fictional_cases':True,'real_product_recordings':True,'scenes':timeline},ensure_ascii=False,indent=2))
 (OUT/'healthy-care-demo-v3.mp4.sha256').write_text(hashlib.sha256(target.read_bytes()).hexdigest()+'  '+target.name+'\n')
 print('Completed',target,flush=True)
if __name__=='__main__':main()
