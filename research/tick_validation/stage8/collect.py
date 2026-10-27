import subprocess,sys,os,json,hashlib
from pathlib import Path
from datetime import datetime,timezone,timedelta
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
if (A/'collection.json').exists():raise SystemExit('Immutable capture exists')
inputs=A/'inputs';inputs.mkdir(exist_ok=True)
python=getattr(sys,'_base_executable',sys.executable);env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'.venv/Lib/site-packages')
attempts=[]
def run(path,arguments):
    path.mkdir(exist_ok=True)
    with (path/'stdout.txt').open('w') as so,(path/'stderr.txt').open('w') as se:
        child=subprocess.Popen([python,str(A/'worker.py'),'--out',str(path),*arguments],env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
        try:code=child.wait(timeout=40);status='COMPLETED' if code==0 else 'ERROR'
        except subprocess.TimeoutExpired:child.kill();code=child.wait(timeout=5);status='TIMEOUT'
    attempts.append(dict(path=str(path.relative_to(A)),status=status,pid=child.pid,returncode=code,arguments=arguments))
    print(path.name,status,flush=True);return status=='COMPLETED'
ok=run(inputs/'discovery',['--mode','discover'])
if ok:
    symbols=json.loads((inputs/'discovery/symbols.json').read_text())['symbols']
    candidates=[s for s in symbols if not s['custom'] and s['currency_base']=='USD' and s['currency_profit']=='PLN']
    # All discovered candidates retained. No guess of which series the broker used internally.
    report=json.loads((A.parent/'stage4/inputs/broker-report.json').read_text())
    minutes=sorted({d['broker_raw_time_msc']//60000*60000 for d in report['broker_snapshot']['deals'] if d['entry']==1})
    for index,s in enumerate(candidates[:3]):
        for ms in minutes:
            start=datetime.fromtimestamp(ms/1000,timezone.utc);end=start+timedelta(minutes=1)
            ok=run(inputs/f'fx-{index}-{start.strftime("%H%M")}', ['--mode','ticks','--symbol',s['name'],'--start',start.isoformat(),'--end',end.isoformat()])
            if not ok:break
        if not ok:break
data=dict(attempts=attempts,new_orders_sent=0,selection_changed=False,full_backtest_run=False,history_UTC_mapping_verified=False)
(A/'collection.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
