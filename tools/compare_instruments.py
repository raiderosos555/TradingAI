"""Read-only comparison of every configured market; never authorizes or sends orders."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from trading_ai.broker import MT5Broker
from trading_ai.calendar import assessment
from trading_ai.journal import atomic_write
from trading_ai.models import load_config, utcnow
from trading_ai.strategy import SignalEngine


def main():
    c = load_config(ROOT / 'config.local.json')
    b = MT5Broker(c['terminal_path'], c.get('broker_time_offset_seconds', 0))
    try:
        snapshot = b.snapshot()
        if [snapshot['account']['login'], snapshot['account']['server']] != [c['account_login'], c['account_server']]:
            raise ValueError('Configured account mismatch')
        engine = SignalEngine(c, b)
        rows = []
        for alias, spec in c['symbols'].items():
            row = {'instrument': alias, 'symbol': spec['broker']}
            try:
                now = utcnow()
                item = engine.evaluate(alias, now)
                m = b.market(spec['broker'])
                info, tick = m['info'], m['tick']
                f = item['analysis']
                spread = tick['ask'] - tick['bid']
                volume = info['volume_min']
                # Comparable diagnostic only. This is not a valid entry/exit plan.
                distance = max(1.5 * f['atr14'],
                               (max(info['trade_stops_level'], info['trade_freeze_level']) + 2) * info['point'])
                costs = spec['cost_buffer_per_lot'] * volume
                examples = []
                for side, price, sign in ((0, tick['ask'], 1), (1, tick['bid'], -1)):
                    worst = price + sign * spec['deviation_points'] * info['point']
                    loss = abs(b.profit(side, spec['broker'], volume, worst, price - sign * distance))
                    examples.append(loss + costs)
                row.update(as_of=now.isoformat(), trend=f['trend'],
                           setup=item['signal']['signal']['kind'] if item.get('signal') else None,
                           reason=item['reason'], spread_points=spread / info['point'],
                           spread_price=spread, spread_pct_ATR=100 * spread / f['atr14'],
                           configured_spread_limit=spec['max_spread_points'],
                           within_configured_spread=spread / info['point'] <= spec['max_spread_points'] + 1e-6,
                           min_volume=volume, illustrative_stop_distance=distance,
                           illustrative_min_volume_risk=max(examples),
                           margin_min_volume=b.margin(0, spec['broker'], volume, tick['ask']),
                           calendar=assessment(c, b, alias, now)['status'],
                           status='ANALYZED')
            except Exception as exc:
                row.update(status='UNAVAILABLE', reason=str(exc))
            rows.append(row)
        report = {'generated_at': utcnow().isoformat(), 'source': 'MT5', 'orders_sent': 0,
                  'currency': snapshot['account']['currency'], 'markets': rows,
                  'notes': ['All configured instruments are scanned independently.',
                            'Points differ between contracts; compare spread/ATR as well.',
                            'Illustrative risk uses minimum volume, 1.5 ATR, configured deviation and cost buffer.',
                            'Costs and limits outside the approved GOLD test have not been approved for execution.',
                            'This comparison is not a trading plan, authorization or full Risk Manager validation.']}
        lines = ['# Porównanie wszystkich instrumentów', '', report['generated_at'], '',
                 'Odczyt MT5, bez dyspozycji. Ryzyko ilustracyjne przy minimum lota i SL 1,5 ATR; nie jest planem transakcji.', '',
                 '| Rynek | Trend H1 | Setup | Spread pkt | Spread / ATR | Min. lot | Ryzyko ilustracyjne '+report['currency']+' | Kalendarz |',
                 '|---|---|---|---:|---:|---:|---:|---|']
        for row in rows:
            if row['status'] == 'ANALYZED':
                lines.append(f"| {row['instrument']} | {row['trend']} | {row['setup'] or 'brak'} | {row['spread_points']:.1f} | {row['spread_pct_ATR']:.2f}% | {row['min_volume']} | {row['illustrative_min_volume_risk']:.2f} | {row['calendar']} |")
            else:
                lines.append(f"| {row['instrument']} | niedostępne | {row['reason'].replace('|', '/')} | — | — | — | — | — |")
        lines += ['', 'Punkty mają różną wartość na różnych kontraktach. Wspólny domyślny limit 30 punktów nie jest kalibracją kosztów dla wszystkich rynków.',
                  'Brak setupu oznacza brak propozycji strategii. Tabela nie uprawnia do otwarcia pozycji.',
                  'Parametry nowych testów wymagają odrębnego zatwierdzenia; pełny Risk Manager obowiązuje przed każdą dyspozycją.']
        atomic_write(ROOT / 'exchange/instrument-comparison.json', json.dumps(report, indent=2))
        atomic_write(ROOT / 'exchange/instrument-comparison.md', '\n'.join(lines))
        print('\n'.join(lines))
    finally:
        b.close()


if __name__ == '__main__':
    main()
