"""Offline chronological portfolio adapter for the four frozen application engines.

No MT5 import, network, live state, credentials or external briefing transport.
Missing valuations are errors, never stale marks or zero PnL. This module accepts
an explicit event tape and explicit pricing policies; it cannot certify them.
"""
from __future__ import annotations
import copy
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

A=Path(__file__).resolve().parent
FROZEN=A.parent/'stage2/source_snapshot'
for row in json.loads((A.parent/'stage2/source_manifest.json').read_text()):
    assert hashlib.sha256((FROZEN/row['path']).read_bytes()).hexdigest()==row['sha256']
sys.path.insert(0,str(FROZEN))
from trading_ai import journal as journal_module
from trading_ai.models import Blocked, digest, canonical
from trading_ai.journal import Journal, atomic_write
from trading_ai.simulation import SimBroker
from trading_ai.risk import RiskManager, on_grid
from trading_ai.execution import ExecutionEngine
from trading_ai.manager import PositionManager
from trading_ai.strategy import SignalEngine, policy_hash
from trading_ai.runtime import configuration_hash
assert Path(journal_module.__file__).resolve().is_relative_to(FROZEN)


def valid_quote(t):
    return bool(t and all(type(t.get(k)) in (float,int) and math.isfinite(t[k]) and t[k]>0 for k in ('bid','ask')) and t['bid']<=t['ask'])


class Tape:
    """Validate supplied order, never sort. Equal times require global sequence.

    utc_ms must already have been mapped by independently validated provenance.
    Invalid quotes stay in the tape. The optional global_sequence proves only
    the declared source order; a fabricated tie-break is not valid evidence.
    """
    def __init__(self, events):
        self.source=iter(events);self.previous=None;self.provider={};self.pending=None
        self._next()

    def _next(self):
        e=next(self.source,None)
        if e is not None:
            if type(e['utc_ms']) is not int:raise ValueError('Integer UTC milliseconds required')
            if self.previous:
                old=self.previous
                if e['utc_ms']<old['utc_ms']:raise ValueError('Tape time regression')
                if e['utc_ms']==old['utc_ms']:
                    same=e['kind']==old['kind']=='tick' and e['symbol']==old['symbol']
                    sequenced=(type(old.get('global_sequence')) is int and type(e.get('global_sequence')) is int and e['global_sequence']>old['global_sequence'])
                    if not same and not sequenced:raise ValueError('Ambiguous inter-stream order at equal UTC millisecond')
            if e['kind']=='tick':
                seq=e['provider_index'];symbol=e['symbol']
                if type(seq) is not int or seq!=self.provider.get(symbol,-1)+1:raise ValueError('Missing/reordered provider index')
                self.provider[symbol]=seq
            self.previous=e
        self.pending=e

    def pop(self):
        result=self.pending
        self._next()
        return result


