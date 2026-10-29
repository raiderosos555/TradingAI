"""One fixed future source-acceptance window, no prices or trading, no retry run."""
import argparse,hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
from capture_eia import capture,LIMIT

def slots(p):
    lo=datetime.fromisoformat(p['start_utc']).timestamp()
    hi=datetime.fromisoformat(p['end_utc_exclusive']).timestamp()
    if hi<=lo or p['interval_seconds']<60 or p['max_requests']>40:
        raise ValueError('Unsupported collection bounds')
    if p['max_requests']*LIMIT>p['max_body_bytes']:raise ValueError('Budget too small')
    return [lo+i*p['interval_seconds'] for i in range(p['max_requests']) if lo+i*p['interval_seconds']<hi]

def run(protocol,out):
    raw=protocol.read_bytes();p=json.loads(raw);times=slots(p)
    if p['mode']!='SHADOW' or p['orders_authorized'] is not False:raise ValueError('SHADOW required')
    if datetime.fromisoformat(p['registered_at_utc']).timestamp()>=times[0]:raise ValueError('Late registration')
    if time.time()<times[0]-120:raise ValueError('Too early; start through the approved schedule')
    if time.time()>=datetime.fromisoformat(p['end_utc_exclusive']).timestamp():raise ValueError('Window already ended; no backfill')
    out.mkdir(parents=True,exist_ok=True)
    # Exclusive marker prevents a duplicate or second run, including after crash.
    with (out/'run-start.json').open('x') as f:
        json.dump({'at':datetime.now(timezone.utc).isoformat(),'protocol_sha256':hashlib.sha256(raw).hexdigest()},f)
    (out/'protocol.json').write_bytes(raw)
    events=[];total=0
    for stamp in times:
        while time.time()<stamp:time.sleep(max(0,min(1,stamp-time.time())))
        if time.time()-stamp>20:
            events.append({'slot_epoch':stamp,'status':'MISSED_SLOT'});continue
        if total+LIMIT>p['max_body_bytes']:break
        r=capture(out/'attempts',p['reference_date'],'FORWARD')
        total+=r.get('transport',{}).get('bytes',0)
        events.append({'slot_epoch':stamp,'status':r['status'],
                       'available_not_before_utc':r.get('available_not_before_utc')})
        with (out/('slot-'+str(int(stamp))+'.json')).open('x') as f:json.dump(events[-1],f,indent=2)
        if r.get('transport',{}).get('bytes',0)>LIMIT:break
    result={'finished_at':datetime.now(timezone.utc).isoformat(),'events':events,'body_bytes':total,
            'mode':'SHADOW','orders_authorized':False,'edge_inference_permitted':False}
    with (out/'result.json').open('x') as f:json.dump(result,f,indent=2)
    return result

if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--protocol',required=True,type=Path);a.add_argument('--out',required=True,type=Path)
    v=a.parse_args();run(v.protocol,v.out)
