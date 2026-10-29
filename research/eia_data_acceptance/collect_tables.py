"""Small dated EIA tables only. No prices/trading; reuse prior first sample."""
import sys,json,hashlib,shutil
from pathlib import Path
from datetime import datetime,timezone
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'edge_data_unblock'))
from fetch import fetch
DATES=['03_04','03_11','03_18','03_25','04_01','04_08','04_15','04_22','04_29','05_06','05_13','05_20']

def main():
    out=HERE/'private'/'tables-v1'
    if out.exists():raise RuntimeError('Refuse overwrite')
    out.mkdir(parents=True)
    plan=HERE/'PLAN.md'
    (out.parent/'plan-lock.json').write_text(json.dumps({'sha256':hashlib.sha256(plan.read_bytes()).hexdigest(),'at':datetime.now(timezone.utc).isoformat()},indent=2),encoding='utf-8')
    previous=HERE.parent/'edge_data_unblock/private/eia-v1'
    records=[]
    for d in DATES:
        if d=='03_04':
            original=previous/'sample_03_04.raw';r=json.loads((previous/'sample_03_04.json').read_text())
            assert hashlib.sha256(original.read_bytes()).hexdigest()==r['sha256']
            shutil.copyfile(original,out/(d+'.raw'));r['reused_previous_artifact']=True
        else:
            url=f'https://www.eia.gov/petroleum/supply/weekly/archive/2026/2026_{d}/csv/table1.csv'
            r=fetch(d,url,out,65536)
        r['release_date']='2026-'+d.replace('_','-');records.append(r)
        (out/'manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        if r['returncode']!=0:raise RuntimeError('Stop on source failure')
    print(json.dumps({'tables':len(records),'bytes':sum(x['bytes'] for x in records),'new_bytes':sum(x['bytes'] for x in records if not x.get('reused_previous_artifact'))}))

if __name__=='__main__':main()
