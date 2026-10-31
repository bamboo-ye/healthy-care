#!/usr/bin/env python3
"""Build and test a separate, disposable synthetic environment.

Does not configure real providers, alter the main deployment or publish a site.
Browser UI tests use the documented CUA workflow separately.
"""
from pathlib import Path
import subprocess
import sys

root=Path(__file__).resolve().parents[1]
def run(*args):subprocess.run(list(args),cwd=root,check=True)
run(sys.executable,'scripts/test_environment.py')
run('docker','compose','--env-file','.local/acceptance.env','-p','healthy-care-test','build')
run('docker','run','--rm','healthy-care-agent:0.1.0','python','-m','pytest','-q','-p','no:cacheprovider','tests')
run('docker','compose','--env-file','.local/acceptance.env','-p','healthy-care-test','up','-d','--no-build')
run(sys.executable,'scripts/reset_acceptance.py')
run(sys.executable,'tests/api_acceptance.py')
run(sys.executable,'tests/recovery_acceptance.py')
run(sys.executable,'tests/backup_acceptance.py')
run(sys.executable,'tests/product_acceptance.py')
run(sys.executable,'tests/retry_acceptance.py')
run(sys.executable,'tests/cohort_acceptance.py')
print('Automated software acceptance passed. Live model/SciencePal and professional content review are separate gates.')
