"""Synthetic execution contract tests, NOT historical replay or a broker adapter.

Uses frozen production policy, only an in-memory broker, explicit UTC fixtures.
Server fills at first observed executable quote are an unverified test convention.
No latency/slippage/liquidity inference or historical broker timezone is made.
"""
from pathlib import Path
import copy
import hashlib
import json
import sys
import tempfile
from datetime import datetime, timedelta, timezone

A = Path(__file__).resolve().parent
FROZEN = A / 'source_snapshot'
CONFIG = json.loads((A / 'config.v1.json').read_text())
assert CONFIG['broker'] == 'IN_MEMORY_ONLY' and CONFIG['time_basis'] == 'EXPLICIT_UTC_FIXTURE'
assert CONFIG['cash_per_price_unit_per_lot'] == 100 and CONFIG['swap'] == 0
assert CONFIG['currency'] == 'USD' and not CONFIG['full_backtest_allowed']
for item in json.loads((A / 'source_manifest.json').read_text()):
    assert hashlib.sha256((FROZEN / item['path']).read_bytes()).hexdigest() == item['sha256']
sys.path.insert(0, str(FROZEN))
sys.path.insert(0, str(A.parent))
from model import validate_quote, protective_trigger, on_grid
from trading_ai import risk as risk_module
from trading_ai.risk import RiskManager
from trading_ai.execution import ExecutionEngine
from trading_ai.manager import PositionManager
from trading_ai.simulation import SimBroker, fixture
from trading_ai.journal import Journal
from trading_ai.models import envelope, Blocked

assert Path(risk_module.__file__).resolve().is_relative_to(FROZEN)


