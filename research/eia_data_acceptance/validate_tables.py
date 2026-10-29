"""Offline acceptance of archived tables; does not infer first availability."""
import csv, hashlib, io, json
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from zoneinfo import ZoneInfo
from collect_tables import DATES

HERE=Path(__file__).resolve().parent
LABELS={'crude':'Commercial (Excluding SPR)', 'gasoline':'Total Motor Gasoline',
        'distillates':'Distillate Fuel Oil'}

def scheduled(day):
    return datetime.fromisoformat(day+'T10:30:00').replace(tzinfo=ZoneInfo('America/New_York')).astimezone(timezone.utc).isoformat()

def parse(raw, day):
    rows=list(csv.reader(io.StringIO(raw.decode('cp1252'))))
    if not rows or rows[0][0]!='STUB_1' or rows[0][3]!='Difference':
        raise ValueError('Unexpected stock table schema')
    current=datetime.strptime(rows[0][1],'%m/%d/%y').date()
    previous=datetime.strptime(rows[0][2],'%m/%d/%y').date()
    release=datetime.fromisoformat(day).date()
    if current-previous!=timedelta(days=7) or release-current!=timedelta(days=5):
        raise ValueError('Unexpected reference period for fixed Wednesday sample')
    end=next((i for i in range(1,len(rows)) if rows[i] and rows[i][0]=='STUB_1'),len(rows))
    stocks={}
    for key,label in LABELS.items():
        found=[r for r in rows[1:end] if r and r[0]==label]
        if len(found)!=1:raise ValueError('Missing or duplicate stock label')
        a,b,d=map(Decimal,found[0][1:4])
        if not all(x.is_finite() for x in (a,b,d)) or a<0 or b<0:
            raise ValueError('Invalid stocks')
        if abs(a-b-d)>Decimal('0.001'):raise ValueError('Stock arithmetic mismatch')
        stocks[key]={'current':str(a),'previous':str(b),'change':str(d)}
    return {'release_date':day,'reference_date':str(current),'previous_reference_date':str(previous),
            'scheduled_utc':scheduled(day),'published_at':None,'first_print_verified':False,
            'consensus_before_release':None,'units':'million barrels','stocks':stocks}

def validate(folder):
    manifest=json.loads((folder/'manifest.json').read_text())
    expected=['2026-'+d.replace('_','-') for d in DATES]
    if [r['release_date'] for r in manifest]!=expected:raise ValueError('Fixed release set mismatch')
    records=[]
    for m,d in zip(manifest,DATES):
        raw=(folder/(d+'.raw')).read_bytes()
        if m['returncode']!=0 or len(raw)!=m['bytes'] or hashlib.sha256(raw).hexdigest()!=m['sha256']:
            raise ValueError('Source integrity failure')
        r=parse(raw,m['release_date'])
        # The legacy downloader records request start, NOT exact body receipt.
        r.update(url=m['url'],sha256=m['sha256'],request_started_utc=m['started_utc'],
                 received_at_exact=None,receipt_note='Body receipt after request start; exact completion not instrumented')
        records.append(r)
    comparisons=[]
    for a,b in zip(records,records[1:]):
        if a['reference_date']!=b['previous_reference_date']:raise ValueError('Noncontiguous issues')
        for key in LABELS:
            x=a['stocks'][key]['current'];y=b['stocks'][key]['previous']
            comparisons.append({'reference_date':a['reference_date'],'series':key,
                                'earlier_issue_value':x,'later_issue_value':y,'equal':Decimal(x)==Decimal(y)})
    return {'events':records,'same_week_comparisons':comparisons,'total_bytes':sum(m['bytes'] for m in manifest),
            'strict_replay':'NO-GO','historical_utc_verified':False}

def main():
    out=HERE/'private'/'acceptance-v1.json'
    if out.exists():raise RuntimeError('Refuse overwrite')
    result=validate(HERE/'private'/'tables-v1')
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({'events':len(result['events']),'comparisons':len(result['same_week_comparisons']),
          'differences':sum(not x['equal'] for x in result['same_week_comparisons']), 'bytes':result['total_bytes']}))

if __name__=='__main__':main()
