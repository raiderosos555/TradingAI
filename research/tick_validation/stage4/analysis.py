"""Empirical fills versus raw tick history, without fitting execution parameters."""
from bisect import bisect_right,bisect_left
from datetime import datetime
from pathlib import Path
import gzip,json,math,sys

A=Path(__file__).resolve().parent
sys.path.insert(0,str(A.parent))
from model import validate_stream

def prior_quotes(ticks,raw_ms,max_age_ms=1000):
    # Provider ordering is retained; equal timestamp quotes are an ambiguity set.
    times=[t['time_msc'] for t in ticks]
    if any(a>b for a,b in zip(times,times[1:])):raise ValueError('Chronology regression; do not silently sort')
    right=bisect_right(times,raw_ms)
    if not right:raise ValueError('No past quote; future tick cannot be used as fill')
    stamp=times[right-1]
    if raw_ms-stamp>max_age_ms:raise ValueError('Prior quote too stale')
    left=bisect_left(times,stamp)
    return ticks[left:right],raw_ms-stamp

def price_difference(transaction_type,fill,reference):
    if transaction_type not in (0,1):raise ValueError('Only BUY/SELL transactions')
    return (fill-reference)*(1 if transaction_type==0 else -1)

def offset_interval(raw_execution_ms,intent,confirmed):
    lo=datetime.fromisoformat(intent).timestamp()*1000
    hi=datetime.fromisoformat(confirmed).timestamp()*1000
    if hi<lo:raise ValueError('Host event order invalid')
    # Conditional on timestamp referring to execution within intent/confirmation.
    return [raw_execution_ms-hi,raw_execution_ms-lo]

def analyze():
    report=json.loads((A/'inputs/broker-report.json').read_text())
    source=report['broker_snapshot'];assert source['account']['trade_mode']==0 and source['account']['currency']=='PLN'
    operations={o['result']['deal']:o for o in report['operations'] if o.get('result',{}).get('deal')}
    confirmations={e['payload']['id']:e['at'] for e in report['audit_events'] if e['kind']=='confirmed'}
    ticks=[];ranges=[]
    for p in sorted((A/'inputs').glob('ticks-*')):
        c=json.loads((p/'coverage.json').read_text());assert c['status']=='OBSERVED'
        with gzip.open(p/'ticks.raw.json.gz','rt',encoding='utf-8') as f:part=json.load(f)
        ticks.extend(part);ranges.append([c['requested_start_raw_ms'],c['requested_end_raw_ms']])
    assert len(list(validate_stream(ticks)))==len(ticks)
    rows=[]
    for deal in source['deals']:
        op=operations[deal['ticket']];payload=op['payload'];request=payload['request'];meta=payload['metadata'];result=op['result']
        assert op['status']=='CONFIRMED' and result['order']==deal['order'] and request['type']==deal['type']
        assert math.isclose(request['volume'],deal['volume']) and math.isclose(result['price'],deal['price'])
        ms=deal['broker_raw_time_msc'];assert any(lo<=ms<hi for lo,hi in ranges)
        quote_group,age=prior_quotes(ticks,ms)
        field='ask' if deal['type']==0 else 'bid'
        prices=sorted({t[field] for t in quote_group})
        matches=any(math.isclose(deal['price'],p,abs_tol=1e-8) for p in prices)
        reference=meta['entry_reference']
        interval=offset_interval(ms,op['at'],confirmations[op['id']])
        rows.append(dict(deal=deal['ticket'],order=deal['order'],position_id=deal['position_id'],rule=payload['rule'],
                         entry=deal['entry'],transaction='BUY' if deal['type']==0 else 'SELL',volume=deal['volume'],
                         raw_execution_ms=ms,host_intent=op['at'],host_confirmation=confirmations[op['id']],
                         fill=deal['price'],preflight_reference=reference,
                         adverse_price_difference=round(price_difference(deal['type'],deal['price'],reference),8),
                         broker_result_quote=result.get(field),quote_side=field,prior_quote_age_ms=age,
                         prior_quote_same_ms_count=len(quote_group),prior_executable_prices=prices,
                         quote_price_unambiguous=len(prices)==1,fill_matches_prior_quote=matches,
                         prior_quotes=quote_group,raw_minus_host_interval_ms=interval,
                         host_intent_confirmation_ms=(datetime.fromisoformat(confirmations[op['id']])-datetime.fromisoformat(op['at'])).total_seconds()*1000,
                         cash={k:deal[k] for k in ['profit','commission','swap','fee']}))
    positions=[]
    for pid in sorted({r['position_id'] for r in rows}):
        ds=[d for d in source['deals'] if d['position_id']==pid]
        opened=sum(d['volume'] for d in ds if d['entry']==0);closed=sum(d['volume'] for d in ds if d['entry']==1)
        assert math.isclose(opened,closed)
        positions.append(dict(position_id=pid,volume_opened=opened,volume_closed=closed,
                              opening_deals=sum(d['entry']==0 for d in ds),closing_deals=sum(d['entry']==1 for d in ds),
                              realized_net_PLN=round(sum(sum(d[k] for k in ['profit','commission','swap','fee']) for d in ds),2)))
    intersection=[max(r['raw_minus_host_interval_ms'][0] for r in rows),min(r['raw_minus_host_interval_ms'][1] for r in rows)]
    totals={k:round(sum(r['cash'][k] for r in rows),2) for k in ['profit','commission','swap','fee']}
    data=dict(stage='EMPIRICAL_EXECUTION_SAMPLES',data_class='EXPLORATORY_OPERATOR_TESTS_NOT_STRATEGY',
              raw_ticks=len(ticks),raw_ranges=ranges,fills=rows,positions=positions,cash_totals_PLN=totals,
              realized_net_PLN=round(sum(totals.values()),2),
              conditional_constant_clock_delta_intersection_ms=intersection,
              accepted_historical_utc_segments=[],calibrated_latency_model=False,
              calibrated_slippage_model=False,full_backtest_run=False,new_orders_sent=0,
              historical_fx_independently_verified=False)
    (A/'comparison.json').write_text(json.dumps(data,indent=2),encoding='utf-8')
    print(json.dumps(dict(raw_ticks=len(ticks),fills=len(rows),matched=sum(r['fill_matches_prior_quote'] for r in rows),
         adverse_differences=[r['adverse_price_difference'] for r in rows],net_PLN=data['realized_net_PLN'],
         clock_delta_interval_ms=intersection)))
    return data

if __name__=='__main__':analyze()
