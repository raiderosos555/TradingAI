"""One explicitly approved DEMO SELL/open-close test. Never a continuous trader.

Default is a read-only preflight. Sending requires --execute-approved-test, recorded
operator consent matching the reviewed document, and all independent risk gates.
"""
import argparse
import copy
import json
import math
import os
import sys
from contextlib import ExitStack
from datetime import timedelta
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from trading_ai.models import Blocked, load_config, utcnow, envelope, validate_briefing, digest, read_json
from trading_ai.journal import Journal, atomic_write, process_lock
from trading_ai.broker import MT5Broker
from trading_ai.risk import RiskManager
from trading_ai.execution import ExecutionEngine
from trading_ai.analyzer import analyze
from trading_ai.reporter import report
from trading_ai.sync import FileTransport


class TestRisk(RiskManager):
    def __init__(self, *args, test_symbol='GOLD.pro', **kwargs):
        super().__init__(*args, **kwargs)
        if test_symbol not in {'GOLD.pro', 'US500.pro'}:
            raise Blocked('Unsupported DEMO test contract')
        self.test_symbol = test_symbol

    def prepare_open(self, env, replacement=None):
        request,meta=super().prepare_open(env,replacement)
        if request['action']!=1 or request['type']!=1 or request['symbol']!=self.test_symbol or request['volume']!=.001 or meta['risk_cash']>5:
            raise Blocked('Request exceeds the explicitly approved DEMO test scope')
        return request,meta


