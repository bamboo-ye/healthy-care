import json
from pathlib import Path
FIELDS=['symptom','onset_days','severity','impact','medication_state','medication_name']
def build():
    rows=[]
    for i in range(20):
        for topic,symptom in [('respiratory','鼻塞'),('skin','皮肤发痒'),('digestive','腹胀')]:
            facts={'symptom':symptom,'onset_days':i%4+1,'severity':None if i%5==0 else i%7+1,'impact':['不影响活动','影响睡眠','影响工作','记不清'][i%4],'medication_state':['not_used','used','unknown','used'][i%4],'medication_name':('虚构记录用品甲' if i%4 in (1,3) else None)}
            disclosed=['symptom']+(['onset_days'] if i%3==0 else [])+(['medication_state'] if i%4==0 else [])
            initial='合成记录：'+json.dumps({f:facts[f] for f in disclosed},ensure_ascii=False)
            rows.append({'id':f'{topic}-{i:02}','cluster':f'template-{i:02}','split':'development' if i<4 else 'test','topic':topic,'initial':initial,'disclosed':disclosed,'facts':facts})
    return {'schema_version':'recording-benchmark-v1','data_origin':'synthetic','fields':FIELDS,'cases':rows}
if __name__=='__main__':
    Path(__file__).with_name('dataset.json').write_text(json.dumps(build(),ensure_ascii=False,indent=2)+'\n')
