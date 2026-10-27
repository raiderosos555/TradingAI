"""Offline validation of frozen research data. No MT5 import or broker execution."""
import argparse
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from trading_ai.research_validation import validate_dataset

if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--dataset',type=Path,default=ROOT/'exchange/research/history-20261024')
    a = p.parse_args()
    validate_dataset(a.dataset)
    print(a.dataset/'validation/report.md')
