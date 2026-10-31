#!/usr/bin/env python3
"""Narrated walkthrough using genuine UI captures; explicitly not continuous recording."""
import json,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'output/video';FONT='/System/Library/Fonts/Supplemental/Arial Unicode.ttf'
SCENES=[
('问题与定位','docs/screenshots/deployment-login.png','院外小病缺少连续记录','伴AI健康伙伴关注一个常见问题：日常轻症往往在院外自行处理，症状变化、实际用药和没有就医的经历，很难形成连续且可核实的记录。作品面向适合自主护理的成年人，用户端与科研端分开。本视频用合成场景和实际界面截图分步讲解，不是连续录屏，旁白使用人工智能配音。'),
('图文对话','docs/screenshots/live-model-chat-20261023.png','自由描述，不需要选择病种','用户直接通过对话描述不适，也可以添加图片。这里展示真实模型对人工红蓝色块的回复，仅验证图片传输与区域描述，不能当成医学影像诊断能力。助手整理信息时保留未知和否定，不根据常识补造用户没有说过的事实，也不发布未经专业审阅的具体药品用量。'),
('确认与保存','output/video/captures/confirmation.png','动作草案先核对，确认后才保存','模型生成的是待核对草案，不能自行声称已经保存。这里是实际操作时截取的结束跟进确认卡。用户确认后，后端检查记录归属、读取版本和幂等状态，再完成写入。日常变化和实际用药也经过相同的确认边界；更正记录不能另建重复条目，缺失评分不能补零。'),
('恢复后的关照','output/video/captures/recovery.png','旧记录是历史，不自动续药','完成归档后，首页重新询问今天有没有不适，同时保留康复后的关照与历史观察。截图来自实际确认后的首页，旧鼻塞记录清楚标记为已结束、非当前不适。历史资料不会重新激活疾病，也不会自动续药。每日内容只引用实际记录，不把一条自评分包装成恢复趋势。'),
('独立研究授权','output/video/captures/consent.png','不参加研究，仍可使用个人健康空间','个人服务和科研使用分开。这里的健康记录研究与影像研究默认没有授权，用户可以了解用途后分别决定。研究默认不开放身份、聊天或图片，授权撤回会使旧研究快照失效。展示的是虚构账户，不是真实患者。我们不把简单去标识化或小样本隐藏称为绝对匿名。'),
('科研工作区','docs/screenshots/research-desktop.png','统一队列、时间窗、分母与来源','科研端提供数据概览、记录缺失、用药待核对、评分描述、队列与任务。筛选条件共同决定冻结输入，纳入和排除都有依据。未知用药、有记录但明确未用、完全没有记录是三种不同状态。候选线索用于后续核实，不是已经证实的滥用；归档和评分下降也不代表医学治愈。'),
('SciencePal实际执行','docs/screenshots/sciencepal-completed-20261023.png','真实平台运行，产物认证取回','SciencePal是实际科研执行环节。截图展示已完成的患者日分析任务，平台核对输入与脚本哈希，实际运行Python并生成报告和日志。新增记录组件实验也已在平台完成评分，通过认证接口取回报告，与本地独立重算完全一致。平台执行既有模型观测的评分，不冒称模型采集本身发生在平台。'),
('对照与局限','output/video/captures/benchmark.png','48例组件实验，尚未证明定向策略更优','新增实验先冻结六十个合成事件，按模板簇划分十二例开发和四十八例测试。初始描述、通用追问、定向追问的来源支持字段召回率，分别为百分之三十点一、七十七点九五和七十九点九七。定向相对通用差约二个百分点，但区间包含零，尚不能证明更优。这不是临床或产品整体准确率。'),
('复现与下一步','output/video/captures/daily.png','源码、协议、失败记录与平台产物可复核','作品使用Go业务后端、LangGraph运行时、PostgreSQL与Redis，通过Docker部署。源码、固定观测、评分协议和真实失败记录随材料提供。工程验收和平台复算已经完成，未来重点是自然语言基准、未知编码与独立可用性反馈，而不是增加没有验证的医疗承诺。评审入口和团队声明须在提交前最终确认。')]
def duration(p):return float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','default=nw=1:nk=1',str(p)],text=True))
def main():
 OUT.mkdir(parents=True,exist_ok=True);work=OUT/'render';work.mkdir(exist_ok=True);timeline=[];elapsed=0
 for i,(title,img,caption,narration) in enumerate(SCENES):
  tag=f'{i:02}';txt=work/(tag+'.txt');txt.write_text(narration);audio=work/(tag+'.aiff');subprocess.run(['say','-v','Tingting','-r','205','-f',str(txt),'-o',str(audio)],check=True)
  seconds=max(21,duration(audio)+1.0);titlefile=work/(tag+'-title.txt');titlefile.write_text(f'{i+1:02}  {title}');capfile=work/(tag+'-caption.txt');capfile.write_text(caption)
  disclosure=work/'disclosure.txt';disclosure.write_text('实际界面分步讲解 · 合成场景 · 非连续录屏 · AI配音')
  filt=f"scale=1740:800:force_original_aspect_ratio=decrease,pad=1920:1080:(ow-iw)/2:125:color=0xf5f9f1,drawtext=fontfile='{FONT}':textfile='{titlefile}':fontsize=44:fontcolor=0x285d43:x=90:y=35,drawtext=fontfile='{FONT}':textfile='{capfile}':fontsize=34:fontcolor=0x304c3d:x=(w-tw)/2:y=955,drawtext=fontfile='{FONT}':textfile='{disclosure}':fontsize=23:fontcolor=0x687a6a:x=(w-tw)/2:y=1024"
  if i==7:
   results=work/'results-table.txt';results.write_text('冻结测试：48个合成事件 / 16个模板簇\n\n初始描述           30.10%   失败0例\n通用结构化追问     77.95%   失败2例\n定向结构化追问     79.97%   失败1例\n\n定向减通用：+2.01个百分点\n95%区间：-4.31 至 +10.69 个百分点\n\n区间包含零，尚未证明定向策略更优。\n组件实验，不代表临床或产品整体准确率。'.replace(chr(92)+'n',chr(10)))
   filt+=f",drawbox=x=150:y=135:w=1620:h=770:color=0xf5f9f1:t=fill,drawtext=fontfile='{FONT}':textfile='{results}':expansion=none:fontsize=43:line_spacing=15:fontcolor=0x304c3d:x=300:y=170"
  segment=work/(tag+'.mp4');subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-loop','1','-i',str(ROOT/img),'-i',str(audio),'-vf',filt,'-af','apad','-t',str(seconds),'-r','12','-c:v','libx264','-preset','fast','-crf','22','-pix_fmt','yuv420p','-c:a','aac','-b:a','128k',str(segment)],check=True)
  timeline.append({'start':elapsed,'end':elapsed+seconds,'title':title,'source':img,'narration':narration});elapsed+=seconds;print('Rendered',title,round(seconds,1),flush=True)
 listing=work/'concat.txt';listing.write_text(''.join(f"file '{(work/(f'{i:02}.mp4')).resolve()}'\n" for i in range(len(SCENES))))
 target=OUT/'healthy-care-demo.mp4';subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',str(listing),'-c','copy','-movflags','+faststart',str(target)],check=True)
 actual=duration(target);assert 180<=actual<=300,f'Video duration {actual} outside contest range'
 (OUT/'timeline.json').write_text(json.dumps({'duration_seconds':actual,'continuous_recording':False,'synthetic_scenarios':True,'ai_narration':True,'scenes':timeline},ensure_ascii=False,indent=2));print('Video ready:',round(actual,1),'seconds',flush=True)
if __name__=='__main__':main()
