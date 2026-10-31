#!/usr/bin/env python3
"""Check input restriction and independently replay the distributed handoff pack."""
import copy
import hashlib
import json
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'prototype/research'))
from run_experiments import derive, experiment

data = json.loads((ROOT / 'analysis/demo-input.json').read_text(encoding='utf-8'))
before = copy.deepcopy(data)
short = derive(data, 3)
assert data == before, 'Deriving a condition must not change the frozen input.'
assert sum(s['expected_days'] for s in short['subjects']) == 144
assert sum(len(s['observations']) for s in short['subjects']) == 129
assert all(o['day'] < 3 for s in short['subjects'] for o in s['observations'])
assert all(s['topic'] == '皮肤不适' for s in derive(data, 7, '皮肤不适')['subjects'])
try:
    experiment(short)
except ValueError:
    pass
else:
    raise AssertionError('A short input cannot be expanded to seven days.')
expected = experiment(data)
assert [c['metrics']['participants'] for c in expected['conditions']] == [48, 48, 8]
assert len({c['input_sha256'] for c in expected['conditions']}) == 3

with tempfile.TemporaryDirectory(prefix='health-sciencepal-pack-') as temp:
    folder = Path(temp)
    with zipfile.ZipFile(ROOT / 'prototype/research/materials/sciencepal-research-pack.zip') as archive:
        for name in archive.namelist():
            assert not Path(name).is_absolute() and '..' not in Path(name).parts
        archive.extractall(folder)
    manifest = json.loads((folder / 'manifest.json').read_text(encoding='utf-8'))
    assert manifest['platform_execution'] == 'not_performed'
    for item in manifest['files']:
        value = (folder / item['path']).read_bytes()
        assert hashlib.sha256(value).hexdigest() == item['sha256_file_bytes'], item['path']
    subprocess.run([sys.executable, 'run_analysis.py', 'health-research-input.json', '--out', 'out'], cwd=folder, check=True, capture_output=True)
    subprocess.run([sys.executable, 'run_experiments.py', 'health-research-input.json', '--out', 'experiments'], cwd=folder, check=True, capture_output=True)
    subprocess.run([sys.executable, 'run_methods.py', 'health-research-input.json', '--out', 'methods'], cwd=folder, check=True, capture_output=True)
    reference = json.loads((folder / 'reference/report.local-python.json').read_text(encoding='utf-8'))
    actual = json.loads((folder / 'out/report.json').read_text(encoding='utf-8'))
    assert actual['metrics'] == reference['metrics']
    assert actual['input_sha256'] == reference['input_sha256'] == manifest['canonical_input_sha256']
    replay = json.loads((folder / 'experiments/experiments.json').read_text(encoding='utf-8'))
    assert replay == expected
    actual_methods = json.loads((folder / 'methods/methods.json').read_text(encoding='utf-8'))
    reference_methods = json.loads((folder / 'reference/methods.local-python.json').read_text(encoding='utf-8'))
    assert actual_methods == reference_methods
print('PASS: window restriction, immutable input, three distinct conditions, package hashes and three-script isolated replay.')
