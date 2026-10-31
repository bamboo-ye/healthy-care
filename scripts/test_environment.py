#!/usr/bin/env python3
"""Generate a separate, disposable acceptance environment with no external keys."""
from pathlib import Path
import os
import secrets
root=Path(__file__).resolve().parents[1]
target=root/'.local/acceptance.env'
if target.exists():
    if 'RUN_SIGNING_KEY=' not in target.read_text():
        with target.open('a') as handle:handle.write('\nRUN_SIGNING_KEY='+secrets.token_hex(24)+'\n')
    print('Preserved isolated acceptance environment.')
else:
    data=(root/'.env.example').read_text()
    for key in ('POSTGRES_PASSWORD','APP_DB_PASSWORD','AGENT_DB_PASSWORD','INTERNAL_TOKEN','RUN_SIGNING_KEY','RESEARCH_PASSWORD'):
        data=data.replace(f'{key}=\n',f'{key}={secrets.token_hex(24)}\n')
    data=data.replace('COMPOSE_PROJECT_NAME=healthy-care','COMPOSE_PROJECT_NAME=healthy-care-test').replace('HTTP_PORT=8780','HTTP_PORT=8782').replace('APP_ORIGIN=http://localhost:8780','APP_ORIGIN=http://localhost:8782').replace('AGENT_PROVIDER=unconfigured','AGENT_PROVIDER=test').replace('ENABLE_TEST_PROVIDER=false','ENABLE_TEST_PROVIDER=true')
    target.parent.mkdir(exist_ok=True)
    fd=os.open(target,os.O_CREAT|os.O_EXCL|os.O_WRONLY,0o600)
    with os.fdopen(fd,'w') as f:f.write(data)
    print('Created isolated acceptance environment. External model and SciencePal keys are empty.')
