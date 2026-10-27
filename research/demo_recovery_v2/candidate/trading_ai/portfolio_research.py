"""Exploratory shared-equity OHLC portfolio, isolated from the live execution path.

Fixed hypotheses; previous-bar features and costs only. No broker connection.
Server SL/TP approximation, pessimistic intrabar ordering. No profitability claim.
"""
from bisect import bisect_left
from datetime import datetime,timezone
from .indicators import ema,atr,rsi
from .risk import floor_volume
from .models import Blocked

VARIANTS=('trend_breakout','trend_pullback','range_reversion')

def features(bars):
    close=[b['close'] for b in bars]
    return {'ema50':ema(close,50),'ema200':ema(close,200),'atr':atr(bars,14),'rsi':rsi(close)}

def proposal(bars,f,i,variant):
    if i<201 or bars[i]['time']-bars[i-1]['time']>7200:return None
    j=i-1; a=f['atr'][j]; close=bars[j]['close']
    if not a or f['ema200'][j] is None:return None
    fast,slow=f['ema50'][j],f['ema200'][j]
    prior=bars[j-20:j]
    side=None
    if variant=='trend_breakout':
        if close>max(b['high'] for b in prior)+.1*a and fast>slow:side=1
        if close<min(b['low'] for b in prior)-.1*a and fast<slow:side=-1
    elif variant=='trend_pullback':
        if fast>slow+.5*a and bars[j]['low']<=fast and close>fast and close>bars[j]['open']:side=1
        if fast<slow-.5*a and bars[j]['high']>=fast and close<fast and close<bars[j]['open']:side=-1
    elif variant=='range_reversion':
        if abs(fast-slow)<.5*a:
            if close<fast-1.5*a and f['rsi'][j]<30:side=1
            if close>fast+1.5*a and f['rsi'][j]>70:side=-1
    else:raise Blocked('Unknown research hypothesis')
    return {'side':side,'atr':a} if side else None