class LastBars:
    def __init__(self, warmup, windows):
        self.closed=copy.deepcopy(warmup);self.windows=list(windows);self.index=0;self.forming=None
        if len(self.closed)<200:raise ValueError('200 actual closed H1 bars required')
        if any(a['time']>=b['time'] for a,b in zip(self.closed,self.closed[1:])):raise ValueError('Warmup chronology')
        if not self.windows or self.closed[-1]['time']*1000+3600000>self.windows[0][0]:raise ValueError('Warmup overlaps replay')
        if any(b-a!=3600000 for a,b in self.windows):raise ValueError('Frozen analyzer requires 3600-second H1 windows')
        if any(b>c for (a,b),(c,d) in zip(self.windows,self.windows[1:])):raise ValueError('Overlapping windows')
        self.missing=[]

    def advance(self, ms):
        while self.index<len(self.windows) and self.windows[self.index][1]<=ms:
            start,end=self.windows[self.index]
            if self.forming is None:self.missing.append([start,end])
            else:self.closed.append(dict(time=start//1000,**self.forming))
            self.forming=None;self.index+=1

    def feed(self, ms, tick):
        self.advance(ms)
        if not tick.get('flags',0)&8:return
        price=tick.get('last')
        if type(price) not in (float,int) or not math.isfinite(price) or price<=0:raise ValueError('Invalid Last update')
        if self.index>=len(self.windows) or ms<self.windows[self.index][0]:return
        if self.forming is None:self.forming=dict(open=price,high=price,low=price,close=price,tick_volume=1)
        else:self.forming.update(high=max(self.forming['high'],price),low=min(self.forming['low'],price),close=price,tick_volume=self.forming['tick_volume']+1)


class PortfolioBroker(SimBroker):
    def __init__(self, config, contracts, policies, bars, start_ms, calendar_root, account_currency):
        super().__init__(datetime.fromtimestamp(start_ms/1000,timezone.utc))
        self.c=config;self.contracts=copy.deepcopy(contracts);self.policies=copy.deepcopy(policies)
        self.bars=bars;self.calendar_root=Path(calendar_root);self.time_offset=config.get('broker_time_offset_seconds',0)
        if not isinstance(account_currency,str) or len(account_currency)!=3:raise ValueError('Explicit account currency required')
        self.account.update(login=config['account_login'],server=config['account_server'],currency=account_currency)
        assert self.account['server']=='SIMULATOR' and config['terminal_path']=='IN_MEMORY_ONLY'
        self.quotes={};self.side_times={};self.ledger=[];self.requests=[];self.invalid=[];self.trace=[]
        self.j=None;self.advance=None;self.tape=None;self.end_ms=None
        self.high_water=None;self.drawdown=0.;self.unpriced_marks=0;self.marks=0

    @property
    def ms(self):return int(round(self.now.timestamp()*1000))

    def paths(self):return dict(data_path=str(self.calendar_root))

    def policy(self,symbol):
        p=self.policies[symbol]
        if not p['valid_from_ms']<=self.ms<p['valid_until_ms']:raise Blocked('Contract/cost policy outside evidenced range')
        for key in ('cash_factor','margin_per_lot','commission_per_lot_side','fee_per_fill','latency_ms','max_wait_ms','slippage_points','fx_symbol','intermediate_digits','rollover_ms'):
            if key not in p:raise Blocked('Missing explicit pricing policy: '+key)
        for key in ('cash_factor','margin_per_lot','commission_per_lot_side','fee_per_fill','slippage_points'):
            if type(p[key]) not in (int,float) or not math.isfinite(p[key]) or p[key]<0:raise Blocked('Invalid pricing policy')
        if p['cash_factor']<=0 or not 1<=p['latency_ms']<=p['max_wait_ms']:raise Blocked('Invalid cash/latency policy')
        if not isinstance(p['rollover_ms'],list):raise Blocked('Explicit rollover schedule required')
        return p

    def quote_for(self,symbol):
        tick=self.quotes.get(symbol)
        if not valid_quote(tick):raise Blocked('No executable Bid/Ask for '+symbol)
        if not 0<=self.ms-tick['time_msc']<=self.c['risk']['max_tick_age_seconds']*1000:raise Blocked('Stale replay quote for '+symbol)
        return tick

    def market(self,symbol,timeframe='H1',count=20):
        if timeframe!='H1':raise Blocked('Replay implements frozen H1 local strategies only')
        tick=self.quotes.get(symbol)
        if tick is None:raise Blocked('No observed quote')
        return copy.deepcopy(dict(symbol=symbol,info=self.contracts[symbol],tick=tick,bars=self.bars[symbol].closed[-count:]))

    def profit(self,side,symbol,volume,start,end):
        p=self.policy(symbol)
        value=(Decimal(str(end))-Decimal(str(start)))*Decimal(str(1 if side==0 else -1))*Decimal(str(volume))*Decimal(str(p['cash_factor']))
        if p['intermediate_digits'] is not None:value=value.quantize(Decimal(1).scaleb(-p['intermediate_digits']),rounding=ROUND_HALF_UP)
        if p['fx_symbol']:
            fx=self.quote_for(p['fx_symbol'])
            value*=Decimal(str(fx['bid'] if value>=0 else fx['ask']))
        return float(value.quantize(Decimal('.01'),rounding=ROUND_HALF_UP))

    def margin(self,side,symbol,volume,price):return volume*self.policy(symbol)['margin_per_lot']

    def revalue(self):
        total=margin=0.
        for p in self.positions:
            q=self.quote_for(p['symbol']);price=q['bid'] if p['type']==0 else q['ask']
            p.update(price_current=price,profit=self.profit(p['type'],p['symbol'],p['volume'],p['price_open'],price))
            total+=p['profit'];margin+=self.margin(p['type'],p['symbol'],p['volume'],price)
        self.account.update(profit=total,equity=self.account['balance']+total,margin_free=self.account['balance']+total-margin)

    def snapshot(self):
        self.revalue()
        return super().snapshot()

    def mark(self):
        self.marks+=1
        try:
            self.revalue();equity=self.account['equity']
            self.high_water=equity if self.high_water is None else max(self.high_water,equity)
            self.drawdown=max(self.drawdown,self.high_water-equity)
        except Blocked:self.unpriced_marks+=1

    def feed(self,event):
        ms=event['utc_ms'];self.now=datetime.fromtimestamp(ms/1000,timezone.utc)
        for b in self.bars.values():b.advance(ms)
        kind=event['kind']
        if kind=='connection':self.terminal['connected']=event['connected'];self.mark();return
        if kind=='calendar':
            d=copy.deepcopy(event['data'])
            if d['retrieved_at_utc']*1000>ms:raise ValueError('Calendar from future')
            atomic_write(self.calendar_root/'MQL5/Files/TradingAI'/f"calendar_{self.c['account_login']}.json",canonical(d));return
        if kind!='tick':raise ValueError('Unknown tape event')
        symbol=event['symbol'];t=copy.deepcopy(event['tick'])
        times=self.side_times.setdefault(symbol,{'bid':None,'ask':None})
        if not valid_quote(t):times.update(bid=None,ask=None)
        else:
            for key,flag in [('bid',2),('ask',4)]:
                if t.get('flags',0)&flag:times[key]=ms
        quote_ms=min(times.values()) if all(x is not None for x in times.values()) else 0
        t.update(time=quote_ms//1000,time_msc=quote_ms,event_time_msc=ms,
            bid_changed_utc_ms=times['bid'],ask_changed_utc_ms=times['ask'])
        self.quotes[symbol]=t
        if symbol in self.bars:self.bars[symbol].feed(ms,t)
        if not valid_quote(t):
            self.invalid.append(dict(symbol=symbol,utc_ms=ms,provider_index=event['provider_index']))
            self.mark()
            return  # Preserve Last and the unavailable quote; never carry a price.
        try:self.quote_for(symbol)
        except Blocked as exc:
            self.invalid.append(dict(symbol=symbol,utc_ms=ms,provider_index=event['provider_index'],reason=str(exc)))
            self.mark()
            return
        for p in list(self.positions):
            if p['symbol']!=symbol:continue
            price=t['bid'] if p['type']==0 else t['ask'];buy=p['type']==0
            rule='SL' if (price<=p['sl'] if buy else price>=p['sl']) else 'TP' if (price>=p['tp'] if buy else price<=p['tp']) else None
            if rule:self.book(dict(action=1,position=p['ticket'],symbol=symbol,type=1-p['type'],volume=p['volume'],magic=p['magic'],comment=p['comment']), 'SERVER_'+rule)
        self.mark()

    def validate_request(self,r):
        if r['action'] not in (1,6):raise Blocked('Pending orders not emitted by the two frozen local strategies; not supported')
        info=self.contracts[r['symbol']];q=self.quote_for(r['symbol'])
        p=next((x for x in self.positions if x['ticket']==r.get('position')),None)
        if 'position' in r and p is None:raise Blocked('Position closed before arrival')
        if r['action']==1:
            v=r['volume']
            if not info['volume_min']<=v<=info['volume_max'] or not on_grid(v,info['volume_step']):raise Blocked('Invalid lot at arrival')
            if p and (v>p['volume']+1e-9 or r['type']==p['type']):raise Blocked('Invalid close at arrival')
            if p:return
        side=p['type'] if p else r['type'];reference=q['bid'] if side==0 else q['ask']
        sl,tp=r['sl'],r['tp'];distance=info['trade_stops_level']*info['point']
        if not all(on_grid(v,info['trade_tick_size']) for v in (sl,tp)):raise Blocked('Off-grid stop')
        if not (sl<reference<tp if side==0 else tp<reference<sl):raise Blocked('Invalid protective levels at arrival')
        if min(abs(reference-sl),abs(reference-tp))<=distance:raise Blocked('Stop distance at arrival')
        if p and min(abs(reference-p['sl']),abs(reference-p['tp']))<=info['trade_freeze_level']*info['point']:raise Blocked('Freeze level at arrival')

    def check(self,request):
        try:self.validate_request(request);return dict(retcode=0,comment='Replay check')
        except Blocked as e:return dict(retcode=10016,comment=str(e))

    def book(self,r,source):
        symbol=r['symbol'];q=self.quote_for(symbol);policy=self.policy(symbol)
        self.tick=copy.deepcopy(q)
        if r['action']==1:
            slip=policy['slippage_points']*self.contracts[symbol]['point']
            # TP is a limit: no adverse fill beyond its threshold.
            if source!='SERVER_TP':
                if r['type']==0:self.tick['ask']+=slip
                else:self.tick['bid']-=slip
            price=self.tick['ask'] if r['type']==0 else self.tick['bid']
            if price<=0 or not on_grid(price,self.contracts[symbol]['trade_tick_size']):raise Blocked('Invalid modeled fill price')
            self.validate_request(r)
        else:self.validate_request(r)
        old=len(self.deals);result=super().send(r)
        for d in self.deals[old:]:
            d['time_msc']=self.ms;d['commission']=-policy['commission_per_lot_side']*d['volume'];d['fee']=-policy['fee_per_fill']
            self.account['balance']+=d['profit']+d['commission']+d['fee']
            self.ledger.append(dict(**copy.deepcopy(d),source=source))
        self.mark()  # Fees and a fill at the last event also affect drawdown.
        return result

    def send(self,r):
        if not self.terminal['connected']:raise Blocked('Disconnected')
        intents=[o for o in self.j.operations() if o['status']=='INTENT' and o['payload']['request']==r]
        if len(intents)!=1:raise Blocked('One durable ExecutionEngine intent required')
        p=self.policy(r['symbol']);submitted=self.ms;ready=submitted+p['latency_ms'];deadline=min(submitted+p['max_wait_ms'],self.end_ms-1)
        self.requests.append(dict(request=copy.deepcopy(r),submitted_ms=submitted,ready_ms=ready,deadline_ms=deadline))
        while self.tape.pending is not None and self.tape.pending['utc_ms']<=deadline:
            event=self.tape.pop();self.advance(event['utc_ms']);self.feed(event)
            if event['kind']!='tick' or event['symbol']!=r['symbol'] or self.ms<ready:continue
            if not self.terminal['connected']:return dict(retcode=10031,comment='Disconnected in flight')
            if not valid_quote(self.quotes.get(r['symbol'])):continue
            try:
                q=self.quote_for(r['symbol']);spec=next(v for v in self.c['symbols'].values() if v['broker']==r['symbol'])
                if (q['ask']-q['bid'])/self.contracts[r['symbol']]['point']>spec['max_spread_points']+1e-6:raise Blocked('Spread exceeds limit at arrival')
                return self.book(r,'APPLICATION_DELAYED')
            except Blocked as exc:return dict(retcode=10016,comment=str(exc))
        self.advance(deadline)
        return dict(retcode=10012,comment='No executable event before bounded deadline; no fill')


class Replay:
    """Explicit event-clock runner: manage first, then scan at full cycles.

    Clock/date/contract/calendar provenance must be checked by the caller before
    historical use. Timer phase and synchronous delays are declared model inputs.
    Initial account is virtual, flat, with an explicit same-UTC-day baseline.
    """
    def __init__(self,c,broker,events,journal,start_ms,end_ms,initial_equity,baseline_equity):
        if not start_ms<end_ms:raise ValueError('Empty replay')
        self.c=c;self.b=broker;self.j=journal;self.start=start_ms;self.end=end_ms
        self.tape=Tape(events);broker.tape=self.tape;broker.j=journal;broker.advance=self.advance;broker.end_ms=end_ms
        if self.tape.pending and self.tape.pending['utc_ms']<start_ms:raise ValueError('Tape before replay')
        self.b.account.update(balance=initial_equity,equity=initial_equity,margin_free=initial_equity)
        self.initial_equity=initial_equity;self.b.high_water=initial_equity
        self.j.set_setting('day_start',dict(date=broker.now.date().isoformat(),equity=baseline_equity,account=c['account_login'],server=c['account_server'],source='Explicit virtual account baseline'))
        self.r=RiskManager(c,broker,journal,activation=f"DEMO:{c['account_login']}",clock=lambda:broker.now)
        self.e=ExecutionEngine(self.r);self.m=PositionManager(self.e);self.s=SignalEngine(c,broker,journal)
        self.decisions=[];self.scans=[];self.equity=[];self.last_full=None

    def advance(self,ms):
        if ms<self.b.ms:raise ValueError('Clock regression')
        # Overnight charges are not silently assumed zero. Until a calibrated
        # rollover model is supplied, crossing a declared rollover while exposed
        # terminates the experiment without a complete performance result.
        for p in self.b.positions:
            if any(self.b.ms<x<=ms for x in self.b.policy(p['symbol'])['rollover_ms']):raise Blocked('Unimplemented historical rollover while exposed')
        if datetime.fromtimestamp(ms/1000,timezone.utc).date()!=self.b.now.date():raise Blocked('One UTC-day adapter requires explicit next-day baseline')
        self.b.now=datetime.fromtimestamp(ms/1000,timezone.utc)
        for b in self.b.bars.values():b.advance(ms)

    def authorize_virtual(self):
        end=datetime.fromtimestamp(self.end/1000,timezone.utc).isoformat()
        self.j.set_setting('strategy_policy',dict(hash=policy_hash(self.c),until=end))
        if 'runtime' in self.c:
            self.j.set_setting('runtime_authorization:'+self.c['runtime']['authorization_id'],dict(config_hash=configuration_hash(self.c),allowed_offsets=[self.c.get('broker_time_offset_seconds',0)]))
            self.j.set_setting('runtime_clock',dict(at=self.b.now.isoformat(),offset=self.c.get('broker_time_offset_seconds',0),account=[self.c['account_login'],self.c['account_server']]))

    def cycle(self,full):
        self.authorize_virtual()
        try:
            self.b.snapshot()
            self.decisions.extend(self.e.reconcile());self.decisions.extend(self.m.run())
            if full:
                items=self.s.scan(self.b.now)
                self.scans.append(dict(utc_ms=self.b.ms,items=copy.deepcopy(items)))
                for item in items:
                    if not item.get('signal'):continue
                    env=item['signal']
                    try:self.decisions.append(dict(signal_id=env['signal']['id'],**self.e.execute(env)))
                    except Blocked as exc:self.decisions.append(dict(signal_id=env['signal']['id'],status='REJECTED',reason=str(exc)))
        except Blocked as exc:self.decisions.append(dict(status='BLOCKED',utc_ms=self.b.ms,reason=str(exc)))
        try:self.equity.append(dict(utc_ms=self.b.ms,value=self.b.snapshot()['account']['equity']))
        except Blocked as exc:self.equity.append(dict(utc_ms=self.b.ms,value=None,reason=str(exc)))

    def run(self):
        next_cycle=self.start
        original_clock=journal_module.utcnow
        journal_module.utcnow=lambda:self.b.now
        try:
            while next_cycle<self.end or self.tape.pending is not None and self.tape.pending['utc_ms']<self.end:
                if self.tape.pending is not None and self.tape.pending['utc_ms']<self.end and self.tape.pending['utc_ms']<=next_cycle:
                    ev=self.tape.pop();self.advance(ev['utc_ms']);self.b.feed(ev);continue
                if next_cycle>=self.end:break
                self.advance(max(next_cycle,self.b.ms));cycle_start=self.b.ms
                full=self.last_full is None or cycle_start-self.last_full>=60000
                self.cycle(full)
                if full:self.last_full=self.b.ms
                next_cycle=max(cycle_start+10000,self.b.ms+50)
            # End is exclusive; do not invent an end-of-sample liquidation.
            self.advance(self.end-1)
            try:equity=self.b.snapshot()['account']['equity']
            except Blocked:equity=None
            metrics=self.metrics(equity)
            return dict(ledger=self.b.ledger,positions=copy.deepcopy(self.b.positions),requests=self.b.requests,
                scans=self.scans,decisions=self.decisions,equity_curve=self.equity,invalid_quotes=self.b.invalid,
                ending_equity=equity,realized_balance=self.b.account['balance'],uncertain=self.j.uncertain(),
                application_operations=self.j.operations(),data_class='UNCLASSIFIED_CALLER_MUST_VALIDATE_PROVENANCE',
                strategy_parameters_optimized=False,no_end_of_sample_forced_fill=True,metrics=metrics)
        finally:journal_module.utcnow=original_clock

    def metrics(self,equity):
        by_position={}
        for d in self.b.ledger:
            by_position.setdefault(d['position_id'],[]).append(d)
        trades=[]
        for pid,deals in by_position.items():
            if any(p['identifier']==pid for p in self.b.positions):continue
            op=next(o for o in self.j.operations() if o['payload']['rule']=='OPEN' and o['result'].get('order')==pid)
            risk=op['payload']['metadata']['risk_cash']
            net=sum(d['profit']+d['commission']+d['fee']+d['swap'] for d in deals)
            trades.append(dict(position_id=pid,net=net,initial_risk=risk,R=net/risk))
        wins=sum(max(0,t['net']) for t in trades);losses=-sum(min(0,t['net']) for t in trades)
        complete=equity is not None and not self.b.unpriced_marks and not self.j.uncertain()
        return dict(net_marked=equity-self.initial_equity if complete else None,
            conditional_modeled_net_marked=None if equity is None else equity-self.initial_equity,
            complete_valuation_path=complete,
            net_realized=self.b.account['balance']-self.initial_equity,closed_trades=trades,
            profit_factor=wins/losses if losses else None,
            expectancy_R=sum(t['R'] for t in trades)/len(trades) if trades else None,
            max_drawdown_cash=self.b.drawdown if not self.b.unpriced_marks else None,
            observed_drawdown_lower_bound=self.b.drawdown,unpriced_marks=self.b.unpriced_marks,
            valuation_marks=self.b.marks,commission_and_fees=-sum(d['commission']+d['fee'] for d in self.b.ledger),
            spread_impact_counterfactual=None)

    def run_report(self):
        """Persistable failure result; partial realized fills are not full PnL."""
        try:return dict(status='COMPLETED_MODEL_RUN',**self.run())
        except (Blocked,ValueError,KeyError) as exc:
            return dict(status='INCOMPLETE',reason=str(exc),stopped_at_utc_ms=self.b.ms,
                ledger=copy.deepcopy(self.b.ledger),positions=copy.deepcopy(self.b.positions),
                requests=copy.deepcopy(self.b.requests),invalid_quotes=copy.deepcopy(self.b.invalid),
                application_operations=self.j.operations(),
                metrics={k:None for k in ('net_marked','net_realized','profit_factor','expectancy_R','max_drawdown_cash')},
                historical_performance=False)
