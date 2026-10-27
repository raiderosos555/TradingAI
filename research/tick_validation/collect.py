"""Bounded read-only raw MT5 probes. Raw epoch coordinates are NOT asserted to be UTC."""
import json,gzip,hashlib,sqlite3,shutil
from pathlib import Path
from datetime import datetime,timedelta,timezone
import MetaTrader5 as mt5
A=Path(__file__).resolve().parent;ROOT=A.parents[1];I=A/'inputs';I.mkdir(exist_ok=True)
if (A/'collection_manifest.json').exists():raise SystemExit('Completed capture is immutable. Use a new version/directory for another collection.')
c=json.loads((ROOT/'config.local.json').read_text())
dates=['2025-10-24','2025-10-27','2026-03-27','2026-03-30','2026-04-27','2026-08-31','2026-10-22','2026-10-23']
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
def plain(r):return {k:(v.item() if hasattr(v,'item') else v) for k,v in r.items()}
protocol={'version':'stage1-v1','dates_raw_coordinate':dates,'probe_hour_raw':12,'probe_minutes':2,'symbols':{a:s['broker'] for a,s in c['symbols'].items()},'raw_to_utc_verified_segments':[],
 'scope':'Coverage probes and price/time verification only; no full backtest, strategy tuning or order calls',
 'data_status':'EXPLORATORY','api':'direct MetaTrader5; no production time normalizer','accepted_historical_contracts':[]}
save(A/'config.v1.json',protocol)
protected=[*ROOT.glob('config*.json'),* (ROOT/'trading_ai').glob('*.py')]
save(I/'protected_hashes.json',[{'path':str(p.relative_to(ROOT)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in protected])
if not mt5.initialize(path=c['terminal_path'],timeout=10000):raise RuntimeError(mt5.last_error())
rows=[];rate_meta=[];anchors=[]
try:
 account=mt5.account_info()
 if account is None or account.login!=c['account_login'] or account.server!=c['account_server'] or account.trade_mode!=0:raise RuntimeError('Expected DEMO account unavailable')
 save(I/'api_environment.json',{'package':mt5.__version__,'terminal_version':mt5.version(),'collected_at_utc':datetime.now(timezone.utc).isoformat(),'account_demo':True,'symbol_chart_mode_bid':mt5.SYMBOL_CHART_MODE_BID,'symbol_chart_mode_last':mt5.SYMBOL_CHART_MODE_LAST,'tick_flag_last':mt5.TICK_FLAG_LAST})
 save(I/'contracts_now.json',{a:mt5.symbol_info(s['broker'])._asdict() for a,s in c['symbols'].items()})
 # Existing confirmed deal times vs host-UTC intent times: evidence points, not a timezone rule.
 db=sqlite3.connect('file:'+str(ROOT/'research/edge_audit/inputs/journal-snapshot.sqlite3')+'?mode=ro',uri=True)
 for oid,at,result in db.execute("SELECT id,at,result FROM operations WHERE status='CONFIRMED'"):
  result=json.loads(result);ticket=result.get('deal')
  if not ticket:continue
  deals=mt5.history_deals_get(ticket=ticket)
  for d in deals or []:
   anchors.append({'operation_id':oid,'host_intent_utc':at,'deal_ticket':ticket,'broker_raw_time_msc':d.time_msc,'raw_minus_host_intent_seconds':d.time_msc/1000-datetime.fromisoformat(at).timestamp(),'limitation':'Host timestamp not independently NTP-certified; operation latency; no extrapolation across dates'})
 save(I/'deal_clock_anchors.json',anchors)
 paths=mt5.terminal_info()
 for p in (Path(paths.data_path)/'MQL5/Files/TradingAI').glob('*.json'):
  if p.name.startswith('observer_') or 'calendar' in p.name:shutil.copy2(p,I/('ea-'+p.name))
 for date in dates:
  start=datetime.fromisoformat(date+'T12:00:00+00:00');end=start+timedelta(minutes=2);lo=int(start.timestamp()*1000);hi=int(end.timestamp()*1000)
  for alias,s in c['symbols'].items():
   ticks=mt5.copy_ticks_range(s['broker'],start,end,mt5.COPY_TICKS_ALL)
   error=mt5.last_error();raw=[] if ticks is None else [plain({k:r[k] for k in ticks.dtype.names}) for r in ticks]
   kept=[t for t in raw if lo<=t['time_msc']<hi];filename=f'{alias}-{date}-raw1200.json.gz'
   with gzip.open(I/filename,'wt',encoding='utf-8') as f:json.dump(kept,f,separators=(',',':'))
   times=[t['time_msc'] for t in kept];gaps=[b-a for a,b in zip(times,times[1:])]
   row={'instrument':alias,'date_raw':date,'requested_start_raw_ms':lo,'requested_end_raw_ms':hi,'api_count':len(raw),'ticks':len(kept),'status':'API_ERROR' if ticks is None else 'OBSERVED' if kept else 'EMPTY','api_error':error,
    'first_raw_ms':times[0] if times else None,'last_raw_ms':times[-1] if times else None,'largest_internal_gap_ms':max(gaps,default=None),'inversions':sum(g<0 for g in gaps),'equal_timestamp_pairs':sum(g==0 for g in gaps),
    'invalid_quotes':sum(not (0<t['bid']<=t['ask']) for t in kept),'missing_last':sum(t['last']<=0 for t in kept),'path':filename,'sha256':hashlib.sha256((I/filename).read_bytes()).hexdigest(),'complete_history_certified':False}
   rows.append(row)
  save(A/'coverage.json',rows);print(date,[(r['instrument'],r['ticks']) for r in rows if r['date_raw']==date],flush=True)
 # Preserve actual raw H1/H4/D1 grids on either side of prior autumn/spring DST.
 for alias in ('GOLD','US100','EURUSD'):
  for begin,finish in [('2025-10-20','2025-10-31'),('2026-03-23','2026-04-03')]:
   for tf in ('H1','H4','D1'):
    x=mt5.copy_rates_range(c['symbols'][alias]['broker'],getattr(mt5,'TIMEFRAME_'+tf),datetime.fromisoformat(begin).replace(tzinfo=timezone.utc),datetime.fromisoformat(finish).replace(tzinfo=timezone.utc))
    bars=[] if x is None else [plain({k:b[k] for k in x.dtype.names}) for b in x];name=f'raw-bars-{alias}-{tf}-{begin}.json';save(I/name,bars)
    rate_meta.append({'instrument':alias,'tf':tf,'start_raw_label':begin,'end_raw_label':finish,'count':len(bars),'file':name,'open_hour_histogram':{str(h):sum(datetime.fromtimestamp(b['time'],timezone.utc).hour==h for b in bars) for h in sorted({datetime.fromtimestamp(b['time'],timezone.utc).hour for b in bars})},'utc_mapping_inferred':False})
 save(A/'raw_bar_grids.json',rate_meta)
finally:mt5.shutdown()
save(A/'collection_manifest.json',{'config_sha256':hashlib.sha256((A/'config.v1.json').read_bytes()).hexdigest(),'files':[{'path':str(p.relative_to(A)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in I.iterdir() if p.is_file()],'orders_sent':0})
