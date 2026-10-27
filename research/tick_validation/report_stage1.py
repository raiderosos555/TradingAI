"""Stage-1 report only. Later-stage deliverables explicitly remain pending."""
from pathlib import Path
import json,hashlib,csv,statistics,sys
from datetime import datetime,timezone
from collections import Counter
A=Path(__file__).resolve().parent;ROOT=A.parents[1]
def read(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def fmt(v):return '—' if v is None else f'{v:.9g}' if isinstance(v,float) else str(v)
def table(head,rows):return '\n'.join(['| '+' | '.join(head)+' |','|'+'|'.join('---' for _ in head)+'|']+['| '+' | '.join(fmt(v) for v in r)+' |' for r in rows])
def report(name,parts):(A/name).write_text('\n\n'.join(parts)+'\n',encoding='utf-8')
prices=read(A/'price_checks.json');coverage=read(A/'coverage.v2.json');tests=read(A/'tests.json');clock=read(A/'clock_assessment.json');grids=read(A/'bar_grid_checks.json')
newclock=read(sorted((A/'evidence').glob('clock-*.json'))[-1]);fresh=[r for r in newclock['records'] if r['fresh_within_600s']]
clock2={**clock,'followup_captured_at_utc':newclock['captured_at_utc'],'fresh_EA_offset_seconds':sorted({r['server_minus_gmt_seconds'] for r in fresh}),
 'DST_wall_clock_change_observed':any(r['server_minus_gmt_seconds']==3600 for r in fresh),'tick_encoding_after_DST_verified':False,
 'notes':['Deal-vs-host anchors on 23-Oct support +7200 only at observed operations.','EA offset changed from +7200 (24-Oct capture) to +3600 (25-Oct capture).','EA arithmetic shares host clock; cannot substitute for history tick/UTC evidence.','No exact transition time or older offset schedule inferred.','No automatic assignment of Europe/Warsaw to broker.','Accepted historical mapping segments remain empty.']}
(A/'clock_assessment.v2.json').write_text(json.dumps(clock2,indent=2),encoding='utf-8')
now=datetime.now(timezone.utc).isoformat();scope='Etap 1, raport '+now+'. Wyłącznie badanie danych, cen i czasu. Brak zleceń, zmian produkcyjnych, strojenia strategii i pełnego ponownego backtestu. Wszystkie dane historyczne są eksploracyjne.'
report('DATA_COVERAGE.md',[
'# Dostępność danych tickowych — etap 1',scope,
'## Potwierdzone lokalne dane',
'Sprawdzono 371 167 zapisanych ticków z siedmiu instrumentów, po jednej godzinie na instrument. Surowy przedział osi API: `[1792681200000, 1792684800000)` ms, czyli etykieta 22.10.2026 15:00–16:00 przy formatowaniu liczby epoki. **Nie nadajemy jej automatycznie znaczenia UTC.** Poprzedni audyt opisywał tę godzinę jako 13:00–14:00 UTC po odjęciu 7200 s. Nowy kod przywraca `broker_raw_time_msc` i zachowuje osobno niepotwierdzone mapowanie.',
table(['Instrument','Ticki','Pierwszy raw ms','Ostatni raw ms','Największa przerwa ms','Pary o tym samym ms'],[[r['instrument'],r['ticks'],r['first_raw_ms'],r['last_raw_ms'],r['largest_gap_ms'],r['equal_timestamp_pairs']] for r in prices]),
'Wszystkie te strumienie przeszły walidację dodatnich, skończonych Bid/Ask, Ask≥Bid oraz niemalejącego czasu. Rekordy o tym samym milisekundowym znaczniku zachowują kolejność dostawcy. Nie sortujemy uszkodzonych szeregów, nie odrzucamy domniemanych duplikatów i nie interpolujemy brakujących cen. Przerwa między tickami może oznaczać brak zmian ceny, zamknięcie sesji albo brak danych — sama jej długość nie rozstrzyga przyczyny. Równe timestampy nie dowodzą błędu danych.',
'## Ograniczone zapytania o dalszą historię',
table(['Data w surowej osi','Status próby GOLD','Pozostałe instrumenty'],[[d,next(r['status'] for r in coverage if r['date_raw']==d and r['instrument']=='GOLD'),'Nie odpytywano po przekroczeniu limitu czasu'] for d in sorted({r['date_raw'] for r in coverage})]),
'Zaplanowano 56 okien po 2 minuty (12:00–12:02 w surowej osi), obejmujących początek i podział dawnej próby oraz okolice poprzednich DST. Osiem prób GOLD przekroczyło 18-sekundowy limit procesu; pozostałe 48 pominięto, aby nie mnożyć kosztownych prób. Limit obejmuje inicjalizację i odczyt, więc nie dowodzi, że zawiesił się konkretnie serwer historii. **TIMEOUT nie oznacza EMPTY ani braku danych u brokera. Nie ustalono najwcześniejszego ani pełnego zakresu dostępności historycznej.**',
'Zachowano `coverage.v2.json` i `bounded_manifest.v2.json`. Pierwsza wersja procesu pomocniczego miała błąd lokalnego importu MetaTrader5; jej `coverage.json` nie służy do oceny brokera. Początkowy nieograniczony odczyt starej historii przerwano; zastąpił go ograniczony proces badawczy. Nie zatrzymywano terminala ani procesów DEMO.',
'## Świece i kalendarz',
'Z wcześniejszych odczytów odzyskano surowe czasy H4/D1 dla GOLD, US100 i EURUSD wokół jesieni 2025 oraz wiosny 2026; dokładne rekordy są w `evidence/raw-grid-*.json`. Początek przechowywanego rocznego zbioru może wypadać po żądanym początku okna; nazwa okna nie stanowi dowodu pełnego pokrycia. H1 historycznie porównano na wyżej wymienionej godzinie; nie pozyskano dodatkowej pełnej historii H1 wokół dawnych DST.',
'Brak archiwalnych harmonogramów sesji uniemożliwia odróżnienie każdej luki od poprawnego zamknięcia rynku. Oficjalne API zwraca pola ticków i znaczniki zmian, lecz pobranie wycinka nie certyfikuje pełności historii. [Dokumentacja copy_ticks_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py).',
'## Odtworzenie',
'`evidence/basis-*.json.gz` zawiera kopie znanych ticków. `price_checks.json/csv`, `bar_grid_checks.json`, `clock_assessment.v2.json` i hashe umożliwiają weryfikację offline. Nie wymagają ponownego pobierania z MT5. Nowe kolekcje należy zapisywać pod nową wersją; ukończony bounded manifest blokuje przypadkowe powtórzenie zapisu.'])
report('PRICE_MODEL.md',[
'# Last, Bid, Ask i czas — etap 1',scope,
'## Model sygnału i wykonania',
'`model.py` jest izolowanym modułem badawczym bez importu MetaTrader5 i bez mechanizmu wysyłania zleceń. Last służy do potencjalnego budowania świec sygnałowych. Domyślna agregacja Last uwzględnia tylko ticki z flagą aktualizacji Last (bit 8), aby przeniesiona wartość Last na ticku samego Bid/Ask nie tworzyła sztucznego nowego sygnału. Brak Last daje brak świecy, a nie zastępcze Bid.',
table(['Operacja','Cena dostępna na ticku'],[['Otwarcie BUY','Ask'],['Zamknięcie BUY / kontrola SL i TP','Bid'],['Otwarcie SELL','Bid'],['Zamknięcie SELL / kontrola SL i TP','Ask']]),
'`first_executable_quote` wymaga ticku późniejszego niż moment decyzji o jawną dodatnią latencję (domyślny parametr testowy 1 ms, nie zmierzony poślizg). Nie przeskakuje szerokiego spreadu w poszukiwaniu korzystniejszej ceny. Luka przekraczająca limit oczekiwania blokuje wykonanie. Cena jest dostępnym kwotowaniem, nie gwarancją pełnej realizacji wolumenu; płynność, slippage i opóźnienia wymagają osobnego modelu.',
table(['Rynek','Last w pierwszym rekordzie','Bid','Ask','Błąd OHLC Last z aktualizacji','Błąd OHLC Bid'],[[r['instrument'],r['first_Last'],r['first_quotes']['SELL_OPEN'],r['first_quotes']['BUY_OPEN'],r['Last_updates_OHLC_error'],r['Bid_OHLC_error']] for r in prices]),
'We wszystkich siedmiu przypadkach Last z flagowanych aktualizacji odtwarza oryginalny OHLC dokładnie. Bid nie jest tym samym szeregiem. Użycie właściwej strony ceny zostało sprawdzone na rzeczywistych rekordach, a nie tylko na przykładach syntetycznych.',
'## Koszty i kontrakty',
'Spread wynika bezpośrednio z Bid/Ask i nie jest ponownie odejmowany jako osobna opłata. `cash_result` wymaga jawnych danych FX/cash factor, prowizji i swapu; None lub NaN blokuje PnL. Funkcja pozwala wyraźnie podać zero, ale nie dowodzi historycznej prawdziwości tej wartości. `validate_contract` sprawdza okres ważności specyfikacji, identyfikator dowodu, siatkę wolumenu, minimum/maksimum i siatkę cen. Bieżący snapshot kontraktu nie został automatycznie uznany za historyczny.',
'Nie policzono historycznego netto, ponieważ kompletność kosztów, kontraktów i wykonania nie została potwierdzona. Przyszła warstwa musi dodatkowo sprawdzić stops/freeze, prawa handlu, margin, częściowe realizacje i historyczną taryfę. Walidator siatki cen nie zastępuje pełnego Risk Managera.',
'## Mapowanie czasu',
'Nie ma domyślnego odjęcia 7200 ani 3600 s. `to_utc` wymaga dokładnie jednego zweryfikowanego segmentu czasowego z identyfikatorem dowodu. Poza zakresem, przy nieznanym offsetcie lub niejednoznaczności jesiennej zmiany czasu odmawia mapowania. Surowa kolejność umożliwia weryfikację cen, ale nie wystarcza do limitu dziennego UTC ani dopasowania publikacji makro.',
f"Pięć istniejących dealów z 23.10 daje różnicę surowego czasu brokera do czasu UTC zapisu zamiaru od {clock['observed_raw_minus_intent_range_seconds'][0]:.6f} do {clock['observed_raw_minus_intent_range_seconds'][1]:.6f} s. Wspiera to +7200 s w tych obserwacjach (z latencją około 0,11–0,13 s); nie wyznacza całego historycznego harmonogramu.",
'Zapis EA z 24.10 wskazuje server−GMT=7200 s, świeże eksporty z 25.10 wskazują 3600 s. Windows raportuje synchronizację SNTP; surowy wynik kontroli zapisano w `evidence/clock-*.json`. Potwierdza to zmianę relacji zegarów, lecz nie dokładną chwilę przestawienia ani kodowanie nowych ticków po DST. W niedzielę brak świeżych notowań nie pozwala potwierdzić tego ostatniego.',
'Dokumentacja Python MT5 opisuje znaczniki jako UTC, co wymaga uzgodnienia z zaobserwowaną rozbieżnością na tym rachunku. EA TimeGMT zależy od zegara i ustawień komputera, więc nie jest niezależnym źródłem czasu. [API ticków](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py), [TimeGMT](https://www.mql5.com/en/docs/dateandtime/timegmt).',
'Nie przypisano brokerowi strefy Europe/Warsaw. Testy tej strefy sprawdzają wyłącznie mechanikę 23/25-godzinnego D1, 3/5-godzinnego H4 przecinającego zmianę czasu, nieistniejącą i powtórzoną godzinę H1 oraz przedziały [open, close). Bez dowodu polityki sesyjnej takie granice nie mogą zostać użyte do produkcyjnej historii brokera. Działającego DEMO nie modyfikowano.'])
report('EXECUTION_PARITY.md',[
'# Zgodność wykonania — stan po etapie 1',scope,
'**Nie potwierdzono jeszcze zgodności pełnego symulatora z Position Managerem.** Zakończono testy prymitywów cenowych i czasu. Reguły produkcyjne odczytano z `trading_ai/manager.py`, `risk.py` i `execution.py`; nie zmieniano ich.',
table(['Obszar','Zweryfikowane teraz','Pozostało do etapu zgodności'],[
['BUY/SELL','Cztery strony Bid/Ask na kontrolowanych i rzeczywistych tickach','Cały proces decyzja→Risk→request→fill oraz limity margin'],
['SL/TP','Warunek po właściwej stronie rynku; SL przy luce nie otrzymuje fikcyjnej ceny poziomu','Pełny model serwerowy SL/TP, kolejność względem cyklu aplikacji i slippage'],
['TP1/TP2','Odczyt priorytetów produkcyjnych; test siatki wolumenów','Częściowe zamknięcia, minimalna reszta, jednokrotność TP1 i PnL częściowe'],
['BE/trailing','Wskazano reguły źródłowe','Replikacja i test różnicowy z rzeczywistym PositionManager/RiskManager'],
['Spread','Dynamiczne Bid/Ask; odrzucenie nadmiernego spreadu w momencie wykonania','Rozdzielenie zleceń aplikacji od ochronnych SL/TP brokera'],
['Minimum lota','Minimum, maksimum i krok wolumenu','Odmowa TP1 z nieprawidłową pozostałością i rezerwacja ryzyka'],
['Dzienny limit','Nieznany UTC blokuje mapowanie','Wspólne equity, baseline UTC 00:00, cash adjustments, dzienna strata'],
['Rozłączenie','Brak ticku/luka blokuje nowy fill','Serwerowe SL/TP podczas odłączenia, reconnect i uzgodnienie bez duplikacji'],
['Koszty','Wymagane jawne wejścia; brak podwójnego spreadu','Potwierdzona historyczna prowizja, swap, FX i rzeczywisty slippage']]),
'Production PositionManager sprawdza STOP_CLOSE, INVALIDATION, TP2, TP1, BREAK_EVEN, TRAILING, po pierwszej potwierdzonej operacji czeka na następny cykl. Risk Manager ogranicza operacje aplikacji przy szerokim spreadzie, sprawdza freeze/stops, a dla TP1 wolumen i minimalną resztę. SL/TP już na serwerze nie mogą być mylone z operacją aplikacji zablokowaną przez spread. Tego rozróżnienia pełny replay jeszcze nie implementuje.',
f"Testy automatyczne: {tests['tests']} uruchomionych, {tests['failures']} błędnych asercji, {tests['errors']} błędów wykonania. Szczegóły w `test_model.py`, `tests.txt` i `tests.json`. Nie są testami rentowności ani pełnej zgodności Risk/Position Managera.",
'Polecenie offline: `.\\.venv\\Scripts\\python.exe -m unittest discover -s research\\tick_validation -p test_model.py -v`. Fixtures testowe są jawnie syntetyczne i nie zastępują brakujących historycznych ticków.'])
report('BACKTEST_COMPARISON.md',[
'# Porównanie starego i poprawionego backtestu — bramka etapu 1',scope,
'**Pełnego ponownego backtestu nie uruchomiono.** Zgodnie z kolejnością prac najpierw przedstawiamy weryfikację danych/cen/czasu. Zgodność zarządzania pozycją i historyczne koszty pozostają niepotwierdzone; porównanie PnL teraz byłoby przedwczesne.',
table(['Metryka','Status'],[['Liczba sygnałów','NIE BADANO — reguły strategii niezmienione, brak nowego replay'],['Wykonane wejścia','NIE BADANO — brak pełnej symulacji'],['Poziomy realizacji','Sprawdzono tylko dobór strony kwotowania'],['Netto, PF, expectancy R, drawdown','NIE WYLICZONO'],['Wpływ prowizji','Nieznana zweryfikowana historyczna taryfa'],['Wpływ spreadu','Dynamiczny spread widoczny w rzeczywistych tickach; bez oszacowania wpływu na wynik strategii']]),
'## Kontrola formuły ceny na identycznym rekordzie',
table(['Rynek','Stara formuła BUY','Dostępny Ask','Różnica','Stara formuła SELL','Dostępny Bid','Różnica'],[[r['instrument'],r['old_BUY_entry_formula'],r['first_quotes']['BUY_OPEN'],r['old_buy_minus_observed_ask'],r['old_SELL_entry_formula'],r['first_quotes']['SELL_OPEN'],r['old_sell_minus_observed_bid']] for r in prices]),
'Stara formuła: open Last + dawny stały spread + 2 punkty slippage dla BUY oraz Last −2 punkty dla SELL. Nowa kolumna pokazuje wyłącznie kwotowanie Ask/Bid bez wymyślonej realizacji i poślizgu. To demonstracja błędnego podstawienia ceny, nie porównanie dwóch transakcji strategii i nie prognoza poprawy PnL. Różnica może działać w obie strony.',
'Pełne porównanie po kolejnej bramce: identyczne zamrożone reguły i sygnały Last, wspólny zakres potwierdzonych ticków, uzgodnione UTC/kontrakty/koszty, testy zgodności Position Managera, następnie porównanie sygnałów, wejść, fillów, opłat, netto, PF, R i DD. Wszystkie stare dane pozostają eksploracyjne; bez promowania parametrów.'])
report('REMAINING_LIMITATIONS.md',[
'# Pozostałe ograniczenia i kolejny etap',scope,
'**Decyzja po pierwszej weryfikacji:** baza do poprawnego rozdzielenia cen jest gotowa i przetestowana. Pełna wiarygodność historycznego backtestu nie została jeszcze osiągnięta.',
'1. Dostępność: potwierdzona jest jedna godzina ticków na siedmiu rynkach. Nowe odczyty miały timeout; nie wiemy, ile historii broker udostępnia. Kolejna kolekcja powinna zaczynać od jednego krótkiego, znanego okna, ze znacznikiem fazy IPC/odczytu i limitem procesu. Nie restartować DEMO ani terminala dla badania.',
'2. Czas: +7200 potwierdzone punktowo w dawnych dealach, +3600 obecnie w EA. Trzeba osobno potwierdzić świeże raw ticki względem UTC po otwarciu oraz uzyskać historyczną politykę/dowody DST. Nie rozciągać punktowego dowodu na sześć miesięcy. Akceptowane segmenty UTC pozostają puste.',
'3. Sesje/świece: wyznaczanie H1/H4/D1 jest przetestowane dla jawnych granic i DST, ale nie potwierdzono historycznych sesji tego brokera. Brak polityki oznacza brak certyfikacji świec i dziennej bazy.',
'4. Model pozycji: następny etap to kontrolowane testy różnicowe SL/TP, TP1, BE, trailing, freeze, spread, limitów dziennych i rozłączeń względem zamrożonego rzeczywistego Position Managera. Obecne funkcje nie są jego kompletnym zamiennikiem.',
'5. Koszty: specyfikacja bieżąca nie zastępuje historycznej. Brak potwierdzonego FX, prowizji, swapu/rollover i wykonania zleceń. Nie przyjmujemy automatycznie zerowych kosztów ani starego przelicznika.',
'6. Briefing: kompletne przyszłe archiwum SHADOW pozostaje kolejnym etapem. Obecny etap nie wdraża automatycznego pobierania ChatGPT ani autoryzacji. W audycie istnieje szkic formatu; docelowy zapis wymaga zachowania pełnej treści, czasu publikacji i pierwszego odbioru, plan_id, poziomów i NO TRADE/HOLD/CANCEL. Nie traktować uciętego archiwum jako kompletnego planu.',
'Nie optymalizowano parametrów. Ujemny wynik poprawnego modelu będzie prawidłowym wynikiem badania. Po przedstawieniu tego etapu można kontynuować kontrolowane testy zgodności, a dopiero po ich przejściu przeliczyć niezmienione strategie.',
'## Wersjonowanie i odtworzenie',
'`config.v1.json` określa zakres próbek i puste listy zweryfikowanych mapowań/kontraktów. `bounded_manifest.v2.json` opisuje ograniczenia pobierania. `stage1_manifest.json` przechowuje SHA-256 kodu, konfiguracji, dowodów i raportów. `production_integrity.json` sprawdza niezmienność kodu/config DEMO, a nie naturalnie aktualizowanych logów/baseline.',
'Odtworzenie offline: uruchom `analyze_stage1.py`, następnie `report_stage1.py` i testy. Korzysta z kopii ticków w `evidence/` oraz zachowanych artefaktów poprzedniego audytu i manifestu H1. Nie uruchamiaj starego `collect.py` do ponownej kolekcji — pierwsza próba nie miała limitu pojedynczego zapytania. Nowe kolekcje powinny mieć nowy numer wersji i nadzór procesu.',
'Nie wysłano zleceń. Nie zmieniono Execution Engine, Risk Managera, ustawień terminala, czasu Windows ani konfiguracji działającego DEMO.'])
integrity=[]
for r in read(A/'inputs/protected_hashes.json'):
 integrity.append({**r,'unchanged':hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256']})
if not all(r['unchanged'] for r in integrity):raise RuntimeError('Protected file differs; inspect before claiming no changes')
(A/'production_integrity.json').write_text(json.dumps(integrity,indent=2),encoding='utf-8')
report('README.md',['# TradingAI — weryfikacja ticków, etap 1','371 167 ticków; 30 testów prymitywów. Model ceny rozdziela Last/Bid/Ask. Zmienny offset czasu potwierdzony w eksporcie EA, pełne mapowanie ticków do UTC nadal nierozstrzygnięte. Pełnego backtestu nie uruchomiono.',
'- [Dostępność danych](DATA_COVERAGE.md)\n- [Model cen i czasu](PRICE_MODEL.md)\n- [Zgodność wykonania — status](EXECUTION_PARITY.md)\n- [Porównanie — przed pełnym backtestem](BACKTEST_COMPARISON.md)\n- [Ograniczenia i dalsze kroki](REMAINING_LIMITATIONS.md)'])
files=[p for p in A.rglob('*') if p.is_file() and '__pycache__' not in str(p) and p.name!='stage1_manifest.json']
(A/'stage1_manifest.json').write_text(json.dumps({'stage':'DATA_PRICE_TIME_VERIFICATION','at':now,'orders_sent':0,'full_backtest_run':False,'strategy_optimized':False,'python':sys.version,'files':[{'path':str(p.relative_to(A)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in files]},indent=2),encoding='utf-8')
print('Five stage reports generated; code/config unchanged; full replay not run.')
