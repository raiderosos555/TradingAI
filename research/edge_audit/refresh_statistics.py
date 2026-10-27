"""Recalculate only statistics from verified enriched records, avoiding economic reruns."""
from pathlib import Path
import ast,json,csv,math,hashlib
from collections import defaultdict
from datetime import datetime
import numpy as np
A=Path(__file__).resolve().parent
source=ast.parse((A/'analyze.py').read_text(encoding='utf-8'))
for node in source.body:
 if isinstance(node,ast.FunctionDef) and node.name in ('epoch','stat'):
  exec(compile(ast.Module(body=[node],type_ignores=[]),'audit_stat','exec'))
def read(n):return json.loads((A/n).read_text(encoding='utf-8-sig'))
def save(n,x):
 (A/(n+'.json')).write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
 if isinstance(x,list) and x:
  with (A/(n+'.csv')).open('w',newline='',encoding='utf-8-sig') as f:
   keys=list(dict.fromkeys(k for r in x for k in r));w=csv.DictWriter(f,keys);w.writeheader();w.writerows(x)
ts=read('trades_enriched.json');runs=read('run_statistics.json');groups=defaultdict(list)
for t in ts:
 for dim in ['ALL','direction','hour_UTC','weekday_UTC','month','trend_H1','trend_H4','trend_D1','volatility','reason','reclosed_inside_prior_range_first3h']:
  groups[t['run'],t['instrument'],t['strategy'],dim,str(t.get(dim,'ALL' if dim=='ALL' else 'UNKNOWN'))].append(t)
sub=[]
for (run,alias,strategy,dim,value),v in groups.items():sub.append({**stat(v),'run':run,'instrument':alias,'strategy':strategy,'dimension':dim,'value':value})
save('subgroup_statistics',sub)
for r in runs:r.update(stat([t for t in ts if t['run']==r['run']]))
save('run_statistics',runs)
stress=read('matched_trade_cost_stress.json')
for r in stress:
 v=[]
 for t in ts:
  if t['run']!=f"validation/{r['instrument']}-{r['period']}-base":continue
  extra=(r['cost_multiple']-1)*(t['spread_cash_proxy']+t['slippage_cash_proxy']+t['commission_cash']-t['swap_cash_model'])
  v.append({**t,'net':t['net']-extra,'R':(t['net']-extra)/t['risk']})
 r.update(stat(v))
save('matched_trade_cost_stress',stress)
summary=read('audit_summary.json');summary['bootstrap']='Circular chronological trade blocks length5,600 resamples,seed20261024; not multiplicity-adjusted; N<20 unavailable';save('audit_summary',summary)
uncertainty=[]
for alias in ('US100','OIL'):
 for period in ('development','validation'):
  v=sorted([t for t in ts if t['run']==f'validation/{alias}-{period}-base'],key=lambda t:t['closed']);rr=np.array([t['R'] for t in v]);n=len(rr)
  for block in (3,5,10):
   rng=np.random.default_rng(20261024);starts=rng.integers(0,n,(30000,math.ceil(n/block)));ix=((starts[:,:,None]+np.arange(block))%n).reshape(30000,-1)[:,:n];means=rr[ix].mean(1)
   uncertainty.append({'instrument':alias,'period':period,'n':n,'block':block,'mean_R':float(rr.mean()),'CI95':np.quantile(means,[.025,.975]).tolist(),'Bonferroni_7_CI':np.quantile(means,[.025/7,1-.025/7]).tolist(),'caveat':'Only accounts for seven market comparisons; full research multiplicity unknown; exploratory'})
save('uncertainty_sensitivity',uncertainty)
print('REFRESHED',len(sub),'groups',uncertainty)
