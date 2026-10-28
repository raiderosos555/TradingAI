"""Frozen COT incremental-information experiment. Offline; no broker P&L.
Latest-vintage reference-price markouts, not a point-in-time certification.
"""
import bisect, hashlib, html, json, re
from collections import Counter
from datetime import date, timedelta, datetime, timezone
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent
PRIVATE=HERE/'private'; PACKAGE=PRIVATE/'package-v1'
EXCLUSIONS=[('2013-10-01','2013-11-15'),('2018-12-18','2019-03-29'),
            ('2023-01-24','2023-04-14'),('2025-09-30','2025-12-31')]
EXCLUSIONS=[(date.fromisoformat(a).toordinal(),date.fromisoformat(b).toordinal()) for a,b in EXCLUSIONS]
SEED=20261029

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def iso(n):return date.fromordinal(int(n)).isoformat()
def put(p,x):
    if p.exists():raise RuntimeError('Refuse overwrite: '+str(p))
    p.write_text(json.dumps(x,indent=2,allow_nan=False),encoding='utf-8')

def load_prices(path):
    text=path.read_text(encoding='utf-8',errors='strict')
    assert '</html>' in text.lower(), 'Incomplete HTML is not accepted'
    pairs=re.findall(r'<tr[^>]*>\s*<th[^>]*>\s*(\d{1,2}-[A-Z]{3}-\d{2})\s*</th>\s*<td[^>]*>\s*([\d.]+|ND)\s*</td>',text,re.S)
    assert len(pairs)>5000
    months={x:i+1 for i,x in enumerate(('JAN','FEB','MAR','APR','MAY','JUN','JUL','AUG','SEP','OCT','NOV','DEC'))}
    out={};missing=[]
    for ds,v in pairs:
        day,month,year=ds.split('-');d=date(2000+int(year),months[month],int(day))
        if not 2010<=d.year<=2025:continue
        if v=='ND':missing.append(d.isoformat());continue
        n=d.toordinal();assert n not in out;out[n]=float(v);assert 0<out[n]<10
    assert len(out)>3900
    return out,dict(rows=len(out),first=iso(min(out)),last=iso(max(out)),ND=len(missing),missing_dates=missing)

def load_cot():
    result={};audit={}
    for ds in ('tff','disagg'):
        rows=json.loads((PACKAGE/(ds+'.raw')).read_text(encoding='utf-8'));assert len(rows)<4000
        for r in rows:
            assert r['futonly_or_combined']=='FutOnly'
            code=r['cftc_contract_market_code'];n=date.fromisoformat(r['report_date_as_yyyy_mm_dd'][:10]).toordinal()
            L='lev_money_positions_long' if ds=='tff' else 'm_money_positions_long_all'
            S='lev_money_positions_short' if ds=='tff' else 'm_money_positions_short_all'
            oi=int(r['open_interest_all']);long=int(r[L]);short=int(r[S])
            assert oi>0 and 0<=long<=oi and 0<=short<=oi
            x=result.setdefault(code,{});assert n not in x
            x[n]={'share':(long-short)/oi,'oi':oi,'long':long,'short':short,'dataset':ds}
    for code,data in result.items():
        dates=sorted(data);gaps=np.diff(dates)
        audit[code]=dict(rows=len(dates),first=iso(dates[0]),last=iso(dates[-1]),
          max_gap_days=int(gaps.max()),gap_counts={str(k):int(v) for k,v in Counter(gaps.tolist()).items()},
          non_tuesday=sum(date.fromordinal(n).weekday()!=1 for n in dates),
          unique=True,dataset=data[dates[0]]['dataset'],first_publication_field=False)
    return result,audit

def excluded(n):return any(a<=n<=b for a,b in EXCLUSIONS)
def part(n):
    y=date.fromordinal(n).year
    return 'discovery' if y<=2017 else 'walk_forward' if y<=2021 else 'confirmation'

def cot_signal(data,decision,lag):
    dates=sorted(data);j=bisect.bisect_right(dates,decision-lag)-1
    if j<4:return None,'warmup'
    window=dates[j-4:j+1]
    if decision-dates[j]>lag+7:return None,'stale_cot'
    if any(excluded(n) for n in window):return None,'publication_disruption'
    if not (26<=window[-1]-window[0]<=30) or any(not 6<=b-a<=8 for a,b in zip(window,window[1:])):return None,'cot_gap'
    return (data[dates[j]]['share']-data[dates[j-4]]['share'],window),None

