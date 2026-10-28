"""Read-only feasibility metadata. No trading API, no forward P&L selection."""
import json,sqlite3,hashlib,math
from collections import Counter,defaultdict
from datetime import datetime,timezone
from pathlib import Path
import argparse

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def finite(v):return isinstance(v,(float,int)) and not isinstance(v,bool) and math.isfinite(v)
def stamp(t):return datetime.fromtimestamp(t,timezone.utc).isoformat()
def audit(root,out):
    out.mkdir(parents=True,exist_ok=True)
    if (out/'feasibility.json').exists():raise RuntimeError('Preserve prior audit')
    result={'at':datetime.now(timezone.utc).isoformat(),'source_hashes':[],'ohlc':[]}
    for alias in ['GOLD','US500','OIL','EURPLN','EURUSD','GBPUSD','US100']:
        for tf in ['H1','H4','D1']:
            p=root/f'exchange/research/history-20261024/{alias}.json' if tf=='H1' else root/f'research/edge_audit/inputs/{alias}-{tf}.json'
            d=read(p);b=d['bars'];result['source_hashes'].append(dict(path=p.relative_to(root).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
            result['ohlc'].append(dict(alias=alias,tf=tf,n=len(b),first_raw=stamp(b[0]['broker_raw_time']),last_raw=stamp(b[-1]['broker_raw_time']),
              real_volume_nonzero=sum(x.get('real_volume',0)!=0 for x in b),tick_volume_nonzero=sum(x.get('tick_volume',0)!=0 for x in b)))
    context=root/'state/forward_validation/cohort-20261026-v1/context/context.sqlite3'
    c=sqlite3.connect(context.as_uri()+'?mode=ro',uri=True);c.execute('BEGIN')
    result['context_versions']=c.execute('SELECT source,COUNT(*),MIN(first_received_at),MAX(first_received_at) FROM versions GROUP BY source').fetchall()
    events={};version_counts=Counter();article_ids=set()
    for source,at,raw in c.execute("SELECT source,first_received_at,raw FROM versions WHERE source IN ('calendar','news') ORDER BY first_received_at"):
        d=json.loads(raw);version_counts[source]+=1
        if source=='news':
            article_ids.update(x['id'] for x in d.get('items',[]));continue
        for e in d.get('events',[]):
            key=(str(e.get('event_id',e.get('id'))),e.get('start_utc'))
            z=events.setdefault(key,dict(currency=e.get('currency'),start=e.get('start_utc'),first_seen=at,forecast_before=False,
                actual_seen=False,actual_after=False,first_actual=None,unit=e.get('unit'),multiplier=e.get('multiplier')))
            if finite(e.get('forecast')) and datetime.fromisoformat(at).timestamp()<e['start_utc']:z['forecast_before']=True
            if finite(e.get('actual')):
                z['actual_seen']=True
                if z['first_actual'] is None:z['first_actual']=at
                if datetime.fromisoformat(at).timestamp()>=e['start_utc']:z['actual_after']=True
    c.close()
    result['calendar']={'unique_events':len(events),'forecast_observed_before_scheduled_time':sum(x['forecast_before'] for x in events.values()),
        'actual_ever_seen':sum(x['actual_seen'] for x in events.values()),
        'forecast_before_and_actual_after':sum(x['forecast_before'] and x['actual_after'] for x in events.values()),
        'by_currency':dict(Counter(x['currency'] for x in events.values())),
        'units_present':sum(x['unit'] is not None for x in events.values()),
        'note':'Field availability only, not release latency, revision authenticity or usable surprise sample; forward reserved, no returns joined.'}
    ndb=root/'state/news/news.sqlite3';c=sqlite3.connect(ndb.as_uri()+'?mode=ro',uri=True)
    items=[json.loads(x[0]) for x in c.execute('SELECT payload FROM items')];c.close()
    result['news']={s:dict(n=len(v),first_seen=min(x['first_seen_at'] for x in v),last_seen=max(x['first_seen_at'] for x in v),
        earliest_published=min(x['published_at'] for x in v),latest_published=max(x['published_at'] for x in v),
        first_receipt_lag_hours_min=min((datetime.fromisoformat(x['first_seen_at'])-datetime.fromisoformat(x['published_at'])).total_seconds()/3600 for x in v),
        directional_items=sum(x.get('direction')!='UNDETERMINED' for x in v))
        for s in sorted({x['source'] for x in items}) for v in [[x for x in items if x['source']==s]]}
    result['news_archived_unique_ids']=len(article_ids)
    latest=read(root/'state/news/latest.json');result['news_latest_status']=latest.get('sources',latest.get('source_status',{}))
    result['briefings']=[dict(name=p.name,bytes=p.stat().st_size) for p in (root/'exchange/briefing-archive').glob('*') if p.is_file()]
    prior=root/'research/edge_discovery/private/market_inventory.json'
    result['runtime_tf_metadata']=read(prior)['bars'] if prior.exists() else []
    costs=root/'research/edge_discovery/private/demo-readonly.json'
    if costs.exists():
        h=read(costs)['history'];by=defaultdict(list)
        for x in h:
            if x.get('symbol'):by[x['symbol']].append(x)
        result['observed_deal_costs']={s:dict(n=len(v),commission_sum=sum(x.get('commission',0) for x in v),
            fee_sum=sum(x.get('fee',0) for x in v),swap_sum=sum(x.get('swap',0) for x in v),
            note='PLN observed specific DEMO fills; not a tariff for hypothetical historical orders') for s,v in by.items()}
    p=root/'research/replay_readiness/20261027/integrity.json'
    if p.exists():
        d=read(p);result['forward_integrity_error_count']=len(d['integrity_errors']);result['forward_errors_by_type']=dict(Counter(x.split(':')[0] for x in d['integrity_errors']))
    p=root/'research/replay_readiness/20261027/readiness.json'
    if p.exists():
        d=read(p);result['forward_window']={k:d[k] for k in ['window','data_completeness','backtest_reliability','conditional_requested_range_coverage']}
        result['forward_ticks']=sum(x['ticks'] for x in d['streams'].values())
    result['protected_hashes']={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in [*sorted((root/'trading_ai').glob('*.py')),*sorted(root.glob('config*.json'))]}
    (out/'feasibility.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['calendar','news','context_versions','observed_deal_costs']},ensure_ascii=False))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True);a=ap.parse_args();audit(a.root,a.out)