class TickBroker(SimBroker):
    """Explicit single-contract synthetic cash factor: 100 USD / unit / lot."""
    def __init__(self, now, side, commission):
        super().__init__(now)
        if commission < 0:
            raise ValueError('Explicit nonnegative commission required')
        self.side, self.commission = side, commission
        self.server_events = []
        self.ledger = []
        self.quotes = []
        self.revalue()

    def market(self, *args, **kwargs):
        market = super().market(*args, **kwargs)
        if self.side == 'SELL':
            for b in market['bars']:
                b.update(open=200-b['open'], close=200-b['close'],
                         high=200-b['low'], low=200-b['high'])
        return market

    def revalue(self):
        super().quote(self.tick['bid'], self.tick['ask'])
        profit = sum(p['profit'] for p in self.positions)
        equity = self.account['balance'] + profit
        margin = sum(p['volume'] * 100 for p in self.positions)
        self.account.update(profit=profit, equity=equity, margin_free=equity-margin)

    def book(self, request, source):
        if request['action'] not in {1, 6}:
            raise NotImplementedError('Pending activation/cancellation not modeled in this harness')
        if self.send_code != 10009:
            raise NotImplementedError('Partial/rejected broker fills require a separate explicit model')
        if request['action'] == 1:
            v = request['volume']
            if not self.info['volume_min'] <= v <= self.info['volume_max'] or not on_grid(v, self.info['volume_step']):
                raise ValueError('Invalid synthetic volume')
            if 'position' in request:
                p = next(p for p in self.positions if p['ticket'] == request['position'])
                if v > p['volume'] + 1e-9 or request['type'] == p['type']:
                    raise ValueError('Invalid close side/volume')
        previous = len(self.deals)
        result = super().send(request)
        for d in self.deals[previous:]:
            d['commission'] = -self.commission * d['volume']
            self.account['balance'] += d['profit'] + d['commission']
            self.ledger.append({**copy.deepcopy(d), 'source': source,
                                'time_msc': self.tick['time_msc']})
        self.revalue()
        return result

    def send(self, request):
        if not self.terminal['connected']:
            raise Blocked('Application disconnected')
        return self.book(request, 'APPLICATION')

    def feed(self, tick):
        validate_quote(tick)
        if tick['time_msc'] < self.tick['time_msc']:
            raise ValueError('Chronology regression; never sort input')
        self.tick = dict(tick, time=tick['time_msc']//1000)
        self.now = datetime.fromtimestamp(tick['time_msc']/1000, timezone.utc)
        self.quotes.append(copy.deepcopy(self.tick))
        self.revalue()
        # A supplied feed is server-visible even if the application is disconnected.
        # No tick supplied means no interpolation or asserted stop time/fill.
        for p in list(self.positions):
            side = 'BUY' if p['type'] == 0 else 'SELL'
            trigger = protective_trigger(side, p['sl'], p['tp'], self.tick)
            if trigger:
                request = dict(action=1, position=p['ticket'], symbol=p['symbol'],
                               type=1-p['type'], volume=p['volume'], magic=p['magic'], comment=p['comment'])
                self.book(request, 'SERVER_'+trigger)
                self.server_events.append({'trigger': trigger, 'time_msc': tick['time_msc'],
                                           'price': self.ledger[-1]['price']})


class Scenario:
    def __init__(self, side='BUY', volume=.08, commission=CONFIG['commission_per_lot_per_side'], management=None):
        if side not in {'BUY', 'SELL'}:
            raise ValueError(side)
        (A / 'scratch').mkdir(exist_ok=True)
        self.temp = tempfile.TemporaryDirectory(dir=A / 'scratch')
        self.start = datetime(2026, 10, 22, 12, tzinfo=timezone.utc)
        self.b = TickBroker(self.start, side, commission)
        self.c, self.plan = fixture(self.start)
        self.c.update(mode='DEMO', terminal_path='IN_MEMORY_ONLY')
        self.c['risk'].update(CONFIG['limits'])
        self.c['symbols']['GOLD']['max_volume'] = volume
        s = self.plan['signals'][0]
        s.update(risk_pct=.1, tp=103.02)
        if side == 'SELL':
            s.update(kind='SELL', entry=100., sl=101.02, tp=97.)
            s['structure'].update(trend='DOWN', invalidation=100.92)
            s['management']['tp1'] = 98.5
        if management:
            s['management'].update(management)
        self.env = envelope(self.plan, s)
        self.j = Journal(Path(self.temp.name))
        self.j.set_setting('day_start', dict(date=self.start.date().isoformat(), equity=10000,
                                          account=123456, server='SIMULATOR', source='SYNTHETIC_UTC_FIXTURE'))
        self.j.approve(self.env, 123456, 'SIMULATOR')
        self.r = RiskManager(self.c, self.b, self.j, activation='DEMO:123456', clock=lambda: self.b.now)
        self.e = ExecutionEngine(self.r)
        self.m = PositionManager(self.e)
        self.decisions = []
        self.last_cycle_ms = int(self.start.timestamp()*1000)

    def open(self):
        result = self.e.execute(self.env)
        assert result['status'] == 'CONFIRMED', result
        return self.b.positions[0]

    def step(self, seconds, bid, ask=None, connected=True, cycle=True):
        tick = dict(time_msc=int((self.start+timedelta(seconds=seconds)).timestamp()*1000),
                    bid=bid, ask=round(bid+.02, 2) if ask is None else ask, last=100., flags=6)
        self.b.terminal['connected'] = connected
        self.b.feed(tick)
        results = []
        if cycle and tick['time_msc']-self.last_cycle_ms >= CONFIG['manager_cycle_seconds']*1000:
            self.last_cycle_ms = tick['time_msc']
            try:
                results = self.m.run()
            except Blocked as e:
                results = [dict(status='HELD', reason=str(e))]
        self.decisions.extend(copy.deepcopy(results))
        return results

    def trace(self):
        return dict(data_class='SYNTHETIC_CONTROLLED_TEST', time_basis='EXPLICIT_UTC_FIXTURE',
                    commission_per_lot_per_side=self.b.commission, cash_factor=100, swap=0,
                    latency_model='synchronous control test only', config=self.c, envelope=self.env,
                    quotes=self.b.quotes, ledger=self.b.ledger, server_events=self.b.server_events,
                    decisions=self.decisions, positions=self.b.positions, account=self.b.account)

    def close(self):
        self.j.close()
        self.temp.cleanup()
