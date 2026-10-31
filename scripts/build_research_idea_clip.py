#!/usr/bin/env python3
"""Standalone subtitle-only transition introducing the research approach."""
import hashlib, json, math, subprocess
from pathlib import Path
from PIL import Image, ImageDraw
import build_demo_video_v2 as b

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/video-v3/research-idea-preview';WORK=OUT/'render'
WORK.mkdir(parents=True,exist_ok=True)
DURATION=20
CAPTIONS=[
 (.3,4.8,'以院外小病为观察对象，连接症状、实际用药与恢复过程。'),
 (5.1,9.8,'比较建档与随访信息，研究连续采集补充了哪些内容。'),
 (10.1,14.8,'统一观察窗口，分析记录覆盖、缺失与待核实的用药线索。'),
 (15.1,19.7,'再回到每条线索的来源记录，逐步核实分析中的发现。'),
]
STEPS=['连续采集','信息补充','窗口分析','来源复核']

def arrow(d,x1,y,x2,color=b.GREEN):
 d.line((x1,y,x2,y),fill=color,width=4)
 d.polygon([(x2,y),(x2-14,y-9),(x2-14,y+9)],fill=color)

def small_card(im,x,y,w,h,label,lines,active=False):
 d=ImageDraw.Draw(im)
 d.rounded_rectangle((x+5,y+8,x+w+5,y+h+8),radius=24,fill='#dfe9dc')
 d.rounded_rectangle((x,y,x+w,y+h),radius=24,fill='white',outline=b.GREEN if active else '#d6e3d2',width=3 if active else 2)
 b.text(d,(x+28,y+28),label,33,b.GREEN)
 for i,line in enumerate(lines):b.text(d,(x+28,y+96+i*53),line,29,b.MUTED)

def stepper(im,stage,progress):
 d=ImageDraw.Draw(im)
 for i,label in enumerate(STEPS):
  x=104+i*450
  d.rounded_rectangle((x,147,x+362,204),radius=28,fill=b.GREEN if i==stage else '#e2ecdd')
  b.text(d,(x+181,176),label,26,'white' if i==stage else b.MUTED,'mm')
  if i<3:arrow(d,x+385,176,x+427,'#a8c3a8')
 d.rounded_rectangle((104,222,1816,227),radius=2,fill='#d6e4d1')
 d.rounded_rectangle((104,222,104+1712*progress,227),radius=2,fill='#7ca27d')

def frame(t):
 im=b.BASE.copy();b.brand_header(im,'RESEARCH APPROACH / 研究思路')
 stage=min(3,int(t/5));local=t-stage*5;e=b.ease(local/1.1)
 stepper(im,stage,t/DURATION);d=ImageDraw.Draw(im)
 headings=[('观察对象','把院外健康过程，连接成连续记录。'),('采集问题','连续记录，补充了哪些信息？'),('分析问题','在同一窗口内，看见变化与空白。'),('复核路径','从总体发现，回到每条来源记录。')]
 kicker,heading=headings[stage]
 b.text(d,(104,275),kicker,26,b.GREEN);b.text(d,(104,330),heading,61,b.INK)
 shift=round(38*(1-e))
 if stage==0:
  d.line((220,720+shift,1700,720+shift),fill='#a9c6ab',width=6)
  for i,(title,body) in enumerate([('症状','当前感受\n每天的变化'),('实际用药','使用情况\n记不清的部分'),('恢复','活动变化\n后续关照')]):
   x=105+i*590;stagger=b.ease((local-i*.18)/1.1)
   b.paste(im,b.card(title,body,510,235),x,442+round(38*(1-stagger)))
   d.ellipse((x+258,709+shift,x+280,731+shift),fill=b.GREEN)
  b.badge(im,'把零散自述，放回一段健康过程',540,815,840)
 elif stage==1:
  small_card(im,110,460+shift,650,282,'建档信息',['主要不适','开始与持续时间'])
  small_card(im,1050,460+shift,755,282,'随访信息',['不适自评分 · 实际用药','日常活动影响 · 后续变化'],True)
  arrow(d,810,596+shift,995)
  b.badge(im,'比较共同字段的覆盖情况',595,817,730)
 elif stage==2:
  x,y,w=115,492+shift,1110
  d.rounded_rectangle((x,y,x+w,y+265),radius=25,fill='white',outline='#d6e3d2',width=2)
  b.text(d,(x+30,y+24),'统一观察窗口',31,b.GREEN)
  d.line((x+72,y+143,x+w-72,y+143),fill='#abc7aa',width=5)
  window_right=x+72+(w-144)*(.35+.65*b.ease(local/2.6))
  d.rounded_rectangle((x+48,y+93,window_right+24,y+194),radius=17,fill='#e5efdf')
  d.line((x+72,y+143,x+w-72,y+143),fill='#b4cbb0',width=4)
  for i in range(7):
   px=x+72+i*(w-144)/6
   if i in (1,3,5):d.ellipse((px-10,y+133,px+10,y+153),outline='#93a88d',width=3)
   else:d.ellipse((px-10,y+133,px+10,y+153),fill=b.GREEN)
  b.text(d,(x+30,y+216),'记录覆盖 · 缺失 · 用药状态',27,b.MUTED)
  arrow(d,1264,620+shift,1310)
  small_card(im,1350,492+shift,445,265,'待核实线索',['用药信息','值得回查的变化'],True)
  b.badge(im,'观察变化，也保留空白',595,817,730)
 else:
  small_card(im,110,466+shift,595,286,'研究线索',['记录覆盖与缺失','用药待核对信息'])
  arrow(d,755,612+shift,1000)
  dot_x=755+245*((local/2.5)%1)
  d.ellipse((dot_x-7,605+shift,dot_x+7,619+shift),fill='#76a67b')
  small_card(im,1050,466+shift,755,286,'来源记录',['观察日 · 实际记录状态','自评分 · 用药记录 · 记录来源'],True)
  b.badge(im,'发现问题 → 追溯来源 → 复核结果',480,817,960)
 b.text(d,(1816,965),'研究思路示意',22,b.MUTED,'ra')
 return im.convert('RGB')

