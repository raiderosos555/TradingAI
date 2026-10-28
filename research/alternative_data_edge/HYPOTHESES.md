# Zamrożony protokół alternative-data-v1 — przed obliczeniami

Pytanie: czy informacja spoza ceny brokera poprawia **ten sam** bazowy sygnał?
Nie wybieramy kierunku według wyników poprzedniego edge_program. Cena wszystkich
CFD pozostaje Last. Obliczenia poniżej są eksploracyjnym testem zależności
opóźnionych, nie historycznym replay as-of ani rzeczywistym netto.

## Cztery rodziny dostępne do małego testu

| ID | Mechanizm | Reguła B: baza z nową informacją | Rynki |
|---|---|---|---|
| V | Napięcie opcyjne może zakłócać spokojną kontynuację | Zachowaj bazowy kierunek tylko gdy ostatni dopuszczony VIX ≤ mediana poprzednich60 obserwacji VIX; inaczej cash | US500, US100 |
| T | Wyższa wycena ryzyka9d niż30d wskazuje koncentrację ryzyka w bliskim terminie | Zachowaj bazę tylko gdy VIX9D/VIX ≤1; obie wartości z tej samej daty; inaczej cash | US500, US100 |
| O | Rosnąca niepewność podaży/popytu może przedłużać dostosowanie ceny ropy | Zachowaj bazę gdy OVX wzrósł względem5 wcześniejszych obserwacji; inaczej cash | OIL |
| G | Rosnący popyt na ochronę i nowe informacje mogą wzmacniać trend złota | Zachowaj bazę gdy GVZ wzrósł względem5 wcześniejszych obserwacji; inaczej cash | GOLD |

To6 pierwotnych porównań, nie poszukiwanie progu. VIX mierzy SPX, więc dla
US100 jest proxy; OVX/GVZ odnoszą się do opcji ETF, nie kontraktów TMS.
Nie zakładamy, że wzrost IV oznacza wzrost ceny bazowej.

Wariant A: sign zwrotu20 D1 brokera. Wariant B: dokładnie A pomnożony przez
binarny filtr. Wariant C: long-only i cash oraz cenowy filtr ATR14/C ponad
medianę60, aby nowa informacja musiała konkurować z już dostępną zmiennością.
Wariant D: losowe zachowanie takiej samej liczby aktywnych okien w każdym
14-dniowym bloku; nie premiujemy automatycznie mniejszej ekspozycji.

D1, od następnego open do open po5 kolejnych dostępnych świecach. Siatka co5
świec od indeksu80, identyczna dla A/B/C/D. 27.04–23.10.2026 raw, split01.08.
Wszystkie stare ceny były oglądane: obie części pozostają eksploracyjne.
Nie czytamy forward do pomiaru zwrotów. Braki nie są zerem; stale IV>7dni
od daty obserwacji wyklucza okno. D1 z przerwą>4dni lub bez wyjścia wykluczone.
Wykluczenie przyszłych luk jest analizą kompletnych przypadków, nie regułą
wykonania przewidującą brak danych.

## Dostępność i ograniczenie interpretacji

Publiczne CSV Cboe są aktualnymi historiami, nie archiwum kolejnych publikacji.
Mamy datę obserwacji i obecny Last-Modified, nie first receipt każdego wiersza.
Do diagnostyki dopuszczamy tylko daty IV starsze o co najmniej72h od raw sygnału,
z dodatkowym marginesem3h (testowy przedział błędu zegara, NIE jego certyfikacja).
To konserwatywny lag badawczy, **nie udowodniony czas historycznej dostępności**.
Dlatego wykonany wynik nie może spełnić bramki „as-of”. Bez potwierdzenia tego
warunku nie symulujemy rzeczywistych wejść.

Z góry deklarujemy6 testów wrażliwości na opóźnienie168h, z dopuszczalnym
wiekiem IV≤11dni; ten wariant mierzy ryzyko błędu czasu, nie wybór najlepszego
opóźnienia. Publikujemy wszystkie12 wyników. Łącznie z wcześniejszymi36 to48
prób tej sesji badawczej. Holm6 dla głównej rodziny oraz konserwatywna korekta
Holm48 łącznie ze wszystkimi wcześniejszymi i diagnostycznymi p.

Koszt to wyłącznie próg wrażliwości: największy p95 spreadu z3 okien22.10
×point/Last wejścia. Stress2×spread+2bps+2bps/dobę. Cash koszt0. Brak sizingu,
SL, brokera Bid/Ask i historycznego finansowania: brak P&L, PF i expectancy R.
CI95 różnicy B−A: bootstrap14-dniowych bloków,4000 losowań, seed20261028.
Osobno różnica B−cenowy filtrATR, signed-markout placebo i thinning placebo.
Reżimy cenowe ATRlow/high i trendup/down opisowo, bez wybierania korzystnego.

Falsyfikuje zastosowanie: brak dodatniej wartości dodanej do A i cenowego
filtra w obu częściach, brak odporności kosztowej, wynik jak losowy filtr,
albo brak kompletnego as-of. Nie odrzuca to całej klasy mechanizmu na latach.
Nominacja wymaga20 późnych bloków, dodatniego stress i CI po wielokrotności,
potwierdzonego czasu i kosztu. Obecna próbka nie może spełnić wszystkich bramek.

## Mechanizmy poza tym obliczeniem

| Mechanizm | Zamysł, benchmark i falsyfikacja | Brakujący warunek |
|---|---|---|
| COT + trend | GOLD/OIL managed-money net/OI; indeksy/6E/6B leveraged-funds zTFF. Zgodna z trendem zmiana4tygodni pozwala utrzymać bazę; ekstremum >90percentyla52tygodni osobna przyszła hipoteza. Hold5sesji, porównanie do tej samej bazy | Publikacja po wtorkowej dacie pozycji, wyjątki i rewizje. Nie łączymy TFF z disaggregated ani futures-only z combined. Brak pełnych known-at blokuje P&L; EURPLN bez bezpośredniego odpowiednika |
| Real yields + GOLD | Spadek realnego US10Y przez20d wspiera BUY, wzrostSELL; hold5sesji. Wartość dodana ponad trend i USD, nie sama korelacja | Vintage i czas H15; indeks USD ma inną częstotliwość publikacji. Nie używać obecnej zrewidowanej serii jako first release |
| EIA + OIL | Kontynuacja/fade pierwszego5min ruchu po rzeczywistym odbiorze, hold30min; osobno model actual change i true surprise | First print, gasoline/distillates/import/production, preconsensus i Bid/Ask z kosztami. Actual bez forecast nie jest surprise |
| NBP/ECB + EURPLN | Zmiana oczekiwanej różnicy stóp a trend i risk-off; hold5sesji | Publiczne stopy to zrealizowana polityka, nie OIS; potrzebna oś publikacji |
| GPR + GOLD/EURPLN | Wysokie ryzyko geopolityczne może zmieniać reakcję na trend, holdmiesiąc; kontrola ceny/USD/vol | Bieżąca historia przeliczana, brak pełnych vintage i czasów pierwszego udostępnienia. Nie utożsamiamy artykułu z momentem otrzymania przez inwestora |

Żadne z tych zablokowanych pytań nie otrzymuje wyniku0 ani wymyślonego netto.
Odrębny przyszły zbiór potwierdzający rozpocznie się po zapieczętowaniu reguł;
stały koniec/liczba zdarzeń i brak strojenia na wielokrotnie oglądanym forward.
