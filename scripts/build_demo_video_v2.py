#!/usr/bin/env python3
"""Animated research-led film plus genuine continuous tab-recording excerpts.

No product UI or model output is synthesized. Raw browser captures and edit map
are retained. Run with the bundled Python runtime (Pillow and NumPy required).
"""
import argparse, json, math, re, subprocess, wave
from functools import lru_cache
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/video-v2'; WORK=OUT/'render'; WORK.mkdir(parents=True,exist_ok=True)
FONT='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
W,H,FPS=1920,1080,30
INK='#193e2e'; GREEN='#28684a'; SOFT='#dfecdc'; MUTED='#627a68'; BG='#f1f6ed'; WHITE='#ffffff'
SPEC=json.loads((OUT/'story.json').read_text())

def run(args): subprocess.run([str(x) for x in args],check=True)
def duration(p):
 return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)],text=True).strip())
@lru_cache(None)
def font(n):return ImageFont.truetype(FONT,n)
def ease(t):t=max(0,min(1,t));return 1-(1-t)**3
def text(draw,xy,value,size=36,color=INK,anchor=None):draw.text(xy,value,font=font(size),fill=color,anchor=anchor)
def wrap(value,maxchars=36):
 parts=[]
 for line in value.split('\n'):
  while len(line)>maxchars:parts.append(line[:maxchars]);line=line[maxchars:]
  parts.append(line)
 return '\n'.join(parts)

@lru_cache(None)
def card(title,body,width=510,height=220,accent=GREEN):
 im=Image.new('RGBA',(width+50,height+60));shadow=Image.new('RGBA',im.size);d=ImageDraw.Draw(shadow)
 d.rounded_rectangle((20,20,width+20,height+20),radius=28,fill=(24,65,42,25));im.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(12)))
 d=ImageDraw.Draw(im);d.rounded_rectangle((12,8,width+12,height+8),radius=28,fill='white',outline='#d9e5d8',width=2)
 d.rounded_rectangle((40,40,48,84),radius=4,fill=accent);text(d,(70,42),title,34,accent)
 d.multiline_text((40,112),body,font=font(27),fill=MUTED,spacing=12)
 return im

def background():
 y,x=np.mgrid[0:H,0:W];a=np.exp(-(((x-1550)/850)**2+((y-220)/650)**2))
 base=np.empty((H,W,3),dtype=np.uint8)
 for c,(v,k) in enumerate([(244,19),(248,12),(238,15)]):base[:,:,c]=(v-k*a).astype(np.uint8)
 im=Image.fromarray(base,'RGB').convert('RGBA');d=ImageDraw.Draw(im)
 for px in range(80,W,80):
  for py in range(100,H,80):d.ellipse((px,py,px+2,py+2),fill='#d6e4d3')
 return im
BASE=background()
MASCOT=Image.open(ROOT/'apps/web/public/assets/health-mascot-green.png').convert('RGBA')

def brand_header(im,tag='AI4SCIENCE / HEALTHCARE'):
 d=ImageDraw.Draw(im);text(d,(104,54),'伴AI·健康伙伴',31,GREEN);text(d,(1816,58),tag,23,MUTED,'ra')
 d.line((104,108,1816,108),fill='#c8dbc8',width=2)
def title(im,kicker,heading,sub=None):
 d=ImageDraw.Draw(im);text(d,(104,160),kicker,26,GREEN);text(d,(104,220),heading,66,INK)
 if sub:text(d,(108,319),sub,30,MUTED)
def paste(im,obj,x,y):im.alpha_composite(obj,(int(x),int(y)))
def badge(im,label,x,y,width=290,color=SOFT):
 d=ImageDraw.Draw(im);d.rounded_rectangle((x,y,x+width,y+54),radius=27,fill=color);text(d,(x+width/2,y+27),label,24,GREEN,'mm')

