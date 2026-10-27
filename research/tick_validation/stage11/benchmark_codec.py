"""Lossless codec check against a completed real capture; no MT5 connection."""
import gzip, hashlib, json, time
from pathlib import Path
A = Path(__file__).resolve().parent
source = A/'inputs/GOLD/raw-12-16/ticks.raw.json.gz'
target = A/'codec_validation.json'
if target.exists(): raise SystemExit('Immutable codec result exists')
raw = gzip.decompress(source.read_bytes())
records = json.loads(raw)
started = time.monotonic()
encoded = gzip.compress(json.dumps(records,separators=(',',':')).encode('utf-8'),compresslevel=1,mtime=0)
duration = time.monotonic()-started
assert gzip.decompress(encoded)==raw
target.write_text(json.dumps(dict(source=source.relative_to(A).as_posix(), records=len(records),
    source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(), decoded_sha256=hashlib.sha256(raw).hexdigest(),
    decompressed_bytes_identical=True, batched_serialization_and_compression_seconds=duration,
    original_compressed_bytes=source.stat().st_size, fast_compressed_bytes=len(encoded), broker_called=False),indent=2),encoding='utf-8')
print('Codec identical:',len(records),'real ticks; elapsed',round(duration,3),'seconds',flush=True)
