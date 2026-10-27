"""Local evidence summary. No broker calls, model calls or inferred UTC schedule."""
import collections,gzip,hashlib,json,sqlite3
from pathlib import Path
from datetime import datetime,timezone
A=Path(__file__).resolve().parent;BASE=A.parent;ROOT=A.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
obs=read(A/'observations.json');quotes=[]
for alias in ['US500','US100','OIL']:
    rows=[r for r in obs['rows'] if r['alias']==alias];bad=[];latest_updates=[]
    for r in rows:
        history=r['history'];before=r['before']
        updates={}
        for name,flag in [('bid',2),('ask',4),('last',8),('volume',16)]:
            values=[t for t in history if t['flags']&flag]
            updates[name]=None if not values else dict(value=values[-1][name],time_msc=values[-1]['time_msc'],flags=values[-1]['flags'])
        latest_updates.append(dict(sample=r['sample'],host_utc=r['host_utc'],before_raw_ms=before['time_msc'],
            history_end_raw_ms=history[-1]['time_msc'] if history else None,updates=updates,
            continuity_proven=False,executable_fallback=None))
        if before['bid']<=0 or before['ask']<=0:
            bad.append(dict(sample=r['sample'],host_utc=r['host_utc'],before=before,after=r['after'],info=r['info'],
                preceding_updates=updates))
    quotes.append(dict(alias=alias,samples=len(rows),invalid=len(bad),invalid_examples=bad,side_timestamp_evidence=latest_updates))
fx=[]
for symbol in ['USDPLN','USDPLN.pro']:
    count=invalid=0;first=last=None;max_gap=0;flags=collections.Counter()
    for b in read(A/'fx-collection.json')['attempts']:
        if b['symbol']!=symbol:continue
        assert b['status']=='OBSERVED'
        path=A/b['path']/'ticks.raw.json.gz';assert sha(path)==b['sha256']
        with gzip.open(path,'rt',encoding='utf-8') as f:rows=json.load(f)
        assert len(rows)==b['count']
        for t in rows:
            ms=t['time_msc'];assert last is None or ms>=last
            if first is None:first=ms
            if last is not None:max_gap=max(max_gap,ms-last)
            last=ms;count+=1;flags[t['flags']]+=1
            invalid+=not(0<t['bid']<=t['ask'])
    fx.append(dict(symbol=symbol,count=count,first_raw_ms=first,last_raw_ms=last,invalid_quotes=invalid,
        maximum_observed_intertick_gap_ms=max_gap,flags=dict(flags),
        certified_complete=False,maximum_gap_is_not_proof_of_missing_data=True,utc_verified=False))
health=read(A/'demo_health_latest.json')
sample_summaries=[]
for s in health['samples']:
    bad={a:q for a,q in s['quotes'].items() if not q['raw'] or not 0<q['raw']['bid']<=q['raw']['ask']}
    sample_summaries.append(dict(at=s['at_host_utc'],engine=s['engine_status']['status'],
        invalid_aliases=list(bad),positions=len(s['positions']),orders=len(s['orders']),
        all_positions_have_sl_tp=all(p['sl']>0 and p['tp']>0 for p in s['positions'])))
changes=[]
for old in read(BASE/'inputs/protected_hashes.json'):
    actual=sha(ROOT/old['path'])
    if actual!=old['sha256']:changes.append(dict(path=Path(old['path']).as_posix(),before_sha256=old['sha256'],after_sha256=actual))
assert {c['path'] for c in changes}=={'config.demo.json','trading_ai/models.py'}
frozen=[]
for item in read(BASE/'stage2/source_manifest.json'):
    assert sha(BASE/'stage2/source_snapshot'/item['path'])==item['sha256']
    frozen.append(item)
evidence_path=A/'journal-evidence.json'
if not evidence_path.exists():
    cutoff=health['samples'][-1]['at_host_utc']
    with sqlite3.connect((ROOT/'state/journal.sqlite3').resolve().as_uri()+'?mode=ro',uri=True) as db:
        migration_events=[dict(at=a,kind=k,payload=json.loads(p)) for a,k,p in db.execute(
            "SELECT at,kind,payload FROM events WHERE kind LIKE 'operator_config_migration%' AND at<=? ORDER BY seq",(cutoff,))]
        active_reasons=[dict(reason=r,count=n,first=a,last=b) for r,n,a,b in db.execute(
            "SELECT json_extract(payload,'$.reason'),count(*),min(at),max(at) FROM events WHERE kind='management_decision' AND at>=? AND at<=? GROUP BY json_extract(payload,'$.reason')",('2026-10-26T08:10:00+00:00',cutoff))]
    evidence_path.write_text(json.dumps(dict(cutoff=cutoff,migration_events=migration_events,active_reasons=active_reasons),indent=2))
evidence=read(evidence_path)
migration_events=evidence['migration_events'];active_reasons=evidence['active_reasons']
calendar_candidates=[]
for path in [BASE/'inputs/ea-calendar_123456789.json',ROOT/'exchange/economic-calendar.json']:
    d=read(path)
    calendar_candidates.append(dict(path=path.relative_to(ROOT).as_posix(),sha256=sha(path),
        retrieved_at_utc=d.get('retrieved_at_utc'),status=d.get('status'),
        available_on_Oct22=False))
result=dict(evidence_cutoff=evidence['cutoff'],quote_evidence=quotes,fx=fx,
    demo_samples=sample_summaries,unresolved_operations=health['unresolved_operations'],
    post_restart_management_reasons=active_reasons,approved_production_changes=changes,
    frozen_source_files_verified=len(frozen),calendar_candidates=calendar_candidates,
    migration_events=migration_events,quotes_fix_deployed=False,
    historical_replay='NOT_RUN_PREREQUISITES_UNSATISFIED',
    net=None,profit_factor=None,expectancy_R=None,drawdown=None,
    signal_count_delta=None,entry_count_delta=None,fill_price_deltas=None,
    spread_impact=None,commission_impact=None,
    decision='NO_GO_HISTORICAL_PERFORMANCE_AND_EDGE',
    technical_integration='GO_SYNTHETIC_CONTROLS_ONLY',all_seen_data='EXPLORATORY')
(A/'analysis.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
(A/'authorized_production_changes.json').write_text(json.dumps(changes,indent=2))
print(json.dumps(dict(fx=fx,demo_samples=sample_summaries,post_restart_management_reasons=active_reasons,changes=changes),indent=2))
