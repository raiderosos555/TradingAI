"""Same-path sensitivity to measured one-day P95 spreads. Not a full cost calibration."""
import json,csv,ast,math
from pathlib import Path
from datetime import datetime
import numpy as np
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
tree=ast.parse((A/'analyze.py').read_text(encoding='utf-8'))
for node in tree.body:
 if isinstance(node,ast.FunctionDef) and node.name in ('stat','epoch'):exec(compile(ast.Module(body=[node],type_ignores=[]),'stats','exec'))
sample=read(ROOT/'exchange/research/cost-sample-20261022/summary.json')['results'];ts=read(A/'trades_enriched.json');rows=[]
for alias in sorted({r['instrument'] for r in sample}):
 p95=max(r['p95_spread_points'] for r in sample if r['instrument']==alias)
 for period in ('development','validation'):
  v=[t for t in ts if t['run']==f'validation/{alias}-{period}-base'];new=[]
  for t in v:
   extra=max(0,p95/t['spread_points']-1)*t['spread_cash_proxy']
   new.append({**t,'net':t['net']-extra,'R':(t['net']-extra)/t['risk']})
  rows.append({'instrument':alias,'period':period,'base_spread_points':v[0]['spread_points'] if v else None,'observed_max_window_p95_points':p95,
   'spread_ratio':p95/v[0]['spread_points'] if v else None,'model':'FIXED_PATH_SPREAD_ONLY_ONE_DAY_P95; NOT_LAST_TO_BID_FIX',**stat(new)})
(A/'observed_cost_sensitivity.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
with (A/'observed_cost_sensitivity.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)
print([{k:r[k] for k in ('instrument','base_spread_points','observed_max_window_p95_points','n','net','pf')} for r in rows if r['period']=='validation'])
