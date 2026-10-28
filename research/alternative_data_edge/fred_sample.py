"""One bounded public FRED CSV request. Failure is evidence, not a zero series."""
import argparse,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
from urllib.request import urlopen
URL='https://fred.stlouisfed.org/graph/graph.csv?id=DFII10,DGS10,T10YIE,DFF,DTWEXBGS,NFCI&cosd=2026-01-01&coed=2026-10-23'
def main(out):
    if out.exists():raise RuntimeError('Refuse overwrite')
    out.mkdir(parents=True);r={'url':URL,'at':datetime.now(timezone.utc).isoformat()}
    try:
        with urlopen(URL,timeout=20) as response:
            raw=response.read(262145)
            if len(raw)>262144:raise RuntimeError('Sample size limit')
            r.update(status=response.status,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
            (out/'sample.csv').write_bytes(raw)
    except Exception as exc:r['error']=type(exc).__name__+': '+str(exc)
    (out/'manifest.json').write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps(r))
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);main(ap.parse_args().out)
