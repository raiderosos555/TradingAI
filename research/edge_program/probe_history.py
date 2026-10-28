"""Bounded MT5 availability probe: max 70 D1 bars + 700 ticks requested.
Read only, no symbol selection, chart/config changes, login, or order API.
Not a historical download campaign or certification of complete coverage.
"""
import json
from datetime import datetime,timezone
from pathlib import Path
import MetaTrader5 as mt5

ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'private/mt5-availability.json'

def main():
    if OUT.exists():raise RuntimeError('Preserve existing probe')
    cfg=json.loads((ROOT/'config.demo.json').read_text())
    if not mt5.initialize(path=cfg['terminal_path'],timeout=10000):raise RuntimeError(str(mt5.last_error()))
    results=[]
    try:
        a=mt5.account_info()
        if not a or a.trade_mode!=0 or a.login!=cfg['account_login'] or a.server!=cfg['account_server']:
            raise RuntimeError('Expected DEMO identity not confirmed')
        result=dict(at=datetime.now(timezone.utc).isoformat(),company=a.company,requests=results,contracts={},orders_sent=0)
        fields=['chart_mode','point','trade_tick_size','trade_contract_size','trade_calc_mode','currency_profit','volume_min','volume_step','swap_mode','swap_long','swap_short','swap_rollover3days']
        for alias,spec in cfg['symbols'].items():
            info=mt5.symbol_info(spec['broker'])
            result['contracts'][alias]={k:getattr(info,k) for k in fields} if info else None
            for date in ('2020-01-15T12:00:00+00:00','2024-01-15T12:00:00+00:00'):
                when=datetime.fromisoformat(date)
                for kind in ('D1','ticks'):
                    rows=(mt5.copy_rates_from(spec['broker'],mt5.TIMEFRAME_D1,when,5) if kind=='D1'
                          else mt5.copy_ticks_from(spec['broker'],when,50,mt5.COPY_TICKS_ALL))
                    error=mt5.last_error();n=0 if rows is None else len(rows)
                    records=[] if rows is None else [{k:v.item() for k,v in zip(rows.dtype.names,row)} for row in rows]
                    entry=dict(alias=alias,kind=kind,requested_from=date,requested_count=5 if kind=='D1' else 50,
                               n=n,error=error,first_raw=int(rows[0]['time']) if n else None,
                               last_raw=int(rows[-1]['time']) if n else None,records=records)
                    results.append(entry)
                    OUT.write_text(json.dumps(result,indent=2),encoding='utf-8')
                    print(json.dumps({k:v for k,v in entry.items() if k!='records'}),flush=True)
    finally:mt5.shutdown()

if __name__=='__main__':main()
