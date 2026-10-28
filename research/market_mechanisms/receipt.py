"""Read-only receipt of completed audit; no broker calls or journal writes."""
import json,sqlite3,hashlib
from pathlib import Path
from datetime import datetime


def run(root):
    base=root/'research/market_mechanisms'
    out=root/'research/replay_readiness/20261027_receipt_20261028'
    if out.exists():raise RuntimeError('Preserve receipt')
    read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
    d=read(root/'research/replay_readiness/20261027/readiness.json')
    probe=read(base/'private/demo-readonly-final.json')
    history={x['ticket']:x for x in probe['history']}
    c=sqlite3.connect((root/'state/journal.sqlite3').as_uri()+'?mode=ro',uri=True)
    records=c.execute('SELECT at,status,payload,result FROM operations').fetchall();c.close()
    checked=[];modifications=0
    lo=datetime.fromisoformat(d['window']['start_utc']);hi=datetime.fromisoformat(d['window']['end_utc'])
    for at,status,payload,result in records:
        if not lo<=datetime.fromisoformat(at)<hi:continue
        q=read_payload=json.loads(payload);r=json.loads(result) if result else {}
        if not r.get('deal'):
            modifications+=1;continue
        deal=history.get(r['deal']);req=q['request']
        fields={k:bool(deal and deal.get(k)==v) for k,v in
                [('price',r.get('price')),('volume',r.get('volume')),('symbol',req.get('symbol')),('type',req.get('type'))]}
        checked.append(dict(at=at,status=status,deal_present=bool(deal),matches=fields))
    out.mkdir(parents=True)
    evidence=dict(probe_at=probe['at'],checked=checked,non_deal_operations=modifications,
        note='Ticket match + symbol/type/price/volume; historical modifications not independently certified by deals',
        sealed_hashes={n:hashlib.sha256((root/'research/replay_readiness/20261027'/n).read_bytes()).hexdigest()
                       for n in ['REPORT.md','readiness.json','integrity.json']})
    (out/'broker-comparison.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    matches=sum(all(x['matches'].values()) for x in checked)
    report=f'''# Odbiór audytu okna 27.10 — bez ponownego audytu

Pierwotny proces zakończył zapis raportu o {d['at']}. PID 11896 nie występował
podczas odbioru; nie uruchamiano następnego audytu. Dowody źródłowe zachowano.

Okno 09:00–17:00 Europe/Warsaw: 1 600 232 rekordy tickowe, 0 błędów hashy
wybranych paczek, 0 nieudanych pobrań w oknie. Żądane zakresy pokryte przy
kandydackim offsecie. Globalnie 11 niezgodności powtórnego pobrania nakładających
się ticków (provider revised overlap); to nie jest 11 uszkodzonych plików.
Nie oznacza to kompletnego feedu: cisza wymaga kontekstu sesji, a offset nie jest
zaakceptowaną historyczną mapą UTC. 95 obserwacji zegara hosta nie certyfikuje
czasu brokera. Nie policzono wyników strategii na forward.

Kontekst: 97 wersji kalendarza, 33 wersje newsów, 2751 runtime, 1 config.
Maksymalne przerwy obserwacji około 30,5 s, poprzednia obserwacja przed oknem
zachowana. **Nie dowodzi to, że każda decyzja silnika użyła dokładnie tej wersji.**

Odczyt brokera: {probe['at']}. Terminal połączony, LIVE wyłączone, jedna otwarta
pozycja z brokerowym SL/TP, silnik WAITING, jedna operacja UNCERTAIN, kolektor
COLLECTING. Siedem kwotowań poprawnych w tym pojedynczym odczycie przy bieżącym
kandydackim offsecie; nie jest to dowód ciągłej aktualności.

Operacje okna powiązane po identyfikatorze deal z historią brokera: {len(checked)};
zgodne symbol/kierunek/cena/wolumen: {matches}. Operacje bez deal: {modifications};
historia deals nie potwierdza kolejnych historycznych zmian SL/TP. Również
wykonana operacja UNCERTAIN pozostaje w kwarantannie. Nie zmieniono jej statusu,
nie ponowiono zlecenia i nie uznano dopasowania deal za naprawę kontroli TP.

| Obszar | Decyzja | Przyczyna |
|---|---|---|
| Odporność DEMO | NO-GO | Recovery v2 niewdrożone; kwarantanna przerywa zarządzanie BE/trailing. Brokerowe SL/TP nie zastępują managera |
| Kompletność danych | NO-GO do certyfikacji | Pokrycie żądań warunkowe; UTC, rewizje feedu i luki niezaakceptowane |
| Pełny historyczny backtest | NO-GO | Brak potwierdzenia zgodności historycznej ceny i ceny decyzji, kolejności między strumieniami, kosztów i dokładnego kontekstu |

Automatyzacja tradingai-audyt-okna-27-10 usunięta po jednorazowym odbiorze.
Nie zmieniono zadań Windows, aktywnego DEMO ani kolektora. Brak deklaracji edge.
'''
    (out/'REPORT.md').write_text(report,encoding='utf-8')
    (base/'DEMO_AUDIT_RECEIPT.md').write_text(report,encoding='utf-8')
    print(json.dumps({'deal_operations':len(checked),'exact_matches':matches,'non_deal_operations':modifications}))


if __name__=='__main__':run(Path(__file__).resolve().parents[2])
