# Nowe dane: dostępność i ograniczenia, 28.10.2026

Małe, jednorazowe pobrania; bez kupowania, kont i masowych archiwów. Ta runda
uzupełnia `../edge_program/DATA_SOURCES.md`, gdzie są broker, konsensus, licencje
i cenniki. Tabela poniżej dotyczy nowych konkretnych pytań, nie katalogu API.

## Cboe: rzeczywiste pobranie i pierwsze obliczenia

[Oficjalny wykaz plików](https://www.cboe.com/tradable-products/vix/vix-historical-data/)
udostępnia codziennie aktualizowane CSV. Pobrano po jednej kopii pięciu plików,
łącznie966122 bajty. Każdy ma mniej niż0,5MB. Bez paginacji i bez danych opcyjnych
tickowych. Zakresy poniżej wynikają z odczytu plików, nie reklamy produktu.

| Indeks | Historia pobranej kopii | Wiersze | Pola | Pytanie |
|---|---|---:|---|---|
| [VIX](https://cdn-api.cboe.com/api/global/us_indices/daily_prices/VIX_History.csv) | 02.01.1990–27.10.2026 | 9303 | DATE,OPEN,HIGH,LOW,CLOSE | Filtr napięcia dla US500/US100 |
| [VIX9D](https://cdn-api.cboe.com/api/global/us_indices/daily_prices/VIX9D_History.csv) | 04.01.2011–27.10.2026 | 3977 | DATE,VIX9D | Ryzyko bliskiego terminu względem VIX |
| [VVIX](https://cdn-api.cboe.com/api/global/us_indices/daily_prices/VVIX_History.csv) | 06.03.2006–27.10.2026 | 5134 | DATE,VVIX | Potencjalna zmienność samego ryzyka; brak dodatkowej próby, żeby nie mnożyć filtrów |
| [OVX](https://cdn-api.cboe.com/api/global/us_indices/daily_prices/OVX_History.csv) | 18.09.2009–27.10.2026 | 4301 | DATE,OVX | Czy wzrost oczekiwanej vol wzmacnia trend OIL |
| [GVZ](https://cdn-api.cboe.com/api/global/us_indices/daily_prices/GVZ_History.csv) | 18.09.2009–27.10.2026 | 4301 | DATE,GVZ | Analogiczne pytanie GOLD |

Daty posortowane i unikalne, wartości skończone i dodatnie. To nie dowód
kompletności sesji ani oryginalnych vintage. Historyczny start może zawierać
backfill; publikacja każdego historycznego wiersza nie jest udokumentowana.
HTTP Last-Modified odnosi się do całej dzisiejszej kopii.

[Metodologia indeksów](https://cdn.cboe.com/api/global/us_indices/governance/Volatility_Index_Methodology_Selected_Broad_Based_Index_Equity_and_ETF_Volatility_Indices.pdf)
i [OVX dashboard](https://www.cboe.com/us/indices/dashboard/ovx/) opisują miary
opcyjne. OVX to opcje USO, GVZ opcje GLD; nie IV naszego CFD ani spread jego
wykonania. VIX9D/VIX porównuje dwa horyzonty implikowanej zmienności, nie
cenową krzywą kontraktów VIX futures.

[Warunki Cboe](https://www.cboe.com/terms): publiczny odczyt/kopia do osobistego
niekomercyjnego wykorzystania, zachowanie oznaczeń; inne zastosowania i
redystrybucja wymagają odpowiednich praw. Ta praca jest lokalnym badaniem,
bez publikacji raw. Nie ustanawiamy licencji na automatyczny produkt komercyjny
ani nie budujemy nowego indeksu. Produkcyjne zastosowanie wymaga wyjaśnienia
praw. Brak gwarancji dokładności/aktualności. Koszt tego pobrania0 USD.

## CFTC COT: dane pozycji, nie data dostępności

[Archiwum](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalCompressed/index.htm)
zawiera Legacy futures-only od1986 (przed30.09.1992 nie pełną cotygodniową
historię), combined od1995. Disaggregated/TFF mają roczne archiwa i retrospektywny
plik2006–2016. Zmiana klasyfikacji i backfill muszą być uwzględnione.
Producer/merchant, swap dealer, managed money i other reportables dotyczą
disaggregated; dealer, asset manager i leveraged funds to TFF. Nie mieszać
tych grup ani futures-only z futures-and-options.

[PRE User Guide](https://publicreporting.cftc.gov/stories/s/COT-Help/p2fg-u73y/)
opisuje filtrowanie dat/kontraktów i API/CSV. Próbki po1rekordzie:
[disaggregated](https://publicreporting.cftc.gov/resource/72hh-3qpy.json?%24limit=1)
i [TFF](https://publicreporting.cftc.gov/resource/gpe5-46if.json?%24limit=1).
Lokalnie pierwsza próba zakończyła się timeoutem TLS, druga błędem walidacji
certyfikatu. Nie wyłączono TLS i nie obchodzono dostępu. **Nie uzyskano lokalnej
próbki pozycji**, więc nie wykonano testu COT. Istnienie API potwierdza źródło,
ale nie działającą lokalną ścieżkę pobierania w tej konfiguracji.

[Harmonogram](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm):
zwykle piątek15:30 America/New_York, pozycje z wtorku, wyjątki świąteczne.
To harmonogram planowany, nie pełna historia opóźnień, korekt i pierwszego
odbioru. Nie dodajemy po prostu3dni do każdej daty pozycji.
[Federalny katalog](https://catalog.data.gov/dataset/commitments-of-traders)
oznacza zbiór jako publiczny do pobierania i Open Government; bez zakupu.
Zachować atrybucję i wersję pobrania. Gold/WTI futures są proxy GOLD/OIL;
finansowe futures odpowiadają indeksom i6E/6B, a nie wszystkim OTC. Nie
potwierdzono bezpośredniego, dostatecznie płynnego odpowiednika EURPLN.

## FRED/ALFRED: nowe zmienne, jawne opóźnienia

| Seria | Pytanie i częstotliwość | Co blokuje as-of |
|---|---|---|
| [DFII10](https://fred.stlouisfed.org/series/DFII10) | Dzienne realne10Y, koszt alternatywny GOLD | Obserwacja i aktualizacja H15 to inne daty; brak pobranego tu pełnego vintage |
| [DGS10](https://fred.stlouisfed.org/series/DGS10) | Dzienne nominalne10Y, dyskonto indeksów | Znacznik publikacji i zmiany metodologii; nie cena wykonalnej obligacji |
| [T10YIE](https://fred.stlouisfed.org/series/T10YIE) | Dzienne breakeven z nominalnej i realnej rentowności | To także premie ryzyka/płynności, nie czysta ankietowa prognoza CPI |
| [DFF](https://fred.stlouisfed.org/series/DFF) | Dzienna efektywna stopa Fed | Zrealizowana stopa, nie surprise decyzji ani oczekiwana ścieżka |
| [DTWEXBGS](https://fred.stlouisfed.org/series/DTWEXBGS) | Szeroki USD; kontrola przy GOLD/FX | Dzienne obserwacje publikowane w innym rytmie; nie ICE DXY |
| [NFCI](https://fred.stlouisfed.org/series/NFCI) | Tygodniowe warunki finansowe, indeksy/risk-off EURPLN | Tydzień kończący się23.10 aktualizowano28.10; użycie23.10 byłoby wyciekiem |

Zakresy są wieloletnie, ale dokładnego początku dostępnych **vintage** każdej
z tych serii nie potwierdzono. Nie zastępujemy go początkiem obserwacji.
[ALFRED realtime](https://fred.stlouisfed.org/docs/api/fred/realtime_period.html)
i [vintage dates](https://fred.stlouisfed.org/docs/api/fred/series_vintagedates.html)
pozwalają wybierać wersje dzienne; dokładniejszy czas wymaga release metadata.
API jest bezpłatne z kluczem; nie rejestrowano konta. Prawa zależne od wydawcy
serii, część stron ma oznaczenie copyright. Retencję/redystrybucję ocenić per seria.

Jedno małe, ograniczone datami zapytanie graph.csv dla6serii z2026 dało HTTP404.
Nie oznacza to niedostępności samych serii. Nie wykorzystano obecnych wartości
z HTML do udawania historycznego testu real yields. Kod pobrania i błąd zapisano
lokalnie; można użyć oficjalnego API z już legalnie posiadanym kluczem w kolejnej
próbie, bez kupowania subskrypcji.

## EIA i dodatkowe źródła z konkretnym pytaniem

[WPSR](https://www.eia.gov/petroleum/supply/weekly/) zawiera crude, gasoline,
distillates, produkcję, import i bilans; CSV/XLS/JSON, tygodniowo. Otwarty
[JSON crude](https://ir.eia.gov/wpsr/psw00.json) miał release28.10.2026 i bieżącą
historię kroczącą2020–2026. To aktualny wyciąg, nie dowód first-print wszystkich
tygodni. [Datowane archiwum](https://www.eia.gov/petroleum/supply/weekly/archive/)
jest właściwym miejscem do odtworzenia publikacji; kompletność i errata trzeba
sprawdzić dla wybranego okna. Brak konsensusu; różnica poziomów to zmiana zapasów,
nie surprise. Odczyt bezpłatny, respektować politykę automatycznego pobierania,
nie publikować tymczasowych podpisanych URL. Test reakcji wymaga jeszcze
ścisłego UTC, Bid/Ask i momentu odbioru. Nie wykonano fikcyjnego P&L EIA.

[NBP API](https://api.nbp.pl/en.html): potwierdzony mały odczyt5referencji EUR,
historia FX od2002; do kontroli EURPLN, nie wykonania. [ECB API](https://data.ecb.europa.eu/help/api/data):
SDMX i wersje serii; publiczne stopy/€STR nie zastępują historycznych OIS.
Szczegóły retencji, ceny0 i dat są w poprzednim raporcie źródeł.

[GPR autorów](https://www.matteoiacoviello.com/gpr.htm),
[pierwotna praca Fed](https://www.federalreserve.gov/econres/ifdp/files/ifdp1222r1.pdf):
indeks oparty o prasę, nowsza seria od1985, historyczna od1900, warianty dzienne
i miesięczne. Pytanie: risk-off GOLD/EURPLN ponad cenę/USD/vol. Narzędzie web
nie odczytało strony z powodu rozmiaru>4MiB; nie pobierano dużego archiwum.
Publiczna dostępność kodu nie dowodzi kompletnych first-available vintage
ani praw do redystrybucji korpusu gazet. Bez tych danych nie ma testu as-of.

## TrueFX i Dukascopy

[TrueFX](https://www.truefx.com/) obecnie opisuje16+par, tick top-of-book,
ms Bid/Offer oraz orientacyjne ceny agregowane. Strona pokazuje plany
streamingu Professional4950 USD/mies. i Institutional7450 USD/mies.; **nie
jest to potwierdzona cena historycznego archiwum**. Nie potwierdzono aktualnie
bezpłatnego eksportu bez logowania, daty początku i licencji retencji. Dawnych
porad o „free od2009” nie traktujemy jako aktualnej umowy. Brak potwierdzenia
EURPLN, indeksów i OIL. Niczego nie kupiono.

[Dukascopy history](https://www.dukascopy.com/swiss/english/marketwatch/historical/)
oraz JForex pozwalają na wybór instrumentu/zakresu; dokładne zakresy i prawa
w poprzednim raporcie pozostają niepotwierdzone dla każdego symbolu. Nie
pobrano z niego ticków w tej rundzie, więc **różnic cen feed-vs-TMS nie
policzono**. Zestawienie możliwości nie jest liczbowym porównaniem jakości.

Wniosek zakupowy: dane Cboe i COT można najpierw oceniać bez subskrypcji.
Nie ma podstaw, by kupować dane cenowe tylko dlatego, że jedno żądanie MT5
się zawiesiło. Braki prawidłowej osi czasu/kosztu nie znikają po zmianie dostawcy.
