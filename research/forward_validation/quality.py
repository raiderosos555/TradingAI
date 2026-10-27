"""Pure validation of raw evidence; never repair quotes or synthesize ticks."""
import hashlib,json,math

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()

def executable(row):
    return all(isinstance(row.get(k),(int,float)) and math.isfinite(row[k]) and row[k]>0 for k in ('bid','ask')) and row['bid']<=row['ask']

def inspect_ticks(rows,start_ms,end_ms,previous_tail=None):
    if not start_ms<end_ms:raise ValueError('Empty request')
    if any(a['time_msc']>b['time_msc'] for a,b in zip(rows,rows[1:])):raise ValueError('Provider chronology regression')
    core=[r for r in rows if start_ms<=r['time_msc']<end_ms]
    overlap=[r for r in rows if start_ms-2000<=r['time_msc']<start_ms]
    overlap_status='NOT_YET_CHECKED' if previous_tail is None else 'MATCH' if overlap==previous_tail else 'MISMATCH'
    last_side={'bid':None,'ask':None};last_tick=None;max_gap=0;invalid=0;trade_only=0;trade_only_invalid=0
    for r in core:
        if last_tick is not None:max_gap=max(max_gap,r['time_msc']-last_tick)
        last_tick=r['time_msc']
        if not executable(r):
            invalid+=1;last_side={'bid':None,'ask':None}
        else:
            for key,flag in [('bid',2),('ask',4)]:
                if r['flags']&flag:last_side[key]=r['time_msc']
        if r['flags']&24 and not r['flags']&6:
            trade_only+=1
            trade_only_invalid+=not executable(r)
    return dict(count=len(core),first_raw_ms=core[0]['time_msc'] if core else None,
        last_raw_ms=core[-1]['time_msc'] if core else None,max_internal_silence_ms=max_gap,
        empty_interval=not core,invalid_quotes=invalid,trade_only_updates=trade_only,
        trade_only_invalid=trade_only_invalid,last_explicit_side_change_raw_ms=last_side,
        side_clock_scope='THIS_CHUNK_ONLY; RAW_TIMESTAMPS; NO_CARRY_FORWARD_EXECUTION',
        overlap_status=overlap_status,core_sha256=digest(core),
        tail=[r for r in core if r['time_msc']>=end_ms-2000],
        completeness_certified=False)

def clock_anchor(raw_ms,before,after,ea_offset):
    """Bracket a recent broker timestamp using receipt time, not price freshness."""
    if after<before or after-before>2:return {'status':'INVALID_HOST_BRACKET'}
    if not isinstance(ea_offset,int) or abs(ea_offset)>14*3600:return {'status':'INVALID_EA_OFFSET'}
    midpoint=(before+after)/2
    candidate=round((raw_ms/1000-midpoint)/900)*900
    age=midpoint-(raw_ms/1000-candidate)
    status='CONSISTENT_CANDIDATE' if candidate==ea_offset and -2<=age<=5 else 'UNCORROBORATED'
    return dict(status=status,candidate_offset_seconds=candidate,ea_offset_seconds=ea_offset,
        raw_ms=raw_ms,host_before_utc_epoch=before,host_after_utc_epoch=after,
        apparent_tick_age_seconds=age,bracket_seconds=after-before,
        historical_mapping_verified=False,quote_executable_not_implied=True)
