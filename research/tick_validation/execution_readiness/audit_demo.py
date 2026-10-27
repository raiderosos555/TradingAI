"""Bounded read-only health observation. No engine, manager or order sender is invoked."""
import json,sqlite3,time,sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
import MetaTrader5 as mt5
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
out=A/('demo_health_latest.json' if '--latest' in sys.argv else 'demo_health.json')
if out.exists():raise SystemExit('Immutable health observation exists')
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
config=read(ROOT/'state/runtime/effective-config.json')
assert mt5.initialize(path=config['terminal_path'],timeout=10000),mt5.last_error()
try:
    account=mt5.account_info()
    assert account and account.login==config['account_login'] and account.server==config['account_server'] and account.trade_mode==0
    samples=[]
    for iteration in range(3):
        status=read(ROOT/'state/runtime/engine-status.json')
        effective=read(ROOT/'state/runtime/effective-config.json')
        offset=effective['broker_time_offset_seconds']
        now=datetime.now(timezone.utc)
        quotes={}
        for alias,spec in config['symbols'].items():
            tick=mt5.symbol_info_tick(spec['broker'])
            quotes[alias]=dict(raw=tick._asdict() if tick else None,
                age_seconds_under_runtime_offset=now.timestamp()-(tick.time_msc/1000-offset) if tick else None)
        positions=mt5.positions_get();orders=mt5.orders_get();terminal=mt5.terminal_info()
        assert positions is not None and orders is not None and terminal
        samples.append(dict(at_host_utc=now.isoformat(),terminal_connected=terminal.connected,
            terminal_trade_allowed=terminal.trade_allowed,external_trade_disabled=terminal.tradeapi_disabled,
            runtime_offset_seconds=offset,engine_status=status,quotes=quotes,
            positions=[p._asdict() for p in positions],orders=[p._asdict() for p in orders]))
        if iteration<2:time.sleep(10)
    since=datetime.now(timezone.utc)-timedelta(hours=24)
    # Broad raw window only for collecting recent broker deals; no historical UTC assertion.
    deals=mt5.history_deals_get(since-timedelta(hours=4),datetime.now(timezone.utc)+timedelta(hours=4))
    assert deals is not None,mt5.last_error()
    history=[]
    with sqlite3.connect((ROOT/'state/journal.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as db:
        db.row_factory=sqlite3.Row
        operations=[dict(r) for r in db.execute('SELECT * FROM operations WHERE at >= ? ORDER BY at',(since.isoformat(),))]
        for op in operations:
            for key in ['payload','result']:
                if op[key]:op[key]=json.loads(op[key])
            if op['status']=='CONFIRMED' and op['payload']['rule']=='OPEN':
                ticket=op['result'].get('order')
                values=mt5.history_orders_get(ticket=ticket) if ticket else None
                history.append(dict(order=ticket,rows=[r._asdict() for r in values] if values else [],error=mt5.last_error()))
        event_counts=[dict(r) for r in db.execute('SELECT kind,COUNT(*) AS count,MAX(at) AS latest FROM events WHERE at >= ? GROUP BY kind',(since.isoformat(),))]
        management=[dict(r) for r in db.execute("SELECT at,kind,payload FROM events WHERE kind='management_decision' ORDER BY seq DESC LIMIT 60")]
        for row in management:row['payload']=json.loads(row['payload'])
        reasons=[dict(r) for r in db.execute("SELECT json_extract(payload,'$.reason') AS reason,COUNT(*) AS count,MAX(at) AS latest FROM events WHERE kind='management_decision' AND at >= ? GROUP BY reason",(since.isoformat(),))]
        uncertain=[dict(r) for r in db.execute("SELECT id,status,at FROM operations WHERE status IN ('INTENT','UNCERTAIN')")]
    result=dict(observation_scope='THREE_READ_ONLY_SAMPLES_PLUS_RECENT_JOURNAL',samples=samples,
        risk_limits=config['risk'],recent_operations=operations,broker_deals_raw=[d._asdict() for d in deals],
        opening_order_history=history,event_counts=event_counts,latest_management_decisions=management,
        management_reasons=reasons,unresolved_operations=uncertain,orders_sent_by_audit=0,
        historical_clock_mapping_proven=False,production_modified=False)
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Read-only DEMO health saved:',len(samples),'samples;',len(operations),'recent operations')
finally:mt5.shutdown()
