"""One explicit SciencePal execution; never restarts on ambiguous submission."""
import argparse,hashlib,json,time,uuid
from pathlib import Path
from urllib import request,parse
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
def main():
 p=argparse.ArgumentParser();p.add_argument('--synthetic-only',required=True,action='store_true');p.add_argument('--pack',required=True,type=Path);p.add_argument('--out',required=True,type=Path);a=p.parse_args()
 cfg=dict(x.split('=',1) for x in (ROOT/'.env').read_text().splitlines() if x and not x.startswith('#') and '=' in x);base=cfg.get('SCIENCEPAL_BASE_URL','https://sciencepal.ai/api').rstrip('/');key=cfg['SCIENCEPAL_API_KEY']
 assert not a.out.exists();a.out.mkdir(parents=True,mode=0o700)
 def api(path,data=None,content_type='application/json',binary=False):
  headers={'Authorization':'Bearer '+key}
  if data is not None:headers['Content-Type']=content_type
  with request.urlopen(request.Request(base+path,data=data,headers=headers),timeout=120) as r:
   raw=r.read(2000001);assert len(raw)<=2000000
   return raw if binary else json.loads(raw)
 boundary='Benchmark-'+uuid.uuid4().hex;parts=[]
 def field(name,value):parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{name}"\r\n\r\n{value}\r\n'.encode())
 outdir='/workspace/healthy-care/benchmark-'+uuid.uuid4().hex
 prompt=f'''本次任务使用新的独立方法recording-benchmark-v1，而非旧患者日统计schema。只处理附件合成数据，不访问业务数据库，不调用外部模型。先以manifest核对输入、评分脚本和协议字节SHA256。实际执行附件Python：python3 run_analysis.py health-research-input.json --out {outdir} > {outdir}/stdout.log 2> {outdir}/stderr.log（先mkdir -p）。保留退出码。脚本计算三臂记录实验及2000次模板簇bootstrap，报告真实差值、错误和局限。禁止复制参考结果（本次不提供参考报告），禁止改数据或脚本生成预想结论。返回{outdir}/report.json、stdout.log和stderr.log路径。原始哈希和运行日志必须来自实际执行。如无法执行则如实报告。'''
 for k,v in {'agent_id':cfg['SCIENCEPAL_AGENT_ID'],'prompt':prompt,'stream':'true','agent_select_type':'manual'}.items():field(k,v)
 for name in ['health-research-input.json','run_analysis.py','manifest.json','protocol.md']:
  content=(a.pack/name).read_bytes();parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="files"; filename="{name}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode()+content+b'\r\n')
 parts.append(f'--{boundary}--\r\n'.encode())
 (a.out/'submission-intent.json').write_text(json.dumps({'output_dir':outdir,'automatic_resubmission':False,'data_origin':'synthetic'}))
 response=api('/agent/initiate',b''.join(parts),'multipart/form-data; boundary='+boundary)
 receipt={'initiate':response,'output_dir':outdir,'technical_status':'running'};(a.out/'receipt.json').write_text(json.dumps(receipt,indent=2));run=response['agent_run_id'];thread=response['thread_id'];print('Submitted synthetic benchmark task',run,flush=True)
 for _ in range(90):
  status=api('/agent-run/'+parse.quote(run,safe=''));receipt['status']=status;(a.out/'receipt.json').write_text(json.dumps(receipt,indent=2));state=status.get('status');print('SciencePal status:',state,flush=True)
  if state in ['completed','failed','stopped','cancelled','error']:break
  time.sleep(10)
 if state!='completed':raise RuntimeError('SciencePal did not complete; inspect saved receipt, no duplicate request sent')
 sandbox=api('/thread/'+thread+'/sandbox')['sandbox_id'];files={}
 for name in ['report.json','stdout.log','stderr.log']:
  blob=api('/sandboxes/'+sandbox+'/files/content?'+parse.urlencode({'path':outdir+'/'+name}),binary=True);(a.out/name).write_bytes(blob);files[name]=hashlib.sha256(blob).hexdigest()
 actual=json.loads((a.out/'report.json').read_text());expected=json.loads((a.pack/'reference/report.json').read_text());assert actual==expected,'Platform result differs from independent local report'
 receipt.update({'technical_status':'passed','verification':'authenticated-api-fetch-and-independent-recompute','sha256':files});(a.out/'receipt.json').write_text(json.dumps(receipt,indent=2));print('PASS: authenticated platform artifacts match independent local calculation',flush=True)
if __name__=='__main__':main()
