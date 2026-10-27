"""Bounded serial read-only tick collection; no changes to the active terminal."""
import hashlib, json, os, subprocess, sys, time
from datetime import datetime, timezone, timedelta
from pathlib import Path
A = Path(__file__).resolve().parent
ROOT = A.parents[2]
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
cfg = read(A / 'config.json')
output = A / 'collection.json'
if output.exists() or (A / 'inputs').exists(): raise SystemExit('Immutable capture exists')
worker = A.parent / 'stage3/probe.py'
env = dict(os.environ, PYTHONPATH=str(ROOT / '.venv/Lib/site-packages'))
start, end = map(datetime.fromisoformat, [cfg['raw_start'], cfg['raw_end']])
assert start.tzinfo and end.tzinfo and end-start == timedelta(days=1)
data = dict(schema_version=1, config_sha256=sha(A / 'config.json'), worker_sha256=sha(worker),
    started_host_utc=datetime.now(timezone.utc).isoformat(), start_raw_ms=int(start.timestamp()*1000),
    end_raw_ms=int(end.timestamp()*1000), instruments=[], new_orders_sent=0, full_backtest_run=False,
    time_basis=cfg['time_basis'], accepted_historical_UTC_segments=[])
began = time.monotonic()
stop = False
for alias in cfg['aliases']:
    base = A / 'inputs' / alias
    base.mkdir(parents=True)
    instrument = dict(alias=alias, blocks=[], bar_sources=[])
    for tf, source in [('H1', ROOT / 'exchange/research/history-20261024' / (alias+'.json')),
                       ('H4', ROOT / 'research/edge_audit/inputs' / (alias+'-H4.json')),
                       ('D1', ROOT / 'research/edge_audit/inputs' / (alias+'-D1.json'))]:
        target = base / (tf+'.json')
        target.write_bytes(source.read_bytes())
        instrument['bar_sources'].append(dict(timeframe=tf, path=target.relative_to(A).as_posix(),
            original=source.relative_to(ROOT).as_posix(), sha256=sha(target)))
    data['instruments'].append(instrument)
    for hour in range(0, 24, cfg['chunk_hours']):
        lo, hi = start+timedelta(hours=hour), start+timedelta(hours=hour+cfg['chunk_hours'])
        dest = base / f'raw-{hour:02d}-{hour+cfg["chunk_hours"]:02d}'
        block = dict(start_raw_ms=int(lo.timestamp()*1000), end_raw_ms=int(hi.timestamp()*1000), path=dest.relative_to(A).as_posix())
        instrument['blocks'].append(block)
        if stop or time.monotonic()-began >= cfg['max_series_seconds_before_next_chunk']:
            block['status'] = 'NOT_ATTEMPTED_AFTER_ERROR' if stop else 'NOT_ATTEMPTED_TIME_BUDGET'
            continue
        dest.mkdir()
        with (dest/'stdout.txt').open('w') as stdout, (dest/'stderr.txt').open('w') as stderr:
            child = subprocess.Popen([getattr(sys, '_base_executable', sys.executable), str(worker), '--out', str(dest),
                '--alias', alias, '--start', lo.isoformat(), '--end', hi.isoformat()], env=env,
                stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
            try:
                code = child.wait(timeout=cfg['timeout_per_chunk_seconds'])
                block.update(status='COMPLETED' if code==0 else 'ERROR', returncode=code)
            except subprocess.TimeoutExpired:
                child.kill(); code = child.wait(timeout=5)
                block.update(status='TIMEOUT', returncode=code)
        block['child_pid'] = child.pid
        if block['status'] == 'COMPLETED':
            coverage = read(dest/'coverage.json')
            block.update(status=coverage['status'], count=coverage['count'])
        stop = block['status'] not in ['OBSERVED', 'EMPTY']
        output.write_text(json.dumps(data, indent=2), encoding='utf-8')
        print(alias, hour, block['status'], block.get('count'), flush=True)
data['finished_host_utc'] = datetime.now(timezone.utc).isoformat()
output.write_text(json.dumps(data, indent=2), encoding='utf-8')
print('Collection finished; no orders sent', flush=True)
