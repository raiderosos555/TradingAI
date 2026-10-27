"""Bounded serial availability sampling, not a claim of continuous history."""
import json,subprocess,sys,time
from pathlib import Path
from datetime import datetime,timezone
A=Path(__file__).resolve().parent
started=time.monotonic();rows=[]
matrix=[(d,s) for d in ['2026-10-23','2026-04-27'] for s in ['EURPLN','EURUSD','GBPUSD','GOLD','OIL','US100','US500']]
report=A/('scan-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'.json')
for date,alias in matrix:
    if time.monotonic()-started>160:
        rows.append(dict(alias=alias,date_raw=date,status='NOT_ATTEMPTED_TIME_BUDGET'));continue
    proc=subprocess.run([sys.executable,str(A/'bounded_probe.py'),'--alias',alias,'--start',date+'T12:00:00+00:00','--end',date+'T12:01:00+00:00'],capture_output=True,text=True,timeout=50)
    if proc.returncode:
        row=dict(alias=alias,date_raw=date,status='WRAPPER_ERROR',error=proc.stderr[-800:]);rows.append(row)
    else:
        data=json.loads(proc.stdout);out=Path(data['path']);coverage=out/'coverage.json'
        row=dict(alias=alias,date_raw=date,**data)
        if coverage.exists():row['coverage']=json.loads(coverage.read_text())
        rows.append(row)
    report.write_text(json.dumps(dict(stage='RAW_AVAILABILITY_SAMPLE',orders_sent=0,rows=rows),indent=2),encoding='utf-8')
    print(alias,date,row['status'],row.get('coverage',{}).get('count'),flush=True)
    # Don't keep issuing historical requests after a live timeout/error.
    if row['status']!='COMPLETED':break
report.write_text(json.dumps(dict(stage='RAW_AVAILABILITY_SAMPLE',orders_sent=0,rows=rows),indent=2),encoding='utf-8')
print(report,flush=True)
