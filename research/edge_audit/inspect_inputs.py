import json, pathlib, sqlite3
r=pathlib.Path(__file__).resolve().parents[2]
for name in ['exchange/research/history-20261024/manifest.json','exchange/research/history-20261024/US100.json','research/edge_audit/inputs/US100-H4.json']:
 d=json.loads((r/name).read_text()); print(name,list(d)); print(d.get('bars',[None])[0])
for p in (r/'exchange/backtests').glob('*.json'):
 d=json.loads(p.read_text()); print(p.name,list(d),len(d.get('trades',[])))
c=sqlite3.connect('file:'+str(r/'research/edge_audit/inputs/journal-snapshot.sqlite3')+'?mode=ro',uri=True)
print('events',c.execute('SELECT kind,count(*) FROM events GROUP BY kind').fetchall())
print('operations',c.execute('SELECT status,count(*) FROM operations GROUP BY status').fetchall())
print('last decisions',c.execute("SELECT payload FROM events WHERE kind='decision' ORDER BY seq DESC LIMIT 3").fetchall())
