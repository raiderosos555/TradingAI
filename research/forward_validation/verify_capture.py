"""Independent bounded audit. Reads sealed batches and a SQLite snapshot only."""
import argparse,gzip,hashlib,json,re,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
from quality import digest,inspect_ticks,executable
from collector import ROOT,hashfile

def ntp_evidence(payload):
    d=payload['evidence']['status'];text=d['stdout']
    def number(label):
        m=re.search(re.escape(label)+r':\s*([-+\d.]+)',text)
        if not m:raise ValueError('Unrecognized NTP status: '+label)
        return float(m.group(1))
    try:
        age=number('Time since Last Good Sync Time')
        bound=number('Root Dispersion')+abs(number('Root Delay'))/2+abs(number('Phase Offset'))+age*.000015
        ok=d['returncode']==0 and number('Leap Indicator')==0 and 1<=number('Stratum')<=15 and number('Last Sync Error')==0 and 0<=age<=36000 and 0<=bound<=2
        return dict(status='NTP_STATUS_ACCEPTABLE' if ok else 'NTP_STATUS_NOT_ACCEPTABLE',
            at=payload['at'],conservative_error_estimate_seconds=bound,
            last_good_sync_age_seconds=age,externally_authenticated=False,
            basis='Windows NTP report; dispersion + half root delay + phase offset + 15ppm since last sync; not a certified bound')
    except (ValueError,KeyError) as exc:return dict(status='NTP_UNPARSED',reason=str(exc))

