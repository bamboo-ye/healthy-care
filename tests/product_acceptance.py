"""Versioned product-source integration on synthetic data, not a real leaflet."""
import copy
import json
import subprocess
from api_acceptance import Client
from recovery_acceptance import BASE, compose

PRODUCT={'id':'synthetic-product','version':'v1','name':'合成产品','region':'ZZ','strength':'合成规格','form':'测试剂型','route':'测试途径','ingredients':['合成成分'],'information':'合成说明，仅用于接口验收。','dosage_label':'合成用量字段，不可用于实际用药。','warnings':['合成资料不可用于真实健康决策。'],'amount_unit':'片','min_age':18,'max_age':64,'source_url':'https://example.test/synthetic','review_status':'reviewed','reviewer':'synthetic-fixture','reviewed_at':'2026-01-01T00:00:00Z','review_reference':'synthetic-review-fixture','valid_until':'2099-01-01T00:00:00Z','data_origin':'synthetic'}
def main():
    bundle={'schema_version':'1','products':[PRODUCT]}
    payload=json.dumps(bundle,ensure_ascii=False)
    compose('exec','-T','api','care','knowledge-import',input=payload,text=True,capture_output=True)
    compose('exec','-T','api','care','knowledge-import',input=payload,text=True,capture_output=True)
    changed=copy.deepcopy(bundle);changed['products'][0]['strength']='different'
    rejected=subprocess.run(BASE+['exec','-T','api','care','knowledge-import'],input=json.dumps(changed),text=True,capture_output=True)
    assert rejected.returncode!=0,'Existing product version must not be overwritten'
    user=Client().register();assert user.call('/v1/system/status')['test_provider']
    catalog=user.call('/v1/health/products?region=ZZ')['items'];assert len(catalog)==1 and 'dosage_label' not in catalog[0]
    user.do('合成说明记录（目录与实际记录绑定验收）','record_medication')
    state=user.state();assert state['product_information'][0]['dosage_available'] is False
    assert 'dosage_label' not in state['product_information'][0]
    assert any(c['rule']=='leaflet_unit_mismatch' for c in state['medication_checks'])
    user.do('合成背景完整（仅用于字段门槛验收）','update_profile')
    info=user.state()['product_information'][0];assert info['dosage_label']==PRODUCT['dosage_label']
    compose('exec','-T','api','care','knowledge-retire','synthetic-product','v1',capture_output=True)
    assert user.call('/v1/health/products')['items']==[]
    state=user.state();assert state['product_information']==[]
    assert any(c['rule']=='leaflet_unavailable' for c in state['medication_checks'])
    print('PASS: synthetic product import, immutable version, identity, background gate, unit check and withdrawal')

if __name__=='__main__':main()
