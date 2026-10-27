"""Bounded read-only file observation. No scheduler and no trading process changes."""
import argparse,json,time,hashlib
from datetime import datetime,timezone
from pathlib import Path
from archive import ContextArchive,stamp
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True);p.add_argument('--duration-seconds',type=int,default=30)
args=p.parse_args()
if not 1<=args.duration_seconds<=600:raise SystemExit('Bounded capture duration must be 1..600 seconds')
args.out.mkdir(parents=True,exist_ok=False)
effective=json.loads((ROOT/'state/runtime/effective-config.json').read_text())
sources={
    'calendar':dict(kind='calendar',path='C:/Users/EXAMPLE_USER/AppData/Roaming/MetaQuotes/Terminal/EXAMPLE_TERMINAL/MQL5/Files/TradingAI/calendar_123456789.json',max_age_seconds=900,account=[effective['account_login'],effective['account_server']]),
    'news':dict(kind='news',path=str(ROOT/'state/news/latest.json'),max_age_seconds=1800),
    'effective_config':dict(kind='config',path=str(ROOT/'state/runtime/effective-config.json'),max_age_seconds=None),
    'runtime':dict(kind='runtime',path=str(ROOT/'state/runtime/engine-status.json'),max_age_seconds=30)}
config=dict(schema_version=1,mode='SHADOW',orders_authorized=False,sources=sources,
    interval_seconds=5,duration_seconds=args.duration_seconds,source_writes=False,
    time_basis='HOST_UTC_RECEIPT; PROVIDER_TIME_IS_A_CLAIM_NOT_A_BROKER_MAPPING')
snapshot=args.out/'source_snapshot';snapshot.mkdir()
config['source_sha256']={}
for name in ['archive.py','capture.py']:
    raw=(A/name).read_bytes();(snapshot/name).write_bytes(raw)
    config['source_sha256'][name]=hashlib.sha256(raw).hexdigest()
(args.out/'config.json').write_text(json.dumps(config,indent=2),encoding='utf-8')
archive=ContextArchive(args.out)
start=datetime.now(timezone.utc);began=time.monotonic();rounds=0
try:
    while True:
        rows=[archive.capture_file(name,spec) for name,spec in sources.items()];rounds+=1
        status=dict(status='RUNNING',at=stamp(datetime.now(timezone.utc)),rounds=rounds,
            last_sources={r['source']:r['status'] for r in rows},orders_authorized=False)
        (args.out/'status.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
        remaining=args.duration_seconds-(time.monotonic()-began)
        if remaining<=0:break
        time.sleep(min(5,remaining))
    result=dict(started_at=stamp(start),finished_at=stamp(datetime.now(timezone.utc)),rounds=rounds,
        status='COMPLETED',**archive.verify())
    (args.out/'result.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    (args.out/'status.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(result),flush=True)
finally:archive.close()
