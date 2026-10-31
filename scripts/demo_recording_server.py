#!/usr/bin/env python3
"""Loopback-only recorder for browser-selected, real tab capture. No app mocking."""
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from pathlib import Path
import argparse, json, re, time

ROOT = Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser()
parser.add_argument('--output', default='output/video-v2')
args=parser.parse_args()
OUT = ROOT / args.output
RAW = OUT / 'raw'
RAW.mkdir(parents=True, exist_ok=True)
PAGE = r'''<!doctype html><html lang="zh"><meta charset="utf-8"><title>健康伙伴 · 录制控制台</title>
<style>body{font:18px system-ui;background:#eef5ed;color:#214d3b;max-width:850px;margin:70px auto}h1{font-size:34px}button,input{font:inherit;padding:14px 22px;border:1px solid #b8cfbc;border-radius:12px;margin:8px}button{background:#1f6848;color:white}#log{white-space:pre-wrap;padding:22px;background:white;border-radius:18px}small{display:block;margin:20px 0;color:#5b7465}</style>
<h1>伴AI·健康伙伴 / 真实录屏</h1><p>只选择本次演示的健康伙伴标签页，不录制桌面、其他标签或麦克风。</p>
<input id="name" value="user-covid" aria-label="录制名称"><button id="start">开始标签页录制</button><button id="stop" disabled>停止并保存</button><small>视频由浏览器 MediaRecorder 连续采集，分块保存在本机项目；本页不含服务密钥。</small><div id="log">尚未录制</div>
<script>
let recorder, stream, pending=Promise.resolve(), started, seq=0, base;
const log=t=>document.querySelector('#log').textContent=t;
document.querySelector('#start').onclick=async()=>{try{
 base=document.querySelector('#name').value;if(!/^[a-z0-9-]{1,64}$/.test(base))throw Error('录制名称格式无效');
 stream=await navigator.mediaDevices.getDisplayMedia({video:{displaySurface:'browser',frameRate:30,width:1920,height:1080},audio:false,preferCurrentTab:false,selfBrowserSurface:'exclude',surfaceSwitching:'exclude',systemAudio:'exclude'});
 if(stream.getVideoTracks()[0].getSettings().displaySurface!=='browser'){stream.getTracks().forEach(t=>t.stop());throw Error('请只选择健康伙伴浏览器标签页');}
 await fetch('/begin/'+base,{method:'POST'});seq=0;started=Date.now();
 const mime=['video/webm;codecs=vp9','video/webm;codecs=vp8','video/webm'].find(x=>MediaRecorder.isTypeSupported(x));
 recorder=new MediaRecorder(stream,{mimeType:mime,videoBitsPerSecond:5500000});
 recorder.ondataavailable=e=>{if(e.data.size){const n=seq++;pending=pending.then(async()=>{const r=await fetch('/chunk/'+base+'/'+n,{method:'POST',body:e.data});if(!r.ok)throw Error('保存分块失败');});}};
 recorder.onstop=async()=>{await pending;stream.getTracks().forEach(t=>t.stop());const duration=(Date.now()-started)/1000;await fetch('/finish/'+base,{method:'POST',body:JSON.stringify({duration_seconds:duration,chunks:seq,settings:stream.getVideoTracks()[0].getSettings(),mime})});log('已保存 '+base+'.webm / '+duration.toFixed(1)+' 秒');document.querySelector('#start').disabled=false;document.querySelector('#stop').disabled=true;};
 recorder.start(1000);log('正在连续录制 '+base+'；切换回健康伙伴进行操作。');document.querySelector('#start').disabled=true;document.querySelector('#stop').disabled=false;
 }catch(e){log(e.message);}};
document.querySelector('#stop').onclick=()=>{if(recorder?.state==='recording')recorder.stop();};
</script></html>'''

class Handler(BaseHTTPRequestHandler):
 def do_GET(self):
  if self.path in ('/', '/record'):
   data=PAGE.encode();kind='text/html; charset=utf-8'
  elif self.path=='/status':
   data=json.dumps([{'name':p.name,'size':p.stat().st_size} for p in RAW.iterdir()]).encode();kind='application/json'
  elif self.path=='/synthetic-antigen.png':
   p=OUT/'assets/synthetic-antigen.png'
   if not p.exists():self.send_error(404);return
   data=p.read_bytes();kind='image/png'
  else:self.send_error(404);return
  self.send_response(200);self.send_header('Content-Type',kind);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
 def do_POST(self):
  if self.headers.get('Origin') not in (None,'http://127.0.0.1:8877'):
   self.send_error(403);return
  m=re.fullmatch(r'/(begin|chunk|finish)/([a-z0-9-]{1,64})(?:/(\d+))?',self.path)
  if not m:self.send_error(404);return
  op,name,seq=m.groups();n=int(self.headers.get('Content-Length','0'))
  if n>16*1024*1024:self.send_error(413);return
  data=self.rfile.read(n);p=RAW/(name+'.webm')
  if op=='begin':
   if p.exists():self.send_error(409);return
   p.touch();(RAW/(name+'-start.json')).write_text(json.dumps({'started_at':time.time(),'capture':'browser-getDisplayMedia','synthetic_only':True}))
  elif op=='chunk':
   with p.open('ab') as f:f.write(data)
  elif op=='finish':(RAW/(name+'-capture.json')).write_bytes(data)
  self.send_response(200);self.end_headers();self.wfile.write(b'ok')
 def log_message(self,*args):pass

if __name__=='__main__':
 print('Recorder ready at http://127.0.0.1:8877',flush=True)
 ThreadingHTTPServer(('127.0.0.1',8877),Handler).serve_forever()
