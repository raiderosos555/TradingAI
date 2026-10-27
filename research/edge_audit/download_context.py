"""Read-only H4/D1 context from MT5; write only inside this audit directory."""
import sys,json
from pathlib import Path
from datetime import timedelta
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from trading_ai.models import load_config,read_json,timestamp,canonical,utcnow
from trading_ai.broker import MT5Broker
from trading_ai.journal import atomic_write
out=Path(__file__).parent/'inputs'
c=load_config(ROOT/'config.local.json');m=read_json(ROOT/'exchange/research/history-20261024/manifest.json')
end=timestamp(m['requested_end']);start=end-timedelta(days=365)
b=MT5Broker(c['terminal_path'],c.get('broker_time_offset_seconds',0))
try:
 a=b.snapshot()['account']
 assert [a['login'],a['server']]==[c['account_login'],c['account_server']]
 report=[]
 for alias,spec in c['symbols'].items():
  for tf in ['H4','D1']:
   try:
    bars=b.rates(spec['broker'],tf,start,end)
    atomic_write(out/(alias+'-'+tf+'.json'),canonical({'bars':bars,'source':'MT5 read-only','downloaded_at':utcnow().isoformat(),'current_offset_assumption':c['broker_time_offset_seconds']}))
    report.append({'instrument':alias,'timeframe':tf,'bars':len(bars)})
   except Exception as exc:report.append({'instrument':alias,'timeframe':tf,'error':str(exc)})
 atomic_write(out/'context-download.json',canonical(report));print(json.dumps(report))
finally:b.close()
