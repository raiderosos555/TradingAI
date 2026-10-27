> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Etap 5 — pełna doba ticków EURUSD i odtworzenie H1/H4/D1

Badanie odczytowe 25.10.2026. Pobrano sześć kolejnych czterogodzinnych bloków **EURUSD.pro**, obejmujących surową oś API od 22.10.2026 00:00 do 23.10.2026 00:00. Te etykiety czasu nie są jeszcze potwierdzonym UTC. Każde zapytanie miało limit 40 s. Wszystkie zakończyły się poprawnie.

**277 031 rekordów tickowych; 138 484 aktualizacje Last.** Wyboru instrumentu nie dokonano według rentowności. Jest to rozszerzenie wcześniejszej weryfikacji siedmiu instrumentów o pełną dobę jednego z nich. Surowe pliki i źródłowe świece zachowano z hashami. Wynik nie jest backtestem strategii.

## Porównanie ze świecami brokera

Granice świec pochodzą z zachowanych `broker_raw_time` kolejnych świec MT5, bez przypisywania strefy UTC i bez automatycznego odejmowania offsetu. Przedziały są lewostronnie domknięte, prawostronnie otwarte. Do Last użyto wyłącznie rekordów z flagą aktualizacji Last; nie przenoszono starego Last z samych aktualizacji Bid/Ask.

| Interwał | Liczba świec | Zgodne wszystkie ceny OHLC Last | Liczba aktualizacji Last zgodna z tick_volume |
|---|---:|---:|---:|
| H1 | 24 | 24 | 24 |
| H4 | 6 | 6 | 6 |
| D1 | 1 | 1 | 1 |
| Razem | **31** | **31** | **31** |

Maksymalny błąd każdej ceny Last wynosi zero w zapisanej reprezentacji liczbowej. Dla agregacji Bid przynajmniej jedna cena różni się w 31 z 31 świec; dla Ask w 30 z 31. Zgodność jednej świecy Ask jest zbieżnością cen, a nie podstawą zmiany typu wykresu. Wcześniej i obecnie pobrana specyfikacja wskazuje `chart_mode=LAST`.

To mocniejszy dowód zgodności agregacji niż samo dopasowanie OHLC: sprawdzono również liczbę aktualizacji Last w każdej świecy. Nie certyfikuje jednak kompletności wszystkich zmian Bid/Ask na serwerze; obie porównywane historie pochodzą od tego samego brokera.

## Pokrycie i przerwy

| Blok surowej osi | Liczba ticków |
|---|---:|
| 00–04 | 20 875 |
| 04–08 | 33 548 |
| 08–12 | 64 170 |
| 12–16 | 72 434 |
| 16–20 | 62 580 |
| 20–24 | 23 424 |

Brak niepobranych przedziałów w planie zapytań. Pierwszy rekord: raw 1792627200094 ms; ostatni: raw 1792713593227 ms. Najdłuższa obserwowana przerwa między rekordami wynosi **360 232 ms**, od raw 1792709939884 do 1792710300116 (etykiety raw około 22:58:59,884–23:05:00,116). Nie rozstrzygnięto, czy jest to harmonogram kwotowań, brak zmian, czy brak historii. Nie wstawiono tam syntetycznych ticków.

Sama ciągłość wykonanych zapytań nie jest równoznaczna z udowodnioną ciągłością strumienia. `comparison.json` rozdziela `request_coverage_complete=true` i `server_history_completeness_certified=false`.

Ta doba obejmuje wcześniej widzianą godzinę EURUSD z 22.10. Nie należy dodawać całej liczby 277 031 do poprzednich statystyk i przedstawiać sumy jako liczby niezależnych nowych rekordów. Wszystkie dane są eksploracyjne.

## Testy i odtwarzanie

**12 testów automatycznych przeszło:** granice półotwarte, rekordy z tą samą milisekundą, flagi Last, brak sztucznych świec, niepoprawne Last, kolejność ticków, nakładające się granice, jawne przedziały 23/25 godzin i mapa niepobranych zakresów. Test 23/25 godzin potwierdza mechanikę arbitralnych granic, nie historyczny DST brokera.

```powershell
.\.venv\Scripts\python.exe research\tick_validation\stage5\analyze_day.py
```

`inputs/` zawiera sześć bloków ticków i dokładne kopie źródłowych H1/H4/D1. `collection.json` opisuje zakresy, limity i pochodzenie; `comparison.json` zawiera wszystkie 31 porównań cen i liczników. `manifest.json` zapisuje SHA-256. Analiza sprawdza też, że chronione pliki produkcyjne nie uległy zmianie.

## Co wynik odblokowuje

Agregator `bars.py` może służyć do budowy technicznych świec Last dla izolowanego replay, przy zachowaniu osobnych Bid/Ask do wykonania. Jest narzędziem offline. Chronologiczny replay musi jeszcze zapewnić udostępnianie silnikowi strategii wyłącznie świec już zamkniętych; wymaga to osobnego testu.

Nadal otwarte: historyczne UTC/DST i sesje, szersze pokrycie instrumentów i dat, koszty/FX, realistyczne opóźnienie oraz pełna zgodność wykonania. Parametry strategii i działające DEMO nie były zmieniane. Nie obliczono PF, expectancy, drawdown ani zysku na tej próbie.
