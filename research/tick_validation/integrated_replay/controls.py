"""Explicit synthetic tape and controls; no historical cost or time assertion."""
import copy,json,math,tempfile
from datetime import datetime,timezone
from pathlib import Path
from adapter import Replay,PortfolioBroker,LastBars,Journal,SimBroker,FROZEN

START=1792670400000  # Explicit fixture UTC, independent of broker raw time.
END=START+60000

def setup(folder,aliases=('GOLD','US500'),side='SELL',end_ms=END,**overrides):
    c=json.loads((FROZEN/'config.demo.json').read_text())
    c.update(account_login=123456,account_server='SIMULATOR',terminal_path='IN_MEMORY_ONLY',broker_time_offset_seconds=0)
    c.pop('runtime',None)
    c['calendar']={'enabled':True}
    c['strategies']=['local_breakout_v1','local_false_breakout_v1']
    original=SimBroker(datetime.fromtimestamp(START/1000,timezone.utc))
    contracts={};policies={};bars={}
    c['symbols']={alias:dict(broker='TEST_'+alias,max_spread_points=5,max_entry_deviation_points=300,
        deviation_points=2,cost_buffer_per_lot=2,max_volume=.08,trading_enabled=True,max_spread_atr_ratio=.2) for alias in aliases}
    for alias in aliases:
        symbol='TEST_'+alias
        contracts[symbol]=dict(original.info,name=symbol)
        policies[symbol]=dict(valid_from_ms=START,valid_until_ms=end_ms+1,cash_factor=100,margin_per_lot=100,
            commission_per_lot_side=2,fee_per_fill=0,latency_ms=50,max_wait_ms=500,slippage_points=0,
            fx_symbol=None,intermediate_digits=None,rollover_ms=[])
        policies[symbol].update(overrides)
        rows=[]
        for k in range(200):
            close=100+math.sin(k*.7)*.5
            rows.append(dict(time=START//1000-(200-k)*3600,open=close-.03,high=close+.1,low=close-.1,close=close,tick_volume=100))
        rows[-1].update(open=100.1,high=102,low=100,close=100.2)
        if side=='BUY':
            for b in rows:b.update(open=200-b['open'],high=200-b['low'],low=200-b['high'],close=200-b['close'])
        bars[symbol]=LastBars(rows,[(START,START+3600000)])
    b=PortfolioBroker(c,contracts,policies,bars,START,folder,'USD')
    j=Journal(Path(folder)/'journal')
    return c,b,j

def calendar_event(ms=START):
    seconds=ms/1000
    return dict(kind='calendar',utc_ms=ms,global_sequence=0,data=dict(schema_version='1.0',read_only=True,status='OK',
        account_login=123456,account_server='SIMULATOR',server_minus_gmt_seconds=0,retrieved_at_utc=seconds,
        coverage_from_utc=seconds-3600,coverage_until_utc=seconds+86400,currencies=['USD'],source='SYNTHETIC_FIXTURE',
        events=[dict(id='test-event',name='Synthetic event outside exposure window',currency='USD',importance=3,
            precision='exact',start_utc=seconds+36000,end_utc=seconds+36000)]))

def ticks(aliases=('GOLD','US500'),side='SELL',invalid_at=(),flat=False,duration_ms=60000,stride_ms=50):
    yield calendar_event()
    order=1;indices={a:0 for a in aliases}
    for delta in sorted(set([0,50,100,150]+list(range(1000,duration_ms,stride_ms)))):
        if delta and delta%600000==0:
            event=calendar_event(START+delta);event['global_sequence']=order
            yield event;order+=1
        price=100 if flat or delta<10000 else 97.8 if delta<40000 else 95.8
        if side=='BUY' and not flat:price=200-price
        for alias in aliases:
            t=dict(bid=round(price,2),ask=round(price+.02,2),last=round(price+.01,2),flags=14)
            if delta in invalid_at:t.update(bid=0.,ask=0.,flags=24)
            yield dict(kind='tick',symbol='TEST_'+alias,provider_index=indices[alias],global_sequence=order,utc_ms=START+delta,tick=t)
            indices[alias]+=1;order+=1

def run_control(aliases=('GOLD','US500'),side='SELL',events=None,end_ms=END,**pricing):
    with tempfile.TemporaryDirectory(prefix='trading-replay-control-') as folder:
        c,b,j=setup(folder,aliases,side,end_ms=end_ms,**pricing)
        try:
            r=Replay(c,b,ticks(aliases,side) if events is None else events,j,START,end_ms,10000,10000).run()
            r.update(data_class='SYNTHETIC_PORTFOLIO_CONTROL',historical_performance=False)
            return r
        finally:j.close()

if __name__=='__main__':
    out=Path(__file__).resolve().parent/'control-results.json'
    if out.exists():raise SystemExit('Control results already exist')
    results={side:run_control(side=side) for side in ['BUY','SELL']}
    out.write_text(json.dumps(results,indent=2),encoding='utf-8')
    print([(side,len(r['ledger']),r['ending_equity'],len(r['invalid_quotes'])) for side,r in results.items()])
