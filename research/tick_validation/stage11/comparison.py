"""Compare explicit raw-coordinate slots, including absent chart bars, without bridging gaps."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from research.tick_validation.stage5.bars import missing_intervals
from quality import aggregate

DURATIONS = {'H1': 3600000, 'H4': 14400000, 'D1': 86400000}

def compare(ticks, references, timeframe, start, end, successful_ranges):
    duration = DURATIONS[timeframe]
    if end <= start or (end-start) % duration:
        raise ValueError('Target does not contain complete raw slots')
    boundaries = [(lo, lo+duration) for lo in range(start, end, duration)]
    selected = {}
    previous = None
    for ref in references:
        raw = ref['broker_raw_time']*1000
        if previous is not None and raw <= previous:
            raise ValueError('Reference bars are duplicated or not chronological')
        previous = raw
        if start <= raw < end:
            if (raw-start) % duration:
                raise ValueError('Reference boundary differs from declared raw grid')
            selected[raw] = ref
    output = []
    for bar in aggregate(ticks, boundaries):
        ref = selected.get(bar['start_raw_ms'])
        missing = missing_intervals(bar['start_raw_ms'], bar['end_raw_ms'], successful_ranges)
        errors = {basis: max(abs(ohlc[k]-ref[k]) for k in ['open','high','low','close'])
            if ref is not None and ohlc is not None else None for basis,ohlc in bar['ohlc'].items()}
        matches = errors['last'] is not None and errors['last'] < 1e-10
        count_matches = ref is not None and bar['last_updates'] == ref['tick_volume']
        if missing:
            status = 'INCOMPLETE_REQUEST_COVERAGE'
        elif bar['invalid_last_updates']:
            status = 'INVALID_LAST_UPDATES'
        elif ref is None:
            status = 'REFERENCE_ABSENT_NO_LAST' if bar['last_updates'] == 0 else 'REFERENCE_MISSING_WITH_LAST'
        else:
            status = 'MATCH' if matches and count_matches else 'MISMATCH'
        if status=='MATCH' and bar['invalid_quote_records']:
            status='MATCH_LAST_WITH_INVALID_QUOTES'
        output.append(dict(timeframe=timeframe, **bar, status=status, missing_request_ranges=missing,
            bid_ask_ohlc_complete=not missing and bar['invalid_quote_records']==0,
            reference_ohlc={k:ref[k] for k in ['open','high','low','close']} if ref else None,
            reference_tick_volume=ref['tick_volume'] if ref else None, max_price_error=errors,
            last_matches=matches, last_count_matches_tick_volume=count_matches))
    return output
