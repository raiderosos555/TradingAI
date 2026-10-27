"""Diagnostic aggregation only. Invalid quotes remain in chronology and cannot execute."""
from bisect import bisect_right
from math import isfinite

def positive(value):
    return isinstance(value,(int,float)) and not isinstance(value,bool) and isfinite(value) and value>0

def quote_error(tick):
    if not positive(tick.get('bid')) or not positive(tick.get('ask')): return 'MISSING_OR_NONPOSITIVE_QUOTE'
    if tick['bid']>tick['ask']: return 'CROSSED_QUOTE'
    return None

def quote_health(ticks):
    records,intervals=[],[]
    active=None
    for index,tick in enumerate(ticks):
        error=quote_error(tick)
        if error:
            records.append(dict(provider_index=index,reason=error,tick=tick))
            if active is None: active=dict(start_provider_index=index,start_raw_ms=tick['time_msc'])
        elif active is not None:
            intervals.append(dict(**active,end_provider_index=index,end_raw_ms=tick['time_msc'],recovered=True))
            active=None
    if active is not None: intervals.append(dict(**active,end_provider_index=None,end_raw_ms=None,recovered=False))
    return dict(invalid_quote_records=records,unavailable_intervals=intervals)

def aggregate(ticks,boundaries):
    starts=[a for a,b in boundaries]
    if any(b<=a or (i and a<boundaries[i-1][1]) for i,(a,b) in enumerate(boundaries)):
        raise ValueError('Unordered or overlapping boundaries')
    bars=[dict(start_raw_ms=a,end_raw_ms=b,tick_records=0,last_updates=0,invalid_quote_records=0,
        invalid_last_updates=0,first_raw_ms=None,last_raw_ms=None,ohlc={'bid':None,'ask':None,'last':None}) for a,b in boundaries]
    previous=None
    for tick in ticks:
        raw=tick['time_msc']
        if type(raw) is not int or previous is not None and raw<previous: raise ValueError('Invalid tick chronology')
        previous=raw
        index=bisect_right(starts,raw)-1
        if index<0 or raw>=boundaries[index][1]: continue
        bar=bars[index];bar['tick_records']+=1
        if bar['first_raw_ms'] is None:bar['first_raw_ms']=raw
        bar['last_raw_ms']=raw
        valid_quote=quote_error(tick) is None
        if not valid_quote:bar['invalid_quote_records']+=1
        for field in ['bid','ask','last']:
            if field=='last':
                if not tick.get('flags',0)&8:continue
                bar['last_updates']+=1
                if not positive(tick.get('last')):
                    bar['invalid_last_updates']+=1
                    continue
            elif not valid_quote:continue
            value=tick[field];current=bar['ohlc'][field]
            if current is None:bar['ohlc'][field]=dict(open=value,high=value,low=value,close=value)
            else:current.update(high=max(current['high'],value),low=min(current['low'],value),close=value)
    return bars
