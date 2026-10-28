"""Fixed indicator ablations on old broker Last bars. Not an execution backtest."""
import argparse,hashlib,json,math,platform
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict
import numpy as np
import protocol as P

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def epoch(s):return datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()

def ewma(x,n,alpha=None):
    """Mean seed of first n finite consecutive inputs, then recursive smoothing."""
    x=np.asarray(x,float);out=np.full(len(x),np.nan);alpha=2/(n+1) if alpha is None else alpha
    valid=np.flatnonzero(np.isfinite(x))
    if len(valid)<n:return out
    start=valid[0];end=start+n-1
    if not np.isfinite(x[start:]).all():raise ValueError('Interior missing feature input')
    out[end]=np.mean(x[start:end+1])
    for i in range(end+1,len(x)):out[i]=alpha*x[i]+(1-alpha)*out[i-1]
    return out

def features(a):
    c=a['close'];h=a['high'];l=a['low'];n=len(c)
    diff=np.r_[np.nan,np.diff(c)]
    gain=ewma(np.maximum(diff,0),P.RSI_N,1/P.RSI_N)
    loss=ewma(np.maximum(-diff,0),P.RSI_N,1/P.RSI_N)
    rsi=np.full(n,np.nan);valid=np.isfinite(gain+loss)
    rsi[valid]=np.divide(100*gain[valid],gain[valid]+loss[valid],out=np.full(valid.sum(),50.),where=(gain[valid]+loss[valid])!=0)
    tr=np.maximum(h-l,np.maximum(np.abs(h-np.r_[np.nan,c[:-1]]),np.abs(l-np.r_[np.nan,c[:-1]])))
    atr=ewma(tr,P.ATR_N,1/P.ATR_N);vol=atr/c
    up=np.r_[np.nan,np.diff(h)];down=np.r_[np.nan,-np.diff(l)]
    plus=np.where((up>down)&(up>0),up,0.);minus=np.where((down>up)&(down>0),down,0.)
    plus[0]=minus[0]=np.nan
    smplus=ewma(plus,P.ADX_N,1/P.ADX_N);smminus=ewma(minus,P.ADX_N,1/P.ADX_N)
    denom=smplus+smminus
    dx=np.divide(100*np.abs(smplus-smminus),denom,out=np.zeros(n),where=denom!=0)
    dx[~np.isfinite(denom)]=np.nan
    adx=ewma(dx,P.ADX_N,1/P.ADX_N)
    ema20=ewma(c,P.TREND_N);macd=ewma(c,12)-ewma(c,26)
    sma=np.full(n,np.nan);roc=np.full(n,np.nan);z=np.full(n,np.nan)
    breakout=np.zeros(n);falsebreak=np.zeros(n);volhigh=np.zeros(n,dtype=bool)
    for i in range(P.TREND_N-1,n):sma[i]=c[i-P.TREND_N+1:i+1].mean()
    roc[P.TREND_N:]=c[P.TREND_N:]/c[:-P.TREND_N]-1
    for i in range(max(P.Z_N,P.DONCHIAN_N),n):
        past=c[i-P.Z_N:i];sd=np.std(past,ddof=1);z[i]=(c[i]-past.mean())/sd if sd else 0
        hi=max(h[i-P.DONCHIAN_N:i]);lo=min(l[i-P.DONCHIAN_N:i])
        if c[i]>hi:breakout[i]=1
        elif c[i]<lo:breakout[i]=-1
        if h[i]>hi and c[i]<hi and l[i]>=lo:falsebreak[i]=-1
        elif l[i]<lo and c[i]>lo and h[i]<=hi:falsebreak[i]=1
    for i in range(P.ATR_N+P.VOL_MEDIAN_N,n):volhigh[i]=vol[i]>np.median(vol[i-P.VOL_MEDIAN_N:i])
    return dict(SMA=np.sign(c-sma),EMA=np.sign(c-ema20),MACD=np.sign(macd),ROC=np.sign(roc),
                RSI=np.where(rsi<P.RSI_LOW,1,np.where(rsi>P.RSI_HIGH,-1,0)),
                Z=np.where(z<-P.Z_LIMIT,1,np.where(z>P.Z_LIMIT,-1,0)),
                breakout=breakout,falsebreak=falsebreak,fade=-np.sign(diff),
                ADX=adx,ATR=atr,volhigh=volhigh,rsi_value=rsi,z_value=z)

