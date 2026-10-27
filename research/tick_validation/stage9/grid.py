"""Contract-valid deterministic diagnostic grid, independent of MetaTrader."""
from decimal import Decimal, ROUND_HALF_UP

def number(value):
    if value is None or isinstance(value, bool):
        raise ValueError('Explicit finite number required')
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError('Non-finite number')
    return result

def make_grid(info, quote, config):
    tick, minimum, step, maximum = map(number, [info['trade_tick_size'], info['volume_min'], info['volume_step'], info['volume_max']])
    bid, ask = map(number, [quote['bid'], quote['ask']])
    if min(tick, minimum, step, maximum, bid, ask) <= 0 or bid > ask or minimum > maximum or minimum % step:
        raise ValueError('Invalid contract or quote')
    volumes = []
    for increment in config['volume_step_increments']:
        if type(increment) is not int or increment < 0:
            raise ValueError('Invalid volume increment')
        volume = minimum + increment * step
        if volume <= maximum and volume not in volumes:
            volumes.append(volume)
    rows = []
    for side in ['BUY', 'SELL']:
        # These prices are diagnostic arguments, not executable orders or historical fills.
        base = ask if side == 'BUY' else bid
        entry = (base / tick).to_integral_value(rounding=ROUND_HALF_UP) * tick
        for volume in volumes:
            for ticks in config['price_tick_deltas']:
                if type(ticks) is not int or ticks == 0:
                    raise ValueError('Invalid tick displacement')
                exit_price = entry + tick * ticks
                if min(entry, exit_price) <= 0:
                    raise ValueError('Diagnostic price is not positive')
                rows.append(dict(side=side, volume=str(volume), entry=str(entry), exit=str(exit_price), delta_ticks=ticks))
    if not rows:
        raise ValueError('Empty diagnostic grid')
    return rows

def stable_fx(before, after):
    # Timestamp equality also prevents treating different observations as a stable bracket.
    if before is None or after is None:
        return False
    try:
        bid, ask = number(before['bid']), number(before['ask'])
        return 0 < bid <= ask and all(before[k] == after[k] for k in ['bid', 'ask', 'time_msc'])
    except (KeyError, ValueError):
        return False
