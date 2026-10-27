"""Capture current observer arithmetic without interpreting it as tick UTC evidence."""
from pathlib import Path
import json,hashlib
from datetime import datetime,timezone
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
source=Path(r'C:\Users\EXAMPLE_USER\AppData\Roaming\MetaQuotes\Terminal\EXAMPLE_TERMINAL\MQL5\Files\TradingAI')
out=A/'clock_evidence';out.mkdir(exist_ok=True)
if (A/'clock_review.json').exists():raise SystemExit('Use a new version for a new capture')
now=datetime.now(timezone.utc);rows=[]
for p in sorted(source.glob('observer_*.json')):
    raw=p.read_bytes();d=json.loads(raw)
    if d.get('account_login')!=123456789 or d.get('account_server')!='EXAMPLE-DEMO-SERVER':continue
    (out/p.name).write_bytes(raw)
    rows.append(dict(file=p.name,sha256=hashlib.sha256(raw).hexdigest(),utc_time=d.get('utc_time'),
                     host_age_seconds=now.timestamp()-d.get('utc_time',0),
                     broker_server_time=d.get('broker_server_time'),calculated_server_minus_gmt_seconds=d.get('server_minus_gmt_seconds')))
mq=ROOT/'mql5/TradingAIObserver.mq5';(out/'TradingAIObserver.mq5').write_bytes(mq.read_bytes())
(out/'engine-status.json').write_bytes((ROOT/'state/runtime/engine-status.json').read_bytes())
result=dict(at=now.isoformat(),observer_arithmetic=rows,source_sha256=hashlib.sha256(mq.read_bytes()).hexdigest(),
            accepted_historical_utc_segments=[],fresh_post_dst_tick_anchor_available=False,
            conclusion='TimeTradeServer and TimeGMT depend on local terminal clock. Weekend arithmetic change alone is not broker DST proof.',
            documentation=[
                dict(url='https://www.mql5.com/en/docs/dateandtime/timetradeserver',finding='Calculated in client terminal; depends on computer time settings.'),
                dict(url='https://www.mql5.com/en/docs/dateandtime/timegmt',finding='GMT calculated using local computer time and DST.'),
                dict(url='https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py',finding='Documented UTC semantics require reconciliation with observed deal/host offset; no automatic global correction.'),
                dict(url='https://www.oanda.com/uk-en/trading/standard-account/differences/',finding='OANDA Europe Limited documentation concerns a different account entity; not adopted as the EXAMPLE-DEMO-SERVER historical timezone policy.')])
(A/'clock_review.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('Recorded',len(rows),'observer exports; historical UTC segments remain empty.')
