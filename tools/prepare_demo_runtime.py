"""Prepare the bounded DEMO configuration from verified broker contract minima.

--record-authorization records the operator's existing explicit instruction to
run autonomous DEMO tests; it never activates LIVE or sends a broker request.
"""
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from trading_ai.broker import MT5Broker
from trading_ai.journal import Journal, atomic_write
from trading_ai.models import canonical, load_config, utcnow
from trading_ai.runtime import configuration_hash


def main(record=False):
    c = load_config(ROOT/'config.local.json')
    b = MT5Broker(c['terminal_path'], c.get('broker_time_offset_seconds', 0))
    try:
        a = b.snapshot()['account']
        if [a['login'], a['server'], a['trade_mode']] != [c['account_login'], c['account_server'], 0]:
            raise ValueError('Expected configured DEMO account')
        c.update(mode='DEMO', live_enabled=False, live_allowlist=[])
        c['runtime'] = {'authorization_id': 'EXAMPLE-NOT-AUTHORIZED',
                        'starts_at': '2026-10-25T21:00:00+01:00',
                        'ends_at': '2026-10-30T23:00:00+01:00'}
        c['risk'].update(max_trade_pct=.1, max_total_pct=.2, max_daily_loss_pct=.5, max_positions=2)
        c['engine'].update(risk_pct=.1)
        limits = {'GOLD':60, 'US500':10, 'US100':20, 'OIL':8, 'EURUSD':15, 'GBPUSD':20, 'EURPLN':30}
        for alias, spec in c['symbols'].items():
            info = b.required(b.mt5.symbol_info(spec['broker']), 'contract')
            spec.update(trading_enabled=True, max_volume=info['volume_min'],
                        max_spread_points=limits[alias], max_spread_atr_ratio=.2,
                        cost_buffer_per_lot=100)
        path = ROOT/'config.demo.json'
        if path.exists() and configuration_hash(load_config(path)) != configuration_hash(c):
            raise ValueError('Existing DEMO config differs; inspect before replacement')
        atomic_write(path, json.dumps(c, indent=2))
        load_config(path)
        if record:
            authorization = {'id':c['runtime']['authorization_id'], 'at':utcnow().isoformat(),
                'config_hash':configuration_hash(c), 'allowed_offsets':[3600,7200],
                'scope':'Bounded autonomous DEMO forward test, minimum broker lot, all seven markets',
                'operator_source': ['ok lecmy z testami na rachunku',
                    'ty mnie nie musisz pytac o zgode ty masz sam dzialac',
                    'dodatkowo to jest konto demo wiec mozesz probowac dowoli', 'przygotujmy to'],
                'window':c['runtime'], 'live_authorized':False}
            j = Journal(ROOT/'state')
            try:
                if j.setting('runtime_revoked') or (ROOT/'state/runtime/REVOKED').exists():
                    raise ValueError('Existing revocation must not be silently reset')
                key = 'runtime_authorization:'+authorization['id']
                prior = j.setting(key)
                if prior and prior['config_hash'] != authorization['config_hash']:
                    raise ValueError('Authorization already bound to different config')
                if not prior:
                    j.set_setting(key, authorization)
                    j.event('operator_runtime_authorization', authorization)
                    atomic_write(ROOT/'state/runtime-authorization.json', canonical(authorization))
            finally:
                j.close()
        print(json.dumps({'config':str(path), 'authorization_recorded':record,
                          'window':c['runtime'], 'minimum_lots':{a:s['max_volume'] for a,s in c['symbols'].items()}}, indent=2))
    finally:
        b.close()


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--record-authorization', action='store_true')
    main(p.parse_args().record_authorization)
