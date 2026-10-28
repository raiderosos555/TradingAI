"""Frozen alternative-data diagnostics. Lagged Last markouts, NOT as-of P&L."""
import argparse,csv,json,sys
from pathlib import Path
from datetime import datetime,timezone
from collections import Counter
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'edge_program'))
import experiments as E

DEFS=[('V','US500','VIX'),('V','US100','VIX'),('T','US500','VIX9D'),
      ('T','US100','VIX9D'),('O','OIL','OVX'),('G','GOLD','GVZ')]

def load_index(path):
    rows=list(csv.DictReader(path.read_text(encoding='utf-8-sig').splitlines()))
    field='CLOSE' if 'CLOSE' in rows[0] else path.stem
    data=[]
    for row in rows:
        t=datetime.strptime(row['DATE'],'%m/%d/%Y').replace(tzinfo=timezone.utc).timestamp()
        v=float(row[field]);assert np.isfinite(v) and v>0
        data.append((t,v))
    # Do not silently repair unordered or duplicated dates.
    a=np.array(data);assert (np.diff(a[:,0])>0).all()
    return a,dict(rows=len(rows),first=rows[0]['DATE'],last=rows[-1]['DATE'],sha256=E.sha(path))

def feature_at(indices,symbol,family,raw_time,lag_days):
    a=indices[symbol];cut=raw_time-(lag_days*86400+3*3600)
    k=np.searchsorted(a[:,0],cut,side='right')-1
    if k<60:return None
    age=(raw_time-a[k,0])/86400
    if age>(7 if lag_days==3 else 11):return None
    if family=='V':flag=a[k,1]<=np.median(a[k-60:k,1])
    elif family=='T':
        b=indices['VIX'];j=np.searchsorted(b[:,0],a[k,0])
        if j>=len(b) or b[j,0]!=a[k,0]:return None
        flag=a[k,1]<=b[j,1]
    else:flag=a[k,1]>a[k-5,1]
    return bool(flag),float(a[k,0]),float(age)

def rows_for(a,f,indices,family,symbol,spread,lag):
    # Reuse the frozen grid and identical cost thresholds, not old test results.
    rows,c=E.windows(a,f,'T','ROC',spread);out=[];rej=Counter()
    bytime={float(t):i for i,t in enumerate(a['t'])}
    for row in rows:
        gate=feature_at(indices,symbol,family,row['signal_raw'],lag)
        if gate is None:rej['missing_or_stale_index']+=1;continue
        keep,index_t,age=gate;r=row.copy();i=bytime[r['signal_raw']]
        # Before the filter the candidate and benchmark are identical ROC20.
        for key in ('direction','gross','cost','net','stress'):r[key]*=keep
        r['delta']=r['net']-r['base']
        pricekeep=bool(f['volhigh'][i])
        r.update(price_filter=r['base']*pricekeep,index_date=index_t,index_age=age,keep=keep)
        out.append(r)
    return out,dict(**c,**rej,accepted_with_index=len(out))

def run(root,out):
    if out.exists():raise RuntimeError('Refuse overwrite')
    here=Path(__file__).resolve().parent;indices={};coverage={}
    for symbol in ('VIX','VIX9D','VVIX','OVX','GVZ'):
        indices[symbol],coverage[symbol]=load_index(here/'private/samples-v1'/f'{symbol}.csv')
    old=E.read(root/'research/edge_program/private/results-v1.json')
    expected={r['path']:r['sha256'] for r in old['source_hashes']}
    tests={};allrows={};filters={};regimes={};hashes=[]
    for fam,alias,symbol in DEFS:
        a,record=E.load(root,alias,'D1');assert record['sha256']==expected[record['path']]
        hashes.append(record);f=E.features(a)
        for lag in (3,7):
            key=f'{fam}/{alias}/{symbol}/lag{lag}'
            rows,counts=rows_for(a,f,indices,fam,symbol,old['spreads'][alias],lag)
            allrows[key]=rows;filters[key]=counts;tests[key]={}
            for period in ('early','late','all'):
                subset=[r for r in rows if period=='all' or r['period']==period]
                s=E.summary(subset,True)
                if subset:
                    s['price_filter']=float(np.mean([r['price_filter'] for r in subset]))
                    s['delta_price_filter']=s['mean']-s['price_filter']
                    s['min_index_age']=min(r['index_age'] for r in subset)
                tests[key][period]=s
            regimes[key]={f'{kind}/{value}':E.summary([r for r in rows if r[kind]==value])
                for kind,values in [('vol',('low','high')),('trend',('up','down'))] for value in values}
    primary=[k for k in tests if k.endswith('lag3')]
    for field in ('p_delta','p_thinning','p_placebo'):
        for k,p in zip(primary,E.holm([tests[k]['late'][field] for k in primary])):
            tests[k]['late'][field+'_holm6']=p
    # Include the 36 earlier price-only trials and all 12 new diagnostics.
    pooled=[t['late']['p_delta'] for t in old['tests'].values()]+[t['late']['p_delta'] for t in tests.values()]
    for k,p in zip(tests,E.holm(pooled)[36:]):tests[k]['late']['p_delta_holm48']=p
    result=dict(version='alternative-data-v1',at=datetime.now(timezone.utc).isoformat(),coverage=coverage,
        source_hashes=hashes,code_hash=E.sha(Path(__file__)),registry_sha256=E.sha(here/'HYPOTHESES.md'),
        tests=tests,rows=allrows,filters=filters,regimes=regimes,
        real_net_backtest=False,as_of_verified=False,independent_confirmation=False,orders_sent=0)
    out.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'comparisons':len(tests),'primary':len(primary),
        'significant_holm6':sum(tests[k]['late']['p_delta_holm6']<.05 for k in primary),
        'coverage':coverage}))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();run(a.root,a.out)
