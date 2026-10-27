"""Offline audit. Writes only below this directory. No trading/broker imports."""
from pathlib import Path
import sys,json,hashlib,copy,csv,math,sqlite3,shutil
from datetime import datetime,timezone
from zoneinfo import ZoneInfo
from bisect import bisect_left,bisect_right
from collections import defaultdict,Counter
import numpy as np
A=Path(__file__).resolve().parent; ROOT=A.parents[1]
sys.path.insert(0,str(A/'source_snapshot'))
from trading_ai.indicators import ema,atr
from trading_ai.strategy import SignalEngine
from trading_ai.models import digest

def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write(name,x):
 p=A/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(x,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')
def csvout(name,rows):
 if not rows:return
 with (A/name).open('w',newline='',encoding='utf-8-sig') as f:
  fields=list(dict.fromkeys(k for r in rows for k in r));w=csv.DictWriter(f,fields);w.writeheader()
  for r in rows:w.writerow({k:json.dumps(v,ensure_ascii=False) if isinstance(v,(list,dict)) else v for k,v in r.items()})
def epoch(t):return float(t) if isinstance(t,(int,float)) else datetime.fromisoformat(t).timestamp()
def iso(t):return datetime.fromtimestamp(t,timezone.utc).isoformat()
def stat(ts):
 if not ts:return {'n':0,'net':0,'mean_R':None,'pf':None}
 ts=sorted(ts,key=lambda t:(epoch(t['closed']),epoch(t['opened'])))
 rr=np.array([t['R'] for t in ts]);p=np.array([t['net'] for t in ts]);n=len(ts)
 wins=p[p>0];loss=p[p<0];c=np.r_[0,np.cumsum(p)];streak=best=0
 for x in p:streak=streak+1 if x<0 else 0;best=max(best,streak)
 # Circular block bootstrap over chronological trade sequence; descriptive, not selection-adjusted.
 if n>=20:
  rng=np.random.default_rng(20261024);L=min(5,n);starts=rng.integers(0,n,(600,math.ceil(n/L)))
  ix=((starts[:,:,None]+np.arange(L))%n).reshape(600,-1)[:,:n]
  ci=np.quantile(rr[ix].mean(axis=1),[.025,.975]).tolist()
 else:ci=None
 return {'n':n,'net':float(p.sum()),'mean_R':float(rr.mean()),'median_R':float(np.median(rr)),
 'sd_R':float(rr.std(ddof=1)) if n>1 else None,'mean_win_PLN':float(wins.mean()) if len(wins) else None,
 'mean_loss_PLN':float(loss.mean()) if len(loss) else None,'mean_win_R':float(rr[p>0].mean()) if len(wins) else None,
 'mean_loss_R':float(rr[p<0].mean()) if len(loss) else None,'pf':float(wins.sum()/-loss.sum()) if len(loss) else None,
 'win_rate':float((p>0).mean()),'closed_equity_DD_PLN':float((np.maximum.accumulate(c)-c).max()),
 'max_loss_streak':best,'expectancy_block5_CI95':ci,'small_group':n<30,
 'median_holding_hours':float(np.median([t['holding_hours'] for t in ts])) if 'holding_hours' in ts[0] else None}

H=ROOT/'exchange/research/history-20261024';m=read(H/'manifest.json')
datasets={i['instrument']:read(H/(i['instrument']+'.json')) for i in m['instruments']}
for item in m['instruments']:assert digest(datasets[item['instrument']])==item['data_sha256']
assert digest(m['config'])==m['config_hash']
inputs={};features={};data_audit=[]
for alias,d in datasets.items():
 for tf,bars in [('H1',d['bars'])]+[(tf,read(A/'inputs'/f'{alias}-{tf}.json')['bars']) for tf in ('H4','D1')]:
  seconds={'H1':3600,'H4':14400,'D1':86400}[tf];times=[b['time'] for b in bars]
  f={'ema20':ema([b['close'] for b in bars],20),'ema50':ema([b['close'] for b in bars],50),'atr':atr(bars,14)}
  inputs[alias,tf]=(bars,times,seconds);features[alias,tf]=f
  gaps=[{'after':iso(x),'before':iso(y),'hours':(y-x)/3600} for x,y in zip(times,times[1:]) if y-x>seconds]
  bad=sum(not(0<b['low']<=min(b['open'],b['close'])<=max(b['open'],b['close'])<=b['high']) for b in bars)
  data_audit.append({'instrument':alias,'tf':tf,'bars':len(bars),'first':iso(times[0]),'last':iso(times[-1]),
   'unordered':sum(x>=y for x,y in zip(times,times[1:])),'duplicates':len(times)-len(set(times)),
   'bad_OHLC':bad,'zero_spread':sum(b.get('spread',0)<=0 for b in bars),'gaps_gt_timeframe':len(gaps),
   'gap_hours_max':max([g['hours'] for g in gaps],default=0),'coverage_certified':False})
  write(f'inputs/gaps-{alias}-{tf}.json',gaps)
write('data_quality.json',data_audit);csvout('data_quality.csv',data_audit)

# Instrumentation changes export fields only; frozen original economics remain identical.
src=(A/'source_snapshot/trading_ai/portfolio_research.py').read_text()
old="'risk':p['risk'],'R':net/p['risk'],'reason':reason,'volume':p['volume']})"
new="'risk':p['risk'],'R':net/p['risk'],'reason':reason,'volume':p['volume'], 'entry':p['entry'], 'exit':price, 'direction':'BUY' if p['side']==1 else 'SELL', 'sl':p['sl'], 'tp':p['tp'], 'commission':p['commission'], 'swap':swap})"
assert src.count(old)==1
src=src.replace(old,new);(A/'isolated/portfolio_instrumented.py').write_text(src,encoding='utf-8')
scope={'__package__':'trading_ai','__name__':'trading_ai.audit_portfolio'};exec(compile(src,'portfolio_instrumented.py','exec'),scope)
paths=sorted((ROOT/'exchange/backtests').glob('*.json'))
for folder in ('validation','candidates','portfolio-v1'):
 paths+=sorted((H/folder).glob('*.json'))
alltrades=[];runs=[];checks=[]
for path in paths:
 result=read(path)
 if not isinstance(result,dict) or not isinstance(result.get('trades'),list):continue
 rel=path.relative_to(ROOT).as_posix();run=path.parent.name+'/'+path.stem
 frozen=A/'inputs/artifacts'/rel;frozen.parent.mkdir(parents=True,exist_ok=True)
 if not frozen.exists():shutil.copy2(path,frozen)
 portfolio=path.parent.name=='portfolio-v1'
 if portfolio:
  replay=scope['replay_portfolio'](m['config'],datasets,result['variant'],result['start'],result['end'],result['initial_equity'],result['cost_multiple'])
  assert len(replay['trades'])==len(result['trades']) and abs(replay['net']-result['net'])<1e-8
  for x,y in zip(replay['trades'],result['trades']):assert all(x[k]==v for k,v in y.items())
  checks.append({'run':run,'exact_trade_fields_match':True,'net_difference':replay['net']-result['net']})
  write('isolated/enriched-'+path.name,replay);trades=replay['trades']
 else:trades=result['trades']
 cfg=copy.deepcopy(m['config'])
 if 'breakout_only' in path.name and 'false_breakout_only' not in path.name:cfg['engine']['enable_false_breakout']=False
 if 'false_breakout_only' in path.name:cfg['engine']['enable_breakout']=False
 enriched=[]
 for k,t in enumerate(trades):
  t=copy.deepcopy(t);alias=t.get('instrument',result.get('instrument'));bars,times,_=inputs[alias,'H1'];opened=epoch(t['opened']);closed=epoch(t['closed']);i=bisect_left(times,opened)
  row={**t,'run':run,'source_path':rel,'index':k,'instrument':alias,'strategy':t.get('strategy',result.get('variant','UNKNOWN_LEGACY')),
   'opened':iso(opened),'closed':iso(closed),'holding_hours':(closed-opened)/3600,
   'hour_UTC':datetime.fromtimestamp(opened,timezone.utc).hour,'weekday_UTC':datetime.fromtimestamp(opened,timezone.utc).strftime('%A'),
   'hour_Warsaw':datetime.fromtimestamp(opened,ZoneInfo('Europe/Warsaw')).hour,'month':iso(opened)[:7],
   'direction':t.get('direction','UNKNOWN'),'feature_provenance':'UNKNOWN_LEGACY' if path.parent.name=='backtests' else 'EXACT_EXPORT_REPLAY' if portfolio else 'NOT_RECONSTRUCTED'}
  contract=result.get('contract',datasets[alias]['contract']);point=contract['point'];factor=contract['cash_per_price_unit_per_lot']
  costs=result.get('costs',{'spread_points':max(1,bars[max(i-1,0)].get('spread',1))*result.get('cost_multiple',1),'slippage_points':2*result.get('cost_multiple',1),'commission_per_lot_roundtrip':10*result.get('cost_multiple',1),'swap_per_lot_per_day':-5*result.get('cost_multiple',1)})
  if not portfolio and path.parent.name!='backtests' and i<len(bars) and times[i]==opened:
   class Market:
    def market(self,*args):return {'symbol':datasets[alias]['symbol'],'info':{**contract,'trade_stops_level':0,'trade_freeze_level':0},'tick':{'bid':bars[i]['open'],'ask':bars[i]['open']+costs['spread_points']*point,'time':opened},'bars':bars[max(0,i-200):i]}
   ev=SignalEngine(cfg,Market()).evaluate(alias,datetime.fromtimestamp(opened,timezone.utc));s=ev['signal']['signal'] if ev['signal'] else None
   assert s and s['id']==t['signal_id'],(run,k,'signal mismatch')
   expected=bars[i]['open']+(costs['spread_points']*point if s['kind']=='BUY' else 0)+(1 if s['kind']=='BUY' else -1)*costs['slippage_points']*point
   assert abs(expected-t['entry'])<1e-8,(run,k,'entry mismatch')
   row.update(direction=s['kind'],sl=s['sl'],tp=s['tp'],tp1=s['management']['tp1'],feature_provenance='SIGNAL_ID_AND_ENTRY_MATCH',strategy=s['strategy'],original_structure_trend=ev['analysis']['trend'])
  row['risk']=t.get('risk',t.get('initial_risk'))
  row.update(spread_points=costs['spread_points'],spread_cash_proxy=costs['spread_points']*point*factor*t['volume'],
   slippage_cash_proxy=2*costs['slippage_points']*point*factor*t['volume'],commission_cash=costs['commission_per_lot_roundtrip']*t['volume'],
   swap_cash_model=costs['swap_per_lot_per_day']*t['volume']*(closed-opened)/86400)
  for tf in ('H1','H4','D1'):
   bb,tt,seconds=inputs[alias,tf];j=bisect_right(tt,opened-seconds)-1;ff=features[alias,tf]
   if j>=50 and ff['atr'][j]:
    z=(ff['ema20'][j]-ff['ema50'][j])/ff['atr'][j]
    row['trend_'+tf]='UP' if z>=.5 else 'DOWN' if z<=-.5 else 'RANGE'
    row['trend_z_'+tf]=z;row['context_'+tf+'_last_closed']=iso(tt[j]+seconds)
   else:row['trend_'+tf]='UNKNOWN'
  j=i-1;a=features[alias,'H1']['atr'][j] if j>=0 else None
  if a and i>=21:
   prior=bars[i-21:i-1];sup=min(b['low'] for b in prior);res=max(b['high'] for b in prior)
   aa=[v for v in features[alias,'H1']['atr'][max(0,j-199):j+1] if v]
   percentile=sum(v<=a for v in aa)/len(aa)
   row.update(ATR=a,ATR_percentile_trailing200=percentile,volatility='HIGH' if percentile>=.8 else 'LOW' if percentile<=.2 else 'MID',support20=sup,resistance20=res)
   if 'entry' in row:row.update(entry_above_support_ATR=(row['entry']-sup)/a,entry_below_resistance_ATR=(res-row['entry'])/a)
   if row['direction']!='UNKNOWN' and row.get('sl') is not None:
    sign=1 if row['direction']=='BUY' else -1;dist=abs(row['entry']-row['sl']);row.update(SL_distance=dist,SL_ATR=dist/a,spread_ATR=costs['spread_points']*point/a,initial_RR=abs(row['tp']-row['entry'])/dist)
    # Exclude exit bar for conservative extrema; include it only as an upper envelope.
    for label,bb in [('pre_exit', [b for b in bars[i:] if b['time']+3600<closed]),('including_exit',[b for b in bars[i:] if b['time']<closed])]:
     if bb:
      add=costs['spread_points']*point if sign==-1 else 0
      fav=max(((b['high']+add-row['entry']) if sign==1 else (row['entry']-b['low']-add)) for b in bb)
      adv=max(((row['entry']-b['low']-add) if sign==1 else (b['high']+add-row['entry'])) for b in bb)
      row['MFE_'+label+'_price_R']=max(0,fav)/dist;row['MAE_'+label+'_price_R']=max(0,adv)/dist
    if row['strategy']=='local_breakout_v1':
     window=[b for b in bars[i:] if b['time']<min(closed,opened+3*3600)]
     row['reclosed_inside_prior_range_first3h']=any(sup<=b['close']<=res for b in window)
  row['macro_window']='UNAVAILABLE_HISTORICAL_ARCHIVE'
  enriched.append(row);alltrades.append(row)
 runstats=stat(enriched);runstats.update(run=run,source_path=rel,reported_net=result['net'],reported_DD=result.get('max_drawdown_cash',result.get('max_drawdown')))
 assert abs(runstats['net']-result['net'])<1e-6,(run,'PnL mismatch')
 runs.append(runstats);print(run,len(trades),flush=True)
write('trades_enriched.json',alltrades);csvout('trades_enriched.csv',alltrades);write('run_statistics.json',runs);csvout('run_statistics.csv',runs);write('reconstruction_checks.json',checks)
groups=defaultdict(list)
for t in alltrades:
 for dim in ['ALL','direction','hour_UTC','weekday_UTC','month','trend_H1','trend_H4','trend_D1','volatility','reason','reclosed_inside_prior_range_first3h']:
  groups[t['run'],t['instrument'],t['strategy'],dim,str(t.get(dim,'ALL' if dim=='ALL' else 'UNKNOWN'))].append(t)
sub=[]
for (run,alias,strategy,dim,value),ts in groups.items():
 ss=stat(sorted(ts,key=lambda t:t['opened']));ss.update(run=run,instrument=alias,strategy=strategy,dimension=dim,value=value);sub.append(ss)
write('subgroup_statistics.json',sub);csvout('subgroup_statistics.csv',sub)
stress=[]
for alias in datasets:
 for period in ('development','validation'):
  ts=[t for t in alltrades if t['run']==f'validation/{alias}-{period}-base']
  for mult in (1,2,3):
   adjusted=[]
   for t in ts:
    extra=(mult-1)*(t['spread_cash_proxy']+t['slippage_cash_proxy']+t['commission_cash']-t['swap_cash_model'])
    v={**t,'net':t['net']-extra,'R':(t['net']-extra)/t['risk']};adjusted.append(v)
   stress.append({'instrument':alias,'period':period,'cost_multiple':mult,'model':'FIXED_PATH_EXTRA_ROUNDTRIP_COST_NO_REFILTER',**stat(adjusted)})
write('matched_trade_cost_stress.json',stress);csvout('matched_trade_cost_stress.csv',stress)
summary={'runs':len(runs),'trade_records_not_independent':len(alltrades),'reconstruction':dict(Counter(t['feature_provenance'] for t in alltrades)),
 'H1_bars':sum(len(d['bars']) for d in datasets.values()),'no_live_changes':True,'no_orders_sent':True,
 'bootstrap':'Circular chronological trade blocks length5,600 resamples,seed20261024; not multiplicity-adjusted; N<20 unavailable',
 'independent_validation_available':False}
write('audit_summary.json',summary);print(summary)
