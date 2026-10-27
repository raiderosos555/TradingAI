"""Local continuous DEMO runtime. No AI calls, credentials or LIVE activation.

Engine and UTC-boundary recorder run in separate processes. Authorization is a
bounded, operator-recorded configuration hash; clock corrections require fresh
EA evidence and broker ticks. Loss of evidence never grants an entry permission.
"""
from __future__ import annotations

import argparse
import copy
import ctypes
import json
import logging
import os
import time
from contextlib import ExitStack
from datetime import timedelta
from logging.handlers import RotatingFileHandler
from pathlib import Path

from .models import Blocked, canonical, digest, load_config, number, read_json, timestamp, utcnow
from .journal import Journal, atomic_write, process_lock


def configuration_hash(config):
    normalized = copy.deepcopy(config)
    normalized.pop('broker_time_offset_seconds', None)
    return digest(normalized)


def require_authorization(config, journal, now, clock_required=True):
    r = config['runtime']
    if config['mode'] != 'DEMO' or config['live_enabled'] or config['live_allowlist']:
        raise Blocked('Runtime is restricted to DEMO')
    auth = journal.setting('runtime_authorization:' + r['authorization_id'])
    if not auth or journal.setting('runtime_revoked') or (journal.root / 'runtime' / 'REVOKED').exists():
        raise Blocked('Runtime authorization missing or revoked')
    if auth['config_hash'] != configuration_hash(config):
        raise Blocked('Runtime configuration changed after authorization')
    if not timestamp(r['starts_at']) <= now < timestamp(r['ends_at']):
        raise Blocked('Outside authorized runtime entry window')
    if config.get('broker_time_offset_seconds', 0) not in auth['allowed_offsets']:
        raise Blocked('Runtime broker clock offset is not authorized')
    if clock_required:
        proof = journal.setting('runtime_clock')
        if (not proof or proof['offset'] != config.get('broker_time_offset_seconds', 0)
                or not 0 <= (now-timestamp(proof['at'])).total_seconds() <= 30
                or proof.get('account') != [config['account_login'], config['account_server']]):
            raise Blocked('Fresh verified broker clock required')
    return auth


def capture_boundary(config, snapshot, now, journal):
    """Record only an actual broker snapshot in UTC seconds 0..5 of this day."""
    a = snapshot['account']; at = timestamp(snapshot['as_of'])
    if ([a['login'], a['server']] != [config['account_login'], config['account_server']]
            or a['trade_mode'] != 0 or not snapshot['terminal']['connected']):
        raise Blocked('Boundary snapshot requires connected configured DEMO account')
    number(a['equity'], 'day start equity')
    start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    if not 0 <= (at-start).total_seconds() <= 5 or not 0 <= (now-at).total_seconds() <= 2:
        return False
    return journal.record_day_start({'date': start.date().isoformat(), 'equity': a['equity'],
        'account': a['login'], 'server': a['server'], 'as_of': snapshot['as_of'],
        'source': 'Independent UTC boundary recorder: fresh broker snapshot within seconds 0..5'})


def entry_blockers(config, snapshot, now, journal):
    """Account-wide readiness only; per-signal gates still run before every order."""
    from .risk import RiskManager
    reasons = []
    try:
        require_authorization(config,journal,now)
    except Blocked as exc:
        reasons.append(str(exc))
    try:
        RiskManager(config,None,journal).daily_budget(snapshot,now)
    except Blocked as exc:
        reasons.append(str(exc))
    if journal.uncertain():reasons.append('Uncertain broker operation')
    if (journal.root/'STOP').exists():reasons.append('Emergency STOP')
    return reasons