def srt_time(t):
 ms=round(t*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'

def main():
 b.OUT=OUT;b.WORK=WORK;b.animation=lambda scene,t:frame(t)
 scene={'id':'research-idea','duration':DURATION}
 visual=b.render_animation(scene)
 ass=WORK/'research-idea.ass'
 ass.write_text('''[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: Default,Arial Unicode MS,31,&H00FFFFFF,&H00FFFFFF,&H4023422D,&H4023422D,0,0,0,0,100,100,0,0,3,9,0,2,70,70,21,1\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n'''+''.join(f'Dialogue: 0,{b.timestamp(a)},{b.timestamp(z)},Default,,0,0,0,,{text}\n' for a,z,text in CAPTIONS))
 target=OUT/'research-idea-20s.mp4'
 b.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',visual,'-vf',f"ass='{ass}':fontsdir='/System/Library/Fonts/Supplemental'",'-an','-c:v','libx264','-preset','veryfast','-crf','19','-pix_fmt','yuv420p','-movflags','+faststart',target])
 (OUT/'research-idea.zh-CN.srt').write_text('\n\n'.join(f'{i+1}\n{srt_time(a)} --> {srt_time(z)}\n{text}' for i,(a,z,text) in enumerate(CAPTIONS))+'\n')
 (OUT/'script.md').write_text('# 科研端研究思路过渡片段\n\n放置于科研端录屏之前；独立预览，尚未并入完整视频。20秒、1080p、30fps、无音轨。\n\n'+''.join(f'- {a:.1f}–{z:.1f}秒：{text}\n' for a,z,text in CAPTIONS))
 meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(target)],text=True))
 assert len(meta['streams'])==1 and meta['streams'][0]['codec_type']=='video'
 assert abs(float(meta['format']['duration'])-DURATION)<.05
 decoded=subprocess.run(['ffmpeg','-hide_banner','-v','error','-i',str(target),'-f','null','-'],capture_output=True,text=True)
 assert decoded.returncode==0 and not decoded.stderr,decoded.stderr
 (OUT/'qa.json').write_text(json.dumps({'duration_seconds':DURATION,'resolution':[1920,1080],'fps':30,'audio_streams':0,'full_decode':'passed','sha256':hashlib.sha256(target.read_bytes()).hexdigest()},indent=2))
 # Inspect representative finished frames, including the burned-in subtitles.
 sheet=Image.new('RGB',(1920,1080),b.BG)
 for i,t in enumerate([3,8,13,18]):
  p=OUT/f'frame-{t}.png'
  b.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-ss',t,'-i',target,'-frames:v','1',p])
  im=Image.open(p);im.thumbnail((960,540),Image.Resampling.LANCZOS);sheet.paste(im,(i%2*960,i//2*540))
 sheet.save(OUT/'contact-sheet.jpg')
 print('Completed',target,flush=True)

if __name__=='__main__':main()
