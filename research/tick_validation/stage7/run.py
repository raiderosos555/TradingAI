from pathlib import Path
import hashlib,io,json,sys,unittest
import test_delayed

A=Path(__file__).resolve().parent;ROOT=A.parents[2]
out=io.StringIO();r=unittest.TextTestRunner(stream=out,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_delayed))
(A/'tests.txt').write_text(out.getvalue(),encoding='utf-8');assert r.wasSuccessful(),out.getvalue()
assert 'MetaTrader5' not in sys.modules
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
for item in read(A.parent/'inputs/protected_hashes.json'):assert sha(ROOT/item['path'])==item['sha256']
for name in ['stage1_manifest.json',*[f'stage{i}/manifest.json' for i in range(2,7)]]:
    manifest=A.parent/name
    for item in read(manifest)['files']:assert sha(manifest.parent/item['path'])==item['sha256']
for trace in test_delayed.TRACES.values():
    assert trace['config']['terminal_path']=='IN_MEMORY_ONLY'
    assert trace['account']['server']=='SIMULATOR' and trace['account']['login']==123456
    assert trace['config']['risk']['max_trade_pct']==.1 and trace['config']['risk']['max_daily_loss_pct']==.5
(A/'traces.json').write_text(json.dumps(test_delayed.TRACES,indent=2,allow_nan=False),encoding='utf-8')
result=dict(stage='DELAYED_EXECUTION_RISK_PARITY',tests=r.testsRun,passed=r.wasSuccessful(),
            real_broker_api_imported=False,new_orders_sent=0,full_backtest_run=False,latency_calibrated=False,
            historical_costs_verified=False,production_unchanged=True,traces_sha256=sha(A/'traces.json'))
(A/'validation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
files=[p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=A/'manifest.json']
(A/'manifest.json').write_text(json.dumps(dict(files=[dict(path=p.relative_to(A).as_posix(),sha256=sha(p)) for p in sorted(files)]),indent=2),encoding='utf-8')
print('PASS:',r.testsRun,'delayed fill/risk/ledger cases; prior artifacts and production unchanged; no real orders.')
