"""Small history probes ONLY in a separately running, read-only terminal.
Never launches a terminal. Refuses the active DEMO executable and data path.
No login, symbol selection, configuration mutation or order functions.
"""
import argparse,json,subprocess,sys,time
from datetime import datetime,timedelta,timezone
from pathlib import Path
from diagnostics import active_data_directory

def require_running(terminal):
    cp=subprocess.run(['powershell','-NoProfile','-Command',
      'Get-Process terminal64 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty Path'],capture_output=True,text=True,timeout=5)
    if str(terminal).lower() not in [x.strip().lower() for x in cp.stdout.splitlines()]:
        raise RuntimeError('Separate terminal must already be running and manually authenticated')

def child(root,terminal,alias,tf,day):
    import MetaTrader5 as mt5
    c=json.loads((root/'config.demo.json').read_text())
    if Path(c['terminal_path']).resolve()==terminal.resolve():raise RuntimeError('Active terminal forbidden')
    require_running(terminal)
    if not mt5.initialize(path=str(terminal),timeout=3000):raise RuntimeError(str(mt5.last_error()))
    try:
        t=mt5.terminal_info();a=mt5.account_info()
        if not t or not a or not t.connected:raise RuntimeError('No connected research terminal')
        if Path(t.path).resolve()!=terminal.parent.resolve():raise RuntimeError('Wrong IPC terminal')
        if Path(t.data_path).resolve()==active_data_directory(root).resolve():raise RuntimeError('Active data folder forbidden')
        if a.trade_mode!=0 or a.server!=c['account_server']:raise RuntimeError('Expected DEMO server required')
        if t.trade_allowed or a.trade_expert:raise RuntimeError('Research terminal trading permissions must be disabled')
        info=mt5.symbol_info(c['symbols'][alias]['broker'])
        if not info or not info.select:raise RuntimeError('Research symbol must already be available')
        start=datetime.fromisoformat(day).replace(tzinfo=timezone.utc)
        rows=mt5.copy_rates_range(info.name,getattr(mt5,'TIMEFRAME_'+tf),start,start+timedelta(hours=1))
        if rows is not None and len(rows)>2:raise RuntimeError('Unexpected response size')
        return dict(alias=alias,tf=tf,date=day,maxbars=t.maxbars,chart_mode=info.chart_mode,
                    error=mt5.last_error(),bars=[] if rows is None else [dict(zip(rows.dtype.names,[x.item() for x in row])) for row in rows])
    finally:mt5.shutdown()

def main(a):
    if a.child:
        print(json.dumps(child(a.root,a.terminal,*a.child)));return
    if a.out.exists():raise RuntimeError('Refuse overwrite')
    active=Path(json.loads((a.root/'config.demo.json').read_text())['terminal_path'])
    if active.resolve()==a.terminal.resolve():raise RuntimeError('Active terminal forbidden')
    # Inspect running executable paths; do not use initialize to auto-launch.
    require_running(a.terminal)
    results=[]
    for day in ('2020-01-15T12:00:00','2021-01-15T12:00:00','2023-01-16T12:00:00'):
        for alias in ('GOLD','US500','US100','OIL','EURUSD','GBPUSD','EURPLN'):
            for tf in ('D1','H1'):
                # D1 interval begins at raw midnight; UTC not inferred from raw.
                stamp=day.replace('12:00:00','00:00:00') if tf=='D1' else day
                args=[sys.executable,str(Path(__file__)),'--root',str(a.root),'--terminal',str(a.terminal),'--child',alias,tf,stamp]
                try:
                    p=subprocess.run(args,capture_output=True,text=True,timeout=10,creationflags=subprocess.CREATE_NO_WINDOW)
                    r=json.loads(p.stdout) if p.returncode==0 else {'error':p.stderr[-600:]}
                except subprocess.TimeoutExpired:r={'error':'HARD_TIMEOUT_10S; probe child stopped; terminal left running'}
                results.append(r);a.out.write_text(json.dumps(results,indent=2),encoding='utf-8')
                if 'bars' not in r:return
                time.sleep(.5)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=Path('C:/TradingAI'))
    p.add_argument('--terminal',type=Path,required=True);p.add_argument('--out',type=Path)
    p.add_argument('--child',nargs=3);a=p.parse_args()
    if not a.child and a.out is None:p.error('--out is required for the parent probe')
    main(a)