def load(root,alias,tf):
    p=root/f'research/edge_audit/inputs/{alias}-{tf}.json';b=read(p)['bars']
    a={k:np.array([x[k] for x in b],float) for k in ['broker_raw_time','open','high','low','close']}
    a['t']=a.pop('broker_raw_time')
    assert np.all(np.diff(a['t'])>0)
    assert all(np.isfinite(v).all() for v in a.values())
    assert all((a[k]>0).all() for k in ['open','high','low','close'])
    assert (a['high']>=np.maximum(a['open'],a['close'])).all()
    assert (a['low']<=np.minimum(a['open'],a['close'])).all()
    return a,dict(path=p.relative_to(root).as_posix(),sha256=sha(p),bars=len(b))

def definitions():
    return ([('T',a,'D1',v) for a in P.ALIASES for v in ('SMA','EMA','MACD')]+
            [('R',a,'H4','RSI') for a in ('EURUSD','GBPUSD','EURPLN')]+
            [('F',a,'H4',v) for a in ('GOLD','OIL','US500','US100') for v in ('ADX','ATR')]+
            [('X',a,'H4','falsebreak') for a in ('GOLD','OIL','US500','US100')])

def signals(f,family,variant):
    if family=='T':return f[variant],f['ROC']
    if family=='R':return f['RSI'],f['Z']
    if family=='F':return f['breakout']*(f['ADX']>=P.ADX_MIN if variant=='ADX' else f['volhigh']),f['breakout']
    if family=='X':return f['falsebreak'],f['fade']*(f['falsebreak']!=0)
    raise ValueError(family)