def previous(dates,cutoff,tolerance=7):
    j=bisect.bisect_right(dates,cutoff)-1
    return dates[j] if j>=0 and cutoff-dates[j]<=tolerance else None

def build_rows(prices,cot,weeks,lag):
    dates=sorted(prices);rows=[];skips=Counter();vol_history=[]
    start=date(2011,1,5).toordinal();end=date(2025,12,31).toordinal()
    for e in range(start,end+1,7*weeks):
        x=e+7*weeks
        if x>end:skips['end_of_sample']+=1;continue
        if part(e)!=part(x):skips['split_boundary']+=1;continue
        if e not in prices or x not in prices:skips['missing_reference_price']+=1;continue
        a=previous(dates,e-14);b=previous(dates,e-14-182)
        if a is None or b is None:skips['price_warmup']+=1;continue
        direction=int(np.sign(prices[a]/prices[b]-1))
        cotvalue,reason=cot_signal(cot,e,lag)
        if reason:skips[reason]+=1;continue
        delta,window=cotvalue
        selected=int(direction*delta>0);move=(prices[x]/prices[e]-1)*10000
        cd=sorted(cot);old_index=cd.index(window[-1])-52
        old,reason_old=(None,'warmup') if old_index<4 else cot_signal(cot,cd[old_index]+lag,lag)
        placebo=None if reason_old else int(direction*old[0]>0)
        historical=[prices[n] for n in dates if a-90<=n<=a]
        vol=float(np.std(np.diff(np.log(historical)),ddof=1)) if len(historical)>=40 else None
        regime='unknown' if vol is None or len(vol_history)<20 else ('high' if vol>np.median(vol_history) else 'low')
        if vol is not None:vol_history.append(vol)
        yr=date.fromordinal(e).year;quarter=(date.fromordinal(e).month-1)//3+1
        rows.append(dict(entry=iso(e),exit=iso(x),price_signal=iso(a),price_start=iso(b),
            cot_start=iso(window[0]),cot_end=iso(window[-1]),cot_delta=delta,
            direction=direction,selected=selected,placebo_selected=placebo,
            reference_entry=prices[e],reference_exit=prices[x],move_bps=move,
            A=direction*move,B=selected*direction*move,part=part(e),year=yr,
            block=f'{yr}Q{quarter}',regime=regime,weeks=weeks,lag=lag))
    return rows,dict(skips)

def inference(values,labels,seed=SEED):
    v=np.asarray(values,dtype=float);labels=np.asarray(labels);groups=sorted(set(labels))
    if len(groups)<3:return dict(blocks=len(groups),ci=None,p=None)
    sums=np.array([v[labels==g].sum() for g in groups]);counts=np.array([(labels==g).sum() for g in groups])
    rng=np.random.default_rng(seed);ix=rng.integers(0,len(groups),(4999,len(groups)))
    boot=sums[ix].sum(axis=1)/counts[ix].sum(axis=1);m=float(v.mean())
    centered=(sums-counts*m)[ix].sum(axis=1)/counts[ix].sum(axis=1)
    return dict(blocks=len(groups),ci=np.quantile(boot,[.025,.975]).tolist(),
                p=float((1+(centered>=m).sum())/5000))

def markout_stats(a):
    a=np.asarray(a);cum=np.r_[0,np.cumsum(a)];loss=-a[a<0].sum()
    return dict(mean=float(a.mean()),sum=float(a.sum()),
       positive_negative_ratio=float(a[a>0].sum()/loss) if loss else None,
       max_sum_drawdown_bps=float(np.max(np.maximum.accumulate(cum)-cum)))

