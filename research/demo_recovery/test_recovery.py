import copy,json,os,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from supervisor import SupervisorPolicy
A=Path(__file__).resolve().parent;SOURCE=A/'source_snapshot'
sys.path.insert(0,str(SOURCE))
from trading_ai.journal import Journal
from trading_ai.simulation import SimBroker,fixture
from trading_ai.models import Blocked,envelope
from trading_ai.risk import RiskManager
from trading_ai.execution import ExecutionEngine
from trading_ai.runtime import require_authorization,configuration_hash
FLAGS=subprocess.CREATE_NO_WINDOW if os.name=='nt' else 0

class HistoryView:
    def __init__(self,b):object.__setattr__(self,'target',b)
    def __getattr__(self,key):return getattr(self.target,key)
    def __setattr__(self,key,value):
        if key=='history':object.__setattr__(self,key,value)
        else:setattr(self.target,key,value)
    def history(self,*args):
        orders=copy.deepcopy(self.target.history)
        # SimBroker's minimal history lacks identity fields present in MT5.
        # Populate those fixture fields from the simulated deal, not live data.
        for order in orders:
            deal=next((d for d in self.target.deals if d['order']==order['ticket']),None)
            if deal:order.update({k:deal[k] for k in ['magic','comment','symbol','type']})
        return dict(orders=orders,deals=copy.deepcopy(self.target.deals))

