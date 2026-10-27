"""Read-only verification of saved uncertainty. Never calls reconcile/finish/send."""
import copy,json,sys
from pathlib import Path
A=Path(__file__).resolve().parent;ROOT=A.parents[1];sys.path.insert(0,str(ROOT))
from trading_ai.broker import MT5Broker
from trading_ai.risk import RiskManager
from trading_ai.execution import ExecutionEngine
cfg=json.loads((ROOT/'state/runtime/effective-config.json').read_text())
ops=json.loads((A/'evidence/uncertain-operations.json').read_text());b=MT5Broker(cfg['terminal_path'],cfg['broker_time_offset_seconds'])
try:
    snap=b.snapshot();out=[]
    for op in ops:
        req=op['payload']['request'];order=op['result'].get('order');history=b.order_history(order)
        pid=history[0].get('position_id') if len(history)==1 else None
        deals=b.position_deals(pid) if pid else []
        info=b.mt5.symbol_info(req['symbol']);step=info.trade_tick_size
        levels=[{'sl_exact':p['sl']==req['sl'],'tp_exact':p['tp']==req['tp'],'sl_difference':p['sl']-req['sl'],'tp_difference':p['tp']-req['tp'],'same_sl_grid':round(p['sl']/step)==round(req['sl']/step),'same_tp_grid':round(p['tp']/step)==round(req['tp']/step)} for p in snap['positions'] if p['identifier']==pid]
        original=ExecutionEngine(RiskManager(cfg,b,None)).verify(op)
        # Counterfactual read-only verify against exact broker SL/TP; no durable change.
        trial=copy.deepcopy(op)
        positions=[p for p in snap['positions'] if p['identifier']==pid]
        counterfactual=None
        if len(positions)==1:
            trial['payload']['request'].update(sl=positions[0]['sl'],tp=positions[0]['tp'])
            counterfactual=ExecutionEngine(RiskManager(cfg,b,None)).verify(trial)
        out.append(dict(id=op['id'],at=op['at'],original_verify=original,using_exact_broker_levels_verify=counterfactual,levels=levels,history=history,deals=deals,tick_size=step))
    (A/'evidence/uncertain-diagnosis.json').write_text(json.dumps(out,indent=2))
    print(json.dumps([{'original_verify':x['original_verify'],'counterfactual_verify':x['using_exact_broker_levels_verify'],'levels':x['levels']} for x in out]))
finally:b.close()
