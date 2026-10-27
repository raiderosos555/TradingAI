"""Bounded local observer for ONLY the two offline LAB scheduled tasks."""
import json,subprocess,time
from pathlib import Path
from supervisor import connect,identity
A=Path(__file__).resolve().parent
def inspect(kind):
    root=A/'evidence'/('scheduler-'+kind)
    with connect(root/'supervision') as db:
        return dict(control=dict(db.execute('SELECT * FROM control').fetchone()),runs=[dict(x) for x in db.execute('SELECT * FROM runs ORDER BY rowid')],events=[dict(x) for x in db.execute('SELECT * FROM events ORDER BY seq')])

start=time.time();healthy_observation=None
while time.time()-start<1000:
    crash=inspect('crash');healthy=inspect('healthy')
    hr=healthy['runs'][-1] if healthy['runs'] else None
    if hr and not healthy_observation:
        ticks=[x for x in healthy['events'] if x['kind']=='TICK' and x['at']>hr['created']]
        if len(ticks)>=2 and hr['pid'] and identity(hr['pid'])==hr['birth']:
            healthy_observation=dict(at=time.time(),same_owner_alive=True,periodic_ticks_while_owner_alive=len(ticks),owner=hr)
            stop=A/'evidence/scheduler-healthy/state/runtime/DISABLED';stop.parent.mkdir(parents=True,exist_ok=True);stop.touch()
    if crash['control']['intervention']=='RETRIES_EXHAUSTED' and healthy_observation:break
    time.sleep(5)
result=dict(started=start,finished=time.time(),crash=inspect('crash'),healthy=inspect('healthy'),healthy_observation=healthy_observation)
delays=[json.loads(x['payload'])['delay'] for x in result['crash']['events'] if x['kind']=='BACKOFF_SET']
result['checks']=dict(three_retries=[x['attempt'] for x in result['crash']['runs']]==[0,1,2,3],delays=delays==[60,120,240],circuit_open=result['crash']['control']['intervention']=='RETRIES_EXHAUSTED',monitor_independent_while_engine_alive=healthy_observation is not None)
result['status']='PASS' if all(result['checks'].values()) else 'FAIL_OR_TIMEOUT'
(A/'evidence/scheduler-result.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'status':result['status'],'checks':result['checks']}),flush=True)
