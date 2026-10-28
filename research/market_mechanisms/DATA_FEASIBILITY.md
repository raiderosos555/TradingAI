# DATA_FEASIBILITY — dane możliwe do uczciwego użycia

Punkt odcięcia audytu: 2026-10-27T18:51:07.302742+00:00. To migawka, a nie bieżąca liczba danych
rosnącego archiwum. Dane do eksperymentów pobrano wcześniej; nie odpytywano
terminala o nowe ceny na potrzeby selekcji. Źródła przypięto 21 hashami SHA256.

| Rynek | H1 | H4 | D1 | H1 real_volume >0 | Próg spreadu w jednostkach ceny |
|---|---|---|---|---|---|
| GOLD | 2973 | 1548 | 261 | 0 | 0.46 |
| US500 | 2969 | 1546 | 262 | 2969 | 0.7 |
| OIL | 2973 | 1548 | 261 | 2973 | 0.04 |
| EURPLN | 3117 | 1607 | 312 | 0 | 0.0007 |
| EURUSD | 3117 | 1607 | 312 | 0 | 3e-05 |
| GBPUSD | 3116 | 1607 | 312 | 0 | 6e-05 |
| US100 | 2969 | 1546 | 262 | 2969 | 1.3 |

Pełna precyzja małych spreadów jest w INPUT_HASHES.md. H1: raw 27.04.2026
02:00–23.10.2026 22:00 (21 234 świece). H4: raw 24.10.2025 04:00–23.10.2026
20:00. D1: raw 26.10.2025–23.10.2026. Etykiety raw nie są potwierdzonym UTC.
Zapisane pole time z legacy przesunięciem −7200 nie jest używane w eksperymencie.
Nie zakładamy stałego przesunięcia brokera. Różna liczba D1 FX wynika również
z odmiennej budowy tygodnia/sesji; 126 D1 nie jest dokładnie 126 sesjami giełdowymi.

Wszystkie siedem kontraktów ma ustalony wcześniej chart_mode LAST. Nie wolno
przenosić spreadu na Last tak, jakby Last był Bid lub mid. H1/H4/D1 nadają się
do eksploracyjnych testów warunkowego ruchu, nie do deklaracji net execution.
Brak historii korekt/rollowania kontraktów dodatkowo ogranicza długi trend.
Niezerowy real_volume w indeksach i OIL jest polem brokera, bez certyfikacji
pełnego obrotu giełdowego; FX/GOLD mają w tym zbiorze zero. Tick_volume jest
liczbą zmian tickowych, nie wolumenem globalnego rynku lub order flow.

## Ticki, czas i inne interwały

Wcześniejszy audyt ticków 22.10 obejmuje 5 401 052 rekordy z 42 żądanych bloków:
GOLD 977 204; US500 1 393 823; OIL 600 008; EURPLN 94 204;
EURUSD 277 031; GBPUSD 432 782; US100 1 626 000. Chronologia wewnątrz pliku
i przypadki niewykonywalnych kwotowań są zachowane. To jedna doba; nie
powtarzano jej testów ani nie nazywano niezależną walidacją nowych hipotez.
Historyczne offsety i zgodność z feedem decyzji pozostają niezaakceptowane.

Runtime ma również M1/M5/M15/M30, zwykle krótkie paczki 200 świec w kilku
przestrzeniach konfiguracji. Nie sumujemy kolejnych kopii jako niezależnej,
ciągłej historii. Nie ma zatwierdzonego wieloletniego tape M1/M30 do sesyjnej
replikacji S7/S8. H1 relacje wyliczono wyłącznie na wspólnych dokładnych raw
timestampach, bez interpolacji; wspólny stempel nie gwarantuje jednoczesnego
wykonania dwóch kontraktów.

Forward cohort-20261026-v1 pozostaje zastrzeżony. Zakończone okno 27.10 ma
1 600 232 rekordy, 0 błędów hashy wybranych plików i warunkowe pokrycie żądań.
11 globalnych rewizji overlap, niecertyfikowane UTC, różnice historycznego
feedu i ceny decyzji oraz kontekst/wykonanie blokują pełny replay. Zobacz
DEMO_AUDIT_RECEIPT.md. Nie użyto zwrotów z forward do wyboru tych hipotez.

