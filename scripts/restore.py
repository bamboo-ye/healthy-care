#!/usr/bin/env python3
"""Restore only to a new, isolated Compose project; never overwrite a live volume."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
from backup import ROOT

def restore(env_file: Path, backup: Path, project: str):
    if not re.fullmatch(r'healthy-care-restore-[a-z0-9-]+',project):raise ValueError('Use a new healthy-care-restore-* project name.')
    volumes=subprocess.run(['docker','volume','ls','--filter',f'label=com.docker.compose.project={project}','--format','{{.Name}}'],capture_output=True,text=True,check=True).stdout
    if volumes.strip():raise ValueError('Restore target already has volumes; refusing to overwrite.')
    manifest=json.loads((backup/'manifest.json').read_text())
    for name in ('database.dump','attachments.tar.gz'):
        if hashlib.sha256((backup/name).read_bytes()).hexdigest()!=manifest['files'][name]:raise ValueError('Backup hash mismatch: '+name)
    base=['docker','compose','--env-file',str(env_file),'-p',project]
    def command(args,**kwargs):return subprocess.run(base+args,cwd=ROOT,check=True,**kwargs)
    command(['up','-d','--no-build','--wait','postgres','redis'],stdout=subprocess.DEVNULL)
    # Init has created empty role schemas. Dump recreates the frozen schema contents.
    command(['exec','-T','postgres','psql','-v','ON_ERROR_STOP=1','-U','hc_owner','-d','healthycare','-c','DROP SCHEMA agent CASCADE;'],stdout=subprocess.DEVNULL)
    with (backup/'database.dump').open('rb') as stream:
        command(['exec','-T','postgres','pg_restore','-U','hc_owner','-d','healthycare','--exit-on-error'],stdin=stream)
    with (backup/'attachments.tar.gz').open('rb') as stream:
        command(['run','--rm','--no-deps','-T','--entrypoint','tar','api','-C','/data/files','-xzf','-'],stdin=stream,stdout=subprocess.DEVNULL)
    print(f'Restored {project}; services have not been exposed or started. Use a separate HTTP_PORT before starting the app.')

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--env-file',type=Path,required=True);parser.add_argument('--backup',type=Path,required=True);parser.add_argument('--project',required=True)
    args=parser.parse_args();restore(args.env_file.resolve(),args.backup.resolve(),args.project)
