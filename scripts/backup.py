#!/usr/bin/env python3
"""Consistent private backup of this checkout's Docker deployment.

Temporarily stops writers; restores their previous running state in finally.
Backups contain private data. Do not publish or commit them.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parents[1]

def run_backup(env_file: Path, output: Path):
    output.mkdir(parents=True,exist_ok=False,mode=0o700)
    base=['docker','compose','--env-file',str(env_file)]
    def command(args,**kwargs):return subprocess.run(base+args,cwd=ROOT,check=True,**kwargs)
    state=command(['ps','--format','json'],capture_output=True,text=True).stdout
    entries=[json.loads(line) for line in state.splitlines() if line.strip()]
    writers=[row['Service'] for row in entries if row['Service'] in ('gateway','api','worker','agent-runtime') and row.get('State')=='running']
    try:
        if writers:command(['stop',*writers],stdout=subprocess.DEVNULL)
        with (output/'database.dump').open('wb') as stream:
            command(['exec','-T','postgres','pg_dump','-U','hc_owner','-d','healthycare','-Fc'],stdout=stream)
        with (output/'attachments.tar.gz').open('wb') as stream:
            command(['run','--rm','--no-deps','-T','--entrypoint','tar','api','-C','/data/files','-czf','-','.'],stdout=stream)
        manifest={'version':1,'created_at':datetime.now(timezone.utc).isoformat(),'files':{}}
        for name in ('database.dump','attachments.tar.gz'):
            path=output/name;path.chmod(0o600)
            manifest['files'][name]=hashlib.sha256(path.read_bytes()).hexdigest()
        (output/'manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
        (output/'manifest.json').chmod(0o600)
    finally:
        if writers:command(['start',*writers],stdout=subprocess.DEVNULL)
    print(f'Backup saved: {output}. Configuration keys must be retained separately.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--env-file',type=Path,default=ROOT/'.env');parser.add_argument('--output',type=Path)
    args=parser.parse_args();stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    run_backup(args.env_file.resolve(),args.output or ROOT/'.local/backups'/stamp)
