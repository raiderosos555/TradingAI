"""Offline ablation study. Never modifies or authorizes the deployed strategy."""
import copy
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from trading_ai.models import read_json, canonical, timestamp, digest, utcnow
from trading_ai.journal import atomic_write
from trading_ai.backtest import replay
from trading_ai.research_validation import segments, summarize

folder=ROOT/'exchange/research/history-20261024'
m=read_json(folder/'manifest.json')
baseline=read_json(folder/'validation/summary.json')
out=folder/'candidates'
variants={'breakout_only':{'enable_false_breakout':False},
          'false_breakout_only':{'enable_breakout':False}}
atomic_write(out/'protocol.json',canonical({'at':utcnow().isoformat(),'variants':variants,
    'automatic_promotion':False,'validation_previously_seen':True,
    'acceptance':'Positive net and PF>1 in development AND validation, >=30 trades in each; further cost/portfolio/news forward validation still required',
    'purpose':'Isolate losing strategy components; exploratory research, not independent evidence'}))
rows=[]
for variant,changes in variants.items():
 for item in m['instruments']:
  alias=item['instrument']; data=read_json(folder/(alias+'.json'))
  assert digest(data)==item['data_sha256']
  c=copy.deepcopy(m['config']);c['engine'].update(changes)
  for period,bars in segments(data['bars'],timestamp(m['validation_start']).timestamp(),200):
   costs=next(r['costs'] for r in baseline['results'] if r['instrument']==alias and r['period']==period and r['scenario']=='base')
   result=replay(c,alias,bars,data['contract'],costs,m['initial_equity'])
   row={'variant':variant,'instrument':alias,'period':period,**summarize(result)}
   rows.append(row)
   atomic_write(out/(alias+'-'+variant+'-'+period+'.json'),canonical(result))
   print(variant,alias,period,row['trades'],round(row['net'],2),flush=True)
atomic_write(out/'summary.json',canonical({'at':utcnow().isoformat(),'results':rows,'automatic_promotion':False}))
lines=['# Badanie rozdzielenia strategii','',
 'Badanie eksploracyjne na wcześniej oglądanej historii. Wariantów nie włączono do handlu. Bez historycznego feedu nie testujemy rzekomego wpływu newsów wstecz.', '',
 '| Wariant | Rynek | Transakcje weryfikacji | Trafność | PF | Netto wcześniej | Netto weryfikacji |',
 '|---|---|---:|---:|---:|---:|---:|']
for r in rows:
 if r['period']!='validation':continue
 dev=next(x for x in rows if x['variant']==r['variant'] and x['instrument']==r['instrument'] and x['period']=='development')
 rate='—' if r['win_rate'] is None else f"{r['win_rate']*100:.1f}%"
 pf='—' if r['profit_factor'] is None else f"{r['profit_factor']:.2f}"
 lines.append(f"| {r['variant']} | {r['instrument']} | {r['trades']} | {rate} | {pf} | {dev['net']:.2f} | {r['net']:.2f} |")
lines+=['','Oddzielne symulacje instrumentów, PLN, minimalne loty, koszty jak w poprzednim raporcie. Nie sumować jako wspólnego portfela. Wybór na tej historii wymaga nowej próby forward.']
atomic_write(out/'report.md','\n'.join(lines))
