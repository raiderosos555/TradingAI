"""Derive the same audited read-only probe with lossless faster serialization."""
from pathlib import Path
A = Path(__file__).resolve().parent
target = A/'fast_probe.py'
if target.exists(): raise SystemExit('Worker exists')
source = (A.parent/'stage3/probe.py').read_text(encoding='utf-8')
old = "    with gzip.open(out/'ticks.raw.json.gz','wt',encoding='utf-8') as f:json.dump(kept,f,separators=(',',':'))"
new = """    phase('SERIALIZE_START',count=len(kept))
    with gzip.open(out/'ticks.raw.json.gz','wt',encoding='utf-8',compresslevel=1) as f:f.write(json.dumps(kept,separators=(',',':')))
    phase('SERIALIZE_DONE')"""
assert source.count(old)==1
target.write_text(source.replace(old,new),encoding='utf-8')
print('Created isolated worker; same raw data/API, lossless batched compression level 1')
