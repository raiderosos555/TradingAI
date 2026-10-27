"""All four frozen engines in one deterministic control fixture, NOT history.

This fills the integration-test gap without presenting synthetic time, calendar,
contracts or cash factors as evidence about Oct22 profitability.
"""
import copy,json,math,sys
from datetime import timedelta,datetime,timezone
from pathlib import Path
A=Path(__file__).resolve().parent
sys.path.insert(0,str(A.parent/'stage2'))
from harness import Scenario,Blocked,FROZEN
from trading_ai.strategy import SignalEngine,policy_hash


def make(side='SELL'):
    s=Scenario(side=side)
    s.c['strategies']=['local_breakout_v1','local_false_breakout_v1']
    s.c['engine']={'enabled':True,'risk_pct':.1}
    rows=[]
    for k in range(200):
        close=100+math.sin(k*.7)*.5
        rows.append(dict(time=int(s.start.timestamp())-(200-k)*3600,open=close-.03,
            high=close+.1,low=close-.1,close=close,tick_volume=100))
    rows[-1].update(open=100.1,high=102,low=100,close=100.2)
    if side=='BUY':
        for b in rows:
            b.update(open=200-b['open'],high=200-b['low'],low=200-b['high'],close=200-b['close'])
    def market(symbol,timeframe='H1',count=20):
        if symbol!='TEST_GOLD' or timeframe!='H1':raise Blocked('Unsupported control market')
        return copy.deepcopy(dict(symbol=symbol,info=s.b.info,tick=s.b.tick,bars=rows[-count:]))
    s.b.market=market
    calendar=Path(s.temp.name)/'calendar.json'
    event_time=int(s.start.timestamp())+36000
    calendar.write_text(json.dumps(dict(schema_version='1.0',read_only=True,status='OK',
        account_login=123456,account_server='SIMULATOR',server_minus_gmt_seconds=0,
        retrieved_at_utc=s.start.timestamp(),coverage_from_utc=s.start.timestamp()-3600,
        coverage_until_utc=s.start.timestamp()+86400,currencies=['USD'],
        source='SYNTHETIC_CONTROL_ONLY',events=[dict(id='control-event',name='Synthetic event',
        currency='USD',importance=3,precision='exact',start_utc=event_time,end_utc=event_time)])))
    s.c['calendar']={'enabled':True,'path':str(calendar.resolve())}
    s.j.set_setting('strategy_policy',dict(hash=policy_hash(s.c),until=(s.start+timedelta(hours=3)).isoformat()))
    s.signal_engine=SignalEngine(s.c,s.b,s.j)
    return s


def generate(s):
    items=s.signal_engine.scan(s.b.now)
    assert len(items)==1 and items[0]['signal'],items
    s.env=items[0]['signal']
    return s.env


def run(side):
    s=make(side)
    try:
        generate(s)
        assert s.env['signal']['kind']==side
        opened=s.e.execute(s.env)
        assert opened['status']=='CONFIRMED',opened
        p=copy.deepcopy(s.b.positions[0]);tp1=s.env['signal']['management']['tp1']
        price=tp1-.02 if side=='SELL' else tp1+.02
        first=s.step(10,round(price,2))
        # Repeated manager cycles on real fixture ticks, with no re-entry.
        second=s.step(20,round(price,2))
        third=s.step(30,round(price,2))
        tp=p['tp'];exit_price=tp-.10 if side=='SELL' else tp+.10
        s.step(40,round(exit_price,2))
        assert not s.b.positions
        return dict(side=side,signal=s.env,entry=opened,management=first+second+third,
            ledger=s.b.ledger,operations=s.j.operations(),server_events=s.b.server_events,
            data_class='SYNTHETIC_INTEGRATION_ONLY',calendar_enabled=True,
            modules=['SignalEngine','RiskManager','ExecutionEngine','PositionManager'],
            frozen_source=str(FROZEN),not_historical_performance=True)
    finally:s.close()


if __name__=='__main__':
    result=[run(side) for side in ['BUY','SELL']]
    (A/'integration-control.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
    print('Two full frozen-engine controlled paths completed; no historical PnL claim')
