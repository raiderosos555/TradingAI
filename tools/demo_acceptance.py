"""Bounded DEMO acceptance scenarios. Default: preflight without order_send.

US500 BUY 0.002 -> separate process closes 0.001 -> closes remainder.
EURUSD pending types 0.01 -> tighten SL -> cancel. No retries of recorded intents.
Every operation uses the production Risk Manager and Execution Engine.
"""
import argparse
import copy
import json
import os
import sys
from contextlib import ExitStack
from datetime import timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from trading_ai.analyzer import analyze
from trading_ai.broker import MT5Broker
from trading_ai.execution import ExecutionEngine
from trading_ai.journal import Journal, atomic_write, process_lock
from trading_ai.models import Blocked, digest, envelope, load_config, utcnow, validate_briefing
from trading_ai.reporter import report
from trading_ai.risk import RiskManager
from trading_ai.sync import FileTransport

STRATEGY = 'operator_demo_acceptance_v1'
CASES = ('market-open', 'market-close', 'BUY_LIMIT', 'SELL_LIMIT', 'BUY_STOP', 'SELL_STOP')


class AcceptanceRisk(RiskManager):
    def prepare_open(self, env, replacement=None):
        req, meta = super().prepare_open(env, replacement)
        expected = {'US500.pro': .002, 'EURUSD.pro': .01}
        if req.get('symbol') not in expected or req.get('volume') != expected[req['symbol']] or meta['risk_cash'] > 5:
            raise Blocked('Acceptance scenario exceeds minimum-volume / 5 PLN scope')
        return req, meta


