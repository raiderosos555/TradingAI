"""Read existing EA exports and Windows clock status; never set clocks or touch DEMO config."""
from pathlib import Path
import json,subprocess,hashlib
from datetime import datetime,timezone
A=Path(__file__).resolve().parent
source=Path(r'C:\Users\EXAMPLE_USER\AppData\Roaming\MetaQuotes\Terminal\EXAMPLE_TERMINAL\MQL5\Files\TradingAI')
now=datetime.now(timezone.utc);records=[]
for p in source.glob('*.json'):
 if not (p.name.startswith('observer_') or p.name.startswith('calendar_')):continue
 raw=p.read_bytes();d=json.loads(raw)
 if d.get('account_login')!=123456789 or d.get('account_server')!='EXAMPLE-DEMO-SERVER':continue
 stamp=d.get('utc_time',d.get('retrieved_at_utc'))
 if stamp is None:continue
 records.append({'file':p.name,'sha256':hashlib.sha256(raw).hexdigest(),'utc_reported':stamp,'utc_label':datetime.fromtimestamp(stamp,timezone.utc).isoformat(),'age_seconds':now.timestamp()-stamp,'server_minus_gmt_seconds':d.get('server_minus_gmt_seconds'),'broker_server_time':d.get('broker_server_time'),'fresh_within_600s':0<=now.timestamp()-stamp<=600})
result={'captured_at_utc':now.isoformat(),'records':records,'windows_clock_query':subprocess.run(['w32tm','/query','/status'],capture_output=True,text=True,creationflags=subprocess.CREATE_NO_WINDOW,timeout=10).stdout,'note':'EA clock arithmetic is host-dependent, not independent proof of timestamp encoding of history ticks.'}
out=A/'evidence'/('clock-'+now.strftime('%Y%m%dT%H%M%SZ')+'.json');out.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(out.name,[(r['file'],r['server_minus_gmt_seconds']) for r in records if r['fresh_within_600s']])
