"""Scheduler fixture: only record start and exit 1. No broker imports."""
import argparse,json,os,sys
from datetime import datetime,timezone
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);a=p.parse_args()
a.out.mkdir(parents=True,exist_ok=True)
with (a.out/'starts.jsonl').open('a') as f:f.write(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})+'\n')
sys.exit(1)
