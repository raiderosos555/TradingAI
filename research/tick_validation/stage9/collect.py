"""Bounded child; terminate only this research worker if MT5 stalls."""
import json, os, subprocess, sys
from pathlib import Path
A = Path(__file__).resolve().parent
ROOT = A.parents[2]
if (A / 'collection.json').exists() or (A / 'capture.json').exists():
    raise SystemExit('Immutable capture exists')
settings = json.loads((A / 'config.json').read_text())
env = dict(os.environ)
env['PYTHONPATH'] = str(ROOT / '.venv/Lib/site-packages')
with (A / 'stdout.txt').open('w') as stdout, (A / 'stderr.txt').open('w') as stderr:
    child = subprocess.Popen([getattr(sys, '_base_executable', sys.executable), str(A / 'probe.py')],
        env=env, stdout=stdout, stderr=stderr, creationflags=subprocess.CREATE_NO_WINDOW)
    try:
        code = child.wait(timeout=settings['timeout_seconds'])
        status = 'COMPLETED' if code == 0 else 'ERROR'
    except subprocess.TimeoutExpired:
        child.kill()
        code = child.wait(timeout=5)
        status = 'TIMEOUT'
result = dict(status=status, pid=child.pid, returncode=code, new_orders_sent=0)
(A / 'collection.json').write_text(json.dumps(result, indent=2))
print(result)
