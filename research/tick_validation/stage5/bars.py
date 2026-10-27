"""Raw-coordinate tick aggregation on explicit broker bar boundaries, not UTC inference."""
from bisect import bisect_right
from math import isfinite
from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from model import validate_stream,Unverified

def aggregate(ticks,boundaries):
    previous_end=None
    for start,end in boundaries:
        if type(start) is not int or type(end) is not int or end<=start:raise ValueError('Invalid boundaries')
        if previous_end is not None and start<previous_end:raise ValueError('Overlapping or unordered boundaries')
        previous_end=end
    starts=[start for start,_ in boundaries]
    bars=[dict(start_raw_ms=start,end_raw_ms=end,tick_records=0,last_updates=0,
               first_raw_ms=None,last_raw_ms=None,ohlc={'bid':None,'ask':None,'last':None}) for start,end in boundaries]
    for _,tick in validate_stream(ticks):
        raw=tick['time_msc'];index=bisect_right(starts,raw)-1
        if index<0 or raw>=boundaries[index][1]:continue
        bar=bars[index];bar['tick_records']+=1
        if bar['first_raw_ms'] is None:bar['first_raw_ms']=raw
        bar['last_raw_ms']=raw
        for field in ['bid','ask','last']:
            if field=='last':
                if not tick.get('flags',0)&8:continue
                if not isfinite(tick.get('last',0)) or tick.get('last',0)<=0:
                    raise Unverified('Invalid LAST update: do not silently replace with Bid/Ask')
                bar['last_updates']+=1
            value=tick[field];current=bar['ohlc'][field]
            if current is None:bar['ohlc'][field]=dict(open=value,high=value,low=value,close=value)
            else:current.update(high=max(current['high'],value),low=min(current['low'],value),close=value)
    return bars

def missing_intervals(start,end,successful_ranges):
    """Request coverage only. Successful requests do not certify every historical tick."""
    if end<=start:raise ValueError('Invalid target')
    cursor=start;missing=[]
    for lo,hi in sorted(successful_ranges):
        if hi<=lo:raise ValueError('Invalid covered range')
        lo=max(lo,start);hi=min(hi,end)
        if hi<=lo:continue
        if lo>cursor:missing.append([cursor,lo])
        cursor=max(cursor,hi)
    if cursor<end:missing.append([cursor,end])
    return missing
