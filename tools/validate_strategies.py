"""Offline replay of archived real bars with explicitly illustrative cost scenarios.

Reads current contract conversion from MT5; never sends or checks an order.
These scenarios test the research pipeline, not historical broker costs or profitability.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from trading_ai.backtest import replay
from trading_ai.broker import MT5Broker
from trading_ai.collector import MarketArchive
from trading_ai.models import load_config, utcnow
from trading_ai.journal import atomic_write, process_lock
from trading_ai.strategy import engine_config


def main():
    c = load_config(ROOT/'config.local.json')
    b = MT5Broker(c['terminal_path'], c.get('broker_time_offset_seconds', 0))
    archive = MarketArchive(ROOT/'state', c['account_login'], c['account_server'], c.get('broker_time_offset_seconds', 0))
    rows = []
    try:
        account = b.snapshot()['account']
        if [account['login'], account['server']] != [c['account_login'], c['account_server']]:
            raise ValueError('Account mismatch')
        for alias, spec in c['symbols'].items():
            market = b.market(spec['broker'], 'H1', 200)
            i, tick = market['info'], market['tick']
            contract = {k:i[k] for k in ('point', 'trade_tick_size', 'digits', 'volume_min', 'volume_max', 'volume_step')}
            # Current conversion is explicit and is NOT called historical FX.
            step = max(i['trade_tick_size']*100, tick['bid']*.001)
            contract['cash_per_price_unit_per_lot'] = abs(b.profit(0, spec['broker'], 1., tick['bid'], tick['bid']+step))/step
            bars = archive.bars(spec['broker'], engine_config(c)['timeframe'])
            for label, multiple in (('illustrative', 1), ('cost_stress', 3)):
                costs = {'spread_points':max(1, (tick['ask']-tick['bid'])/i['point'])*multiple,
                         'slippage_points':2*multiple, 'commission_per_lot_roundtrip':10*multiple,
                         'swap_per_lot_per_day':-5*multiple}
                result = replay(c, alias, bars, contract, costs)
                result.update(scenario=label, historical_broker_costs_verified=False,
                              historical_fx_verified=False, orders_sent=0, source='Archived broker OHLC')
                path = ROOT/'exchange'/'backtests'/(alias+'-'+label+'.json')
                atomic_write(path, json.dumps(result, indent=2))
                rows.append({'instrument':alias, 'scenario':label, 'bars':len(bars), 'trades':len(result['trades']),
                             'net':result['net'], 'sum_R':result['sum_R'], 'max_drawdown_cash':result['max_drawdown_cash']})
        summary = {'at':utcnow().isoformat(), 'orders_sent':0, 'simulation':True,
                   'purpose':'Research pipeline and cost sensitivity only; costs and historical FX are unverified',
                   'profitability_validated':False, 'results':rows}
        atomic_write(ROOT/'docs'/'strategy-validation.json', json.dumps(summary, indent=2))
        print(json.dumps(summary, indent=2))
    finally:
        b.close()
        archive.close()


if __name__ == '__main__':
    with process_lock(ROOT/'state'):
        main()