def windows(a,f,family,variant,spread):
    candidate,benchmark=signals(f,family,variant);h=5 if family=='T' else 2
    rows=[];counts=defaultdict(int)
    for i in range(P.WARMUP,len(a['t']),h):
        if not epoch(P.START)<=a['t'][i]<epoch(P.END):continue
        counts['grid_opportunities']+=1;e=i+1;x=e+h
        if x>=len(a['t']):counts['missing_exit']+=1;continue
        seq=np.diff(a['t'][i:x+1])
        if not ((seq<=4*86400).all() if family=='T' else (seq==14400).all()):
            counts['gap']+=1;continue
        te=a['t'][e];tx=a['t'][x]
        if tx>=epoch(P.END) or a['t'][i]<epoch(P.SPLIT)<=tx:
            counts['boundary']+=1;continue
        d=float(candidate[i]);b=float(benchmark[i])
        if not np.isfinite(d+b):raise ValueError('Uninitialized feature')
        raw=(a['open'][x]/a['open'][e]-1)*10000;cost=spread/a['open'][e]*10000
        stress=2*cost+2+2*(tx-te)/86400
        cg=d*raw;bg=b*raw;cn=cg-abs(d)*cost;bn=bg-abs(b)*cost
        rows.append(dict(signal_raw=float(a['t'][i]),entry_raw=float(te),exit_raw=float(tx),direction=d,base_direction=b,
            period='early' if te<epoch(P.SPLIT) else 'late',block=int((te-epoch('2026-01-05'))//(P.BLOCK_DAYS*86400)),
            vol='high' if f['volhigh'][i] else 'low',trend='up' if f['ROC'][i]>=0 else 'down',
            gross=float(cg),base_gross=float(bg),cost=float(abs(d)*cost),base_cost=float(abs(b)*cost),
            net=float(cn),base=float(bn),delta=float(cn-bn),stress=float(cg-abs(d)*stress),
            base_stress=float(bg-abs(b)*stress),long=float(raw-cost)))
    counts['accepted_opportunities']=len(rows);return rows,dict(counts)

def holm(p):
    out=[1.]*len(p);mx=0.
    for j,k in enumerate(np.argsort(p)):
        mx=max(mx,min(1.,(len(p)-j)*p[k]));out[k]=mx
    return out

def summary(rows,filter_test=False):
    if not rows:return dict(n=0,active=0,base_active=0,blocks=0,p_delta=1.,p_placebo=1.,p_thinning=1.)
    n=len(rows);blocks=sorted({r['block'] for r in rows});nb=len(blocks)
    group=[[r for r in rows if r['block']==b] for b in blocks]
    sums=np.array([sum(r['delta'] for r in g) for g in group]);counts=np.array([len(g) for g in group])
    mean=sum(r['delta'] for r in rows)/n;rng=np.random.default_rng(P.SEED)
    ids=rng.integers(0,nb,(P.BOOT,nb));boot=sums[ids].sum(1)/counts[ids].sum(1)
    p=(1+sum(boot-mean>=mean))/(P.BOOT+1) if nb>=2 else 1.
    gross=np.array([sum(r['gross'] for r in g) for g in group]);cost=sum(r['cost'] for r in rows)
    placebo=(rng.choice([-1,1],(P.BOOT,nb))@gross-cost)/n;net=sum(r['net'] for r in rows)/n
    pp=(1+sum(placebo>=net))/(P.BOOT+1) if nb>=2 else 1.
    thinning=None;pt=1.
    if filter_test:
        samples=np.zeros(P.BOOT)
        for g in group:
            available=np.array([r['base'] for r in g if r['base_direction']])
            k=sum(bool(r['direction']) for r in g)
            if k:
                samples+=np.array([rng.choice(available,k,replace=False).sum() for _ in range(P.BOOT)])
        samples/=n;pt=(1+sum(samples>=net))/(P.BOOT+1);thinning=float(samples.mean())
    active=sum(bool(r['direction']) for r in rows);base_active=sum(bool(r['base_direction']) for r in rows)
    avg=lambda k:float(np.mean([r[k] for r in rows]))
    return dict(n=n,active=active,base_active=base_active,blocks=nb,mean=net,gross=avg('gross'),cost=avg('cost'),
        per_active=float(sum(r['net'] for r in rows)/active) if active else None,
        base=avg('base'),stress=avg('stress'),base_stress=avg('base_stress'),delta=mean,long=avg('long'),
        delta_stress=avg('stress')-avg('base_stress'),
        ci_delta=[float(x) for x in np.quantile(boot,[.025,.975])] if nb>=2 else None,
        p_delta=float(p),p_placebo=float(pp),p_thinning=float(pt),thinning_mean=thinning,
        signal_agreement=float(np.mean([r['direction']==r['base_direction'] for r in rows])))

def run(root,out):
    if out.exists():raise RuntimeError('Refuse overwrite')
    previous=read(root/'research/market_mechanisms/private/feasibility.json')
    expected={h['path']:h['sha256'] for h in previous['source_hashes']}
    data={};feat={};hashes=[]
    for alias in P.ALIASES:
        for tf in ('D1','H4'):
            a,record=load(root,alias,tf);assert expected[record['path']]==record['sha256']
            hashes.append(record);data[alias,tf]=a;feat[alias,tf]=features(a)
    cp=root/'exchange/research/cost-sample-20261022/summary.json';costs=read(cp)['results']
    spreads={a:max(r['p95_spread_points']*r['contract_now']['point'] for r in costs if r['instrument']==a and r['status']=='OBSERVED') for a in P.ALIASES}
    tests={};rows_by={};filters={};regimes={}
    for family,alias,tf,variant in definitions():
        key='/'.join((family,alias,variant));rows,c=windows(data[alias,tf],feat[alias,tf],family,variant,spreads[alias])
        rows_by[key]=rows;filters[key]=c
        tests[key]={p:summary([r for r in rows if p=='all' or r['period']==p],family=='F') for p in ('early','late','all')}
        regimes[key]={f'{k}/{v}':summary([r for r in rows if r[k]==v]) for k,vs in [('vol',('low','high')),('trend',('up','down'))] for v in vs}
    keys=list(tests);assert len(keys)==P.PRIMARY_TESTS
    for field in ('p_delta','p_placebo'):
        for k,v in zip(keys,holm([tests[k]['late'][field] for k in keys])):tests[k]['late'][field+'_holm']=v
    fk=[k for k in keys if k.startswith('F/')]
    for k,v in zip(fk,holm([tests[k]['late']['p_thinning'] for k in fk])):tests[k]['late']['p_thinning_holm']=v
    # All combinations retained, even no active positions or negative values.
    base=Path(__file__).resolve().parent
    result=dict(version=P.VERSION,at=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),numpy=np.__version__,
        source_hashes=hashes,cost_sha256=sha(cp),spreads=spreads,
        code_hashes={p.name:sha(p) for p in base.glob('*.py')},registry_sha256=sha(base/'STRATEGY_HYPOTHESES.md'),
        tests=tests,regimes=regimes,filters=filters,rows=rows_by,orders_sent=0,
        independent_confirmation=False,real_net_backtest=False)
    out.parent.mkdir(parents=True,exist_ok=True);out.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'tests':len(tests),'paired_opportunities':sum(len(r) for r in rows_by.values()),
        'positive_late_delta':sum(x['late'].get('delta',0)>0 for x in tests.values()),
        'significant_late_delta_holm':sum(x['late']['p_delta_holm']<.05 for x in tests.values())}))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();run(a.root,a.out)