def animation(scene,t):
 im=BASE.copy();brand_header(im)
 d=ImageDraw.Draw(im);sid=scene['id']
 if sid=='intro':
  if t<7:
   title(im,'发生在医院之外','一段健康过程，散落在日常里。','新冠自述场景 / 合成演示')
   rows=[('今天','自测抗原阳性\n喉咙痛、鼻塞',1080,405),('昨天','用过什么药？\n有些信息记不清了',700,600),('后来','症状如何变化？\n什么时候结束跟进？',130,465)]
   for i,(a,b,x,y) in enumerate(rows):
    e=ease((t-i*.65)/1.8);paste(im,card(a,b,470,220),x,y+60*(1-e)+6*math.sin(t+i))
  elif t<14:
   title(im,'院外健康研究的难点','没有记录，不等于没有发生。','时间、未知与来源，需要一起保留。')
   d.line((180,600,1740,600),fill='#abc6ad',width=7)
   for i,(h,b) in enumerate([('症状变化','评分、日期、具体感受'),('实际用药','明确使用 / 未用 / 未知'),('恢复过程','结束跟进，保留历史')]):
    x=100+i*580;e=ease((t-7-i*.45)/1.4);paste(im,card(h,b,530,225),x,410+(1-e)*75)
    d.ellipse((x+250,682,x+270,702),fill=GREEN)
   badge(im,'来源可回查',240,775,330);badge(im,'未知不补造',795,775,330);badge(im,'过程可观察',1350,775,330)
  else:
   title(im,'伴AI·健康伙伴','把一次求助，连接到可追溯研究。','个人关照与科研工作区，分别服务各自的使用者。')
   for i,(h,b) in enumerate([('自然对话','症状、图片、实际用药'),('用户确认','核对草案，保留未知'),('科研分析','独立授权，冻结输入')]):
    e=ease((t-14-i*.55)/1.5);paste(im,card(h,b,500,240),110+i*590,435+(1-e)*90)
    if i<2:
     x=650+i*590;d.line((x,560,x+30,560),fill=GREEN,width=4);d.polygon([(x+30,560),(x+16,551),(x+16,569)],fill=GREEN)
   badge(im,'先看一次真实使用',700,810,520)
  text(d,(104,979),'全片病例、检测示意与研究数据均为合成；旁白为AI配音。',24,MUTED)
 elif sid=='bridge':
  title(im,'同一工作区，后台联动','SciencePal 执行，产物回传与核验。','等待已压缩；本次补齐交付总结后续跑，保留已有计算。')
  labels=[('冻结输入','数据快照 + 方法版本'),('API 提交','科研Agent实际执行'),('取回产物','报告 + CSV + 日志'),('独立核验','输入哈希 + 统计指标')]
  for i,(a,b) in enumerate(labels):
   x=95+i*455;paste(im,card(a,b,405,235),x,445)
   if i<3:
    d.line((x+435,560,x+459,560),fill='#a9c7ad',width=4)
    dot=x+435+((t*.4+i*.23)%1)*24;d.ellipse((dot-6,554,dot+6,566),fill=GREEN)
  badge(im,'下面查看本次任务续跑后的完成结果',590,820,740)
 elif sid=='benchmark':
  title(im,'独立的信息采集组件实验','提出问题，也检验方法。','48个合成留出案例 · 16个模板簇 · 固定追问预算')
  text(d,(110,370),'来源支持字段宏平均召回率',30,MUTED)
  values=[('初始描述',30.10,0,'#b2c9ac'),('通用追问',77.95,2,'#76a582'),('定向追问',79.97,1,GREEN)]
  for i,(label,value,fail,color) in enumerate(values):
   y=445+i*110;e=ease((t-2-i*.5)/2.5);text(d,(110,y+15),label,34,INK)
   d.rounded_rectangle((350,y,1550,y+64),radius=14,fill='#e1ebdc')
   end=350+value*12*e
   if end>355:d.rounded_rectangle((350,y,end,y+64),radius=14,fill=color)
   text(d,(1590,y+13),f'{value*e:.2f}%',37,INK);text(d,(1770,y+23),f'失败{fail}',23,MUTED)
  d.rounded_rectangle((105,805,1815,959),radius=24,fill='white',outline='#c8d9c7',width=2)
  if t<13:
   text(d,(145,830),'同一模型、最多3个追问字段、1轮脚本化应答',31,GREEN)
   text(d,(145,889),'失败案例保留并计入；仅在固定合成条件下比较。',29,MUTED)
  else:
   text(d,(145,826),'定向 − 通用：+2.01个百分点；95%区间 −4.31 至 +10.69',30,GREEN)
   text(d,(145,884),'区间包含0，尚不能证明定向方案更优。',32,INK)
  text(d,(110,983),'不是临床或产品整体准确率；SciencePal执行已有模型观测的评分与复核。',24,MUTED)
 elif sid=='outro':
  title(im,'从日常关照，到院外健康研究','日常有人关照，研究有据可循。')
  mascot=MASCOT.copy();mascot.thumbnail((390,390),Image.Resampling.LANCZOS);paste(im,mascot,114,430+6*math.sin(t))
  paste(im,card('个人健康空间','对话 · 图片 · 病程 · 用药 · 每日关照',1100,205),610,415)
  paste(im,card('科研工作区','队列 · 数据质量 · 来源核对 · SciencePal',1100,205),610,655)
  text(d,(110,965),'伴AI·健康伙伴  /  AI in Action · Science Forward',29,GREEN)
 return im.convert('RGB')

