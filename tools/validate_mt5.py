"""Integration validation on the connected terminal. This script cannot submit orders."""
import json
import sys
from pathlib import Path
from datetime import timedelta

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from trading_ai.broker import MT5Broker
from trading_ai.collector import Collector, MarketArchive
from trading_ai.models import load_config, utcnow
from trading_ai.risk import RiskManager
from trading_ai.strategy import SignalEngine
from trading_ai.journal import Journal, atomic_write, process_lock


class ReadOnlyBroker(MT5Broker):
    def send(self, request):
        raise RuntimeError("Integration validator never sends orders")


def main():
    c = load_config(ROOT/'config.local.json')
    b = ReadOnlyBroker(c['terminal_path'], c.get('broker_time_offset_seconds',0))
    archive = MarketArchive(ROOT/'state',c['account_login'],c['account_server'],c.get('broker_time_offset_seconds',0))
    journal = Journal(ROOT/'state')
    try:
        first=b.snapshot()
        if [first['account']['login'],first['account']['server']] != [c['account_login'],c['account_server']]:
            raise RuntimeError('Account identity mismatch')
        collection=Collector(c,b,archive).collect()
        scans=SignalEngine(c,b,journal).scan(utcnow())
        contracts=[]
        for alias,spec in c['symbols'].items():
            m=b.market(spec['broker'],'H1',200)
            i,t=m['info'],m['tick']
            lot=i['volume_min']
            entry=t['ask']
            distance=max(i['trade_tick_size']*100,entry*.001)
            sl=round(int((entry-distance)/i['trade_tick_size'])*i['trade_tick_size'],i['digits'])
            tp=round(int((entry+2*distance)/i['trade_tick_size'])*i['trade_tick_size'],i['digits'])
            request={'action':1,'symbol':spec['broker'],'volume':lot,'type':0,'sl':sl,'tp':tp,
                     'magic':c['magic'],'comment':'TA:read-only-check','deviation':spec['deviation_points'],
                     'type_filling':RiskManager.filling(i)}
            if i['trade_exemode'] != 2: request['price']=entry
            contracts.append({'instrument':alias,'symbol':spec['broker'],'volume_min':lot,'sl_loss_account_currency':-b.profit(0,spec['broker'],lot,entry,sl),
                              'margin_account_currency':b.margin(0,spec['broker'],lot,entry),'order_check':b.check(request),
                              'quote_age_seconds':utcnow().timestamp()-t['time_msc']/1000})
            # A longer H1 sample is archived for strategy replay, separately from execution checks.
            historical=b.market(spec['broker'],'H1',1200)
            archive.save_bars(spec['broker'],'H1',historical['bars'])
        history=b.history(utcnow()-timedelta(days=7),utcnow())
        archive.save_history(history)
        last=b.snapshot()
        result={'at':utcnow().isoformat(),'read_only':True,'orders_sent':0,'account_type':'DEMO' if first['account']['trade_mode']==0 else 'LIVE_READ_ONLY',
                'account_currency':first['account']['currency'],'broker_time_offset_seconds':c.get('broker_time_offset_seconds',0),
                'collection':collection,'contracts':contracts,'market_analysis':scans,'history_deals_7d':len(history['deals']),
                'positions_before':len(first['positions']),'positions_after':len(last['positions']),
                'pending_before':len(first['orders']),'pending_after':len(last['orders'])}
        atomic_write(ROOT/'state'/'mt5-integration.json',json.dumps(result,indent=2))
        summary={'read_only':True,'orders_sent':0,'account_type':result['account_type'],
                 'ohlcv_series_ok':sum(x.get('bars',0)>0 for x in collection),
                 'tick_symbols_ok':sum('ticks' in x for x in collection),
                 'analysis_ok':sum(x.get('analysis') is not None for x in scans),
                 'order_checks':[{'symbol':x['symbol'],'retcode':x['order_check']['retcode']} for x in contracts],
                 'positions_before':len(first['positions']),'positions_after':len(last['positions'])}
        atomic_write(ROOT/'docs'/'mt5-readonly-validation.json',json.dumps(summary,indent=2))
        print(json.dumps(summary,indent=2))
    finally:
        b.close();archive.close();journal.close()


if __name__=='__main__':
    with process_lock(ROOT/'state'): main()
