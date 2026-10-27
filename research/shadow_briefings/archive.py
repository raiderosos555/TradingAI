"""Local append-only SHADOW archive. Standard library only, no execution transport.

Raw source bytes and JSON metadata are retained even if metadata is invalid.
Publication time is a source claim; first receipt is recorded by this process.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import re
from pathlib import Path
import sqlite3
import sys
from datetime import datetime, timezone

VERSION = 'shadow-briefing-1.0'
MAX_BYTES = 16 * 1024 * 1024
DECISIONS = {'TRADE', 'NO TRADE', 'HOLD', 'CANCEL'}
KINDS = {'BUY', 'SELL', 'BUY_LIMIT', 'SELL_LIMIT', 'BUY_STOP', 'SELL_STOP'}

def utc(value):
    if not isinstance(value, str):raise ValueError('Expected ISO timestamp with timezone')
    d = datetime.fromisoformat(value.replace('Z', '+00:00'))
    if d.tzinfo is None:raise ValueError('Timezone missing')
    return d.astimezone(timezone.utc)

def stamp(d):
    if d.tzinfo is None:raise ValueError('Receipt clock must be timezone-aware')
    return d.astimezone(timezone.utc).isoformat(timespec='microseconds')

def canonical(value):return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)
def sha(data):return hashlib.sha256(data).hexdigest()

def parse(raw):
    def pairs(items):
        result = {}
        for k,v in items:
            if k in result:raise ValueError('Duplicate JSON key: '+k)
            result[k] = v
        return result
    def bad_number(value):raise ValueError('Nonfinite JSON number: '+value)
    def finite_float(value):
        number=float(value)
        if not math.isfinite(number):return bad_number(value)
        return number
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=pairs, parse_constant=bad_number,parse_float=finite_float)

def validate(meta, document):
    errors=[]
    def require(condition, message):
        if not condition:errors.append(message)
    def text(v):return isinstance(v,str) and bool(v.strip())
    def positive(v):return type(v) in (int,float) and math.isfinite(v) and v>0
    if not isinstance(meta,dict):return ['Metadata must be an object']
    require(meta.get('schema_version')==VERSION, 'Unsupported schema_version')
    require(meta.get('mode')=='SHADOW', 'mode must be SHADOW')
    require(meta.get('orders_authorized') is False, 'orders_authorized must be false')
    require(type(meta.get('complete')) is bool, 'complete must be explicit boolean')
    require(text(meta.get('briefing_id')), 'briefing_id missing')
    require(meta.get('session') in {'morning','evening','ad_hoc'}, 'Invalid session')
    source=meta.get('source')
    if not isinstance(source,dict):errors.append('source missing');source={}
    require(source.get('kind') in {'manual_export','authorized_connector','local_generator'}, 'Unsupported source.kind')
    require(text(source.get('document_id')), 'source.document_id missing')
    require(text(source.get('publication_evidence')), 'publication_evidence required')
    try:utc(source.get('published_at'))
    except (ValueError,TypeError,OverflowError):errors.append('published_at missing or invalid timezone')
    require(isinstance(document,str) and bool(document.strip()), 'Full UTF-8 document required')
    plans=meta.get('plans')
    if not isinstance(plans,list):errors.append('plans must be an explicit list');plans=[]
    ids=set()
    for i,p in enumerate(plans):
        if not isinstance(p,dict):errors.append(f'plans[{i}] must be object');continue
        tag=f'plans[{i}]: '
        pid=p.get('plan_id')
        require(text(pid),tag+'plan_id missing')
        if text(pid):
            require(pid not in ids,tag+'duplicate plan_id');ids.add(pid)
        require(text(p.get('instrument')),tag+'instrument missing')
        decision=p.get('decision')
        require(isinstance(decision,str) and decision in DECISIONS,tag+'unknown decision')
        require(text(p.get('reason')),tag+'reason missing')
        require('sl' in p and 'tp' in p,tag+'explicit sl/tp fields required (null allowed for non-TRADE)')
        if decision=='TRADE':
            require(isinstance(p.get('kind'),str) and p.get('kind') in KINDS,tag+'kind required')
            require(positive(p.get('entry')),tag+'entry must be positive')
            require(positive(p.get('sl')),tag+'sl must be positive')
            targets=p.get('tp')
            require(isinstance(targets,list) and bool(targets) and all(positive(x) for x in targets),tag+'tp must contain positive targets')
            if positive(p.get('entry')) and positive(p.get('sl')) and isinstance(targets,list) and targets and all(positive(x) for x in targets) and isinstance(p.get('kind'),str):
                buy=p['kind'].startswith('BUY')
                require(all(p['sl']<p['entry']<x if buy else x<p['entry']<p['sl'] for x in targets),tag+'price levels conflict with direction')
            try:require(utc(p['valid_from'])<utc(p['valid_until']),tag+'empty validity interval')
            except (KeyError,ValueError,TypeError,OverflowError):errors.append(tag+'validity requires explicit timezone')
        else:
            require(p.get('sl') is None or positive(p.get('sl')),tag+'invalid optional sl')
            require(p.get('tp') is None or isinstance(p.get('tp'),list) and all(positive(x) for x in p['tp']),tag+'invalid optional tp')
        if decision in {'HOLD','CANCEL'}:require(text(p.get('target_plan_id')),tag+'target_plan_id required')
    return errors


class Archive:
    def __init__(self, root, clock=None):
        self.root=Path(root)
        self.root.mkdir(parents=True,exist_ok=True)
        self.clock=clock or (lambda:datetime.now(timezone.utc))
        self.db=sqlite3.connect(self.root/'shadow.sqlite3',timeout=30)
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.executescript('''
          CREATE TABLE IF NOT EXISTS records (
            id TEXT PRIMARY KEY, source_key TEXT, first_received_at TEXT NOT NULL,
            raw_document BLOB NOT NULL, raw_metadata BLOB NOT NULL,
            metadata_json TEXT, errors_json TEXT NOT NULL, clock_regression INTEGER NOT NULL);
          CREATE TABLE IF NOT EXISTS receipts (
            seq INTEGER PRIMARY KEY, record_id TEXT NOT NULL REFERENCES records(id),
            received_at TEXT NOT NULL, clock_regression INTEGER NOT NULL);
          CREATE INDEX IF NOT EXISTS source_lookup ON records(source_key);
          CREATE TRIGGER IF NOT EXISTS records_no_update BEFORE UPDATE ON records BEGIN SELECT RAISE(ABORT,'append-only records'); END;
          CREATE TRIGGER IF NOT EXISTS records_no_delete BEFORE DELETE ON records BEGIN SELECT RAISE(ABORT,'append-only records'); END;
          CREATE TRIGGER IF NOT EXISTS receipts_no_update BEFORE UPDATE ON receipts BEGIN SELECT RAISE(ABORT,'append-only receipts'); END;
          CREATE TRIGGER IF NOT EXISTS receipts_no_delete BEFORE DELETE ON receipts BEGIN SELECT RAISE(ABORT,'append-only receipts'); END;
        ''')

    def close(self):self.db.close()

    def ingest(self, document:bytes, metadata:bytes):
        if not isinstance(document,bytes) or not isinstance(metadata,bytes):raise TypeError('Exact bytes required')
        if max(len(document),len(metadata))>MAX_BYTES:raise ValueError('Input exceeds 16 MiB; not truncated or archived')
        errors=[];meta=None;source_key=None
        try:body=document.decode('utf-8-sig')
        except UnicodeError:body=None;errors.append('Document is not UTF-8; original bytes retained')
        try:
            meta=parse(metadata)
            errors.extend(validate(meta,body))
        except (ValueError,UnicodeError,TypeError,RecursionError) as exc:errors.append('Invalid metadata: '+str(exc))
        if isinstance(meta,dict) and isinstance(meta.get('source'),dict):
            src=meta['source']
            if isinstance(src.get('kind'),str) and isinstance(src.get('document_id'),str):
                source_key=canonical([src['kind'],src['document_id']])
        record_id=sha(len(document).to_bytes(8,'big')+document+metadata)
        # Receipt timestamp is generated under the write lock, never read from payload.
        with self.db:
            self.db.execute('BEGIN IMMEDIATE')
            received=stamp(self.clock())
            previous=self.db.execute('SELECT MAX(received_at) FROM receipts').fetchone()[0]
            regression=bool(previous and received<previous)
            exists=self.db.execute('SELECT id FROM records WHERE id=?',(record_id,)).fetchone()
            if not exists:
                self.db.execute('INSERT INTO records VALUES (?,?,?,?,?,?,?,?)',
                    (record_id,source_key,received,document,metadata,canonical(meta) if meta is not None else None,canonical(errors),int(regression)))
            self.db.execute('INSERT INTO receipts(record_id,received_at,clock_regression) VALUES (?,?,?)',
                            (record_id,received,int(regression)))
        return dict(record_id=record_id,duplicate=bool(exists),mode='SHADOW',orders_authorized=False,
                    first_received_at=self.get(record_id)['first_received_at'],received_at=received,
                    validation_errors=errors,clock_regression=regression)

    def get(self, record_id):
        row=self.db.execute('SELECT * FROM records WHERE id=?',(record_id,)).fetchone()
        if row is None:raise KeyError(record_id)
        raw,metadata=bytes(row['raw_document']),bytes(row['raw_metadata'])
        # SQLite constraints prevent routine edits, but verify stored bytes on every read.
        if sha(len(raw).to_bytes(8,'big')+raw+metadata)!=row['id']:
            raise ValueError('Archive integrity failure: raw bytes no longer match record ID')
        try:
            parsed=parse(metadata)
        except (ValueError,UnicodeError,TypeError,RecursionError):parsed=None
        meta=json.loads(row['metadata_json']) if row['metadata_json'] is not None else None
        if canonical(parsed)!=canonical(meta):raise ValueError('Archive integrity failure: metadata cache differs')
        # No source field may override envelope safety or locally recorded receipt.
        return dict(schema_version='shadow-archive-record-1.0',record_id=row['id'],mode='SHADOW',
                    orders_authorized=False,research_status='EXPLORATORY_UNLESS_SEPARATE_FORWARD_PROTOCOL',
                    first_received_at=row['first_received_at'],clock_regression=bool(row['clock_regression']),
                    document_sha256=sha(raw),metadata_sha256=sha(metadata),metadata=meta,
                    validation_errors=json.loads(row['errors_json']),document_utf8=raw.decode('utf-8-sig',errors='replace'),
                    receipts=[dict(x) for x in self.db.execute('SELECT received_at,clock_regression FROM receipts WHERE record_id=? ORDER BY seq',(record_id,))])

    def as_of(self, cutoff):
        cutoff=utc(cutoff)
        rows=self.db.execute('SELECT id FROM records WHERE first_received_at<=? ORDER BY first_received_at,id',(stamp(cutoff),)).fetchall()
        result=[]
        for row in rows:
            record=self.get(row['id']);m=record['metadata'];reasons=list(record['validation_errors'])
            # A point-in-time view must not reveal later duplicate receipt timestamps.
            record['receipts']=[x for x in record['receipts'] if not x['clock_regression'] and utc(x['received_at'])<=cutoff]
            if record['clock_regression']:reasons.append('Receipt clock regressed')
            if not isinstance(m,dict) or m.get('complete') is not True:reasons.append('Source declared incomplete or completeness unknown')
            try:
                if utc(m['source']['published_at'])>cutoff:reasons.append('Publication later than cutoff')
            except (KeyError,TypeError,ValueError,OverflowError):reasons.append('Publication unverified or missing')
            record.update(as_of=stamp(cutoff),context_eligible=not reasons,context_exclusions=reasons)
            plan_states=[]
            for plan in m.get('plans',[]) if isinstance(m,dict) and isinstance(m.get('plans'),list) else []:
                if not isinstance(plan,dict):continue
                state='INFORMATION_ONLY'
                if plan.get('decision')=='TRADE':
                    try:
                        start,end=utc(plan['valid_from']),utc(plan['valid_until'])
                        state='EXPIRED' if cutoff>=end else 'NOT_YET_VALID' if cutoff<start else 'WITHIN_DECLARED_WINDOW'
                    except (KeyError,TypeError,ValueError,OverflowError):state='UNKNOWN_VALIDITY'
                plan_states.append(dict(plan_id=plan.get('plan_id'),decision=plan.get('decision'),
                                        temporal_state=state,orders_authorized=False))
            record['plan_states']=plan_states
            result.append(record)
        return result

    def export(self, record_id, output):
        output=Path(output);output.mkdir(parents=True,exist_ok=True)
        r=self.get(record_id)
        row=self.db.execute('SELECT raw_document,raw_metadata FROM records WHERE id=?',(record_id,)).fetchone()
        # Hash-derived filenames; source IDs are never paths. Existing differing files are refused.
        values={record_id+'.json':(canonical(r)+'\n').encode('utf-8'),
                record_id+'.source':bytes(row[0]),record_id+'.metadata.source':bytes(row[1])}
        structured=canonical(r['metadata'])
        fence='`'*(max([len(x.group()) for x in re.finditer(r'`+',r['document_utf8']+structured)]+[2])+1)
        md=f"# Briefing SHADOW\n\nOrders authorized: false.\n\nRecord: {record_id}\n\nFirst received: {r['first_received_at']}\n\nValidation errors: {json.dumps(r['validation_errors'],ensure_ascii=False)}\n\nSource metadata and decisions (untrusted):\n\n{fence}json\n{structured}\n{fence}\n\nSource document (untrusted, verbatim text):\n\n{fence}text\n{r['document_utf8']}\n{fence}\n"
        values[record_id+'.md']=md.encode('utf-8')
        # Receipts grow, so each export is a snapshot in a new output directory.
        for name,data in values.items():
            p=output/name
            if p.exists() and p.read_bytes()!=data:raise FileExistsError('Use a new export directory; immutable export differs: '+str(p))
        for name,data in values.items():
            p=output/name
            if not p.exists():
                with p.open('xb') as f:f.write(data)
        return str(output/(record_id+'.json'))


def main():
    if hasattr(sys.stdout,'reconfigure'):sys.stdout.reconfigure(encoding='utf-8')
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--root',type=Path,default=Path(__file__).resolve().parent/'archive')
    sub=p.add_subparsers(dest='command',required=True)
    ingest=sub.add_parser('ingest');ingest.add_argument('--document',type=Path,required=True);ingest.add_argument('--metadata',type=Path,required=True)
    view=sub.add_parser('as-of');view.add_argument('--at',required=True)
    exp=sub.add_parser('export');exp.add_argument('--id',required=True);exp.add_argument('--output',type=Path,required=True)
    args=p.parse_args();a=Archive(args.root)
    try:
        if args.command=='ingest':result=a.ingest(args.document.read_bytes(),args.metadata.read_bytes())
        elif args.command=='as-of':result=dict(mode='SHADOW',orders_authorized=False,records=a.as_of(args.at))
        else:result=dict(export=a.export(args.id,args.output),mode='SHADOW',orders_authorized=False)
        print(canonical(result))
    finally:a.close()

if __name__=='__main__':main()
