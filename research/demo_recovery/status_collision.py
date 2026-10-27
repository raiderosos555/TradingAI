"""Run original/candidate runtime with a failing fake broker and Windows read lock."""
import argparse,json,os,sys
from contextlib import nullcontext
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--source',type=Path,required=True);p.add_argument('--out',type=Path,required=True);p.add_argument('--no-lock',action='store_true');a=p.parse_args()
sys.path.insert(0,str(a.source.resolve()))
from trading_ai import broker,runtime
from trading_ai.models import Blocked
assert 'MetaTrader5' not in sys.modules
a.out.mkdir(parents=True,exist_ok=True);os.environ['LOCALAPPDATA']=str(a.out/'local')
c=json.loads((a.source/'config.demo.json').read_text());c['account_login']=999123;c['account_server']='OFFLINE_SIMULATOR';c['terminal_path']='IN_MEMORY_ONLY'
(a.out/'config.json').write_text(json.dumps(c));home=a.out/'state/runtime';home.mkdir(parents=True,exist_ok=True)
status=home/'engine-status.json';status.write_text('{}')
calls=0
class FailingBroker:
    def __init__(self,*args,**kwargs):
        global calls
        calls+=1
        # A second attempted connection proves the retry loop survived telemetry.
        if calls>=2:(home/'DISABLED').touch()
        raise Blocked("MT5 initialization failed: (-6, 'Terminal: Authorization failed') [OFFLINE FIXTURE]")
broker.MT5Broker=FailingBroker
original_sleep=runtime.time.sleep
runtime.time.sleep=lambda delay:original_sleep(min(delay,.02))
with (nullcontext() if a.no_lock else status.open('rb')):
    runtime.run(a.out/'config.json',a.out/'state',a.out/'exchange','engine')
(a.out/'result.json').write_text(json.dumps(dict(connection_attempts=calls,mt5_imported='MetaTrader5' in sys.modules,orders_sent=0)))
