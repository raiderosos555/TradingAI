"""Reproducible chronological validation; no parameter optimization or MT5 calls."""
from __future__ import annotations

import math
import hashlib
from collections import Counter
from datetime import datetime, timezone
from statistics import median

from .backtest import replay
from .journal import atomic_write
from .models import Blocked, canonical, digest, read_json, timestamp, utcnow
from .strategy import engine_config


def source_hashes():
    from pathlib import Path
    folder = Path(__file__).parent
    return {name:hashlib.sha256((folder/name).read_bytes()).hexdigest()
            for name in ['backtest.py','strategy.py','analyzer.py','indicators.py','risk.py']}


def win_interval(wins, count):
    """Wilson 95% descriptive interval, assuming independent Bernoulli outcomes."""
    if not count:
        return None
    z = 1.959963984540054
    p = wins/count
    denominator = 1+z*z/count
    center = (p+z*z/(2*count))/denominator
    half = z*math.sqrt(p*(1-p)/count+z*z/(4*count*count))/denominator
    return [max(0,center-half), min(1,center+half)]


def summarize(result):
    trades = result['trades']
    n = len(trades)
    wins = sum(t['net']>0 for t in trades)
    return {'trades':n, 'wins':wins, 'win_rate':result['win_rate'],
        'win_rate_interval_95':win_interval(wins,n), 'profit_factor':result['profit_factor'],
        'net':result['net'], 'average_net':result['net']/n if n else None,
        'expectancy_R':result['sum_R']/n if n else None,
        'max_drawdown_cash':result['max_drawdown_cash'], 'max_drawdown_pct':result['max_drawdown_pct'],
        'by_strategy':{name:{'trades':sum(t['strategy']==name for t in trades),
                             'net':sum(t['net'] for t in trades if t['strategy']==name)}
                       for name in sorted({t['strategy'] for t in trades})},
        'skipped':dict(Counter(x['reason'] for x in result['skipped_setups']))}


def segments(bars, split, warmup):
    boundary = next((i for i,b in enumerate(bars) if b['time'] >= split), len(bars))
    if boundary <= warmup or len(bars)-boundary < 100:
        raise Blocked('Insufficient development or validation history')
    return [('development',bars[:boundary]), ('validation',bars[boundary-warmup:])]


