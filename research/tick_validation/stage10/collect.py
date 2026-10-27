"""Isolated bounded retries; preserve previous failed evidence unchanged."""
import hashlib, json, os, subprocess, sys, time
from datetime import datetime, timezone
from pathlib import Path
A = Path(__file__).resolve().parent
ROOT = A.parents[2]
config = json.loads((A / 'config.json').read_text())
target = A / 'collection.json'
if target.exists() or (A / 'captures').exists():
    raise SystemExit('Immutable attempt exists')
worker = A.parent / 'stage3/probe.py'
env = dict(os.environ, PYTHONPATH=str(ROOT / '.venv/Lib/site-packages'))
results, stopped = [], False
for index, request in enumerate(config['requests']):
    row = dict(**request)
    if stopped:
        row['process_status'] = 'NOT_ATTEMPTED_AFTER_ERROR'
        results.append(row)
        continue
    path = A / 'captures' / f'{index}-{request["alias"]}'
    path.mkdir(parents=True)
    cmd = [getattr(sys, '_base_executable', sys.executable), str(worker), '--out', str(path),
        '--alias', request['alias'], '--start', request['start'], '--end', request['end']]
    started = time.monotonic()
    with (path / 'stdout.txt').open('w') as so, (path / 'stderr.txt').open('w') as se:
        child = subprocess.Popen(cmd, env=env, stdout=so, stderr=se, creationflags=subprocess.CREATE_NO_WINDOW)
        try:
            code = child.wait(timeout=config['timeout_seconds'])
            status = 'COMPLETED' if code == 0 else 'ERROR'
        except subprocess.TimeoutExpired:
            child.kill()
            code = child.wait(timeout=5)
            status = 'TIMEOUT'
    phases = [json.loads(x) for x in (path / 'phases.jsonl').read_text().splitlines()] if (path / 'phases.jsonl').exists() else []
    row.update(path=path.relative_to(A).as_posix(), process_status=status, child_pid=child.pid,
        returncode=code, elapsed_seconds=time.monotonic()-started, last_phase=phases[-1]['phase'] if phases else None)
    coverage = path / 'coverage.json'
    if coverage.exists():
        row['coverage'] = json.loads(coverage.read_text())
    results.append(row)
    stopped = status != 'COMPLETED' or row.get('coverage', {}).get('status') == 'API_ERROR'
    target.write_text(json.dumps(dict(captured_at=datetime.now(timezone.utc).isoformat(), requests=results,
        worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(), new_orders_sent=0, terminal_restarted=False), indent=2), encoding='utf-8')
    print(request['alias'], status, row.get('coverage', {}).get('count'), flush=True)
target.write_text(json.dumps(dict(captured_at=datetime.now(timezone.utc).isoformat(), requests=results,
    worker_sha256=hashlib.sha256(worker.read_bytes()).hexdigest(), new_orders_sent=0, terminal_restarted=False), indent=2), encoding='utf-8')
