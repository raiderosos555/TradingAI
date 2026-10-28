# Dostęp do dłuższej historii — 29.10.2026

**Odblokowano wieloletnie dane COT i referencyjne ceny FX. Nie potwierdzono
pięciu lat wykonalnej historii D1/H1/Bid/Ask u TMS.** Brak odpowiedzi API
nie jest dowodem braku danych na serwerze.

## MT5: nowe ustalenia bez ingerencji w DEMO

Odczytano lokalne ustawienia, inwentarz cache i dzienniki. `MaxBars=100000`.
Taki limit nominalnie wystarcza na pięć lat H1/D1, ale sam nie gwarantuje
dostępności danych. Nie zmieniono limitu ani konfiguracji terminala.

| Rynek | Lata plików cache właściwego symbolu kontraktu | Co to potwierdza |
|---|---|---|
| GOLD | 2017–2026 | istnieją pliki, wcześniejsza sonda zwróciła H1 z 2024 |
| US500 | 2022–2026 | istnieją pliki; wcześniejsza sonda H1 2024 przekroczyła 15 s |
| US100 | 2025–2026 | istnienie cache, nie początek historii serwera |
| OIL (WTI) | 2025–2026 | jak wyżej; nie mieszamy z Brent |
| EURUSD | 2025–2026 | właściwy kontrakt; pliki innego symbolu od 2024 nie są zamiennikiem |
| GBPUSD | 2025–2026 | jak wyżej |
| EURPLN | 2025–2026 | istnienie cache |

53 pliki HCC łącznie obejmują również inne symbole i bazę Default; nie utożsamiamy
ich z siedmioma kontraktami DEMO. Nie dekodowano binarnego HCC według zgadywanego
formatu i nie wyliczono z niego sztucznych świec. Nagłówek roku w nazwie pliku
nie dowodzi pełnych sesji, zgodności timestampów ani braku luk.

