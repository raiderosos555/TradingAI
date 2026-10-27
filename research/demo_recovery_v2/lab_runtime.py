"""Offline fixtures behind the real launcher. Import of MT5 is prohibited."""
import copy,importlib.abc,json,os,sys,time
from contextlib import ExitStack,nullcontext
from datetime import datetime,timedelta
from pathlib import Path
from supervisor import connect,update_progress

class NoMT5(importlib.abc.MetaPathFinder):
    def find_spec(self,fullname,path=None,target=None):
        if fullname.split('.')[0]=='MetaTrader5':raise RuntimeError('LAB PROHIBITS MT5 IMPORT')
        return None

def run(c,run_id):
    assert c['mode']=='LAB';sys.meta_path.insert(0,NoMT5())
    assert 'MetaTrader5' not in sys.modules
    root=Path(c['state']);root.mkdir(parents=True,exist_ok=True)
    scenario=c['scenario'];print('LAB START '+scenario,flush=True)
    if scenario in {'authorization','disconnect','status_collision'}:
        return fault_runtime(c,run_id,scenario)
    from trading_ai.journal import process_lock
    with ExitStack() as stack:
        for folder in c['engine_locks']:stack.enter_context(process_lock(folder))
        if scenario=='crash':
            print('LAB abrupt exit with original engine locks held',flush=True);os._exit(17)
        if scenario=='exception':raise RuntimeError('CONTROLLED_LAUNCHER_TRACEBACK')
        if scenario in {'reconcile','uncertain','stop_revoked'}:return recover(c,run_id)
        update_progress(c,run_id,{'status':'RUNNING','clock':{'fixture':True}})
        until=time.monotonic()+c.get('lifetime',30)
        while time.monotonic()<until:
            if (root/'runtime/DISABLED').exists():return
            if scenario!='hang':update_progress(c,run_id,{'status':'RUNNING','clock':{'fixture':True}})
            time.sleep(.05)

def fault_runtime(c,run_id,scenario):
    from trading_ai import runtime,broker
    from trading_ai.models import Blocked
    root=Path(c['state']);home=root/'runtime';home.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((Path(c['source'])/'config.demo.json').read_text())
    cfg.update(account_login=123456,account_server='SIMULATOR',terminal_path='OFFLINE_ONLY')
    cfgpath=root/'lab-engine.json';cfgpath.write_text(json.dumps(cfg))
    os.environ['LOCALAPPDATA']=str(root/'local')
    calls=0;closed=0
    class FakeBroker:
        def __init__(self,*a,**kw):
            nonlocal calls
            calls+=1
            if calls>=2:(home/'DISABLED').touch()
            if scenario!='disconnect':raise Blocked('OFFLINE authorization failure')
        def snapshot(self):raise Blocked('OFFLINE MT5 disconnected')
        def close(self):
            nonlocal closed
            closed+=1
    broker.MT5Broker=FakeBroker
    original=runtime.status_file
    def status(home,role,**data):
        update_progress(c,run_id,data);return original(home,role,**data)
    runtime.status_file=status
    real_sleep=time.sleep;runtime.time.sleep=lambda delay:real_sleep(min(delay,.02))
    path=home/'engine-status.json';path.write_text('{}')
    with path.open('rb') if scenario=='status_collision' else nullcontext():
        runtime.run(cfgpath,root,Path(c['exchange']),'engine')
    (root/'fixture-result.json').write_text(json.dumps({'attempts':calls,'closed':closed,'orders_sent_to_mt5':0,'mt5_imported':'MetaTrader5' in sys.modules}))

class HistoryView:
    def __init__(self,b):object.__setattr__(self,'target',b)
    def __getattr__(self,k):return getattr(self.target,k)
    def __setattr__(self,k,v):setattr(self.target,k,v)
    def history(self,*a):
        rows=copy.deepcopy(self.target.history)
        for row in rows:
            deal=next((d for d in self.target.deals if d['order']==row['ticket']),None)
            if deal:row.update({k:deal[k] for k in ['magic','comment','symbol','type']})
        return dict(orders=rows,deals=copy.deepcopy(self.target.deals))

def recover(c,run_id):
    from trading_ai.simulation import SimBroker,fixture
    from trading_ai.journal import Journal
    from trading_ai.models import envelope,Blocked
    from trading_ai.execution import ExecutionEngine
    from trading_ai.manager import PositionManager
    from trading_ai.risk import RiskManager
    from trading_ai.runtime import require_authorization,configuration_hash
    root=Path(c['state']);saved=root/'simulated-broker.json';b=HistoryView(SimBroker())
    if saved.exists():
        data=json.loads(saved.read_text());b.now=datetime.fromisoformat(data.pop('now'))
        for key,value in data.items():setattr(b,key,value)
    cfg,plan=fixture(b.now);cfg['mode']='DEMO';env=envelope(plan,plan['signals'][0]);j=Journal(root)
    e=ExecutionEngine(RiskManager(cfg,b,j,'DEMO:123456',clock=lambda:b.now))
    if not saved.exists():
        j.set_setting('day_start',dict(date=b.now.date().isoformat(),equity=10000,account=123456,server='SIMULATOR'))
        j.approve(env,123456,'SIMULATOR');e.execute(env);op=j.operations()[0]
        with j.db:j.db.execute("UPDATE operations SET status='INTENT',result=NULL WHERE id=?",(op['id'],))
        if c['scenario']=='stop_revoked':(root/'STOP').touch();j.set_setting('runtime_revoked',True)
        saved.write_text(json.dumps({**{k:getattr(b.target,k) for k in ('positions','orders','deals','history','sent','account')},'now':b.now.isoformat()}))
        j.close();print('LAB crash after simulated broker fill, before durable confirmation',flush=True);os._exit(23)
    count=len(b.sent)
    if c['scenario']=='uncertain':b.history=[];b.positions=[];b.orders=[];b.deals=[]
    result=e.reconcile()
    if not j.uncertain():PositionManager(e).run()
    blocked=False
    if c['scenario']=='stop_revoked':
        cfg['runtime']=dict(authorization_id='fixture',starts_at=(b.now-timedelta(hours=1)).isoformat(),ends_at=(b.now+timedelta(hours=1)).isoformat())
        j.set_setting('runtime_authorization:fixture',dict(config_hash=configuration_hash(cfg),allowed_offsets=[0]))
        try:require_authorization(cfg,j,b.now,clock_required=False)
        except Blocked:blocked=True
    outcome=dict(result=result,sent_before=count,sent_after=len(b.sent),uncertain=j.uncertain(),stop=(root/'STOP').exists(),revoked=j.setting('runtime_revoked'),entry_blocked=blocked,mt5_imported='MetaTrader5' in sys.modules)
    (root/'fixture-result.json').write_text(json.dumps(outcome,indent=2));j.close()
    update_progress(c,run_id,{'status':'WAITING','clock':{'fixture':True},'quarantined':outcome['uncertain'],'stop_active':outcome['stop']})
    (root/'runtime').mkdir(exist_ok=True);(root/'runtime/DISABLED').touch()
