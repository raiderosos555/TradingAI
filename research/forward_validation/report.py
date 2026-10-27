"""Materialize a point-in-time handoff from observed local evidence."""
import json,sqlite3
from collections import Counter
from pathlib import Path
from datetime import datetime,timezone
from collector import ROOT,A,hashfile

root=ROOT/'state/forward_validation/cohort-20261026-v1'
audit_file=A/'verification.post-recovery.json'
if not audit_file.exists():audit_file=A/'verification.final.json'
v=json.loads(audit_file.read_text());protocol=json.loads((root/'protocol.v1.json').read_text())
status=json.loads((root/'status.json').read_text());engine=json.loads((ROOT/'state/runtime/engine-status.json').read_text())
db=sqlite3.connect((root/'evidence.sqlite3').as_uri()+'?mode=ro',uri=True)
events=[json.loads(r[0]) for r in db.execute("SELECT raw FROM journal_versions WHERE source='events'")]
management=[json.loads(e['payload']) for e in events if e['kind']=='management_decision']
reasons=Counter(x.get('reason','') for x in management)
quote_holds={k:n for k,n in reasons.items() if any(w in k.lower() for w in ['bid','ask','quote','spread','stale','future','crossed'])}
starts=[json.loads(r[0]) for r in db.execute("SELECT payload FROM receipts WHERE kind='START' ORDER BY seq")]
stops=[json.loads(r[0]) for r in db.execute("SELECT payload FROM receipts WHERE kind='STOP' ORDER BY seq")]
collection_errors=[json.loads(r[0]) for r in db.execute("SELECT payload FROM receipts WHERE kind='ERROR' ORDER BY seq")]
batch_failures=[json.loads(r[0]) for r in db.execute("SELECT payload FROM receipts WHERE kind='BATCH' ORDER BY seq") if json.loads(r[0]).get('status')!='COMPLETED']
db.close()
complete=[p for p in sorted((root/'batches').glob('*/broker.json')) if (p.parent/'manifest.json').exists() and (p.parent/'result.json').exists() and json.loads((p.parent/'result.json').read_text()).get('status')=='COMPLETED']
broker=json.loads(complete[-1].read_text())
first=complete[0]
initial=json.loads(first.read_text())
first_deals={d['ticket'] for d in initial['deals'] or []}
new_deals=[d for d in broker['deals'] or [] if d['ticket'] not in first_deals]
health=dict(at=datetime.now(timezone.utc).isoformat(),engine=engine,collector=status,
    management_decisions_observed=len(management),management_reasons=dict(reasons),quote_related_holds=quote_holds,
    collector_errors=collection_errors,incomplete_batches=batch_failures,collector_starts=starts,collector_stops=stops,
    newly_observed_deal_tickets=[d['ticket'] for d in new_deals],
    starting_open_positions=len(initial['positions'] or []),last_open_positions=len(broker['positions'] or []),
    interpretation='Observation window only; not a proof of long-run stability. New ticket arrival is not a verified UTC execution time.')
