"""Research-only quote evidence. No MT5 dependency or execution authorization."""
import math

class QuoteEvidence:
    def __init__(self):self.bid=None;self.ask=None;self.last=None;self.now=None
    def feed(self,t):
        ms=t['time_msc']
        if self.now is not None and ms<self.now:raise ValueError('Out-of-order source')
        self.now=ms
        # A zero snapshot is evidence of uncertainty, regardless of Last-only
        # flags. Do not reuse a cached side across this barrier.
        if any(name in t and (type(t[name]) not in (float,int) or not math.isfinite(t[name]) or t[name]<=0) for name in ('bid','ask')):
            self.bid=self.ask=None
        for name,flag in [('bid',2),('ask',4)]:
            if t['flags']&flag:
                value=t.get(name)
                valid=isinstance(value,(float,int)) and math.isfinite(value) and value>0
                setattr(self,name,(value,ms) if valid else None)
        if t['flags']&8:self.last=(t.get('last'),ms)
    def candidate(self,now_ms,*,continuous_evidence_id,connected,max_age_ms=10000):
        if not connected or not continuous_evidence_id:raise ValueError('Continuity/connection not evidenced')
        if not self.bid or not self.ask:raise ValueError('Both quote sides require actual updates')
        if any(not 0<=now_ms-x[1]<=max_age_ms for x in [self.bid,self.ask]):raise ValueError('Stale/future quote side')
        if self.bid[0]>self.ask[0]:raise ValueError('Crossed quote')
        return dict(bid=self.bid[0],ask=self.ask[0],bid_time_msc=self.bid[1],ask_time_msc=self.ask[1],
            evidence_id=continuous_evidence_id,orders_authorized=False)


def recover_fresh_pair(invalid_tick, read_tick, *, now_raw_ms, attempts=3):
    """Research proposal: bounded reread; never return any older cached quote.

    Both sides must have changed in a strictly later broker event. Same-ms
    samples without a provider sequence are ambiguous and rejected. Caller must
    still run the ordinary Risk Manager with independently validated UTC.
    """
    if type(attempts) is not int or not 1<=attempts<=3:raise ValueError('Bounded read budget required')
    barrier=invalid_tick['time_msc'];evidence=[]
    for _ in range(attempts):
        t=read_tick()
        evidence.append(t)
        if not t:continue
        if (t['time_msc']<=barrier or t.get('flags',0)&6!=6 or
            not 0<=now_raw_ms()-t['time_msc']<=10000):continue
        if all(type(t.get(k)) in (float,int) and math.isfinite(t[k]) and t[k]>0 for k in ['bid','ask']) and t['bid']<=t['ask']:
            return dict(tick=dict(t),evidence=evidence,orders_authorized=False)
    raise ValueError('No proven fresh Bid/Ask after invalid event')
