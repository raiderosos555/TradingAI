"""Offline archive checks and evidence exports; production files are read-only."""
from pathlib import Path
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import datetime,timezone
from archive import Archive,canonical
import test_archive

A=Path(__file__).resolve().parent;ROOT=A.parents[1];OUT=A/'validation'
OUT.mkdir(exist_ok=True)
out=io.StringIO()
result=unittest.TextTestRunner(stream=out,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_archive))
(OUT/'tests.txt').write_text(out.getvalue(),encoding='utf-8')
assert result.wasSuccessful(),out.getvalue()
examples=A/'examples';examples.mkdir(exist_ok=True)
doc='# SYNTHETIC TEST ONLY\n\nUS500: BUY LIMIT 100; SL 99; TP1 102; TP2 103.\nEURPLN: NO TRADE.\nOIL: HOLD prior-oil, SL 95, TP 110.\nGOLD: CANCEL prior-gold.\n\nThis is the complete synthetic fixture, not a market briefing.\n'.encode('utf-8')
metadata=(canonical(test_archive.fixture())+'\n').encode('utf-8')
(examples/'complete.synthetic.md').write_bytes(doc)
(examples/'complete.synthetic.shadow.json').write_bytes(metadata)
with tempfile.TemporaryDirectory() as tmp:
    a=Archive(tmp,clock=lambda:datetime(2026,10,26,8,0,5,tzinfo=timezone.utc))
    try:
        receipt=a.ingest(doc,metadata)
        a.export(receipt['record_id'],OUT/'synthetic-export')
        (OUT/'point-in-time.json').write_text(canonical(a.as_of('2026-10-26T08:00:05Z'))+'\n',encoding='utf-8')
    finally:a.close()
checks=[]
for name in ['research/tick_validation/verify_stage1.py','research/tick_validation/stage2/verify.py']:
    proc=subprocess.run([sys.executable,str(ROOT/name)],capture_output=True,text=True,timeout=30)
    checks.append(dict(check=name,passed=proc.returncode==0,output=proc.stdout+proc.stderr))
assert all(c['passed'] for c in checks),checks
assert 'MetaTrader5' not in sys.modules
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
(OUT/'result.json').write_text(canonical(dict(schema_version='shadow-validation-1.0',tests=result.testsRun,
    passed=result.wasSuccessful(),real_broker_orders=0,full_backtest_run=False,production_checks=checks,
    synthetic_export_id=receipt['record_id']))+'\n',encoding='utf-8')
files=[p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'archive' not in p.relative_to(A).parts and p!=OUT/'manifest.json']
(OUT/'manifest.json').write_text(canonical(dict(files=[dict(path=p.relative_to(A).as_posix(),sha256=sha(p)) for p in sorted(files)]))+'\n',encoding='utf-8')
print(f'PASS: {result.testsRun} archive tests, exact synthetic export, immutable prior research and production integrity. No MT5 connection.')
