from pathlib import Path
import json,hashlib
A=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=read(A/'comparison.json')
assert r['tests']==9 and r['tests_passed'] and r['current_observations']==96
assert [x['matches'] for x in r['comparisons']]==[24,42,64,96]
assert len(r['historical_checks'])==12
assert all(x['matches'] and x['rounded_cash_unambiguous'] for x in r['historical_checks'] if x['round_profit_currency'])
assert not r['historical_model_approved'] and r['accepted_historical_cost_policy'] is None
assert not r['full_backtest_run'] and r['new_orders_sent']==0
assert sum(read(p)['count'] for p in (A/'inputs').glob('fx-*/coverage.json'))==189
files=[p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=A/'manifest.json']
(A/'manifest.json').write_text(json.dumps(dict(stage='FX_AND_CASH_ROUNDING_DIAGNOSTICS',files=[dict(path=p.relative_to(A).as_posix(),sha256=sha(p)) for p in sorted(files)]),indent=2),encoding='utf-8')
print('Sealed: 96 current broker calculations, 189 FX ticks, 9 tests; historical cost policy not approved.')
