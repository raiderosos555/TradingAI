"""One-shot, durable Windows supervisor. No MT5/order/journal mutation APIs.

The scheduled task calls tick once per minute. The launcher is the engine process;
its PID+creation time and progress are registered in a separate SQLite database.
An ambiguous launch reservation fails closed; it is never blindly retried.
"""
from __future__ import annotations
import argparse,ctypes,hashlib,json,os,sqlite3,subprocess,sys,time,traceback,uuid
from contextlib import contextmanager,ExitStack
from pathlib import Path

BACKOFF=(60,120,240)
_children=[]  # Retain Popen handles until exit; dispatcher does not wait on engine.

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()

@contextmanager
def lock(folder):
    # Same byte-range mechanism as the engine; separate supervisor ownership.
    import msvcrt
    folder=Path(folder);folder.mkdir(parents=True,exist_ok=True)
    with (folder/'engine.lock').open('a+b') as f:
        if f.seek(0,2)==0:f.write(b'0');f.flush()
        f.seek(0)
        try:msvcrt.locking(f.fileno(),msvcrt.LK_NBLCK,1)
        except OSError as exc:raise RuntimeError('LOCK_BUSY') from exc
        try:yield
        finally:f.seek(0);msvcrt.locking(f.fileno(),msvcrt.LK_UNLCK,1)

def identity(pid):
    """None means proven absent/exited; access/query failure is UNKNOWN, not dead."""
    from ctypes import wintypes as w
    k=ctypes.WinDLL('kernel32',use_last_error=True)
    k.OpenProcess.argtypes=[w.DWORD,w.BOOL,w.DWORD];k.OpenProcess.restype=w.HANDLE
    k.CloseHandle.argtypes=[w.HANDLE]
    k.GetExitCodeProcess.argtypes=[w.HANDLE,ctypes.POINTER(w.DWORD)]
    k.GetProcessTimes.argtypes=[w.HANDLE,*([ctypes.POINTER(w.FILETIME)]*4)]
    h=k.OpenProcess(0x1000,False,int(pid))
    if not h:
        if ctypes.get_last_error()==87:return None
        raise RuntimeError('PROCESS_IDENTITY_UNKNOWN')
    try:
        code=w.DWORD()
        if not k.GetExitCodeProcess(h,ctypes.byref(code)):raise RuntimeError('PROCESS_EXIT_UNKNOWN')
        if code.value!=259:return None
        times=[w.FILETIME() for _ in range(4)]
        if not k.GetProcessTimes(h,*[ctypes.byref(x) for x in times]):raise RuntimeError('PROCESS_CREATION_UNKNOWN')
        return str((times[0].dwHighDateTime<<32)|times[0].dwLowDateTime)
    finally:k.CloseHandle(h)

@contextmanager
def connect(home):
    p=Path(home)/'supervisor.sqlite3'
    if not p.is_file():raise RuntimeError('NOT_INITIALIZED: no automatic recreation of supervisor state')
    db=sqlite3.connect(p,timeout=10);db.row_factory=sqlite3.Row
    db.execute('PRAGMA synchronous=FULL')
    if db.execute('PRAGMA quick_check').fetchone()[0]!='ok':raise RuntimeError('CORRUPT_SUPERVISOR_STATE')
    try:
        with db:yield db
    finally:db.close()

def event(db,kind,**details):
    db.execute('INSERT INTO events(at,kind,payload) VALUES(?,?,?)',(time.time(),kind,json.dumps(details)))

def load(path):
    path=Path(path).resolve();c=json.loads(path.read_text(encoding='utf-8-sig'))
    c['_path']=str(path);c['_hash']=sha(path)
    if c['mode'] not in {'LAB','DEMO'}:raise RuntimeError('Unsupported supervisor mode')
    if c['mode']=='DEMO':
        if tuple(c['backoff_seconds'])!=BACKOFF or c['healthy_seconds']<300 or c['startup_timeout']<120:
            raise RuntimeError('Unapproved production recovery parameters')
        cfg=json.loads(Path(c['engine_config']).read_text(encoding='utf-8-sig'))
        if cfg['mode']!='DEMO' or cfg['live_enabled'] or cfg['live_allowlist']:raise RuntimeError('DEMO only')
        if not (Path(c['state'])/'journal.sqlite3').is_file():raise RuntimeError('Existing operation journal required')
    if len(c['backoff_seconds'])!=3 or any(x<=0 for x in c['backoff_seconds']):raise RuntimeError('Exactly three bounded retry delays required')
    for name,h in c['pinned_files'].items():
        if sha(name)!=h:raise RuntimeError('Pinned release/config changed: '+Path(name).name)
    return c

