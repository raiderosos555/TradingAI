"""Read-only empirical audit of existing DEMO executions; no new orders."""
import os,sys,json,subprocess,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
out=A/'inputs';out.mkdir(parents=True,exist_ok=True)
if (A/'collection.json').exists():raise SystemExit('Immutable collection exists; create a new version')
src=ROOT/'exchange/outbox/20261023T194453-3b5d0e08.json';raw=src.read_bytes()
(out/'broker-report.json').write_bytes(raw)
report=json.loads(raw);snap=report['broker_snapshot']
assert snap['account']['login']==123456789 and snap['account']['server']=='EXAMPLE-DEMO-SERVER' and snap['account']['trade_mode']==0
deals=snap['deals'];assert len(deals)==5 and {d['symbol'] for d in deals}=={'US500.pro'}
minutes=sorted({d['broker_raw_time_msc']//60000*60000 for d in deals})
python=getattr(sys,'_base_executable',sys.executable);env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'.venv/Lib/site-packages')
worker=A.parent/'stage3/probe.py';rows=[]
for ms in minutes:
    start=datetime.fromtimestamp(ms/1000,timezone.utc);end=start+timedelta(minutes=1)
    path=out/('ticks-'+start.strftime('%Y%m%dT%H%M'));path.mkdir()
    args=[python,str(worker),'--out',str(path),'--alias','US500','--start',start.isoformat(),'--end',end.isoformat()]
    status='COMPLETED'
    with (path/'stdout.txt').open('w') as so,(path/'stderr.txt').open('w') as se:
        child=subprocess.Popen(args,env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
        try:code=child.wait(timeout=40)
        except subprocess.TimeoutExpired:
            status='TIMEOUT';child.kill();code=child.wait(timeout=5)
    rows.append(dict(path=str(path.relative_to(A)),status=status if status=='TIMEOUT' else 'COMPLETED' if code==0 else 'ERROR',pid=child.pid,returncode=code))
    print(path.name,rows[-1]['status'],flush=True)
    if status=='TIMEOUT' or code!=0:break
data=dict(source_report=str(src.relative_to(ROOT)),source_sha256=hashlib.sha256(raw).hexdigest(),
          worker_source_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(),captures=rows,orders_sent=0,terminal_restarted=False)
(A/'collection.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
