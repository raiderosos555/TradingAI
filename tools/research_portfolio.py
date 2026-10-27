"""Evaluate three predeclared hypotheses on one shared account, offline only."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from trading_ai.models import read_json,canonical,digest,timestamp,utcnow
from trading_ai.journal import atomic_write
from trading_ai.portfolio_research import replay_portfolio,VARIANTS

folder=ROOT/'exchange/research/history-20261024'
out=folder/'portfolio-v1'
m=read_json(folder/'manifest.json');datasets={}
for item in m['instruments']:
 d=read_json(folder/(item['instrument']+'.json'))
 assert digest(d)==item['data_sha256']
 datasets[item['instrument']]=d
start=timestamp(m['requested_start']).timestamp();end=timestamp(m['requested_end']).timestamp()
edges=[int(start+(end-start)*k/3) for k in range(4)]
atomic_write(out/'protocol.json',canonical({'at':utcnow().isoformat(),'variants':VARIANTS,'edges':edges,
 'source_sha256':__import__('hashlib').sha256((ROOT/'trading_ai/portfolio_research.py').read_bytes()).hexdigest(),
 'config_hash':m['config_hash'],'data_hashes':{i['instrument']:i['data_sha256'] for i in m['instruments']},
 'selection':'All predeclared hypotheses reported. No automatic promotion; previously seen history.'}))
rows=[]
for variant in VARIANTS:
 for k in range(3):
  for multiple in (1,2):
   result=replay_portfolio(m['config'],datasets,variant,edges[k],edges[k+1],m['initial_equity'],multiple)
   assert result['max_positions_observed']<=2
   assert result['max_reserved_pct']<=m['config']['risk']['max_total_pct']+1e-8
   assert abs(result['net']-sum(t['net'] for t in result['trades']))<1e-6
   atomic_write(out/f'{variant}-{k+1}-cost{multiple}.json',canonical(result))
   row={key:result[key] for key in ('variant','net','profit_factor','win_rate','max_drawdown','max_positions_observed','max_reserved_pct','rejected')}
   row.update(period=k+1,cost_multiple=multiple,trades=len(result['trades']))
   rows.append(row);print(row,flush=True)
atomic_write(out/'summary.json',canonical({'at':utcnow().isoformat(),'results':rows,'promoted':False}))
lines=['# Portfel: trzy hipotezy strukturalne','',
 'Wspólne equity, maksymalnie 2 pozycje, 0,1% na pozycję / 0,2% łącznie / 0,5% dziennie. Minimalne loty. Wszystkie 7 rynków konkuruje o ten sam kapitał.',
 'Trzy kolejne okresy po około 60 dni; każdy zaczyna się od tego samego kapitału, bez pozycji. Historia była już oglądana. Nie jest to niezależny forward ani wdrożenie nowej strategii.', '',
 '| Hipoteza | Okres | Koszty × | Transakcje | Trafność | PF | Netto PLN | Max DD PLN |',
 '|---|---:|---:|---:|---:|---:|---:|---:|']
for r in rows:
 rate='—' if r['win_rate'] is None else f"{100*r['win_rate']:.1f}%"
 pf='—' if r['profit_factor'] is None else f"{r['profit_factor']:.2f}"
 lines.append(f"| {r['variant']} | {r['period']} | {r['cost_multiple']} | {r['trades']} | {rate} | {pf} | {r['net']:.2f} | {r['max_drawdown']:.2f} |")
lines+=['','## Ograniczenia','',*['- '+x for x in result['limitations']], '',
 'Koszty są przybliżone. Mniejsze limity portfela i spreadu mogą ograniczyć liczbę transakcji w stresie. Każda nowa hipoteza ma osobny rejestr; żadnej nie promowano do handlu.']
atomic_write(out/'report.md','\n'.join(lines))