def initialize(c):
    home=Path(c['home']);home.mkdir(parents=True,exist_ok=True)
    with lock(home/'dispatch'):
        if (home/'supervisor.sqlite3').exists():raise RuntimeError('Never reset existing recovery state')
        with sqlite3.connect(home/'supervisor.sqlite3') as db:
            db.executescript('''PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL;
            CREATE TABLE control(id INTEGER PRIMARY KEY CHECK(id=1),config_hash TEXT,failures INTEGER,ready_at REAL,last_clock REAL,intervention TEXT);
            CREATE TABLE runs(id TEXT PRIMARY KEY,attempt INTEGER,created REAL,phase TEXT,pid INTEGER,birth TEXT,progress REAL,health_since REAL,healthy INTEGER DEFAULT 0,status TEXT,exit_code INTEGER,handled INTEGER DEFAULT 0);
            CREATE TABLE events(seq INTEGER PRIMARY KEY,at REAL,kind TEXT,payload TEXT);''')
            db.execute('INSERT INTO control VALUES(1,?,0,0,?,NULL)',(c['_hash'],time.time()))
            event(db,'INITIALIZED',mode=c['mode'])
        db.close()

def disabled(c):return (Path(c['home'])/'DISABLED').exists() or (Path(c['state'])/'runtime/DISABLED').exists()

def update_progress(c,run_id,status):
    now=time.time()
    with connect(c['home']) as db:
        row=db.execute('SELECT * FROM runs WHERE id=?',(run_id,)).fetchone()
        good=(status.get('status') in {'RUNNING','WAITING'} and bool(status.get('clock'))
              and not status.get('quarantined') and not status.get('stop_active'))
        since=(row['health_since'] or now) if good else None
        healthy=bool(good and now-since>=c['healthy_seconds'])
        db.execute('UPDATE runs SET progress=?,status=?,health_since=?,healthy=? WHERE id=?',
                   (now,status.get('status'),since,int(healthy or row['healthy']),run_id))

