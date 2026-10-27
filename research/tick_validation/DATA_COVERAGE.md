> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Dostępność danych tickowych — etap 1

Etap 1, raport 2026-10-25T07:50:23.638758+00:00. Wyłącznie badanie danych, cen i czasu. Brak zleceń, zmian produkcyjnych, strojenia strategii i pełnego ponownego backtestu. Wszystkie dane historyczne są eksploracyjne.

## Potwierdzone lokalne dane

Sprawdzono 371 167 zapisanych ticków z siedmiu instrumentów, po jednej godzinie na instrument. Surowy przedział osi API: `[1792681200000, 1792684800000)` ms, czyli etykieta 22.10.2026 15:00–16:00 przy formatowaniu liczby epoki. **Nie nadajemy jej automatycznie znaczenia UTC.** Poprzedni audyt opisywał tę godzinę jako 13:00–14:00 UTC po odjęciu 7200 s. Nowy kod przywraca `broker_raw_time_msc` i zachowuje osobno niepotwierdzone mapowanie.

| Instrument | Ticki | Pierwszy raw ms | Ostatni raw ms | Największa przerwa ms | Pary o tym samym ms |
|---|---|---|---|---|---|
| EURPLN | 5030 | 1792681200139 | 1792684799237 | 27771 | 2515 |
| EURUSD | 21524 | 1792681200017 | 1792684799952 | 5198 | 10762 |
| GBPUSD | 30138 | 1792681200088 | 1792684799885 | 6054 | 15069 |
| GOLD | 76518 | 1792681200033 | 1792684799985 | 3431 | 38259 |
| OIL | 49354 | 1792681200044 | 1792684799932 | 2534 | 9498 |
| US100 | 101861 | 1792681200035 | 1792684799973 | 874 | 36634 |
| US500 | 86742 | 1792681200049 | 1792684799973 | 1217 | 26349 |

Wszystkie te strumienie przeszły walidację dodatnich, skończonych Bid/Ask, Ask≥Bid oraz niemalejącego czasu. Rekordy o tym samym milisekundowym znaczniku zachowują kolejność dostawcy. Nie sortujemy uszkodzonych szeregów, nie odrzucamy domniemanych duplikatów i nie interpolujemy brakujących cen. Przerwa między tickami może oznaczać brak zmian ceny, zamknięcie sesji albo brak danych — sama jej długość nie rozstrzyga przyczyny. Równe timestampy nie dowodzą błędu danych.

## Ograniczone zapytania o dalszą historię

| Data w surowej osi | Status próby GOLD | Pozostałe instrumenty |
|---|---|---|
| 2025-10-24 | TIMEOUT | Nie odpytywano po przekroczeniu limitu czasu |
| 2025-10-27 | TIMEOUT | Nie odpytywano po przekroczeniu limitu czasu |
| 2026-03-27 | TIMEOUT | Nie odpytywano po przekroczeniu limitu czasu |
| 2026-03-30 | TIMEOUT | Nie odpytywano po przekroczeniu limitu czasu |
| 2026-04-27 | TIMEOUT | Nie odpytywano po przekroczeniu limitu czasu |
| 2026-08-31 | TIMEOUT | Nie odpytywano po przekroczeniu limitu czasu |
| 2026-10-22 | TIMEOUT | Nie odpytywano po przekroczeniu limitu czasu |
| 2026-10-23 | TIMEOUT | Nie odpytywano po przekroczeniu limitu czasu |

Zaplanowano 56 okien po 2 minuty (12:00–12:02 w surowej osi), obejmujących początek i podział dawnej próby oraz okolice poprzednich DST. Osiem prób GOLD przekroczyło 18-sekundowy limit procesu; pozostałe 48 pominięto, aby nie mnożyć kosztownych prób. Limit obejmuje inicjalizację i odczyt, więc nie dowodzi, że zawiesił się konkretnie serwer historii. **TIMEOUT nie oznacza EMPTY ani braku danych u brokera. Nie ustalono najwcześniejszego ani pełnego zakresu dostępności historycznej.**

Zachowano `coverage.v2.json` i `bounded_manifest.v2.json`. Pierwsza wersja procesu pomocniczego miała błąd lokalnego importu MetaTrader5; jej `coverage.json` nie służy do oceny brokera. Początkowy nieograniczony odczyt starej historii przerwano; zastąpił go ograniczony proces badawczy. Nie zatrzymywano terminala ani procesów DEMO.

## Świece i kalendarz

Z wcześniejszych odczytów odzyskano surowe czasy H4/D1 dla GOLD, US100 i EURUSD wokół jesieni 2025 oraz wiosny 2026; dokładne rekordy są w `evidence/raw-grid-*.json`. Początek przechowywanego rocznego zbioru może wypadać po żądanym początku okna; nazwa okna nie stanowi dowodu pełnego pokrycia. H1 historycznie porównano na wyżej wymienionej godzinie; nie pozyskano dodatkowej pełnej historii H1 wokół dawnych DST.

Brak archiwalnych harmonogramów sesji uniemożliwia odróżnienie każdej luki od poprawnego zamknięcia rynku. Oficjalne API zwraca pola ticków i znaczniki zmian, lecz pobranie wycinka nie certyfikuje pełności historii. [Dokumentacja copy_ticks_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py).

## Odtworzenie

`evidence/basis-*.json.gz` zawiera kopie znanych ticków. `price_checks.json/csv`, `bar_grid_checks.json`, `clock_assessment.v2.json` i hashe umożliwiają weryfikację offline. Nie wymagają ponownego pobierania z MT5. Nowe kolekcje należy zapisywać pod nową wersją; ukończony bounded manifest blokuje przypadkowe powtórzenie zapisu.