class ClockGuard:
    def __init__(self):
        self.offset = None
        self.observations = set()

    def observe(self, config, data, now, raw_ticks, allowed_offsets):
        if (data.get('read_only') is not True or data.get('schema_version') != '1.0'
                or [data.get('account_login'), data.get('account_server')] != [config['account_login'], config['account_server']]
                or not -2 <= now.timestamp()-data.get('retrieved_at_utc', 0) <= 900):
            raise Blocked('Fresh account-bound EA clock evidence unavailable')
        offset = data.get('server_minus_gmt_seconds')
        if offset not in allowed_offsets:
            raise Blocked('Unapproved EA clock offset')
        if self.offset != offset:
            self.offset, self.observations = offset, set()
        self.observations = {at for at in self.observations if 0 <= now.timestamp()-at <= 900}
        self.observations.add(data['retrieved_at_utc'])
        if len(self.observations) < 2:
            raise Blocked('Waiting for two distinct EA clock exports')
        # At least two independent contracts must corroborate EA offset with fresh ticks.
        fresh = [symbol for symbol, raw_time_msc in raw_ticks.items()
                 if -2 <= now.timestamp() - (raw_time_msc/1000-offset) <= config['risk']['max_tick_age_seconds']]
        if len(fresh) < 2:
            raise Blocked('Waiting for fresh quotes from two contracts to verify broker clock')
        return {'at': now.isoformat(), 'offset': offset, 'symbols': fresh,
                'account': [config['account_login'], config['account_server']],
                'ea_export_at': data['retrieved_at_utc']}


def prevent_idle_sleep():
    if os.name == 'nt':
        # Refresh idle timer; screen may turn off and explicit user sleep is respected.
        return bool(ctypes.windll.kernel32.SetThreadExecutionState(0x00000001))
    return False


def status_file(root, role, **data):
    # Status is telemetry, not the durable trading journal. A Windows reader
    # may temporarily deny replacement; that must not terminate error handling.
    content = canonical({'at': utcnow().isoformat(), 'pid': os.getpid(), **data})
    for attempt in range(3):
        try:
            atomic_write(root / f'{role}-status.json', content)
            return True
        except OSError:
            if attempt < 2:
                time.sleep(.05 * (attempt + 1))
            else:
                logging.getLogger('runtime.' + role).exception('Status publication failed; trading journal unchanged')
    return False


