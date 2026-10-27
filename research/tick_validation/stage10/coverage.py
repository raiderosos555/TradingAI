"""Raw-coordinate coverage and lossless overlap checks; no fabricated ticks."""
import hashlib, json, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from research.tick_validation.model import validate_stream

FIELDS = ('time', 'time_msc', 'bid', 'ask', 'last', 'volume', 'flags', 'volume_real')

def intervals_union(ranges):
    merged = []
    for lo, hi in sorted(ranges):
        if type(lo) is not int or type(hi) is not int or lo >= hi:
            raise ValueError('Invalid half-open interval')
        if merged and lo <= merged[-1][1]:
            merged[-1][1] = max(hi, merged[-1][1])
        else:
            merged.append([lo, hi])
    return merged

def raw_groups(rows, lo, hi):
    groups, count, current, values = {}, 0, None, []
    def store():
        if current is not None:
            encoded = json.dumps(values, separators=(',', ':'), allow_nan=False).encode()
            groups[current] = dict(count=len(values), sha256=hashlib.sha256(encoded).hexdigest())
    def raw_rows():
        for row in rows:
            # Legacy normalized columns cannot be used when original broker columns exist.
            if ('broker_raw_time_msc' in row) != ('broker_raw_time' in row):
                raise ValueError('Incomplete raw timestamp provenance')
            if 'broker_raw_time_msc' in row:
                row = dict(row, time=row['broker_raw_time'], time_msc=row['broker_raw_time_msc'])
            yield row
    for _, row in validate_stream(raw_rows()):
        ms = row['time_msc']
        if not lo <= ms < hi or row['time'] != ms // 1000:
            raise ValueError('Timestamp outside request or inconsistent seconds')
        if current != ms:
            store()
            current, values = ms, []
        # Provider ordering and identical repeated rows within one millisecond are retained.
        values.append([row[key] for key in FIELDS])
        count += 1
    store()
    return groups, count

def combine(captures):
    union, conflicts, overlap_pairs, prior = {}, [], 0, []
    total = 0
    for capture in captures:
        lo, hi = capture['start_raw_ms'], capture['end_raw_ms']
        groups = capture['groups']
        total += capture['count']
        for previous in prior:
            lower, upper = max(lo, previous['start_raw_ms']), min(hi, previous['end_raw_ms'])
            if lower >= upper:
                continue
            overlap_pairs += 1
            left = {t:g for t,g in previous['groups'].items() if lower <= t < upper}
            right = {t:g for t,g in groups.items() if lower <= t < upper}
            differing = [t for t in left.keys() | right.keys() if left.get(t) != right.get(t)]
            if differing:
                conflicts.append(dict(source_a=previous['source'], source_b=capture['source'],
                    overlap_raw_ms=[lower, upper], differing_timestamp_groups=len(differing),
                    first_differing_raw_ms=min(differing)))
        for timestamp, group in groups.items():
            if timestamp not in union:
                union[timestamp] = group
        prior.append(capture)
    ranges = intervals_union([[c['start_raw_ms'], c['end_raw_ms']] for c in captures])
    unique = sum(g['count'] for g in union.values()) if not conflicts else None
    return dict(captures=len(captures), downloaded_records=total, consistent_unique_records=unique,
        repeated_records_across_captures=total-unique if unique is not None else None,
        checked_overlap_pairs=overlap_pairs, overlap_conflicts=conflicts, successful_request_ranges_raw_ms=ranges,
        requested_duration_ms=sum(hi-lo for lo,hi in ranges),
        first_observed_raw_ms=min(union) if union else None, last_observed_raw_ms=max(union) if union else None,
        same_ms_additional_records=sum(g['count']-1 for g in union.values()) if not conflicts else None,
        continuous_server_history_certified=False, historical_UTC_verified=False)
