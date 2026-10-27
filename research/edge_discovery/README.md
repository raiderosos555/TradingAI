# Offline edge discovery

Research branch: `research/edge-discovery-20261027`. No imports of the active
trading engines, broker APIs, or forward-cohort inputs in `screen.py`.
Python 3.11+ and NumPy are required. Local data are intentionally excluded
from Git; exact files and SHA256 are listed in INPUT_HASHES.md.

From this directory, with an existing private TradingAI dataset:

```powershell
python -m unittest test_screen -v
python screen.py --root <private-data-root> --out <new-empty-results-directory>
```

The script refuses to overwrite completed results. This is an event study,
not an order simulator: ATR-normalized U must not be presented as actual R.
The four result JSON files contain aggregate diagnostics and every retained
event, including the explicit tick non-execution list in results.json.

`report.py` renders the reviewed `results-v1` into Markdown. It additionally
expects private/inventory.json from `inventory.py` and an existing private
read-only health snapshot from the earlier Recovery probe. Those inputs are
local and not required to recompute the quantitative screen. Do not collect
account data merely to reproduce the event study. The committed reports are
the sanitized rendering; hashes allow local verification.

`PROTOCOL.md` and `protocol.py` were written before computation. The first
run failed while constructing a tick output record (duplicate dictionary
keys); a regression test and correction were applied without changing the
rules, then the calculation completed. `POSTHOC_SELECTION.md` explicitly
separates later market-specific leads from the failed frozen family gate.

No synthetic market data enter measured results. Small invented fixtures
appear only in unit tests, where the expected answers are known. No active
DEMO configuration, Risk Manager, strategy or collector is modified.
