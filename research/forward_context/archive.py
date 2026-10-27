"""Append-only local context evidence. No MT5, network or execution imports."""
from __future__ import annotations
import hashlib,json,math,sqlite3
from datetime import datetime,timezone,timedelta
from pathlib import Path

MAX_BYTES=2_000_000
def utc(value):
    if not isinstance(value,str):raise ValueError('ISO timestamp string required')
    d=datetime.fromisoformat(value.replace('Z','+00:00'))
    if d.tzinfo is None:raise ValueError('Timezone required')
    return d.astimezone(timezone.utc)
def stamp(d):
    if d.tzinfo is None:raise ValueError('Receipt clock must be timezone-aware')
    return d.astimezone(timezone.utc).isoformat(timespec='microseconds')
def canonical(d):return json.dumps(d,sort_keys=True,ensure_ascii=False,allow_nan=False,separators=(',',':'))
def sha(raw):return hashlib.sha256(raw).hexdigest()
def parse(raw):
    def pairs(rows):
        d={}
        for k,v in rows:
            if k in d:raise ValueError('Duplicate JSON key')
            d[k]=v
        return d
    def finite(value):
        x=float(value)
        if not math.isfinite(x):raise ValueError('Nonfinite number')
        return x
    if len(raw)>MAX_BYTES:raise ValueError('Source exceeds byte limit')
    d=json.loads(raw.decode('utf-8-sig'),object_pairs_hook=pairs,parse_float=finite,parse_constant=lambda x:(_ for _ in ()).throw(ValueError('Nonfinite number')))
    if not isinstance(d,dict):raise ValueError('JSON object required')
    return d


