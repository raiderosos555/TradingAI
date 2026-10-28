"""Independent saved-output arithmetic/timing checks, no network or MT5."""
import hashlib,json
from pathlib import Path
from datetime import date,datetime,timezone
import numpy as np
import cot_experiment as C

def main():
    p=C.PRIVATE;d=json.loads((p/'experiment-v1.json').read_text(encoding='utf-8'))
    assert C.sha(C.HERE/'cot_experiment.py')==d['code_hash']
    assert C.sha(C.HERE/'COT_EXPERIMENT_PROTOCOL.md')==d['protocol_hash']
    for name,h in d['source_hashes'].items():assert C.sha(C.PACKAGE/name)==h
    hashes=json.loads((p/'local-before.json').read_text())['protected_hashes']
    root=C.HERE.parents[1];changed=[f for f,h in hashes.items() if C.sha(root/f)!=h]
    assert not changed
    cot,_=C.load_cot();n=0
    for key,rows in d['rows'].items():
        market=key.split('/')[0];code='099741' if market=='EURUSD' else '096742'
        prices,_=C.load_prices(C.PACKAGE/('fed_eur_complete.raw' if market=='EURUSD' else 'fed_gbp_complete.raw'))
        last_exit=None
        for r in rows:
            n+=1;e=date.fromisoformat(r['entry']).toordinal();x=date.fromisoformat(r['exit']).toordinal()
            assert last_exit is None or e>=last_exit
            last_exit=x
            assert x-e==r['weeks']*7 and C.part(e)==C.part(x)
            a=date.fromisoformat(r['price_signal']).toordinal();b=date.fromisoformat(r['price_start']).toordinal()
            assert a<=e-14 and b<=e-14-182
            assert r['reference_entry']==prices[e] and r['reference_exit']==prices[x]
            direction=int(np.sign(prices[a]-prices[b]));move=(prices[x]-prices[e])/prices[e]*10000
            assert direction==r['direction'] and abs(move-r['move_bps'])<1e-8
            end=date.fromisoformat(r['cot_end']).toordinal();start=date.fromisoformat(r['cot_start']).toordinal()
            assert r['lag']<=e-end<=r['lag']+7 and 26<=end-start<=30
            dates=[v for v in sorted(cot[code]) if start<=v<=end]
            assert len(dates)==5 and not any(C.excluded(v) for v in dates)
            delta=cot[code][end]['share']-cot[code][start]['share']
            assert abs(delta-r['cot_delta'])<1e-12
            selected=int(delta*direction>0);assert selected==r['selected']
            assert abs(r['A']-direction*move)<1e-8 and abs(r['B']-selected*direction*move)<1e-8
        for part in ('discovery','walk_forward','confirmation','all'):
            subset=[r for r in rows if part=='all' or r['part']==part];s=d['results'][key][part]
            assert len(subset)==s['n'] and sum(r['selected'] for r in subset)==s['selected']
            assert abs(np.mean([r['B']-r['A'] for r in subset])-s['delta'])<1e-9
            for label,rt,wk in [('zero',0,0),('base',5,2),('stress',15,5)]:
                cost=rt+wk*subset[0]['weeks'];A=np.mean([r['A']-cost*abs(r['direction']) for r in subset]);B=np.mean([r['B']-cost*r['selected'] for r in subset])
                assert abs(A-s['hurdles'][label]['A'])<1e-9 and abs(B-s['hurdles'][label]['B'])<1e-9
    bytes_used=sum(json.loads(f.read_text(encoding='utf-8')).get('bytes',0) for f in C.PACKAGE.glob('*.json') if f.name!='manifest.json')
    assert bytes_used<=5_000_000
    status_path=root/'state/forward_validation/cohort-20261026-v1/status.json'
    collector=json.loads(status_path.read_text())
    result=dict(at=datetime.now(timezone.utc).isoformat(),arithmetic_rows=n,source_hashes=len(d['source_hashes']),
      protected_files=len(hashes),changed=changed,download_bytes=bytes_used,status='PASS',
      collector={k:collector.get(k) for k in ('status','at','configuration_matches_frozen')},
      collector_file_age_seconds=datetime.now(timezone.utc).timestamp()-status_path.stat().st_mtime,
      point_in_time_verified=False,broker_pnl=False,orders_sent=0)
    C.put(p/'validation-v1.json',result);print(json.dumps(result,indent=2))

if __name__=='__main__':main()
