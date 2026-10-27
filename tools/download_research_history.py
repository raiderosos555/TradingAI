"""Read-only download of six months of H1 data, with immutable research inputs."""
import json
import sys
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from trading_ai.broker import MT5Broker
from trading_ai.journal import atomic_write
from trading_ai.models import canonical, digest, load_config, utcnow
from trading_ai.strategy import engine_config


def main():
    c = load_config(ROOT/'config.demo.json')
    end = utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    start = end-timedelta(days=180)
    split = start+(end-start)*.7
    folder = ROOT/'exchange/research'/('history-'+end.strftime('%Y%m%d'))
    if (folder/'manifest.json').exists():
        raise ValueError('Research dataset already frozen; reuse it instead of overwriting')
    b = MT5Broker(c['terminal_path'], c.get('broker_time_offset_seconds',0))
    try:
        account = b.snapshot()['account']
        if [account['login'],account['server']] != [c['account_login'],c['account_server']]:
            raise ValueError('Account mismatch')
        manifest = {'downloaded_at':utcnow().isoformat(), 'orders_sent':0,
            'requested_start':start.isoformat(), 'requested_end':end.isoformat(),
            'validation_start':split.isoformat(), 'timeframe':'H1', 'config_hash':digest(c),
            'initial_equity':account['equity'], 'currency':account['currency'],
            'config':c, 'instruments':[],
            'limitations':['Broker timestamps normalized using the currently observed offset; historical offset not independently verified',
                'Current contract specifications and cash conversion, not a historical contract/FX series',
                'Chronological validation, not a blind holdout: part of this history was used by an earlier pipeline test']}
        for alias,spec in c['symbols'].items():
            market = b.market(spec['broker'], 'H1', engine_config(c)['bars'])
            info,tick = market['info'],market['tick']
            contract = {k:info[k] for k in ('point','trade_tick_size','digits','volume_min','volume_max','volume_step')}
            step = max(info['trade_tick_size']*100, tick['bid']*.001)
            probe = info['volume_min']
            contract['cash_per_price_unit_per_lot'] = abs(b.profit(0,spec['broker'],probe,tick['bid'],tick['bid']+step))/step/probe
            bars = b.rates(spec['broker'], 'H1', start, end)
            if len(bars) < 800 or any(x['time'] >= y['time'] for x,y in zip(bars,bars[1:])):
                raise ValueError(alias+': insufficient or disordered history')
            payload = {'instrument':alias, 'symbol':spec['broker'], 'contract':contract, 'bars':bars}
            atomic_write(folder/(alias+'.json'), canonical(payload))
            item = {'instrument':alias, 'bars':len(bars), 'first':bars[0]['time'], 'last':bars[-1]['time'],
                    'data_sha256':digest(payload), 'gaps_over_3h':sum(y['time']-x['time']>10800 for x,y in zip(bars,bars[1:])),
                    'positive_spread_bars':sum(x.get('spread',0)>0 for x in bars)}
            manifest['instruments'].append(item)
            print(json.dumps(item), flush=True)
        atomic_write(folder/'manifest.json', json.dumps(manifest, indent=2))
        print(str(folder/'manifest.json'), flush=True)
    finally:
        b.close()


if __name__ == '__main__':
    main()
