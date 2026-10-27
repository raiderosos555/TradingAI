"""Small read-only inventory; no raw account data in the public output."""
import argparse,json,sqlite3,hashlib
from pathlib import Path
from datetime import datetime,timezone

def run(root,out):
    context=[]
    for s in ['GOLD','US500','OIL','EURPLN','EURUSD','GBPUSD','US100']:
        for tf in ['H4','D1']:
            p=root/f'research/edge_audit/inputs/{s}-{tf}.json';d=json.loads(p.read_text());b=d['bars']
            context.append(dict(alias=s,tf=tf,n=len(b),first_raw=b[0]['broker_raw_time'],last_raw=b[-1]['broker_raw_time'],sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
    db=root/'state/market.sqlite3';conn=sqlite3.connect(db.as_uri()+'?mode=ro',uri=True)
    try:tables=conn.execute("SELECT name,sql FROM sqlite_master WHERE type='table'").fetchall()
    finally:conn.close()
    protected={p.relative_to(root).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
        for p in [*sorted((root/'trading_ai').glob('*.py')),*sorted(root.glob('config*.json'))]}
    result=dict(at=datetime.now(timezone.utc).isoformat(),context=context,market_database_bytes=db.stat().st_size,
        market_tables=tables,active_source_hashes=protected)
    out.write_text(json.dumps(result,indent=2),encoding='utf-8')
    print(json.dumps(dict(context_series=len(context),market_database_bytes=db.stat().st_size,table_names=[x[0] for x in tables])))

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);ap.add_argument('--out',type=Path,required=True)
    a=ap.parse_args();run(a.root,a.out)
