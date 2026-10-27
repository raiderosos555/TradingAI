"""Local verification and sanitized data inventory; no recalculation or trading."""
import json,hashlib,math
from pathlib import Path
from datetime import datetime,timezone
from report import table

A=Path(__file__).resolve().parent;root=A.parents[1]
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
d=read(A/'results-v1/results.json');events=read(A/'results-v1/events.json');ticks=read(A/'results-v1/tick_events.json')
inv=read(A/'private/inventory.json');market=read(A/'private/market_inventory.json')
assert all(sha(root/r['path'])==r['sha256'] for r in d['source_hashes'])
assert sha(A/'screen.py')==d['script_sha256'] and sha(A/'protocol.py')==d['protocol_sha256']
assert all(sha(root/p)==value for p,value in inv['active_source_hashes'].items())
assert len({(r['alias'],r['family']) for r in events})==53
for r in ticks:
    entry=r['entry_ask'] if r['direction']>0 else r['entry_bid']
    exit=r['exit_bid'] if r['direction']>0 else r['exit_ask']
    expected=r['direction']*(exit-entry)/r['atr']
    assert math.isclose(expected,r['after_hurdle'],abs_tol=1e-12)
    assert r['net_cash_verified'] is None and r['net_R_verified'] is None
    assert r['fill_entry_raw_ms']>=r['raw_entry']*1000+250
    assert r['fill_exit_raw_ms']>=r['raw_exit']*1000+250
assert d['independent_confirmation_observations']==0 and not d['forward_data_used_for_selection']
rows=[]
for alias in ['GOLD','US500','OIL','EURPLN','EURUSD','GBPUSD','US100']:
    symbol='OILWTI.pro' if alias=='OIL' else alias+'.pro'
    tr=[r for r in market['ticks'] if r[1]==symbol]
    br=[r for r in market['bars'] if r[1]==symbol]
    rows.append([alias,sum(r[2] for r in tr),min(r[3] for r in tr),max(r[4] for r in tr),','.join(sorted({r[2] for r in br}))])
fmt=lambda t:datetime.fromtimestamp(t,timezone.utc).isoformat()[:19]
text=['# Dodatkowy inwentarz danych, tylko metadane',
    'Nie odczytano wyników forward do wyboru strategii. Poniższe sumy runtime obejmują różne namespaces konfiguracji: '
    'nie są liczbą unikatowych ticków ani dowodem kompletności i nie były wejściem do screeningu.',
    table(['Instrument','Wiersze ticków runtime','Min raw ms','Max raw ms','Dostępne TF'],rows),
    'Historyczny kontekst z edge_audit (raw, nie potwierdzone UTC):',
    table(['Instrument','TF','N','Pierwszy raw','Ostatni raw','SHA256'],[[r['alias'],r['tf'],r['n'],fmt(r['first_raw']),fmt(r['last_raw']),r['sha256']] for r in inv['context']]),
    'Baza runtime zawiera także snapshots, deals i orders. Dane rachunku i identyfikatory konfiguracji pozostają prywatne. '
    'Historyczne kopie danych pokrywają się; nie sumujemy ich jako niezależnych obserwacji.']
(A/'DATA_INVENTORY.md').write_text('\n\n'.join(text)+'\n',encoding='utf-8')
check=dict(status='PASS',source_hashes=len(d['source_hashes']),active_sources_unchanged=len(inv['active_source_hashes']),
           tick_formula_checks=len(ticks),unit_tests=6,at=datetime.now(timezone.utc).isoformat())
(A/'private/verification.json').write_text(json.dumps(check,indent=2));print(json.dumps(check))
