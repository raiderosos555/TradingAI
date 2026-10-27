"""Research-only comparison. Never imports, approves or sends an execution plan."""
import json,sys,hashlib
from pathlib import Path
from datetime import datetime
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
ALLOWED={'GOLD','US500','US100','OIL','EURUSD','EURPLN','GBPUSD','WIG20','DAX'}
def time(value):
 t=datetime.fromisoformat(value)
 if t.tzinfo is None:raise ValueError('Timezone required')
 return t.timestamp()
def validate(r):
 if r.get('schema_version')!='edge_context_v1':raise ValueError('Wrong research schema')
 if r['instrument'] not in ALLOWED:raise ValueError('Unknown instrument')
 if r['decision'] not in {'OPEN','HOLD','CANCEL','NO_TRADE'}:raise ValueError('Invalid decision')
 if r['direction'] not in {'BUY','SELL',None}:raise ValueError('Invalid direction')
 if type(r['source_complete']) is not bool:raise ValueError('source_complete must be boolean')
 if not r['id'] or not r['source_reference']:raise ValueError('Missing identity/provenance')
 if time(r['valid_until'])<=time(r['published_at']):raise ValueError('Invalid expiry')
 time(r['first_seen_at'])
 if r['decision']=='OPEN':
  if r['direction'] is None or not r['broker_symbol']:raise ValueError('Exact broker contract and direction required')
  for k in ('entry','sl','tp'):
   if type(r[k]) not in (float,int) or not 0<r[k]<float('inf'):raise ValueError('Complete finite plan required')
  if not (r['sl']<r['entry']<r['tp'] if r['direction']=='BUY' else r['tp']<r['entry']<r['sl']):raise ValueError('Inconsistent levels')
 return r
def compare(records,trades,mapping):
 ids=[r['id'] for r in records]
 if len(ids)!=len(set(ids)):raise ValueError('Duplicate immutable IDs')
 records=[validate(r) for r in records];out=[]
 for t in trades:
  at=time(t['opened']);active=[r for r in records if r['source_complete'] and r['instrument']==t['instrument'] and r['broker_symbol']==mapping.get(t['instrument'])
   and max(time(r['published_at']),time(r['first_seen_at']))<=at<time(r['valid_until'])]
  state='NO_ELIGIBLE_CONTEXT'
  if len(active)>1:state='AMBIGUOUS'
  elif active:
   r=active[0];state='AGREES' if r['decision']=='OPEN' and r['direction']==t['direction'] else 'OPPOSES' if r['decision']=='OPEN' else r['decision']
  out.append({'run':t['run'],'trade_index':t['index'],'instrument':t['instrument'],'opened':t['opened'],'comparison':state,'context_ids':[r['id'] for r in active],'net':t['net'],'R':t['R']})
 return out
if __name__=='__main__':
 records=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8-sig')) if len(sys.argv)>1 else []
 config=json.loads((A/'source_snapshot/config.demo.json').read_text())
 trades=json.loads((A/'trades_enriched.json').read_text())
 # One predeclared research population, never pool overlapping candidate reruns.
 trades=[t for t in trades if t['run'].startswith('validation/') and t['run'].endswith('-validation-base')]
 result=compare(records,trades,{k:v['broker'] for k,v in config['symbols'].items()})
 out={'research_only':True,'eligible_historical_briefing_signals':len(records),'comparisons':result,
 'limitations':['The saved 23-Oct partial source is incomplete, NO TRADE, and not an executable plan.',
 'Synthetic simulation inbox excluded. No reconstruction of recommendations from future prices.',
 'Published/first-seen timestamps need immutable capture evidence; self-reported times are not independent proof.',
 'WIG20 and DAX have no configured broker contract; context cannot authorize or match a CFD trade.']}
 (A/'briefing_comparison.json').write_text(json.dumps(out,indent=2,ensure_ascii=False),encoding='utf-8')
 print('Research comparisons:',len(result),'context records:',len(records))
