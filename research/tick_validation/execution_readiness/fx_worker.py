"""Read-only raw-coordinate FX history; never selects symbols or sends orders."""
import argparse
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path
import MetaTrader5 as mt5

p=argparse.ArgumentParser()
p.add_argument('--symbol', choices=['USDPLN','USDPLN.pro'], required=True)
p.add_argument('--hour',type=int,required=True)
p.add_argument('--out',type=Path,required=True)
a=p.parse_args()
assert a.hour in range(0,24,4)
root=Path(__file__).resolve().parents[3]
c=json.loads((root/'config.demo.json').read_text())
assert mt5.initialize(path=c['terminal_path'],timeout=10000), mt5.last_error()
try:
    account=mt5.account_info()
    assert account and account.login==c['account_login'] and account.server==c['account_server'] and account.trade_mode==0
    lo=1792627200000+a.hour*3600000; hi=lo+14400000
    ticks=mt5.copy_ticks_range(a.symbol,datetime.fromtimestamp(lo/1000,timezone.utc),datetime.fromtimestamp(hi/1000,timezone.utc),mt5.COPY_TICKS_ALL)
    error=mt5.last_error()
    print('API_DONE',None if ticks is None else len(ticks),error,flush=True)
    rows=[] if ticks is None else [dict(zip(ticks.dtype.names, row)) for row in ticks.tolist() if lo<=row[5]<hi]
    # MT5 structured field order is checked before the raw millisecond filter.
    if ticks is not None:
        assert ticks.dtype.names[5]=='time_msc'
    with gzip.open(a.out/'ticks.raw.json.gz','wt',encoding='utf-8',compresslevel=1) as stream:
        stream.write(json.dumps(rows,separators=(',',':')))
    info=mt5.symbol_info(a.symbol)
    result=dict(symbol=a.symbol,start_raw_ms=lo,end_raw_ms=hi,count=len(rows),
        first_raw_ms=rows[0]['time_msc'] if rows else None,last_raw_ms=rows[-1]['time_msc'] if rows else None,
        status='API_ERROR' if ticks is None else 'OBSERVED' if rows else 'EMPTY',error=error,
        time_basis='RAW_API_COORDINATE_UTC_UNVERIFIED',full_history_certified=False,
        captured_at=datetime.now(timezone.utc).isoformat(),contract_now=info._asdict() if info else None)
    (a.out/'coverage.json').write_text(json.dumps(result,indent=2))
finally:
    mt5.shutdown()
