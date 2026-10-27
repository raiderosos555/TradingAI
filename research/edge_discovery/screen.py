"""Offline Last-price event study and separate observed Bid/Ask markouts.

No broker imports, order APIs, strategy optimization or forward-cohort access.
The output is NOT an executable portfolio backtest or monetary P&L.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import numpy as np
import protocol as P

def read(p):
    return json.loads(p.read_text(encoding='utf-8-sig'))

def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def write(p, obj):
    p.write_text(json.dumps(obj, ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')

def label(t):
    return datetime.fromtimestamp(float(t), timezone.utc).isoformat()[:19]  # raw axis LABEL, not UTC claim

def ema(x, n):
    z = np.empty(len(x)); z[0] = x[0]
    for i in range(1, len(x)):
        z[i] = z[i-1] + 2/(n+1)*(x[i]-z[i-1])
    return z

def features(bars):
    t = np.array([b['broker_raw_time'] for b in bars], dtype=np.int64)
    o,h,l,c = (np.array([b[k] for b in bars], dtype=float) for k in ('open','high','low','close'))
    if np.any(np.diff(t)<=0) or not np.isfinite(np.c_[o,h,l,c]).all():
        raise ValueError('Unordered/invalid source bars')
    if np.any(l>np.minimum(o,c)) or np.any(h<np.maximum(o,c)) or np.any(l<=0):
        raise ValueError('Bad OHLC')
    tr = np.maximum(h-l, np.maximum(abs(h-np.r_[c[0],c[:-1]]), abs(l-np.r_[c[0],c[:-1]])))
    atr = np.full(len(c), np.nan)
    for i in range(13,len(c)): atr[i] = tr[i-13:i+1].mean()
    return dict(t=t,o=o,h=h,l=l,c=c,atr=atr,e20=ema(c,20),e50=ema(c,50),index={int(v):i for i,v in enumerate(t)})

def direction(f, i, family, alias, all_f):
    c,h,l,a = (f[k] for k in ('c','h','l','atr'))
    sign = lambda x: int(np.sign(x))
    move = c[i]-c[i-6]
    if family=='trend': return sign(f['e20'][i]-f['e50'][i])
    if family in ('momentum','volatile_momentum'):
        if family=='volatile_momentum' and a[i]<=1.25*np.median(a[i-100:i]): return 0
        return sign(move) if abs(move)>=0.5*a[i] else 0
    if family=='extreme_reversion':
        move=c[i]-c[i-1]
        return -sign(move) if abs(move)>2*a[i] else 0
    if family in ('breakout','clock_breakout'):
        look=6 if family=='clock_breakout' else 20
        if family=='clock_breakout' and not 14<=((f['t'][i]+3600)//3600)%24<18: return 0
        return 1 if c[i]>h[i-look:i].max() else -1 if c[i]<l[i-look:i].min() else 0
    if family=='false_breakout':
        hi=h[i-20:i].max();lo=l[i-20:i].min()
        up=h[i]>hi; down=l[i]<lo
        if up and down: return 0
        return -1 if up and c[i]<hi else 1 if down and c[i]>lo else 0
    if family=='cross_momentum' and alias in P.LEADERS:
        other,polarity=P.LEADERS[alias]; g=all_f[other];j=g['index'].get(int(f['t'][i]))
        if j is None or j<120 or g['t'][j]-g['t'][j-6]!=21600: return 0
        move=g['c'][j]-g['c'][j-6]
        return polarity*sign(move) if abs(move)>=0.5*g['atr'][j] else 0
    return 0

def events(alias, f, all_f, p95):
    result=[]; blocked={k:0 for k in P.FAMILIES}; rejected={k:0 for k in P.FAMILIES}
    for i in range(120,len(f['t'])-P.HORIZON_HOURS-1):
        ent=i+1; ex=ent+P.HORIZON_HOURS; a=float(f['atr'][i]);t=int(f['t'][ent]);end=int(f['t'][ex])
        # No artificial fills across missing bars/weekends or raw-day boundary.
        eligible=(end-t==14400 and t-f['t'][i]==3600 and t//86400==end//86400 and 6<=t//3600%24<=19)
        for fam in P.FAMILIES:
            d=direction(f,i,fam,alias,all_f)
            if not d: continue
            if not eligible or a<=0: rejected[fam]+=1;continue
            if t<blocked[fam]: continue
            blocked[fam]=end
            gross=d*float(f['o'][ex]-f['o'][ent])/a
            cost=p95/a
            result.append(dict(alias=alias,family=fam,raw_signal=int(f['t'][i]),raw_entry=t,raw_exit=end,
                day=label(t)[:10],month=label(t)[:7],period='early' if label(t)[:10]<P.SPLIT_RAW else 'late',
                direction=d,atr=a,last_entry=float(f['o'][ent]),last_exit=float(f['o'][ex]),gross=gross,
                spread_hurdle=cost,after_hurdle=gross-cost,stress=gross-2*cost-0.05,
                volatility='high' if a>np.median(f['atr'][i-100:i]) else 'low',raw_hour=int(t//3600%24)))
    return result,rejected

def stats(rows, field='after_hurdle'):
    if not rows: return dict(n=0,days=0,mean=None,pf=None,dd=None,ci95=None,ci_familywise=None)
    rows=sorted(rows,key=lambda r:(r['raw_exit'],r['alias']))
    x=np.array([r[field] for r in rows]); eq=np.r_[0,np.cumsum(x)]
    # Equal-event diagnostic curve, NOT a capital/margin/risk-managed portfolio.
    return dict(n=len(x),days=len({r['day'] for r in rows}),mean=float(x.mean()),
        pf=float(x[x>0].sum()/-x[x<0].sum()) if np.any(x<0) else None,
        dd=float((np.maximum.accumulate(eq)-eq).max()),gross=float(np.mean([r['gross'] for r in rows])),
        stress=float(np.mean([r['stress'] for r in rows])),mean_hurdle=float(np.mean([r['spread_hurdle'] for r in rows])))

def uncertainty(rows, calendar, field='after_hurdle'):
    if len(rows)<10 or len(calendar)<10: return dict(ci95=None,ci_familywise=None)
    index={d:i for i,d in enumerate(calendar)};sums=np.zeros(len(calendar));counts=np.zeros(len(calendar))
    for r in rows: sums[index[r['day']]]+=r[field];counts[index[r['day']]]+=1
    rng=np.random.default_rng(P.SEED);n=len(calendar); starts=rng.integers(0,n,(P.BOOTSTRAPS,int(np.ceil(n/P.BLOCK_DAYS))))
    ids=((starts[:,:,None]+np.arange(P.BLOCK_DAYS))%n).reshape(P.BOOTSTRAPS,-1)[:,:n]
    den=counts[ids].sum(1);means=sums[ids].sum(1)[den>0]/den[den>0]
    return dict(ci95=np.quantile(means,[.025,.975]).tolist(),
        ci_familywise=np.quantile(means,[.025/P.TESTS,1-.025/P.TESTS]).tolist(),
        warning='Exploratory percentile block bootstrap; extreme adjusted tails approximate, prior search multiplicity unknown')

def tick_arrays(root, alias, evidence):
    base=root/'research/tick_validation/stage11'
    coll=read(base/'resolved_collection.json')
    inst=next((x for x in coll['instruments'] if x['alias']==alias),None)
    if inst is None:
        base=root/'research/tick_validation/stage5';inst=read(base/'collection.json')
        assert inst['alias']==alias
    parts=[];coverage=[]
    for b in inst['blocks']:
        if b['status'] not in ('OBSERVED','EMPTY'): raise ValueError('Missing requested block')
        folder=base/b['path'];p=folder/'ticks.raw.json.gz';cv=read(folder/'coverage.json')
        with gzip.open(p,'rt',encoding='utf-8') as fd: data=json.load(fd)
        assert len(data)==cv['count']
        arr=np.array([[t['time_msc'],t['bid'],t['ask'],t['last'],t['flags']] for t in data],dtype=float).reshape(-1,5)
        if len(arr) and (arr[:,0].min()<b['start_raw_ms'] or arr[:,0].max()>=b['end_raw_ms']): raise ValueError('Outside request')
        parts.append(arr);coverage.append([b['start_raw_ms'],b['end_raw_ms']]);evidence.append(dict(path=p.relative_to(root).as_posix(),sha256=sha(p)))
        del data
    a=np.concatenate(parts);del parts
    if np.any(np.diff(a[:,0])<0): raise ValueError('Tick time reversal')
    t,bid,ask,last,flags=a.T;flags=flags.astype(np.int64)
    valid=np.isfinite(a).all(axis=1)&(bid>0)&(ask>=bid)
    invalid_time=np.maximum.accumulate(np.where(valid,-1,t))
    bt=np.maximum.accumulate(np.where(valid&((flags&2)>0),t,-1))
    at=np.maximum.accumulate(np.where(valid&((flags&4)>0),t,-1))
    executable=valid&(bt>=invalid_time)&(at>=invalid_time)&(t-bt<=P.TICK_SIDE_MAX_AGE_MS)&(t-at<=P.TICK_SIDE_MAX_AGE_MS)
    return a,executable,dict(alias=alias,ticks=len(a),first_raw=label(t[0]/1000),last_raw=label(t[-1]/1000),
        invalid_quotes=int((~valid).sum()),conservative_ineligible=int((~executable).sum()),
        max_gap_seconds=float(np.diff(t).max()/1000),request_ranges=coverage,
        spread_p50=float(np.median((ask-bid)[valid])),spread_p95=float(np.quantile((ask-bid)[valid],.95)))

def quote(a, executable, target, delay=P.TICK_DELAY_MS):
    lo=np.searchsorted(a[:,0],target+delay,side='left');hi=np.searchsorted(a[:,0],target+delay+P.TICK_MAX_WAIT_MS,side='right')
    good=np.flatnonzero(executable[lo:hi])
    return int(lo+good[0]) if len(good) else None

def tick_markout(a, eligible, row, point, delay=P.TICK_DELAY_MS):
    en=quote(a,eligible,row['raw_entry']*1000,delay);ex=quote(a,eligible,row['raw_exit']*1000,delay)
    if en is None or ex is None: return None
    d=row['direction'];entry=a[en,2 if d>0 else 1];exit_price=a[ex,1 if d>0 else 2]
    value=d*(exit_price-entry)/row['atr']
    midmove=d*((a[ex,1]+a[ex,2])-(a[en,1]+a[en,2]))/2/row['atr']
    return row | dict(entry_bid=float(a[en,1]),entry_ask=float(a[en,2]),exit_bid=float(a[ex,1]),exit_ask=float(a[ex,2]),
        entry_provider_index=en,exit_provider_index=ex,fill_entry_raw_ms=int(a[en,0]),fill_exit_raw_ms=int(a[ex,0]),
        gross=float(midmove),after_hurdle=float(value),spread_hurdle=float(midmove-value),
        stress=float(value-4*point/row['atr']-0.05),break_even_extra_price=float(value*row['atr']),
        broker_fill=False,net_R_verified=None,net_cash_verified=None)

def run(root,out):
    if (out/'results.json').exists(): raise RuntimeError('Preserve prior results; use a new output directory')
    out.mkdir(parents=True,exist_ok=True);evidence=[];data={};fs={};audit=[]
    for s in P.SYMBOLS:
        p=root/f'exchange/research/history-20261024/{s}.json';data[s]=read(p);fs[s]=features(data[s]['bars'])
        evidence.append(dict(path=p.relative_to(root).as_posix(),sha256=sha(p)))
        f=fs[s];audit.append(dict(alias=s,bars=len(f['t']),first_raw=label(f['t'][0]),last_raw=label(f['t'][-1]),
            gaps_over_1h=int((np.diff(f['t'])>3600).sum()),chart_mode='LAST',utc_verified=False))
    source=root/'exchange/research/cost-sample-20261022/summary.json';costs=read(source)['results']
    evidence.append(dict(path=source.relative_to(root).as_posix(),sha256=sha(source)))
    hurdles={s:max(c['p95_spread_points'] for c in costs if c['instrument']==s)*data[s]['contract']['point'] for s in P.SYMBOLS}
    rows=[];reject={}
    for s in P.SYMBOLS:
        part,reject[s]=events(s,fs[s],fs,hurdles[s]);rows+=part
    summaries=[];subgroups=[]
    for family in P.FAMILIES:
        for period in ('early','late'):
            rr=[r for r in rows if r['family']==family and r['period']==period]
            calendar=sorted({label(t)[:10] for f in fs.values() for t in f['t'][120:] if ('early' if label(t)[:10]<P.SPLIT_RAW else 'late')==period})
            summaries.append(dict(family=family,period=period,**stats(rr),**uncertainty(rr,calendar)))
            for s in P.SYMBOLS:
                sr=[r for r in rr if r['alias']==s]
                if sr: subgroups.append(dict(family=family,period=period,alias=s,**stats(sr),**uncertainty(sr,calendar)))
    groups=[]
    for fam in P.FAMILIES:
        for field in ('month','volatility','raw_hour'):
            for v in sorted({r[field] for r in rows}):
                rr=[r for r in rows if r['family']==fam and r[field]==v]
                if rr:groups.append(dict(family=fam,group=field,value=v,**stats(rr)))
    print('H1 event study completed',len(rows),flush=True)
    ticks=[];tick_audit=[];missed=[];latency=[]
    for s in P.SYMBOLS:
        a,eligible,info=tick_arrays(root,s,evidence);tick_audit.append(info)
        for r in rows:
            if r['alias']!=s or r['day']!='2026-10-22':continue
            filled=tick_markout(a,eligible,r,data[s]['contract']['point'])
            if filled is None:missed.append(dict(alias=s,family=r['family'],raw_entry=r['raw_entry'],reason='No fresh executable snapshot within 10s at entry or exit'))
            else:ticks.append(filled)
            delayed=tick_markout(a,eligible,r,data[s]['contract']['point'],1000)
            if delayed:latency.append(delayed)
        print('Ticks completed',s,info['ticks'],flush=True)
        del a,eligible
    result=dict(protocol=P.VERSION,created_utc=datetime.now(timezone.utc).isoformat(),data_class='EXPLORATORY_ONLY',
        protocol_sha256=sha(Path(P.__file__)),script_sha256=sha(Path(__file__)),
        cost_hurdles_price=hurdles,data=audit,tick_data=tick_audit,summary=summaries,by_instrument=subgroups,subgroups=groups,
        tick_summary=[dict(family=fam,**stats([r for r in ticks if r['family']==fam])) for fam in P.FAMILIES],
        latency_1s_summary=[dict(family=fam,**stats([r for r in latency if r['family']==fam])) for fam in P.FAMILIES],
        rejected_windows=reject,tick_missed=missed,source_hashes=evidence,
        monetary_pnl=None,verified_net_R=None,independent_confirmation_observations=0,forward_data_used_for_selection=False)
    write(out/'events.json',rows);write(out/'tick_events.json',ticks);write(out/'latency_events.json',latency);write(out/'results.json',result)
    return result

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();run(args.root,args.out)
