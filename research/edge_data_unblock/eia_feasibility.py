"""Twelve metadata-only checks and one tiny dated balance sheet; no MT5."""
from pathlib import Path
import json,re
from fetch import fetch
DATES=['03_04','03_11','03_18','03_25','04_01','04_08','04_15','04_22','04_29','05_06','05_13','05_20']
OUT=Path(__file__).resolve().parent/'private'/'eia-v1'

def main():
    if OUT.exists():raise RuntimeError('Refuse overwrite')
    records=[]
    for d in DATES:
        url=f'https://www.eia.gov/petroleum/supply/weekly/archive/2026/2026_{d}/csv/table1.csv'
        r=fetch('head_'+d,url,OUT,65536,True)
        if (OUT/('head_'+d+'.raw')).exists():
            raw=(OUT/('head_'+d+'.raw')).read_text(encoding='utf-8',errors='replace')
            r['headers']={k.lower():v.strip() for k,v in re.findall(r'^(Content-Length|Last-Modified|Content-Type):\s*(.*)$',raw,re.M|re.I)}
        records.append(r)
    fetch('sample_03_04','https://www.eia.gov/petroleum/supply/weekly/archive/2026/2026_03_04/csv/table1.csv',OUT,65536)
    (OUT/'summary.json').write_text(json.dumps(records,indent=2),encoding='utf-8')

if __name__=='__main__':main()
