"""The registered owner IS the runtime process, not an untracked wrapper child."""
import argparse,os,sys,time,traceback
from pathlib import Path
from supervisor import connect,event,identity,load,lock,disabled,update_progress

def launch(c,run_id):
    with lock(Path(c['home'])/'owner'):
        with connect(c['home']) as db:
            db.execute('BEGIN IMMEDIATE')
            ctl=db.execute('SELECT * FROM control WHERE id=1').fetchone()
            row=db.execute('SELECT * FROM runs WHERE id=?',(run_id,)).fetchone()
            if (not row or row['phase']!='STARTING' or ctl['config_hash']!=c['_hash']
                or ctl['intervention'] or disabled(c)):
                raise RuntimeError('Launch reservation not valid; no engine startup')
            db.execute("UPDATE runs SET phase='RUNNING',pid=?,birth=?,progress=? WHERE id=?",(os.getpid(),identity(os.getpid()),time.time(),run_id))
            event(db,'OWNER_REGISTERED',run=run_id,pid=os.getpid())
        code=1
        try:
            sys.path.insert(0,c['source'])
            if c['mode']=='LAB':
                from lab_runtime import run
                run(c,run_id)
            else:
                from trading_ai import runtime
                original=runtime.status_file
                def status(home,role,**data):
                    # Independent of os.replace: a locked JSON alone is not a hang.
                    update_progress(c,run_id,data)
                    return original(home,role,**data)
                runtime.status_file=status
                runtime.run(c['engine_config'],c['state'],c['exchange'],'engine')
            code=0
        except BaseException:
            trace=traceback.format_exc();print(trace,file=sys.stderr,flush=True)
            with connect(c['home']) as db:event(db,'ENGINE_EXCEPTION',run=run_id,traceback=trace)
            raise
        finally:
            with connect(c['home']) as db:
                db.execute("UPDATE runs SET phase='EXITED',exit_code=? WHERE id=?",(code,run_id))
                event(db,'ENGINE_EXIT',run=run_id,code=code,disabled=disabled(c))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--config',required=True);p.add_argument('--run-id',required=True);a=p.parse_args()
    launch(load(a.config),a.run_id)
