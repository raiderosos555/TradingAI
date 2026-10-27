"""Current read-only broker arithmetic. Never calls order_send/order_check or symbol_select."""
import json
from datetime import datetime, timezone
from pathlib import Path
import MetaTrader5 as mt5
from grid import make_grid

A = Path(__file__).resolve().parent
ROOT = A.parents[2]
out = A / 'capture.json'
if out.exists():
    raise SystemExit('Immutable capture already exists')
settings = json.loads((A / 'config.json').read_text())
local = json.loads((ROOT / 'config.local.json').read_text())
demo = json.loads((ROOT / 'config.demo.json').read_text())
assert mt5.initialize(path=local['terminal_path'], timeout=10000), mt5.last_error()
try:
    account = mt5.account_info()
    assert account and account.login == local['account_login'] and account.server == local['account_server'] and account.trade_mode == 0
    assert account.currency == 'PLN'
    def fx_quotes():
        values = {}
        for name in settings['fx_candidates']:
            q = mt5.symbol_info_tick(name)
            values[name] = q._asdict() if q else None
        return values
    started = datetime.now(timezone.utc).isoformat()
    fx_info = {name: mt5.symbol_info(name)._asdict() for name in settings['fx_candidates']}
    instruments = []
    for alias, item in demo['symbols'].items():
        name = item['broker']
        info, quote = mt5.symbol_info(name), mt5.symbol_info_tick(name)
        result = dict(alias=alias, symbol=name, at=datetime.now(timezone.utc).isoformat(), rows=[])
        if info is None or quote is None:
            result.update(status='UNAVAILABLE', error=mt5.last_error())
        else:
            result.update(contract=info._asdict(), quote=quote._asdict(), status='OBSERVED')
            for row in make_grid(result['contract'], result['quote'], settings):
                before = fx_quotes()
                value = mt5.order_calc_profit(mt5.ORDER_TYPE_BUY if row['side'] == 'BUY' else mt5.ORDER_TYPE_SELL,
                    name, float(row['volume']), float(row['entry']), float(row['exit']))
                error = mt5.last_error()
                after = fx_quotes()
                result['rows'].append(dict(**row, broker_profit=value, error=error, fx_before=before, fx_after=after))
        instruments.append(result)
        print(alias, result['status'], len(result['rows']), flush=True)
    out.write_text(json.dumps(dict(started=started, finished=datetime.now(timezone.utc).isoformat(),
        account_currency=account.currency, account_currency_digits=account.currency_digits,
        terminal_build=mt5.terminal_info().build, python_mt5_version=mt5.__version__, fx_contracts=fx_info,
        instruments=instruments, historical=False, new_orders_sent=0), indent=2), encoding='utf-8')
finally:
    mt5.shutdown()
