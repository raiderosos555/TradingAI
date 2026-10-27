"""Bounded child, MT5 READ ONLY. Raw coordinates are never normalized in storage."""
import argparse,gzip,json,time
from datetime import datetime,timezone,timedelta
from pathlib import Path
from quality import inspect_ticks,clock_anchor

def now():return datetime.now(timezone.utc).isoformat()
def write(path,value):path.write_text(json.dumps(value,allow_nan=False,separators=(',',':')),encoding='utf-8')
def array(a):return None if a is None else [dict(zip(a.dtype.names,row)) for row in a.tolist()]

def main():
    p=argparse.ArgumentParser();p.add_argument('request',type=Path);args=p.parse_args()
    r=json.loads(args.request.read_text());out=args.request.parent;c=r['config']
    import MetaTrader5 as mt5
    result=dict(started_at=now(),status='STARTED',orders_sent=0,symbols={},raw_time_normalization='NONE')
    write(out/'phase.json',result)
    if not mt5.initialize(path=c['terminal_path'],timeout=10000):raise RuntimeError(str(mt5.last_error()))
    try:
        a=mt5.account_info();terminal=mt5.terminal_info()
        if not (a and terminal and a.login==c['account_login'] and a.server==c['account_server'] and a.trade_mode==0 and terminal.connected):
            raise RuntimeError('Connected matching DEMO account required')
        result['environment']=dict(package=mt5.__version__,version=mt5.version(),account=a._asdict(),terminal=terminal._asdict())
        write(out/'environment.json',result['environment'])
        for symbol in r['symbols']:
            before=time.time();tick=mt5.symbol_info_tick(symbol);after=time.time();info=mt5.symbol_info(symbol)
            if tick is None or info is None:
                result['symbols'][symbol]={'status':'SYMBOL_UNAVAILABLE','error':mt5.last_error()};continue
            tick=tick._asdict();anchor=clock_anchor(tick['time_msc'],before,after,r.get('ea_offset'))
            data=dict(symbol=symbol,received_at=now(),info=info._asdict(),latest_tick_raw=tick,clock_anchor=anchor)
            write(out/(symbol+'.snapshot.json'),data)
            offset=anchor.get('candidate_offset_seconds')
            if anchor['status']!='CONSISTENT_CANDIDATE':
                # This symbol may be inactive. Use contemporaneously corroborated
                # batch offset ONLY for retrieval, not as an accepted UTC segment.
                offset=r.get('retrieval_offset')
            if offset is None:
                result['symbols'][symbol]={'status':'NO_RETRIEVAL_COORDINATE','anchor':anchor};continue
            end_limit=int((time.time()+offset-5)//60)*60*1000
            cursor=r['cursors'].get(symbol)
            start=cursor['end_raw_ms'] if cursor else end_limit-60000
            end=min(start+120000,end_limit)
            item=dict(status='NO_CLOSED_INTERVAL',anchor=anchor)
            if start<end:
                request_start=datetime.fromtimestamp((start-2000)/1000,timezone.utc)
                request_end=datetime.fromtimestamp(end/1000,timezone.utc)
                fetch_before=now();ticks=mt5.copy_ticks_range(symbol,request_start,request_end,mt5.COPY_TICKS_ALL)
                error=mt5.last_error();fetch_after=now();rows=array(ticks)
                if rows is None:item=dict(status='API_ERROR',error=error,anchor=anchor)
                else:
                    # Keep the complete response, including query overlaps, in provider order.
                    with gzip.open(out/(symbol+'.ticks.json.gz'),'wt',encoding='utf-8',compresslevel=1) as f:
                        json.dump(rows,f,separators=(',',':'),allow_nan=False)
                    q=inspect_ticks(rows,start,end,None if cursor is None else cursor['tail'])
                    item=dict(status='CAPTURED',anchor=anchor,start_raw_ms=start,end_raw_ms=end,
                        query_start_raw_ms=start-2000,query_end_raw_ms=end,fetch_before=fetch_before,
                        fetch_after=fetch_after,api_count=len(rows),api_error=error,quality=q,
                        backlog_ms=max(0,end_limit-end),retrieval_offset=offset,
                        utc_normalization_accepted=False)
            if r['capture_bars'] and symbol in r['strategy_symbols']:
                rates={}
                for name,tf in [('H1',mt5.TIMEFRAME_H1),('H4',mt5.TIMEFRAME_H4),('D1',mt5.TIMEFRAME_D1)]:
                    before_rates=now();bars=mt5.copy_rates_from_pos(symbol,tf,1,220)
                    rates[name]=dict(received_at=now(),requested_at=before_rates,exclude_current_bar=True,
                        rows=array(bars),error=mt5.last_error(),historical_utc_verified=False)
                write(out/(symbol+'.bars.json'),rates)
            # Current broker calculators are observed evidence, not a historical tariff.
            costs=[];v=info.volume_min;point=info.trade_tick_size
            if tick['bid']>0 and tick['ask']>=tick['bid'] and v>0 and point>0:
                for side,action,price in [('BUY',mt5.ORDER_TYPE_BUY,tick['ask']),('SELL',mt5.ORDER_TYPE_SELL,tick['bid'])]:
                    for direction in [-1,1]:
                        close=price+direction*point*10
                        costs.append(dict(side=side,volume=v,open=price,close=close,
                            profit=mt5.order_calc_profit(action,symbol,v,price,close),
                            margin=mt5.order_calc_margin(action,symbol,v,price),received_at=now()))
            write(out/(symbol+'.cost-probes.json'),costs)
            result['symbols'][symbol]=item
            write(out/'phase.json',dict(status='PROGRESS',finished_symbol=symbol,at=now()))
        positions=mt5.positions_get();orders=mt5.orders_get()
        # Broad raw-coordinate interval deliberately covers both host UTC and shifted
        # broker time. Ticket identity deduplicates observations, not tick rows.
        lower=datetime.now(timezone.utc)-timedelta(days=2);upper=datetime.now(timezone.utc)+timedelta(days=1)
        deals=mt5.history_deals_get(lower,upper);history_orders=mt5.history_orders_get(lower,upper)
        broker=dict(received_at=now(),positions=None if positions is None else [x._asdict() for x in positions],
            orders=None if orders is None else [x._asdict() for x in orders],
            deals=None if deals is None else [x._asdict() for x in deals],
            history_orders=None if history_orders is None else [x._asdict() for x in history_orders],
            history_query_start=lower.isoformat(),history_query_end=upper.isoformat(),
            time_basis='RAW_BROKER_COORDINATE; NO_IMPLICIT_UTC',error=mt5.last_error())
        write(out/'broker.json',broker)
        result.update(status='COMPLETED',finished_at=now())
        write(out/'result.json',result)
    finally:mt5.shutdown()

if __name__=='__main__':main()
