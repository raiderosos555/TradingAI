"""Offline integrity and independent arithmetic checks, no MT5/network/orders."""
import argparse,json,hashlib,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
import alternative_experiments as A
E=A.E

def main(root):
    here=Path(__file__).resolve().parent;old=E.read(root/'research/edge_program/private/results-v1.json')
    new=E.read(here/'private/results-v1.json');checks={};n=0
    expected=E.read(root/'research/market_mechanisms/private/feasibility.json')['protected_hashes']
    changed=[p for p,h in expected.items() if E.sha(root/p)!=h]
    checks['protected_files_checked']=len(expected);checks['protected_changed']=changed
    assert not changed,changed
    for x in old['source_hashes']:assert E.sha(root/x['path'])==x['sha256']
    checks['ohlc_hashes']=len(old['source_hashes'])
    assert E.sha(here/'HYPOTHESES.md')==new['registry_sha256']
    assert E.sha(here.parent/'edge_program/STRATEGY_HYPOTHESES.md')==old['registry_sha256']
    assert E.sha(here/'alternative_experiments.py')==new['code_hash']
    for name in ('experiments.py','protocol.py'):assert E.sha(here.parent/'edge_program'/name)==old['code_hashes'][name]
    checks['frozen_protocols_and_calculation_code']='MATCH'
    assert len(old['tests'])==36 and len(new['tests'])==12
    for result in (old,new):
        for key,rows in result['rows'].items():
            for r in rows:
                n+=1
                assert r['signal_raw']<r['entry_raw']<r['exit_raw']
                assert not (r['signal_raw']<E.epoch('2026-08-01')<=r['exit_raw'])
                assert r['exit_raw']<E.epoch('2026-10-24')
                assert abs(r['net']-(r['gross']-r['cost']))<1e-9
                assert abs(r['delta']-(r['net']-r['base']))<1e-9
                if r['direction']==0:assert r['net']==r['cost']==r['stress']==0
                assert r['stress']<=r['net']+1e-9
            for period,s in result['tests'][key].items():
                sub=[r for r in rows if period=='all' or r['period']==period]
                assert len(sub)==s['n']
                if sub:
                    assert abs(np.mean([r['net'] for r in sub])-s['mean'])<1e-9
                    assert abs(np.mean([r['delta'] for r in sub])-s['delta'])<1e-9
    # Independently re-evaluate all selected IV dates and compare raw price legs.
    indices={}
    for symbol,coverage in new['coverage'].items():
        path=here/'private/samples-v1'/f'{symbol}.csv';assert E.sha(path)==coverage['sha256']
        indices[symbol]=A.load_index(path)[0]
    for key,rows in new['rows'].items():
        family,alias,symbol,lagname=key.split('/');lag=int(lagname[-1]);bars,_=E.load(root,alias,'D1')
        for r in rows:
            cutoff=r['signal_raw']-86400*lag-10800
            eligible=indices[symbol][indices[symbol][:,0]<=cutoff]
            assert eligible[-1,0]==r['index_date']
            e=np.flatnonzero(bars['t']==r['entry_raw'])[0];x=np.flatnonzero(bars['t']==r['exit_raw'])[0]
            assert abs(r['base_gross']-r['base_direction']*(bars['open'][x]-bars['open'][e])/bars['open'][e]*10000)<1e-8
            assert r['base_direction']==np.sign(bars['close'][np.flatnonzero(bars['t']==r['signal_raw'])[0]]/bars['close'][np.flatnonzero(bars['t']==r['signal_raw'])[0]-20]-1)
    checks.update(arithmetic_rows=n,comparisons=48,index_hashes=5,result='PASS',as_of_verified=False,
        orders_sent=0,at=datetime.now(timezone.utc).isoformat())
    out=here/'private/validation-v1.json'
    if out.exists():raise RuntimeError('Refuse overwrite')
    out.write_text(json.dumps(checks,indent=2),encoding='utf-8');print(json.dumps(checks))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);main(ap.parse_args().root)
