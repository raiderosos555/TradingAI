"""Offline day/price validation; no strategy calls, no UTC offset or order API."""
import gzip, hashlib, heapq, json, sys
from collections import Counter
from pathlib import Path
from comparison import compare
from quality import quote_health,quote_error
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from research.tick_validation.stage5.bars import missing_intervals

A = Path(__file__).resolve().parent
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def build(verbose=False):
    collection = read(A/'resolved_collection.json')
    if 'retry_finished_host_utc' not in collection: raise ValueError('Collection still running')
    prior = read(A.parent/'stage5/collection.json')
    instruments = [(A, i) for i in collection['instruments']] + [(A.parent/'stage5', prior)]
    summaries, evidence = [], []
    for base, instrument in instruments:
        alias = instrument['alias']
        if verbose: print('Analyzing', alias, flush=True)
        ticks, ranges, blocks = [], [], []
        for block in instrument['blocks']:
            if block['status'] not in ['OBSERVED','EMPTY']: continue
            path = base/block['path']
            coverage = read(path/'coverage.json')
            source = path/'ticks.raw.json.gz'
            with gzip.open(source, 'rt', encoding='utf-8') as f: part = json.load(f)
            lo, hi = block['start_raw_ms'], block['end_raw_ms']
            if len(part) != coverage['count'] or any(not lo<=t['time_msc']<hi for t in part):
                raise ValueError('Capture count or interval mismatch')
            ticks.extend(part); ranges.append([lo, hi])
            evidence.extend([dict(path=p.relative_to(A.parent).as_posix(),sha256=sha(p)) for p in [source,path/'coverage.json']])
            blocks.append(dict(**block, first_raw_ms=part[0]['time_msc'] if part else None, last_raw_ms=part[-1]['time_msc'] if part else None))
        rows = []
        for tf in ['H1','H4','D1']:
            # Stage 5 keeps reference files directly under inputs; stage 11 separates aliases.
            source = base/'inputs'/(alias if base==A else '')/(tf+'.json')
            refs = read(source)['bars']
            evidence.append(dict(path=source.relative_to(A.parent).as_posix(),sha256=sha(source)))
            rows.extend(compare(ticks, refs, tf, collection['start_raw_ms'], collection['end_raw_ms'], ranges))
        gaps = heapq.nlargest(10,((b['time_msc']-a['time_msc'],a['time_msc'],b['time_msc']) for a,b in zip(ticks,ticks[1:])))
        health=quote_health(ticks)
        spreads = [t['ask']-t['bid'] for t in ticks if quote_error(t) is None]
        previous_source=A.parent/'evidence'/f'basis-{alias}-20261022T1300.json.gz'
        with gzip.open(previous_source,'rt',encoding='utf-8') as f: previous=json.load(f)
        fields=['time','time_msc','bid','ask','last','volume','flags','volume_real']
        old=[[t['broker_raw_time'],t['broker_raw_time_msc'],*(t[k] for k in fields[2:])] for t in previous]
        hour_start=collection['start_raw_ms']+15*3600000
        current=[[t[k] for k in fields] for t in ticks if hour_start<=t['time_msc']<hour_start+3600000]
        evidence.append(dict(path=previous_source.relative_to(A.parent).as_posix(),sha256=sha(previous_source)))
        hour_coverage=missing_intervals(hour_start,hour_start+3600000,ranges)
        overlap=dict(prior_records=len(old),current_records=len(current),request_coverage_complete=not hour_coverage,
            exact_provider_sequence_matches=old==current if not hour_coverage else None)
        summary = dict(alias=alias, tick_records=len(ticks), ranges=ranges,
            missing_request_ranges=missing_intervals(collection['start_raw_ms'],collection['end_raw_ms'],ranges),
            first_raw_ms=ticks[0]['time_msc'] if ticks else None, last_raw_ms=ticks[-1]['time_msc'] if ticks else None,
            largest_observed_gaps=[dict(duration_ms=d,start_raw_ms=lo,end_raw_ms=hi) for d,lo,hi in gaps],
            spread_min_price=min(spreads,default=None),spread_max_price=max(spreads,default=None),
            statuses=dict(Counter(r['status'] for r in rows)), bars=rows, blocks=blocks,
            previous_hour_overlap=overlap,
            quote_health=health,
            session_schedule_verified=False, server_history_complete_certified=False)
        summaries.append(summary)
        if verbose: print(alias,len(ticks),summary['statuses'],flush=True)
    return dict(schema_version=1, config_sha256=sha(A/'config.json'), collection_sha256=sha(A/'resolved_collection.json'),
        previous_EURUSD_collection_sha256=sha(A.parent/'stage5/collection.json'), data_class='EXPLORATORY',
        time_basis=collection['time_basis'], instruments=summaries, source_hashes=evidence,
        tick_records=sum(s['tick_records'] for s in summaries),
        status_counts=dict(Counter(row['status'] for s in summaries for row in s['bars'])),
        full_backtest_run=False, strategy_parameters_changed=False,new_orders_sent=0,
        accepted_historical_UTC_segments=[], historical_cost_policy_approved=False)

if __name__ == '__main__':
    result = build(verbose=True)
    (A/'comparison.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('TOTAL',result['tick_records'],result['status_counts'],flush=True)
