"""Read-only post-window audit. No strategy search, MT5 import or order API."""
import argparse,gzip,hashlib,json,sqlite3,sys
from datetime import datetime,timezone
from pathlib import Path
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
sys.path.insert(0,str(ROOT/'research/forward_validation'))
from verify_capture import audit

def stamp():return datetime.now(timezone.utc).isoformat()
def gaps(intervals,start,end):
    cursor=start;missing=[]
    for a,b in sorted(intervals):
        a=max(a,start);b=min(b,end)
        if b<=a:continue
        if a>cursor:missing.append([cursor,a])
        cursor=max(cursor,b)
    if cursor<end:missing.append([cursor,end])
    return missing
def ready_time(now,end):return now>=end
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()

def run(root,out):
    root=root.resolve();protocol=json.loads((root/'protocol.v1.json').read_text());window=protocol['first_window']
    start=datetime.fromisoformat(window['start_utc']);end=datetime.fromisoformat(window['end_utc'])
    out.mkdir(parents=True,exist_ok=True)
    if not ready_time(datetime.now(timezone.utc),end):
        result=dict(at=stamp(),status='PENDING_WINDOW_END',window=window,
            operational_resilience='NO_GO_UNDEPLOYED_CANDIDATE',data_completeness='PENDING',backtest_reliability='NO_GO',
            reason='Do not interpret a partial future window as complete',edge_confirmed=False)
        (out/'readiness.json').write_text(json.dumps(result,indent=2));return result
    if (out/'REPORT.md').exists():raise RuntimeError('Use a new output directory; preserve prior audit')
    try:
        integrity=audit(root)
    except Exception as exc:
        integrity=dict(status='INTEGRITY_AUDIT_FAILED',at=stamp(),integrity_errors=[type(exc).__name__+': '+str(exc)],
            note='Failure is not a clean audit; do not accept this dataset')
    (out/'integrity.json').write_text(json.dumps(integrity,indent=2))
    config=json.loads((root/'frozen/effective-config.json').read_text())
    symbols=[s['broker'] for s in config['symbols'].values()]+['USDPLN','USDPLN.pro']
    streams={s:dict(intervals=[],ticks=0,invalid_quotes=0,trade_only_invalid=0,offsets=[],empty_intervals=0) for s in symbols}
    warmup={};initial=None;failed=[];hash_errors=[];seen_manifests={}
    db=sqlite3.connect((root/'evidence.sqlite3').as_uri()+'?mode=ro',uri=True)
    receipts=[json.loads(row[0]) for row in db.execute("SELECT payload FROM receipts WHERE kind='BATCH' ORDER BY seq")]
    ntp=[json.loads(row[0]) for row in db.execute("SELECT payload FROM receipts WHERE kind='HOST_CLOCK' AND at>=? AND at<? ORDER BY seq",(start.isoformat(),end.isoformat()))]
    journal=[]
    for raw, in db.execute("SELECT raw FROM journal_versions WHERE source='events'"):
        row=json.loads(raw)
        if start<=datetime.fromisoformat(row['at'])<end:journal.append(row)
    db.close()
    for receipt in receipts:
        folder=root/receipt['path'];m=folder/'manifest.json'
        if sha(m)!=receipt['manifest_sha256']:hash_errors.append(str(m));continue
        manifest=json.loads(m.read_text());request=json.loads((folder/'request.json').read_text())
        received=datetime.fromisoformat(request['requested_at'])
        if receipt['status']!='COMPLETED':
            if start<=received<end:failed.append(receipt)
            continue
        r=json.loads((folder/'result.json').read_text())
        relevant=False
        for s,item in r['symbols'].items():
            if item.get('status')!='CAPTURED' or s not in streams:continue
            offset=item.get('retrieval_offset')
            if not isinstance(offset,int):continue
            lo=item['start_raw_ms']-offset*1000;hi=item['end_raw_ms']-offset*1000
            if hi<=start.timestamp()*1000 or lo>=end.timestamp()*1000:continue
            relevant=True;t=streams[s];t['intervals'].append([lo,hi]);t['offsets'].append(offset)
            with gzip.open(folder/(s+'.ticks.json.gz'),'rt',encoding='utf-8') as f:rows=json.load(f)
            core=[x for x in rows if item['start_raw_ms']<=x['time_msc']<item['end_raw_ms'] and start.timestamp()*1000<=x['time_msc']-offset*1000<end.timestamp()*1000]
            t['ticks']+=len(core);t['empty_intervals']+=not core
            for x in core:
                invalid=not(0<x['bid']<=x['ask']);t['invalid_quotes']+=invalid
                t['trade_only_invalid']+=invalid and bool(x['flags']&24) and not bool(x['flags']&6)
        if received<=start:
            for path in folder.glob('*.bars.json'):
                data=json.loads(path.read_text());observed=datetime.fromisoformat(data['H1']['received_at'])
                if observed<=start:warmup[path.name.removesuffix('.bars.json')]=dict(path=str(path),received_at=data['H1']['received_at'],H1=len(data['H1']['rows'] or []))
            broker=json.loads((folder/'broker.json').read_text())
            if datetime.fromisoformat(broker['received_at'])<=start:initial=broker
        if relevant or received<=start and start.timestamp()-received.timestamp()<7200:
            for name,expected in manifest.items():
                if sha(folder/name)!=expected:hash_errors.append(str(folder/name))
            seen_manifests[str(m.relative_to(root))]=receipt['manifest_sha256']
    for s,t in streams.items():
        t['missing_requested_ranges_under_candidate_offset']=gaps(t.pop('intervals'),int(start.timestamp()*1000),int(end.timestamp()*1000))
        t['retrieval_offsets']=sorted(set(t.pop('offsets')))
    db=sqlite3.connect((root/'context/context.sqlite3').as_uri()+'?mode=ro',uri=True)
    context={}
    for source in ['calendar','news','runtime','effective_config']:
        rows=db.execute('SELECT not_before_utc,payload,version_id FROM observations WHERE source=? AND not_before_utc>=? AND not_before_utc<? ORDER BY seq',(source,start.isoformat(),end.isoformat())).fetchall()
        prior=db.execute('SELECT not_before_utc,payload,version_id FROM observations WHERE source=? AND not_before_utc<? ORDER BY seq DESC LIMIT 1',(source,start.isoformat())).fetchone()
        times=[datetime.fromisoformat(x[0]).timestamp() for x in ([prior] if prior else [])+rows]+[end.timestamp()]
        context[source]=dict(observations=len(rows),versions=len({x[2] for x in rows if x[2]}),prior_observation=prior[0] if prior else None,
            largest_observation_gap_seconds=max([b-a for a,b in zip(times,times[1:])],default=None),
            non_observed=sum(json.loads(x[1]).get('status')!='OBSERVED' for x in rows),
            exact_engine_input_proven=False)
    db.close()
    conditional_coverage=all(not t['missing_requested_ranges_under_candidate_offset'] for t in streams.values())
    result=dict(at=stamp(),window=window,status='AUDITED_NOT_BACKTESTED',streams=streams,context=context,
        initial_broker_snapshot=initial,warmup=warmup,failed_batches=failed,window_manifest_errors=hash_errors,
        manifest_cutoff=seen_manifests,journal_events=len(journal),host_clock_observations=ntp,
        conditional_requested_range_coverage=conditional_coverage,
        operational_resilience='NO_GO_UNDEPLOYED_CANDIDATE',data_completeness='NO_GO_PENDING_UTC_AND_FEED_ACCEPTANCE',
        backtest_reliability='NO_GO',edge_confirmed=False,strategy_optimized=False,
        remaining=['Retrieval offsets are candidates, not an accepted UTC segment map',
            'Complete API request ranges do not certify complete tick feed; silence needs session context',
            'Live decision quote differs from history in calibration evidence; execution parity unresolved',
            'Same-millisecond cross-stream order, exact decision context, costs and initial positions still require explicit replay input validation'])
    (out/'readiness.json').write_text(json.dumps(result,indent=2))
    text=f"""# Gotowość okna 27.10 do replay

Audyt: {result['at']}. Okno: 08:00–16:00 UTC / 09:00–17:00 Europe/Warsaw.

- Odporność aktywnego DEMO: **NO-GO** — poprawka i nadzór nie zostały wdrożone.
- Kompletność danych: **NO-GO do uznania za kompletny zbiór UTC**. Pokrycie żądanych przedziałów przy kandydackim offsecie: {conditional_coverage}.
- Wiarygodność pełnego backtestu: **NO-GO** — patrz konkretne braki w readiness.json.
- Błędy hashy w wybranych paczkach: {len(hash_errors)}; globalne błędy integralności: {len(integrity['integrity_errors'])}.
- Ticki w wybranych przedziałach: {sum(x['ticks'] for x in streams.values())}; nieudane paczki w oknie: {len(failed)}.

Nie uruchomiono optymalizacji, nie promowano strategii, nie policzono pozornego wyniku przy brakujących danych. Decyzje NO-GO dotyczą udokumentowanego braku akceptacji czasu i wykonania, nie rentowności. Część nieudanych pobrań mogła zostać uzupełniona; sam błąd pobrania nie jest dowodem luki w finalnym pliku. Surowe dane i hashe pozostają zachowane.

Pełne dane, pokrycie każdego strumienia, wersje kontekstu, stan początkowy oraz świece: readiness.json. Integralność archiwum i dowody czasu: integrity.json.
"""
    (out/'REPORT.md').write_text(text,encoding='utf-8');return result

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--root',type=Path,default=ROOT/'state/forward_validation/cohort-20261026-v1');p.add_argument('--out',type=Path,required=True);a=p.parse_args()
    r=run(a.root,a.out);print(json.dumps({k:r[k] for k in ['status','operational_resilience','data_completeness','backtest_reliability']}))