**Timeouty:** udokumentowany objaw to niedokończone wywołanie synchroniczne.
`initialize(timeout=...)` nie ustanawia limitu kolejnego `copy_rates_range`.
[MetaQuotes](https://www.mql5.com/en/docs/series/copyrates) opisuje pobieranie
i budowę brakujących szeregów przez terminal; zakończenie wywołania klienta
nie musi zatrzymać synchronizacji. Lokalny cache GOLD obejmuje starsze lata,
więc hipoteza „serwer ma tylko 6 miesięcy” jest nieuprawniona. Dzienniki nie
zawierają jednoznacznej przyczyny poprzednich timeoutów. Nie rozstrzygnięto,
czy dominowało pobieranie, budowa szeregu, IPC czy opóźnienie serwera.

Nie wysłano w tej rundzie kolejnych odległych zapytań do aktywnego terminala:
limit dwóch zwracanych świec nie ogranicza jego wewnętrznego pobierania.
To konkretna przeszkoda w spełnieniu jednocześnie żądania sond i zakazu
obciążania aktywnego DEMO. Nie przedstawiamy niesprawdzonej historii jako odzyskanej.

Minimalne bezpieczne środowisko: oddzielny katalog instalacji i danych MT5,
już uruchomiony, ręcznie zalogowany do właściwego serwera w trybie odczytu,
bez EA/DLL i uprawnień handlowych. [MetaQuotes dopuszcza odrębne kopie](https://www.metatrader5.com/en/terminal/help/start_advanced/start).
Nie kopiujemy haseł/profili aktywnego terminala. Przygotowano `isolated_mt5_probe.py`:
daty 15.01.2020, 15.01.2021, 16.01.2023 × 7 rynków × D1/H1, maksymalnie dwie
świece na odpowiedź, 10 s na proces klienta, stop po pierwszym błędzie.
Skrypt odrzuca aktywny terminal i nie uruchamia nowego. **Sond w odrębnym
terminalu jeszcze nie wykonano — nie ma potwierdzonej, uwierzytelnionej sesji badawczej.**

## Cena, UTC, sesje i rollover

Wcześniejsze archiwa nadal mają `chart_mode=LAST` dla wszystkich siedmiu rynków.
Nie stają się Bid/Ask wskutek zmiany interwału. Historyczne spready, prowizje,
finansowanie, konwersje i rollover pozostają niekompletne. Dokumentacja Python
[deklaruje UTC](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py),
ale nie zastępuje lokalnego dowodu mapowania surowych czasów tego serwera ani
historycznych zmian DST. Zachowujemy poprzednie ograniczenia tick_validation.
Nie zmieniono czasu działającego DEMO. Pełności sesji D1/H1 i rollover za pięć
lat nie zweryfikowano, ponieważ takich wyeksportowanych szeregów nie mamy.

## Alternatywa faktycznie pobrana

Fed H.10: [EURUSD](https://www.federalreserve.gov/releases/h10/hist/dat00_eu.htm)
i [GBPUSD](https://www.federalreserve.gov/releases/h10/hist/dat00_uk.htm).
Pełne strony zawierają również daty poza zakresem; analiza twardo wybiera
2010–2025. Referencyjna obserwacja to noon buying rate w Nowym Jorku, USD
za jednostkę waluty. Brak futures rollover, ale brak też brokerowych stron
rynku i finansowania. Nie odwracamy GBPUSD ani EURUSD. Braki ND pozostają brakami.
Publikacja H.10 jest tygodniowa, poniedziałek 16:15 Eastern; data obserwacji
nie oznacza daty publikacji. Źródło: [opis H.10](https://www.federalreserve.gov/releases/h10/hist/).
Przy mapowaniu czasu USA trzeba stosować America/New_York, nie stałe UTC−5.

To legalny, bezpłatny materiał do zbadania związku COT–FX, a nie wykonania CFD.
[Fed wymaga podania źródła dla public-domain danych](https://www.federalreserve.gov/disclaimer.htm).
W obecnym programie DDP [nie ma danych przed rewizjami](https://www.federalreserve.gov/datadownload/help/).
Dłuższe ceny GOLD/OIL/indeksów nadal wymagają uporządkowanego feedu futures:
datowane kontrakty, rozliczenie, harmonogram rolowania i jednostki; ciągły
wykres skorygowany wstecz nie będzie automatycznie wiarygodnym szeregiem zysków.
EURPLN nie ma tu bezpośredniego COT; nie zastępujemy go samym Euro FX.

## FRED/ALFRED: konkretnie odblokowany endpoint, brak klucza

Poprzedni 404 pochodził z `fred.stlouisfed.org/graph/graph.csv`, a nie oficjalnego
API obserwacji. W nowej próbie pojedyncza seria na endpointcie wykresu zakończyła
się resetem połączenia. **Nie udowodniono przyczyny poprzedniego 404** i nie
przypisujemy go brakowi klucza do API — to różne interfejsy.

`https://api.stlouisfed.org/fred/series/observations` działa: HTTP400 i jawny
błąd `Variable api_key is not set`. Nie znaleziono FRED_API_KEY/ALFRED_API_KEY
w środowisku procesu, User, Machine ani `.env*` katalogu projektu.
Nie przeszukiwano magazynów haseł i nie zakładano konta.

Najmniejszy krok użytkownika: uzyskać/użyć własnego klucza według
[oficjalnej instrukcji](https://fred.stlouisfed.org/docs/api/api_key.html), zapisać
go lokalnie jako FRED_API_KEY (bez wysyłania w czacie/Git). Wtedy mała próbka:
series_id=DFII10, observation_start=2024-01-02, observation_end=2024-01-05,
realtime_start=2024-01-02, realtime_end=2024-01-31, output_type=3, limit=100,
file_type=json. Parametry i API key wymagane przez [API](https://fred.stlouisfed.org/docs/api/fred/series_observations.html).
Daty vintage są dzienne, nie udowadniają godziny pierwszego odbioru.
Test vintage pozostaje BLOCKED; nie uruchomiono drugiego eksperymentu real yields.
