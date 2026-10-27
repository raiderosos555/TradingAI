"""Compare actually observed new fills to raw ticks; no hypothetical orders."""
import gzip,json,sqlite3
from pathlib import Path
from datetime import datetime
from collector import ROOT,A
from quality import executable

root=ROOT/'state/forward_validation/cohort-20261026-v1';status=json.loads((root/'status.json').read_text())
complete=[p for p in sorted((root/'batches').glob('*/broker.json')) if (p.parent/'manifest.json').exists() and (p.parent/'result.json').exists() and json.loads((p.parent/'result.json').read_text()).get('status')=='COMPLETED']
last=json.loads(complete[-1].read_text());first=json.loads(complete[0].read_text())
old={d['ticket'] for d in first['deals'] or []};deals=[d for d in last['deals'] or [] if d['ticket'] not in old and d['type'] in (0,1)]
db=sqlite3.connect((root/'evidence.sqlite3').as_uri()+'?mode=ro',uri=True)
operations=[json.loads(r[0]) for r in db.execute("SELECT raw FROM journal_versions WHERE source='operations'")]
events=[json.loads(r[0]) for r in db.execute("SELECT raw FROM journal_versions WHERE source='events'")]
db.close();results=[]
for deal in deals:
    t=deal['time_msc'];symbol=deal['symbol'];near=[]
    for result_path in sorted((root/'batches').glob('*/result.json')):
        folder=result_path.parent
        if not (folder/'manifest.json').exists():continue
        item=json.loads(result_path.read_text())['symbols'].get(symbol,{})
        if item.get('status')!='CAPTURED' or item['end_raw_ms']<t-2000 or item['start_raw_ms']>t+2000:continue
        with gzip.open(folder/(symbol+'.ticks.json.gz'),'rt',encoding='utf-8') as f:rows=json.load(f)
        near.extend(dict(raw_tick=r,source=str(folder.relative_to(root)),provider_response_index=i) for i,r in enumerate(rows)
            if item['start_raw_ms']<=r['time_msc']<item['end_raw_ms'] and abs(r['time_msc']-t)<=2000)
    matching=[]
    for op in operations:
        result=json.loads(op['result']) if op['result'] else {}
        if result.get('order')==deal['order'] and op['status']=='CONFIRMED':matching.append(op)
    op=matching[-1] if matching else None
    side='ask' if deal['type']==0 else 'bid'
    same=[r for r in near if r['raw_tick']['time_msc']==t]
    before=[r for r in near if r['raw_tick']['time_msc']<=t]
    after=[r for r in near if r['raw_tick']['time_msc']>t]
    price_matches=[r for r in same if executable(r['raw_tick']) and abs(r['raw_tick'][side]-deal['price'])<1e-8]
    row=dict(deal=deal,execution_side=side,same_millisecond_ticks=same,
        price_matches_at_same_ms=price_matches,nearest_raw_tick_at_or_before=before[-1] if before else None,
        first_raw_tick_after=after[0] if after else None,
        exact_same_ms_event_order_known=False,stale_price_substituted=False,
        fees_observed=sum(deal[k] for k in ('commission','swap','fee')),operation=op,
        inference='Observed match only; not a calibrated slippage distribution or a strategy backtest')
    if op:
        payload=json.loads(op['payload']);request=payload['request']
        row['fill_minus_requested_price']=None if request.get('price') is None else deal['price']-request['price']
        row['requested_price_available']=request.get('price') is not None
        metadata=payload.get('metadata',{});reference=metadata.get('entry_reference')
        row['fill_minus_risk_entry_reference']=None if reference is None else deal['price']-reference
        live_quote=metadata.get('broker_quote',{});reference_ms=live_quote.get('broker_raw_time_msc')
        reference_rows=[r for r in near if r['raw_tick']['time_msc']==reference_ms]
        row['history_at_risk_quote_timestamp']=reference_rows
        row['risk_quote_has_exact_bid_ask_match_in_history']=any(all(r['raw_tick'][k]==live_quote.get(k) for k in ['bid','ask']) for r in reference_rows)
        row['intent_host_utc']=op['at']
        row['broker_raw_minus_intent_host_seconds']=t/1000-datetime.fromisoformat(op['at']).timestamp()
        confirmed=[e for e in events if e['kind']=='confirmed' and json.loads(e['payload']).get('id')==op['id']]
        row['confirmed_host_utc']=confirmed[-1]['at'] if confirmed else None
    results.append(row)
out=dict(observed_at=status['at'],source='Actual DEMO broker history joined to archived operations and raw ticks',
    last_complete_broker_snapshot=last['received_at'],
    retrospective_calibration_only=True,prospective_validation_window=False,orders_sent_by_analysis=0,results=results)
(A/'observed-fill-comparison.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps([dict(symbol=r['deal']['symbol'],ticket=r['deal']['ticket'],same_ms_matches=len(r['price_matches_at_same_ms']),
    fill_minus_requested_price=r.get('fill_minus_requested_price'),fees_observed=r['fees_observed'],
    broker_raw_minus_intent_host_seconds=r.get('broker_raw_minus_intent_host_seconds')) for r in results]))
