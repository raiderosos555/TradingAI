"""Offline prerequisites and observations; never substitutes missing replay evidence."""
import json,hashlib
from pathlib import Path
A=Path(__file__).resolve().parent;BASE=A.parent;ROOT=A.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
start=1792627200
warm=[]
for alias in ['EURPLN','EURUSD','GBPUSD','GOLD','OIL','US100','US500']:
    source=ROOT/'exchange/research/history-20261024'/(alias+'.json')
    bars=[b for b in read(source)['bars'] if b['broker_raw_time']+3600<=start][-200:]
    assert len(bars)==200 and all(a['broker_raw_time']<b['broker_raw_time'] for a,b in zip(bars,bars[1:]))
    target=A/(alias+'-warmup.json');target.write_text(json.dumps(dict(time_basis='RAW_UTC_UNVERIFIED',bars=bars),indent=2))
    warm.append(dict(alias=alias,count=len(bars),source=source.relative_to(ROOT).as_posix(),source_sha256=sha(source),sha256=sha(target)))
obs=read(A/'observations.json');summary=[]
for alias in ['US500','US100','OIL']:
    rows=[r for r in obs['rows'] if r['alias']==alias]
    bad=[r for r in rows if r['before']['bid']<=0 or r['before']['ask']<=0]
    summary.append(dict(alias=alias,samples=len(rows),invalid=len(bad),invalid_flags=[r['before']['flags'] for r in bad]))
changes=read(A/'authorized_production_changes.json')
allowed={p['path']:p for p in changes}
for p in read(BASE/'inputs/protected_hashes.json'):
    actual=sha(ROOT/p['path']);key=Path(p['path']).as_posix()
    if actual!=p['sha256']:
        assert key in allowed and actual==allowed[key]['after_sha256'] and p['sha256']==allowed[key]['before_sha256']
result=dict(warmup=warm,observations=summary,production_unchanged=False,
    authorized_production_changes=changes,research_modified_quote_logic_in_demo=False,orders_sent=0,
    gate='NO_GO',integrated_replay_run=False,old_new_profit_comparison=None,
    blockers=['UTC mapping for 2026-10-22 not evidenced','Historical contract/fees and execution-time FX policy unconfirmed',
        'Point-in-time calendar required by frozen Risk Manager missing','Historical integrated portfolio replay not completed; only synthetic four-engine controls passed',
        'Global inter-symbol order for equal-millisecond events not supplied by per-symbol tick history'],
    fx_collection='fx-collection.json',
    frozen_source_manifest_sha256=sha(BASE/'stage2/source_manifest.json'))
(A/'readiness.json').write_text(json.dumps(result,indent=2))
print(summary);print('7 x 200 closed H1 warmup bars prepared; economic replay NO-GO')
