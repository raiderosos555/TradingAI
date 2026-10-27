from pathlib import Path
from decimal import Decimal
import json,gzip,sys,hashlib,io,unittest
from cash import diagnostic_profit
import test_cash
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
sys.path.insert(0,str(A.parent/'stage4'))
from analysis import prior_quotes
from model import validate_stream
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
grid=read(A/'inputs/rounding-grid-current.json');assert grid['quotes_unchanged']
comparisons=[]
for symbol,fx in grid['quotes_before'].items():
    for round_first in [False,True]:
        cases=[]
        for row in grid['rows']:
            assert row['broker_profit_PLN'] is not None and row['error'][0]==1
            calc=diagnostic_profit('BUY' if row['type']==0 else 'SELL',row['entry'],row['exit'],row['volume'],grid['contract_size'],fx['bid'],fx['ask'],round_first)
            cases.append(dict(**row,diagnostic=calc,matches=Decimal(calc['profit_account'])==Decimal(str(row['broker_profit_PLN']))))
        comparisons.append(dict(fx_symbol=symbol,round_profit_currency=round_first,matches=sum(c['matches'] for c in cases),cases=cases))
report=read(A.parent/'stage4/inputs/broker-report.json');deals=report['broker_snapshot']['deals']
historical=[]
max_age=read(ROOT/'config.demo.json')['risk']['max_tick_age_seconds']*1000
for p in sorted((A/'inputs').glob('fx-*')):
    coverage=read(p/'coverage.json')
    if coverage['status']!='OBSERVED':continue
    with gzip.open(p/'ticks.json.gz','rt') as f:ticks=json.load(f)
    assert len(list(validate_stream(ticks)))==coverage['count']
    for d in deals:
        if d['entry']!=1 or not coverage['start_raw_ms']<=d['broker_raw_time_msc']<coverage['end_raw_ms']:continue
        opening=next(x for x in deals if x['position_id']==d['position_id'] and x['entry']==0)
        quotes,age=prior_quotes(ticks,d['broker_raw_time_msc'],max_age_ms=max_age)
        for round_first in [False,True]:
            variants=[diagnostic_profit('BUY' if opening['type']==0 else 'SELL',opening['price'],d['price'],d['volume'],grid['contract_size'],fx['bid'],fx['ask'],round_first) for fx in quotes]
            historical.append(dict(deal=d['ticket'],fx_symbol=coverage['symbol'],fx_age_ms=age,
                fx_raw_time_msc=quotes[0]['time_msc'],deal_raw_time_msc=d['broker_raw_time_msc'],round_profit_currency=round_first,
                historical_contract_verified=False,historical_conversion_route_verified=False,
                prior_quote_variants=quotes,rounded_cash_unambiguous=len({x['profit_account'] for x in variants})==1,
                broker_profit_PLN=d['profit'],diagnostic_variants=variants,
                matches=all(Decimal(calc['profit_account'])==Decimal(str(d['profit'])) for calc in variants)))
out=io.StringIO();tests=unittest.TextTestRunner(stream=out,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_cash))
(A/'tests.txt').write_text(out.getvalue(),encoding='utf-8');assert tests.wasSuccessful(),out.getvalue()
result=dict(current_grid=grid['at'],current_observations=len(grid['rows']),comparisons=comparisons,historical_checks=historical,
    tests=tests.testsRun,tests_passed=tests.wasSuccessful(),historical_model_approved=False,new_orders_sent=0,full_backtest_run=False,
    accepted_historical_cost_policy=None,technical_formula_source='https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants')
(A/'comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
assert [x['matches'] for x in comparisons]==[24,42,64,96]
assert all(r['matches'] for r in historical if r['round_profit_currency'])
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for item in read(A.parent/'inputs/protected_hashes.json'):assert sha(ROOT/item['path'])==item['sha256']
for name in ['stage1_manifest.json',*[f'stage{i}/manifest.json' for i in range(2,8)]]:
    p=A.parent/name
    for item in read(p)['files']:assert sha(p.parent/item['path'])==item['sha256']
print('PASS:',tests.testsRun,'cash tests;',len(grid['rows']),'current calculations; diagnostic matches:',[c['matches'] for c in comparisons],'; historical policy remains unverified.')
