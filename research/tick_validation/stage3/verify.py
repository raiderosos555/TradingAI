"""Offline cross-check of new captures and previous protected evidence."""
from pathlib import Path
import hashlib,json,gzip,subprocess,sys
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
read=lambda p:json.loads(p.read_text(encoding='utf-8'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for item in read(A/'manifest.json')['files']:assert sha(A/item['path'])==item['sha256'],item['path']
data=read(A/'availability.json');assert data['total_downloaded_tick_records']==6525
assert not data['full_backtest_run'] and not data['continuous_history_certified'] and not data['accepted_historical_utc_segments']
rows=data['samples'];assert len(rows)==13 and sum(r['status']=='OBSERVED' for r in rows)==12
assert {r['alias'] for r in rows if r['start'].startswith('2026-10-23') and r['status']=='OBSERVED'}=={'GOLD','OIL','US100','US500','EURUSD','EURPLN','GBPUSD'}
assert sum(r.get('exact_same_sequence_as_prior_capture') is True for r in rows)==1
for row in rows:
    capture=A/'captures'/row['capture']
    for item in read(capture/'manifest.json'):assert sha(A/item['path'])==item['sha256']
    result=read(capture/'result.json');assert result['orders_sent']==0 and not result['terminal_restarted']
    if row['status']=='OBSERVED':
        with gzip.open(capture/'ticks.raw.json.gz','rt',encoding='utf-8') as f:ticks=json.load(f)
        assert len(ticks)==row['count']
        assert ticks[0]['time_msc']==row['first_raw_ms'] and ticks[-1]['time_msc']==row['last_raw_ms']
        assert all(row['requested_start_raw_ms']<=t['time_msc']<row['requested_end_raw_ms'] for t in ticks)
    else:
        assert row['alias']=='OIL' and row['status']=='TIMEOUT' and row['last_phase']=='TICKS_START'
assert not read(A/'clock_review.json')['accepted_historical_utc_segments']
for item in read(A.parent/'inputs/protected_hashes.json'):assert sha(ROOT/item['path'])==item['sha256']
for script in ['verify_stage1.py','stage2/verify.py']:
    result=subprocess.run([sys.executable,str(A.parent/script)],capture_output=True,text=True,timeout=30)
    assert result.returncode==0,result.stdout+result.stderr
print('PASS: 13 attempts, 12 observed samples, 6525 records, one diagnosed timeout, historical UTC unresolved, protected sources unchanged.')
