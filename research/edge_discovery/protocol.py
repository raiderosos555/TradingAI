"""Frozen before the first run; exploratory research, never trading authority."""
VERSION = 'edge-discovery-20261027-v1'
SEED = 20261027
SYMBOLS = ['GOLD', 'US500', 'OIL', 'EURPLN', 'EURUSD', 'GBPUSD', 'US100']
FAMILIES = ['trend', 'momentum', 'extreme_reversion', 'breakout',
            'false_breakout', 'volatile_momentum', 'clock_breakout', 'cross_momentum']
LEADERS = {'US500': ('US100', 1), 'US100': ('US500', 1),
           'EURUSD': ('GBPUSD', 1), 'GBPUSD': ('EURUSD', 1)}
SPLIT_RAW = '2026-08-01'
HORIZON_HOURS = 4
BOOTSTRAPS = 4000
BLOCK_DAYS = 5
TESTS = 53  # seven families x seven markets + four cross-market tests
TICK_DELAY_MS = 250
TICK_MAX_WAIT_MS = 10000
TICK_SIDE_MAX_AGE_MS = 10000

DESCRIPTIONS = {
 'trend': ('Persistence of slow information/flows', 'BUY if EMA20 > EMA50, SELL otherwise'),
 'momentum': ('Delayed response to order flow', 'Direction of close minus close six completed bars ago; absolute move >= 0.5 ATR14'),
 'extreme_reversion': ('Temporary inventory pressure unwinds', 'Oppose the last one-bar close move if absolute move > 2 ATR14'),
 'breakout': ('Stop orders and information beyond established range', 'Close outside high/low of previous 20 bars; follow break'),
 'false_breakout': ('Failed price discovery and trapped breakout traders', 'High breaches prior 20-bar high but closes below: SELL; symmetric BUY; reject double-sided breach'),
 'volatile_momentum': ('Information arrival can strengthen continuation', 'Momentum rule only when ATR14 > 1.25 times its preceding 100-bar median'),
 'clock_breakout': ('Participation and liquidity differ during the day', 'Break previous six-bar range; entry raw clock hour 14..17; NOT a verified New York/London session'),
 'cross_momentum': ('Related equity/FX markets transmit common flows', 'Follow matched leader six-bar momentum >= 0.5 leader ATR; only four predeclared directed pairs'),
}
