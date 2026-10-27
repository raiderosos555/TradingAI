"""Paired read-only Last/quote observations. No order, selection or configuration calls."""
import json,time,sqlite3
from datetime import datetime,timezone,timedelta
from pathlib import Path
import MetaTrader5 as m
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
target=A/'observations.json'
if target.exists():raise SystemExit('Capture exists')
c=json.loads((ROOT/'state/runtime/effective-config.json').read_text())
assert m.initialize(path=c['terminal_path'],timeout=10000),m.last_error()
start=datetime.now(timezone.utc);rows=[]
try:
    account=m.account_info();assert account.login==c['account_login'] and account.trade_mode==0
    for sample in range(12):
        for alias in ['US500','US100','OIL']:
            symbol=c['symbols'][alias]['broker'];before=m.symbol_info_tick(symbol)
            assert before
            end=datetime.fromtimestamp(before.time_msc/1000,timezone.utc)
            begin=end-timedelta(seconds=15)
            history=m.copy_ticks_range(symbol,begin,end,m.COPY_TICKS_ALL)
            error=m.last_error()
            info=m.symbol_info(symbol);after=m.symbol_info_tick(symbol)
            ticks=[] if history is None else [{k:t[k].item() for k in history.dtype.names} for t in history]
            rows.append(dict(sample=sample,alias=alias,host_utc=datetime.now(timezone.utc).isoformat(),
                before=before._asdict(),after=after._asdict() if after else None,
                info=dict(bid=info.bid,ask=info.ask,time_seconds=info.time),history=ticks,error=error,
                raw_time_unmodified=True))
        time.sleep(.5)
    with sqlite3.connect((ROOT/'state/journal.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as db:
        events=[dict(at=at,kind=kind,payload=json.loads(payload)) for at,kind,payload in db.execute(
            'SELECT at,kind,payload FROM events WHERE at>=? ORDER BY seq',(start.isoformat(),))]
    target.write_text(json.dumps(dict(start=start.isoformat(),end=datetime.now(timezone.utc).isoformat(),
        offset_observed=c['broker_time_offset_seconds'],rows=rows,concurrent_events=events,orders_sent=0),separators=(',',':')),encoding='utf-8')
    print('Saved',len(rows),'paired observations')
finally:m.shutdown()
