"""Current calculation diagnostic, explicitly not a historical contract proof."""
from pathlib import Path
from datetime import datetime,timezone
import json
import MetaTrader5 as m
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
c=json.loads((ROOT/'config.local.json').read_text())
assert m.initialize(path=c['terminal_path'],timeout=10000),m.last_error()
try:
    a=m.account_info();assert a.login==c['account_login'] and a.server==c['account_server'] and a.trade_mode==0
    symbol=c['symbols']['US500']['broker'];i=m.symbol_info(symbol)
    discovery=json.loads((A/'inputs/discovery/symbols.json').read_text())['symbols']
    quotes={s['name']:m.symbol_info_tick(s['name'])._asdict() for s in discovery}
    tests=[dict(side='SELL',type=1,volume=.001,entry=7665.1,exit=7665.8),dict(side='BUY',type=0,volume=.001,entry=7665.5,exit=7664.6)]
    for test in tests:
        test['current_order_calc_profit_PLN']=m.order_calc_profit(test['type'],symbol,test['volume'],test['entry'],test['exit'])
        test['api_error']=m.last_error()
    result=dict(at=datetime.now(timezone.utc).isoformat(),historical=False,account_currency=a.currency,
                contract={k:getattr(i,k) for k in ['name','currency_base','currency_profit','trade_contract_size','trade_calc_mode','trade_tick_size','trade_tick_value','trade_tick_value_profit','trade_tick_value_loss']},
                current_quotes=quotes,calculations=tests,new_orders_sent=0)
    p=A/'inputs/current-profit-diagnostic.json'
    if p.exists():raise ValueError('Immutable capture exists')
    p.write_text(json.dumps(result,indent=2),encoding='utf-8')
finally:m.shutdown()
