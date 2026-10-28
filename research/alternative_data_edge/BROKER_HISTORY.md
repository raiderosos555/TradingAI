# Historia brokera: zakres potwierdzony, nie domniemany

OANDA TMS, chart_mode=LAST dla wszystkich7. Poniższe daty są interpretacją liczby raw jako daty kalendarzowej, **nie certyfikatem UTC**. Nie zmieniono konfiguracji terminala, liczby świec ani symboli.

## Istniejące lokalne archiwa

| Rynek | TF | n | pierwszy raw | ostatni raw |
|---|---|---|---|---|
| GOLD | H1 | 2973 | 2026-04-27T02:00:00+00:00 | 2026-10-23T22:00:00+00:00 |
| GOLD | H4 | 1548 | 2025-10-24T04:00:00+00:00 | 2026-10-23T20:00:00+00:00 |
| GOLD | D1 | 261 | 2025-10-26T00:00:00+00:00 | 2026-10-23T00:00:00+00:00 |
| US500 | H1 | 2969 | 2026-04-27T02:00:00+00:00 | 2026-10-23T22:00:00+00:00 |
| US500 | H4 | 1546 | 2025-10-24T04:00:00+00:00 | 2026-10-23T20:00:00+00:00 |
| US500 | D1 | 262 | 2025-10-26T00:00:00+00:00 | 2026-10-23T00:00:00+00:00 |
| OIL | H1 | 2973 | 2026-04-27T02:00:00+00:00 | 2026-10-23T22:00:00+00:00 |
| OIL | H4 | 1548 | 2025-10-24T04:00:00+00:00 | 2026-10-23T20:00:00+00:00 |
| OIL | D1 | 261 | 2025-10-26T00:00:00+00:00 | 2026-10-23T00:00:00+00:00 |
| EURPLN | H1 | 3117 | 2026-04-27T02:00:00+00:00 | 2026-10-23T22:00:00+00:00 |
| EURPLN | H4 | 1607 | 2025-10-24T04:00:00+00:00 | 2026-10-23T20:00:00+00:00 |
| EURPLN | D1 | 312 | 2025-10-26T00:00:00+00:00 | 2026-10-23T00:00:00+00:00 |
| EURUSD | H1 | 3117 | 2026-04-27T02:00:00+00:00 | 2026-10-23T22:00:00+00:00 |
| EURUSD | H4 | 1607 | 2025-10-24T04:00:00+00:00 | 2026-10-23T20:00:00+00:00 |
| EURUSD | D1 | 312 | 2025-10-26T00:00:00+00:00 | 2026-10-23T00:00:00+00:00 |
| GBPUSD | H1 | 3116 | 2026-04-27T02:00:00+00:00 | 2026-10-23T22:00:00+00:00 |
| GBPUSD | H4 | 1607 | 2025-10-24T04:00:00+00:00 | 2026-10-23T20:00:00+00:00 |
| GBPUSD | D1 | 312 | 2025-10-26T00:00:00+00:00 | 2026-10-23T00:00:00+00:00 |
| US100 | H1 | 2969 | 2026-04-27T02:00:00+00:00 | 2026-10-23T22:00:00+00:00 |
| US100 | H4 | 1546 | 2025-10-24T04:00:00+00:00 | 2026-10-23T20:00:00+00:00 |
| US100 | D1 | 262 | 2025-10-26T00:00:00+00:00 | 2026-10-23T00:00:00+00:00 |

## Nowa sonda range z limitem czasu

| Rynek | API/TF | zakres żądany od | rekordów | Bid/Ask dodatnie | status |
|---|---|---|---|---|---|
| GOLD | M1 | 2026-10-22T12:00:00 | 61 | nie dotyczy | OK |
| US500 | M1 | 2026-10-22T12:00:00 | 61 | nie dotyczy | OK |
| OIL | M1 | 2026-10-22T12:00:00 | 61 | nie dotyczy | OK |
| EURPLN | M1 | 2026-10-22T12:00:00 | 61 | nie dotyczy | OK |
| EURUSD | M1 | 2026-10-22T12:00:00 | 61 | nie dotyczy | OK |
| GBPUSD | M1 | 2026-10-22T12:00:00 | 61 | nie dotyczy | OK |
| US100 | M1 | 2026-10-22T12:00:00 | 61 | nie dotyczy | OK |
| GOLD | ticks | 2026-10-22T12:00:00 | 24 | 24 | OK |
| US500 | ticks | 2026-10-22T12:00:00 | 29 | 29 | OK |
| OIL | ticks | 2026-10-22T12:00:00 | 30 | 30 | OK |
| EURPLN | ticks | 2026-10-22T12:00:00 | 2 | 2 | OK |
| EURUSD | ticks | 2026-10-22T12:00:00 | 8 | 8 | OK |
| GBPUSD | ticks | 2026-10-22T12:00:00 | 18 | 18 | OK |
| US100 | ticks | 2026-10-22T12:00:00 | 34 | 34 | OK |
| GOLD | H1 | 2024-01-15T12:00:00 | 2 | nie dotyczy | OK |
| US500 | H1 | 2024-01-15T12:00:00 | nieweryfikowalne | nie dotyczy | TIMEOUT_15S |

M1:22.10.2026 12:00–13:00,61świec/rynek. Ticks:12:00:00–12:00:01, odczyt rzeczywistych Bid/Ask w krótkiej próbce, bez dopisywania cen. Granice API mogą być inkluzywne. Poszczególny sukces nie dowodzi pełnej doby ani lat bez luk.
GOLD H1:2świece z15.01.2024. Następne US500 H1 przekroczyło15s; zatrzymano wyłącznie własne procesy sondy i nie wysłano pozostałych26żądań. Brak odpowiedzi nie oznacza braku historii. Wcześniejsza sonda copy_rates_from D1 także nie odpowiedziała; dlatego zastosowano zewnętrzny deadline.
**Najdłuższy możliwy zakres serwera pozostaje nieustalony.** Udowodniony punkt starszej dostępności to2024 H1 GOLD; dla innych instrumentów są archiwa lokalne i krótka próbka22.10. Nie ogłaszamy2025 początkiem historii serwera.

## Jakość, czas i koszty

- H1/H4/D1 z istniejących archiwów; M1 nowo potwierdzony. Nie badano wszystkich pozostałych interwałów.
- Brak pełnej historycznej mapy UTC/DST. Nie używamy stałego offsetu do testów sesyjnych lub EIA. Potrzebny współczesny dowód server-vs-UTC i osobne datowane dowody historyczne.
- Historia brokerowych spreadów, prowizji, finansowania, przeliczenia FX i rollover nie jest kompletna. Archiwalne specyfikacje i swapy TMS z edge_program/DATA_SOURCES.md pomagają, lecz nie tworzą automatycznie pełnego modelu.
- Dodatnie Bid/Ask jednej sekundy nie certyfikują aktualności każdej strony ani okresów zerowych kwotowań. Last/volume i zmiany stron należy rozdzielać po flags i czasie.
- Nie policzono różnic kwotowań TMS–Dukascopy/TrueFX: brak dopasowanych próbek w obu feedach. Ich ticki mogą służyć replikacji mechanizmu, nie dowodowi netto TMS.
- Nie pobrano masowych archiwów, nie zmieniono aktywnego DEMO ani kolektora.

Wniosek: małe zapytania range potrafią zwrócić rzeczywiste dane. Zakup innego feedu nie jest jeszcze uzasadniony samą nieskuteczną sondą starej historii. Następna próba powinna mieć mały, jawny zakres i działać poza aktywną sesją terminala.