def render_animation(scene):
 dest=WORK/(scene['id']+'-visual.mp4')
 p=subprocess.Popen(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','-','-an','-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',str(dest)],stdin=subprocess.PIPE)
 try:
  for n in range(round(scene['duration']*FPS)):p.stdin.write(animation(scene,n/FPS).tobytes())
 finally:p.stdin.close()
 if p.wait()!=0:raise RuntimeError('Animation encode failed')
 return dest

def recording_visual(scene,edit):
 dest=WORK/(scene['id']+'-visual.mp4');titlefile=WORK/(scene['id']+'-title.txt');titlefile.write_text(scene['title'])
 label=edit.get('label','真实操作录屏 · 合成场景 · 等待与操作加速');labelpath=WORK/(scene['id']+'-label.txt');labelpath.write_text(label)
 inputs=[];filters=[];names=[]
 for i,part in enumerate(edit['parts']):
  source=OUT/'raw'/part['file'];start,end=part['start'],part['end'];seconds=part['duration']
  inputs+=['-ss',str(start),'-t',str(end-start),'-i',str(source)]
  filters.append(f'[{i}:v]setpts=(PTS-STARTPTS)*{seconds/(end-start):.9f},fps={FPS},tpad=stop_mode=clone:stop_duration={seconds},trim=duration={seconds},scale=1800:880:force_original_aspect_ratio=decrease,pad={W}:{H}:(ow-iw)/2:110:color=0xf1f6ed,setsar=1[v{i}]')
  names.append(f'[v{i}]')
 filters.append(''.join(names)+f'concat=n={len(names)}:v=1:a=0[base]')
 filters.append(f"[base]drawtext=fontfile='{FONT}':textfile='{titlefile}':expansion=none:fontsize=39:fontcolor=0x193e2e:x=92:y=28,drawtext=fontfile='{FONT}':textfile='{labelpath}':expansion=none:fontsize=22:fontcolor=0x627a68:x=94:y=81,drawbox=x=0:y=1004:w=1920:h=76:color=0xf1f6ed:t=fill[out]")
 run(['ffmpeg','-hide_banner','-loglevel','error','-y',*inputs,'-filter_complex',';'.join(filters),'-map','[out]','-an','-t',str(scene['duration']),'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p',dest])
 return dest

def timestamp(seconds):
 c=int(round(seconds*100));return f'{c//360000}:{c//6000%60:02}:{c//100%60:02}.{c%100:02}'
def subtitle_chunks(narration,maxlen=34):
 chunks=[];acc=''
 for frag in re.split(r'(?<=[。；！？])',narration):
  if not frag:continue
  if len(acc)+len(frag)>maxlen and acc:chunks.append(acc);acc=''
  while len(frag)>maxlen:
   cut=max(frag.rfind('，',0,maxlen+1),frag.rfind('、',0,maxlen+1))
   cut=cut+1 if cut>8 else maxlen
   if acc:chunks.append(acc);acc=''
   chunks.append(frag[:cut]);frag=frag[cut:]
  acc+=frag
 if acc:chunks.append(acc)
 return chunks

def add_audio_subtitles(scene,visual):
 audio=OUT/'audio'/(scene['id']+'.aiff');ad=duration(audio);space=scene['duration']-.6
 speed=max(1,ad/space);voiced=ad/speed
 ass=WORK/(scene['id']+'.ass')
 header='''[Script Info]\nScriptType: v4.00+\nPlayResX: 1920\nPlayResY: 1080\nWrapStyle: 2\n[V4+ Styles]\nFormat: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,Bold,Italic,Underline,StrikeOut,ScaleX,ScaleY,Spacing,Angle,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding\nStyle: Default,Arial Unicode MS,31,&H00FFFFFF,&H00FFFFFF,&H4023422D,&H4023422D,0,0,0,0,100,100,0,0,3,9,0,2,90,90,20,1\n[Events]\nFormat: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text\n'''
 lines=[]
 sections=scene.get('narration_parts') or [{'start':0,'duration':voiced+.25,'text':scene['narration']}]
 for section in sections:
  chunks=subtitle_chunks(section['text']);units=sum(len(x) for x in chunks);elapsed=section['start']+.25
  voice_time=section.get('voice_seconds',voiced if len(sections)==1 else section['duration']-.7)
  for chunk in chunks:
   end=elapsed+voice_time*len(chunk)/units;lines.append(f'Dialogue: 0,{timestamp(elapsed)},{timestamp(end)},Default,,0,0,0,,{chunk}');elapsed=end
 ass.write_text(header+'\n'.join(lines)+'\n')
 dest=WORK/(scene['id']+'.mp4')
 run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',visual,'-i',audio,'-vf',f"ass='{ass}':fontsdir='/System/Library/Fonts/Supplemental',fade=t=in:st=0:d=0.25:color=0xf1f6ed,fade=t=out:st={scene['duration']-.25}:d=0.25:color=0xf1f6ed",'-af',f'atempo={speed:.8f},adelay=250|250,apad','-t',str(scene['duration']),'-r',FPS,'-c:v','libx264','-preset','veryfast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-ar','48000','-ac','2',dest])
 return dest

def soundtrack(seconds):
 sr=44100;n=int(sr*seconds);t=np.arange(n)/sr;signal=np.zeros(n,dtype=np.float32)
 chords=[(130.8128,164.8138,195.9977),(110,130.8128,164.8138),(87.3071,110,130.8128),(97.9989,123.4708,146.8324)]
 for i,start in enumerate(range(0,int(seconds),12)):
  length=min(14,seconds-start);count=int(length*sr);tt=np.arange(count)/sr
  env=np.minimum(1,tt/2)*np.minimum(1,(length-tt)/2)
  chord=chords[i%4];v=sum(np.sin(2*np.pi*f*tt)+.2*np.sin(2*np.pi*2*f*tt) for f in chord)/3
  signal[start*sr:start*sr+count]+=v*env*.010
 signal*=np.minimum(1,t/3)*np.minimum(1,(seconds-t)/3)
 stereo=np.stack([signal,signal*.94],axis=1);p=WORK/'original-ambient.wav'
 with wave.open(str(p),'wb') as wav:
  wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(sr);wav.writeframes((stereo*32767).astype('<i2').tobytes())
 return p

def main():
 parser=argparse.ArgumentParser();parser.add_argument('--only',default='all',help='all, animation, or comma-separated scene ids');parser.add_argument('--reuse-visuals',action='store_true');args=parser.parse_args()
 edits=json.loads((OUT/'edit-map.json').read_text()) if (OUT/'edit-map.json').exists() else {}
 selected=[s for s in SPEC['scenes'] if args.only=='all' or (args.only=='animation' and s['kind']=='animation') or s['id'] in args.only.split(',')]
 for scene in selected:
  print('Rendering',scene['id'],flush=True)
  previous=WORK/(scene['id']+'-visual.mp4')
  visual=previous if args.reuse_visuals and previous.exists() else (render_animation(scene) if scene['kind']=='animation' else recording_visual(scene,edits[scene['id']]))
  add_audio_subtitles(scene,visual);print('Ready',scene['id'],flush=True)
 if args.only!='all':return
 for s in SPEC['scenes']:
  streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(WORK/(s['id']+'.mp4'))],text=True))['streams']
  audio=next(x for x in streams if x['codec_type']=='audio')
  assert audio['sample_rate']=='48000' and audio['channels']==2, 'Concat requires matching AAC configuration'
 listing=WORK/'concat.txt';listing.write_text(''.join(f"file '{WORK/(s['id']+'.mp4')}'\n" for s in SPEC['scenes']))
 joined=WORK/'joined.mp4';run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',listing,'-c','copy',joined])
 total=sum(s['duration'] for s in SPEC['scenes']);music=soundtrack(total);target=OUT/'healthy-care-demo-v2.mp4'
 run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',joined,'-i',music,'-filter_complex','[0:a]loudnorm=I=-17:TP=-2:LRA=10[voice];[voice][1:a]amix=inputs=2:duration=first:normalize=0[a]','-map','0:v','-map','[a]','-c:v','copy','-c:a','aac','-b:a','160k','-ar','48000','-ac','2','-t',str(total),'-movflags','+faststart',target])
 actual=duration(target);assert 180<=actual<=300
 timeline=[];elapsed=0
 for s in SPEC['scenes']:
  timeline.append({**s,'start':elapsed,'end':elapsed+s['duration'],'edit':edits.get(s['id'])});elapsed+=s['duration']
 (OUT/'timeline.json').write_text(json.dumps({'duration_seconds':actual,'resolution':[W,H],'fps':FPS,'contains_continuous_screen_recordings':True,'edited_segments':True,'synthetic_scenarios':True,'ai_narration':True,'original_procedural_music':True,'scenes':timeline},ensure_ascii=False,indent=2))
 print('Completed',target,'duration',actual,flush=True)

if __name__=='__main__':main()
