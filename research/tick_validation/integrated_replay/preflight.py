"""Evidence preflight for Oct22. No market/strategy execution and no MT5 calls."""
import hashlib,json
from pathlib import Path
A=Path(__file__).resolve().parent
read=lambda p:json.loads(p.read_text(encoding='utf-8'))

def check():
    c=read(A/'config.v1.json');clock=read(A/c['clock_assessment']);data=read(A/c['data_readiness'])
    reasons=[]
    if not clock.get('accepted_historical_segments'):reasons.append(dict(code='UTC_UNPROVEN',detail='No accepted UTC segments for the requested day and warm-up'))
    if c['contract_cost_evidence'] is None:reasons.append(dict(code='COST_POLICY_MISSING',detail='Historical contracts, fees, margin/FX policy and execution calibration are not evidenced'))
    if c['point_in_time_calendar_evidence'] is None:reasons.append(dict(code='CALENDAR_ASOF_MISSING',detail='No calendar version proven available at decision time on Oct22'))
    if c['normalized_event_bundle'] is None:reasons.append(dict(code='UTC_TAPE_NOT_PREPARED',detail='Raw-day files cannot be passed as UTC; cross-stream equal-time order is unresolved'))
    if len(data['warmup'])!=7 or any(x['count']!=200 for x in data['warmup']):reasons.append(dict(code='WARMUP_MISSING',detail='Incomplete 200 H1 prehistory'))
    # This version is specifically an audit of the missing inputs. Any future
    # evidence plan needs its own reviewed, versioned semantic validations.
    if not reasons:reasons.append(dict(code='NEW_EVIDENCE_REQUIRES_VALIDATION',detail='This missing-input audit cannot certify a newly supplied bundle'))
    paths=[A/'config.v1.json',A/c['clock_assessment'],A/c['data_readiness']]
    return dict(schema_version=1,decision='NO_GO_HISTORICAL_REPLAY',reasons=reasons,
        adapter_control_tests='tests.txt',historical_replay_run=False,
        metrics={k:None for k in ['signal_delta','entry_delta','fill_price_delta','net','profit_factor','expectancy_R','drawdown','spread_impact','commission_impact']},
        sources=[dict(path=str(p.resolve()),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in paths])

if __name__=='__main__':
    target=A/'historical-preflight.json'
    if target.exists():raise SystemExit('Audit already exists')
    result=check();target.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(result['decision'],[r['code'] for r in result['reasons']])
