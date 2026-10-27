"""Independent invariant checks of audit outputs; never sends orders or changes runtime."""
import json,csv,hashlib,copy,math
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from briefing_research import compare,validate
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
checks=[]
def check(name,condition):
 if not condition:raise AssertionError(name)
 checks.append(name)
for item in read(A/'inputs/inventory.json'):
 check('unchanged:'+item['path'],hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'])
ts=read(A/'trades_enriched.json');runs=read(A/'run_statistics.json');group=defaultdict(list)
for t in ts:group[t['run']].append(t)
check('88 historical runs',len(runs)==88)
check('4294 historical records',len(ts)==4294)
for run in runs:
 v=group[run['run']];check('count:'+run['run'],len(v)==run['n']);check('net:'+run['run'],abs(sum(t['net'] for t in v)-run['reported_net'])<1e-6)
 if v:check('R:'+run['run'],abs(sum(t['R'] for t in v)/len(v)-run['mean_R'])<1e-12)
for name,rows in [('trades_enriched',ts),('run_statistics',runs),('subgroup_statistics',read(A/'subgroup_statistics.json')),('matched_trade_cost_stress',read(A/'matched_trade_cost_stress.json')),('sensitivity',read(A/'sensitivity.json')),('walk_forward',read(A/'walk_forward.json'))]:
 with (A/(name+'.csv')).open(encoding='utf-8-sig',newline='') as f:csvrows=list(csv.DictReader(f))
 check('CSV row count:'+name,len(csvrows)==len(rows))
for t in ts:
 for tf in ('H1','H4','D1'):
  k='context_'+tf+'_last_closed'
  if k in t:check('closed context:'+t['run']+str(t['index'])+tf,datetime.fromisoformat(t[k])<=datetime.fromisoformat(t['opened']))
 if 'MAE_pre_exit_price_R' in t:check('MAE bounds',t['MAE_pre_exit_price_R']<=t['MAE_including_exit_price_R']+1e-12)
 if 'MFE_pre_exit_price_R' in t:check('MFE bounds',t['MFE_pre_exit_price_R']<=t['MFE_including_exit_price_R']+1e-12)
stress=read(A/'matched_trade_cost_stress.json')
for alias in {r['instrument'] for r in stress}:
 for period in ('development','validation'):
  v=sorted([r for r in stress if r['instrument']==alias and r['period']==period],key=lambda r:r['cost_multiple'])
  check('stress fixed N',len({r['n'] for r in v})==1);check('stress cost monotonic',v[0]['net']>=v[1]['net']>=v[2]['net'])
sens=read(A/'sensitivity.json');check('54 sensitivity cells',len(sens)==54)
check('No all-period baseline-cost winners',not any(all(r['net']>0 for r in sens if r['family']==family and r['stop_ATR']==stop and r['cost_multiple']==1) for family in {r['family'] for r in sens} for stop in {r['stop_ATR'] for r in sens}))
for r in read(A/'walk_forward.json'):check('WF past-only folds',max(r['training_folds'])<r['fold'])
basis=read(A/'price_basis_check.json')
check('Seven instrument H1 reconstructions',len(basis)==7)
for r in basis:
 check('Last OHLC exact:'+r['instrument'],r['last_max_abs_OHLC_diff']<1e-10)
 check('Bid OHLC differs:'+r['instrument'],r['bid_max_abs_OHLC_diff']>0)
for r in read(A/'observed_cost_sensitivity.json'):
 original=next(x for x in runs if x['run']==f"validation/{r['instrument']}-{r['period']}-base")
 check('Observed stress fixed trade count',r['n']==original['n'])
 check('Observed stress never silently improves cost',r['net']<=original['net']+1e-6)
record={'schema_version':'edge_context_v1','id':'TEST_ONLY','instrument':'US100','broker_symbol':'US100.pro','source_reference':'synthetic isolated validation fixture','source_complete':True,'published_at':'2026-10-01T08:00:00+00:00','first_seen_at':'2026-10-01T08:05:00+00:00','valid_until':'2026-10-01T10:00:00+00:00','decision':'OPEN','direction':'BUY','entry':100,'sl':99,'tp':102}
trade={'run':'isolated_test','index':0,'instrument':'US100','opened':'2026-10-01T08:02:00+00:00','direction':'BUY','net':0,'R':0}
mapping={'US100':'US100.pro'}
check('Reject news not yet received',compare([record],[trade],mapping)[0]['comparison']=='NO_ELIGIBLE_CONTEXT')
trade['opened']='2026-10-01T08:06:00+00:00';check('Known compatible context',compare([record],[trade],mapping)[0]['comparison']=='AGREES')
other={**record,'id':'SECOND'};check('Conflicting active context ambiguous',compare([record,other],[trade],mapping)[0]['comparison']=='AMBIGUOUS')
check('Incomplete context excluded',compare([{**record,'source_complete':False}],[trade],mapping)[0]['comparison']=='NO_ELIGIBLE_CONTEXT')
try:validate(read(A/'briefing_future_template.json'));valid=True
except (ValueError,TypeError):valid=False
check('Template cannot pass as actual data',not valid)
for name in ('DATA_AUDIT','TRADE_DIAGNOSTICS','US100_VS_OIL','EDGE_HYPOTHESES','VALIDATION_REPORT','NEXT_STEPS'):check('report:'+name,(A/(name+'.md')).stat().st_size>1000)
summary={'passed':len(checks),'failed':0,'checks_scope':'Hashes, arithmetic, CSV counts, closed-time causality, cost monotonicity, portfolio selection chronology, briefing availability and ambiguity. Not a profitability or real execution certification.'}
(A/'verification.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(summary)
