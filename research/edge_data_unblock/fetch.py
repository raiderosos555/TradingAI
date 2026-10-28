"""Bounded public HTTPS samples; Windows curl/Schannel verifies TLS normally.
No insecure flags, credentials, automatic pagination, retries or paid endpoints.
Each artifact is immutable. JSON evidence and raw files stay private.
"""
import argparse, hashlib, json, subprocess
from datetime import datetime, timezone
from pathlib import Path

def fetch(name, url, out, limit=1048576, head=False):
    out.mkdir(parents=True, exist_ok=True)
    dest=out/(name+'.raw'); meta=out/(name+'.json')
    if dest.exists() or meta.exists(): raise RuntimeError('Refuse overwrite: '+name)
    args=['curl.exe','--silent','--show-error','--fail-with-body','--location',
          '--proto','=https','--proto-redir','=https','--connect-timeout','10',
          '--max-time','35','--max-filesize',str(limit),
          '--user-agent','TradingAI-public-research/1.0','--output',str(dest),
          '--write-out','%{http_code}|%{size_download}|%{ssl_verify_result}']
    if head: args.append('--head')
    r={'name':name,'url':url,'started_utc':datetime.now(timezone.utc).isoformat(),
       'limit_bytes':limit,'tls_verification':True,'head':head}
    try:
        p=subprocess.run(args+[url],capture_output=True,text=True,timeout=40,
                         creationflags=subprocess.CREATE_NO_WINDOW)
        r.update(returncode=p.returncode,transport=p.stdout,error=p.stderr[:800])
    except subprocess.TimeoutExpired: r.update(returncode=-1,error='HARD_TIMEOUT_40S')
    if dest.exists():
        raw=dest.read_bytes();r.update(bytes=len(raw),sha256=hashlib.sha256(raw).hexdigest())
        if len(raw)>limit: raise RuntimeError('Response limit violated')
    meta.write_text(json.dumps(r,indent=2),encoding='utf-8')
    print(json.dumps(r),flush=True);return r

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('name');p.add_argument('url')
    p.add_argument('--out',type=Path,default=Path(__file__).parent/'private'/'samples-v1')
    p.add_argument('--limit',type=int,default=1048576);p.add_argument('--head',action='store_true')
    a=p.parse_args();fetch(a.name,a.url,a.out,a.limit,a.head)
