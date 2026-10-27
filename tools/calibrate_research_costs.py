"""Read-only historical Bid/Ask sample. Estimates spread, not realized slippage or future costs."""
import gzip
import json
import sys
from datetime import datetime,timedelta,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from trading_ai.models import load_config,canonical,utcnow
from trading_ai.broker import MT5Broker
from trading_ai.journal import atomic_write

c=load_config(ROOT/'config.local.json')
out=ROOT/'exchange/research/cost-sample-20261022'
out.mkdir(parents=True,exist_ok=True)
b=MT5Broker(c['terminal_path'],c.get('broker_time_offset_seconds',0))
rows=[]
try:
 snap=b.snapshot()
 if [snap['account']['login'],snap['account']['server']]!=[c['account_login'],c['account_server']]:raise ValueError('Account mismatch')
 for alias,spec in c['symbols'].items():
  info=b.required(b.mt5.symbol_info(spec['broker']),'contract')
  meta={k:info.get(k) for k in ['point','trade_tick_size','trade_contract_size','trade_calc_mode','currency_profit',
      'currency_margin','swap_mode','swap_long','swap_short','swap_rollover3days','volume_min','volume_step']}
  for hour,minute in [(8,0),(13,30),(20,30)]:
   start=datetime(2026,10,22,hour,minute,tzinfo=timezone.utc);end=start+timedelta(minutes=15)
   try:
    ticks=b.ticks(spec['broker'],start,end)
    valid=[t for t in ticks if t['bid']>0 and t['ask']>=t['bid']]
    spreads=sorted((t['ask']-t['bid'])/info['point'] for t in valid)
    quantile=lambda p:spreads[round((len(spreads)-1)*p)] if spreads else None
    payload={'instrument':alias,'start':start.isoformat(),'end':end.isoformat(),'contract_now':meta,'ticks':ticks}
    path=out/f'{alias}-{hour:02}{minute:02}.json.gz'
    with gzip.open(path,'wt',encoding='utf-8') as f:json.dump(payload,f,separators=(',',':'))
    row={'instrument':alias,'start':start.isoformat(),'ticks':len(ticks),'valid_quotes':len(valid),
         'p50_spread_points':quantile(.5),'p95_spread_points':quantile(.95),'max_spread_points':max(spreads) if spreads else None,
         'contract_now':meta,'status':'OBSERVED' if valid else 'NO_DATA'}
   except Exception as exc:row={'instrument':alias,'start':start.isoformat(),'status':'UNAVAILABLE','reason':str(exc)}
   rows.append(row);print({k:v for k,v in row.items() if k!='contract_now'},flush=True)
 summary={'at':utcnow().isoformat(),'orders_sent':0,'results':rows,
  'limitations':['Three fixed 15-minute windows on one day are not a representative full-history cost model',
   'Quantiles weighted by tick count, not elapsed time','No executed slippage measurements or verified historical swap/commission',
   'Contract metadata is current; broker timestamp correction uses the observed +2h offset']}
 atomic_write(out/'summary.json',canonical(summary))
 lines=['# Próbka rzeczywistych spreadów Bid/Ask','',
  'Odczyt historyczny MT5, bez zleceń. Trzy ustalone okna po 15 minut, 22.10.2026. Nie jest to pełna kalibracja kosztów.', '',
  '| Instrument | UTC | Ticki | Mediana spreadu (punkty) | P95 | Status |','|---|---|---:|---:|---:|---|']
 for r in rows:
  fmt=lambda x:'—' if x is None else f'{x:.2f}'
  lines.append(f"| {r['instrument']} | {r['start'][11:16]} | {r.get('ticks',0)} | {fmt(r.get('p50_spread_points'))} | {fmt(r.get('p95_spread_points'))} | {r['status']} |")
 lines+=['',*['- '+x for x in summary['limitations']]]
 atomic_write(out/'report.md','\n'.join(lines))
finally:b.close()
