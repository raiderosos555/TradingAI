import json
from pathlib import Path
from collections import defaultdict
A=Path(__file__).resolve().parent
read=lambda n:json.loads((A/n).read_text(encoding='utf-8-sig'))
ts=read('trades_enriched.json');runs=read('run_statistics.json');groups=read('subgroup_statistics.json')
for alias in ('US100','OIL'):
 for period in ('development','validation'):
  run=f'validation/{alias}-{period}-base';tr=[t for t in ts if t['run']==run];print('MAIN',next(x for x in runs if x['run']==run))
  for dim in ('ALL','month','direction','trend_H4','trend_D1','volatility'):
   print(dim,[{k:g[k] for k in ('strategy','value','n','net','mean_R','pf','expectancy_block5_CI95')} for g in groups if g['run']==run and g['dimension']==dim])
  ordered=sorted(tr,key=lambda t:t['net'],reverse=True)
  print('concentration',{'best1':sum(t['net'] for t in ordered[:1]),'best3':sum(t['net'] for t in ordered[:3]),'best5':sum(t['net'] for t in ordered[:5]),'without5':sum(t['net'] for t in ordered[5:])})
  if period=='validation':
   print('worst3',[{k:t.get(k) for k in ('opened','direction','strategy','entry','sl','tp','ATR','SL_ATR','volume','risk','net','R','trend_H4','trend_D1','spread_cash_proxy','reclosed_inside_prior_range_first3h')} for t in sorted(tr,key=lambda t:t['net'])[:3]])
print('STRESS',[r for r in read('matched_trade_cost_stress.json') if r['instrument'] in ('US100','OIL') and r['period']=='validation'])
print('STRATEGIES',[{k:g[k] for k in ('instrument','strategy','n','net','mean_R','pf')} for g in groups if g['run'].startswith('validation/') and g['run'].endswith('-validation-base') and g['dimension']=='ALL'])
