"""Twelve bounded serial FX reads for the requested Oct22 replay prerequisites."""
import hashlib,json,os,subprocess,sys
from pathlib import Path
A=Path(__file__).resolve().parent; ROOT=A.parents[2]
target=A/'fx-collection.json'
if target.exists():raise SystemExit('Capture already exists')
env=dict(os.environ,PYTHONPATH=str(ROOT/'.venv/Lib/site-packages'))
attempts=[];stop=False
for symbol in ['USDPLN','USDPLN.pro']:
    for hour in range(0,24,4):
        out=A/'fx'/symbol/f'{hour:02d}-{hour+4:02d}'
        row=dict(symbol=symbol,hour=hour,path=out.relative_to(A).as_posix())
        attempts.append(row)
        if stop:row['status']='NOT_ATTEMPTED_AFTER_ERROR';continue
        out.mkdir(parents=True,exist_ok=False)
        with (out/'stdout.txt').open('w') as so,(out/'stderr.txt').open('w') as se:
            child=subprocess.Popen([sys._base_executable,str(A/'fx_worker.py'),'--symbol',symbol,'--hour',str(hour),'--out',str(out)],env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
            try:code=child.wait(timeout=40);status='COMPLETED' if code==0 else 'ERROR'
            except subprocess.TimeoutExpired:child.kill();code=child.wait(timeout=5);status='TIMEOUT'
        row.update(status=status,returncode=code,pid=child.pid)
        if status=='COMPLETED':
            coverage=json.loads((out/'coverage.json').read_text());row.update(status=coverage['status'],count=coverage['count'])
            row['sha256']=hashlib.sha256((out/'ticks.raw.json.gz').read_bytes()).hexdigest()
        stop=row['status'] not in ['OBSERVED','EMPTY']
        print(symbol,hour,row['status'],row.get('count'),flush=True)
        target.write_text(json.dumps(dict(attempts=attempts,orders_sent=0,utc_mapping_verified=False),indent=2))
target.write_text(json.dumps(dict(attempts=attempts,orders_sent=0,utc_mapping_verified=False),indent=2))
