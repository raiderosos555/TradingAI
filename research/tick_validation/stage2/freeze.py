"""Freeze production policy for isolated, synthetic contract tests. Never edit production."""
from pathlib import Path
import hashlib,json,shutil
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
files=[*sorted((ROOT/'trading_ai').glob('*.py')),ROOT/'config.json',ROOT/'config.demo.json']
rows=[]
for src in files:
 rel=src.relative_to(ROOT);dst=A/'source_snapshot'/rel;dst.parent.mkdir(parents=True,exist_ok=True)
 if not dst.exists():shutil.copy2(src,dst)
 sha=hashlib.sha256(src.read_bytes()).hexdigest()
 if hashlib.sha256(dst.read_bytes()).hexdigest()!=sha:raise RuntimeError('Snapshot differs: create a new research version, do not overwrite it')
 rows.append({'path':rel.as_posix(),'sha256':sha})
p=A/'source_manifest.json'
if not p.exists():p.write_text(json.dumps(rows,indent=2),encoding='utf-8')
assert json.loads(p.read_text())==rows
print('Frozen',len(rows),'source/config files')
