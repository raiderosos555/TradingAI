import concurrent.futures,ctypes,json,os,sqlite3,subprocess,sys,tempfile,time,unittest
from pathlib import Path
from make_config import build
from supervisor import load,initialize,tick,connect,identity,BACKOFF
A=Path(__file__).resolve().parent

class IntegrationTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='TradingAI-recovery-v2-');self.root=Path(self.temp.name)
        self.config=build(self.root);self.c=load(self.config);initialize(self.c)
        self.addCleanup(self.clean)
    def rows(self):
        with connect(self.c['home']) as db:return [dict(x) for x in db.execute('SELECT * FROM runs ORDER BY rowid')]
    def clean(self):
        try:
            rows=self.rows()
            for r in rows:
                if r['pid'] and identity(r['pid'])==r['birth']:self.kill(r)
            time.sleep(.1)
        finally:self.temp.cleanup()
    def kill(self,row):
        # Only a process registered by this test's isolated LAB database.
        assert self.c['mode']=='LAB' and self.root in Path(self.c['home']).parents
        assert identity(row['pid'])==row['birth']
        from ctypes import wintypes as w
        k=ctypes.WinDLL('kernel32',use_last_error=True)
        k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
        k.TerminateProcess.argtypes=[w.HANDLE,w.UINT];k.CloseHandle.argtypes=[w.HANDLE]
        h=k.OpenProcess(1,False,row['pid']);self.assertTrue(h)
        try:self.assertTrue(k.TerminateProcess(h,91))
        finally:k.CloseHandle(h)
        self.wait(lambda:identity(row['pid']) is None)
    def wait(self,predicate,timeout=8):
        until=time.monotonic()+timeout
        while time.monotonic()<until:
            if predicate():return
            time.sleep(.05)
        self.fail('Timed out waiting for controlled fixture')
    def scenario(self,name,backoff=None):
        # Replace entire unused fixture before first launch, never reset production state.
        self.temp.cleanup();self.temp=tempfile.TemporaryDirectory(prefix='TradingAI-recovery-v2-');self.root=Path(self.temp.name)
        self.config=build(self.root,name,backoff=backoff or (.15,.3,.6));self.c=load(self.config);initialize(self.c)
    def drive(self,until,timeout=12):
        deadline=time.monotonic()+timeout
        while time.monotonic()<deadline:
            tick(load(self.config)) # Reconstruct supervisor config/DB every time.
            if until():return
            time.sleep(.05)
        self.fail('No expected supervised outcome')
    def test_three_durable_failed_restarts_with_ordered_backoff(self):
        self.scenario('crash')
        def done():
            with connect(self.c['home']) as db:return db.execute('SELECT intervention FROM control').fetchone()[0]=='RETRIES_EXHAUSTED'
        self.drive(done)
        rows=self.rows();self.assertEqual([r['attempt'] for r in rows],[0,1,2,3])
        with connect(self.c['home']) as db:
            delays=[json.loads(x[0])['delay'] for x in db.execute("SELECT payload FROM events WHERE kind='BACKOFF_SET'")]
        self.assertEqual(delays,[.15,.3,.6]);self.assertEqual(BACKOFF,(60,120,240))
        self.assertEqual(tick(load(self.config)),'INTERVENTION');self.assertEqual(len(self.rows()),4)
    def test_live_stale_process_is_alarm_never_replaced(self):
        self.scenario('hang');tick(self.c);self.wait(lambda:self.rows()[0]['phase']=='RUNNING')
        time.sleep(.65);self.assertEqual(tick(load(self.config)),'ALERT_STALLED_NO_REPLACEMENT')
        self.assertEqual(len(self.rows()),1);self.assertIsNotNone(identity(self.rows()[0]['pid']))
    def test_real_owner_termination_and_new_supervisor_process_recovers(self):
        tick(self.c);self.wait(lambda:self.rows()[0]['phase']=='RUNNING');old=self.rows()[0];self.kill(old)
        # Entire dispatcher process is new, as after logout/reboot; not physical OS reboot.
        cmd=[sys.executable,str(A/'supervisor.py'),'--config',str(self.config)]
        a=subprocess.run(cmd,capture_output=True,timeout=10);self.assertEqual(a.returncode,0)
        time.sleep(.2);b=subprocess.run(cmd,capture_output=True,timeout=10);self.assertEqual(b.returncode,0)
        self.wait(lambda:len(self.rows())==2 and self.rows()[-1]['phase']=='RUNNING')
        self.assertNotEqual(self.rows()[-1]['birth'],old['birth'])
    def test_concurrent_dispatchers_have_only_one_owner(self):
        cmd=[sys.executable,str(A/'supervisor.py'),'--config',str(self.config)]
        with concurrent.futures.ThreadPoolExecutor(4) as ex:
            results=list(ex.map(lambda _:subprocess.run(cmd,capture_output=True,timeout=10),range(4)))
        self.wait(lambda:self.rows() and self.rows()[0]['phase']=='RUNNING')
        self.assertEqual(len(self.rows()),1)
    def test_lifetime_engine_lock_blocks_unmanaged_competitor(self):
        from supervisor import lock
        with lock(self.c['engine_locks'][1]):self.assertEqual(tick(self.c),'EXISTING_OWNER_NO_START')
        self.assertEqual(self.rows(),[])
    def test_ambiguous_launch_reservation_never_retried(self):
        with connect(self.c['home']) as db:
            db.execute("INSERT INTO runs(id,attempt,created,phase) VALUES('unknown',0,?,'STARTING')",(time.time()-10,))
        self.assertEqual(tick(self.c),'INTERVENTION');self.assertEqual(len(self.rows()),1)
    def test_disabled_prevents_launch_without_altering_engine_state(self):
        p=Path(self.c['state'])/'runtime/DISABLED';p.parent.mkdir();p.touch()
        self.assertEqual(tick(self.c),'DISABLED');self.assertEqual(self.rows(),[])
    def test_clock_regression_and_config_change_fail_closed(self):
        with connect(self.c['home']) as db:db.execute('UPDATE control SET last_clock=?',(time.time()+100,))
        self.assertEqual(tick(self.c),'INTERVENTION')
        altered=dict(self.c);altered['_hash']='wrong'
        with self.assertRaisesRegex(RuntimeError,'configuration changed'):tick(altered)
    def test_missing_or_corrupt_state_not_silently_reset(self):
        with self.assertRaisesRegex(RuntimeError,'Never reset'):initialize(self.c)
        with self.assertRaisesRegex(RuntimeError,'NOT_INITIALIZED'):
            with connect(self.root/'missing'):pass
    def test_exception_traceback_captured_from_real_launcher(self):
        self.scenario('exception');tick(self.c);self.wait(lambda:self.rows()[0]['phase']=='EXITED')
        log=next((Path(self.c['home'])/'runs').glob('*/console.log')).read_text()
        self.assertIn('Traceback',log);self.assertIn('CONTROLLED_LAUNCHER_TRACEBACK',log)
    def fault_case(self,scenario):
        self.scenario(scenario);tick(self.c);p=Path(self.c['state'])/'fixture-result.json'
        self.wait(p.exists);self.wait(lambda:self.rows()[0]['phase']=='EXITED')
        data=json.loads(p.read_text());self.assertEqual(data['attempts'],2);self.assertFalse(data['mt5_imported'])
        self.assertEqual(data['orders_sent_to_mt5'],0);self.assertEqual(self.rows()[0]['exit_code'],0)
        if scenario=='status_collision':self.assertIn('PermissionError',(p.parent/'runtime/engine.log').read_text())
    def test_mt5_disconnect_runtime_retry(self):self.fault_case('disconnect')
    def test_auth_failure_runtime_retry(self):self.fault_case('authorization')
    def test_status_file_collision_does_not_kill_launcher(self):self.fault_case('status_collision')
    def recovered_case(self,scenario):
        self.scenario(scenario);p=Path(self.c['state'])/'fixture-result.json'
        self.drive(p.exists);data=json.loads(p.read_text());self.assertFalse(data['mt5_imported'])
        self.assertEqual(data['sent_before'],data['sent_after']);self.assertEqual(len(self.rows()),2)
        return data
    def test_filled_intent_reconciled_after_process_crash_no_resend(self):
        d=self.recovered_case('reconcile');self.assertEqual(d['result'][0]['status'],'CONFIRMED');self.assertFalse(d['uncertain'])
    def test_uncertain_intent_quarantined_no_resend(self):
        d=self.recovered_case('uncertain');self.assertEqual(d['result'][0]['status'],'UNCERTAIN');self.assertTrue(d['uncertain'])
    def test_stop_revocation_survive_actual_restart(self):
        d=self.recovered_case('stop_revoked');self.assertTrue(d['stop']);self.assertTrue(d['revoked']);self.assertTrue(d['entry_blocked'])

if __name__=='__main__':unittest.main()
