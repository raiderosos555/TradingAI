"""Read-only migration checks; lock probes do not remove locks or send orders."""
import argparse,json,hashlib,sys
from contextlib import ExitStack
from pathlib import Path
from supervisor import load,lock
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
p=argparse.ArgumentParser();p.add_argument('--locks-free',action='store_true');p.add_argument('--preflight',action='store_true');a=p.parse_args()
c=load(A/'deployment/supervise.json')
protected=json.loads((A/'protected-before.json').read_text())
for rel,h in protected.items():
    if hashlib.sha256((ROOT/rel).read_bytes()).hexdigest()!=h:raise RuntimeError('Protected source/config changed; refresh migration review')
if a.locks_free:
    with ExitStack() as stack:
        for d in c['engine_locks']:stack.enter_context(lock(d))
        stack.enter_context(lock(Path(c['home'])/'owner'))
if a.preflight:
    from datetime import datetime,timezone
    from readiness_probe import run
    out=A/'evidence'/('migration-preflight-'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'.json')
    run(out);d=json.loads(out.read_text())
    if not d['connected'] or not d['all_positions_have_broker_sl_tp'] or d['live_enabled']:raise RuntimeError('Broker/account protection gate failed')
    if d['collector']['status']!='COLLECTING':raise RuntimeError('Collector not healthy; do not migrate')
    # Existing quarantine is preserved, never a reason to auto-clear or resend.
    print('Existing uncertain operations retained:',d['uncertain_operations'])
print('PASS')
