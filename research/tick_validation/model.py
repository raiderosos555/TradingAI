"""Stage 1 research primitives. No MT5 import, strategy, order sender or implicit UTC shift."""
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from math import isfinite
from zoneinfo import ZoneInfo

class Unverified(ValueError): pass

@dataclass(frozen=True)
class ClockSegment:
    utc_start_ms: int
    utc_end_ms: int
    raw_minus_utc_ms: int
    evidence_id: str
    verified: bool = False

def to_utc(raw_ms, segments):
    candidates=[]
    for s in segments:
        if not s.verified or not s.evidence_id: continue
        candidate=raw_ms-s.raw_minus_utc_ms
        if s.utc_start_ms<=candidate<s.utc_end_ms:candidates.append(candidate)
    if len(candidates)!=1:raise Unverified('Missing or ambiguous verified historical UTC mapping')
    return candidates[0]

def local_boundary(naive,zone,fold=None):
    if naive.tzinfo is not None:raise ValueError('Expected local naive boundary')
    z=ZoneInfo(zone);options={}
    for f in (0,1):
        aware=naive.replace(tzinfo=z,fold=f);utc=aware.astimezone(timezone.utc)
        if utc.astimezone(z).replace(tzinfo=None)==naive:options[utc]=f
    if not options:raise Unverified('Nonexistent local time at DST transition')
    if len(options)>1 and fold is None:raise Unverified('Ambiguous local time needs explicit fold')
    if fold is not None:
        if fold not in (0,1):raise ValueError('fold must be 0 or 1')
        target=naive.replace(tzinfo=z,fold=fold).astimezone(timezone.utc)
        if target not in options:raise Unverified('Invalid fold')
        return target
    return next(iter(options))

def bar_interval(local_open,timeframe,verified_zone):
    if not verified_zone:raise Unverified('Broker boundary policy required')
    hours={'H1':1,'H4':4,'D1':24}[timeframe]
    start=local_boundary(local_open,verified_zone)
    end=local_boundary(local_open+timedelta(hours=hours),verified_zone)
    return int(start.timestamp()*1000),int(end.timestamp()*1000)

def on_grid(value,step):
    if not isfinite(value) or not isfinite(step) or step<=0:return False
    q=Decimal(str(value))/Decimal(str(step))
    return abs(q-q.to_integral_value())<Decimal('0.000001')

def validate_quote(t):
    for k in ('bid','ask'):
        if not isfinite(t[k]) or t[k]<=0:raise Unverified('Missing/nonfinite executable quote')
    if t['ask']<t['bid']:raise Unverified('Crossed quote')
    if type(t['time_msc']) is not int:raise Unverified('Integer timestamp required')

def validate_stream(ticks):
    previous=None
    for index,t in enumerate(ticks):
        validate_quote(t)
        if previous is not None and t['time_msc']<previous:raise Unverified('Out-of-order ticks: do not silently sort')
        previous=t['time_msc']
        yield index,t  # Preserve repeated millisecond timestamps in provider order.

def execution_price(side,action,tick):
    validate_quote(tick)
    if side not in ('BUY','SELL') or action not in ('OPEN','CLOSE'):raise ValueError('Invalid side/action')
    return tick['ask'] if (side=='BUY')==(action=='OPEN') else tick['bid']

def validate_contract(volume,levels,contract,at_raw_ms):
    if not contract['valid_from_raw_ms']<=at_raw_ms<contract['valid_until_raw_ms']:raise Unverified('Contract not evidenced for this time')
    if not contract.get('evidence_id'):raise Unverified('Contract provenance missing')
    if not isfinite(volume) or not contract['volume_min']<=volume<=contract['volume_max'] or not on_grid(volume,contract['volume_step']):raise Unverified('Invalid volume/minimum/step')
    for p in levels:
        if p<=0 or not on_grid(p,contract['tick_size']):raise Unverified('Price off tick grid')

def first_executable_quote(ticks,decision_raw_ms,latency_ms=1,max_wait_ms=10000,max_spread=None):
    if latency_ms<1 or max_wait_ms<latency_ms:raise ValueError('Explicit positive latency and bounded wait required')
    for i,t in validate_stream(ticks):
        if t['time_msc']<decision_raw_ms+latency_ms:continue
        if t['time_msc']>decision_raw_ms+max_wait_ms:raise Unverified('Gap/disconnection: no quote in permitted execution window')
        if max_spread is not None and t['ask']-t['bid']>max_spread+1e-12:raise Unverified('Spread limit exceeded at execution; do not wait for a better quote')
        return i,t
    raise Unverified('No available quote; no synthetic fill')

def protective_trigger(side,sl,tp,tick):
    price=execution_price(side,'CLOSE',tick)
    if not (sl<tp if side=='BUY' else tp<sl):raise ValueError('Inconsistent protective levels')
    if price<=sl if side=='BUY' else price>=sl:return 'SL'
    if price>=tp if side=='BUY' else price<=tp:return 'TP'
    return None

def cash_result(side,entry,exit,volume,cash_per_price_unit_per_lot,commission,swap):
    if side not in ('BUY','SELL'):raise ValueError('Invalid side')
    vals=(entry,exit,volume,cash_per_price_unit_per_lot,commission,swap)
    if any(v is None or not isfinite(v) for v in vals):raise Unverified('Historical FX/commission/swap must be explicit; no zero default')
    if min(entry,exit,volume,cash_per_price_unit_per_lot)<=0 or commission<0:raise ValueError('Invalid pricing inputs')
    return (exit-entry)*(1 if side=='BUY' else -1)*volume*cash_per_price_unit_per_lot-commission+swap

def ohlc(ticks,field,start_raw_ms,end_raw_ms,last_updates_only=True):
    if field not in ('last','bid','ask'):raise ValueError('Unknown price basis')
    values=[t[field] for t in ticks if start_raw_ms<=t['time_msc']<end_raw_ms and isfinite(t.get(field,0)) and t.get(field,0)>0
            and (field!='last' or not last_updates_only or t.get('flags',0)&8)]
    return dict(zip(('open','high','low','close'),(values[0],max(values),min(values),values[-1]))) if values else None
