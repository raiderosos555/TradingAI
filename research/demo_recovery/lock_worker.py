"""Real process fixture: production lock implementation, no trading imports."""
import argparse,sys,time,json,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--root',type=Path,required=True);p.add_argument('--seconds',type=float,default=30);p.add_argument('--exit-code',type=int,default=0);a=p.parse_args()
sys.path.insert(0,str(a.source))
from trading_ai.journal import process_lock
with process_lock(a.root/'runtime/engine'),process_lock(a.root/'state'),process_lock(a.root/'account'):
    (a.root/('owner-'+str(os.getpid())+'.json')).write_text(json.dumps({'pid':os.getpid()}))
    time.sleep(a.seconds)
sys.exit(a.exit_code)
