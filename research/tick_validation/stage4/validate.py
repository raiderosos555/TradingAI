from pathlib import Path
import hashlib,json,io,sys,unittest
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
import analysis,test_analysis
out=io.StringIO();r=unittest.TextTestRunner(stream=out,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_analysis))
(A/'tests.txt').write_text(out.getvalue(),encoding='utf-8');assert r.wasSuccessful(),out.getvalue()
d=analysis.analyze()
assert len(d['fills'])==5 and d['raw_ticks']==2338
assert all(x['fill_matches_prior_quote'] and x['quote_price_unambiguous'] for x in d['fills'])
assert [x['prior_quote_age_ms'] for x in d['fills']]==[46,19,76,24,49]
assert [x['adverse_price_difference'] for x in d['fills']]==[0,0,0,.2,0]
assert d['realized_net_PLN']==-.56 and len(d['positions'])==2
assert sum(p['closing_deals'] for p in d['positions'])==3
assert not d['accepted_historical_utc_segments'] and not d['full_backtest_run'] and d['new_orders_sent']==0
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
c=json.loads((A/'collection.json').read_text())
assert sha(ROOT/c['source_report'])==sha(A/'inputs/broker-report.json')==c['source_sha256']
assert sha(A.parent/'stage3/probe.py')==c['worker_source_sha256']
for item in json.loads((A.parent/'inputs/protected_hashes.json').read_text()):assert sha(ROOT/item['path'])==item['sha256']
for stage in ['stage1_manifest.json','stage2/manifest.json','stage3/manifest.json']:
    manifest=A.parent/stage
    for item in json.loads(manifest.read_text())['files']:assert sha(manifest.parent/item['path'])==item['sha256']
data=dict(tests=r.testsRun,passed=r.wasSuccessful(),real_deals_compared=5,matched_to_prior_quote=5,
          new_orders_sent=0,full_backtest_run=False,production_unchanged=True,prior_stages_unchanged=True)
(A/'validation.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
files=[p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=A/'manifest.json']
(A/'manifest.json').write_text(json.dumps(dict(stage='EMPIRICAL_FILL_CHECK',files=[dict(path=p.relative_to(A).as_posix(),sha256=sha(p)) for p in sorted(files)]),indent=2),encoding='utf-8')
print('PASS:',r.testsRun,'unit cases, 5 observed deal comparisons, raw history, net cash ledger, protected sources.')
