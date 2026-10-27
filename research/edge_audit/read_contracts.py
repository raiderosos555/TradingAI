"""Read-only present contract evidence; not a historical specification claim."""
from pathlib import Path
import json
from datetime import datetime,timezone
import MetaTrader5 as mt5
A=Path(__file__).resolve().parent
c=json.loads((A/'source_snapshot/config.demo.json').read_text())
if not mt5.initialize(path=c['terminal_path'],timeout=10000):raise RuntimeError(mt5.last_error())
try:
 a=mt5.account_info()
 if a is None or a.login!=c['account_login'] or a.server!=c['account_server'] or a.trade_mode!=0:raise RuntimeError('Wrong or unavailable DEMO account')
 fields=['name','custom','chart_mode','trade_contract_size','currency_profit','currency_margin','trade_calc_mode','point','trade_tick_size','swap_mode','swap_long','swap_short','swap_rollover3days','volume_min','volume_step','trade_stops_level','trade_freeze_level','start_time','expiration_time']
 result={}
 for alias,s in c['symbols'].items():
  info=mt5.symbol_info(s['broker'])
  result[alias]={k:getattr(info,k,None) for k in fields} if info else {'error':str(mt5.last_error())}
 (A/'inputs/current_contracts.json').write_text(json.dumps({'at':datetime.now(timezone.utc).isoformat(),'historical':False,'contracts':result},indent=2),encoding='utf-8')
 print(result)
finally:mt5.shutdown()
