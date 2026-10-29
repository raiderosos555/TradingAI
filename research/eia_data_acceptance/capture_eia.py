"""One bounded official EIA capture. SHADOW only; no terminal or trading imports.
Invoke externally; this module does not install a scheduler or start a service.
"""
import argparse,hashlib,json,sys,time,uuid
from datetime import date,datetime,timedelta,timezone
from pathlib import Path
from validate_tables import parse

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent/'edge_data_unblock'))
from fetch import fetch
URL='https://ir.eia.gov/wpsr/table1.csv'
LIMIT=65536

def now():return datetime.now(timezone.utc)

def accept(raw,reference):
    expected=date.fromisoformat(reference)
    if expected.weekday()!=4:raise ValueError('Expected EIA reference week must end Friday')
    # Reuse stock schema/arithmetic checks with a nominal Wednesday. It is NOT
    # a claimed release date: Thursday holiday releases have the same week-end.
    r=parse(raw,(expected+timedelta(days=5)).isoformat())
    if r['reference_date']!=reference:raise ValueError('Wrong reference week; no fallback')
    return {k:r[k] for k in ('reference_date','previous_reference_date','units','stocks')}

def clocks_consistent(before,after,elapsed):
    wall=(after-before).total_seconds()
    return elapsed>=0 and wall>=0 and abs(wall-elapsed)<=1

def capture(out,reference,classification):
    # Immutable per-attempt directories; caller must select a separate cohort
    # for genuinely future observations. No reuse of old data as forward.
    run=out/(now().strftime('%Y%m%dT%H%M%S')+'-'+uuid.uuid4().hex)
    run.mkdir(parents=True,exist_ok=False)
    before=now();mono=time.monotonic()
    record={'schema':1,'url':URL,'expected_reference_date':reference,
            'classification':classification,'mode':'SHADOW','orders_authorized':False,
            'request_started_utc':before.isoformat(),'published_at':None,
            'first_print_verified':False,'utc_accuracy_certified':False,
            'source_code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'status':'FAILED','limit_bytes':LIMIT}
    try:
        transport=fetch('response',URL,run,LIMIT)
        received=now();elapsed=time.monotonic()-mono
        record.update(body_received_no_later_than_utc=received.isoformat(),elapsed_seconds=elapsed,
                      host_clock_consistent=clocks_consistent(before,received,elapsed),transport=transport)
        if transport['returncode']!=0 or not transport.get('transport','').startswith('200|'):
            raise ValueError('HTTP transfer failed; no fallback to previous data')
        raw=(run/'response.raw').read_bytes()
        if len(raw)>LIMIT or hashlib.sha256(raw).hexdigest()!=transport['sha256']:
            raise ValueError('Body integrity/size mismatch')
        record['data']=accept(raw,reference)
        if not record['host_clock_consistent']:raise ValueError('Wall/monotonic clock discrepancy')
        # Earliest usable time for THIS local observation is after validation.
        # This does not certify exchange publication or authorize an order.
        record.update(status='AVAILABLE_FOR_SHADOW',available_not_before_utc=now().isoformat())
    except Exception as exc:
        record['error']=type(exc).__name__+': '+str(exc)
    record['finished_at_utc']=now().isoformat()
    with (run/'receipt.json').open('x',encoding='utf-8') as f:json.dump(record,f,indent=2)
    print(json.dumps({'status':record['status'],'receipt':str(run/'receipt.json'),
                      'orders_authorized':False,'reference':reference}))
    return record

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--out',type=Path,required=True)
    p.add_argument('--expected-reference',required=True)
    p.add_argument('--classification',choices=['CALIBRATION','FORWARD'],required=True)
    a=p.parse_args();result=capture(a.out,a.expected_reference,a.classification)
    raise SystemExit(0 if result['status']=='AVAILABLE_FOR_SHADOW' else 2)