(A/'demo-health.json').write_text(json.dumps(health,indent=2),encoding='utf-8')
total=sum(s['ticks'] for s in v['streams'].values());matches=sum(s['overlap_matches'] for s in v['streams'].values())
rows=['| Strumień | Ticki w rozłącznych odcinkach | Nakładki zgodne | Niewykonywalne Bid/Ask |', '|---|---:|---:|---:|']
for symbol,s in v['streams'].items():rows.append(f"| {symbol} | {s['ticks']} | {s['overlap_matches']} | {s['invalid_quotes']} |")
text=f'''# Przyszła walidacja TradingAI — uruchomienie zbierania danych

Stan dowodów: {v['at']}. Raport dotyczy uruchomienia rejestratora, nie wyniku strategii.

**GO: pasywne zbieranie przyszłych danych. NO-GO: twierdzenie o przewadze lub pełnej zgodności replay z DEMO.**

## Co rzeczywiście działa

- Zadanie Windows `TradingAI-Forward-Evidence` działa lokalnie, bez modelu i bez API wysyłania zleceń.
- Dane: `C:\\TradingAI\\state\\forward_validation\\cohort-20261026-v1`.
- Surowe Bid/Ask/Last, wolumeny, flagi oraz kolejność odpowiedzi MT5: 7 instrumentów i 2 strumienie FX.
- Na moment audytu **{total} ticków**, **{matches} zgodnych nakładek**, **{len(v['integrity_errors'])} błędów integralności**. Ticki powtórzone w nakładkach nie są ponownie liczone; identyczne ticki wewnątrz odpowiedzi pozostają zachowane.
- Pierwszy pełny odczyt: po 220 zamkniętych H1, H4 i D1 dla wszystkich 7 instrumentów. Surowe historyczne znaczniki nie zostały uznane za zweryfikowane UTC.
- Specyfikacje kontraktów i bieżące kalkulacje profit/margin, pozycje, zlecenia i historia transakcji brokera są zapisywane w paczkach. Wykonania zawierają cenę, wolumen, commission, fee, swap i profit.
- Zachowane wersje kalendarza: **{v['context_versions'].get('calendar',0)}**, newsów: **{v['context_versions'].get('news',0)}**. Pełne bajty JSON, pierwsze otrzymanie i błędy odczytu są przechowywane osobno. Nie przypisujemy nowej wersji do wcześniejszej decyzji.
- Dziennik: **{v['journal_versions'].get('events',0)}** zaobserwowanych nowych zdarzeń; wersje operacji, sygnałów i ustawień zapisane niezależnie. Pierwszy zrzut wcześniejszego stanu nie staje się nową próbą forward.
- 13 testów rejestratora/weryfikacji i 13 testów archiwum kontekstu przeszło. Kontrolowany restart wyłącznie rejestratora odtworzył kursory; nakładki po wznowieniu są sprawdzane jak pozostałe. Dane dzisiejsze są rozruchem i kalibracją.

{chr(10).join(rows)}

## Czas i luki

Ocena całego dotychczasowego odcinka: `{v['clock']['status']}`. Początkowo dwa odrębne eksporty kalendarza, równoczesne odczyty czasu ticków i raport NTP Windows potwierdzały offset +3600 s, przy oszacowanej niepewności zegara około 1,55 s. Po przerwie sieciowej raport NTP dał oszacowanie około 8,16 s, powyżej zadeklarowanego progu 2 s, więc pełen odcinek nie został zaakceptowany. Trzy niezależne odczyty NTP o 18:20:21–23 UTC pokazały odchylenie około 0,160–0,164 s i RTT 0,037–0,041 s (`ntp-direct-probe.txt`); nie dowodzą one jakości czasu w trakcie wcześniejszej przerwy. Nie zmieniano zegara Windows ani konfiguracji czasu DEMO. Surowe ticki pozostają niezmienione.

Nie rozszerzamy tego ustalenia na 22.10, historyczny DST ani czas poza obserwowanym zakresem. Przed replay potrzebna jest mapa segmentów czasu dla wybranego odcinka i jawne potraktowanie decyzji przy granicach niepewności czasowej. Raport `verification.final.json` przechowuje dokładny zakres i dowody.

Każda kolejna paczka sprawdza dokładną zgodność 2 sekund poprzedniego odcinka, łącznie z kolejnością i powtórzeniami. Wykrywamy cofnięcie czasu, brak ciągłości zakresów, puste odcinki, zmienione nakładki, zerowe/crossed Bid/Ask, ciszę pomiędzy tickami i skoki zegara hosta. **Cisza nie oznacza automatycznie zgubionych ticków ani kompletności feedu**; trzeba zestawić ją z sesją instrumentu. Nie odtwarzamy cen sztucznie.

## Zamrożony zakres przyszłego pomiaru

Protokół zapisano {protocol['registered_at']}, przed wynikami wybranego okna. Pierwsze okno: **27.10.2026 08:00–16:00 UTC, czyli 09:00–17:00 Europe/Warsaw**. Wszystkie 7 instrumentów i obie istniejące strategie lokalne, bez zmiany parametrów. Limit 7 pozycji odzwierciedla wcześniej zatwierdzony stan DEMO; porównanie nie może po cichu użyć starszej konfiguracji z limitem 2.

Kolejne dni robocze w tych samych godzinach są rejestrowane także wtedy, gdy nie było transakcji lub dane okażą się niewystarczające. Nie zastępujemy słabego dnia lepszym. Jedna doba służy sprawdzeniu odtwarzania, nie wykazaniu przewagi. Protokół przewiduje pierwszy wniosek statystyczny dopiero po co najmniej 60 sesjach i 100 zamkniętych transakcjach; te progi nie gwarantują mocy statystycznej. Bieżąca autoryzacja handlu DEMO nadal kończy się 30.10; rejestrator jej nie przedłuża.

## Co pozostaje przed pierwszym wiarygodnym replay

1. Poczekać na z góry wskazane przyszłe okno i sprawdzić jego paczki, czas, kalendarz, FX i świece. Nie ma jeszcze kompletnego nowego odcinka ani wyniku replay.
2. Dobrać politykę kosztów i opóźnień na podstawie zarejestrowanych rzeczywistych wykonań, niezależnie od rentowności strategii. Bieżące `order_calc_profit/margin` nie podają taryfy prowizji ani realizacji przyszłego zlecenia. Brak zaobserwowanej prowizji nie dowodzi, że zawsze wynosi zero.
3. Uzgodnić rzeczywisty stan startowy DEMO z replay. Przy uruchomieniu była **{len(initial['positions'] or [])} otwarta pozycja**; istniejący adapter rozpoczyna od pustego portfela. Nie wolno przemilczeć tej różnicy ani wymusić zamknięcia w celu poprawienia próby.
4. Rozstrzygnąć zdarzenia różnych instrumentów z takim samym znacznikiem milisekundowym. Historia MT5 dostarcza kolejność w obrębie strumienia, nie wspólny numer sekwencji całego portfela. Kolejność pobrania plików nie jest kolejnością brokerową. Konieczne jest wykazanie niewrażliwości wyniku na nierozstrzygnięte kolejności albo pozostawienie wyniku warunkowego.
5. Rozdzielić kontekst dostępny rejestratorowi od dokładnych wejść użytych przez aktywny silnik. Polling co 5 s i dziennik nie dowodzą, które bajty kalendarza DEMO odczytał przy każdej decyzji. Dokładne porównanie wymaga przechwycenia wejść albo udokumentowania równoważności wersji w danej decyzji.

To konkretne ograniczenia pierwszego porównania; nie rozpoczynamy kolejnego szerokiego strojenia ani badań parametrów. Automatyczny `readiness.json` jest bramką danych, **nie automatycznym uruchomieniem ani certyfikatem poprawnego backtestu**. Pełne porównanie cen, kosztów, zarządzania i P&L pozostaje oczekujące; wartości nie są zastępowane zerami.

## DEMO i oddzielny monitoring

W próbce obserwacji: **{len(management)} decyzji zarządzania**, **{sum(quote_holds.values())} decyzji wstrzymanych z przyczyn kwotowań/spreadu**; powtórzone decyzje nie oznaczają odrębnych incydentów. Nowe numery transakcji względem pierwszego zrzutu: **{len(new_deals)}**. Pierwszy zrzut zawiera wcześniejszą historię i nie jest dowodem nowych wykonań.

Stan silnika w ostatnim odczycie ({engine['at']}): **{engine['status']}**, pozycje raportowane przez silnik: {engine.get('positions','brak w tym statusie')}, quarantined={engine.get('quarantined','brak w tym statusie')}, PID {engine['pid']}. Ostatni pełny odczyt brokera pokazał {len(broker['positions'] or [])} pozycji. Wszystkie produkcyjne pliki Python są identyczne ze zrzutem z początku tego zadania. Nie wdrożono poprawki kwotowań ani zmian czasu DEMO.

### Dwa rzeczywiste problemy ujawnione w trakcie rejestracji

**Cena wykonania a historia:** DEMO wykonał SELL GOLD.pro 0,001 po 4020,13; broker potwierdził tę samą cenę i zerowe commission/fee/swap dla tego konkretnego dealu. Dziennik Risk Managera zapisał Bid 4020,13 / Ask 4020,60 przy raw `1793041594963`. Historia ticków zawiera dla tej samej milisekundy dwa rekordy: Bid 4020,20 oraz 4020,25, oba z Ask 4020,49. Żaden nie odtwarza dokładnie kwotowania z decyzji. Różnica wykonanie–referencja Risk Managera wynosi 0; zlecenie MARKET nie zawierało zadanej ceny, więc różnica względem ceny żądanej jest null. Brak ticka dokładnie w milisekundzie dealu nie zostaje zastąpiony starszym tickiem. Dowody: `observed-fill-comparison.json`. To kalibracja mechaniki, nie wynik strategii. Minimalne dalsze sprawdzenie: ocenić powtarzalność rozbieżności na kolejnych już rejestrowanych wykonaniach i ustalić, czy potrzebny jest osobny model strumienia widzianego przez silnik; nie stroić strategii pod tę różnicę.

**Rozłączenie:** log terminala pokazuje utratę połączenia o 19:13:44 czasu lokalnego (18:13:44 UTC), ponowną autoryzację 19:15:49 i synchronizację 19:15:59. Rejestrator zachował nieudane paczki i wznowił pobieranie od wcześniejszych kursorów. Proces silnika PID 10844 zakończył się z kodem 1; nie uruchomił się sam. O 18:18 UTC uruchomiono istniejące zadanie DEMO bez zmiany źródeł i konfiguracji (PID 652); ponowna aktywacja wymagała standardowo dwóch eksportów zegara EA. Nie ustalono jeszcze przyczyny zakończenia procesu z kodem 1. Brak wykrycia błędnego Bid/Ask w poprawnie pobranych tickach nie oznacza ciągłości zarządzania podczas tej przerwy. Dowody: `terminal-network-excerpt.txt`, `demo-recovery-incident.json`, `demo-health.json`. **NO-GO dla twierdzenia, że DEMO jest odporny na rozłączenia.** Minimalna potrzebna poprawa to zdiagnozowanie zakończenia procesu i przetestowanie nadzoru restartów z weryfikacją stanu/kwotowań; nie wdrożono takiej poprawki.

## Działanie bez udziału modelu

Rejestrator sam pobiera kolejne paczki, zapisuje kontekst i dziennik oraz co 5 minut aktualizuje wstępną gotowość. Zadanie Windows ponawia uruchomienie co 2 minuty po zakończeniu procesu i przy logowaniu; blokada zapobiega podwójnemu zapisowi. Komputer, sesja użytkownika i połączony MT5 muszą działać. Wyłączenie komputera nie zostaje ukryte jako pełna obserwacja; późniejszy backfill ticków nie odtworzy dawnych wersji kalendarza.

Niekompletne paczki zachowane w archiwum: **{len(batch_failures)}**. Nie są błędem hasha; są odrębną informacją o niedostępności danych. Po wznowieniu DEMO odczyt dziennika o 18:22 UTC potwierdził 12 kolejnych decyzji zarządzania obejmujących obie pozycje (US500 i GOLD), bez blokady kwotowań w tej próbce (`management-after-recovery.json`). Jest to potwierdzenie powrotu zarządzania, nie usunięcia przyczyny awarii.

Rezerwa dysku 10 GiB blokuje następne pobrania ticków, nie działanie DEMO. Wszystkie błędy pozostają w archiwum; źródła, konfiguracja, paczki i lokalny łańcuch odbiorów mają hashe. Hashe lokalne wykrywają zmiany, ale nie stanowią zewnętrznie poświadczonego czasu.
'''
(A/'REPORT.md').write_text(text,encoding='utf-8')
print(json.dumps(dict(ticks=total,overlap_matches=matches,management_decisions=len(management),quote_holds=quote_holds,
    newly_observed_deals=len(new_deals),engine_pid=engine['pid'],collector_errors=collection_errors)))
