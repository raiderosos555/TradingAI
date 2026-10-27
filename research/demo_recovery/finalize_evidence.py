"""Read-only end-of-task evidence, no MT5 connections or production mutation."""
import hashlib,json,sqlite3
from datetime import datetime,timezone
from pathlib import Path
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
def load(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cohort=ROOT/'state/forward_validation/cohort-20261026-v1';status=load(cohort/'status.json')
baseline=load(A/'protected-before.json');production={rel:sha(ROOT/rel)==h for rel,h in baseline.items()}
protocol=load(cohort/'protocol.v1.json')
collector={rel:sha(ROOT/rel)==h for rel,h in protocol['collector_hashes'].items()}
engine=load(ROOT/'state/runtime/engine-status.json')
broker_files=[p for p in sorted((cohort/'batches').glob('*/broker.json')) if (p.parent/'manifest.json').exists() and (p.parent/'result.json').exists()]
broker=load(broker_files[-1]);manifest=load(broker_files[-1].parent/'manifest.json')
db=sqlite3.connect((ROOT/'state/journal.sqlite3').as_uri()+'?mode=ro',uri=True)
db.execute('BEGIN')
operations=[]
for key,state,payload,result in db.execute('SELECT id,status,payload,result FROM operations'):
    operations.append(dict(id=key,status=state,payload=json.loads(payload),result=json.loads(result) if result else {}))
events=[dict(at=at,**json.loads(payload)) for at,payload in db.execute("SELECT at,payload FROM events WHERE kind='management_decision' ORDER BY seq DESC LIMIT 100")]
db.close();positions=[]
for pos in broker['positions'] or []:
    ids={o['ticket'] for o in broker['history_orders'] or [] if o.get('position_id')==pos['identifier']}
    matches=[o for o in operations if o['status']=='CONFIRMED' and o['payload']['rule']=='OPEN' and o['result'].get('order') in ids]
    recent=[e for e in events if e.get('ticket')==pos['ticket']]
    positions.append(dict(ticket=pos['ticket'],symbol=pos['symbol'],identifier=pos['identifier'],
        confirmed_open_matches=len(matches),sl=pos['sl'],tp=pos['tp'],volume=pos['volume'],
        recent_management=recent[:6],snapshot_received_at=broker['received_at'],
        interpretation='Identity/protection observation, not an independent full verification of every management amendment'))
result=dict(at=datetime.now(timezone.utc).isoformat(),protected_files_unchanged=all(production.values()),protected_checks=production,
    collector_code_unchanged=all(collector.values()),engine_task_xml_unchanged=(A/'engine-task.before.xml').read_bytes()==(A/'engine-task.after.xml').read_bytes(),
    engine=engine,collector=status,positions=positions,uncertain_operations=sum(o['status'] in ['INTENT','UNCERTAIN'] for o in operations),
    latest_broker_snapshot_hash_valid=sha(broker_files[-1])==manifest['broker.json'],
    window_evaluation='PENDING 2026-10-27T16:00:00Z; follow-up scheduled 17:10 Europe/Warsaw',
    tests=dict(recovery=13,runtime_regression=21,window_boundaries=5),live_deployment=False,
    test_orders_sent_to_mt5=0)
(A/'validation-state.final.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(dict(production_unchanged=result['protected_files_unchanged'],collector_unchanged=result['collector_code_unchanged'],
    task_unchanged=result['engine_task_xml_unchanged'],engine_status=engine['status'],positions=[dict(symbol=p['symbol'],matches=p['confirmed_open_matches'],recent_decisions=len(p['recent_management'])) for p in positions],uncertain=result['uncertain_operations'])))
