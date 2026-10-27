"""Independent passive local service. No trading_ai imports and no order API."""
import argparse,hashlib,json,os,shutil,sqlite3,subprocess,sys,time,uuid,msvcrt
from datetime import datetime,timezone
from pathlib import Path
from quality import digest

A=Path(__file__).resolve().parent;ROOT=A.parents[1]
sys.path.insert(0,str(ROOT/'research/forward_context'))
from archive import ContextArchive

def now():return datetime.now(timezone.utc).isoformat()
def save(path,data):
    temp=path.with_suffix(path.suffix+'.tmp');temp.write_text(json.dumps(data,indent=2,allow_nan=False),encoding='utf-8');temp.replace(path)
def load(path,default=None):
    return json.loads(path.read_text(encoding='utf-8-sig')) if path.exists() else default
def hashfile(path):return hashlib.sha256(path.read_bytes()).hexdigest()

class Collector:
    def __init__(self,root):
        self.root=root;root.mkdir(parents=True,exist_ok=True)
        self.lock=(root/'collector.lock').open('a+b');self.lock.seek(0)
        if not self.lock.read(1):self.lock.write(b'0');self.lock.flush()
        self.lock.seek(0);msvcrt.locking(self.lock.fileno(),msvcrt.LK_NBLCK,1)
        self.protocol=load(root/'protocol.v1.json')
        if not self.protocol:raise ValueError('Register protocol before collection')
        # Fail closed if collector code changed after registration. New versions
        # require a new cohort or explicit versioned amendment, never silent drift.
        for rel,expected in self.protocol['collector_hashes'].items():
            if hashfile(ROOT/rel)!=expected:raise ValueError('Collector source changed: '+rel)
        self.config=load(root/'frozen/effective-config.json')
        self.state=load(root/'cursor.json',{'cursors':{},'journal_seq':None,'last_bars_hour':None,'last_ntp':0})
        self.archive=ContextArchive(root/'context')
        self.db=sqlite3.connect(root/'evidence.sqlite3',timeout=10)
        self.db.executescript('''PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
          CREATE TABLE IF NOT EXISTS receipts(seq INTEGER PRIMARY KEY,at TEXT,kind TEXT,payload TEXT,previous_hash TEXT,hash TEXT);
          CREATE TABLE IF NOT EXISTS journal_versions(source TEXT,key TEXT,sha TEXT,first_received_at TEXT,raw TEXT,PRIMARY KEY(source,key,sha));
          CREATE TRIGGER IF NOT EXISTS receipts_no_update BEFORE UPDATE ON receipts BEGIN SELECT RAISE(ABORT,'append-only'); END;
          CREATE TRIGGER IF NOT EXISTS receipts_no_delete BEFORE DELETE ON receipts BEGIN SELECT RAISE(ABORT,'append-only'); END;
          CREATE TRIGGER IF NOT EXISTS journal_no_update BEFORE UPDATE ON journal_versions BEGIN SELECT RAISE(ABORT,'append-only'); END;
          CREATE TRIGGER IF NOT EXISTS journal_no_delete BEFORE DELETE ON journal_versions BEGIN SELECT RAISE(ABORT,'append-only'); END;''')
        self.child=None;self.last_fetch=0;self.last_journal=0;self.last_context=0;self.last_review=0
        self.previous_clock=None
        self.status=dict(status='STARTING',pid=os.getpid(),started_at=now(),orders_authorized=False,quote_patch_deployed=False)

    def record(self,kind,payload):
        last=self.db.execute('SELECT hash FROM receipts ORDER BY seq DESC LIMIT 1').fetchone()
        body=dict(at=now(),kind=kind,payload=payload,previous_hash=last[0] if last else '')
        h=digest(body)
        self.db.execute('INSERT INTO receipts(at,kind,payload,previous_hash,hash) VALUES(?,?,?,?,?)',
            (body['at'],kind,json.dumps(payload,sort_keys=True),body['previous_hash'],h));self.db.commit()

    def context(self):
        sources=self.protocol['context_sources']
        rows=[self.archive.capture_file(name,spec) for name,spec in sources.items()]
        self.status['context']={r['source']:r['status'] for r in rows}
        current=load(ROOT/'state/runtime/effective-config.json')
        self.status['configuration_matches_frozen']=current==self.config

    def journal(self):
        source=sqlite3.connect((ROOT/'state/journal.sqlite3').as_uri()+'?mode=ro',uri=True,timeout=2)
        source.row_factory=sqlite3.Row;source.execute('PRAGMA query_only=ON');source.execute('BEGIN')
        stamp=now();count=0
        try:
            if self.state['journal_seq'] is None:
                # Historical decisions are not reclassified as prospective.
                self.state['journal_seq']=source.execute('SELECT COALESCE(MAX(seq),0) FROM events').fetchone()[0]
                self.record('JOURNAL_START',dict(seq=self.state['journal_seq'],at=stamp))
            for table,key in [('signals','id'),('operations','id'),('settings','key'),('events','seq')]:
                sql='SELECT * FROM '+table
                args=()
                if table=='events':sql+=' WHERE seq>? ORDER BY seq LIMIT 5000';args=(self.state['journal_seq'],)
                for row in source.execute(sql,args):
                    value=dict(row);raw=json.dumps(value,sort_keys=True,allow_nan=False);sha=hashlib.sha256(raw.encode()).hexdigest()
                    cur=self.db.execute('INSERT OR IGNORE INTO journal_versions VALUES(?,?,?,?,?)',(table,str(value[key]),sha,stamp,raw))
                    count+=cur.rowcount
                    if table=='events':self.state['journal_seq']=value[key]
            self.db.commit()
            self.record('JOURNAL_OBSERVATION',dict(new_versions=count,through_seq=self.state['journal_seq'],received_at=stamp,
                exact_engine_input_snapshot=False))
        finally:source.close()

    def launch(self):
        if shutil.disk_usage(self.root).free<10*1024**3:raise RuntimeError('Less than 10 GiB free; collector pauses, trading unchanged')
        name=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex[:8]
        out=self.root/'batches'/name;out.mkdir(parents=True)
        calendar=load(Path(self.protocol['context_sources']['calendar']['path']),{})
        offset=calendar.get('server_minus_gmt_seconds')
        age=time.time()-calendar.get('retrieved_at_utc',0)
        if not -2<=age<=900:offset=None
        strategy=[s['broker'] for s in self.config['symbols'].values()]
        bars_hour=int(time.time()//3600)
        r=dict(config=self.config,symbols=strategy+['USDPLN','USDPLN.pro'],strategy_symbols=strategy,
            cursors=self.state['cursors'],ea_offset=offset,retrieval_offset=offset,
            capture_bars=self.state['last_bars_hour']!=bars_hour,bars_hour=bars_hour,requested_at=now())
        save(out/'request.json',r)
        log=(out/'worker.log').open('wb')
        env=dict(os.environ,PYTHONPATH=str(ROOT/'.venv/Lib/site-packages'))
        process=subprocess.Popen([sys._base_executable,str(A/'worker.py'),str(out/'request.json')],
            cwd=ROOT,env=env,stdout=log,stderr=log,creationflags=subprocess.CREATE_NO_WINDOW|subprocess.BELOW_NORMAL_PRIORITY_CLASS)
        self.child=(process,out,time.monotonic(),log,r);self.last_fetch=time.monotonic()

    def collect_child(self):
        process,out,started,log,r=self.child
        if process.poll() is None and time.monotonic()-started<50:return
        timeout=process.poll() is None
        if timeout:process.kill();process.wait(timeout=5)
        log.close();result=load(out/'result.json',{})
        # Seal even interrupted responses. Advance cursors only for complete batches.
        manifest={p.name:hashfile(p) for p in sorted(out.iterdir()) if p.is_file()}
        save(out/'manifest.json',manifest)
        self.record('BATCH',dict(path=str(out.relative_to(self.root)),manifest_sha256=hashfile(out/'manifest.json'),
            exit_code=process.returncode,timeout=timeout,status=result.get('status','INCOMPLETE')))
        stats={};complete=process.returncode==0 and result.get('status')=='COMPLETED'
        if complete:
            for symbol,item in result['symbols'].items():
                stats[symbol]={'status':item['status']}
                if item['status']=='CAPTURED':
                    q=item['quality'];stats[symbol].update({k:q[k] for k in ['count','invalid_quotes','trade_only_invalid','overlap_status','max_internal_silence_ms']})
                    # Mismatches remain evidence and block acceptance; a cursor can
                    # still advance to collect the future without erasing the failure.
                    self.state['cursors'][symbol]=dict(end_raw_ms=item['end_raw_ms'],tail=q['tail'])
            if r['capture_bars'] and all((out/(s+'.bars.json')).exists() for s in r['strategy_symbols']):
                self.state['last_bars_hour']=r['bars_hour']
        self.status['last_batch']=dict(path=str(out),completed=complete,finished_at=now(),symbols=stats)
        save(self.root/'cursor.json',self.state);self.child=None

    def ntp(self):
        data={}
        for key,args in [('status',['w32tm','/query','/status','/verbose']),('peers',['w32tm','/query','/peers'])]:
            p=subprocess.run(args,capture_output=True,timeout=5,creationflags=subprocess.CREATE_NO_WINDOW)
            data[key]=dict(returncode=p.returncode,stdout=p.stdout.decode(errors='replace'),stderr=p.stderr.decode(errors='replace'))
        self.record('HOST_CLOCK',dict(at=now(),monotonic_ns=time.monotonic_ns(),evidence=data,
            utc_accuracy_certified=False))
        self.state['last_ntp']=time.time()

    def run(self,duration=None):
        began=time.monotonic();self.record('START',dict(pid=os.getpid(),protocol_sha256=hashfile(self.root/'protocol.v1.json')))
        try:
            while not (self.root/'STOP_COLLECTOR').exists() and (duration is None or time.monotonic()-began<duration):
                t=time.monotonic()
                try:
                    wall=time.time()
                    if self.previous_clock:
                        old_wall,old_mono=self.previous_clock
                        drift=(wall-old_wall)-(t-old_mono)
                        if abs(drift)>.25:self.record('CLOCK_DISCONTINUITY',dict(wall_epoch=wall,monotonic=t,drift_seconds=drift))
                    self.previous_clock=(wall,t)
                    # Enforce the child deadline even when a context file is broken.
                    if self.child:self.collect_child()
                    if t-self.last_context>=5:self.context();self.last_context=t
                    if t-self.last_journal>=30:self.journal();self.last_journal=t
                    if time.time()-self.state['last_ntp']>=300:self.ntp()
                    if self.child is None and t-self.last_fetch>=60:self.launch()
                    self.status.update(status='COLLECTING',at=now(),child_running=self.child is not None)
                except Exception as exc:
                    self.record('ERROR',dict(type=type(exc).__name__,reason=str(exc)))
                    self.status.update(status='DEGRADED',at=now(),reason=str(exc))
                # Local review is a gate report, never an order authorization.
                if t-self.last_review>=300:
                    from review import review
                    try:save(self.root/'readiness.json',review(self.root))
                    except Exception as exc:self.record('REVIEW_ERROR',dict(reason=str(exc)))
                    self.last_review=t
                save(self.root/'status.json',self.status);time.sleep(1)
        finally:
            if self.child:
                p,out,started,log,r=self.child
                if p.poll() is None:p.kill();p.wait(timeout=5)
                log.close();self.record('INTERRUPTED_BATCH',dict(path=str(out.relative_to(self.root))))
            save(self.root/'cursor.json',self.state)
            self.record('STOP',dict(at=now()))
            self.status.update(status='STOPPED',at=now());save(self.root/'status.json',self.status)
            self.archive.close();self.db.close();self.lock.close()

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,required=True);p.add_argument('--duration',type=int)
    a=p.parse_args();Collector(a.root).run(a.duration)
