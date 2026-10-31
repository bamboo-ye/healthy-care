#!/usr/bin/env python3
"""Create checkout-local secrets without printing them or overwriting configuration."""
from pathlib import Path
import secrets
import os

root = Path(__file__).resolve().parents[1]
target = root / '.env'
if target.exists():
    content=target.read_text()
    if 'RUN_SIGNING_KEY=' not in content:
        with target.open('a') as handle:handle.write('\nRUN_SIGNING_KEY='+secrets.token_hex(24)+'\n')
    target.chmod(0o600)
    print('.env existing values preserved; required new secrets added if missing.')
else:
    content = (root / '.env.example').read_text()
    for key in ('POSTGRES_PASSWORD', 'APP_DB_PASSWORD', 'AGENT_DB_PASSWORD', 'INTERNAL_TOKEN', 'RUN_SIGNING_KEY', 'RESEARCH_PASSWORD'):
        content = content.replace(f'{key}=\n', f'{key}={secrets.token_hex(24)}\n')
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as handle:
        handle.write(content)
    print('Created .env with private local credentials. Configure model and SciencePal values locally.')
