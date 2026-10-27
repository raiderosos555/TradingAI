import json,statistics,sqlite3,shutil,hashlib
from pathlib import Path
from collections import Counter,defaultdict
from datetime import datetime,timezone
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
read=lambda p:json.loads(Path(p).read_text(encoding='utf-8-sig'))
ts=read(A/'trades_enriched.json');facts={}
for alias in ('US100','OIL'):
 for period in ('development','validation'):
  v=sorted([t for t in ts if t['run']==f'validation/{alias}-{period}-base'],key=lambda t:t['opened']);n=len(v);order=sorted(v,key=lambda t:t['net'],reverse=True)
  def sums(items):return {'n':len(items),'net':sum(t['net'] for t in items),'mean_R':statistics.mean(t['R'] for t in items) if items else None}
  f={'top1':sums(order[:1]),'top3':sums(order[:3]),'top5':sums(order[:5]),'without_top5':sums(order[5:]),'first_third':sums(v[:n//3]),'middle_third':sums(v[n//3:2*n//3]),'last_third':sums(v[2*n//3:]),'last5':sums(v[-5:])}
  for dim in ('month','hour_UTC','trend_H4','trend_D1','direction','volatility'):
   f[dim]={str(key):sums([t for t in v if t[dim]==key]) for key in sorted({t[dim] for t in v})}
  f['median_ATR']=statistics.median(t['ATR'] for t in v);f['median_risk_PLN']=statistics.median(t['risk'] for t in v)
  f['median_SL_ATR']=statistics.median(t['SL_ATR'] for t in v);f['median_spread_ATR']=statistics.median(t['spread_ATR'] for t in v)
  b=[t for t in v if t['strategy']=='local_breakout_v1']
  f['breakout_reclosed3h']={str(key):sums([t for t in b if t['reclosed_inside_prior_range_first3h']==key]) for key in (False,True)}
  f['worst_breakout_examples']=[{k:t.get(k) for k in ('index','opened','closed','direction','strategy','entry','sl','tp','ATR','SL_ATR','initial_RR','volume','risk','net','R','trend_H4','trend_D1','spread_cash_proxy','slippage_cash_proxy','commission_cash','swap_cash_model','reclosed_inside_prior_range_first3h','MAE_including_exit_price_R','MFE_pre_exit_price_R')} for t in sorted(b,key=lambda t:t['net'])[:3]]
  f['cost_proxy_sums']={k:sum(t[k] for t in v) for k in ('spread_cash_proxy','slippage_cash_proxy','commission_cash','swap_cash_model')}
  facts[alias+'-'+period]=f
inventory=read(A/'inputs/inventory.json');integrity=[]
for item in inventory:
 p=ROOT/item['path'];actual=hashlib.sha256(p.read_bytes()).hexdigest()
 integrity.append({'path':item['path'],'expected_sha256':item['sha256'],'current_sha256':actual,'unchanged':actual==item['sha256']})
assert all(i['unchanged'] for i in integrity)
(A/'integrity_check.json').write_text(json.dumps(integrity,indent=2),encoding='utf-8')
db=sqlite3.connect('file:'+str(A/'inputs/journal-snapshot.sqlite3')+'?mode=ro',uri=True)
ops=[]
for oid,status,payload,result,at in db.execute('select id,status,payload,result,at from operations'):
 p=json.loads(payload);r=json.loads(result);ops.append({'id':oid,'status':status,'at':at,'rule':p.get('rule'),'payload_keys':list(p),'result_keys':list(r),'strategy':p.get('envelope',{}).get('signal',{}).get('strategy')})
facts['risk_journal']={'operations':ops,'events':dict(db.execute('select kind,count(*) from events group by kind').fetchall()),'signals_by_strategy':dict(Counter(json.loads(r[0])['signal']['strategy'] for r in db.execute('select payload from signals')))}
runtime={}
for name in ('engine-status.json','baseline-status.json','engine.log','baseline.log'):
 src=ROOT/'state/runtime'/name;dst=A/'inputs'/('runtime-'+name);shutil.copy2(src,dst)
 if name.endswith('.json'):runtime[name]=read(dst)
facts['runtime_snapshot']=runtime
facts['sample_costs']=read(ROOT/'exchange/research/cost-sample-20261022/summary.json')
facts['at']=datetime.now(timezone.utc).isoformat()
(A/'focused_facts.json').write_text(json.dumps(facts,indent=2,ensure_ascii=False),encoding='utf-8')
for key in ('US100-validation','OIL-validation'):
 f=facts[key];print(key,{k:f[k] for k in ('top5','without_top5','first_third','middle_third','last_third','last5','month','median_risk_PLN','median_ATR','breakout_reclosed3h','cost_proxy_sums')})
print('risk',facts['risk_journal']);print('integrity',len(integrity),'unchanged')
