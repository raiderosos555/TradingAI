"""Compare old/new unchanged strategy rules on an explicit control tape only."""
import json,tempfile
from pathlib import Path
from controls import setup,run_control,ticks,START
from trading_ai.backtest import replay as old_replay

def compare(side):
    alias='GOLD';symbol='TEST_GOLD'
    with tempfile.TemporaryDirectory(prefix='trading-old-control-') as folder:
        c,b,j=setup(folder,aliases=(alias,),side=side,end_ms=START+3600000)
        try:
            actual=[e['tick']['last'] for e in ticks((alias,),side,duration_ms=3600000,stride_ms=1000) if e['kind']=='tick']
            # Exactly the old assumption under audit: chart Last supplied as Bid.
            bar=dict(time=START//1000,open=actual[0],high=max(actual),low=min(actual),close=actual[-1],tick_volume=len(actual))
            contract=dict(b.contracts[symbol],cash_per_price_unit_per_lot=100)
            old=old_replay(c,alias,b.bars[symbol].closed+[bar],contract,
                dict(spread_points=2,slippage_points=0,commission_per_lot_roundtrip=4,swap_per_lot_per_day=0))
        finally:j.close()
    new=run_control(aliases=(alias,),side=side,events=ticks((alias,),side,duration_ms=3600000,stride_ms=1000),end_ms=START+3600000,max_wait_ms=1500)
    new_entries=[d for d in new['ledger'] if d['entry']==0]
    signals={i['signal']['signal']['id'] for scan in new['scans'] for i in scan['items'] if i.get('signal')}
    return dict(data_class='SYNTHETIC_CONTROL_ONLY',side=side,
        comparability_limits=['One exact H1 control window; OHLC cannot represent intrabar event sequence',
            'Old engine has no shared portfolio/calendar parity; one instrument only',
            'Known constant synthetic costs/FX, not broker history',
            'Difference combines price basis, fill timing and management; not an isolated spread attribution'],
        old=dict(entries=len(old['trades']),net=old['net'],profit_factor=old['profit_factor'],
            expectancy_R=old['sum_R']/len(old['trades']) if old['trades'] else None,max_drawdown_cash=old['max_drawdown_cash'],trades=old['trades']),
        corrected=dict(signals=len(signals),entries=len(new_entries),metrics=new['metrics'],ledger=new['ledger']),
        entry_count_delta=len(new_entries)-len(old['trades']),net_delta=new['metrics']['net_marked']-old['net'],
        first_entry_price_delta=new_entries[0]['price']-old['trades'][0]['entry'] if new_entries and old['trades'] else None,
        historical_profitability_claim=False)

if __name__=='__main__':
    out=Path(__file__).resolve().parent/'control-comparison.json'
    if out.exists():raise SystemExit('Comparison already exists')
    values=[compare(side) for side in ['BUY','SELL']]
    out.write_text(json.dumps(values,indent=2),encoding='utf-8')
    print([(r['side'],r['old']['net'],r['corrected']['metrics']['net_marked']) for r in values])
