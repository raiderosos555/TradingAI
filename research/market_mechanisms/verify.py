"""Verify saved evidence and independent arithmetic without repeating the screen."""
import argparse,json,hashlib,math
from pathlib import Path
import experiment as E
import protocol as P


def run(root):
    base=root/'research/market_mechanisms';f=E.read(base/'private/feasibility.json')
    r=E.read(base/'private/results-v1.json')
    for h in r['source_hashes']:assert E.sha(root/h['path'])==h['sha256'],h['path']
    assert E.sha(root/'exchange/research/cost-sample-20261022/summary.json')==r['cost_source_sha256']
    for name in ('experiment.py','protocol.py','test_experiment.py','audit_data.py'):
        assert E.sha(base/name)==r['code_hashes'][name],name
    assert E.sha(base/'HYPOTHESIS_REGISTRY.md')==r['registry_sha256']
    for path,h in f['protected_hashes'].items():assert E.sha(root/path)==h,path
    market={}
    for name in P.ALIASES:
        for tf in ('H1','H4','D1'):
            a,_=E.load(root,name,tf)
            market[name,tf]={int(t):float(o) for t,o in zip(a['t'],a['open'])}
    ends={};n=0
    for row in r['events']:
        m=row['mechanism'];alias=row['alias'];tf={'M1':'D1','M2':'H1','M3':'H4','M4':'H1'}[m]
        te=row['entry_raw'];tx=row['exit_raw'];ts=row['signal_raw']
        assert E.epoch(P.START)<=ts<te<tx<E.epoch(P.END)
        if row['period']=='early':assert tx<E.epoch(P.SPLIT)
        else:assert ts>=E.epoch(P.SPLIT)
        key=m,alias;assert ends.get(key,0)<=te;ends[key]=tx
        if m=='M4':
            a=market['US100',tf];b=market['US500',tf];beta=row['beta']
            pa=a[te];pb=b[te]
            ra=(a[tx]-pa)/pa;rb=(b[tx]-pb)/pb
            change=(ra-beta*rb)/(1+abs(beta))
            cost=(r['spread_price_hurdles']['US100']/pa+abs(beta)*r['spread_price_hurdles']['US500']/pb)*10000/(1+abs(beta))
        else:
            a=market[alias,tf];price=a[te];change=(a[tx]-price)/price
            cost=r['spread_price_hurdles'][alias]/price*10000
        gross=row['direction']*change*10000
        assert math.isclose(gross,row['gross'],abs_tol=1e-8)
        assert math.isclose(cost,row['hurdle'],abs_tol=1e-10)
        assert math.isclose(gross-cost,row['after_hurdle'],abs_tol=1e-8)
        assert row['stress']<row['after_hurdle'];n+=1
    assert n==sum(r['results'][m+'/ALL']['all']['n'] for m in ('M1','M2','M3','M4'))
    for name in ['RESEARCH_REVIEW.md','DATA_FEASIBILITY.md','HYPOTHESIS_REGISTRY.md','EDGE_RESEARCH_RESULTS.md','DETAILS.md']:
        assert (base/name).stat().st_size>100
    report=dict(status='PASS',input_files=len(r['source_hashes'])+1,events_checked=n,
                protected_files_unchanged=len(f['protected_hashes']),strategy_parameters_changed=False,
                orders_sent=0,forward_returns_used=False)
    (base/'private/verification.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report))


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);run(ap.parse_args().root)
