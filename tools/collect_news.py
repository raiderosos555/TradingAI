"""Fetch configured public feeds; no broker connection, credentials or model calls."""
import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from trading_ai.news import collect
if __name__=='__main__':
    d=collect(ROOT/'state/news')
    print(d['status'],len(d['items']),{k:v['status'] for k,v in d['sources'].items()})
