"""Reproduce stage-1 price evidence offline from existing tick captures and raw bar times."""
import json,gzip,csv,hashlib,shutil,statistics,unittest,io
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
from model import *
A=Path(__file__).resolve().parent;ROOT=A.parents[1];OLD=ROOT/'research/edge_audit';E=A/'evidence';E.mkdir(exist_ok=True)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def save(name,x):(A/name).write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
rows=[]
for src in sorted((OLD/'inputs').glob('basis-*.json.gz')):
 dst=E/src.name
 if not dst.exists():shutil.copy2(src,dst)
 with gzip.open(dst,'rt',encoding='utf-8') as f:original=json.load(f)
 ticks=[{**t,'time_msc':t['broker_raw_time_msc'],'time':t['broker_raw_time']} for t in original]
 alias=src.name.split('-')[1];data=read(ROOT/'exchange/research/history-20261024'/f'{alias}.json');bar=next(b for b in data['bars'] if b['broker_raw_time']==1792681200)
 lo=bar['broker_raw_time']*1000;hi=lo+3600000;contract=data['contract'];point=contract['point'];first=ticks[0]
 check=list(validate_stream(ticks));lastbar=ohlc(ticks,'last',lo,hi);snapshotbar=ohlc(ticks,'last',lo,hi,last_updates_only=False)
 diff=lambda b:max(abs(b[k]-bar[k]) for k in ('open','high','low','close')) if b else None
 # Price comparison at the exact same first observed snapshot. No strategy decision/fill assertion.
 spread=first['ask']-first['bid'];quotes={s+'_'+act:execution_price(s,act,first) for s in ('BUY','SELL') for act in ('OPEN','CLOSE')}
 costs=read(ROOT/'exchange/research/history-20261024/validation'/f'{alias}-validation-base.json')['costs']
 oldbuy=bar['open']+costs['spread_points']*point+costs['slippage_points']*point;oldsell=bar['open']-costs['slippage_points']*point
 row={'instrument':alias,'source_file':str(dst.relative_to(A)),'raw_start_ms':lo,'raw_end_ms':hi,'utc_mapping':'UNVERIFIED_FOR_INTERVAL',
 'ticks':len(ticks),'first_raw_ms':first['time_msc'],'last_raw_ms':ticks[-1]['time_msc'],'largest_gap_ms':max(b['time_msc']-a['time_msc'] for a,b in zip(ticks,ticks[1:])),
 'equal_timestamp_pairs':sum(a['time_msc']==b['time_msc'] for a,b in zip(ticks,ticks[1:])),
 'tick_flags':dict(Counter(t['flags'] for t in ticks)),'last_update_ticks':sum(bool(t['flags']&8) for t in ticks),
 'Last_updates_OHLC_error':diff(lastbar),'Last_snapshots_OHLC_error':diff(snapshotbar),'Bid_OHLC_error':diff(ohlc(ticks,'bid',lo,hi)),
 'Ask_OHLC_error':diff(ohlc(ticks,'ask',lo,hi)),'original_raw_bar':bar,'last_updated_bar':lastbar,
 'first_quotes':quotes,'first_Last':first['last'],'first_spread_points':spread/point,
 'old_BUY_entry_formula':oldbuy,'old_SELL_entry_formula':oldsell,'old_buy_minus_observed_ask':oldbuy-first['ask'],'old_sell_minus_observed_bid':oldsell-first['bid'],
 'roundtrip_BUY_same_quote_price_delta':quotes['BUY_CLOSE']-quotes['BUY_OPEN'],
 'roundtrip_SELL_same_quote_price_delta':quotes['SELL_OPEN']-quotes['SELL_CLOSE'],
 'PnL':None,'PnL_status':'NOT_CALCULATED_UNKNOWN_HISTORICAL_FEES_FX_SWAP; NO_STRATEGY_BACKTEST'}
 rows.append(row)
save('price_checks.json',rows)
with (A/'price_checks.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)
grids=[]
for alias in ('GOLD','US100','EURUSD'):
 for tf in ('H4','D1'):
  bars=read(OLD/'inputs'/f'{alias}-{tf}.json')['bars']
  for start,end in [('2025-10-20','2025-10-31'),('2026-03-23','2026-04-03')]:
   lo=datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp();hi=datetime.fromisoformat(end).replace(tzinfo=timezone.utc).timestamp()
   raw=[{k:v for k,v in b.items() if k!='time'}|{'time':b['broker_raw_time']} for b in bars if lo<=b['broker_raw_time']<hi]
   name=f'raw-grid-{alias}-{tf}-{start}.json';(E/name).write_text(json.dumps(raw,indent=2),encoding='utf-8')
   grids.append({'instrument':alias,'timeframe':tf,'start_raw_label':start,'end_raw_label':end,'bars':len(raw),'hour_of_raw_coordinate':dict(Counter(datetime.fromtimestamp(b['time'],timezone.utc).hour for b in raw)),
   'observed_intervals_seconds':dict(Counter(b['time']-a['time'] for a,b in zip(raw,raw[1:]))),'file':name,'absolute_UTC_proven':False})
save('bar_grid_checks.json',grids)
anchors=read(A/'inputs/deal_clock_anchors.json');offsets=[r['raw_minus_host_intent_seconds'] for r in anchors]
save('clock_assessment.json',{'accepted_historical_segments':[],'status':'HISTORICAL_MAPPING_UNRESOLVED','deal_anchor_count':len(anchors),'offset_candidate_seconds':7200 if offsets and all(7200<=x<7201 for x in offsets) else None,
 'observed_raw_minus_intent_range_seconds':[min(offsets),max(offsets)] if offsets else None,
 'anchor_date':'2026-10-23','DST_verified':False,'extrapolation_permitted':False,
 'notes':['Direct raw API read: no production normalize() used.','EA TimeGMT uses host clock; not an independent clock authority.','Raw H4/D1 grids are preserved but do not determine UTC timezone.','Future autumn 2026 transition has not occurred at capture time.','Synthetic DST tests verify mechanics only; Europe/Warsaw is not assigned to broker.']})
stream=io.StringIO();suite=unittest.defaultTestLoader.discover(str(A),pattern='test_model.py');result=unittest.TextTestRunner(stream=stream,verbosity=2).run(suite)
(A/'tests.txt').write_text(stream.getvalue(),encoding='utf-8');save('tests.json',{'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'passed':result.wasSuccessful()})
if not result.wasSuccessful():raise SystemExit(1)
integrity=[]
for item in read(A/'inputs/protected_hashes.json'):
 actual=hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest();integrity.append({**item,'unchanged':actual==item['sha256']})
assert all(r['unchanged'] for r in integrity);save('production_integrity.json',integrity)
print('Prices',[(r['instrument'],r['ticks'],r['Last_updates_OHLC_error']) for r in rows]);print('Clock',offsets);print('Tests',result.testsRun)
