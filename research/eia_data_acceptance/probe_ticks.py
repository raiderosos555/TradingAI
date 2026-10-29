"""Bounded probes in an already running investor terminal. Never submits orders."""
import argparse, hashlib, json, subprocess, sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'edge_data_unblock'))
from diagnostics import active_data_directory
from isolated_mt5_probe import require_running
from collect_tables import DATES
from validate_tables import scheduled

def gate(t,a,c,terminal,active_data):
    checks={
        'connected':bool(t and t.connected),
        'separate_executable':bool(t and Path(t.path).resolve()==terminal.parent.resolve()
                                   and terminal.resolve()!=Path(c['terminal_path']).resolve()),
        'separate_portable_data':bool(t and Path(t.data_path).resolve()==terminal.parent.resolve()
                                     and Path(t.data_path).resolve()!=active_data.resolve()),
        'same_demo_identity':bool(a and a.trade_mode==0 and a.server==c['account_server'] and a.login==int(c['account_login'])),
        'investor_permissions':bool(a and not a.trade_allowed and not a.trade_expert),
        'terminal_trading_off':bool(t and not t.trade_allowed),
        'dll_off':bool(t and not t.dlls_allowed)}
    if not all(checks.values()):raise RuntimeError('Isolation/permissions gate: '+json.dumps(checks))
    return checks

def child(root,terminal,day):
    import MetaTrader5 as mt5
    import numpy as np
    c=json.loads((root/'config.demo.json').read_text())
    if terminal.resolve()==Path(c['terminal_path']).resolve():raise RuntimeError('Active terminal forbidden')
    require_running(terminal)
    if not mt5.initialize(path=str(terminal),portable=True,timeout=3000):raise RuntimeError('Research IPC unavailable')
    try:
        checks=gate(mt5.terminal_info(),mt5.account_info(),c,terminal,active_data_directory(root))
        info=mt5.symbol_info(c['symbols']['OIL']['broker'])
        if not info or not info.select:raise RuntimeError('OIL not available in research Market Watch')
        start=datetime.fromisoformat(scheduled(day)); end=start+timedelta(seconds=1)
        ticks=mt5.copy_ticks_range(info.name,start,end,mt5.COPY_TICKS_ALL)
        err=mt5.last_error()
        if ticks is None:raise RuntimeError('Tick API returned None: '+str(err))
        lo=int(start.timestamp()*1000);hi=lo+1000
        # API end bound may be inclusive. Retain raw, evaluate exactly [start,start+1s).
        if len(ticks)>10000:raise RuntimeError('Unexpected response size')
        if len(ticks) and ((ticks['time_msc']<lo).any() or (ticks['time_msc']>hi).any()):raise RuntimeError('Outside requested range')
        sample=ticks[ticks['time_msc']<hi]
        valid=np.isfinite(sample['bid']) & np.isfinite(sample['ask']) & (sample['bid']>0) & (sample['ask']>=sample['bid'])
        ordered=bool(np.all(np.diff(sample['time_msc'])>=0))
        rows=[{k:row[k].item() for k in ticks.dtype.names} for row in ticks]
        return {'day':day,'request_api_utc':start.isoformat(),'historical_utc_verified':False,
                'gate':checks,'chart_mode':info.chart_mode,'api_error':err,'raw_rows':rows,
                'ticks_in_second':len(sample),'positive_uncrossed_sides':int(valid.sum()),'ordered':ordered,
                'bid_flag_updates':int(((sample['flags'] & mt5.TICK_FLAG_BID)!=0).sum()),
                'ask_flag_updates':int(((sample['flags'] & mt5.TICK_FLAG_ASK)!=0).sum()),
                'last_flag_updates':int(((sample['flags'] & mt5.TICK_FLAG_LAST)!=0).sum()),
                'quote_freshness_verified':False,
                'continue':bool(len(sample)>0 and valid.all() and ordered)}
    finally:mt5.shutdown()

def main(a):
    if a.child:
        print(json.dumps(child(a.root,a.terminal,a.child)));return
    if a.out.exists():raise RuntimeError('Refuse overwrite')
    a.out.mkdir(parents=True)
    results=[]
    for d in DATES:
        day='2026-'+d.replace('_','-')
        args=[sys.executable,str(Path(__file__)), '--root',str(a.root),'--terminal',str(a.terminal),'--child',day]
        try:
            p=subprocess.run(args,capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
            r=json.loads(p.stdout) if p.returncode==0 else {'day':day,'error':p.stderr[-1800:],'continue':False}
        except subprocess.TimeoutExpired:r={'day':day,'error':'HARD_TIMEOUT_10S; terminal not stopped; background sync may continue','continue':False}
        raw=json.dumps(r,indent=2).encode();(a.out/(d+'.json')).write_bytes(raw)
        results.append({k:v for k,v in r.items() if k!='raw_rows'})
        results[-1]['sha256']=hashlib.sha256(raw).hexdigest()
        (a.out/'summary.json').write_text(json.dumps(results,indent=2),encoding='utf-8')
        print(json.dumps(results[-1]),flush=True)
        if not r['continue']:break

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('C:/TradingAI'))
    p.add_argument('--terminal',type=Path,default=Path('C:/TradingAI-ResearchMT5/terminal64.exe'))
    p.add_argument('--out',type=Path);p.add_argument('--child');a=p.parse_args()
    if not a.child and a.out is None:p.error('--out required')
    main(a)
