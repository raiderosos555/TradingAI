"""Four small public requests, no credentials, no retry/pagination/subscription.
Responses remain private; coverage metadata is not a trading dataset.
"""
import argparse,hashlib,json,time
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import urlopen,Request

URLS={
 'forecast_coverage':'https://api.fxmacrodata.com/v1/predictions/coverage/usd',
 'usd_catalogue':'https://api.fxmacrodata.com/v1/data_catalogue/usd',
 'one_cpi':'https://api.fxmacrodata.com/v1/announcements/usd/inflation?limit=1',
 'nbp_five_eur':'https://api.nbp.pl/api/exchangerates/rates/a/eur/last/5/?format=json',
}
def main(out):
    if out.exists():raise RuntimeError('Refuse overwrite')
    out.mkdir(parents=True); records=[]
    for name,url in URLS.items():
        record=dict(name=name,url=url,retrieved_at=datetime.now(timezone.utc).isoformat())
        started=time.monotonic()
        try:
            with urlopen(Request(url,headers={'User-Agent':'TradingAI-research-sample/1.0'}),timeout=20) as response:
                record['status']=response.status;raw=bytearray()
                while True:
                    chunk=response.read(16384)
                    if not chunk:break
                    raw.extend(chunk)
                    if len(raw)>1048576 or time.monotonic()-started>40:
                        raise RuntimeError('Bounded response limit reached')
                path=out/(name+'.json');path.write_bytes(raw)
                record.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        except Exception as exc:
            record['error']=type(exc).__name__+': '+str(exc)
        records.append(record)
        (out/'manifest.json').write_text(json.dumps(records,indent=2),encoding='utf-8')
        print(json.dumps(record),flush=True)
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--out',type=Path,required=True)
    main(ap.parse_args().out)
