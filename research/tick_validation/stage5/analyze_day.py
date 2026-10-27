from pathlib import Path
import json,gzip,hashlib,io,unittest
from bars import aggregate,missing_intervals
import test_bars

A=Path(__file__).resolve().parent;ROOT=A.parents[2]
c=json.loads((A/'collection.json').read_text());ticks=[];ranges=[];blocks=[]
for block in c['blocks']:
    if block['status'] not in {'OBSERVED','EMPTY'}:continue
    path=A/block['path'];coverage=json.loads((path/'coverage.json').read_text())
    with gzip.open(path/'ticks.raw.json.gz','rt',encoding='utf-8') as f:part=json.load(f)
    assert len(part)==coverage['count']
    assert all(block['start_raw_ms']<=t['time_msc']<block['end_raw_ms'] for t in part)
    ticks.extend(part);ranges.append([block['start_raw_ms'],block['end_raw_ms']])
    blocks.append(dict(**block,first_raw_ms=part[0]['time_msc'] if part else None,last_raw_ms=part[-1]['time_msc'] if part else None))
missing=missing_intervals(c['start_raw_ms'],c['end_raw_ms'],ranges)
rows=[]
for tf in ['H1','H4','D1']:
    all_bars=json.loads((A/'inputs'/(tf+'.json')).read_text())['bars']
    assert all(a['broker_raw_time']<b['broker_raw_time'] for a,b in zip(all_bars,all_bars[1:]))
    selected=[(b,n) for b,n in zip(all_bars,all_bars[1:]) if c['start_raw_ms']<=b['broker_raw_time']*1000<c['end_raw_ms']]
    boundaries=[(b['broker_raw_time']*1000,n['broker_raw_time']*1000) for b,n in selected]
    bars=aggregate(ticks,boundaries)
    for computed,(reference,_) in zip(bars,selected):
        errors={field:max(abs(ohlc[k]-reference[k]) for k in ['open','high','low','close']) if ohlc else None for field,ohlc in computed['ohlc'].items()}
        missing_here=missing_intervals(computed['start_raw_ms'],computed['end_raw_ms'],ranges)
        rows.append(dict(timeframe=tf,**computed,reference_ohlc={k:reference[k] for k in ['open','high','low','close']},
                         reference_tick_volume=reference['tick_volume'],max_price_error=errors,
                         last_matches=errors['last'] is not None and errors['last']<1e-10,
                         last_count_matches_tick_volume=computed['last_updates']==reference['tick_volume'],
                         missing_request_ranges=missing_here))
allgaps=[b['time_msc']-a['time_msc'] for a,b in zip(ticks,ticks[1:])]
out=io.StringIO();result=unittest.TextTestRunner(stream=out,verbosity=2).run(unittest.defaultTestLoader.loadTestsFromModule(test_bars))
(A/'tests.txt').write_text(out.getvalue(),encoding='utf-8');assert result.wasSuccessful(),out.getvalue()
data=dict(instrument=c['alias'],time_basis=c['time_basis'],data_class='EXPLORATORY',tick_records=len(ticks),
          first_raw_ms=ticks[0]['time_msc'] if ticks else None,last_raw_ms=ticks[-1]['time_msc'] if ticks else None,
          largest_observed_gap_ms=max(allgaps,default=None),equal_ms_pairs=sum(x==0 for x in allgaps),
          missing_request_ranges=missing,request_coverage_complete=not missing,server_history_completeness_certified=False,
          bars=rows,block_summary=blocks,tests=result.testsRun,tests_passed=result.wasSuccessful(),
          accepted_historical_utc_segments=[],full_backtest_run=False,new_orders_sent=0)
(A/'comparison.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for r in json.loads((A.parent/'inputs/protected_hashes.json').read_text()):assert sha(ROOT/r['path'])==r['sha256']
for r in c['bar_sources']:assert sha(ROOT/r['path'])==sha(A/'inputs'/(r['timeframe']+'.json'))==r['sha256']
assert sha(A.parent/'stage3/probe.py')==c['worker_sha256']
print(json.dumps(dict(ticks=len(ticks),bars=len(rows),last_matches=sum(r['last_matches'] for r in rows),
    counts_match=sum(r['last_count_matches_tick_volume'] for r in rows),tests=result.testsRun,
    missing=missing,maxgap=data['largest_observed_gap_ms'])))
