"""Read-only broker evidence: reconstruct one H1 candle separately from Bid/Ask/Last."""
import sys,json,gzip,statistics
from pathlib import Path
from datetime import datetime,timedelta,timezone
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
sys.path.insert(0,str(A/'source_snapshot'))
from trading_ai.broker import MT5Broker
c=json.loads((A/'source_snapshot/config.local.json').read_text());b=MT5Broker(c['terminal_path'],c['broker_time_offset_seconds'])
start=datetime(2026,10,22,13,tzinfo=timezone.utc);end=start+timedelta(hours=1);rows=[]
try:
 a=b.snapshot()['account'];assert a['login']==c['account_login'] and a['server']==c['account_server'] and a['trade_mode']==0
 for alias,spec in c['symbols'].items():
  try:
   ticks=b.ticks(spec['broker'],start,end)
   with gzip.open(A/'inputs'/f'basis-{alias}-20261022T1300.json.gz','wt',encoding='utf-8') as f:json.dump(ticks,f)
   d=json.loads((ROOT/'exchange/research/history-20261024'/f'{alias}.json').read_text());bar=next(x for x in d['bars'] if x['time']==start.timestamp())
   row={'instrument':alias,'start':start.isoformat(),'ticks':len(ticks),'saved_H1':bar,'offset_assumed':c['broker_time_offset_seconds']}
   for side in ('bid','ask','last'):
    # All returned ticks carry a snapshot, including unchanged quote fields.
    v=[t[side] for t in ticks if t.get(side,0)>0]
    ohlc=dict(zip(('open','high','low','close'),(v[0],max(v),min(v),v[-1]))) if v else None
    row[side+'_ohlc']=ohlc;row[side+'_max_abs_OHLC_diff']=max(abs(ohlc[k]-bar[k]) for k in ohlc) if ohlc else None
   v=[t for t in ticks if t.get('last',0)>0 and t['bid']>0 and t['ask']>=t['bid']]
   row['median_Last_minus_Bid_points']=statistics.median((t['last']-t['bid'])/d['contract']['point'] for t in v) if v else None
   row['Last_equals_Bid_fraction']=sum(t['last']==t['bid'] for t in v)/len(v) if v else None
   row['valid_Last_samples']=len(v);rows.append(row);print(row,flush=True)
  except Exception as exc:rows.append({'instrument':alias,'error':str(exc)})
finally:b.close()
(A/'price_basis_check.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
