"""Kill only the exact research child at timeout; do not restart the terminal."""
import argparse,json,os,subprocess,sys,time,hashlib
from pathlib import Path
from datetime import datetime,timezone

A=Path(__file__).resolve().parent;ROOT=A.parents[2]
p=argparse.ArgumentParser();p.add_argument('--alias',default='GOLD');p.add_argument('--start',default='2026-10-22T15:00:00+00:00');p.add_argument('--end',default='2026-10-22T15:01:00+00:00')
args=p.parse_args()
out=A/'captures'/datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ');out.mkdir(parents=True)
python=getattr(sys,'_base_executable',sys.executable)
env=dict(os.environ);env['PYTHONPATH']=str(ROOT/'.venv/Lib/site-packages')
cmd=[python,str(A/'probe.py'),'--out',str(out),'--alias',args.alias,'--start',args.start,'--end',args.end]
started=time.monotonic();status='COMPLETED'
with (out/'stdout.txt').open('w',encoding='utf-8') as stdout,(out/'stderr.txt').open('w',encoding='utf-8') as stderr:
    process=subprocess.Popen(cmd,stdout=stdout,stderr=stderr,env=env,creationflags=subprocess.CREATE_NO_WINDOW)
    try:code=process.wait(timeout=40)
    except subprocess.TimeoutExpired:
        status='TIMEOUT';process.kill();code=process.wait(timeout=5)
phases=[json.loads(s) for s in (out/'phases.jsonl').read_text().splitlines()] if (out/'phases.jsonl').exists() else []
summary=dict(status=status if status=='TIMEOUT' else 'COMPLETED' if code==0 else 'ERROR',returncode=code,
             child_pid=process.pid,last_phase=phases[-1]['phase'] if phases else None,elapsed_seconds=time.monotonic()-started,
             timeout_seconds=40,orders_sent=0,terminal_restarted=False,args=vars(args),python=python)
(out/'result.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
files=[*out.iterdir(),A/'probe.py',A/'bounded_probe.py']
(out/'manifest.json').write_text(json.dumps([dict(path=str(x.relative_to(A)),sha256=hashlib.sha256(x.read_bytes()).hexdigest()) for x in files if x.is_file()],indent=2),encoding='utf-8')
print(json.dumps(dict(path=str(out),**summary)),flush=True)
