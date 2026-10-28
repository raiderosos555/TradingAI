"""Read-only bounded range probe. Abort campaign on first timeout.
Stops only its own Python process tree; never stops MT5/collector/engine.
Requires an already running terminal. No login/symbol_select/order API calls.
"""
import argparse,json,subprocess,sys
from pathlib import Path
from datetime import datetime,timedelta,timezone

def child(root,alias,kind,date):
    import MetaTrader5 as mt5
    cfg=json.loads((root/'config.demo.json').read_text())
    if not mt5.initialize(path=cfg['terminal_path'],timeout=5000):raise RuntimeError(str(mt5.last_error()))
    try:
        account=mt5.account_info()
        if not account or account.trade_mode!=0 or account.login!=cfg['account_login'] or account.server!=cfg['account_server']:
            raise RuntimeError('Expected DEMO identity not confirmed')
        symbol=cfg['symbols'][alias]['broker'];info=mt5.symbol_info(symbol)
        start=datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        if kind=='ticks':rows=mt5.copy_ticks_range(symbol,start,start+timedelta(seconds=1),mt5.COPY_TICKS_ALL)
        else:rows=mt5.copy_rates_range(symbol,getattr(mt5,'TIMEFRAME_'+kind),start,start+timedelta(hours=1))
        n=0 if rows is None else len(rows)
        result=dict(alias=alias,kind=kind,start=date,n=n,error=mt5.last_error(),chart_mode=info.chart_mode,
            first_raw=int(rows[0]['time']) if n else None,last_raw=int(rows[-1]['time']) if n else None)
        if n and kind=='ticks':
            result['positive_bid_ask']=int(((rows['bid']>0)&(rows['ask']>=rows['bid'])).sum())
        print(json.dumps(result))
    finally:mt5.shutdown()

def main(root,out):
    if out.exists():raise RuntimeError('Refuse overwrite')
    # Read-only process inventory; do not cause initialize to launch a terminal.
    chk=subprocess.run(['powershell','-NoProfile','-Command',"if (Get-Process terminal64 -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }"],capture_output=True)
    if chk.returncode:raise RuntimeError('No running terminal; no probe')
    cfg=json.loads((root/'config.demo.json').read_text());results=[]
    requests=[(a,k,d) for k,d in [('M1','2026-10-22T12:00:00'),('ticks','2026-10-22T12:00:00'),
        ('H1','2024-01-15T12:00:00'),('H1','2020-01-15T12:00:00'),
        ('H1','2015-01-15T12:00:00'),('H1','2010-01-15T12:00:00')] for a in cfg['symbols']]
    for alias,kind,date in requests:
        args=[sys.executable,str(Path(__file__)), '--root',str(root),'--child',alias,kind,date]
        p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            stdout,stderr=p.communicate(timeout=15)
            record=json.loads(stdout) if p.returncode==0 else dict(alias=alias,kind=kind,status='ERROR',message=stderr[-500:])
        except subprocess.TimeoutExpired:
            subprocess.run(['taskkill','/PID',str(p.pid),'/T','/F'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
            p.communicate(timeout=5)
            record=dict(alias=alias,kind=kind,start=date,status='TIMEOUT_15S',remaining_requests_not_sent=len(requests)-len(results)-1)
        results.append(record);out.write_text(json.dumps(dict(at=datetime.now(timezone.utc).isoformat(),requests=results,orders_sent=0),indent=2),encoding='utf-8')
        print(json.dumps(record),flush=True)
        if record.get('status')=='TIMEOUT_15S':break
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path);ap.add_argument('--child',nargs=3)
    a=ap.parse_args()
    if a.child:child(a.root,*a.child)
    else:main(a.root,a.out)
