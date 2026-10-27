"""Phase-instrumented read-only MT5 probe. Never normalize raw timestamps."""
import argparse,gzip,json
from pathlib import Path
from datetime import datetime,timezone
import time

p=argparse.ArgumentParser();p.add_argument('--out',required=True,type=Path);p.add_argument('--alias',default='GOLD')
p.add_argument('--start',default='2026-10-22T15:00:00+00:00');p.add_argument('--end',default='2026-10-22T15:01:00+00:00')
args=p.parse_args();out=args.out;out.mkdir(parents=True,exist_ok=True)
ROOT=Path(__file__).resolve().parents[3]
c=json.loads((ROOT/'config.local.json').read_text())
def phase(name,**data):
    row=dict(phase=name,host_utc=datetime.now(timezone.utc).isoformat(),monotonic=time.monotonic(),**data)
    with (out/'phases.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n');f.flush()
def save(name,data):(out/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
phase('IMPORT_START')
import MetaTrader5 as mt5
phase('IMPORT_DONE',package=mt5.__version__)
phase('INITIALIZE_START')
ok=mt5.initialize(path=c['terminal_path'],timeout=10000)
phase('INITIALIZE_DONE',ok=ok,error=mt5.last_error())
if not ok:raise SystemExit(2)
try:
    phase('ACCOUNT_START')
    a=mt5.account_info();t=mt5.terminal_info()
    assert a and t and a.login==c['account_login'] and a.server==c['account_server'] and a.trade_mode==0
    phase('ACCOUNT_DONE',connected=t.connected,demo=True)
    save('environment.json',dict(package=mt5.__version__,terminal_version=mt5.version(),connected=t.connected,
                                account_matches=True,demo=True,raw_time_normalization='NONE',orders_sent=0))
    symbol=c['symbols'][args.alias]['broker']
    phase('SYMBOL_START',symbol=symbol)
    info=mt5.symbol_info(symbol);tick=mt5.symbol_info_tick(symbol)
    assert info and tick
    keys=['name','chart_mode','point','digits','trade_tick_size','volume_min','volume_max','volume_step','trade_contract_size','currency_profit','currency_margin','swap_mode','swap_long','swap_short','trade_stops_level','trade_freeze_level']
    save('symbol_now.json',{k:getattr(info,k) for k in keys});save('latest_tick_raw.json',tick._asdict())
    phase('SYMBOL_DONE',last_tick_raw_ms=tick.time_msc)
    start=datetime.fromisoformat(args.start);end=datetime.fromisoformat(args.end)
    assert start.tzinfo and end.tzinfo and start<end
    lo,hi=int(start.timestamp()*1000),int(end.timestamp()*1000)
    phase('TICKS_START',symbol=symbol,start_raw_ms=lo,end_raw_ms=hi,range_semantics='RAW_API_COORDINATE; UTC correspondence unverified')
    ticks=mt5.copy_ticks_range(symbol,start,end,mt5.COPY_TICKS_ALL);error=mt5.last_error()
    phase('TICKS_DONE',count=None if ticks is None else len(ticks),error=error)
    rows=[] if ticks is None else [{k:r[k].item() for k in ticks.dtype.names} for r in ticks]
    kept=[r for r in rows if lo<=r['time_msc']<hi]
    phase('SERIALIZE_START',count=len(kept))
    with gzip.open(out/'ticks.raw.json.gz','wt',encoding='utf-8',compresslevel=1) as f:f.write(json.dumps(kept,separators=(',',':')))
    phase('SERIALIZE_DONE')
    save('coverage.json',dict(alias=args.alias,symbol=symbol,requested_start_raw_ms=lo,requested_end_raw_ms=hi,
         api_count=None if ticks is None else len(ticks),count=len(kept),status='API_ERROR' if ticks is None else 'OBSERVED' if kept else 'EMPTY',
         first_raw_ms=kept[0]['time_msc'] if kept else None,last_raw_ms=kept[-1]['time_msc'] if kept else None,
         error=error,full_history_certified=False,utc_mapping_verified=False))
finally:
    phase('SHUTDOWN_START');mt5.shutdown();phase('SHUTDOWN_DONE')
