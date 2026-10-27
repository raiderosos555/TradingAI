"""Reconcile all frozen real tick captures without assuming a continuous history."""
import gzip, hashlib, json
from collections import defaultdict
from pathlib import Path
from coverage import raw_groups, combine

A = Path(__file__).resolve().parent
BASE = A.parent
ROOT = A.parents[2]
read = lambda p: json.loads(p.read_text(encoding='utf-8'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def build():
    contracts = read(BASE / 'stage9/capture.json')['instruments']
    names = {s['alias']:s['symbol'] for s in contracts}
    specifications = []
    metadata = {}
    def meta(path):
        metadata[path.relative_to(BASE).as_posix()] = sha(path)
    meta(BASE / 'stage9/capture.json')
    meta(BASE / 'price_checks.json')
    for item in read(BASE / 'price_checks.json'):
        specifications.append(dict(source=item['source_file'].replace('\\', '/'), symbol=names[item['instrument']],
            start_raw_ms=item['raw_start_ms'], end_raw_ms=item['raw_end_ms'], expected_count=item['ticks'], status='OBSERVED'))
    patterns = ['stage3/captures/*/coverage.json', 'stage4/inputs/ticks-*/coverage.json',
        'stage5/inputs/raw-*/coverage.json', 'stage8/inputs/fx-*/coverage.json', 'stage10/captures/*/coverage.json']
    for pattern in patterns:
        for path in sorted(BASE.glob(pattern)):
            item = read(path)
            meta(path)
            if item['status'] not in ['OBSERVED', 'EMPTY']:
                continue
            file = path.parent / ('ticks.json.gz' if path.parts[-4] == 'stage8' else 'ticks.raw.json.gz')
            specifications.append(dict(source=file.relative_to(BASE).as_posix(), symbol=item['symbol'],
                start_raw_ms=item.get('requested_start_raw_ms', item.get('start_raw_ms')),
                end_raw_ms=item.get('requested_end_raw_ms', item.get('end_raw_ms')),
                expected_count=item['count'], status=item['status']))
    grouped, sources = defaultdict(list), []
    for spec in specifications:
        path = BASE / spec['source']
        with gzip.open(path, 'rt', encoding='utf-8') as stream:
            rows = json.load(stream)
        groups, count = raw_groups(rows, spec['start_raw_ms'], spec['end_raw_ms'])
        if count != spec['expected_count']:
            raise ValueError('Capture count mismatch: ' + spec['source'])
        if (spec['status'] == 'EMPTY') != (count == 0):
            raise ValueError('Capture status contradicts records: ' + spec['source'])
        grouped[spec['symbol']].append(dict(**spec, count=count, groups=groups))
        sources.append(dict(**spec, sha256=sha(path), unique_timestamp_groups=len(groups)))
    summaries = [dict(symbol=symbol, **combine(captures)) for symbol, captures in sorted(grouped.items())]
    meta(BASE / 'stage3/availability.json')
    meta(A / 'collection.json')
    earlier = [s for s in read(BASE / 'stage3/availability.json')['samples'] if s['process_status'] != 'COMPLETED']
    attempts = read(A / 'collection.json')['requests']
    return dict(schema_version=1, data_class='EXPLORATORY', time_basis='RAW_API_COORDINATE_UTC_UNVERIFIED',
        sources=sources, source_metadata_sha256=metadata, instruments=summaries,
        downloaded_records=sum(s['downloaded_records'] for s in summaries),
        consistent_unique_records=sum(s['consistent_unique_records'] for s in summaries) if all(s['consistent_unique_records'] is not None for s in summaries) else None,
        earlier_unsuccessful_attempts=earlier, new_attempts=attempts,
        synthetic_tick_records=0, historical_UTC_verified=False, continuous_history_certified=False,
        full_backtest_run=False, new_orders_sent=0)

if __name__ == '__main__':
    result = build()
    (A / 'coverage_inventory.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    for instrument in result['instruments']:
        print(instrument['symbol'], 'downloaded', instrument['downloaded_records'], 'unique', instrument['consistent_unique_records'],
            'overlap conflicts', len(instrument['overlap_conflicts']), 'request hours', round(instrument['requested_duration_ms']/3600000, 4))
    print('TOTAL:', result['downloaded_records'], 'downloaded;', result['consistent_unique_records'], 'unique')
