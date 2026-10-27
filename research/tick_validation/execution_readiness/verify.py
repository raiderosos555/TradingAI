"""Offline verification and sealing; does not connect to or restart DEMO."""
import hashlib,json,subprocess,sys
from pathlib import Path
A=Path(__file__).resolve().parent;BASE=A.parent;ROOT=A.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
manifest=A/'manifest.json'
if '--seal' in sys.argv:
    assert not manifest.exists(),'Already sealed'
else:
    for item in read(manifest)['files']:
        assert sha(A/item['path'])==item['sha256'],item['path']

# Historical research artifacts remain immutable even though active DEMO has an
# explicitly authorized slot-cap migration. Do not rewrite their old manifests.
for item in read(BASE/'stage11/manifest.json')['files']:
    assert sha(BASE/'stage11'/item['path'])==item['sha256'],item['path']
for item in read(BASE/'stage2/source_manifest.json'):
    assert sha(BASE/'stage2/source_snapshot'/item['path'])==item['sha256'],item['path']
assert read(BASE/'stage2/source_snapshot/config.demo.json')['risk']['max_positions']==2
config=read(A/'config.v1.json')
assert not config['full_historical_replay_permitted'] and config['accepted_historical_UTC_segments']==[]
data=read(A/'analysis.json')
assert data['historical_replay']=='NOT_RUN_PREREQUISITES_UNSATISFIED'
assert not data['quotes_fix_deployed']
for key in ['net','profit_factor','expectancy_R','drawdown','signal_count_delta','entry_count_delta','fill_price_deltas','spread_impact','commission_impact']:
    assert data[key] is None,key
assert [x['count'] for x in data['fx']]==[126629,160216]
assert all(x['count']==200 for x in read(A/'readiness.json')['warmup'])
for item in read(A/'authorized_production_changes.json'):
    assert sha(ROOT/item['path'])==item['after_sha256'], 'Active config/code has changed; inspect migration rather than overwrite evidence'
before=read(ROOT/'state/config-migrations/demo-slots-20261026-validated/config-before.json')
after=read(ROOT/'state/config-migrations/demo-slots-20261026-validated/config-after.json')
assert before['risk']['max_positions']==2 and after['risk']['max_positions']==7
after['risk']['max_positions']=2;assert before==after
run=subprocess.run([sys.executable,'-m','unittest','discover','-s',str(A),'-p','test_*.py','-v'],cwd=ROOT,capture_output=True,text=True,timeout=60)
assert run.returncode==0,run.stdout+run.stderr
assert 'Ran 18 tests' in run.stderr,run.stderr
if '--seal' in sys.argv:
    files=[p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=manifest]
    manifest.write_text(json.dumps(dict(schema_version=1,purpose=config['purpose'],tests=18,
        historical_replay_run=False,decision='NO_GO_HISTORICAL_PERFORMANCE',
        files=[dict(path=p.relative_to(A).as_posix(),sha256=sha(p)) for p in sorted(files)]),indent=2))
print('PASS: 18 tests, immutable stage11/frozen sources, explicit DEMO cap migration, NO-GO preserved')
