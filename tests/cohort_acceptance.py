"""Advanced cohort definitions stay aligned across metrics, bundles and exports."""
import csv
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import zipfile
from urllib.parse import urlencode
from api_acceptance import Client,CONFIG

def main():
    r=Client();identity=r.call('/v1/auth/login',{'email':CONFIG['RESEARCH_EMAIL'],'password':CONFIG['RESEARCH_PASSWORD']});r.csrf=identity['csrf']
    base={'source':'synthetic','topic':'all','category':'all','window_days':7}
    snapshot=r.call('/v1/research/snapshots',base,expected=201);original=r.call('/v1/research/snapshots/'+snapshot['id']+'/package')
    product=next(p['id'] for s in original['subjects'] for o in s['observations'] for p in o['products'])
    d={**base,'product_id':product,'availability':'observed','start_from':'2020-01-01','start_to':'2090-01-01'};query=urlencode(d)
    overview=r.call('/v1/research/overview?'+query);assert 0<overview['metrics']['events']<48
    selection=overview['selection'];assert selection['eligible_events']==selection['included_events']+sum(selection['excluded'].values())
    cohort=r.call('/v1/research/cohorts',{'name':'合成高级筛选验收','definition':d},expected=201)
    assert next(c for c in r.call('/v1/research/cohorts')['items'] if c['id']==cohort['id'])['definition']['product_id']==product
    frozen=r.call('/v1/research/snapshots',d,expected=201);data=r.call('/v1/research/snapshots/'+frozen['id']+'/package')
    assert len(data['subjects'])==overview['metrics']['events'];ids={s['id'] for s in data['subjects']}
    exported=r.call('/v1/research/export?'+query+'&format=csv',raw=True).decode();assert {row['event_id'] for row in csv.DictReader(io.StringIO(exported))}==ids
    bundle=r.call('/v1/research/snapshots/'+frozen['id']+'/bundle',raw=True)
    with tempfile.TemporaryDirectory() as folder:
        with zipfile.ZipFile(io.BytesIO(bundle)) as archive:archive.extractall(folder)
        root=Path(folder);subprocess.run([sys.executable,str(root/'run_analysis.py'),str(root/'health-research-input.json'),'--out',str(root/'output')],capture_output=True,check=True)
        result=json.loads((root/'output/report.json').read_text());assert result['metrics']['expected_patient_days']==overview['metrics']['expected_patient_days']
        assert result['input_sha256']==overview['input_sha256']
    r.call('/v1/research/overview?'+urlencode({**base,'start_from':'2099-01-01','start_to':'2000-01-01'}),expected=400)
    print('PASS: advanced cohort filters, exclusion counts, saved definition, immutable input, CSV and independent Python calculation agree')

if __name__=='__main__':main()