def main(execute=False, instrument='GOLD'):
    if instrument not in {'GOLD', 'US500'}:
        raise Blocked('Unsupported DEMO test profile')
    symbol = {'GOLD':'GOLD.pro', 'US500':'US500.pro'}[instrument]
    prefix = 'demo-test' if instrument == 'GOLD' else 'demo-us500-test'
    spread_limit = 30 if instrument == 'GOLD' else 10
    base=load_config(ROOT/'config.local.json')
    # A preview cannot inherit permission from another contract. Sending always
    # requires the separate consent file matching this exact reviewed profile.
    if execute or instrument == 'GOLD':
        consent=read_json(ROOT/f'state/{prefix}-consent.json')
        if consent['plan_sha256']!=digest((ROOT/f'docs/{prefix}-plan.md').read_text(encoding='utf-8')):
            raise Blocked('Reviewed DEMO test plan changed after operator approval')
    if base['mode']!='DRY_RUN' or base['live_enabled'] or base['symbols'][instrument]['broker']!=symbol:
        raise Blocked('Unexpected base configuration; no DEMO test')
    account_lock=Path(os.environ.get('LOCALAPPDATA',str(Path.home())))/'TradingAI'/'locks'/digest([base['account_login'],base['account_server']])
    with ExitStack() as stack:
        stack.enter_context(process_lock(ROOT/'state'));stack.enter_context(process_lock(account_lock))
        b=MT5Broker(base['terminal_path'],base.get('broker_time_offset_seconds',0));stack.callback(b.close)
        j=Journal(ROOT/'state');stack.callback(j.close)
        snap=b.snapshot();a=snap['account']
        if [a['login'],a['server']]!=[base['account_login'],base['account_server']] or a['trade_mode']!=0 or a['currency']!='PLN':
            raise Blocked('Exact approved PLN DEMO account required')
        j.bind_account(a['login'],a['server'])
        if snap['positions'] or snap['orders'] or j.uncertain(): raise Blocked('Test requires a flat account and reconciled journal')
        if any(op['payload']['envelope']['signal']['strategy']=='operator_demo_smoke_v1' for op in j.operations()):
            raise Blocked('An approved demo test intent already exists; never open another')
        now=utcnow();market=b.market(symbol,'H1',60);i=market['info'];entry=market['tick']['bid'];tick=i['trade_tick_size']
        structure={'timeframe':'H1','lookback':60,'trend':'DOWN','invalidation':round(math.ceil((entry+5)/tick)*tick,i['digits'])}
        if analyze(market,structure,now)['trend']!='DOWN': raise Blocked('Approved SELL technical test requires current DOWN structure')
        c=copy.deepcopy(base);c['mode']='DEMO' if execute else 'DRY_RUN';c['engine']['enabled']=False
        c['strategies']=['operator_demo_smoke_v1'];c['risk']['max_trade_pct']=min(.25,5/a['equity']*100)
        c['symbols'][instrument].update(trading_enabled=True,max_spread_points=spread_limit,max_entry_deviation_points=10,deviation_points=5,cost_buffer_per_lot=100)
        s={'id':'demo-smoke-'+instrument.lower()+'-'+now.strftime('%Y%m%dT%H%M%S'),'instrument':instrument,'strategy':'operator_demo_smoke_v1',
           'kind':'SELL','entry':entry,'sl':structure['invalidation'],'tp':round(math.floor((entry-10)/tick)*tick,i['digits']),
           'volume':.001,'risk_pct':c['risk']['max_trade_pct'],'valid_from':now.isoformat(),'valid_until':(now+timedelta(minutes=5)).isoformat(),
           'reason':'One-position technical DEMO test; requires separate contract-specific approval before sending',
           'structure':structure,'management':{'break_even_r':None,'trailing_distance':None,'tp1':None,'tp1_fraction':.5,'close_on_invalidation':True}}
        brief={'schema_version':'1.0','briefing_id':s['id'],'session':'morning','generated_at':now.isoformat(),'signals':[s]}
        validate_briefing(brief);env=envelope(brief,s)
        config_path=ROOT/f'state/{prefix}-config.json';atomic_write(config_path,json.dumps(c,indent=2))
        result={'at':now.isoformat(),'instrument':instrument,'execute_requested':execute,'decisions':[],
                'observed_quote':market['tick'], 'spread_points':(market['tick']['ask']-market['tick']['bid'])/i['point'],
                'max_spread_points':spread_limit,'day_start':j.setting('day_start')}
        try:
            risk=TestRisk(c,b,j,f"DEMO:{a['login']}",config_loader=lambda:load_config(config_path),test_symbol=symbol)
            executor=ExecutionEngine(risk)
            if execute: j.approve(env,a['login'],a['server'])
            request,meta=risk.prepare_open(env)
            check=b.check(request)
            if check.get('retcode')!=0: raise Blocked('Broker order_check rejected the test')
            result.update(preflight={'request':request,'risk_cash_PLN':meta['risk_cash'],'margin_PLN':meta['margin'],'order_check':check},signal=brief)
            result['status']='PREFLIGHT_OK'
            atomic_write(ROOT/f'state/{prefix}-preflight.json',json.dumps(result,indent=2))
            if not execute:
                print(json.dumps({'status':'PREFLIGHT_OK','orders_sent':0,'request':request,'risk_PLN':meta['risk_cash'],'margin_PLN':meta['margin']},indent=2));return
            opening=executor.execute(env);result['decisions'].append({'rule':'OPEN',**opening})
            if opening['status']!='CONFIRMED': raise Blocked('Open is uncertain; inspect broker before any further instruction')
            # Resolve actual position from stable broker identity, never from a guessed ticket.
            history=b.order_history(opening['result']['order']);ids={o.get('position_id') for o in history if o.get('position_id')}
            positions=[p for p in b.snapshot()['positions'] if p['identifier'] in ids]
            if len(positions)!=1: raise Blocked('Opened position no longer uniquely present; broker history requires review')
            opened_report,md=report(b,j,result['decisions'],'DEMO',c);FileTransport(ROOT/'exchange').publish(opened_report,md)
            closing=executor.execute(env,'OPERATOR_CLOSE',positions[0]['ticket'],operation_id='approved-smoke-close')
            result['decisions'].append({'rule':'OPERATOR_CLOSE',**closing})
            result['status']='COMPLETE' if closing['status']=='CONFIRMED' and not any(p['identifier'] in ids for p in b.snapshot()['positions']) else 'REVIEW_REQUIRED'
        except Exception as exc:
            result.update(status='BLOCKED_OR_REVIEW_REQUIRED',reason=str(exc))
            raise
        finally:
            c['mode']='DRY_RUN';c['symbols'][instrument]['trading_enabled']=False
            atomic_write(config_path,json.dumps(c,indent=2))
            result['current_mode']='DRY_RUN'
            atomic_write(ROOT/f'state/{prefix}-result.json',json.dumps(result,indent=2))
            final_report,md=report(b,j,result['decisions'],'DRY_RUN',base);FileTransport(ROOT/'exchange').publish(final_report,md)
        print(json.dumps({'status':result.get('status'),'decisions':result['decisions'],'mode':'DRY_RUN'},indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--execute-approved-test',action='store_true')
    parser.add_argument('--instrument',choices=['GOLD','US500'],default='GOLD')
    args=parser.parse_args()
    try: main(args.execute_approved_test,args.instrument)
    except Exception as exc: print('BLOCKED: '+str(exc),file=sys.stderr);sys.exit(2)