def replay_portfolio(config,datasets,variant,start,end,initial_equity=100000.0,cost_multiple=1):
    if variant not in VARIANTS:raise Blocked('Unknown hypothesis')
    if start>=end or initial_equity<=0:raise Blocked('Invalid replay interval/equity')
    cache={}; lookup={}; timeline=set()
    for alias,data in datasets.items():
        bars=data['bars']
        if any(x['time']>=y['time'] for x,y in zip(bars,bars[1:])):raise Blocked('Unordered bars')
        for b in bars:
            if not 0<b['low']<=min(b['open'],b['close'])<=max(b['open'],b['close'])<=b['high']:raise Blocked('Invalid OHLC')
        cache[alias]=features(bars)
        lookup[alias]={b['time']:i for i,b in enumerate(bars)}
        timeline.update(b['time'] for b in bars if start<=b['time']<end)
    cash=initial_equity; positions={}; marks={}; trades=[]; curve=[]; rejected={}
    high=cash; dd=0.; daily=None; baseline=cash; max_slots=0; max_reserved=0.
    def reject(reason):rejected[reason]=rejected.get(reason,0)+1
    def equity():
        return cash+sum((marks[a]-p['entry'])*p['side']*p['volume']*p['factor'] for a,p in positions.items())
    def close(alias,price,time,reason):
        nonlocal cash
        p=positions.pop(alias)
        gain=(price-p['entry'])*p['side']*p['volume']*p['factor']
        swap=-5*cost_multiple*p['volume']*max(0,time-p['opened'])/86400
        cash+=gain+swap
        net=gain+swap-p['commission']
        trades.append({'instrument':alias,'opened':p['opened'],'closed':time,'net':net,
                       'risk':p['risk'],'R':net/p['risk'],'reason':reason,'volume':p['volume']})
    for time in sorted(timeline):
        available={a:lookup[a][time] for a in datasets if time in lookup[a]}
        # Opening marks are known before allocating capital. Never use this bar's close for entry.
        for alias,i in available.items():
            data=datasets[alias]; b=data['bars'][i]; point=data['contract']['point']
            spread=max(1,data['bars'][max(0,i-1)].get('spread',1))*point*cost_multiple
            marks[alias]=b['open']+(spread if alias in positions and positions[alias]['side']==-1 else 0)
        day=datetime.fromtimestamp(time,timezone.utc).date()
        if day!=daily:daily=day;baseline=equity()
        # Mark all existing positions at the new opens before any candidate is admitted.
        for alias in sorted(available):
            if alias in positions:continue
            i=available[alias];data=datasets[alias];b=data['bars'][i]; spec=config['symbols'][alias];contract=data['contract']
            s=proposal(data['bars'],cache[alias],i,variant)
            if not s:continue
            if len(positions)>=config['risk']['max_positions']:reject('slots');continue
            point=contract['point']; spread=max(1,data['bars'][i-1].get('spread',1))*point*cost_multiple
            if spread/point>spec['max_spread_points'] or spread>s['atr']*spec.get('max_spread_atr_ratio',1):reject('spread');continue
            side=s['side'];slip=2*cost_multiple*point
            entry=b['open']+(spread if side==1 else 0)+side*slip
            distance=2*s['atr']; sl=entry-side*distance;tp=entry+side*distance*2
            factor=contract['cash_per_price_unit_per_lot']
            per_lot=(distance+slip)*factor+max(100,10*cost_multiple)
            eq=equity()
            reserved=sum(max(0,(marks[a]-p['sl'])*p['side'])*p['volume']*p['factor']+100*p['volume'] for a,p in positions.items())
            budget=min(eq*config['risk']['max_trade_pct']/100,
                eq*config['risk']['max_total_pct']/100-reserved,
                baseline*config['risk']['max_daily_loss_pct']/100-max(0,baseline-eq)-reserved)
            if budget<=0:reject('risk');continue
            volume=floor_volume(min(budget/per_lot,spec['max_volume'],contract['volume_max']),contract['volume_step'])
            if volume<contract['volume_min']:reject('minimum_lot');continue
            fee=10*cost_multiple*volume;cash-=fee
            positions[alias]={'entry':entry,'sl':sl,'tp':tp,'side':side,'volume':volume,'factor':factor,
                'opened':time,'risk':per_lot*volume,'commission':fee}
            marks[alias]=b['open']+(spread if side==-1 else 0)
            max_slots=max(max_slots,len(positions));max_reserved=max(max_reserved,(reserved+per_lot*volume)/eq*100)
        for alias in list(positions):
            if alias not in available:continue
            i=available[alias];data=datasets[alias];b=data['bars'][i];p=positions[alias]
            point=data['contract']['point'];spread=max(1,data['bars'][max(0,i-1)].get('spread',1))*point*cost_multiple
            add=spread if p['side']==-1 else 0;hi=b['high']+add;lo=b['low']+add;op=b['open']+add
            slip=2*cost_multiple*point;buy=p['side']==1
            if (lo<=p['sl'] if buy else hi>=p['sl']):
                close(alias,(min(op,p['sl'])-slip if buy else max(op,p['sl'])+slip),time+3600,'SL')
            elif (hi>=p['tp'] if buy else lo<=p['tp']):close(alias,p['tp']-p['side']*slip,time+3600,'TP')
            elif time-p['opened']>=120*3600:close(alias,b['close']+add-p['side']*slip,time+3600,'TIME')
            else:marks[alias]=b['close']+add
        eq=equity();high=max(high,eq);dd=max(dd,high-eq)
        curve.append({'time':time+3600,'equity':eq})
    for alias in list(positions):
        p=positions[alias];close(alias,marks[alias]-p['side']*2*cost_multiple*datasets[alias]['contract']['point'],end,'END')
    if curve:curve[-1]['equity']=cash
    dd=max(dd,high-cash)
    wins=sum(max(0,t['net']) for t in trades);loss=-sum(min(0,t['net']) for t in trades)
    return {'variant':variant,'start':start,'end':end,'cost_multiple':cost_multiple,'initial_equity':initial_equity,
        'net':cash-initial_equity,'trades':trades,'profit_factor':wins/loss if loss else None,
        'win_rate':sum(t['net']>0 for t in trades)/len(trades) if trades else None,
        'max_drawdown':dd,'curve':curve,'max_positions_observed':max_slots,'max_reserved_pct':max_reserved,'rejected':rejected,
        'limitations':['Exploratory fixed hypotheses, different from deployed strategy',
            'Shared portfolio, fixed tie order by symbol; no historical margin/calendar or tick execution',
            'Previous H1 spread proxy; illustrative commission/swap and current cash conversion',
            'Daily baseline from first observed bar, unlike live exact UTC boundary',
            'No news backfill or profitability claim']}
