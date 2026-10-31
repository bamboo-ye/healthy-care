#!/usr/bin/env python3
"""Build an allowlisted source archive; refuse configured secrets or symlinks."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'output/submission';EXCLUDED={'node_modules','dist','__pycache__','.pytest_cache','.venv','.local','.git','test-results'}
def main():
 paths=[]
 for folder in ['agent','backend','apps/web','deploy','tests','analysis','prototype','docs']:
  for p in (ROOT/folder).rglob('*'):
   if any(x in EXCLUDED for x in p.relative_to(ROOT).parts) or not p.is_file():continue
   if p.is_symlink():raise ValueError('Symlink not allowed in source archive')
   paths.append(p)
 for name in ['README.md','.env.example','compose.yaml','compose.production.yaml','compose.server.yaml','.dockerignore','.gitignore']:
  paths.append(ROOT/name)
 paths.extend(p for p in (ROOT/'scripts').glob('*.py') if not p.name.startswith('_'))
 for name in ['project-brief.md','demo-script.md','resource-statement.md','usability-session-kit.md','competition-gap-review-2026-10-24.md']:
  paths.append(ROOT/'docs/submission'/name)
 for name in ['operations.md','implementation-status.md','sciencepal-integration.md','live-service-acceptance-2026-10-23.md','sciencepal-live-acceptance-2026-10-23.md','sciencepal-agent-system-prompt.md']:
  paths.append(ROOT/'docs'/name)
 secrets=[]
 for line in '\n'.join(p.read_text() for p in [ROOT/'.env',ROOT/'.local/server-production.env'] if p.exists()).splitlines():
  if '=' not in line:continue
  k,v=line.split('=',1);v=v.strip().strip('"').strip("'")
  if any(x in k for x in ['KEY','PASSWORD','SECRET','TOKEN']) and len(v)>=12:secrets.append(v.encode())
 paths=sorted(set(paths));manifest={}
 OUT.mkdir(parents=True,exist_ok=True)
 target=OUT/'healthy-care-source.zip'
 # Validate everything before replacing a previous deliverable.
 for p in paths:
  raw=p.read_bytes()
  if any(s in raw for s in secrets):raise ValueError('Configured secret detected; archive not written')
  manifest[str(p.relative_to(ROOT))]=hashlib.sha256(raw).hexdigest()
 with zipfile.ZipFile(target.with_suffix('.tmp'),'w',zipfile.ZIP_DEFLATED) as z:
  for p in paths:z.write(p,p.relative_to(ROOT))
  z.writestr('SOURCE-MANIFEST.json',json.dumps(manifest,ensure_ascii=False,indent=2))
 target.with_suffix('.tmp').replace(target)
 (OUT/'source-manifest.json').write_text(json.dumps({'archive_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'files':manifest},ensure_ascii=False,indent=2)+'\n')
 kit_files=[(target,'healthy-care-source.zip')]
 for name,label in [('output/pdf/health-companion-project-description.pdf','project-brief.pdf'),('output/video-v7/healthy-care-demo-v7.mp4','demo.mp4'),('output/video-v7/timeline.json','video-timeline.json'),('output/recording-benchmark-20261024.zip','recording-benchmark.zip'),('output/recording-benchmark-unknown-sensitivity-20261026.json','unknown-sensitivity.json')]:
  p=ROOT/name
  if p.exists():kit_files.append((p,label))
 for p in (ROOT/'docs/submission').glob('*.md'):kit_files.append((p,'documents/'+p.name))
 for p in (ROOT/'output/recording-benchmark-platform-evidence-20261024').glob('*'):
  if p.is_file():kit_files.append((p,'platform-evidence/'+p.name))
 for p,_ in kit_files:
  if any(s in p.read_bytes() for s in secrets):raise ValueError('Secret in kit; not written')
 kit=OUT/'healthy-care-submission-kit.zip'
 with zipfile.ZipFile(kit,'w',zipfile.ZIP_DEFLATED) as z:
  for p,name in kit_files:z.write(p,name)
  z.writestr('START-HERE.txt','Read documents/submission-index.md. Top-level demo.mp4, project-brief.pdf, recording-benchmark.zip and healthy-care-source.zip are prepared deliverables. Team signature and official submission still require confirmation. Public endpoints are listed in the index; temporary tunnel addresses can change.\n')
 print(f'Built {len(paths)} allowlisted source files and delivery kit; local/server configured secret scan passed.')
if __name__=='__main__':main()