def tick(c):
    _children[:]=[p for p in _children if p.poll() is None]
    now=time.time();home=Path(c['home'])
    with lock(home/'dispatch'),connect(home) as db:
        db.execute('BEGIN IMMEDIATE')
        ctl=db.execute('SELECT * FROM control WHERE id=1').fetchone()
        event(db,'TICK')
        if ctl['config_hash']!=c['_hash']:raise RuntimeError('Recovery configuration changed after initialization')
        if now<ctl['last_clock']-2:
            db.execute("UPDATE control SET intervention='CLOCK_REGRESSION' WHERE id=1")
            event(db,'CLOCK_REGRESSION');return 'INTERVENTION'
        db.execute('UPDATE control SET last_clock=? WHERE id=1',(now,))
        row=db.execute('SELECT * FROM runs ORDER BY rowid DESC LIMIT 1').fetchone()
        # Living owners are always observed, including while disabled/circuit-open.
        if row and row['phase']=='RUNNING':
            try:birth=identity(row['pid'])
            except Exception:
                event(db,'IDENTITY_UNKNOWN',run=row['id']);return 'IDENTITY_UNKNOWN_NO_START'
            if birth==row['birth']:
                age=now-(row['progress'] or row['created'])
                alarm=age>c['heartbeat_timeout']
                event(db,'ALERT_STALLED_NO_REPLACEMENT' if alarm else 'OBSERVE',run=row['id'],age=age,status=row['status'])
                if row['healthy'] and ctl['failures']:
                    db.execute('UPDATE control SET failures=0 WHERE id=1');event(db,'HEALTHY_RESET')
                return 'ALERT_STALLED_NO_REPLACEMENT' if alarm else 'OBSERVE'
            db.execute("UPDATE runs SET phase='EXITED',exit_code=-999 WHERE id=?",(row['id'],))
            event(db,'OWNER_PROVEN_DEAD',run=row['id'],pid_reused=birth is not None)
            row=db.execute('SELECT * FROM runs WHERE id=?',(row['id'],)).fetchone()
        if disabled(c):event(db,'DISABLED');return 'DISABLED'
        if ctl['intervention']:return 'INTERVENTION'
        if row and row['phase']=='STARTING':
            if now-row['created']>c['startup_timeout']:
                db.execute("UPDATE control SET intervention='AMBIGUOUS_LAUNCH' WHERE id=1")
                event(db,'AMBIGUOUS_LAUNCH',run=row['id']);return 'INTERVENTION'
            return 'STARTING'
        if row and row['phase']=='EXITED' and not row['handled']:
            # Initial run is not a failed restart. Then 60/120/240, exactly 3 retries.
            failures=0 if row['healthy'] else (ctl['failures']+int(row['attempt']>0))
            db.execute('UPDATE runs SET handled=1 WHERE id=?',(row['id'],))
            if failures>=3:
                db.execute("UPDATE control SET failures=?,intervention='RETRIES_EXHAUSTED' WHERE id=1",(failures,))
                event(db,'CIRCUIT_OPEN',failures=failures);return 'INTERVENTION'
            retry_at=now+c['backoff_seconds'][failures]
            db.execute('UPDATE control SET failures=?,ready_at=? WHERE id=1',(failures,retry_at))
            event(db,'BACKOFF_SET',failures=failures,delay=c['backoff_seconds'][failures],retry_at=retry_at)
            return 'BACKOFF'
        if now<ctl['ready_at']:return 'BACKOFF'
        # Preflight only; the launcher and engine acquire lifetime locks again.
        try:
            with ExitStack() as stack:
                for folder in c['engine_locks']:stack.enter_context(lock(folder))
                stack.enter_context(lock(home/'owner'))
        except RuntimeError:
            event(db,'EXISTING_OWNER_NO_START');return 'EXISTING_OWNER_NO_START'
        run_id=uuid.uuid4().hex
        attempt=0 if row is None else ctl['failures']+1
        db.execute("INSERT INTO runs(id,attempt,created,phase) VALUES(?,?,?,'STARTING')",(run_id,attempt,now))
        event(db,'START_RESERVED',run=run_id,attempt=attempt)
        db.commit()  # Durable intent BEFORE Popen; a crash here cannot duplicate a child.
        folder=home/'runs'/run_id;folder.mkdir(parents=True)
        proc=None
        try:
            env=os.environ.copy();env['PYTHONUNBUFFERED']='1'
            with (folder/'console.log').open('ab',buffering=0) as output:
                proc=subprocess.Popen([c['python'],str(Path(__file__).with_name('launcher.py')),'--config',c['_path'],'--run-id',run_id],
                    cwd=c['source'],env=env,stdin=subprocess.DEVNULL,stdout=output,stderr=subprocess.STDOUT,
                    creationflags=subprocess.CREATE_NO_WINDOW,close_fds=True)
                _children.append(proc)
        except Exception:
            event(db,'SPAWN_FAILED',run=run_id,traceback=traceback.format_exc())
            if proc is None:db.execute("UPDATE runs SET phase='EXITED',exit_code=-998 WHERE id=?",(run_id,))
        return 'LAUNCHED'

def main():
    p=argparse.ArgumentParser();p.add_argument('--config',required=True,type=Path);p.add_argument('--initialize',action='store_true');a=p.parse_args()
    try:
        c=load(a.config)
        if a.initialize:initialize(c);print('INITIALIZED')
        else:print(tick(c))
    except BaseException:
        trace=traceback.format_exc();print(trace,file=sys.stderr)
        # Separate from engine status; preserve full dispatcher traceback.
        try:
            with a.config.with_suffix('.supervisor-errors.log').open('a',encoding='utf-8') as f:f.write(trace+'\n')
        except OSError:pass
        raise

if __name__=='__main__':main()