def main(case, execute=False):
    base = load_config(ROOT / 'config.local.json')
    if base['mode'] != 'DRY_RUN' or base['live_enabled']:
        raise Blocked('Base configuration must remain DRY_RUN with LIVE disabled')
    if execute:
        consent = json.loads((ROOT / 'state/demo-acceptance-consent.json').read_text(encoding='utf-8'))
        if consent.get('scope') != 'bounded_demo_acceptance_v1':
            raise Blocked('Explicit bounded DEMO acceptance authorization missing')
    locks = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'TradingAI/locks' / digest([base['account_login'], base['account_server']])
    with ExitStack() as stack:
        stack.enter_context(process_lock(ROOT / 'state'))
        stack.enter_context(process_lock(locks))
        b = MT5Broker(base['terminal_path'], base.get('broker_time_offset_seconds', 0)); stack.callback(b.close)
        j = Journal(ROOT / 'state'); stack.callback(j.close)
        snap = b.snapshot(); a = snap['account']
        if [a['login'], a['server']] != [base['account_login'], base['account_server']] or a['trade_mode'] != 0 or a['currency'] != 'PLN':
            raise Blocked('Exact configured PLN DEMO account required')
        j.bind_account(a['login'], a['server'])
        if j.uncertain():
            raise Blocked('Uncertain operation requires reconciliation, never a new trial')
        c = copy.deepcopy(base); c['mode'] = 'DEMO' if execute else 'DRY_RUN'
        c['engine']['enabled'] = False
        c['strategies'] = list(set(c['strategies'] + [STRATEGY, 'operator_demo_smoke_v1']))
        c['risk']['max_trade_pct'] = min(.25, 5 / a['equity'] * 100)
        for alias, limit in (('US500', 10), ('EURUSD', 15)):
            c['symbols'][alias].update(trading_enabled=True, max_spread_points=limit,
                max_entry_deviation_points=250, deviation_points=5, cost_buffer_per_lot=100)
        path = ROOT / 'state/demo-acceptance-config.json'
        atomic_write(path, json.dumps(c, indent=2))
        risk = AcceptanceRisk(c, b, j, f"DEMO:{a['login']}", config_loader=lambda: load_config(path))
        engine = ExecutionEngine(risk)
        decisions = []
        result = {'case': case, 'execute_requested': execute, 'at': utcnow().isoformat(), 'decisions': decisions}
        def perform(env, rule='OPEN', ticket=None, **kwargs):
            outcome = engine.execute(env, rule, ticket, **kwargs)
            decisions.append({'rule': rule, **outcome})
            if outcome['status'] != ('CONFIRMED' if execute else 'DRY_RUN'):
                raise Blocked('Broker result requires review; do not retry')
            return outcome
        try:
            if case == 'market-close':
                saved = json.loads((ROOT / 'state/demo-acceptance-market-envelope.json').read_text(encoding='utf-8'))
                decisions.extend(engine.reconcile())
                op = j.operation('open:' + saved['signal']['id'])
                if not op or op['status'] != 'CONFIRMED':
                    raise Blocked('No confirmed opening to recover')
                pid = b.order_history(op['result']['order'])[0]['position_id']
                positions = [p for p in b.snapshot()['positions'] if p['identifier'] == pid]
                if len(positions) != 1 or abs(positions[0]['volume'] - .002) > 1e-9:
                    raise Blocked('Expected original 0.002 position absent; inspect broker')
                result['recovered_position_id'] = pid
                ticket = positions[0]['ticket']
                perform(saved, 'OPERATOR_CLOSE', ticket, close_volume=.001, operation_id='acceptance-partial')
                if execute:
                    rest = [p for p in b.snapshot()['positions'] if p['identifier'] == pid]
                    if len(rest) != 1 or abs(rest[0]['volume'] - .001) > 1e-9:
                        raise Blocked('Partial close volume not confirmed')
                    result['confirmed_remaining_volume'] = .001
                    perform(saved, 'OPERATOR_CLOSE', rest[0]['ticket'], operation_id='acceptance-remainder')
            else:
                if snap['positions'] or snap['orders']:
                    raise Blocked('Opening a test requires a flat account')
                alias = 'US500' if case == 'market-open' else 'EURUSD'
                expected_symbol = {'US500': 'US500.pro', 'EURUSD': 'EURUSD.pro'}[alias]
                if c['symbols'][alias]['broker'] != expected_symbol:
                    raise Blocked('Unexpected test contract mapping')
                kind = 'BUY' if case == 'market-open' else case
                m = b.market(expected_symbol, 'H1', 60); i, t = m['info'], m['tick']
                now = utcnow(); buy = kind.startswith('BUY'); sign = 1 if buy else -1
                price = t['ask'] if buy else t['bid']
                if kind.endswith('LIMIT'):
                    price -= sign * 100 * i['point']
                elif kind.endswith('STOP'):
                    price += sign * 100 * i['point']
                grid = lambda p: round(round(p / i['trade_tick_size']) * i['trade_tick_size'], i['digits'])
                distance = 5 if alias == 'US500' else 50 * i['point']
                sl, tp = grid(price - sign * distance), grid(price + sign * 2 * distance)
                invalid = min(sl, t['bid'] - distance) if buy else max(sl, t['ask'] + distance)
                structure = {'timeframe': 'H1', 'lookback': 60, 'trend': 'RANGE', 'invalidation': grid(invalid)}
                structure['trend'] = analyze(m, structure, now)['trend']
                signal = {'id': 'demo-acceptance-v1-' + case.lower(), 'instrument': alias,
                    'strategy': STRATEGY, 'kind': kind, 'entry': grid(price), 'sl': sl, 'tp': tp,
                    'volume': .002 if alias == 'US500' else .01, 'risk_pct': c['risk']['max_trade_pct'],
                    'valid_from': now.isoformat(), 'valid_until': (now + timedelta(minutes=5)).isoformat(),
                    'reason': 'Authorized bounded DEMO execution acceptance; technical test, not a strategy setup',
                    'structure': structure, 'management': {'break_even_r': None, 'trailing_distance': None,
                    'tp1': None, 'tp1_fraction': .5, 'close_on_invalidation': True}}
                brief = {'schema_version': '1.0', 'briefing_id': signal['id'], 'session': 'evening',
                         'generated_at': now.isoformat(), 'signals': [signal]}
                validate_briefing(brief); env = envelope(brief, signal)
                if j.operation('open:' + signal['id']):
                    raise Blocked('Scenario has a durable intent; do not repeat')
                if execute:
                    j.approve(env, a['login'], a['server'])
                req, meta = risk.prepare_open(env)
                check = b.check(req)
                if check.get('retcode') != 0:
                    raise Blocked('Broker order_check rejected scenario: ' + str(check))
                result.update(preflight={'request': req, 'risk_PLN': meta['risk_cash'], 'margin_PLN': meta['margin'], 'check': check})
                if execute:
                    if case == 'market-open':
                        atomic_write(ROOT / 'state/demo-acceptance-market-envelope.json', json.dumps(env, indent=2))
                    opened = perform(env)
                    if case != 'market-open':
                        ticket = opened['result']['order']
                        perform(env, 'TIGHTEN_PENDING', ticket, new_sl=grid(sl + sign * 10 * i['point']))
                        current = j.effective_operation(j.operation('open:' + signal['id']))['payload']['envelope']
                        perform(current, 'OPERATOR_CANCEL', ticket, operation_id='acceptance-cancel')
            end = b.snapshot()
            result.update(status='CONFIRMED' if execute else 'PREFLIGHT_OK',
                          remaining_positions=end['positions'], remaining_orders=end['orders'])
        except Exception as exc:
            result.update(status='BLOCKED_OR_REVIEW_REQUIRED', reason=str(exc))
            raise
        finally:
            c['mode'] = 'DRY_RUN'
            for spec in c['symbols'].values(): spec['trading_enabled'] = False
            atomic_write(path, json.dumps(c, indent=2))
            atomic_write(ROOT / f'state/demo-acceptance-{case.lower()}-result.json', json.dumps(result, indent=2))
            data, md = report(b, j, decisions, 'DRY_RUN', base)
            FileTransport(ROOT / 'exchange').publish(data, md)
        print(json.dumps(result, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('case', choices=CASES); p.add_argument('--execute', action='store_true')
    args = p.parse_args()
    try: main(args.case, args.execute)
    except Exception as exc:
        print('BLOCKED: ' + str(exc), file=sys.stderr); sys.exit(2)
