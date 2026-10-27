"""Synthetic delayed broker integrated with frozen production Risk/Execution code.

Only control fixtures. Does not claim calibrated latency or historical costs.
"""
import copy,sys
from datetime import datetime,timezone
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'stage2'))
from harness import TickBroker,Scenario,Blocked,on_grid
from model import validate_stream

class DelayedBroker(TickBroker):
    def __init__(self,now,side,commission,journal):
        super().__init__(now,side,commission)
        self.j=journal;self.tape=[];self.cursor=0;self.delay_ms=50;self.wait_ms=1000
        self.application_requests=[];self.outcomes=[]
    def arm(self,ticks,delay_ms=50,max_wait_ms=1000):
        if type(delay_ms) is not int or type(max_wait_ms) is not int or not 1<=delay_ms<=max_wait_ms:
            raise ValueError('Explicit bounded positive latency required')
        data=copy.deepcopy(ticks);list(validate_stream(data))
        if data and data[0]['time_msc']<self.tick['time_msc']:raise ValueError('Tape starts before current quote')
        self.tape=data;self.cursor=0;self.delay_ms=delay_ms;self.wait_ms=max_wait_ms
    def reject(self,code,reason):
        result=dict(retcode=code,comment=reason,order=0,deal=0)
        self.outcomes.append(copy.deepcopy(result));return result
    def server_validate(self,r):
        if r['action'] not in {1,6}:raise NotImplementedError('Pending orders not covered')
        p=next((p for p in self.positions if p['ticket']==r.get('position')),None)
        if 'position' in r and p is None:return (10036,'Position already closed before application request arrived')
        if r['action']==1 and 'position' in r:return None
        side=p['type'] if p else r['type'];price=self.tick['bid'] if side==0 else self.tick['ask']
        sl,tp=r['sl'],r['tp'];distance=self.info['trade_stops_level']*self.info['point']
        if not all(on_grid(x,self.info['trade_tick_size']) for x in [sl,tp]):return (10016,'Off-grid protective level')
        if not (sl<price<tp if side==0 else tp<price<sl):return (10016,'Protective levels invalid at arrival')
        if min(abs(price-sl),abs(price-tp))<distance-1e-9:return (10016,'Stop distance invalid at arrival')
        if p:
            freeze=self.info['trade_freeze_level']*self.info['point']
            if min(abs(price-p['sl']),abs(price-p['tp']))<=freeze:return (10029,'Existing protection frozen at arrival')
        return None
    def send(self,request):
        if not self.terminal['connected']:raise Blocked('Application disconnected')
        assert self.account['server']=='SIMULATOR' and self.account['login']==123456
        intents=[o for o in self.j.operations() if o['status']=='INTENT' and o['payload']['request']==request]
        if len(intents)!=1:raise Blocked('Research sender requires one durable ExecutionEngine intent')
        submitted=self.tick['time_msc'];ready=submitted+self.delay_ms;deadline=submitted+self.wait_ms
        self.application_requests.append(dict(request=copy.deepcopy(request),submitted_raw_ms=submitted,ready_raw_ms=ready,deadline_raw_ms=deadline))
        while self.cursor<len(self.tape):
            tick=self.tape[self.cursor]
            if tick['time_msc']>deadline:break
            self.cursor+=1;self.feed(tick)  # Server stops remain active during the blocking send.
            if tick['time_msc']<ready:continue
            rejection=self.server_validate(request)
            if rejection:return self.reject(*rejection)
            result=self.book(request,'APPLICATION_DELAYED')
            self.outcomes.append(copy.deepcopy(result));return result
        self.now=datetime.fromtimestamp(deadline/1000,timezone.utc)
        return self.reject(10012,'Synthetic timeout: no quote within execution window; no fill')

def scenario(**kwargs):
    s=Scenario(**kwargs)
    b=DelayedBroker(s.start,s.b.side,s.b.commission,s.j)
    s.b=b;s.r.b=b;s.e.b=b
    return s

def tick(s,after_ms,bid,ask=None):
    return dict(time_msc=int(s.start.timestamp()*1000)+after_ms,bid=bid,ask=round(bid+.02,2) if ask is None else ask,last=bid,flags=14)
