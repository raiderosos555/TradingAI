import json,os,subprocess,sys
from pathlib import Path
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
prefix='demo_audit_retry' if '--retry' in sys.argv else 'demo_audit'
if (A/(prefix+'_process.json')).exists():raise SystemExit('Audit attempt exists')
env=dict(os.environ,PYTHONPATH=str(ROOT/'.venv/Lib/site-packages'))
with (A/(prefix+'_stdout.txt')).open('w') as so,(A/(prefix+'_stderr.txt')).open('w') as se:
    child=subprocess.Popen([getattr(sys,'_base_executable',sys.executable),str(A/'audit_demo.py')],env=env,
        stdout=so,stderr=se,creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        code=child.wait(timeout=45);status='COMPLETED' if code==0 else 'ERROR'
    except subprocess.TimeoutExpired:
        child.kill();code=child.wait(timeout=5);status='TIMEOUT'
result=dict(pid=child.pid,returncode=code,status=status)
(A/(prefix+'_process.json')).write_text(json.dumps(result,indent=2),encoding='utf-8')
print(result)
