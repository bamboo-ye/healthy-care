"""Publishable research supplements; excludes application source and credentials."""
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo
from html import escape
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'output/supplementary'
ORIGIN_FILE = ROOT / '.local/server-public-origin.json'
ORIGIN = (json.loads(ORIGIN_FILE.read_text())['origin'] if ORIGIN_FILE.exists()
          else 'https://admissions-broadband-bend-vanilla.trycloudflare.com')
REPO = 'https://github.com/bamboo-ye/healthy-care'
SHARE = 'https://sciencepal.ai/share/65ecd584-6adf-4000-88d9-4004e3f82a65'
DATE = datetime.now(ZoneInfo('Asia/Shanghai')).date().isoformat()

def write(name, value):
    path = OUT / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(value, encoding='utf8')
    return path

def write_json(name, value):
    return write(name, json.dumps(value, ensure_ascii=False, indent=2) + '\n')

def archive(name, files):
    target = OUT / name
    with zipfile.ZipFile(target, 'w', zipfile.ZIP_DEFLATED) as z:
        for source, member in files:
            z.write(source, member)
    return target

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    prompt_md = (ROOT / 'docs/sciencepal-agent-system-prompt.md').read_text()
    prompt = prompt_md[prompt_md.index('你是一个科研数据质量'):].strip()
    agent = {
        'schema': 'healthy-care-sanitized-agent-config-v1',
        'export_kind': 'project-maintained configuration description; not a native SciencePal import',
        'platform': 'SciencePal', 'name': '伴AI·健康伙伴｜院外健康科研Agent', 'version': '0.1.0',
        'system_prompt': prompt,
        'required_capabilities': ['Python code execution', 'sandbox file read/write'],
        'data_scope': 'synthetic inputs only',
        'model': {'selection': 'platform-managed', 'specific_model': None},
        'credentials_included': False,
        'task_inputs': ['health-research-input.json', 'manifest.json', 'run_analysis.py'],
        'expected_outputs': ['report.json', 'quality.csv', 'patient_days.csv', 'medication_candidates.csv', 'stdout.log', 'stderr.log'],
        'platform_sdk_contract_reference': '0.2.1; SDK not bundled',
        'public_replay': SHARE,
    }
    write_json('agent-config/agent-config.json', agent)
    write('agent-config/system-prompt.md', '# 科研Agent系统提示词 v0.1.0\n\n' + prompt + '\n')
    write('agent-config/README.md', '''# 科研Agent配置说明

这是本项目维护的脱密配置说明和实际保存的系统提示词，不是SciencePal官方原生导出文件。
不含API Key、账户登录信息、模型密钥、业务数据库地址或真实患者资料。
在SciencePal自己的账户中创建Agent，复制系统提示词，并启用代码执行和沙箱文件读写能力。
平台托管模型的具体型号没有在本项目记录中公开，因此配置中保持null。
使用应用的专用科研评审账号时，已有后台连接，无需另配密钥。
''')
    archive('agent-config.zip', [(p, str(p.relative_to(OUT / 'agent-config'))) for p in sorted((OUT / 'agent-config').glob('*'))])

    graph = json.loads((OUT / 'langgraph-workflow.json').read_text())
    assert {'context', 'triage', 'model', 'validate', 'confirmation'} <= {n['id'] for n in graph['nodes']}
    research_flow = {
        'schema': 'healthy-care-sciencepal-workflow-description-v1',
        'export_kind': 'project workflow description; not a native SciencePal import',
        'nodes': ['authorize_researcher', 'freeze_synthetic_input', 'create_manifest', 'submit_sciencepal_agent', 'poll_external_state', 'fetch_artifacts', 'independent_validation', 'publish_verified_result'],
        'edges': [[a,b] for a,b in zip(['authorize_researcher', 'freeze_synthetic_input', 'create_manifest', 'submit_sciencepal_agent', 'poll_external_state', 'fetch_artifacts', 'independent_validation'], ['freeze_synthetic_input', 'create_manifest', 'submit_sciencepal_agent', 'poll_external_state', 'fetch_artifacts', 'independent_validation', 'publish_verified_result'])],
        'non_success_states': ['external_asked', 'external_unknown', 'awaiting_import', 'failed', 'stopped', 'invalidated'],
        'verification': ['input hash', 'method/data/rule/knowledge versions', 'independently recomputed metrics'],
        'scope': 'synthetic external execution only; personal chat is a separate LangGraph workflow',
    }
    write_json('sciencepal-workflow.json', research_flow)
    write('workflow-README.md', f'''# 工作流结构导出

日期：{DATE}（Asia/Shanghai）。

- langgraph-workflow.json：只读连接实际部署的Agent容器，调用build_graph(None).get_graph().to_json()取得的LangGraph结构。
- context → triage → model/validate → confirmation → end。紧急分支可绕过模型；确认节点支持中断与恢复。
- sciencepal-workflow.json：按项目实现整理的科研联动流程说明，含冻结输入、平台执行、取回产物和独立校验。
- 这些文件不含节点函数实现、应用源码、数据库凭据、API密钥或会话。
- LangGraph结构JSON用于查看节点与连接关系，不足以单独启动应用；SciencePal说明不是平台原生一键导入格式。
- 本包仅导出结构；节点实现与完整应用源码另见项目GitHub仓库。
''')
    archive('workflow-exports.zip', [(OUT / n,n) for n in ['langgraph-workflow.json','sciencepal-workflow.json','workflow-README.md']])

    write('technical-report.md', f'''# 伴AI·健康伙伴：技术补充报告

更新：{DATE}（Asia/Shanghai）。项目独立部署，用户端与科研端按服务端角色隔离。

## 技术方案

React双入口前端通过Go API访问PostgreSQL。Go承担账户、归属、动作确认、版本、研究授权、队列快照与结果校验。
Python LangGraph运行时承担上下文、紧急路由、真实图文模型调用、输出校验和用户确认中断恢复，检查点存于PostgreSQL。
Redis仅用于公共知识缓存与限流。Docker Compose部署网关、API、worker、Agent、PostgreSQL/pgvector、Redis、备份和专用隧道。
pgvector已安装；当前小知识包使用确定性查询，未声称完成向量召回评估。私有文件采用卷权限隔离，未声称实现应用层文件加密。

## SciencePal核心工作

科研端冻结合成输入和版本清单，服务端调用自定义科研Agent，平台实际运行Python。
完成后经认证API取得report.json、CSV与日志，Go独立核验哈希、版本和指标，再发布结果。
用户日常对话模型通过OpenRouter配置，与SciencePal科研执行分开。
工作流结构、配置说明和系统提示词见本目录下载项；没有将项目生成说明称为平台原生导出。

## 数据与权限

用户确认前，模型只提出动作草案；写入事务重新核对归属、版本与授权。
研究与影像授权分开，撤回后对应快照失效。当前外部平台只开放合成数据，不上传真实用户聊天、身份或图片。
缺失、未知、明确未用与实际用药分别记录，不插值评分，不将归档等同于痊愈。

## 已有验证与局限

2026-10-23：运行时32项、真实模型基础6项与业务流程19项技术检查有保留证据；不合并为医学准确率。
2026-10-30：专用用户和科研评审账号登录、401/403角色边界及公开文件一致性已核验。
科研评审账号下SciencePal任务0ccc7791-daa9-4189-8e0b-588a7e09ffa3完成，产物经接口取得并通过独立校验。
固定48例合成队列：267/324患者日有记录，完整率82.4%，32项待核对候选。
独立追问组件实验见实验结果与复现包，定向相对通用差值区间包含零，未建立优越性。
没有独立真人可用性结果或临床有效性结论；医生问诊、处方确认和购药为拟接入能力。

## 访问与复现

- 科研端：{ORIGIN}/research/，使用非公开交付的专用评审账号。
- 公开运行回放：{SHARE}，无需登录，展示另一项独立组件评分实验。
- 项目说明PDF：{ORIGIN}/materials/health-companion-project-description.pdf。
- 本目录的报告、配置、工作流和实验包公开下载，不含评审账号密码。
''')
    write('usability-plan.md', (ROOT / 'docs/submission/usability-session-kit.md').read_text())
    write('technical-acceptance.md', '''# 软件与真实服务技术验收摘要

本页整理已有技术证据，不是独立真人用户测试，也不是临床验证。

| 日期 | 检查范围 | 结果 |
|---|---|---|
| 2026-10-23 | Python运行时 | 32项通过 |
| 2026-10-23 | 真实模型文字/人工色块传输 | 6项通过，仅技术链路 |
| 2026-10-23 | 真实模型完整业务流程 | 19项通过；包括未知保留、确认、更正、授权撤回、归档和紧急路由 |
| 2026-10-30 | 专用评审账号及API角色隔离 | 两端登录通过；未登录科研API 401，普通用户科研API 403，科研身份个人健康API 403 |
| 2026-10-30 | 评审账号SciencePal任务 | 已完成；认证API产物取回及独立核验通过 |

最终视频、PDF和公开链接已作一致性核验。独立可用性研究尚未招募或执行；任务表见usability-plan.md。
用户界面和虚构案例的产品操作不能作为真实患者结局证据。未发布未经专业审阅的具体药品用量。
''')
    results = (ROOT / 'docs/submission/benchmark-results-2026-10-24.md').read_text()
    results = results.replace('`python3 output/recording-benchmark-20261024/run_analysis.py output/recording-benchmark-20261024/health-research-input.json --out /tmp/health-benchmark-recheck`', '`python3 run_analysis.py health-research-input.json --out actual-output`（在复现包解压目录运行）')
    write('benchmark-results.md', results)

    with tempfile.TemporaryDirectory(prefix='healthy-care-reproduction-') as tmp:
        folder = Path(tmp)
        with zipfile.ZipFile(ROOT / 'output/recording-benchmark-20261024.zip') as z:
            assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
            z.extractall(folder)
        manifest = json.loads((folder/'manifest.json').read_text())
        for name, value in manifest['files'].items(): assert digest(folder/name) == value
        shutil.copyfile(ROOT/'analysis/recording_benchmark/unknown_sensitivity.py', folder/'unknown_sensitivity.py')
        shutil.copyfile(ROOT/'output/recording-benchmark-unknown-sensitivity-20261026.json', folder/'reference/unknown-sensitivity.json')
        evidence = folder/'platform-evidence';evidence.mkdir()
        for name in ['report.json','stdout.log','stderr.log','verification.json']:
            shutil.copyfile(ROOT/'output/recording-benchmark-platform-evidence-20261024'/name, evidence/name)
        (folder/'README.md').write_text('''# 记录采集组件实验复现

本包只含独立科研评分脚本、合成数据、冻结真实模型观测与运行证据。完整应用源码另见项目GitHub仓库。
Python 3.12标准库即可离线重算；无需模型密钥、SciencePal账号或再次调用供应商。

解压后进入本目录执行：

    python3 run_analysis.py health-research-input.json --out actual-output
    python3 unknown_sensitivity.py health-research-input.json --out actual-output/unknown-sensitivity.json

对比actual-output/report.json与reference/report.json、platform-evidence/report.json；整份JSON应一致。
敏感性分析与reference/unknown-sensitivity.json对比，属于事后分析，不替换主结果。
manifest.json保留原冻结材料哈希；SUPPLEMENT-MANIFEST.json校验本次全部补充文件。
数据集开发12/测试48，2类追问各一轮最多3字段。固定响应器、模板相关和未知编码等限制见protocol.md与结果说明。
SciencePal在该实验中评分既有模型观测，不是在平台运行OpenRouter采集。重算不是重新采集模型响应。
数据不含真实患者。主结果不能用作诊断或临床疗效指标。
''')
        output = folder/'actual-output'
        subprocess.run([sys.executable,str(folder/'run_analysis.py'),str(folder/'health-research-input.json'),'--out',str(output)], check=True, capture_output=True)
        actual = json.loads((output/'report.json').read_text())
        assert actual == json.loads((folder/'reference/report.json').read_text()) == json.loads((evidence/'report.json').read_text())
        subprocess.run([sys.executable,str(folder/'unknown_sensitivity.py'),str(folder/'health-research-input.json'),'--out',str(output/'unknown-sensitivity.json')], check=True, capture_output=True)
        assert json.loads((output/'unknown-sensitivity.json').read_text()) == json.loads((folder/'reference/unknown-sensitivity.json').read_text())
        shutil.rmtree(output)
        files = sorted(p for p in folder.rglob('*') if p.is_file())
        (folder/'SUPPLEMENT-MANIFEST.json').write_text(json.dumps({str(p.relative_to(folder)):digest(p) for p in files},ensure_ascii=False,indent=2)+'\n')
        archive('benchmark-reproduction.zip', [(p,str(p.relative_to(folder))) for p in sorted(folder.rglob('*')) if p.is_file()])
    archive('platform-evidence.zip', [(ROOT/'output/recording-benchmark-platform-evidence-20261024'/n,n) for n in ['report.json','stdout.log','stderr.log','verification.json']])

    items = [
        ('代码仓库', REPO, '公开源码、锁文件、部署配置与合成研究材料；本机凭据和原始个人记录不进入仓库。'),
        ('技术报告（五页项目说明）', ORIGIN+'/materials/health-companion-project-description.pdf', '公开PDF，无需登录。'),
        ('技术补充报告', 'technical-report.md', '公开下载Markdown，说明架构、SciencePal联动与验证边界。'),
        ('科研Agent配置与系统提示词', 'agent-config.zip', '公开下载；脱密配置说明，非SciencePal原生导入文件。'),
        ('工作流结构导出', 'workflow-exports.zip', '公开下载；实际LangGraph结构JSON与SciencePal联动说明，不含节点实现。'),
        ('用户测试执行计划', 'usability-plan.md', '公开下载；尚未招募或执行，无独立真人测试结果。'),
        ('软件与真实服务技术验收', 'technical-acceptance.md', '公开下载；软件检查与合成输入验收，不替代真人或临床研究。'),
        ('实验结果与局限', 'benchmark-results.md', '公开下载，含主结果与事后敏感性分析说明。'),
        ('可复现实验包', 'benchmark-reproduction.zip', '公开下载；独立科研脚本、合成观测、协议、哈希和参考结果；Python标准库可离线重算。'),
        ('SciencePal执行产物与日志', 'platform-evidence.zip', '公开下载；认证API取得的合成实验产物及校验记录。'),
        ('SciencePal公开运行回放', SHARE, '无需登录，只读回放独立追问组件实验。'),
        ('科研端运行与快照下载', ORIGIN+'/research/', '使用已交付的专用科研评审账号；分析任务中可下载当前冻结输入和任务包。'),
    ]
    write_json('materials.json', {'updated':DATE,'materials':[{'name':n,'url':url if url.startswith('https:') else ORIGIN+'/materials/supplementary/'+url,'access':access} for n,url,access in items]})
    rows=''.join('<tr><td>'+escape(n)+'</td><td><a href="'+escape(u,quote=True)+'">打开 / 下载</a></td><td>'+escape(a)+'</td></tr>' for n,u,a in items)
    write('index.html', '<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>伴AI·健康伙伴｜补充材料</title><style>body{font:15px/1.8 system-ui,"PingFang SC","Microsoft YaHei",sans-serif;color:#193e2e;background:#f3f7ef;max-width:1100px;margin:42px auto;padding:0 24px}h1{font-size:28px}table{width:100%;border-collapse:collapse;background:white}th,td{padding:15px;text-align:left;border-bottom:1px solid #dce6d7}th{background:#dfecdc}a{color:#28684a}p{color:#627a68}</style><h1>伴AI·健康伙伴 · 补充材料</h1><p>'+escape(DATE)+' · 报告、配置、工作流与科研复现材料</p><table><thead><tr><th>材料名称</th><th>链接</th><th>访问说明</th></tr></thead><tbody>'+rows+'</tbody></table><p>完整应用源码见GitHub仓库；可复现包仅含独立科研分析脚本和合成数据。用户测试计划不代表已经取得独立真人反馈。当前使用临时隧道域名，评审期间需保持服务运行。</p></html>')

    secrets=[]
    for envpath in [ROOT/'.env',ROOT/'.local/server-production.env']:
        if envpath.exists():
            for line in envpath.read_text().splitlines():
                if '=' not in line:continue
                k,v=line.split('=',1);v=v.strip().strip('"').strip("'")
                if any(s in k for s in ['KEY','PASSWORD','SECRET','TOKEN']) and len(v)>=12:secrets.append(v.encode())
    private = ROOT/'.local/reviewer-access.json'
    if private.exists():
        credentials=json.loads(private.read_text())
        for role in ['user','researcher']:secrets.append(credentials[role]['password'].encode())
    for p in OUT.rglob('*'):
        if not p.is_file():continue
        contents=[p.read_bytes()]
        if p.suffix=='.zip':
            with zipfile.ZipFile(p) as z:
                assert all(not n.startswith('/') and '..' not in Path(n).parts for n in z.namelist())
                assert not any(n.split('/')[-1] in ['.env','server-production.env','reviewer-access.json','reviewer-access.md'] for n in z.namelist())
                contents += [z.read(n) for n in z.namelist()]
        assert not any(s in body for body in contents for s in secrets), 'Configured credential detected'
    public_files = ['index.html','materials.json','technical-report.md','agent-config.zip','workflow-exports.zip','usability-plan.md','technical-acceptance.md','benchmark-results.md','benchmark-reproduction.zip','platform-evidence.zip']
    manifest = {n:{'bytes':(OUT/n).stat().st_size,'sha256':digest(OUT/n)} for n in public_files}
    write_json('manifest.json', {'date':DATE,'application_source_included':False,'offline_primary_reproduction':'passed','offline_sensitivity_reproduction':'passed','credential_scan':'passed','files':manifest})
    print(json.dumps({'public_files':len(public_files)+1,'credential_scan':'passed','primary_recompute':'passed','sensitivity_recompute':'passed','application_source_in_material_package':False},ensure_ascii=False))

if __name__=='__main__':main()
