"""Small local timing baseline; not a load test, SLA or clinical benchmark."""
import json
import math
from pathlib import Path
import statistics
import time
from api_acceptance import Client, CONFIG, ROOT

def measure(fn,count=20):
    values=[]
    for _ in range(count):
        start=time.perf_counter();fn();values.append((time.perf_counter()-start)*1000)
    ordered=sorted(values)
    return {'samples':count,'p50_ms':round(statistics.median(values),2),'p95_ms':round(ordered[math.ceil(count*.95)-1],2),'max_ms':round(max(values),2)}

if __name__=='__main__':
    user=Client().register();assert user.call('/v1/system/status')['test_provider']
    researcher=Client();identity=researcher.call('/v1/auth/login',{'email':CONFIG['RESEARCH_EMAIL'],'password':CONFIG['RESEARCH_PASSWORD']});researcher.csrf=identity['csrf']
    output={'environment':'local Docker, synthetic data, serial requests; no live model','measured_at':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'ready':measure(lambda:user.call('/readyz')),'health_state':measure(user.state),'research_overview':measure(lambda:researcher.call('/v1/research/overview')),'tiny_png_upload':measure(user.upload,5)}
    (ROOT/'.local/performance.json').write_text(json.dumps(output,indent=2)+'\n')
    print(json.dumps(output,indent=2))
