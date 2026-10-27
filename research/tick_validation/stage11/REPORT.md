> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Etap 11 — walidacja jednej doby na siedmiu instrumentach

Raport końcowy: 26.10.2026. Zakres danych: 22.10.2026 00:00–23.10.2026 00:00 w surowych współrzędnych API, **nie potwierdzonym UTC**. Wyłącznie dane eksploracyjne. Etap zakończony jako audyt jakości, nie jako certyfikacja pełnego symulatora.

## Dane i odtworzenie świec

Łącznie **5,401,052 rekordów** w siedmiu dobach instrumentowych, w tym 277 031 wcześniej pobranych ticków EURUSD. Wszystkie 42 czterogodzinne przedziały żądań zostały pokryte odpowiedziami API. To nie jest gwarancja kompletności historii serwera ani ciągłej dostępności cen wykonania.

| Instrument | Ticki | Zgodne świece Last OHLC i tick_volume | Puste przedziały H1 bez Last | Niepoprawne kwotowania Bid/Ask |
|---|---:|---:|---:|---:|
| EURPLN | 94,204 | 31 | 0 | 0 |
| GBPUSD | 432,782 | 31 | 0 | 0 |
| GOLD | 977,204 | 30 | 1 | 1 |
| OIL | 600,008 | 30 | 1 | 0 |
| US500 | 1,393,823 | 30 | 1 | 0 |
| US100 | 1,626,000 | 30 | 1 | 0 |
| EURUSD | 277,031 | 31 | 0 | 0 |

Odtworzono **213 istniejących świec H1/H4/D1**. Cztery dodatkowe przedziały H1 23:00–24:00 dla CFD nie mają świecy referencyjnej ani aktualizacji Last; nie dopisano świec i nie rozciągnięto poprzedniej godziny. Same przerwy w tickach nie dowodzą oficjalnego harmonogramu sesji.

Wszystkie 213 świec ma OHLC różne od agregacji Bid. Zgodność Last nie dowodzi kompletności wszystkich aktualizacji Bid/Ask. Największe wewnętrzne przerwy między tickami i pierwsze/ostatnie czasy są w JSON; te największe przerwy nie obejmują odcinków przed pierwszym i po ostatnim ticku doby. Nie utożsamiamy udanego całodobowego żądania z całodobową możliwością wykonania.

Każda z siedmiu wcześniej pobranych godzin raw 15:00–16:00 jest zgodna z nową dobą rekord po rekordzie, z zachowaniem wszystkich ośmiu pól oraz kolejności dostawcy. Dodatkowe rekordy o identycznej milisekundzie nie zostały usunięte. Nie wolno sumować całej nowej doby z dawnymi próbkami bez uwzględnienia nakładania.

## Niepoprawne kwotowania

Znaleziono 1 niepoprawny rekord kwotowania: pierwszy tick GOLD o raw 00:05:00.027 ma Bid=Ask=0, Last=4139.44. Następny rekord ma poprawne kwotowanie przy identycznym czasie milisekundowym. Dlatego granice niedostępności zachowują również indeks dostawcy, a nie tylko czas. Szczegóły zapisano w `comparison.json` → `quote_health`. Last jest analizowany niezależnie od Bid/Ask: prawidłowy Last może tworzyć świecę, ale zerowy Bid/Ask nie może realizować zlecenia. Nie ma forward-fill ani wymyślonej ceny.

Pierwotny ścisły walidator poprawnie zatrzymał się na takim rekordzie. Nowy `quality.py` służy wyłącznie diagnostyce: zachowuje anomalię, oznacza niepełność OHLC Bid/Ask i rozdziela ją od zgodnego Last. Ścisła funkcja ceny wykonania nadal odrzuca zerowy Bid/Ask — potwierdza to test. **Nie wdrożono jeszcze tej klasyfikacji jako pełnego mechanizmu wstrzymania i wznowienia wykonania w wieloinstrumentowym replay.**

## Pobieranie i powtarzalność

Pierwsze pobranie GOLD raw 16:00–20:00 dostało 232 990 ticków, lecz przekroczyło 40 s podczas lokalnego zapisu; nie był to brak odpowiedzi brokera. Pierwsza próba, częściowy plik i fazy pozostały zachowane i nie są źródłem analizy. Szybszy, osobny worker zapisuje ten sam JSON jednorazowo z gzip poziomu 1. Na 210 744 rzeczywistych rekordach potwierdzono identyczne bajty po rozpakowaniu. Ponowiono tylko niedokończone przedziały. Limity: 40 s na proces, pierwotnie 600 s na serię, uzupełnienie 300 s przed rozpoczęciem kolejnego bloku.

`config.json` oraz `retry_config.json` mają wersje 1 i 2. `resolved_collection.json` wskazuje wybrane kompletne pliki i hashe pierwotnej próby. Źródła, kod, raporty i wyniki są objęte manifestem SHA-256. Żadnej strategii nie strojono i nie wysyłano zleceń z narzędzi badawczych.

**14 testów** obejmuje granice H1, brakujące i puste zakresy, prawidłowy Last przy niepoprawnym Bid/Ask, odrzucenie wykonania, odzyskanie kwotowania w tej samej milisekundzie z zachowaniem kolejności, brak odzyskania i błędny Last. Sprawdzono także manifesty etapów 1–10 i chroniony kod/konfiguracje DEMO.

```powershell
# Z C:\TradingAI; offline:
.\.venv\Scripts\python.exe research/tick_validation/stage11/verify.py
# Pełne powtórzenie obliczeń na 5,4 mln zapisanych ticków, bez brokera:
.\.venv\Scripts\python.exe research/tick_validation/stage11/verify.py --recompute
```

## Decyzja

**GO dla zamknięcia walidacji danych etapu 11 i użycia zbioru do diagnostyki. NO-GO dla wiarygodnego wyniku netto strategii na tym etapie.** Jedna doba nie potwierdza przewagi. Brakuje zatwierdzonego mapowania tej doby na UTC, historycznych kosztów/FX i zintegrowanego replay z pełną semantyką luk, portfela, Risk Managera i stanu pozycji na końcu próby. Szczegółowa odpowiedź na pięć pytań znajduje się w `../STATUS_REPORT.md`.
