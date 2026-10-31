#!/usr/bin/env python3
"""Reset only this project's explicitly isolated, synthetic acceptance database."""
from pathlib import Path
import subprocess
import sys
root=Path(__file__).resolve().parents[1]
envfile=root/'.local/acceptance.env'
cfg=dict(line.split('=',1) for line in envfile.read_text().splitlines() if line and not line.startswith('#'))
if cfg.get('COMPOSE_PROJECT_NAME')!='healthy-care-test' or cfg.get('AGENT_PROVIDER')!='test' or cfg.get('ENABLE_TEST_PROVIDER')!='true':
    sys.exit('Refusing to reset a non-test environment.')
if cfg.get('SCIENCEPAL_API_KEY') or cfg.get('MODEL_API_KEY'):
    sys.exit('Refusing to reset an environment configured with real external keys.')
base=['docker','compose','--env-file',str(envfile),'-p','healthy-care-test']
subprocess.run(base+['stop','worker','agent-runtime'],cwd=root,check=True,stdout=subprocess.DEVNULL)
sql="""TRUNCATE users RESTART IDENTITY CASCADE;
DELETE FROM product_leaflets WHERE data->>'data_origin'='synthetic';
DO $$DECLARE r record; BEGIN FOR r IN SELECT tablename FROM pg_tables WHERE schemaname='agent' AND tablename<>'checkpoint_migrations' LOOP EXECUTE format('TRUNCATE TABLE agent.%I CASCADE',r.tablename); END LOOP; END$$;"""
subprocess.run(base+['exec','-T','postgres','psql','-v','ON_ERROR_STOP=1','-U','hc_owner','-d','healthycare','-c',sql],cwd=root,check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
subprocess.run(base+['exec','-T','redis','redis-cli','FLUSHDB'],cwd=root,check=True,stdout=subprocess.DEVNULL)
subprocess.run(base+['restart','api'],cwd=root,check=True,stdout=subprocess.DEVNULL)
subprocess.run(base+['up','-d','--no-build','agent-runtime','worker','gateway'],cwd=root,check=True,stdout=subprocess.DEVNULL)
print('Reset only the isolated synthetic acceptance stack; reference knowledge is preserved.')
