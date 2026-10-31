"""Daily backup container and file-deletion barrier, synthetic test stack only."""
import json
from pathlib import Path
import subprocess
import sys
from uuid import uuid4
from api_acceptance import Client, ROOT
from recovery_acceptance import BASE, compose, sql, eventually

def main():
    user=Client().register();assert user.call('/v1/system/status')['test_provider']
    user.do('喉咙不舒服（每日备份合成样例）','create_episode')
    image=user.upload();raw=user.call('/v1/health/attachments/'+image['id'],raw=True)
    output=compose('run','--rm','--no-deps','-T','-e','BACKUP_ONCE=true','backup',capture_output=True,text=True).stdout
    names=[line.split(': ',1)[1] for line in output.splitlines() if line.startswith('Private snapshot complete: ')]
    assert len(names)==1,'Daily backup must record exactly one completed snapshot'
    failed=subprocess.run(BASE+['run','--rm','--no-deps','-T','-e','BACKUP_ONCE=true','-e','PGDATABASE=missing_acceptance_database','backup'],cwd=ROOT,capture_output=True,text=True)
    assert failed.returncode!=0 and 'Private snapshot complete:' not in failed.stdout,'A failed backup must never be marked complete'
    suffix=uuid4().hex[:10];folder=ROOT/'.local/backups'/('container-'+suffix);folder.mkdir(mode=0o700)
    compose('cp','backup:/backups/'+names[0]+'/.',str(folder),stdout=subprocess.DEVNULL)
    sys.path.insert(0,str(ROOT/'scripts'))
    from restore import restore
    project='healthy-care-restore-'+suffix
    try:
        restore(ROOT/'.local/acceptance.env',folder,project)
        assert sql(f"SELECT count(*) FROM episodes WHERE user_id='{user.user['id']}'",project)=='1'
        restored=subprocess.run(['docker','compose','--env-file',str(ROOT/'.local/acceptance.env'),'-p',project,'run','--rm','--no-deps','-T','--entrypoint','cat','api',f'/data/files/{user.user["id"]}/{image["id"]}'],cwd=ROOT,capture_output=True,check=True).stdout
        assert raw==restored
        print('PASS: daily container creates a verifiable snapshot and restores the confirmed episode and private image')
    finally:
        subprocess.run(['docker','compose','--env-file',str(ROOT/'.local/acceptance.env'),'-p',project,'down','-v'],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
    deletion=user.propose('删除所有健康记录（备份互斥验收）','delete_records')
    # Hold exactly the backup's lock using a separate trusted DB connection.
    program="""import os,sys,psycopg
with psycopg.connect(os.environ['AGENT_DATABASE_URL'],autocommit=True) as conn:
 conn.execute('SELECT pg_advisory_lock(626120261019)')
 print('LOCKED',flush=True)
 sys.stdin.read(1)
 conn.execute('SELECT pg_advisory_unlock(626120261019)')
"""
    barrier=subprocess.Popen(BASE+['exec','-T','agent-runtime','python','-c',program],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    try:
        assert barrier.stdout.readline().strip()=='LOCKED'
        user.confirm(deletion)
        eventually(lambda:sql(f"SELECT count(*) FROM deletion_jobs WHERE user_id='{user.user['id']}' AND status='queued'")=='1')
        compose('exec','-T','api','test','-f',f'/data/files/{user.user["id"]}/{image["id"]}',stdout=subprocess.DEVNULL)
    finally:
        barrier.communicate('x',timeout=10)
        assert barrier.returncode==0
    eventually(lambda:sql(f"SELECT count(*) FROM deletion_jobs WHERE user_id='{user.user['id']}' AND status='completed'")=='1')
    missing=compose('exec','-T','api','sh','-c','test ! -f "$1"','sh',f'/data/files/{user.user["id"]}/{image["id"]}',stdout=subprocess.DEVNULL)
    print('PASS: deletion waits for the backup barrier and completes after release')

if __name__=='__main__':main()
