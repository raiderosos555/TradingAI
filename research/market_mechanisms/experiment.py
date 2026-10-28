"""Exploratory Last-price markouts, NOT executions or net P&L.

Inputs are immutable old research files. No connection to MT5 or forward prices.
Only NumPy and the standard library are used. Run tests before experiments.
"""
import argparse
from collections import defaultdict
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import numpy as np
import protocol as P


def epoch(s):
    return datetime.fromisoformat(s).replace(tzinfo=timezone.utc).timestamp()


def read(path):
    return json.loads(path.read_text(encoding='utf-8-sig'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(root, alias, tf):
    rel = (f'exchange/research/history-20261024/{alias}.json' if tf == 'H1'
           else f'research/edge_audit/inputs/{alias}-{tf}.json')
    path = root / rel
    bars = read(path)['bars']
    a = {k: np.array([b[k] for b in bars], dtype=float)
         for k in ('broker_raw_time', 'open', 'high', 'low', 'close')}
    a['t'] = a.pop('broker_raw_time')
    if not all(np.isfinite(v).all() for v in a.values()):
        raise ValueError('Non-finite bars')
    if not (np.diff(a['t']) > 0).all():
        raise ValueError('Duplicate or reversed raw timestamp')
    if not all((a[k] > 0).all() for k in ('open','high','low','close')):
        raise ValueError('Nonpositive bar')
    if not ((a['high'] >= np.maximum(a['open'], a['close'])).all()
            and (a['low'] <= np.minimum(a['open'], a['close'])).all()):
        raise ValueError('Inconsistent OHLC')
    return a, dict(path=rel, sha256=sha(path), bars=len(bars))


def features(a, mechanism, b=None):
    """Causal: at index i only prices at or before i are consulted."""
    c = a['close']; n = len(c)
    direction = np.zeros(n); beta = np.ones(n); regime = np.zeros(n)
    if mechanism == 'M1':
        j = P.MOMENTUM_BARS
        direction[j:] = np.sign(c[j:] / c[:-j] - 1)
        regime[j:] = np.abs(c[j:] / c[:-j] - 1)
    elif mechanism == 'M2':
        j = P.REVERSION_LOOKBACK
        for i in range(j, n):
            past = c[i-j:i]; sd = np.std(past, ddof=1)
            distance = np.abs(np.diff(c[i-j:i+1])).sum()
            er = abs(c[i] - c[i-j]) / distance if distance else 0
            z = (c[i] - past.mean()) / sd if sd else 0
            regime[i] = er
            if abs(z) > P.REVERSION_Z and er < P.REVERSION_ER_MAX:
                direction[i] = -np.sign(z)
    elif mechanism == 'M3':
        tr = np.maximum(a['high']-a['low'], np.maximum(
            np.abs(a['high']-np.r_[c[0],c[:-1]]),
            np.abs(a['low']-np.r_[c[0],c[:-1]])))
        atr = np.full(n, np.nan)
        for i in range(P.ATR_LOOKBACK-1,n):
            atr[i] = tr[i-P.ATR_LOOKBACK+1:i+1].mean()
        for i in range(P.ATR_LOOKBACK+P.ATR_BASELINE,n):
            baseline = np.median(atr[i-P.ATR_BASELINE:i])
            ratio = atr[i]/baseline if baseline else 0
            regime[i] = ratio
            if ratio > P.ATR_EXPANSION:
                if c[i] > max(a['high'][i-P.BREAKOUT_LOOKBACK:i]): direction[i] = 1
                elif c[i] < min(a['low'][i-P.BREAKOUT_LOOKBACK:i]): direction[i] = -1
    elif mechanism == 'M4':
        x = np.log(b['close']); y = np.log(c); j = P.PAIR_LOOKBACK
        for i in range(j,n):
            xx = x[i-j:i]; yy = y[i-j:i]; xc = xx-xx.mean()
            denom = xc@xc
            if not denom: continue
            slope = float(xc@(yy-yy.mean())/denom)
            intercept = yy.mean()-slope*xx.mean()
            sd = np.std(yy-intercept-slope*xx, ddof=1)
            z = (y[i]-intercept-slope*x[i])/sd if sd else 0
            beta[i] = slope; regime[i] = abs(z)
            if P.PAIR_BETA_MIN <= slope <= P.PAIR_BETA_MAX and abs(z)>P.PAIR_Z:
                direction[i] = -np.sign(z)
    else:
        raise ValueError(mechanism)
    return direction, beta, regime


def aligned(a,b):
    _, ia, ib = np.intersect1d(a['t'],b['t'],return_indices=True)
    return ({k:v[ia] for k,v in a.items()}, {k:v[ib] for k,v in b.items()})


def pair_return(ra, rb, beta):
    return (ra-beta*rb)/(1+abs(beta))


def events(a, mechanism, alias, spread, b=None, second_spread=0):
    direction, betas, regime = features(a,mechanism,b)
    hold = {'M1':P.MOMENTUM_HOLD,'M2':P.REVERSION_HOLD,
            'M3':P.BREAKOUT_HOLD,'M4':P.PAIR_HOLD}[mechanism]
    step = {'M1':86400,'M2':3600,'M3':14400,'M4':3600}[mechanism]
    output = []; rejected = defaultdict(int); next_free = 0
    for i,d in enumerate(direction):
        if not d or not epoch(P.START)<=a['t'][i]<epoch(P.END): continue
        rejected['raw_signals'] += 1
        entry = i+1; leave = entry+hold
        if entry < next_free:
            rejected['overlap'] += 1; continue
        if leave >= len(a['t']):
            rejected['unobserved_exit'] += 1; continue
        seq = np.diff(a['t'][i:leave+1])
        continuous = (seq==step).all() if mechanism!='M1' else (seq<=4*86400).all()
        if not continuous:
            rejected['gap'] += 1; continue
        if mechanism in ('M2','M4') and a['t'][entry]//86400 != a['t'][leave]//86400:
            rejected['cross_raw_day'] += 1; continue
        if mechanism == 'M2' and not 6 <= (a['t'][i]//3600)%24 <= 19:
            rejected['raw_hour_filter'] += 1; continue
        te = a['t'][entry]; tx = a['t'][leave]
        if tx >= epoch(P.END) or (te<epoch(P.SPLIT)<=tx):
            rejected['split_boundary'] += 1; continue
        if te < epoch(P.SPLIT) and a['t'][i]>=epoch(P.SPLIT):
            raise AssertionError('Reversed time')
        # Signal preceding the split may not seed the later segment.
        if a['t'][i]<epoch(P.SPLIT)<=te:
            rejected['split_boundary'] += 1; continue
        ra = a['open'][leave]/a['open'][entry]-1
        hurdle = spread/a['open'][entry]*10000
        if b is not None:
            beta = betas[i]; rb = b['open'][leave]/b['open'][entry]-1
            ra = pair_return(ra,rb,beta)
            hurdle = (hurdle+abs(beta)*second_spread/b['open'][entry]*10000)/(1+abs(beta))
        elapsed_days = (tx-te)/86400
        stress_cost = P.STRESS_SPREAD_MULTIPLIER*hurdle+P.STRESS_EXTRA_BPS+P.STRESS_FINANCING_BPS_PER_DAY*elapsed_days
        gross = float(d*ra*10000)
        output.append(dict(mechanism=mechanism,alias=alias,signal_raw=float(a['t'][i]),
            entry_raw=float(te),exit_raw=float(tx),direction=float(d),beta=float(betas[i]),
            regime=float(regime[i]),period='early' if te<epoch(P.SPLIT) else 'late',
            block=int((te-epoch('2026-01-05'))//(P.BLOCK_DAYS*86400)),
            gross=gross,hurdle=float(hurdle),after_hurdle=gross-hurdle,
            stress=gross-stress_cost,benchmark=float(ra*10000-hurdle),
            delta_benchmark=float((d-1)*ra*10000)))
        next_free = leave
    rejected['accepted_markouts'] = len(output)
    return output,dict(rejected)


def holm(values):
    order = np.argsort(values); result = [1.0]*len(values); prev = 0.0
    for j,k in enumerate(order):
        prev = max(prev,min(1.0,(len(values)-j)*values[k])); result[k]=prev
    return result


def summarize(rows):
    if not rows:
        return dict(n=0,blocks=0,p_zero=1.0,p_placebo=1.0)
    blocks = sorted({r['block'] for r in rows})
    x = np.array([r['after_hurdle'] for r in rows]); mean=float(x.mean())
    sums = np.array([sum(r['after_hurdle'] for r in rows if r['block']==b) for b in blocks])
    counts = np.array([sum(r['block']==b for r in rows) for b in blocks])
    gross = np.array([sum(r['gross'] for r in rows if r['block']==b) for b in blocks])
    rng = np.random.default_rng(P.SEED)
    indexes = rng.integers(0,len(blocks),(P.RESAMPLES,len(blocks)))
    boot = sums[indexes].sum(axis=1)/counts[indexes].sum(axis=1)
    p = float((1+np.sum(boot-mean>=mean))/(P.RESAMPLES+1))
    signs = rng.choice([-1,1],(P.RESAMPLES,len(blocks)))
    placebos = (signs@gross-sum(r['hurdle'] for r in rows))/len(rows)
    pp = float((1+np.sum(placebos>=mean))/(P.RESAMPLES+1))
    if len(blocks)<2: p=pp=1.0
    positive=x[x>0].sum(); negative=-x[x<0].sum()
    # Descriptive sum-of-markouts only, no portfolio-equity interpretation.
    daily=defaultdict(float)
    for r in rows: daily[r['exit_raw']//86400] += r['after_hurdle']
    cumulative=np.r_[0,np.cumsum([daily[k] for k in sorted(daily)])]
    dd=float(np.max(np.maximum.accumulate(cumulative)-cumulative))
    return dict(n=len(rows),blocks=len(blocks),gross=float(np.mean([r['gross'] for r in rows])),
        hurdle=float(np.mean([r['hurdle'] for r in rows])),mean=mean,
        stress=float(np.mean([r['stress'] for r in rows])),
        benchmark=float(np.mean([r['benchmark'] for r in rows])),
        delta_benchmark=float(np.mean([r['delta_benchmark'] for r in rows])),
        ci95=[float(v) for v in np.quantile(boot,[.025,.975])],p_zero=p,p_placebo=pp,
        descriptive_pf=float(positive/negative) if negative else None,
        summed_markout_dd_bps=dd,
        first_entry_raw=datetime.fromtimestamp(min(r['entry_raw'] for r in rows),timezone.utc).isoformat(),
        last_exit_raw=datetime.fromtimestamp(max(r['exit_raw'] for r in rows),timezone.utc).isoformat())


def relationships(data):
    # Returns only across exactly consecutive raw hours. Never interpolate.
    series={}
    for name,a in data.items():
        series[name]={int(a['t'][i]):float(np.log(a['close'][i]/a['close'][i-1]))
                      for i in range(1,len(a['t'])) if a['t'][i]-a['t'][i-1]==3600}
    result=[]
    for i,name in enumerate(P.ALIASES):
        for other in P.ALIASES[i+1:]:
            for period,lo,hi in [('early',epoch(P.START),epoch(P.SPLIT)),('late',epoch(P.SPLIT),epoch(P.END))]:
                common=sorted(t for t in series[name].keys() & series[other].keys() if lo<=t<hi)
                x=[series[name][t] for t in common]; y=[series[other][t] for t in common]
                result.append(dict(a=name,b=other,period=period,n=len(common),
                    correlation=float(np.corrcoef(x,y)[0,1]) if len(common)>2 else None))
    return result


def main(root,out):
    if out.exists(): raise RuntimeError('Preserve results; do not rerun without reason')
    audit=read(root/'research/market_mechanisms/private/feasibility.json')
    expected={x['path']:x['sha256'] for x in audit['source_hashes']}
    data={}; hashes=[]
    for alias in P.ALIASES:
        for tf in ('H1','H4','D1'):
            a,h=load(root,alias,tf)
            if expected[h['path']]!=h['sha256']: raise RuntimeError('Source changed since audit')
            data[alias,tf]=a; hashes.append(h)
    cost_path=root/'exchange/research/cost-sample-20261022/summary.json'
    costs=read(cost_path)['results']
    spread={alias:max(x['p95_spread_points']*x['contract_now']['point']
                      for x in costs if x['instrument']==alias and x['status']=='OBSERVED') for alias in P.ALIASES}
    all_rows=[]; filters={}
    definitions=[('M1',x,'D1') for x in P.ALIASES]+[('M2',x,'H1') for x in ('EURPLN','EURUSD','GBPUSD')]+[('M3',x,'H4') for x in ('GOLD','OIL')]
    for mechanism,alias,tf in definitions:
        rows,f=events(data[alias,tf],mechanism,alias,spread[alias])
        all_rows.extend(rows); filters[mechanism+'/'+alias]=f
    a,b=aligned(data['US100','H1'],data['US500','H1'])
    rows,f=events(a,'M4','US100-US500',spread['US100'],b,spread['US500'])
    all_rows.extend(rows); filters['M4/US100-US500']=f
    keys=list(filters)+[m+'/ALL' for m in ('M1','M2','M3','M4')]
    assert len(keys)==P.PLANNED_TESTS
    results={}
    for key in keys:
        mechanism,alias=key.split('/')
        rows=[r for r in all_rows if r['mechanism']==mechanism and (alias=='ALL' or r['alias']==alias)]
        results[key]={p:summarize([r for r in rows if p=='all' or r['period']==p]) for p in ('early','late','all')}
    for field in ('p_zero','p_placebo'):
        adjusted=holm([results[k]['late'][field] for k in keys])
        for key,value in zip(keys,adjusted): results[key]['late'][field+'_holm']=value
    source_dir=Path(__file__).resolve().parent
    code_hashes={p.name:sha(p) for p in sorted(source_dir.glob('*.py'))}
    digest=sha(source_dir/'HYPOTHESIS_REGISTRY.md')
    result=dict(version=P.VERSION,at=datetime.now(timezone.utc).isoformat(),python=platform.python_version(),
        numpy=np.__version__,source_hashes=hashes,cost_source_sha256=sha(cost_path),spread_price_hurdles=spread,
        code_hashes=code_hashes,registry_sha256=digest,filters=filters,results=results,events=all_rows,
        relationships=relationships({k:data[k,'H1'] for k in P.ALIASES}),
        unavailable={'M5':'No paired forecast-before/first-actual-after sample and 24 past surprises',
                     'M6':'No EIA inventory forecast/first-release as-of history'},
        outcome='EXPLORATORY_LAST_MARKOUTS_NOT_NET_BACKTEST',orders_sent=0)
    out.parent.mkdir(parents=True,exist_ok=True)
    out.write_text(json.dumps(result,indent=2,allow_nan=False),encoding='utf-8')
    print(json.dumps({'events':len(all_rows),'tests':len(keys),'families':{k:results[k] for k in keys if k.endswith('/ALL')}},indent=2))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    args=ap.parse_args();main(args.root,args.out)
