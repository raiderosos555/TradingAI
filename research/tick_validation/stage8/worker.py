"""Read-only currency symbol discovery and raw FX history; no symbol selection or orders."""
import argparse,json,gzip
from pathlib import Path
from datetime import datetime,timezone
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--mode',choices=['discover','ticks'],required=True)
p.add_argument('--symbol');p.add_argument('--start');p.add_argument('--end');a=p.parse_args();a.out.mkdir(parents=True,exist_ok=True)
ROOT=Path(__file__).resolve().parents[3];config=json.loads((ROOT/'config.local.json').read_text())
def save(name,data):(a.out/name).write_text(json.dumps(data,indent=2),encoding='utf-8')
def phase(name):
    with (a.out/'phases.jsonl').open('a') as f:f.write(json.dumps(dict(phase=name,host_utc=datetime.now(timezone.utc).isoformat()))+'\n')
phase('IMPORT_START')
import MetaTrader5 as mt5
phase('INIT_START')
if not mt5.initialize(path=config['terminal_path'],timeout=10000):save('error.json',mt5.last_error());raise SystemExit(2)
try:
    account=mt5.account_info();assert account and account.login==config['account_login'] and account.server==config['account_server'] and account.trade_mode==0
    if a.mode=='discover':
        phase('SYMBOLS_START');symbols=mt5.symbols_get(group='*USDPLN*');assert symbols is not None,mt5.last_error()
        keys=['name','description','path','currency_base','currency_profit','select','visible','custom','trade_mode','point','trade_tick_size','trade_contract_size','trade_calc_mode']
        rows=[{k:getattr(s,k) for k in keys} for s in symbols]
        save('symbols.json',dict(at=datetime.now(timezone.utc).isoformat(),symbols=rows,selection_changed=False))
        info=mt5.symbol_info(config['symbols']['US500']['broker'])
        save('us500-current-contract.json',dict(at=datetime.now(timezone.utc).isoformat(),historical_validity_verified=False,
             **{k:getattr(info,k) for k in ['name','trade_contract_size','currency_profit','trade_calc_mode','trade_tick_size','point']}))
    else:
        info=mt5.symbol_info(a.symbol);assert info and not info.custom and info.currency_base=='USD' and info.currency_profit=='PLN'
        lo=datetime.fromisoformat(a.start);hi=datetime.fromisoformat(a.end);assert lo.tzinfo and hi.tzinfo and lo<hi
        phase('TICKS_START');data=mt5.copy_ticks_range(a.symbol,lo,hi,mt5.COPY_TICKS_ALL);error=mt5.last_error();phase('TICKS_DONE')
        lower,upper=int(lo.timestamp()*1000),int(hi.timestamp()*1000)
        rows=[] if data is None else [{k:r[k].item() for k in data.dtype.names} for r in data if lower<=int(r['time_msc'])<upper]
        with gzip.open(a.out/'ticks.json.gz','wt') as f:json.dump(rows,f,separators=(',',':'))
        save('coverage.json',dict(symbol=a.symbol,start_raw_ms=lower,end_raw_ms=upper,count=len(rows),status='API_ERROR' if data is None else 'OBSERVED' if rows else 'EMPTY',error=error,
                                 utc_verified=False,first_raw_ms=rows[0]['time_msc'] if rows else None,last_raw_ms=rows[-1]['time_msc'] if rows else None))
finally:phase('SHUTDOWN');mt5.shutdown()