def audit(root):
    root=Path(root).resolve()
    protocol=json.loads((root/'protocol.v1.json').read_text());errors=[];totals={};previous={};last_core={};batch_anchors=[];snapshot_bad={}
    for rel,sha in protocol['collector_hashes'].items():
        if hashfile(ROOT/rel)!=sha:errors.append('Source changed: '+rel)
    for rel,sha in protocol['strategy_source_hashes'].items():
        if hashfile(root/rel)!=sha:errors.append('Frozen strategy changed: '+rel)
    production_unchanged={p.name:hashfile(p)==hashfile(root/'frozen/trading_ai'/p.name) for p in (ROOT/'trading_ai').glob('*.py')}
    # Snapshot includes receipts and journal consistency at one cutoff, not a live moving target.
    src=sqlite3.connect((root/'evidence.sqlite3').as_uri()+'?mode=ro',uri=True);db=sqlite3.connect(':memory:');src.backup(db);src.close()
    receipt_hash='';ntp=[];batch_receipts={};clock_steps=[]
    for seq,at,kind,payload,prev,h in db.execute('SELECT * FROM receipts ORDER BY seq'):
        p=json.loads(payload)
        if prev!=receipt_hash or digest(dict(at=at,kind=kind,payload=p,previous_hash=prev))!=h:errors.append('Receipt chain: '+str(seq))
        receipt_hash=h
        if kind=='HOST_CLOCK':ntp.append(ntp_evidence(p))
        if kind=='CLOCK_DISCONTINUITY':clock_steps.append(p)
        if kind=='BATCH':batch_receipts[p['path']]=p
    journal_counts=dict(db.execute('SELECT source,COUNT(*) FROM journal_versions GROUP BY source'))
    for raw,sha in db.execute('SELECT raw,sha FROM journal_versions'):
        if hashlib.sha256(raw.encode()).hexdigest()!=sha:errors.append('Journal bytes hash mismatch')
    for rel,receipt in batch_receipts.items():
        folder=root/rel;manifest=json.loads((folder/'manifest.json').read_text())
        if hashfile(folder/'manifest.json')!=receipt['manifest_sha256']:errors.append('Manifest changed: '+rel)
        for name,sha in manifest.items():
            if hashfile(folder/name)!=sha:errors.append('Batch bytes changed: '+rel+'/'+name)
        if receipt['status']!='COMPLETED':continue
        r=json.loads((folder/'result.json').read_text());req=json.loads((folder/'request.json').read_text());anchors=[]
        for symbol,item in r['symbols'].items():
            a=item.get('anchor',{})
            if a.get('status')=='CONSISTENT_CANDIDATE':anchors.append(a)
            sfile=folder/(symbol+'.snapshot.json')
            if sfile.exists():
                tick=json.loads(sfile.read_text())['latest_tick_raw']
                if not executable(tick):snapshot_bad[symbol]=snapshot_bad.get(symbol,0)+1
            if item['status']!='CAPTURED':continue
            with gzip.open(folder/(symbol+'.ticks.json.gz'),'rt',encoding='utf-8') as f:rows=json.load(f)
            old=previous.get(symbol);start,end=item['start_raw_ms'],item['end_raw_ms']
            q=inspect_ticks(rows,start,end,None if old is None else old['tail'])
            if q!=item['quality']:errors.append('Computed tick summary differs: '+rel+'/'+symbol)
            if old is not None and old['end']!=start:errors.append('Missing/overlapping core window: '+rel+'/'+symbol)
            if q['overlap_status']=='MISMATCH':errors.append('Provider revised overlap: '+rel+'/'+symbol)
            t=totals.setdefault(symbol,dict(ticks=0,chunks=0,invalid_quotes=0,trade_only_invalid=0,empty_chunks=0,
                overlap_matches=0,max_observed_silence_ms=0,start_raw_ms=start,end_raw_ms=end))
            t['ticks']+=q['count'];t['chunks']+=1;t['invalid_quotes']+=q['invalid_quotes'];t['trade_only_invalid']+=q['trade_only_invalid']
            t['empty_chunks']+=q['empty_interval'];t['overlap_matches']+=q['overlap_status']=='MATCH';t['end_raw_ms']=end
            silence=q['max_internal_silence_ms']
            if q['first_raw_ms'] is not None:
                if symbol in last_core:silence=max(silence,q['first_raw_ms']-last_core[symbol])
                last_core[symbol]=q['last_raw_ms']
            t['max_observed_silence_ms']=max(t['max_observed_silence_ms'],silence)
            previous[symbol]=dict(end=end,tail=q['tail'])
        batch_anchors.append(dict(at=r['started_at'],offset=req['ea_offset'],anchors=anchors))
    db.close()
    # Verify a snapshot of the context DB, without mutating the live archive.
    import tempfile
    sys.path.insert(0,str(ROOT/'research/forward_context'))
    from archive import ContextArchive
    with tempfile.TemporaryDirectory(prefix='forward-context-verify-') as tmp:
        src=sqlite3.connect((root/'context/context.sqlite3').as_uri()+'?mode=ro',uri=True)
        dest=sqlite3.connect(Path(tmp)/'context.sqlite3');src.backup(dest);src.close();dest.close()
        arc=ContextArchive(tmp);context=arc.verify()
        versions=dict(arc.db.execute('SELECT source,COUNT(*) FROM versions GROUP BY source'))
        calendar=[]
        for raw in arc.db.execute("SELECT raw FROM versions WHERE source='calendar'"):
            c=json.loads(raw[0]);calendar.append(dict(export_utc=c['retrieved_at_utc'],offset=c['server_minus_gmt_seconds']))
        arc.close()
    offsets={a['candidate_offset_seconds'] for b in batch_anchors for a in b['anchors']}
    corroborated=len(batch_anchors)>=2 and len(calendar)>=2 and len(offsets)==1 and all(n['status']=='NTP_STATUS_ACCEPTABLE' for n in ntp) and bool(ntp) and not clock_steps
    if corroborated:
        offset=next(iter(offsets));corroborated=all(c['offset']==offset for c in calendar) and sum(len(b['anchors'])>=3 for b in batch_anchors)>=2
    else:offset=None
    return dict(at=datetime.now(timezone.utc).isoformat(),integrity_errors=errors,receipt_chain_head=receipt_hash,
        context_integrity=context,context_versions=versions,journal_versions=journal_counts,streams=totals,
        invalid_latest_snapshots=snapshot_bad,production_sources_unchanged=all(production_unchanged.values()),
        clock=dict(status='FORWARD_OFFSET_CORROBORATED' if corroborated else 'INSUFFICIENT_CORROBORATION',
            offset_seconds=offset if corroborated else None,observed_from=batch_anchors[0]['at'] if batch_anchors else None,
            observed_until=batch_anchors[-1]['at'] if batch_anchors else None,ntp=ntp,clock_discontinuities=clock_steps,
            raw_data_unchanged=True,exact_millisecond_utc_certified=False,valid_outside_observed_span=False,
            historical_dst_mapping_verified=False,normalized_bundle_accepted=False),
        prospective_replay_completed=False,edge_confirmed=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    result=audit(a.root);a.out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(integrity_errors=result['integrity_errors'],ticks=sum(s['ticks'] for s in result['streams'].values()),
        streams=len(result['streams']),clock=result['clock']['status'],production_sources_unchanged=result['production_sources_unchanged'])))