class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(prefix='trading-recovery-lab-');self.addCleanup(self.tmp.cleanup);self.root=Path(self.tmp.name)

    def command(self,root,seconds=30,code=0):
        return [sys.executable,str(A/'lock_worker.py'),'--source',str(SOURCE),'--root',str(root),'--seconds',str(seconds),'--exit-code',str(code)]

    def test_disconnect_alone_original_runtime_retries(self):
        out=self.root/'disconnect-only'
        r=subprocess.run([sys.executable,str(A/'status_collision.py'),'--source',str(SOURCE),'--out',str(out),'--no-lock'],capture_output=True,timeout=15,creationflags=FLAGS)
        self.assertEqual(r.returncode,0)
        self.assertEqual(json.loads((out/'result.json').read_text())['connection_attempts'],2)

    def test_original_status_read_collision_exits_one_candidate_recovers(self):
        evidence={}
        for name,expected in [('source_snapshot',1),('candidate',0)]:
            out=self.root/name
            r=subprocess.run([sys.executable,str(A/'status_collision.py'),'--source',str(A/name),'--out',str(out)],capture_output=True,timeout=15,creationflags=FLAGS)
            evidence[name]={'exit_code':r.returncode,'stderr':r.stderr.decode(errors='replace')}
            self.assertEqual(r.returncode,expected)
            if name=='source_snapshot':
                self.assertIn('PermissionError',evidence[name]['stderr'])
                tmp=list((out/'state/runtime').glob('engine-status.json.*.tmp'))
                self.assertEqual(json.loads(tmp[0].read_text())['status'],'STOPPED')
            else:
                data=json.loads((out/'result.json').read_text());self.assertEqual(data['connection_attempts'],2);self.assertFalse(data['mt5_imported'])
                self.assertEqual(data['orders_sent'],0)
        (A/'collision-test-evidence.json').write_text(json.dumps(evidence,indent=2))

    def test_windows_lock_excludes_competitor_and_releases_after_abrupt_death(self):
        owner=subprocess.Popen(self.command(self.root),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=FLAGS)
        try:
            deadline=time.monotonic()+5
            while not list(self.root.glob('owner-*.json')) and time.monotonic()<deadline:time.sleep(.03)
            self.assertTrue(list(self.root.glob('owner-*.json')))
            other=subprocess.run(self.command(self.root,0),capture_output=True,timeout=5,creationflags=FLAGS)
            self.assertEqual(other.returncode,1);self.assertIn(b'Another engine',other.stderr)
            owner.kill();owner.wait(timeout=5)
            again=subprocess.run(self.command(self.root,0),capture_output=True,timeout=5,creationflags=FLAGS)
            self.assertEqual(again.returncode,0)
            self.assertTrue((self.root/'account/engine.lock').exists()) # no deleting locks
        finally:
            if owner.poll() is None:owner.kill();owner.wait(timeout=5)
            owner.stderr.close()

    def test_real_child_exit_then_supervised_restart_has_one_owner(self):
        policy=SupervisorPolicy();codes=[];launches=[]
        for code in [1,0]:
            now=max(time.monotonic(),policy.retry_at)
            self.assertEqual(policy.decide(now),'START')
            child=subprocess.Popen(self.command(self.root,.03,code),stdout=subprocess.DEVNULL,stderr=subprocess.PIPE,creationflags=FLAGS)
            self.assertEqual(policy.decide(now,child_alive=True),'OBSERVE')
            child.wait(timeout=5);codes.append(child.returncode);launches.append(child.pid);child.stderr.close()
            if child.returncode:policy.failed(now)
        self.assertEqual(codes,[1,0]);self.assertEqual(len(list(self.root.glob('owner-*.json'))),2)

    def test_stale_heartbeat_live_process_does_not_spawn_replacement(self):
        self.assertEqual(SupervisorPolicy().decide(10,child_alive=True,heartbeat_fresh=False),'ALERT_STALLED_NO_DUPLICATE')
    def test_existing_owner_disabled_backoff_and_circuit(self):
        p=SupervisorPolicy();self.assertEqual(p.decide(0,lock_free=False),'EXISTING_OWNER_NO_START')
        self.assertEqual(p.decide(0,enabled=False),'DISABLED')
        p.failed(0);self.assertEqual(p.decide(.5),'BACKOFF');self.assertEqual(p.decide(1),'START')
        p.failed(1);p.failed(3);self.assertEqual(p.decide(100),'CIRCUIT_OPEN')

    def setup_engine(self):
        self.b=HistoryView(SimBroker());self.c,plan=fixture(self.b.now);self.c['mode']='DEMO'
        self.env=envelope(plan,plan['signals'][0]);self.j=Journal(self.root/'state')
        self.addCleanup(lambda:self.j.close())
        self.j.set_setting('day_start',dict(date=self.b.now.date().isoformat(),equity=10000,account=123456,server='SIMULATOR'))
        self.j.approve(self.env,123456,'SIMULATOR')
        self.e=ExecutionEngine(RiskManager(self.c,self.b,self.j,activation='DEMO:123456',clock=lambda:self.b.now))
    def reopen(self):
        self.j.close();self.j=Journal(self.root/'state')
        self.e=ExecutionEngine(RiskManager(self.c,self.b,self.j,activation='DEMO:123456',clock=lambda:self.b.now))
    def test_filled_before_crash_is_reconciled_without_resend(self):
        self.setup_engine();self.e.execute(self.env);n=len(self.b.sent);op=self.j.operations()[0]
        with self.j.db:self.j.db.execute("UPDATE operations SET status='INTENT',result=NULL WHERE id=?",(op['id'],))
        self.reopen();result=self.e.reconcile()
        self.assertEqual(result[0]['status'],'CONFIRMED');self.assertEqual(len(self.b.sent),n)
        with self.assertRaises(Blocked):self.e.execute(self.env)
        self.assertEqual(len(self.b.sent),n)
    def test_missing_execution_evidence_quarantines_without_resend(self):
        self.setup_engine();self.e.execute(self.env);op=self.j.operations()[0];n=len(self.b.sent)
        with self.j.db:self.j.db.execute("UPDATE operations SET status='INTENT',result=NULL WHERE id=?",(op['id'],))
        self.b.history=lambda *a:dict(orders=[],deals=[]);self.b.positions=[];self.b.orders=[]
        self.reopen();result=self.e.reconcile();self.assertEqual(result[0]['status'],'UNCERTAIN')
        self.assertTrue(self.j.uncertain());self.assertEqual(len(self.b.sent),n)
    def test_confirmed_replay_is_idempotent(self):
        self.setup_engine();self.e.execute(self.env);n=len(self.b.sent);self.reopen()
        self.e.reconcile();self.e.reconcile();self.assertEqual(len(self.b.sent),n)
    def test_ambiguous_broker_candidates_remain_quarantined(self):
        self.setup_engine();self.e.execute(self.env);op=self.j.operations()[0];n=len(self.b.sent)
        with self.j.db:self.j.db.execute("UPDATE operations SET status='INTENT',result=NULL WHERE id=?",(op['id'],))
        history=self.b.history();history['orders'].append({**history['orders'][0],'ticket':99999})
        self.b.history=lambda *a:history
        self.reopen();self.assertEqual(self.e.reconcile()[0]['status'],'UNCERTAIN');self.assertEqual(len(self.b.sent),n)
    def test_partial_fill_not_automatically_topped_up(self):
        self.setup_engine();self.e.execute(self.env);op=self.j.operations()[0];n=len(self.b.sent)
        with self.j.db:self.j.db.execute("UPDATE operations SET status='INTENT',result=NULL WHERE id=?",(op['id'],))
        self.b.deals[0]['volume']/=2;self.b.positions[0]['volume']/=2
        self.reopen();self.assertEqual(self.e.reconcile()[0]['status'],'UNCERTAIN');self.assertEqual(len(self.b.sent),n)
    def test_other_account_cannot_reconcile(self):
        self.setup_engine();self.e.execute(self.env);op=self.j.operations()[0]
        with self.j.db:self.j.db.execute("UPDATE operations SET status='INTENT',result=NULL WHERE id=?",(op['id'],))
        self.b.account['login']=999;self.reopen()
        with self.assertRaisesRegex(Blocked,'across accounts'):self.e.reconcile()
    def test_authorization_cannot_be_extended_or_revoked_by_restart(self):
        self.setup_engine()
        from datetime import timedelta
        self.c['runtime']=dict(authorization_id='lab',starts_at=(self.b.now-timedelta(hours=1)).isoformat(),ends_at=(self.b.now+timedelta(hours=1)).isoformat())
        self.j.set_setting('runtime_authorization:lab',dict(config_hash=configuration_hash(self.c),allowed_offsets=[0]))
        self.c['broker_time_offset_seconds']=0
        require_authorization(self.c,self.j,self.b.now,clock_required=False)
        with self.assertRaisesRegex(Blocked,'window'):require_authorization(self.c,self.j,self.b.now+timedelta(hours=2),clock_required=False)
        self.j.set_setting('runtime_revoked',True)
        with self.assertRaisesRegex(Blocked,'revoked'):require_authorization(self.c,self.j,self.b.now,clock_required=False)

if __name__=='__main__':unittest.main()
