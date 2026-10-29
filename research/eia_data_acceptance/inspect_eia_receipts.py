"""Read-only data-availability audit; never inspects price returns or alters cohort."""
import hashlib,json,sqlite3
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
START='2026-10-28T14:20:00+00:00'
END='2026-10-29T17:00:00+00:00'
VALUE_ID='316565'

def inspect():
    path=ROOT/'state/forward_validation/cohort-20261026-v1/context/context.sqlite3'
    db=sqlite3.connect(path.as_uri()+'?mode=ro',uri=True,timeout=5)
    records=[];changes=[];previous=None;missing=0;count=0
    try:
        rows=db.execute('SELECT id,first_received_at,raw,raw_sha256 FROM versions WHERE source=? AND first_received_at>=? AND first_received_at<? ORDER BY first_received_at',('calendar',START,END))
        for vid,at,raw,h in rows:
            count+=1
            if hashlib.sha256(raw).hexdigest()!=h:raise ValueError('Calendar hash mismatch')
            d=json.loads(raw);matches=[e for e in d['events'] if e['id']==VALUE_ID]
            if len(matches)>1:raise ValueError('Duplicate calendar value ID')
            if not matches:missing+=1;continue
            e=matches[0]
            r={'received_at':at,'version_id':vid,'sha256':h,'event_id':e['event_id'],
               'value_id':e['id'],'actual':e['actual'],'forecast':e['forecast'],
               'previous':e['previous'],'producer_scheduled_utc_epoch':e['start_utc'],
               'producer_at_utc_epoch':d['retrieved_at_utc']}
            records.append(r)
            state=tuple(r[k] for k in ('actual','forecast','previous','producer_scheduled_utc_epoch'))
            if state!=previous:changes.append(r);previous=state
        first_actual=next((r for r in records if r['actual'] is not None),None)
        observation=None
        if first_actual:
            row=db.execute('SELECT payload FROM observations WHERE source=? AND version_id=? ORDER BY seq LIMIT 1',('calendar',first_actual['version_id'])).fetchone()
            if row:
                o=json.loads(row[0]);observation={k:o.get(k) for k in ('status','not_before_utc','clock_regression','orders_authorized')}
        return {'start':START,'end_exclusive':END,'calendar_versions_checked':count,
                'matching_versions':len(records),'missing_event_versions':missing,'changes':changes,
                'first_actual_observed':first_actual,'first_actual_observation':observation,
                'last_matching_receipt':records[-1]['received_at'] if records else None,
                'forecast_semantics':'Provider forecast; survey consensus NOT verified',
                'scope':'Local first observation, not global first publication. No price outcomes inspected.'}
    finally:db.close()

if __name__=='__main__':
    r=inspect();p=Path(__file__).resolve().parent/'private/eia-forward-receipt-20261028.json'
    with p.open('x',encoding='utf-8') as f:json.dump(r,f,indent=2)
    print(json.dumps(r,indent=2))
