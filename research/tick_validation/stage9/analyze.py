"""Replay captured broker arithmetic offline, preserving all predefined hypotheses."""
import hashlib, io, json, math, sys, unittest
from pathlib import Path
A = Path(__file__).resolve().parent
ROOT = A.parents[2]
sys.path.insert(0, str(ROOT))
from research.tick_validation.stage8.cash import diagnostic_profit, dec, rounded
from grid import stable_fx

def reported_cash(value, digits):
    """Accept only currency-grid values within two binary ULPs of the API float."""
    raw = dec(value)
    amount = rounded(raw, digits)
    if abs(raw - amount) > 2 * dec(math.ulp(float(value))):
        raise ValueError('Broker cash is not on account-currency grid')
    return amount

def evaluate(capture, config):
    results = []
    for instrument in capture['instruments']:
        result = dict(alias=instrument['alias'], symbol=instrument['symbol'], observations=len(instrument['rows']), comparisons=[])
        if instrument['status'] != 'OBSERVED':
            result['status'] = instrument['status']
            results.append(result)
            continue
        info = instrument['contract']
        currency = info['currency_profit']
        result.update(currency_profit=currency, calc_mode=info['trade_calc_mode'])
        # Only modes actually observed here are implemented. Unsupported contracts stay explicit.
        if info['trade_calc_mode'] not in [0, 4] or capture['account_currency'] != 'PLN' or currency not in ['USD', 'PLN']:
            result['status'] = 'UNSUPPORTED_CONTRACT'
            results.append(result)
            continue
        result['status'] = 'DIAGNOSTIC_ONLY'
        candidates = config['fx_candidates'] if currency == 'USD' else [None]
        for candidate in candidates:
            for round_first in config['round_profit_currency_hypotheses']:
                cases = []
                for index, row in enumerate(instrument['rows']):
                    case = dict(index=index, broker_profit=row['broker_profit'])
                    if row['broker_profit'] is None:
                        case['status'] = 'BROKER_CALCULATION_ERROR'
                    elif candidate and not stable_fx(row['fx_before'].get(candidate), row['fx_after'].get(candidate)):
                        case['status'] = 'FX_BRACKET_UNSTABLE_OR_MISSING'
                    else:
                        if candidate:
                            fx = row['fx_before'][candidate]
                            calc = diagnostic_profit(row['side'], row['entry'], row['exit'], row['volume'],
                                info['trade_contract_size'], fx['bid'], fx['ask'], round_first,
                                profit_digits=config['currency_digits'][currency], account_digits=capture['account_currency_digits'],
                                fx_digits=capture['fx_contracts'][candidate]['digits'])
                            expected = dec(calc['profit_account'])
                        else:
                            raw = (dec(row['exit']) - dec(row['entry'])) * dec(row['volume']) * dec(info['trade_contract_size']) * (1 if row['side'] == 'BUY' else -1)
                            intermediate = rounded(raw, config['currency_digits'][currency]) if round_first else raw
                            expected = rounded(intermediate, capture['account_currency_digits'])
                            calc = dict(gross_profit_currency_unrounded=str(raw), profit_account=str(expected), conversion_side='NONE')
                        try:
                            reported = reported_cash(row['broker_profit'], capture['account_currency_digits'])
                        except ValueError:
                            case['status'] = 'BROKER_CASH_OFF_CURRENCY_GRID'
                        else:
                            error = expected - reported
                            case.update(status='COMPARED', calculation=calc, broker_cash_normalized=str(reported),
                                binary_representation_residual=str(dec(row['broker_profit']) - reported),
                                error_PLN=str(error), matches=error == 0)
                    cases.append(case)
                compared = [case for case in cases if case['status'] == 'COMPARED']
                result['comparisons'].append(dict(fx_symbol=candidate, round_profit_currency=round_first,
                    compared=len(compared), excluded=len(cases)-len(compared), matches=sum(case['matches'] for case in compared),
                    maximum_absolute_error_PLN=str(max([abs(dec(case['error_PLN'])) for case in compared], default=dec(0))), cases=cases))
        results.append(result)
    return results

def main():
    read = lambda p: json.loads(p.read_text(encoding='utf-8'))
    capture, config = read(A / 'capture.json'), read(A / 'config.json')
    results = evaluate(capture, config)
    from test_grid import GridTests
    output = io.StringIO()
    tests = unittest.TextTestRunner(stream=output, verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(GridTests))
    (A / 'tests.txt').write_text(output.getvalue(), encoding='utf-8')
    assert tests.wasSuccessful(), output.getvalue()
    sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
    for item in read(A.parent / 'inputs/protected_hashes.json'):
        assert sha(ROOT / item['path']) == item['sha256'], item['path']
    for name in ['stage1_manifest.json', *[f'stage{i}/manifest.json' for i in range(2, 9)]]:
        manifest = A.parent / name
        for item in read(manifest)['files']:
            assert sha(manifest.parent / item['path']) == item['sha256'], item['path']
    report = dict(schema_version=1, capture_started=capture['started'], config_sha256=sha(A / 'config.json'),
        capture_sha256=sha(A / 'capture.json'), instruments=results, tests=tests.testsRun, tests_passed=True,
        observations=sum(len(s['rows']) for s in capture['instruments']), new_orders_sent=0, full_backtest_run=False,
        historical_policy_approved=False, accepted_historical_cost_policy=None, production_and_prior_manifests_unchanged=True,
        all_data_exploratory=True)
    (A / 'comparison.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    for result in results:
        print(result['alias'], [(c['fx_symbol'], c['round_profit_currency'], c['matches'], c['compared']) for c in result['comparisons']])
    print('Tests:', tests.testsRun, 'PASS; protected production and stages 1-8 unchanged')

if __name__ == '__main__':
    main()