def run(config_path, state, exchange, role, once=False):
    from .broker import MT5Broker
    from .cli import cycle
    from .execution import ExecutionEngine
    from .manager import PositionManager
    from .risk import RiskManager
    from .strategy import policy_hash
    from .sync import FileTransport
    config_path, state, exchange = Path(config_path).resolve(), Path(state).resolve(), Path(exchange).resolve()
    home = state / 'runtime'; home.mkdir(parents=True, exist_ok=True)
    logger = logging.getLogger('runtime.' + role); logger.setLevel(logging.INFO)
    handler = RotatingFileHandler(home / (role+'.log'), maxBytes=2_000_000, backupCount=3, encoding='utf-8')
    logger.addHandler(handler)
    initial = load_config(config_path)
    if 'runtime' not in initial:
        raise Blocked('Bounded runtime configuration required')
    broker = None
    with ExitStack() as stack:
        stack.enter_context(process_lock(home / role))
        if role == 'engine':
            stack.enter_context(process_lock(state))
            lock = Path(os.environ.get('LOCALAPPDATA', str(Path.home()))) / 'TradingAI/locks' / digest([initial['account_login'], initial['account_server']])
            stack.enter_context(process_lock(lock))
        j = Journal(state); stack.callback(j.close)
        c = initial
        guard = ClockGuard(); last_full = last_report = 0; last_message = None
        try:
            while not (home / 'DISABLED').exists():
                started = time.monotonic(); now = utcnow()
                try:
                    c = load_config(config_path)
                    if [c['account_login'], c['account_server'], c['terminal_path']] != [initial['account_login'], initial['account_server'], initial['terminal_path']]:
                        raise Blocked('Runtime account/terminal changed; stop and reconfigure')
                    awake = prevent_idle_sleep()
                    if broker is None:
                        broker = MT5Broker(c['terminal_path'], c.get('broker_time_offset_seconds', 0))
                    snap = broker.snapshot()
                    if [snap['account']['login'], snap['account']['server']] != [c['account_login'], c['account_server']] or snap['account']['trade_mode'] != 0:
                        raise Blocked('Unexpected account; runtime never changes login')
                    if role == 'baseline':
                        recorded = capture_boundary(c, snap, utcnow(), j)
                        status_file(home, role, status='RECORDED' if recorded else 'OBSERVING',
                                    day_start=j.setting('day_start'), sleep_idle_reset=awake)
                    else:
                        auth = j.setting('runtime_authorization:' + c['runtime']['authorization_id'])
                        if not auth or auth['config_hash'] != configuration_hash(c):
                            raise Blocked('Runtime configuration lacks matching operator authorization')
                        ea = read_json(Path(broker.paths()['data_path']) / 'MQL5/Files/TradingAI' / f"calendar_{c['account_login']}.json")
                        raw = {}
                        for spec in c['symbols'].values():
                            tick = broker.mt5.symbol_info_tick(spec['broker'])
                            if tick: raw[spec['broker']] = tick.time_msc
                        proof = guard.observe(c, ea, utcnow(), raw, auth['allowed_offsets'])
                        c['broker_time_offset_seconds'] = proof['offset']
                        broker.time_offset = proof['offset']
                        j.set_setting('runtime_clock', proof)
                        effective = home / 'effective-config.json'
                        atomic_write(effective, canonical(c))
                        def current_config():
                            current = load_config(config_path)
                            # Always re-read the authorized source before each risk gate.
                            current['broker_time_offset_seconds'] = proof['offset']
                            return current
                        permission_error = None
                        try:
                            require_authorization(c, j, utcnow())
                            policy = j.setting('strategy_policy')
                            if not policy or policy['hash'] != policy_hash(c) or (timestamp(policy['until'])-utcnow()).total_seconds() < 3600:
                                until = min(utcnow()+timedelta(hours=24), timestamp(c['runtime']['ends_at']))
                                j.set_setting('strategy_policy', {'hash': policy_hash(c), 'until': until.isoformat()})
                                j.event('runtime_policy_renewal', {'authorization_id': c['runtime']['authorization_id'], 'until': until.isoformat()})
                        except Blocked as exc:
                            permission_error = str(exc)
                        activation = f"DEMO:{c['account_login']}"
                        if time.monotonic()-last_full >= 60:
                            publish = time.monotonic()-last_report >= 1800
                            result = cycle(c, broker, j, FileTransport(exchange), activation,
                                           current_config, publish=publish)
                            last_full = time.monotonic()
                            if publish: last_report = last_full
                            if result['broker_error']: raise Blocked(result['broker_error'])
                        else:
                            e = ExecutionEngine(RiskManager(c, broker, j, activation, config_loader=current_config))
                            e.reconcile(); PositionManager(e).run()
                        current_snapshot = broker.snapshot()
                        blockers = entry_blockers(c,current_snapshot,utcnow(),j)
                        status_file(home, role, status='WAITING' if blockers else 'RUNNING',
                                    reason='; '.join(blockers) or None, entry_blockers=blockers,
                                    per_signal_checks='Calendar, quote, structure and risk are checked for each request',
                                    mode='DEMO', starts_at=c['runtime']['starts_at'],
                                    ends_at=c['runtime']['ends_at'], clock=proof, day_start=j.setting('day_start'),
                                    quarantined=j.uncertain(), stop_active=(state/'STOP').exists(),
                                    sleep_idle_reset=awake, positions=len(current_snapshot['positions']), orders=len(current_snapshot['orders']))
                    last_message = None
                except Exception as exc:
                    message = str(exc)
                    waiting = message.startswith('Waiting for ')
                    status_file(home, role, status='WAITING' if waiting else 'BLOCKED', reason=message,
                                day_start=j.setting('day_start'), mode=c['mode'],
                                starts_at=c['runtime']['starts_at'], ends_at=c['runtime']['ends_at'])
                    if message != last_message:
                        logger.warning('%s %s', utcnow().isoformat(), message); last_message = message
                    if broker:
                        broker.close(); broker = None
                if once: break
                # Boundary observer accelerates around midnight; it never sends orders.
                current_time = utcnow()
                second = (current_time-current_time.replace(hour=0, minute=0, second=0, microsecond=0)).total_seconds()
                interval = .25 if role == 'baseline' and (second < 10 or second > 86390) else (5 if role == 'baseline' else 10)
                time.sleep(max(.05, interval-(time.monotonic()-started)))
        finally:
            if broker: broker.close()
            if not once:
                status_file(home, role, status='STOPPED')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--config', default='config.demo.json'); p.add_argument('--state', default='state')
    p.add_argument('--exchange', default='exchange'); p.add_argument('--role', choices=['engine', 'baseline'], required=True)
    p.add_argument('--once', action='store_true')
    a = p.parse_args()
    try:
        run(a.config, a.state, a.exchange, a.role, a.once)
    except BaseException:
        logging.getLogger('runtime.' + a.role).exception('Unhandled runtime termination')
        raise
