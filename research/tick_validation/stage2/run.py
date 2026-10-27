"""Offline reproducible controlled tests; retain traces, never connect to MT5."""
from pathlib import Path
import hashlib
import io
import json
import platform
import sys
import unittest

A=Path(__file__).resolve().parent
ROOT=A.parents[2]
sys.path.insert(0,str(A))
import test_parity

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(name,data):
    (A/name).write_text(json.dumps(data,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')

suite=unittest.defaultTestLoader.loadTestsFromModule(test_parity)
out=io.StringIO()
result=unittest.TextTestRunner(stream=out,verbosity=2).run(suite)
(A/'tests.txt').write_text(out.getvalue(),encoding='utf-8')
save('traces.json',test_parity.TRACES)
integrity=[]
for item in json.loads((A/'source_manifest.json').read_text()):
    integrity.append(dict(path=item['path'],unchanged=sha(ROOT/item['path'])==item['sha256']))
save('production_integrity.json',integrity)
config=json.loads((A/'config.v1.json').read_text())
for cases in test_parity.TRACES.values():
    for case in cases:
        assert case['config']['terminal_path']=='IN_MEMORY_ONLY'
        for key,value in config['limits'].items():assert case['config']['risk'][key]==value
assert 'MetaTrader5' not in sys.modules,'Unexpected real broker API import'
save('tests.json',dict(tests=result.testsRun,failures=len(result.failures),errors=len(result.errors),
                       passed=result.wasSuccessful(),real_orders_sent=0,full_backtest_run=False,
                       source_unchanged=all(x['unchanged'] for x in integrity),
                       traces_sha256=sha(A/'traces.json'),python=platform.python_version()))
files=[p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'scratch' not in p.parts
       and p.name!='manifest.json']
save('manifest.json',dict(stage='CONTROLLED_POLICY_TESTS',schema_version=config['schema_version'],
                         files=[dict(path=p.relative_to(A).as_posix(),sha256=sha(p)) for p in sorted(files)]))
print(out.getvalue())
print('Real broker API imported: NO. Production integrity:',all(x['unchanged'] for x in integrity))
raise SystemExit(0 if result.wasSuccessful() and all(x['unchanged'] for x in integrity) else 1)
