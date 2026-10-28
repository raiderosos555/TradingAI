"""Read-only local evidence and bounded network diagnostics. No trading APIs."""
import argparse, hashlib, json, os, re, ssl, subprocess, sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import urlopen
from urllib.parse import urlencode
from fetch import fetch
HERE=Path(__file__).resolve().parent
OUT=HERE/'private'/'samples-v1'

def active_data_directory(root):
    config=json.loads((root/'config.demo.json').read_text())
    install=Path(config['terminal_path']).parent.resolve()
    base=Path(os.environ['APPDATA'])/'MetaQuotes/Terminal'
    for origin in base.glob('*/origin.txt'):
        raw=origin.read_bytes();text=raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8',errors='replace').strip()
        if Path(text).resolve()==install:return origin.parent
    raise RuntimeError('Active terminal data folder not established')

def save(name,value):
    p=HERE/'private'/(name+'.json');p.parent.mkdir(parents=True,exist_ok=True)
    if p.exists():raise RuntimeError('Refuse overwrite')
    p.write_text(json.dumps(value,indent=2),encoding='utf-8')

def local(root):
    r={'at':datetime.now(timezone.utc).isoformat(),'tls':ssl.OPENSSL_VERSION}
    protected=json.loads((root/'research/market_mechanisms/private/feasibility.json').read_text())['protected_hashes']
    r['protected_hashes']={p:hashlib.sha256((root/p).read_bytes()).hexdigest() for p in protected}
    r['keys_present']={k:bool(os.environ.get(k)) for k in ('FRED_API_KEY','ALFRED_API_KEY')}
    r['env_file_keys_present']={}
    for p in root.glob('.env*'):
        if p.is_file() and p.stat().st_size<65536:
            t=p.read_text(errors='replace')
            for key in ('FRED_API_KEY','ALFRED_API_KEY'):
                m=re.search(r'^\s*'+key+r'\s*=\s*(.+)',t,re.M)
                r['env_file_keys_present'][key]=bool(m and m[1].strip().strip('\"\''))
    terminal=active_data_directory(root)
    r['maxbars']=None;r['history_log_evidence']=[]
    for p in (terminal/'config').glob('*.ini'):
        raw=p.read_bytes();text=raw.decode('utf-16' if raw[:2] in (b'\xff\xfe',b'\xfe\xff') else 'utf-8',errors='replace')
        m=re.search(r'^MaxBars=(\d+)',text,re.M)
        if m:r['maxbars']=int(m[1])
    for p in (terminal/'logs').glob('2026102[78].log'):
        for line in p.read_text(encoding='utf-16',errors='replace').splitlines():
            if any(x in line.lower() for x in ('history','timeout','synchroniz')):
                line=re.sub(r'\d{7,}','[REDACTED_NUMBER]',line)
                r['history_log_evidence'].append({'file':p.name,'line':line})
    r['cached_history']=[dict(path=str(p.relative_to(terminal)),bytes=p.stat().st_size)
        for p in (terminal/'bases').rglob('*.hcc')]
    save('local-before',r);print(json.dumps({k:v for k,v in r.items() if k not in ('protected_hashes','cached_history','history_log_evidence')}))

def network():
    try:
        with urlopen('https://publicreporting.cftc.gov/resource/gpe5-46if.json?%24limit=1',timeout=10) as q:
            py={'status':q.status,'bytes':len(q.read(65537))}
    except Exception as e:py={'error':type(e).__name__+': '+str(e)}
    save('python-tls-comparison',py)
    queries={
      'cot_tff_mapping':('gpe5-46if',{'$select':'cftc_contract_market_code,market_and_exchange_names,min(report_date_as_yyyy_mm_dd) as first,max(report_date_as_yyyy_mm_dd) as last,count(*) as n',
          '$where':"cftc_contract_market_code in ('099741','096742','13874A','209742','13874+','20974+')",'$group':'cftc_contract_market_code,market_and_exchange_names','$limit':'100'}),
      'cot_disagg_sample':('72hh-3qpy',{'$where':"cftc_contract_market_code in ('088691','067651')",'$limit':'2'}),
    }
    for name,(dataset,params) in queries.items():
        fetch(name,'https://publicreporting.cftc.gov/resource/'+dataset+'.json?'+urlencode(params),OUT,65536)
    fetch('fred_graph_single','https://fred.stlouisfed.org/graph/graph.csv?id=DFII10&cosd=2024-01-01&coed=2024-01-05',OUT,65536)
    fetch('fred_api_no_key','https://api.stlouisfed.org/fred/series/observations?series_id=DFII10&file_type=json&observation_start=2024-01-01&observation_end=2024-01-05&limit=5',OUT,65536)
    fetch('cot_announcements','https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm',OUT,1048576)
    fetch('eia_archive','https://www.eia.gov/petroleum/supply/weekly/archive/',OUT,524288)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['local','network']);p.add_argument('--root',type=Path,default=Path('C:/TradingAI'));a=p.parse_args()
    local(a.root) if a.mode=='local' else network()
