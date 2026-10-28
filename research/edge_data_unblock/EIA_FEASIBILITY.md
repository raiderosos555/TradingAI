# EIA + OIL: mały plan gotowy do zatwierdzenia

**GO dla dostępności datowanych tabel EIA; NO-GO dla certyfikowanego replay
12 wydarzeń.** Brakuje potwierdzenia pierwszej dostępności oraz odpowiednich
kwotowań OIL z poprawną osią UTC. Nie pobrano kampanii tickowej.

## Faktycznie sprawdzone

[Archiwum EIA](https://www.eia.gov/petroleum/supply/weekly/archive/) zawiera
12 kolejnych publikacji od marca 2026, bez wybierania po reakcji rynku:

| Data wydania | Wielkość table1.csv, B | Planowana godzina UTC |
|---|---:|---|
| 04.03.2026 | 6559 | 15:30 |
| 11.03.2026 | 6532 | 14:30 |
| 18.03.2026 | 6550 | 14:30 |
| 25.03.2026 | 6554 | 14:30 |
| 01.04.2026 | 6558 | 14:30 |
| 08.04.2026 | 6541 | 14:30 |
| 15.04.2026 | 6587 | 14:30 |
| 22.04.2026 | 6566 | 14:30 |
| 29.04.2026 | 6590 | 14:30 |
| 06.05.2026 | 6589 | 14:30 |
| 13.05.2026 | 6568 | 14:30 |
| 20.05.2026 | 6579 | 14:30 |

Wszystkie 12 HEAD: HTTP200; Content-Length łącznie **78 773 B**. Pobrano tylko
jedną treść CSV (6559 B). W [tabeli 04.03](https://www.eia.gov/petroleum/supply/weekly/archive/2026/2026_03_04/csv/table1.csv)
kolumny obejmują tydzień 27.02 i 20.02 oraz różnicę; crude excluding SPR:
439,279 vs435,804 mln baryłek, różnica +3,475 mln. To odczyt archiwalnego pliku,
nie jeszcze udowodniony pierwszy komunikat. CSV wymaga cp1252, nie bezwarunkowego UTF-8.

Planowane godziny pochodzą ze [standardu EIA](https://www.eia.gov/petroleum/supply/weekly/schedule.php)
10:30 America/New_York. Zmiana DST w USA powoduje zmianę UTC między04.03 i11.03.
**Harmonogram nie dowodzi faktycznej godziny publikacji.** HTTP Last-Modified
przeważnie wskazuje poprzedni dzień (np.03.03 21:22:47 UTC dla04.03), a zatem
nie jest momentem udostępnienia inwestorom. Nie używać go jako entry timestamp.

Datowany URL umożliwia rozdzielenie wydań od obecnego, aktualizowanego szeregu.
Nie gwarantuje jednak niezmienności pliku po korekcie. Wymagany jest dowód
pierwszej wersji, lista errata i faktyczny published_at/received_at, albo jawna
kategoria „as-of nieweryfikowalne”. Nie wymyślono preconsensus.

## OIL Bid/Ask: obecny stan

Wcześniej potwierdzono jedną sekundę poprawnych Bid/Ask OIL z22.10.2026,
30 rekordów. Nie potwierdza to zakresu marzec–maj. Cache świec WTI z2025/2026
nie dowodzi ticków ani ich historycznej dostępności. W tej rundzie nie
wywołano starych zakresów w aktywnym terminalu, nie podmieniono zerowych
stron ostatnią ceną i nie użyto zewnętrznego feedu jako wykonania TMS.

## Zakres proponowanej zgody — jeszcze niewykonany

1. Najpierw jedna próbka **1 sekundy przy każdym z12 wydarzeń**, wyłącznie
   w oddzielnym terminalu badawczym; maks.10 s procesu klienta na zapytanie,
   przerwanie po pierwszym timeout/niezgodnym czasie. Wykazać UTC na podstawie
   dowodów brokera, nie dopasowania największego skoku do zegara EIA.
2. Tylko po sukcesie jakości:12 okien [-10,+60]min, porcje do5min, maksymalnie
   **512 MiB łącznie /64 MiB na wydarzenie**; zatrzymać przed następną porcją
   po przekroczeniu budżetu. MT5 może pobierać wewnętrznie więcej niż zwraca —
   dlatego izolacja jest obowiązkowa. Żadnych zmian w aktywnym DEMO.
3. Tabele EIA wszystkich12 dat (około79 kB), potrzebne datowane komunikaty,
   errata i metadane: oddzielny budżet do5 MB. Bez masowego pobierania całych lat.
4. Zachować Bid/Ask/Last/time_msc/flags, rzeczywistą kolejność, przerwy,
   kontrakt, spready i koszty. Dowód ważności każdej strony i czas informacji
   muszą poprzedzać decyzję. Nie wolno domniemywać ich z późniejszego wykresu.

Orientacyjnie 30 ticków/s ×50 400 s ×60 B/rekord = **90,72 MB** przed formatem
i metadanymi. To przykład z wcześniejszej jednej sekundy, nie prognoza szczytu
newsowego ani gwarancja limitu. Wydarzenia mogą generować znacznie więcej danych.
Koszt EIA0 USD, istniejący dostęp TMS bez nowej subskrypcji; nie jest to wycena
kosztów tradingu. Suma512 MiB jest limitem do zatwierdzenia, nie pobranym wolumenem.

## Odbiór próby i następne badanie

12 wydarzeń ma zweryfikować pozyskanie i synchronizację, a nie przewagę. Rekordy
bez first print/UTC/wystarczających Bid/Ask są nieweryfikowalne — nie odrzucamy
ich tylko dlatego, że dały niekorzystny ruch. W raporcie pokażemy wszystkie12,
powody braków i rzeczywisty zakres pokrycia. Wymagamy kompletnych dowodów dla
każdego wydarzenia, zanim zestaw nazwiemy gotowym do ścisłego replay.

Po odbiorze osobno zamrozić test zgodny z wcześniejszym NEXT_STEP: czy znak
zmiany zapasów dodaje informację ponad pierwszy5-minutowy ruch OIL, przy decyzji
nie wcześniej niż5min po potwierdzonym odbiorze i wyjściu po30min. To kontekst
actual, **nie surprise bez historycznego konsensusu**. Nie liczyć teraz wyników.

Jeżeli stare ticki lub first print są niedostępne, minimalny uczciwy zamiennik
to12 kolejnych przyszłych publikacji z datowanym pierwszym odbiorem i już
zbieranym pasywnie OIL. Nie uruchomiono nowej usługi ani automatyzacji; wariant
wymaga odrębnego ustalenia odbioru komunikatów i z góry określonego końca próby.