def summarize(rows):
    if not rows:return {'n':0}
    a=np.array([r['A'] for r in rows]);b=np.array([r['B'] for r in rows]);mask=np.array([r['selected'] for r in rows]);active=np.array([abs(r['direction']) for r in rows]);exposure=float(mask.mean())
    stat=dict(n=len(rows),selected=int(mask.sum()),exposure=exposure,quarters=len(set(r['block'] for r in rows)),years=len(set(r['year'] for r in rows)),
      A=markout_stats(a),B=markout_stats(b),delta=float(np.mean(b-a)),
      exposure_matched_delta=float(np.mean(b-exposure*a)),
      long_only=float(np.mean([r['move_bps'] for r in rows])),short_only=-float(np.mean([r['move_bps'] for r in rows])),cash=0,
      inference=inference(b-a,[r['block'] for r in rows]),
      annual_ci=inference(b-a,[r['year'] for r in rows])['ci'])
    stat['hurdles']={}
    for label,rt,weekly in [('zero',0,0),('base',5,2),('stress',15,5)]:
        cost=rt+weekly*rows[0]['weeks'];aa=a-cost*active;bb=b-cost*mask
        stat['hurdles'][label]=dict(cost_per_active_opportunity=cost,A=float(aa.mean()),B=float(bb.mean()),delta=float((bb-aa).mean()),
          exposure_matched_delta=float((bb-exposure*aa).mean()))
    # Exposure exactly matched within every year AND direction; blocks of mask
    # are rotated, preserving serial clustering within that stratum.
    rng=np.random.default_rng(SEED);groups={}
    for i,r in enumerate(rows):groups.setdefault((r['year'],r['direction']),[]).append(i)
    distribution=[]
    for _ in range(999):
        candidate=mask.copy()
        for inds in groups.values():
            candidate[inds]=np.roll(mask[inds],int(rng.integers(1,len(inds))) if len(inds)>1 else 0)
        distribution.append(float(np.mean(candidate*a)))
    stat['random_filter']=dict(mean=float(np.mean(distribution)),ci=np.quantile(distribution,[.025,.975]).tolist(),
        upper_tail_p=float((1+sum(v>=b.mean() for v in distribution))/1000))
    subset=[r for r in rows if r['placebo_selected'] is not None]
    stat['lag52_placebo']=dict(n=len(subset),B=float(np.mean([r['B'] for r in subset])) if subset else None,
        placebo=float(np.mean([r['A']*r['placebo_selected'] for r in subset])) if subset else None)
    return stat

def holm(p):
    names=sorted(p,key=lambda k:p[k]);out={};running=0
    for i,k in enumerate(names):running=max(running,min(1,p[k]*(len(names)-i)));out[k]=running
    return out

def main():
    locked=json.loads((PRIVATE/'protocol-lock.json').read_text(encoding='utf-8'))
    assert sha(HERE/'COT_EXPERIMENT_PROTOCOL.md')==locked['sha256']
    data,cot_audit=load_cot();price_audit={};results={};allrows={};skips={}
    for market,code,file in [('EURUSD','099741','fed_eur_complete.raw'),('GBPUSD','096742','fed_gbp_complete.raw')]:
        prices,price_audit[market]=load_prices(PACKAGE/file)
        for lag in (14,28):
            for weeks in (1,4):
                key=f'{market}/w{weeks}/lag{lag}';rows,skips[key]=build_rows(prices,data[code],weeks,lag)
                allrows[key]=rows;results[key]={p:summarize([r for r in rows if p=='all' or r['part']==p]) for p in ['discovery','walk_forward','confirmation','all']}
                results[key]['annual']={str(y):summarize([r for r in rows if r['year']==y]) for y in sorted(set(r['year'] for r in rows))}
                results[key]['regimes']={x:summarize([r for r in rows if r['regime']==x]) for x in ['high','low','unknown']}
                results[key]['directions']={str(d):summarize([r for r in rows if r['direction']==d]) for d in [-1,1]}
    adjusted=holm({k:v['confirmation']['inference']['p'] for k,v in results.items()})
    for k in results:results[k]['confirmation']['holm8']=adjusted[k]
    hashes={p.name:sha(p) for p in PACKAGE.glob('*.raw')}
    result=dict(at=datetime.now(timezone.utc).isoformat(),protocol_hash=locked['sha256'],code_hash=sha(Path(__file__)),source_hashes=hashes,
                price_audit=price_audit,cot_audit=cot_audit,skips=skips,results=results,rows=allrows,
                point_in_time_verified=False,broker_pnl=False,trials=8,orders_sent=0)
    put(PRIVATE/'experiment-v1.json',result)
    print(json.dumps({'trials':8,'rows':sum(map(len,allrows.values())),'confirmation':{k:{x:v['confirmation'][x] for x in ['n','selected','delta','holm8']} for k,v in results.items()}},indent=2))

if __name__=='__main__':main()