def validate_dataset(folder):
    manifest = read_json(folder/'manifest.json')
    c = manifest['config']
    if digest(c) != manifest['config_hash']:
        raise Blocked('Frozen configuration checksum differs')
    rows = []
    output = folder/'validation'
    for item in manifest['instruments']:
        alias = item['instrument']
        data = read_json(folder/(alias+'.json'))
        if digest(data) != item['data_sha256']:
            raise Blocked(alias+': history checksum differs')
        warmup = engine_config(c)['bars']
        for period, bars in segments(data['bars'],timestamp(manifest['validation_start']).timestamp(),warmup):
            # Freeze the estimate using ONLY the 200 candles before this segment's entries.
            # H1 spread is a proxy, not a historical Bid/Ask tick series.
            spreads = [b.get('spread',0) for b in bars[:warmup] if b.get('spread',0)>0]
            if len(spreads) < warmup*.9:
                raise Blocked(alias+': missing warm-up spread data')
            base_spread = median(spreads)
            for scenario, multiplier in [('base',1),('cost_stress',3)]:
                costs = {'spread_points':base_spread*multiplier, 'slippage_points':2*multiplier,
                         'commission_per_lot_roundtrip':10*multiplier, 'swap_per_lot_per_day':-5*multiplier}
                result = replay(c, alias, bars, data['contract'], costs, manifest['initial_equity'])
                result.update(period=period, scenario=scenario, orders_sent=0, data_sha256=item['data_sha256'],
                              config_hash=manifest['config_hash'], historical_costs_verified=False,
                              historical_fx_verified=False)
                atomic_write(output/(alias+'-'+period+'-'+scenario+'.json'), canonical(result))
                row = {'instrument':alias, 'period':period, 'scenario':scenario,
                       'bars_traded':len(bars)-warmup, 'costs':costs, **summarize(result)}
                rows.append(row)
                print(f"{alias} {period} {scenario}: n={row['trades']} net={row['net']:.2f} PF={row['profit_factor']}", flush=True)
    summary = {'at':utcnow().isoformat(), 'orders_sent':0, 'simulation':True,
        'source_sha256':source_hashes(),
        'profitability_validated':False, 'parameters_optimized':False,
        'config_hash':manifest['config_hash'], 'initial_equity_per_instrument':manifest['initial_equity'],
        'currency':manifest['currency'], 'requested_start':manifest['requested_start'],
        'requested_end':manifest['requested_end'], 'validation_start':manifest['validation_start'],
        'bars':sum(x['bars'] for x in manifest['instruments']),
        'limitations':manifest['limitations']+result['limitations']+[
            'Spread estimated from prior 200 H1 bars; fees and swap are illustrative, not confirmed broker charges',
            'No combined account return: instruments are replayed independently, without the shared two-position limit',
            'Wilson intervals assume independent trades and are descriptive, not forecasts of future win rates'],
        'results':rows}
    atomic_write(output/'summary.json',canonical(summary))
    lines = ['# Test historyczny strategii — 24.10.2026', '',
        'To test badawczy na rzeczywistych świecach brokera. Nie wysłano żadnego zlecenia.', '',
        f"Zakres zamówiony: {manifest['requested_start'][:10]}–{manifest['requested_end'][:10]}; {summary['bars']:,} świec H1, siedem instrumentów.",
        f"Podział chronologiczny: 70% okresu do analizy, 30% do weryfikacji od {manifest['validation_start'][:10]}. Parametry zamrożono przed tym przebiegiem; nie optymalizowano ich na wynikach.",
        'Część historii była używana we wcześniejszym teście technicznym, dlatego nie nazywamy tego całkowicie niewidzianą próbą. Nową próbą będzie przyszły test DEMO.', '',
        '## Wyniki okresu weryfikacji', '',
        'Każdy instrument ma oddzielną symulację z kapitałem początkowym '+f"{manifest['initial_equity']:.2f} PLN i konfiguracją minimalnych lotów przygotowaną do DEMO. Wyników nie wolno sumować jako wyniku wspólnego rachunku.", '',
        '| Instrument | Transakcje | Trafność | Przedział 95%* | Profit factor | Netto PLN | Śr. R | Max DD PLN |',
        '|---|---:|---:|---:|---:|---:|---:|---:|']
    fmt = lambda x: '—' if x is None else f'{x:.2f}'
    for row in rows:
        if row['period']!='validation' or row['scenario']!='base': continue
        rate = '—' if row['win_rate'] is None else f"{100*row['win_rate']:.1f}%"
        interval = row['win_rate_interval_95']
        ci = '—' if not interval else f'{100*interval[0]:.1f}–{100*interval[1]:.1f}%'
        lines.append(f"| {row['instrument']} | {row['trades']} | {rate} | {ci} | {fmt(row['profit_factor'])} | {fmt(row['net'])} | {fmt(row['expectancy_R'])} | {fmt(row['max_drawdown_cash'])} |")
    lines += ['', '*Przybliżony przedział Wilsona przy założeniu niezależnych transakcji. Transakcje mogą być zależne, więc nie jest to prognoza przyszłej skuteczności.', '',
        'Profit factor = suma zysków / suma strat po przyjętych kosztach; wartość poniżej 1 oznacza stratę. Trafność sama nie wystarcza do oceny strategii.', '',
        '## Trzykrotnie większe koszty', '',
        '| Instrument | Transakcje | Profit factor | Netto PLN |', '|---|---:|---:|---:|']
    for row in rows:
        if row['period']=='validation' and row['scenario']=='cost_stress':
            lines.append(f"| {row['instrument']} | {row['trades']} | {fmt(row['profit_factor'])} | {fmt(row['net'])} |")
    lines += ['', 'Większy spread może zablokować wejścia przez limity ryzyka. Zero transakcji nie oznacza pozytywnego wyniku testu.', '',
        '## Metoda i ograniczenia', '',
        '- Sygnał tylko z zamkniętych świec, wykonanie na otwarciu następnej. Jeśli świeca obejmuje SL i TP, rozstrzygamy na niekorzyść pozycji.',
        '- Uwzględniono spread, poślizg, prowizję i uproszczony swap. Spread to mediana wcześniejszych 200 świec; pozostałe koszty są założeniami: 2 punkty poślizgu, 10 PLN/lot prowizji łącznie, −5 PLN/lot/dzień swapu. Nie są potwierdzonym taryfikatorem brokera.',
        '- Przelicznik do PLN oraz parametry kontraktu pochodzą z obecnego MT5. Brakuje historycznej serii przeliczeń walutowych i zmian specyfikacji.',
        '- Zastosowano limit lota, limit ryzyka oraz filtry spreadu/ATR przygotowane do DEMO. Minimalny lot zwykle uniemożliwia TP1 częściowym zamknięciem.',
        '- Brakuje wspólnej symulacji portfela, historycznego kalendarza i realizacji na tickach. Zarządzanie raz na świecę H1 różni się od działającego programu.',
        '- Okresy zaczynają się bez pozycji i kończą wymuszonym zamknięciem. Przerwy sesyjne/weekendy są zachowane; pełności harmonogramu brokera nie zweryfikowano niezależnie.',
        '- Wynik dodatni nie potwierdza przewagi. Przed oceną gotowości potrzebne są test na tickach, koszty i FX historyczne, portfel oraz niezależny forward DEMO.', '',
        'Dane, konfiguracja i ich SHA-256: `../manifest.json`. Szczegóły wszystkich 28 przebiegów oraz transakcje: pliki JSON w tym katalogu.', '',
        'Odczyt historii oparto na [oficjalnym API MT5](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py). Liczba dostępnych świec zależy od historii terminala; zapisano rzeczywisty zakres każdego instrumentu.', '']
    atomic_write(output/'report.md','\n'.join(lines))
    return summary
