"""Fixed arithmetic grid, read-only current order_calc_profit. No trading request."""
from pathlib import Path
from datetime import datetime,timezone
from decimal import Decimal
import json
import MetaTrader5 as m
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
p=A/'inputs/rounding-grid-current.json'
if p.exists():raise ValueError('Immutable capture exists')
config=json.loads((ROOT/'config.local.json').read_text())
assert m.initialize(path=config['terminal_path'],timeout=10000),m.last_error()
try:
    a=m.account_info();assert a.login==config['account_login'] and a.server==config['account_server'] and a.trade_mode==0
    symbol=config['symbols']['US500']['broker'];info=m.symbol_info(symbol)
    names=[s['name'] for s in json.loads((A/'inputs/discovery/symbols.json').read_text())['symbols']]
    before={n:m.symbol_info_tick(n)._asdict() for n in names}
    deltas=['-1','-0.91','-0.9','-0.11','-0.1','-0.09','0.09','0.1','0.11','0.9','0.91','1'];volumes=['0.001','0.002','0.01','0.1']
    rows=[]
    for side in [0,1]:
        for volume in volumes:
            for delta in deltas:
                entry=Decimal('7665');exit=entry+Decimal(delta)
                value=m.order_calc_profit(side,symbol,float(volume),float(entry),float(exit))
                rows.append(dict(type=side,volume=volume,entry=str(entry),exit=str(exit),delta=delta,broker_profit_PLN=value,error=m.last_error()))
    after={n:m.symbol_info_tick(n)._asdict() for n in names}
    result=dict(at=datetime.now(timezone.utc).isoformat(),historical=False,mode='READ_ONLY_ARITHMETIC_DIAGNOSTIC',
        contract_size=info.trade_contract_size,currency_profit=info.currency_profit,currency_account=a.currency,
        trade_tick_value_profit=info.trade_tick_value_profit,trade_tick_value_loss=info.trade_tick_value_loss,
        quotes_before=before,quotes_after=after,quotes_unchanged=before==after,rows=rows,new_orders_sent=0)
    p.write_text(json.dumps(result,indent=2),encoding='utf-8')
finally:m.shutdown()