class ContextArchive:
    def __init__(self,root,clock=None):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True)
        self.clock=clock or (lambda:datetime.now(timezone.utc))
        self.db=sqlite3.connect(self.root/'context.sqlite3',timeout=10)
        self.db.row_factory=sqlite3.Row
        self.db.executescript('''
          PRAGMA journal_mode=WAL; PRAGMA synchronous=FULL; PRAGMA foreign_keys=ON;
          CREATE TABLE IF NOT EXISTS versions(id TEXT PRIMARY KEY, source TEXT NOT NULL,
            raw BLOB NOT NULL, raw_sha256 TEXT NOT NULL, first_received_at TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS observations(seq INTEGER PRIMARY KEY,
            source TEXT NOT NULL, version_id TEXT REFERENCES versions(id),
            observed_wall_utc TEXT NOT NULL, not_before_utc TEXT NOT NULL,
            payload TEXT NOT NULL, previous_hash TEXT NOT NULL, record_hash TEXT NOT NULL);
          CREATE INDEX IF NOT EXISTS observed_source ON observations(source,seq);
          CREATE TRIGGER IF NOT EXISTS versions_no_update BEFORE UPDATE ON versions BEGIN SELECT RAISE(ABORT,'append-only'); END;
          CREATE TRIGGER IF NOT EXISTS versions_no_delete BEFORE DELETE ON versions BEGIN SELECT RAISE(ABORT,'append-only'); END;
          CREATE TRIGGER IF NOT EXISTS observations_no_update BEFORE UPDATE ON observations BEGIN SELECT RAISE(ABORT,'append-only'); END;
          CREATE TRIGGER IF NOT EXISTS observations_no_delete BEFORE DELETE ON observations BEGIN SELECT RAISE(ABORT,'append-only'); END;
        ''')
    def close(self):self.db.close()

    @staticmethod
    def metadata(raw,spec,now):
        d=parse(raw);kind=spec['kind'];producer=None
        if kind=='calendar':
            if [d.get('account_login'),d.get('account_server')]!=spec['account']:raise ValueError('Calendar account mismatch')
            if d.get('schema_version')!='1.0' or d.get('read_only') is not True:raise ValueError('Calendar schema')
            if d.get('status')!='OK':raise ValueError('Calendar source unavailable')
            value=d.get('retrieved_at_utc')
            if type(value) not in (int,float) or not math.isfinite(value):raise ValueError('Calendar time missing')
            producer=datetime.fromtimestamp(value,timezone.utc)
            if not isinstance(d.get('events'),list) or not d['events']:raise ValueError('Calendar events unavailable')
            lo,hi=d['coverage_from_utc'],d['coverage_until_utc']
            if any(type(v) not in (int,float) or not math.isfinite(v) for v in (lo,hi)) or not lo<hi:raise ValueError('Calendar coverage invalid')
        elif kind=='news':
            producer=utc(d['as_of'])
            if d.get('mode')!='SHADOW_CONTEXT' or d.get('orders_authorized') is not False:raise ValueError('News must remain SHADOW')
            if d.get('status') not in ('COLLECTED','PARTIAL'):raise ValueError('News source unavailable')
            if not isinstance(d.get('items'),list):raise ValueError('News items missing')
        elif kind=='runtime':producer=utc(d['at'])
        elif kind=='config':
            if d.get('mode')!='DEMO' or d.get('live_enabled') or d.get('live_allowlist'):raise ValueError('Unexpected trading mode')
        else:raise ValueError('Unsupported source kind')
        if producer and producer>now:raise ValueError('Producer time is in future; no availability assumed')
        return dict(kind=kind,producer_at=stamp(producer) if producer else None,
            producer_status=d.get('status'),source_validation='STRUCTURAL_ONLY_NOT_TRADING_APPROVAL')

    def observe(self,source,spec,raw=None,error=None,source_stat=None):
        now=self.clock();wall=stamp(now);metadata={};status='OBSERVED';reason=error
        if raw is not None:
            try:metadata=self.metadata(raw,spec,now)
            except (ValueError,KeyError,TypeError,OverflowError,UnicodeError) as exc:status='INVALID';reason=str(exc)
        else:status='UNAVAILABLE'
        with self.db:
            # Serialize observation order and receipt assignment across writers.
            self.db.execute('BEGIN IMMEDIATE')
            previous=self.db.execute('SELECT seq,not_before_utc,record_hash FROM observations ORDER BY seq DESC LIMIT 1').fetchone()
            sequence=previous['seq']+1 if previous else 1
            before=wall;clock_regression=bool(previous and wall<previous['not_before_utc'])
            if clock_regression:
                before=previous['not_before_utc'];status='CLOCK_REGRESSION';reason='Wall clock regressed; do not backdate availability'
            version=None
            if raw is not None:
                version=sha(source.encode()+b'\0'+raw)
                self.db.execute('INSERT OR IGNORE INTO versions VALUES(?,?,?,?,?)',(version,source,raw,sha(raw),wall))
            payload=dict(seq=sequence,source=source,version_id=version,observed_wall_utc=wall,
                not_before_utc=before,status=status,reason=reason,metadata=metadata,
                max_age_seconds=spec.get('max_age_seconds'),source_stat=source_stat,
                clock_regression=clock_regression,mode='SHADOW',orders_authorized=False)
            previous_hash=previous['record_hash'] if previous else '0'*64
            digest=sha((previous_hash+'\n'+canonical(payload)).encode())
            self.db.execute('INSERT INTO observations VALUES(?,?,?,?,?,?,?,?)',
                (sequence,source,version,wall,before,canonical(payload),previous_hash,digest))
        return payload

    def capture_file(self,source,spec):
        path=Path(spec['path'])
        try:
            before=path.stat()
            if before.st_size>MAX_BYTES:raise ValueError('Oversized source')
            raw=path.read_bytes();after=path.stat()
            keys=('st_ino','st_size','st_mtime_ns')
            if any(getattr(before,k)!=getattr(after,k) for k in keys):raise ValueError('Source changed during read')
            return self.observe(source,spec,raw=raw,source_stat=dict(path=str(path),size=after.st_size,
                mtime_ns=after.st_mtime_ns,mtime_is_not_receipt_evidence=True))
        except (OSError,ValueError) as exc:return self.observe(source,spec,error=str(exc))

    def asof(self,source,when):
        when=utc(when) if isinstance(when,str) else when
        at=stamp(when)
        row=self.db.execute('SELECT * FROM observations WHERE source=? AND not_before_utc<=? ORDER BY seq DESC LIMIT 1',(source,at)).fetchone()
        if not row:return dict(status='UNAVAILABLE',reason='No observation available by decision time',orders_authorized=False)
        meta=json.loads(row['payload'])
        result=dict(status=meta['status'],receipt=meta,orders_authorized=False,mode='SHADOW')
        if meta['status']!='OBSERVED':return result  # Never fall back past an error/new invalid version.
        provider=meta['metadata']['producer_at'];age=meta['max_age_seconds']
        if provider and (when<utc(provider) or age is not None and (when-utc(provider)).total_seconds()>age):
            return dict(result,status='STALE',reason='Producer snapshot is not current for decision time')
        version=self.db.execute('SELECT * FROM versions WHERE id=?',(row['version_id'],)).fetchone()
        if sha(version['raw'])!=version['raw_sha256']:raise ValueError('Blob integrity failure')
        result.update(status='AVAILABLE_FOR_SHADOW',source_payload=parse(version['raw']),
            first_received_at=version['first_received_at'],raw_sha256=version['raw_sha256'])
        if meta['metadata']['kind']=='news':
            eligible=[]
            for item in result['source_payload']['items']:
                try:
                    pub,seen=utc(item['published_at']),utc(item['first_seen_at'])
                    if pub<=when and seen<=when and (when-pub).total_seconds()<=72*3600:eligible.append(item)
                except (ValueError,KeyError,TypeError):pass
            result['eligible_news_items']=eligible
            result['news_coverage_gaps']=result['source_payload'].get('coverage_gaps',[])
        return result

    def verify(self):
        previous='0'*64;count=0
        for row in self.db.execute('SELECT * FROM observations ORDER BY seq'):
            count+=1;payload=json.loads(row['payload'])
            assert row['seq']==count and payload['seq']==count
            assert all(payload[k]==row[k] for k in ['source','version_id','observed_wall_utc','not_before_utc'])
            assert row['previous_hash']==previous
            assert row['record_hash']==sha((previous+'\n'+canonical(payload)).encode())
            assert payload['orders_authorized'] is False and payload['mode']=='SHADOW'
            previous=row['record_hash']
        for row in self.db.execute('SELECT * FROM versions'):
            assert sha(row['raw'])==row['raw_sha256']
            assert sha(row['source'].encode()+b'\0'+row['raw'])==row['id']
            first=self.db.execute('SELECT observed_wall_utc FROM observations WHERE version_id=? ORDER BY seq LIMIT 1',(row['id'],)).fetchone()
            assert first and first[0]==row['first_received_at']
        return dict(observations=count,versions=self.db.execute('SELECT count(*) FROM versions').fetchone()[0],
            head_hash=previous,orders_authorized=False,integrity='LOCAL_HASH_CHAIN_NOT_EXTERNAL_TIMESTAMP_AUTHORITY')
