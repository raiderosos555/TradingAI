"""Predeclared finite sensitivity and expanding chronological selection; offline only."""
from pathlib import Path
import sys,json,hashlib,csv,math
import numpy as np
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
sys.path.insert(0,str(A/'source_snapshot'))
from trading_ai.portfolio_research import features,proposal

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def save(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
H=ROOT/'exchange/research/history-20261024';m=read(H/'manifest.json');protocol=read(H/'portfolio-v1/protocol.json');edges=protocol['edges']
data={i['instrument']:read(H/(i['instrument']+'.json')) for i in m['instruments']}
variants=['trend_breakout','trend_pullback','range_reversion']
src=(A/'source_snapshot/trading_ai/portfolio_research.py').read_text()
plan={'created_at':__import__('datetime').datetime.now(__import__('datetime').timezone.utc).isoformat(),
 'status':'PREDECLARED_BEFORE_THIS_GRID; ALL_HISTORY_ALREADY_EXPLORED',
 'families':variants,'stop_ATR':[1.75,2.0,2.25],'reward_R':2,'cost_multiples':[1,2],
 'source_sha256':hashlib.sha256(src.encode()).hexdigest(),'edges':edges,
 'sensitivity':'Report all 54 cells. Do not select best stop; baseline remains 2.0. No deployed changes.',
 'walk_forward':'For fold k=2,3 rank the three BASELINE families by total net in all earlier folds only. Strict strategy holds cash unless every earlier fold has positive net and >=30 trades. Report permissive best-family comparator too. Costs 1 and 2 separately. Reset at fold boundaries.',
 'rejection':'No demonstrated edge unless positive mean R with block-bootstrap lower bound >0, >=100 unseen forward trades, >=3 months, no one-trade concentration, acceptable risk and positive doubled-cost expectancy. Existing data cannot satisfy unseen condition.',
 'independent_holdout':False,'orders_sent':0}
save(A/'validation_protocol.json',plan)
rows=[];records={};checks=[]
for alias,d in data.items():
 bb=d['bars'];full=features(bb)
 for i in (250,1000,2000):
  if i>=len(bb):continue
  past=features(bb[:i])
  for key in full:assert past[key][-1]==full[key][i-1]
  for variant in variants:assert proposal(bb,full,i,variant)==proposal(bb[:i+1],past,i,variant)
  checks.append({'instrument':alias,'cutoff_index':i,'prefix_indicator_and_proposal_match':True})
save(A/'causality_checks.json',checks)
for stop in (1.75,2.0,2.25):
 code=src.replace("distance=2*s['atr']",f"distance={stop}*s['atr']")
 assert code!=src or stop==2
 namespace={'__package__':'trading_ai','__name__':'trading_ai.audit_sensitivity'}
 exec(compile(code,'isolated_sensitivity','exec'),namespace)
 for variant in variants:
  for k in range(3):
   for cost in (1,2):
    result=namespace['replay_portfolio'](m['config'],data,variant,edges[k],edges[k+1],m['initial_equity'],cost)
    trades=result['trades'];n=len(trades);rr=np.array([t['R'] for t in trades]);ci=None
    if n>=5:
     rng=np.random.default_rng(20261024);starts=rng.integers(0,n,(2000,math.ceil(n/5)));ix=((starts[:,:,None]+np.arange(5))%n).reshape(2000,-1)[:,:n];ci=np.quantile(rr[ix].mean(1),[.025,.975]).tolist()
    row={'family':variant,'stop_ATR':stop,'period':k+1,'cost_multiple':cost,'n':n,'net':result['net'],'PF':result['profit_factor'],
     'mean_R':float(rr.mean()) if n else None,'sd_R':float(rr.std(ddof=1)) if n>1 else None,'block5_CI95':ci,'DD_PLN':result['max_drawdown'],'max_reserved_pct':result['max_reserved_pct']}
    assert abs(sum(t['net'] for t in trades)-result['net'])<1e-6
    assert result['max_positions_observed']<=2 and result['max_reserved_pct']<=.2+1e-8
    if stop==2:
     old=read(H/'portfolio-v1'/f'{variant}-{k+1}-cost{cost}.json');assert old==result
    rows.append(row);records[variant,stop,k+1,cost]=result
    save(A/'isolated'/f'sensitivity-{variant}-{stop}-{k+1}-cost{cost}.json',result)
    print(row,flush=True)
save(A/'sensitivity.json',rows)
with (A/'sensitivity.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,rows[0].keys());w.writeheader();w.writerows(rows)
wf=[]
for cost in (1,2):
 for k in (2,3):
  history={v:[r for r in rows if r['stop_ATR']==2 and r['family']==v and r['period']<k and r['cost_multiple']==cost] for v in variants}
  best=max(variants,key=lambda v:sum(r['net'] for r in history[v]))
  eligible=[v for v in variants if all(r['net']>0 and r['n']>=30 for r in history[v])]
  strict=max(eligible,key=lambda v:sum(r['net'] for r in history[v])) if eligible else None
  for mode,v in [('strict_gate',strict),('permissive_comparator',best)]:
   r=next((r for r in rows if r['stop_ATR']==2 and r['family']==v and r['period']==k and r['cost_multiple']==cost),None)
   wf.append({'fold':k,'cost_multiple':cost,'mode':mode,'training_folds':list(range(1,k)),
    'training_net_by_family':{v:sum(x['net'] for x in history[v]) for v in variants},'selected':v or 'CASH',
    'test_net':r['net'] if r else 0,'test_n':r['n'] if r else 0,'test_PF':r['PF'] if r else None,
    'test_mean_R':r['mean_R'] if r else None,'test_DD_PLN':r['DD_PLN'] if r else 0,
    'independent':False,'reason':'Earlier-fold-only selection; design made after history was seen'})
save(A/'walk_forward.json',wf)
with (A/'walk_forward.csv').open('w',newline='',encoding='utf-8-sig') as f:
 w=csv.DictWriter(f,wf[0].keys());w.writeheader();w.writerows(wf)
print('COMPLETED',len(rows),'sensitivity cells',len(wf),'walk-forward rows')
