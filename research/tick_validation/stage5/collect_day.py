"""Collect a single raw-coordinate day in bounded blocks. No strategy/execution."""
import json,os,subprocess,sys,time,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
out=A/'inputs';out.mkdir(parents=True,exist_ok=True)
if (A/'collection.json').exists():raise SystemExit('Existing capture is immutable; create another version')
alias='EURUSD';start=datetime(2026,10,22,tzinfo=timezone.utc)
sources={'H1':ROOT/'exchange/research/history-20261024/EURUSD.json',
         'H4':ROOT/'research/edge_audit/inputs/EURUSD-H4.json',
         'D1':ROOT/'research/edge_audit/inputs/EURUSD-D1.json'}
provenance=[]
for tf,path in sources.items():
    raw=path.read_bytes();(out/(tf+'.json')).write_bytes(raw)
    provenance.append(dict(timeframe=tf,path=str(path.relative_to(ROOT)),sha256=hashlib.sha256(raw).hexdigest()))
worker=A.parent/'stage3/probe.py';python=getattr(sys,'_base_executable',sys.executable)
env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'.venv/Lib/site-packages')
blocks=[];began=time.monotonic();stop=False
for hour in range(0,24,4):
    lo=start+timedelta(hours=hour);hi=lo+timedelta(hours=4);dest=out/f'raw-{hour:02d}-{hour+4:02d}'
    row=dict(start_raw_ms=int(lo.timestamp()*1000),end_raw_ms=int(hi.timestamp()*1000),path=str(dest.relative_to(A)))
    if stop or time.monotonic()-began>160:
        row['status']='NOT_ATTEMPTED';blocks.append(row);continue
    dest.mkdir()
    command=[python,str(worker),'--out',str(dest),'--alias',alias,'--start',lo.isoformat(),'--end',hi.isoformat()]
    with (dest/'stdout.txt').open('w') as so,(dest/'stderr.txt').open('w') as se:
        child=subprocess.Popen(command,env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            code=child.wait(timeout=40);row.update(status='OBSERVED' if code==0 else 'ERROR',returncode=code)
        except subprocess.TimeoutExpired:
            child.kill();code=child.wait(timeout=5);row.update(status='TIMEOUT',returncode=code)
    row['child_pid']=child.pid
    if row['status']=='OBSERVED':
        coverage=json.loads((dest/'coverage.json').read_text());row.update(status=coverage['status'],count=coverage['count'])
    stop=row['status'] not in {'OBSERVED','EMPTY'}
    blocks.append(row);print(hour,row['status'],row.get('count'),flush=True)
data=dict(alias=alias,symbol='EURUSD.pro',data_class='EXPLORATORY',time_basis='UNVERIFIED_RAW_API_COORDINATE',
          start_raw_ms=int(start.timestamp()*1000),end_raw_ms=int((start+timedelta(days=1)).timestamp()*1000),
          max_block_seconds=40,max_series_seconds_before_new_block=160,blocks=blocks,bar_sources=provenance,
          worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(),new_orders_sent=0,full_backtest_run=False)
(A/'collection.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
print('Collection saved',flush=True)