## Makro i informacje dostępne w danej chwili

Archiwum rozpoczęło zbieranie wersji kalendarza 26.10.2026. W migawce audytu:
296 wersji, 207 zdarzeń, 127 z prognozą zaobserwowaną przed planowanym czasem,
5 z jakimkolwiek actual, **0 par prognoza-przed + actual-po**. USD93, EUR103,
GBP11, PLN0. Jednostki występują w 207 rekordach. Pola previous istnieją w
schemacie, ale nie ma zaakceptowanej historii pierwszych publikacji i rewizji
previous/actual. Nie używamy dzisiejszego previous jako wiedzy z przeszłości.
Nawet obecność forecast/actual nie dowodzi prawidłowej latencji i czasu UTC.

**M5/M6 są NIEWERYFIKOWALNE**, nie mają wartości P&L równej zero. Historia
24 wcześniejszych niespodzianek i as-of konsensus są dodatkowymi brakami.

| RSS | Liczba | Pierwszy odbiór UTC | Ostatni pierwszy odbiór UTC | Najmniejsze opóźnienie publikacja→odbiór [h] |
|---|---|---|---|---|
| bbc_world | 190 | 2026-10-24T10:10:57.534718+00:00 | 2026-10-27T18:29:19.643988+00:00 | 0.006 |
| ecb | 18 | 2026-10-24T10:14:18.641949+00:00 | 2026-10-27T09:14:18.586489+00:00 | 0.238 |
| eia | 19 | 2026-10-24T10:10:57.532720+00:00 | 2026-10-24T10:10:57.534718+00:00 | 44.183 |
| fed | 15 | 2026-10-24T10:10:57.528727+00:00 | 2026-10-24T10:10:57.532720+00:00 | 256.183 |

To tytuł, URL, znaczniki publikacji/odbioru i znormalizowany rekord, nie pełny
historyczny korpus artykułów ani surowe wszystkie wersje RSS. Zero kierunkowych
sygnałów we wszystkich czterech źródłach. Archiwum kontekstu zawiera 100 wersji
newsów w tej migawce; odtworzenie późniejszego nagłówka nie czyni go dostępnym
wcześniej. EIA Today in Energy nie jest taśmą pierwszego inventory actual i
konsensusu. BBC World nie jest precyzyjnym makro wire. Fed/EBC oficjalne
komunikaty nie zastępują historycznych oczekiwań rynku.

Briefing: tylko częściowy poranny zapis 23.10 (JSON i Markdown). Brak pełnego
zbioru przyszłych planów wraz ze wszystkimi NO TRADE/HOLD/CANCEL. Istnienie
kodu archiwizacji nie jest dowodem danych. Briefingi pozostają SHADOW.

## Koszty i klasy dopuszczalnych badań

Trzy 15-minutowe okna 22.10 dostarczają rzeczywistych spreadów, ważonych liczbą
ticków. Największe p95 to jawny próg analityczny, **nie historyczny spread każdej
transakcji**. Wcześniejszy odczyt historii zawiera 27 deal, z zerową prowizją i fee
w tych konkretnych zapisach oraz swap GOLD +0,04 PLN. Nie dowodzi zerowej taryfy
historycznej ani przyszłej; brak reprezentatywnego poślizgu, spreadu i finansowania.
Nie używamy aktualnego tick_value do historycznego wyniku PLN.

| Zastosowanie | Decyzja |
|---|---|
| Odkrywanie i odrzucanie hipotez cenowych, koszty jako scenariusz | GO eksploracyjne, z jawnymi ograniczeniami Last/raw |
| Makro/news backtest as-of | NO-GO: brak wcześniejszych prognoz/pierwszych publikacji i historii latencji |
| Sesyjne wzorce cash/FX | NO-GO: brak certyfikowanego czasu i długiej historii odpowiednich interwałów |
| Netto/PF/drawdown rachunku z tych OHLC | NO-GO: brak prawidłowego modelu wykonania i kosztów |
| Niezależny forward po zamrożeniu | Warunkowo: najpierw akceptacja czasu, feedu i as-of; nie stroić na wyniku |
