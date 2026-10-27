"""Verify local artifacts, controls and unchanged active DEMO; no MT5 calls."""
import hashlib,json,subprocess,sys
from pathlib import Path
A=Path(__file__).resolve().parent;BASE=A.parent;ROOT=A.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=A/'manifest.json'
seal='--seal' in sys.argv
if seal:assert not manifest.exists()
else:
    for row in read(manifest)['files']:assert sha(A/row['path'])==row['sha256'],row['path']
for stage in ['stage11','execution_readiness']:
    for row in read(BASE/stage/'manifest.json')['files']:
        assert sha(BASE/stage/row['path'])==row['sha256'],str((stage,row['path']))
for row in read(BASE/'stage2/source_manifest.json'):
    assert sha(BASE/'stage2/source_snapshot'/row['path'])==row['sha256'],row['path']
allowed={row['path']:row['after_sha256'] for row in read(BASE/'execution_readiness/authorized_production_changes.json')}
for row in read(BASE/'inputs/protected_hashes.json'):
    p=Path(row['path']);assert sha(ROOT/p)==allowed.get(p.as_posix(),row['sha256']),str(p)
controls=read(A/'control-results.final.json')
for side,result in controls.items():
    assert result['data_class']=='SYNTHETIC_PORTFOLIO_CONTROL' and not result['historical_performance']
    assert len(result['metrics']['closed_trades'])==2
    assert abs(result['ending_equity']-10025.12)<1e-8
preflight=read(A/'historical-preflight.json')
assert preflight['decision']=='NO_GO_HISTORICAL_REPLAY' and not preflight['historical_replay_run']
assert all(x is None for x in preflight['metrics'].values())
run=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(A),'-p','test_*.py','-v'],cwd=ROOT,capture_output=True,text=True,timeout=60)
assert run.returncode==0,run.stdout+run.stderr
assert 'Ran 23 tests' in run.stderr,run.stderr
if seal:
    (A/'tests.txt').write_text(run.stdout+run.stderr,encoding='utf-8')
    (A/'validation.json').write_text(json.dumps(dict(tests=23,passed=True,production_unchanged_since_authorized_slot_migration=True,
        historical_replay_run=False,decision='GO_CONTROL_CORE_NO_GO_HISTORICAL_PERFORMANCE'),indent=2))
    files=[p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=manifest]
    manifest.write_text(json.dumps(dict(schema_version=1,files=[dict(path=p.relative_to(A).as_posix(),sha256=sha(p)) for p in sorted(files)]),indent=2))
print('PASS: 23 adapter tests; frozen artifacts and active DEMO unchanged; historical NO-GO preserved')
