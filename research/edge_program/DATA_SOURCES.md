# Źródła danych — stan sprawdzenia 28.10.2026

Rozróżniamy dokumentację dostawcy, odpowiedź API i zwalidowany zbiór do replay.
Żaden katalog ani cennik nie stanowi dowodu kompletności historycznych danych.
Ceny w USD, przed ewentualnym podatkiem; nie kupiono usług, nie utworzono kont
i nie pobrano masowych zbiorów. Surowe odpowiedzi i dane rachunku pozostają lokalnie.

## 1. Najpierw MT5 i rzeczywisty broker

Odczyt terminala potwierdził OANDA TMS Brokers S.A. Nie utożsamiamy jego feedu
z inną ofertą OANDA ani API v20. Istniejące archiwa wszystkich siedmiu kontraktów
mają chart_mode=LAST. H4/D1 wystarczają do eksploracji opisanej w wynikach,
ale nie do rekonstrukcji historycznego Bid/Ask. Nie zastępujemy zerowych kwotowań
starymi cenami bez dowodu ich ważności.

| Źródło / adres | Historia, pola, czas i jakość | Koszt / prawa / ograniczenie |
|---|---|---|
| MetaQuotes [copy_ticks_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py), [copy_ticks_from](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksfrom_py) | Bid, Ask, Last, volume, time_msc, flags; INFO rozdziela aktualizacje kwotowań od TRADE. Zakres zależy od serwera; dokumentacja opisuje UTC. Lokalne wcześniejsze rozbieżności wymagają potwierdzenia mapowania, a nie stałego offsetu | W istniejącym dostępie rachunku bez zakupu. Archiwizacja do własnego researchu według umowy brokera; brak potwierdzenia praw do redystrybucji. Nie ma gwarantowanego wieloletniego zakresu |
| MetaQuotes [kalendarz](https://www.mql5.com/en/docs/calendar), [historia wartości](https://www.mql5.com/en/docs/calendar/calendarvaluehistory) | Actual, forecast, previous/revisions. **Czas serwera**, również DST; inny kontrakt czasu niż Python ticks. Historia wartości nie gwarantuje wszystkich wcześniejszych wersji prognoz. Kalendarz nie działa bezpośrednio w testerze — potrzebny zapis | Bez dodatkowego zakupu w obecnym terminalu. Zachować wersje i pierwszy odbiór. Dane kalendarza nie autoryzują zleceń |
| OANDA TMS [archiwum dokumentów](https://www.tms.pl/dokumenty) | Datowane specyfikacje, opłaty, swapy; widoczne wersje specyfikacji m.in. 2019/2022–2026, opłat 2021–2026; zakres zależy od produktu. Etykieta strony nie zawsze zgadza się z datą obowiązywania PDF | Publiczny odczyt 0 USD. Do zastosowania trzeba przyporządkować konkretny produkt, symbol, datę i wzór naliczania; nie potwierdzono kompletności wszystkich dni ani licencji masowego kopiowania |
| [Specyfikacja TMS Connect 30.01.2026](https://www.tms.pl/sites/default/files/documents/30-01-2026/sif_tms_connect_30.01.2026.pdf) | 70 stron; instrument bazowy, mnożnik, krok, sesje. OILWTI.pro jest oparty o futures WTI NYMEX. Archiwalnego kontraktu nie przenosić automatycznie na dzisiejszy symbol | 0 USD odczyt. Pozwala odtworzyć część zasad, nie spread, slippage ani każdą zmianę specyfikacji |
| [Swapy 19.10.2026](https://www.tms.pl/sites/default/files/document_files/punkty_swapowe_tms_pl_2026.10.19.pdf) | Datowana tabela BUY/SELL; jednostkę i okres naliczania należy łączyć ze specyfikacją. Same procenty nie są kosztem jednej doby | 0 USD odczyt. Należy uwzględnić triple swap, dni wolne, przeliczenie walutowe i faktyczne księgowanie; nie zastosowano jej do wcześniejszych miesięcy |
| TMS [rolowania](https://www.tms.pl/rolowania), OANDA [opis rollover](https://help.oanda.com/eu/pl/faqs/contract-rollover-eu.htm) | Zmiana serii futures i korekta gotówkowa. Obecny kalendarz oraz archiwalne pozycje dokumentów nie dowodzą kompletnej historii wszystkich korekt | 0 USD odczyt; potrzebne daty, kwoty i reguły konkretnego CFD. Back-adjusted futures nie zastępują rozliczenia klienta |
| TMS [GOLD / historyczne spready](https://www.tmsbrokers.com/market-watch/live-quotes/GOLD) | Widok bieżących kwotowań i agregatów spreadu dla krótkich zakresów: dziś, wczoraj, tydzień, miesiąc. Nie potwierdzono publicznego API wieloletniego eksportu ticków | 0 USD podgląd; nie ekstrapolować obecnych spreadów na lata. Brokerowe deklaracje przechowywania ticków nie oznaczają dostępnego klientowi eksportu |

Próba lokalna: zaplanowano najwyżej 70 D1 i 700 ticków dla siedmiu instrumentów
i dwóch dat (2020/2024). Już pierwsze żądanie pięciu D1 sprzed 15.01.2020 nie
zwróciło odpowiedzi przez ponad 180 s. Zatrzymano wyłącznie własne procesy
sondy; nie terminal ani kolektor. **Nie uzyskano dowodu braku historii**.
Nie ponawiano szerokiego pobierania. Najmniejsza ścieżka: potwierdzenie zakresu
eksportu przez brokera i pojedynczy kontrolowany wycinek, poza aktywnym terminalem.

Aktualizacja po nowej instrukcji właściciela: osobna, ograniczona czasowo sonda
range potwierdziła M1 i jednosekundowy Bid/Ask22.10 dla7rynków oraz H1 GOLD
z15.01.2024. US500 H1 z2024 przekroczył deadline15s i zakończył kampanię.
Szczegóły w `../alternative_data_edge/BROKER_HISTORY.md`; najdłuższy zakres
serwera nadal nie został ustalony. Nie wyciągamy wniosku o konieczności zakupu
zewnętrznego feedu na podstawie samego wcześniejszego timeoutu.

## 2. Ceny zewnętrzne — odkrywanie mechanizmu, nie wykonanie TMS

| Dostawca i produkt | Zakres / rozdzielczość / as-of | Cena i licencja / różnica wobec CFD |
|---|---|---|
| Dukascopy [Historical Data](https://www.dukascopy.com/swiss/english/marketwatch/historical/), [JForex history](https://www.dukascopy.com/wiki/en/development/strategy-api/historical-data/) | Ticks Bid/Ask i świece, FX/metale/wybrane CFD. Dokładnego początku dla każdego z 7 symboli nie potwierdzono w oficjalnym eksporcie; nie przyjmujemy jednej daty „od 2003”. API umożliwia zapytania historyczne, lecz zakres wymaga próbki symbol-po-symbolu | Publiczny eksport bez ceny subskrypcji. Warunki retencji/automatyzacji konkretnego produktu trzeba potwierdzić; warunków osobnego XML feedu nie stosować do JForex. Inny LP, spread i rollover niż TMS |
| HistData [FAQ](https://www.histdata.com/f-a-q/) | FX, zakres zależny od pary/pliku. OHLC są Bid; Ask występuje w Generic ASCII tick. Czas **stałe EST bez DST**. Publikowane raporty luk; brak gwarancji jakości | Pobranie bezpłatne. Nie potwierdzono licencji redystrybucji ani pokrycia wszystkich CFD/EURPLN. Nie nadaje się do netto TMS bez mostu kosztowego |
| Databento [GLBX.MDP3](https://databento.com/docs/datasets/glbx-mdp3), [cennik](https://databento.com/pricing/) | CME od VI 2010; MBO od V 2017. GC/ES/NQ/CL, 6E/6B; trades/BBO/MBP-1, OHLC, definicje. ts_event i ts_recv opisują różne zegary. GC nie jest spot GOLD, futures walutowe nie są OTC EURUSD/GBPUSD | Standard **199 USD/mies.**, 16+ lat L0, 1 rok L1, 1 miesiąc L2/L3; starszy L1 płatny usage-based. Historia także bez subskrypcji za GB — dokładny wycinek wymaga kalkulacji. Kredyt 125 USD wymaga konta, nie użyto. Retencja/use-case zgodnie z licencją datasetu; nie publikować raw |
| Tick Data LLC [Forex](https://www.tickdata.com/product/historical-forex-data/), [FAQ](https://www.tickdata.com/forex-faq/forex-data/) | Od 01.05.2008, 2000+ par, 95+ kontrybutorów, ms Bid/Ask, minuty Bid; contributor IDs od VIII 2010. EURPLN i ciągłość wymagają listy pokrycia. Raw/filtered to różne produkty | **Wycena indywidualna, brak zweryfikowanej kwoty**. Umowa na research/retencję. Agregowane OTC nie jest ceną wykonania u brokera; strefę US/Eastern mapować z DST |
| EODHD [plany](https://eodhd.com/pricing), [warunki](https://eodhd.com/financial-apis/terms-conditions) | EOD/intraday zależnie od instrumentu i planu; ceny FX/CFD nie stanowią potwierdzenia executable Bid/Ask. Brak zapewnienia PIT dla rewizji | EOD **19,99**, EOD+Intraday **29,99**, Fundamentals **59,99**, All-in-One **99,99 USD/mies.**; free ograniczone. Prywatne przechowanie/analiza, bez raw redystrybucji; biznes wymaga odpowiedniej licencji. Nie kupować jako historyczne TMS |

Mapowanie docelowe (bez zakładania równoważności kontraktów):

| Rynek | Bezpośrednie źródło wykonania | Źródło mechanizmu / kluczowa różnica |
|---|---|---|
| GOLD | TMS GOLD.pro Bid/Ask + swapy | Dukascopy XAUUSD albo CME GC; spot kontra futures, basis i finansowanie |
| US500 | Właściwy symbol CFD TMS | CME ES albo inny CFD indeksowy; sesja, dividend/carry, seria futures |
| US100 | Właściwy symbol CFD TMS | CME NQ; inna seria i koszt, nie utożsamiać z NASDAQ cash |
| OIL | TMS OILWTI.pro i korekty rollover | CME CL; seria, termin dostawy, baza zapasów i roll |
| EURUSD | TMS EURUSD.pro | Dukascopy/HistData/Tick Data OTC; 6E tylko proxy futures |
| GBPUSD | TMS GBPUSD.pro | Jak FX wyżej; 6B jako proxy, odmienna płynność |
| EURPLN | TMS EURPLN.pro | Dukascopy/Tick Data po weryfikacji pary; NBP tylko kurs referencyjny, nie tick |

## 3. Urzędowe makro, rentowności, waluty i surowce

| Źródło | Historia / zawartość / wersje | Cena, prawa i ograniczenia |
|---|---|---|
| BLS [Employment Situation archive](https://www.bls.gov/bls/news-release/empsit.htm), [archiwa publikacji](https://www.bls.gov/bls/news-release/) | Empsit 1994–2026; odrębne datowane publikacje CPI/NFP, jednostki i rewizje. Pierwszy raport trzeba odróżnić od obecnej serii i późniejszej korekty dokumentu | Bezpłatne oficjalne dane, zachować źródło/wyjątki praw do treści. Brak konsensusu. Planowana godzina nie jest dowodem pierwszego odbioru |
| EIA [WPSR](https://www.eia.gov/petroleum/supply/weekly/), [harmonogram](https://www.eia.gov/petroleum/supply/weekly/schedule.php), [serwis publikacyjny](https://ir.eia.gov/) | Datowane tygodniowe raporty i serie zapasów; dokładna ciągłość first-print archiwum do potwierdzenia, nie utożsamiać z długą historią obecnej serii. Zwykle środa 10:30 America/New_York, wyjątki świąteczne | Bezpłatny odczyt/API; respektować ograniczenia automatycznego pobierania. Brak konsensusu rynkowego. latest PDF może się zmienić; zapisywać datowany artefakt i hash |
| FRED/ALFRED [realtime periods](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html), [vintagedates](https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html) | Serie i vintages, historia zależna od serii; realtime_start/end w dniach. Domyślny widok to obecne dane po rewizjach, nie historyczne as-of | API bez opłaty, klucz wymaga rejestracji; nie zakładano konta. Prawa zależne od pierwotnego wydawcy. Dzień vintage nie rozstrzyga dostępności o 08:30:01 |
| Fed [DFII10](https://fred.stlouisfed.org/series/DFII10), [DTWEXBGS](https://fred.stlouisfed.org/series/DTWEXBGS) | Dzienne realne US10Y i szeroki indeks USD. Początek z metadata przed pobraniem; data obserwacji nie jest datą dostępności. H10 może aktualizować serię dzienną tygodniowo | Bezpłatny odczyt, oznaczone public domain z prośbą o cytowanie. Indeks handlowy USD nie jest ICE DXY; yield nie jest tradowalną ceną obligacji |
| NBP [API](https://api.nbp.pl/en.html), [archiwum stóp](https://nbp.pl/podstawowe-stopy-procentowe-archiwum/) | FX od 02.01.2002, złoto PLN/g od 02.01.2013, maks.93 dni/zapytanie. A=mid, C=referencyjne kupno/sprzedaż. API nie zawiera oczekiwań OIS. Strona stóp przy tej próbie zwróciła 403 | Publiczny API bez klucza/opłaty. Zweryfikowano pobranie pięciu kursów EUR, nie historii tickowej. Prawa do redystrybucji sprawdzić osobno; nie publikujemy raw. Data effectiveDate nie oznacza czasu wykonania |
| ECB [API](https://data.ecb.europa.eu/help/api/data), [datasets](https://data.ecb.europa.eu/data/datasets) | Kursy/stopy/rentowności, zakres per seria. includeHistory=true zwraca wcześniejsze wersje; updatedAfter sam nie jest pełnym PIT. €STR od X2019, T publikowane T+1 o 08:00 CET | Publiczny dostęp; licencja i źródła zewnętrzne per dataset. Zrealizowana €STR i stopa banku nie są krzywą oczekiwań OIS |
| FRBSF [Monetary Policy Surprises](https://www.frbsf.org/research-and-insights/data-and-indicators/monetary-policy-surprises/) | Badawcze szoki z 30-min futures stóp, warianty surowe i ortogonalizowane. Zakres pliku sprawdzić przy pobraniu, nie przenosić zakresu publikacji na aktualny plik | Publiczny plik badawczy z atrybucją; ex-post PCA/oczyszczenie nie jest dostępnym wtedy sygnałem. Nie wolno użyć pełnego 30-min surprise do wejścia po5min |

PLN/EUR OIS: publiczne stopy NBP/EBC nie rozwiązują tego braku. Kandydatem do
historii kwotowanych krzywych jest LSEG (poniżej); dokładne instrumenty PLN,
tenory, interwał i archiwum as-of trzeba uzyskać w specyfikacji oferty.

## 4. Konsensus, pierwsza publikacja i newsy

| Produkt / adres | Co rzeczywiście wiadomo o zakresie | Koszt / prawa / warunek akceptacji |
|---|---|---|
| Trading Economics [Calendar Point-in-Time](https://docs.tradingeconomics.com/economic_calendar/point-in-time/), [pricing](https://tradingeconomics.com/api/pricing.aspx), [terms](https://tradingeconomics.com/terms.aspx) | Dokumentuje oryginalne wartości i Forecast/Actual/Previous/Revised/LastUpdate; przykład z2016 nie gwarantuje początku NFP/CPI/EIA. Pokazany endpoint nie dowodzi wszystkich wcześniejszych vintage prognoz. TEForecast odróżnić od ankietowego Forecast | **Wycena API indywidualna; brak potwierdzonej publicznej kwoty**. Warunki retencji i konkretnego użycia zapisać w ofercie. Wymaga próbki forecast sprzed publikacji z dowodem czasu i first actual; samo pole LastUpdate niewystarczające |
| Econoday [Historical Economic Data](https://www.econoday.com/pdf/Econoday-Historical-Economic-Data-for-Firms-using-FinTech-AI.pdf), [oferta/demo](https://www.econoday.com/request-a-demo/) | Własny panel20 ekonomistów, mediany konsensusu, actual-as-released i revised. Większość USA od2001, wiele globalnych od2003; dostępna lista per event. Broszura odczytana przez wynik wyszukiwania; ponowne bezpośrednie pobranie PDF dało404 | **Indywidualna wycena — kwota niepubliczna, nie zgadujemy**. NFP/CPI i zwłaszcza EIA wymagają potwierdzonej listy. Umowa musi pozwalać zachować vintage do wewnętrznych badań po wygaśnięciu. Nie wysłano zapytania do sprzedawcy |
| FXMacroData [pricing](https://fxmacrodata.com/subscribe), [PIT guide](https://fxmacrodata.com/documentation/point-in-time-backtesting), [licencje](https://fxmacrodata.com/data-sources-and-licensing) | **Brak miesięcznego historycznego konsensusu NFP/CPI na jakimkolwiek planie**. Nowcast Cleveland to prognoza modelowa, SPF ma inny horyzont. Własne zapisane modele wskazanych5 serii US od VIII2026. Rekonstrukcje czasu, capture i first-print mają jawne znaczniki jakości | Individual **50 USD/mies. lub500/rok**, Business250/mies.; trial wymaga płatności i odnawia się — nie uruchomiono. Legalnie pobrane dane można zachować wewnętrznie po anulowaniu, lecz prawa wydawców pozostają. Cena nie rozwiązuje braku konsensusu |
| EODHD [Economic Events](https://eodhd.com/financial-academy/stocks-data-analysis-examples/how-to-get-economic-events-data-with-python) | Kalendarz od2020: actual/estimate/previous. Nie potwierdzono przechowania oryginalnych forecast vintage lub first receipt | Plany cenowe wyżej; uprawnienia tego endpointu trzeba potwierdzić. Nie kupować jako PIT tylko dlatego, że rekord ma estimate |
| LSEG [Economics](https://www.lseg.com/en/data-catalogue/economics), [Reuters Polls w API](https://developers.lseg.com/en/article-catalog/article/retrieve-cross-economic-data-using-data-library) | Ekonomia, poll forecasts, 10tys. serii PIT; start i dostępność zależne od serii. Ogólny długi zakres ekonomii nie jest początkiem consensus PIT. Możliwe rentowności i krzywe rynku stóp | **Wycena i licencja indywidualne**, potrzebne prawa non-display, archiwizacji i dostęp do exact product. Niezweryfikowane dla PLN OIS/per-event EIA; nie deklarujemy kompletności |
| LSEG [Machine Readable News / Tick History](https://www.lseg.com.cn/content/dam/data-analytics/en_us/documents/fact-sheets/machine-readable-news-real-time-optimized-and-tick-history-factsheet.pdf) | MRN analytics od2003, znaczniki ms; Tick History quotes/trades od1996, zakres zależny od venue. Story/version IDs i semantics timestamp wymagają próbki; nie nasz pierwszy receipt | **Wycena indywidualna**, osobne uprawnienia do treści, analityki, retencji i redistribution. Przydatne do news reaction dopiero po kontroli poprawek/duplikatów; nie TMS Bid/Ask |
| GDELT [data](https://gdeltproject.org/data.html) | GDELT2 od2015, aktualizacje co15min; metadane news/event/GKG. Pierwsze zobaczenie przez crawler nie dowodzi pierwszej dostępności informacji na rynku | Bezpłatne dane projektu; prawa do pełnych artykułów osobne. Do katalogowania korpusu; nie szybki intraday surprise ani etykiety sentymentu o gwarantowanej jakości |
| RavenPack [katalog dystrybutora WRDS](https://wrds-www.wharton.upenn.edu/pages/about/data-vendors/ravenpack/) | W tym katalogu historia 01.01.2000–30.09.2026, aktualizacja miesięczna. News analytics, encje/zdarzenia; nie dowodzi chwili dostępności u konkretnego klienta | **Licencja/wycena**, nie bezpłatny download WRDS. Prawa do korpusu, wersji i retencji osobno. Nie budujemy modelu bez deduplikacji i oznaczonego korpusu |

## 5. Sprawdzone małe pobrania, nie tylko katalogi

`acquire_samples.py`: cztery publiczne GET, bez kluczy, retry ani paginacji,
limit1MiB/odpowiedź. Wszystkie HTTP200, łącznie196637 bajtów:

- [USD forecast coverage](https://api.fxmacrodata.com/v1/predictions/coverage/usd):
  NFP i crude_oil_inventories nie mają źródła konsensusu. CPI/core wskazują
  Cleveland od referencji VIII2013 (pierwsza publikacja17.09.2013), ale to
  **nowcast**, a obecność SPF nie oznacza zgodnego miesięcznego celu.
- [USD catalogue](https://api.fxmacrodata.com/v1/data_catalogue/usd): metadane
  długich serii nie poświadczają czasu pierwszej publikacji każdej obserwacji.
- [Jedna obserwacja CPI](https://api.fxmacrodata.com/v1/announcements/usd/inflation?limit=1):
  zapytanie domyślne zwróciło `point_in_time_safe=false`, rekord
  `vintage_status=captured_snapshot`, `is_first_release=false`, czas publikacji
  unverified. W revisions istnieje deklarowana source_vintage first release,
  ale nie zweryfikowano jej samodzielnie z artefaktem BLS. **Odrzucono tę
  odpowiedź jako wejście do ścisłego replay**, nie cały produkt na zawsze.
- [Pięć referencji EUR NBP](https://api.nbp.pl/api/exchangerates/rates/a/eur/last/5/?format=json):
  format i dostęp potwierdzone, nie wykonanie ani test strategii.

Próbki, hashe, czas pobrania, status i ograniczenia zapisano lokalnie w
`private/public-samples-v1/`. Nie wykorzystano nowych obserwacji do selekcji
strategii. Nie ma obecnie kompletnego darmowego zestawu konsensus+first-print+
broker Bid/Ask. Jedna konkretna ścieżka odbioru danych jest w NEXT_EDGE_STEP.md.
