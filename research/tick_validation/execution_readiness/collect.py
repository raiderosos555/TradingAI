import os,sys,subprocess,json
from pathlib import Path
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
suffix='_retry' if '--retry' in sys.argv else ''
if (A/('process'+suffix+'.json')).exists():raise SystemExit('Capture already attempted')
env=dict(os.environ,PYTHONPATH=str(ROOT/'.venv/Lib/site-packages'))
with (A/('stdout'+suffix+'.txt')).open('w') as so,(A/('stderr'+suffix+'.txt')).open('w') as se:
    p=subprocess.Popen([getattr(sys,'_base_executable',sys.executable),str(A/'observe.py')],env=env,stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
    try:code=p.wait(timeout=50);status='COMPLETED' if code==0 else 'ERROR'
    except subprocess.TimeoutExpired:p.kill();code=p.wait(timeout=5);status='TIMEOUT'
(A/('process'+suffix+'.json')).write_text(json.dumps(dict(status=status,returncode=code,pid=p.pid)))
print(status)
