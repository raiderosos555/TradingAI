"""Incremental Last bars and delayed quote candidates; no trading authority."""
import copy,math,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent))
from model import validate_quote,execution_price,to_utc,Unverified

class Timeline:
    def __init__(self,boundaries):
        self.boundaries=copy.deepcopy(boundaries)
        self.index={};self.current={};self.closed={};self.now=None;self.quote=None
        for tf,windows in self.boundaries.items():
            if any(type(a) is not int or type(b) is not int or a>=b for a,b in windows):raise ValueError('Invalid boundaries')
            if any(b>c for (a,b),(c,d) in zip(windows,windows[1:])):raise ValueError('Overlapping boundaries')
            self.index[tf]=0;self.current[tf]=None;self.closed[tf]=[]

    def advance(self,raw_ms):
        if type(raw_ms) is not int or self.now is not None and raw_ms<self.now:raise ValueError('Timeline regression')
        self.now=raw_ms;published=[]
        for tf,windows in self.boundaries.items():
            while self.index[tf]<len(windows) and windows[self.index[tf]][1]<=raw_ms:
                start,end=windows[self.index[tf]];bar=self.current[tf]
                record=dict(timeframe=tf,start_raw_ms=start,end_raw_ms=end,published_raw_ms=raw_ms,
                            status='CLOSED' if bar is not None else 'MISSING_LAST',ohlc=copy.deepcopy(bar))
                self.closed[tf].append(record);published.append(copy.deepcopy(record))
                self.index[tf]+=1;self.current[tf]=None
        return published

    def feed(self,tick):
        validate_quote(tick)
        if tick.get('flags',0)&8 and (not math.isfinite(tick.get('last',0)) or tick.get('last',0)<=0):
            raise Unverified('Invalid Last update')
        events=self.advance(tick['time_msc'])
        self.quote=copy.deepcopy(tick)
        if tick.get('flags',0)&8:
            for tf,windows in self.boundaries.items():
                i=self.index[tf]
                if i>=len(windows) or tick['time_msc']<windows[i][0]:continue
                price=tick['last'];b=self.current[tf]
                if b is None:self.current[tf]=dict(open=price,high=price,low=price,close=price,tick_volume=1)
                else:b.update(high=max(b['high'],price),low=min(b['low'],price),close=price,tick_volume=b['tick_volume']+1)
        return events

    def snapshot(self,tf):return copy.deepcopy(self.closed[tf])

    def utc_market(self,symbol,info,tf,count,clock_segments,max_quote_age_ms):
        # This boundary prevents the raw coordinate from silently becoming UTC.
        if type(count) is not int or count<=0 or max_quote_age_ms<0:raise ValueError('Invalid market request')
        if self.quote is None:raise Unverified('No quote')
        now_utc=to_utc(self.now,clock_segments)
        quote_utc=to_utc(self.quote['time_msc'],clock_segments)
        if not 0<=now_utc-quote_utc<=max_quote_age_ms:raise Unverified('Stale quote')
        records=self.closed[tf][-count:]
        if len(records)<count or any(r['status']!='CLOSED' for r in records):raise Unverified('Insufficient complete closed bars')
        bars=[]
        for r in records:
            start=to_utc(r['start_raw_ms'],clock_segments);end=to_utc(r['end_raw_ms'],clock_segments)
            if end>now_utc:raise Unverified('Future bar')
            expected_ms={'H1':3600000,'H4':14400000,'D1':86400000}.get(tf)
            if expected_ms is None or end-start!=expected_ms:
                raise Unverified('Mapped duration incompatible with frozen fixed-duration analyzer')
            bars.append(dict(time=start//1000,end_time_msc=end,**r['ohlc']))
        quote=dict(self.quote,time_msc=quote_utc,time=quote_utc//1000)
        return dict(symbol=symbol,info=copy.deepcopy(info),tick=quote,bars=bars)

class QuoteQueue:
    """First eligible quote for each intent; NOT a fill or risk authorization."""
    def __init__(self):self.pending={};self.used=set();self.now=None
    def submit(self,identifier,side,action,decision_raw_ms,delay_ms,max_wait_ms,max_spread):
        if identifier in self.used:raise ValueError('Intent ID reused')
        if side not in {'BUY','SELL'} or action not in {'OPEN','CLOSE'}:raise ValueError('Invalid action')
        if type(decision_raw_ms) is not int or type(delay_ms) is not int or type(max_wait_ms) is not int or delay_ms<1 or max_wait_ms<delay_ms:raise ValueError('Explicit positive delay required')
        if type(max_spread) not in (int,float) or not math.isfinite(max_spread) or max_spread<0:raise ValueError('Explicit spread limit required')
        if self.now is not None and decision_raw_ms<self.now:raise ValueError('Cannot backdate decision')
        self.used.add(identifier)
        self.pending[identifier]=dict(side=side,action=action,decision_raw_ms=decision_raw_ms,
                                     ready=decision_raw_ms+delay_ms,deadline=decision_raw_ms+max_wait_ms,max_spread=max_spread)
    def advance(self,raw_ms):
        if type(raw_ms) is not int or self.now is not None and raw_ms<self.now:raise ValueError('Timeline regression')
        self.now=raw_ms;events=[]
        for key,p in list(self.pending.items()):
            if raw_ms>p['deadline']:
                events.append(dict(id=key,status='EXPIRED_NO_QUOTE',at_raw_ms=raw_ms,orders_authorized=False));del self.pending[key]
        return events
    def feed(self,tick):
        validate_quote(tick);events=self.advance(tick['time_msc'])
        for key,p in list(self.pending.items()):
            if self.now<p['ready']:continue
            status='QUOTE_CANDIDATE' if tick['ask']-tick['bid']<=p['max_spread']+1e-12 else 'REJECTED_SPREAD'
            events.append(dict(id=key,status=status,at_raw_ms=self.now,orders_authorized=False,
                               side=p['side'],action=p['action'],decision_raw_ms=p['decision_raw_ms'],
                               price=execution_price(p['side'],p['action'],tick) if status=='QUOTE_CANDIDATE' else None))
            del self.pending[key]
        return events
