import importlib.util, tempfile, csv
from pathlib import Path
p=Path(__file__).resolve().parents[1]/'scripts'/'02_strict_qa.py'
spec=importlib.util.spec_from_file_location('strictqa',p)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
def test():
    sample=[('Avatar therapy for distressing voices','A'),('Relating to distressing voices','B'),('Virtual reality therapy for psychosis','C'),('Neuroimaging auditory cortex of schizophrenia','EXCLUDE')]
    for title,expected in sample:
        r={'title':title,'abstract':'','year':'2020','publication_type':'article'}
        layer=m.classify(r)[0]
        assert layer==expected,(title,layer,expected)
    with tempfile.TemporaryDirectory() as d:
        file=Path(d)/'raw.csv';out=Path(d)/'qa'
        fields=['openalex_id','doi','title','year','journal','abstract','language','publication_type']
        with file.open('w',newline='',encoding='utf-8') as f:
            w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
            for i,(title,_) in enumerate(sample):w.writerow({'openalex_id':f'W{i}','title':title,'year':'2020','journal':'X','language':'en','publication_type':'article'})
        s=m.run(file,out);assert s['included']==3 and s['excluded']==1 and s['duplicates']==0
    print('PASS: classification, audit, exclusion preservation')
if __name__=='__main__':test()
