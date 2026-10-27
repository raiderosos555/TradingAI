"""One bounded-process raw tick probe; no writes outside stage directory."""
import sys,json,gzip,hashlib
from pathlib import Path
from datetime import datetime,timedelta
import MetaTrader5 as mt5
A=Path(__file__).resolve().parent;ROOT=A.parents[1];c=json.loads((ROOT/'config.local.json').read_text());alias,date=sys.argv[1:3]
if not mt5.initialize(path=c['terminal_path'],timeout=10000):raise RuntimeError(mt5.last_error())
try:
 a=mt5.account_info();assert a and a.login==c['account_login'] and a.server==c['account_server'] and a.trade_mode==0
 start=datetime.fromisoformat(date+'T12:00:00+00:00');end=start+timedelta(minutes=2);lo=int(start.timestamp()*1000);hi=int(end.timestamp()*1000)
 ticks=mt5.copy_ticks_range(c['symbols'][alias]['broker'],start,end,mt5.COPY_TICKS_ALL);err=mt5.last_error()
 raw=[] if ticks is None else [{k:r[k].item() for k in ticks.dtype.names} for r in ticks]
 kept=[t for t in raw if lo<=t['time_msc']<hi];name=f'{alias}-{date}-raw1200.json.gz'
 with gzip.open(A/'inputs'/name,'wt',encoding='utf-8') as f:json.dump(kept,f,separators=(',',':'))
 times=[t['time_msc'] for t in kept];gaps=[b-a for a,b in zip(times,times[1:])]
 row={'instrument':alias,'date_raw':date,'requested_start_raw_ms':lo,'requested_end_raw_ms':hi,'api_count':len(raw),'ticks':len(kept),'status':'API_ERROR' if ticks is None else 'OBSERVED' if kept else 'EMPTY','api_error':err,
 'first_raw_ms':times[0] if times else None,'last_raw_ms':times[-1] if times else None,'largest_internal_gap_ms':max(gaps,default=None),'inversions':sum(g<0 for g in gaps),'equal_timestamp_pairs':sum(g==0 for g in gaps),'invalid_quotes':sum(not(0<t['bid']<=t['ask']) for t in kept),'missing_last':sum(t['last']<=0 for t in kept),'path':name,'sha256':hashlib.sha256((A/'inputs'/name).read_bytes()).hexdigest(),'complete_history_certified':False}
 (A/'inputs'/f'probe-{alias}-{date}.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
finally:mt5.shutdown()
