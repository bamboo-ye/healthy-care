"""Export only synthetic benchmark observations and reproducible scorer."""
import argparse,hashlib,json,shutil,zipfile
from pathlib import Path
from run_analysis import evaluate
HERE=Path(__file__).resolve().parent

def main():
 p=argparse.ArgumentParser();p.add_argument('observations',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args();assert not a.out.exists();data=json.loads(a.observations.read_text());assert data['data_origin']=='synthetic'
 # Keep model request text and actual content/usage; exclude provider metadata.
 for o in data['observations']:
  o['calls']=[{'request':c['request'],'response_content':c['response']['choices'][0]['message']['content'],'usage':c['response'].get('usage'),'seconds':c['seconds']} for c in o['calls']]
 a.out.mkdir(parents=True);(a.out/'health-research-input.json').write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
 for name in ['run_analysis.py','protocol.md']:shutil.copyfile(HERE/name,a.out/name)
 (a.out/'reference').mkdir();(a.out/'reference/report.json').write_text(json.dumps(evaluate(data),ensure_ascii=False,indent=2)+'\n')
 manifest={'method_version':'recording-benchmark-v1','data_origin':'synthetic','files':{f.name:hashlib.sha256(f.read_bytes()).hexdigest() for f in a.out.iterdir() if f.is_file()}}
 (a.out/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
 (a.out/'TASK.md').write_text('''# 合成记录组件对照实验\n\n这是独立于既有患者日统计的新方法recording-benchmark-v1。输入为实际模型对冻结合成事件的响应，不含真实患者。\n\n先核对manifest内各文件字节SHA256，再实际执行：\n\npython3 run_analysis.py health-research-input.json --out actual-output > stdout.log 2> stderr.log\n\n保留退出码、stdout、stderr和actual-output/report.json；对照reference报告，不能复制参考结果冒充运行。报告主要成对差值、模板簇bootstrap区间、失败率和局限。不要把字段实验解释为生产整体收益或医学准确率，也不要更改原始观测。\n''')
 with zipfile.ZipFile(a.out.with_suffix('.zip'),'w',zipfile.ZIP_DEFLATED) as z:
  for f in sorted(a.out.rglob('*')):
   if f.is_file():z.write(f,f.relative_to(a.out))
 print(a.out)
if __name__=='__main__':main()
