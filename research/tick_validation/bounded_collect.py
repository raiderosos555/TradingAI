"""Limit old-history synchronization time; do not mistake timeout for empty history."""
import subprocess,sys,json,hashlib,time,os
from pathlib import Path
A=Path(__file__).resolve().parent;cfg=json.loads((A/'config.v1.json').read_text());rows=[];budget_start=time.monotonic()
if (A/'bounded_manifest.v2.json').exists():raise SystemExit('Immutable completed capture; use new version for recollection')
python=getattr(sys,'_base_executable',sys.executable)
if not Path(python).exists():python=sys.executable
env=dict(os.environ);env['PYTHONPATH']=str(A.parents[1]/'.venv/Lib/site-packages')
# Newest first. A timeout stops further requests on that date, not the terminal.
for date in reversed(cfg['dates_raw_coordinate']):
 skip=None
 for alias in cfg['symbols']:
  row={'instrument':alias,'date_raw':date,'ticks':None,'complete_history_certified':False}
  if time.monotonic()-budget_start>150:skip='STAGE_TIME_BUDGET'
  if skip:row.update(status='NOT_ATTEMPTED',reason=skip)
  else:
   try:
    result=subprocess.run([python,str(A/'probe_worker.py'),alias,date],capture_output=True,text=True,timeout=18,env=env,creationflags=getattr(subprocess,'CREATE_NO_WINDOW',0))
    p=A/'inputs'/f'probe-{alias}-{date}.json'
    if result.returncode==0 and p.exists():row=json.loads(p.read_text())
    else:row.update(status='API_ERROR',reason=(result.stderr or result.stdout)[-1000:]);skip='PRECEDING_API_ERROR'
   except subprocess.TimeoutExpired:row.update(status='TIMEOUT',reason='18s process budget, not proof of absent ticks');skip='PRECEDING_TIMEOUT'
  rows.append(row)
 (A/'coverage.v2.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
 print(date,[(r['instrument'],r['status'],r['ticks']) for r in rows if r['date_raw']==date],flush=True)
(A/'bounded_manifest.v2.json').write_text(json.dumps({'version':'stage1-bounded-v2','max_probe_seconds':18,'stage_budget_seconds':150,'orders_sent':0,'files':[{'path':str(p.relative_to(A)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in (A/'inputs').iterdir() if p.is_file()]},indent=2),encoding='utf-8')
