"""Small official index files and two COT sample rows; no bulk archive/API key.
One copy per URL, 1 MiB limit each, no retries or pagination.
"""
import argparse,hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import Request,urlopen
URLS={**{s:'https://cdn-api.cboe.com/api/global/us_indices/daily_prices/'+s+'_History.csv'
          for s in ('VIX','VIX9D','VVIX','OVX','GVZ')},
 'cot_disagg':'https://publicreporting.cftc.gov/resource/72hh-3qpy.json?%24limit=1',
 'cot_tff':'https://publicreporting.cftc.gov/resource/gpe5-46if.json?%24limit=1',
}
def main(out):
    if out.exists():raise RuntimeError('Refuse overwrite')
    out.mkdir(parents=True);manifest=[]
    for name,url in URLS.items():
        r=dict(name=name,url=url,received_at=datetime.now(timezone.utc).isoformat());start=time.monotonic()
        try:
            with urlopen(Request(url,headers={'User-Agent':'TradingAI-research-sample/1.0'}),timeout=20) as response:
                r.update(status=response.status,last_modified=response.headers.get('Last-Modified'));raw=bytearray()
                while True:
                    b=response.read(16384)
                    if not b:break
                    raw.extend(b)
                    if len(raw)>1048576 or time.monotonic()-start>45:raise RuntimeError('Response limit')
                path=out/(name+('.csv' if name in ('VIX','VIX9D','VVIX','OVX','GVZ') else '.json'))
                path.write_bytes(raw);r.update(file=path.name,bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        except Exception as exc:r['error']=type(exc).__name__+': '+str(exc)
        manifest.append(r);(out/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
        print(json.dumps(r),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True);main(ap.parse_args().out)
