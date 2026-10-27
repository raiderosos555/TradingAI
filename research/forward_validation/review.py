"""Cheap deterministic collection status, not a backtest readiness certificate."""
import argparse,json,sqlite3
from datetime import datetime,timezone
from pathlib import Path

def review(root):
    protocol=json.loads((root/'protocol.v1.json').read_text());totals={};batches=0;bad_batches=0;anchors={};bars={}
    for path in sorted((root/'batches').glob('*/manifest.json')):
        p=path.parent/'result.json'
        if not p.exists():bad_batches+=1;continue
        r=json.loads(p.read_text());batches+=1
        for symbol,item in r['symbols'].items():
            a=item.get('anchor',{})
            if a.get('status')=='CONSISTENT_CANDIDATE':
                offsets=anchors.setdefault(symbol,{})
                k=str(a['candidate_offset_seconds']);offsets[k]=offsets.get(k,0)+1
            if item['status']!='CAPTURED':continue
            q=item['quality'];s=totals.setdefault(symbol,dict(ticks=0,chunks=0,invalid_quotes=0,trade_only_invalid=0,
                overlap_mismatches=0,empty_chunks=0,max_internal_silence_ms=0,first_raw_ms=None,last_raw_ms=None))
            for key in ['invalid_quotes','trade_only_invalid']:s[key]+=q[key]
            s['ticks']+=q['count'];s['chunks']+=1;s['overlap_mismatches']+=q['overlap_status']=='MISMATCH';s['empty_chunks']+=q['empty_interval']
            s['max_internal_silence_ms']=max(s['max_internal_silence_ms'],q['max_internal_silence_ms'])
            if s['first_raw_ms'] is None:s['first_raw_ms']=q['first_raw_ms']
            if q['last_raw_ms'] is not None:s['last_raw_ms']=q['last_raw_ms']
        for p in path.parent.glob('*.bars.json'):
            v=json.loads(p.read_text());bars[p.name.removesuffix('.bars.json')]={k:len(x['rows']) if x['rows'] is not None else None for k,x in v.items()}
    end=datetime.fromisoformat(protocol['first_window']['end_utc'])
    pending=datetime.now(timezone.utc)<end
    blockers=['Accepted UTC segments with uncertainty and DST evidence not yet issued; raw data retained',
        'Tick silence is not certified feed completeness; session boundaries and overlap revisions require assessment',
        'Exact cross-symbol same-millisecond order is not supplied by MT5 history API',
        'Entry latency/slippage/commission policy requires matching future observed broker executions',
        'Existing replay starts flat; any DEMO positions at window start require validated initial-state support',
        'Polled context proves collector receipt, not exact bytes read by the live engine at each decision']
    return dict(at=datetime.now(timezone.utc).isoformat(),mode='SHADOW',orders_authorized=False,
        status='WAITING_FOR_PREREGISTERED_WINDOW' if pending else 'NO_GO_PENDING_EVIDENCE_REVIEW',
        first_window=protocol['first_window'],complete_batches=batches,incomplete_batches=bad_batches,
        streams=totals,clock_anchor_candidates=anchors,warmup_observed=bars,
        utc_mapping_verified=False,backtest_completed=False,edge_confirmed=False,
        blockers=blockers,selection_by_profit=False,automatic_promotion=False)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('root',type=Path);a=p.parse_args()
    print(json.dumps(review(a.root),indent=2))
