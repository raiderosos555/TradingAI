"""Bounded read-only MT5 pre-migration evidence. Never order_send/login/shutdown terminal."""
import hashlib,json,sqlite3,sys
from datetime import datetime,timezone,timedelta
from pathlib import Path
A=Path(__file__).resolve().parent;ROOT=A.parents[1]

def run(out):
    if out.exists():raise RuntimeError('Preserve earlier probe; choose a new output')
    import MetaTrader5 as mt5
    cfg=json.loads((ROOT/'config.demo.json').read_text());effective=json.loads((ROOT/'state/runtime/effective-config.json').read_text())
    now=datetime.now(timezone.utc)
    if not mt5.initialize(path=cfg['terminal_path'],timeout=10000):raise RuntimeError(str(mt5.last_error()))
    try:
        account=mt5.account_info();terminal=mt5.terminal_info();positions=mt5.positions_get();orders=mt5.orders_get()
        if not account or not terminal or positions is None or orders is None:raise RuntimeError('Incomplete broker state')
        if [account.login,account.server]!=[cfg['account_login'],cfg['account_server']] or account.trade_mode!=0:raise RuntimeError('Not the expected DEMO account')
        history=mt5.history_deals_get(now-timedelta(days=2),now+timedelta(days=1))
        if history is None:raise RuntimeError('History unavailable')
        quotes={}
        for name,spec in cfg['symbols'].items():
            tick=mt5.symbol_info_tick(spec['broker'])
            if tick:
                d=tick._asdict();d['candidate_age_seconds']=datetime.now(timezone.utc).timestamp()-(tick.time_msc/1000-effective['broker_time_offset_seconds'])
                d['executable_now']=tick.bid>0 and tick.ask>=tick.bid and -2<=d['candidate_age_seconds']<=cfg['risk']['max_tick_age_seconds'];quotes[name]=d
        conn=sqlite3.connect((ROOT/'state/journal.sqlite3').as_uri()+'?mode=ro',uri=True)
        try:
            uncertain=conn.execute("SELECT COUNT(*) FROM operations WHERE status IN ('INTENT','UNCERTAIN')").fetchone()[0]
            events=conn.execute("SELECT at,payload FROM events WHERE kind='management_decision' ORDER BY seq DESC LIMIT 100").fetchall()
        finally:conn.close()
        result=dict(at=now.isoformat(),account=dict(login=account.login,server=account.server,trade_mode=account.trade_mode),
            connected=terminal.connected,trade_allowed=terminal.trade_allowed,live_enabled=cfg['live_enabled'],
            positions=[p._asdict() for p in positions],orders=[p._asdict() for p in orders],history=[p._asdict() for p in history],
            all_positions_have_broker_sl_tp=all(p.sl>0 and p.tp>0 for p in positions),quotes=quotes,uncertain_operations=uncertain,
            recent_management=[dict(at=at,payload=json.loads(payload)) for at,payload in events],
            engine=json.loads((ROOT/'state/runtime/engine-status.json').read_text()),collector=json.loads((ROOT/'state/forward_validation/cohort-20261026-v1/status.json').read_text()),
            note='Broker SL/TP presence does not prove continuous BE/trailing or gap execution. Quote age uses current effective candidate offset, not historic UTC certification.',orders_sent=0)
        out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2),encoding='utf-8')
        print(json.dumps({k:result[k] for k in ['connected','live_enabled','all_positions_have_broker_sl_tp','uncertain_operations','orders_sent']}|{'positions':len(positions),'engine_status':result['engine']['status'],'collector_status':result['collector']['status'],'nonexecutable_quotes':[s for s,q in quotes.items() if not q['executable_now']]}))
    finally:mt5.shutdown() # Close this client's IPC session only; never terminate MT5.

if __name__=='__main__':run(Path(sys.argv[1]))
