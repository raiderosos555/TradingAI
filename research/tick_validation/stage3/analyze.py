"""Summarize actual raw samples; never infer continuous coverage or UTC mapping."""
from pathlib import Path
import gzip,json,hashlib,sys,math
A=Path(__file__).resolve().parent
sys.path.insert(0,str(A.parent))
from model import validate_stream,execution_price
rows=[]
for out in sorted((A/'captures').iterdir()):
    if not (out/'result.json').exists():continue
    run=json.loads((out/'result.json').read_text());phases=[json.loads(x) for x in (out/'phases.jsonl').read_text().splitlines()]
    byphase={p['phase']:p for p in phases}
    row=dict(capture=out.name,**run['args'],process_status=run['status'],last_phase=run['last_phase'])
    for key in ['INITIALIZE','TICKS']:
        row[key.lower()+'_seconds']=byphase[key+'_DONE']['monotonic']-byphase[key+'_START']['monotonic'] if key+'_DONE' in byphase else None
    if (out/'coverage.json').exists():
        c=json.loads((out/'coverage.json').read_text());row.update(c)
        with gzip.open(out/'ticks.raw.json.gz','rt',encoding='utf-8') as f:ticks=json.load(f)
        validated=list(validate_stream(ticks));assert len(validated)==c['count']
        assert all(c['requested_start_raw_ms']<=t['time_msc']<c['requested_end_raw_ms'] for t in ticks)
        row['invalid_quotes']=0
        row['inversions']=0
        row['same_ms_pairs']=sum(a['time_msc']==b['time_msc'] for a,b in zip(ticks,ticks[1:]))
        row['max_internal_gap_ms']=max((b['time_msc']-a['time_msc'] for a,b in zip(ticks,ticks[1:])),default=None)
        info=json.loads((out/'symbol_now.json').read_text());row['current_chart_mode']=info['chart_mode']
        spreads=sorted((t['ask']-t['bid'])/info['point'] for t in ticks)
        row['spread_median_points']=spreads[len(spreads)//2] if spreads else None
        row['spread_p95_points']=spreads[min(len(spreads)-1,math.ceil(len(spreads)*.95)-1)] if spreads else None
        for t in ticks:
            assert execution_price('BUY','OPEN',t)==execution_price('SELL','CLOSE',t)==t['ask']
            assert execution_price('SELL','OPEN',t)==execution_price('BUY','CLOSE',t)==t['bid']
        if c['alias']=='GOLD' and run['args']['start']=='2026-10-22T15:00:00+00:00':
            with gzip.open(A.parent/'evidence/basis-GOLD-20261022T1300.json.gz','rt',encoding='utf-8') as f:old=json.load(f)
            # Prior capture may store a wrapper; inspect explicitly instead of assuming its basis.
            old=old['ticks'] if isinstance(old,dict) else old
            normalized=[]
            for t in old:
                raw=t.get('broker_raw_time_msc')
                if raw is not None and c['requested_start_raw_ms']<=raw<c['requested_end_raw_ms']:
                    normalized.append({k:t['broker_raw_'+k] if k in {'time','time_msc'} else t[k] for k in ticks[0]})
            row['repeat_old_count']=len(normalized)
            row['exact_same_sequence_as_prior_capture']=normalized==ticks
    else:row.update(count=None,status=run['status'])
    rows.append(row)
summary=dict(data_class='EXPLORATORY',samples=rows,total_downloaded_tick_records=sum(r.get('count') or 0 for r in rows),
             all_sample_quotes_valid=all(r.get('invalid_quotes',0)==0 for r in rows),
             continuous_history_certified=False,accepted_historical_utc_segments=[],full_backtest_run=False,orders_sent=0)
(A/'availability.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps(dict(captures=len(rows),total_records=summary['total_downloaded_tick_records'],
                     rows=[(r['alias'],r['start'][:10],r['status'],r.get('count'),r.get('exact_same_sequence_as_prior_capture')) for r in rows])))
