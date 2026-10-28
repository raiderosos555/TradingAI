# EDGE_RESEARCH_RESULTS — pierwsze testy mechanizmów

**Wiarygodna przewaga po rzeczywistych kosztach: NIE POTWIERDZONA / ZA MAŁO
WIARYGODNYCH DANYCH. Żaden kandydat z tej rundy nie kwalifikuje się do wdrożenia.**
To wynik rzeczywistych obliczeń, a nie obietnica rentowności. Nie optymalizowano
parametrów ani nie zmieniano aktywnego DEMO. Eksperyment mechanisms-v1, znacznik
wykonania 2026-10-28T12:30:47.314682+00:00, Python 3.12.14, NumPy 2.5.4.

## Co wykonano

Przegląd 16 źródeł pierwotnych, audyt danych, rejestr 11 mechanizmów. Wybrano
6 odmiennych mechanizmów przed wynikami: cztery policzono, dwa makro odrzucono
na bramce dostępności danych. 13 relacji mechanizm–rynek, 4 agregaty, 822
niepokrywające się wewnątrz danej relacji zdarzenia. Zależności między rynkami
pozostają: nie jest to 822 niezależnych transakcji. Wyniki dawniej oglądane
stanowią wyłącznie eksplorację; żadnego zwrotu z forward nie użyto do selekcji.

Sygnały z okresu raw 27.04–23.10.2026, chronologiczny podział 01.08.2026.
H4/D1 korzystają z wcześniejszego warm-up od X 2025. Wszystkie wejścia pomiarowe
po zamknięciu świecy sygnału, na kolejnym open. Pomiary z brakującym przyszłym
odcinkiem pominięto, nie interpolowano: to analiza kompletnych przypadków,
mogąca mieć bias dostępności danych. Nie jest to wykonywalna reguła pomijania
przyszłej luki. Czas raw nie pozwala nazwać godzin sesją Londynu/Nowego Jorku.

## Wyniki zbiorcze

Wartości to **bps ruchu Last i scenariusza progu kosztowego**, nie zysk netto,
R ryzyka ani PLN. Próg bazowy pomija nieznaną historyczną prowizję/finansowanie;
stress zawiera 2× próg spreadu, 2 bp dodatkowego kosztu i 2 bp/dobę utrzymania.
Nie istnieje gwarancja, że stress ogranicza najgorszy realny koszt lub lukę.

| Mechanizm | N | Bloki14d | Last brutto bp | Próg bp | Wczesne po progu | Późne po progu | Całość po progu | Stress bp | CI95 całość | p Holm późne |
|---|---|---|---|---|---|---|---|---|---|---|
| M1 | 186 | 13 | -11.471 | 1.284 | -10.051 | -15.897 | -12.754 | -28.876 | [-48.354; 22.336] | 1.000 |
| M2 | 499 | 13 | 0.253 | 0.786 | -0.193 | -0.891 | -0.533 | -3.486 | [-1.644; 0.631] | 1.000 |
| M3 | 19 | 6 | -36.906 | 3.558 | -26.637 | -59.476 | -40.464 | -46.689 | [-147.991; 32.872] | 1.000 |
| M4 | 118 | 12 | 1.125 | 0.728 | -0.721 | 1.442 | 0.397 | -2.664 | [-1.152; 2.036] | 1.000 |

M5 (makro FX) i M6 (zapasy OIL): **NIEWERYFIKOWALNE**, brak par forecast-before /
first-actual-after, historii skali surprises i zaakceptowanego czasu wykonania.
Nie wstawiono im zerowego ani hipotetycznie dodatniego wyniku.

## Wszystkie rynki, bez ukrywania nieudanych testów

| Hipoteza/rynek | N | Wczesne po progu | Późne po progu | Stress całość | Delta vs long bp | p Holm | Placebo Holm |
|---|---|---|---|---|---|---|---|
| M1/GOLD | 24 | -21.299 | -28.120 | -41.489 | 18.987 | 1.000 | 1.000 |
| M1/US500 | 24 | 26.085 | 12.869 | 3.105 | 0.000 | 1.000 | 1.000 |
| M1/OIL | 24 | -103.662 | -149.333 | -145.199 | -158.675 | 1.000 | 1.000 |
| M1/EURPLN | 30 | 10.235 | 9.597 | -5.290 | 0.000 | 0.004 | 0.246 |
| M1/EURUSD | 30 | 7.860 | 9.706 | -5.139 | 25.938 | 1.000 | 1.000 |
| M1/GBPUSD | 30 | -20.685 | -9.961 | -29.728 | -8.818 | 1.000 | 1.000 |
| M1/US100 | 24 | 24.745 | 28.412 | 9.988 | 0.000 | 1.000 | 1.000 |
| M2/EURPLN | 168 | -0.745 | -1.686 | -5.003 | -0.447 | 1.000 | 1.000 |
| M2/EURUSD | 155 | 0.075 | -0.220 | -2.497 | 0.356 | 1.000 | 1.000 |
| M2/GBPUSD | 176 | 0.086 | -0.712 | -2.909 | -0.211 | 1.000 | 1.000 |
| M3/GOLD | 6 | 20.798 | 35.752 | 24.536 | 30.984 | 1.000 | 1.000 |
| M3/OIL | 13 | -44.425 | -116.613 | -79.562 | -59.877 | 1.000 | 1.000 |
| M4/US100-US500 | 118 | -0.721 | 1.442 | -2.664 | 0.920 | 1.000 | 0.520 |

Holm obejmuje 17 zaplanowanych porównań późnej podpróby. Korekty p-zero i
placebo są odrębne; nie wybieramy korzystniejszej. Podpróba późna była już
oglądana w innych badaniach, więc nawet skorygowana istotność nie byłaby
niezależnym potwierdzeniem. M4/ALL powtarza pojedynczą parę w zestawie 17:
konserwatywna korekta, nie drugi niezależny dowód.

## Co odrzucamy, a czego próba nie rozstrzyga

- **M1, uniwersalna implementacja 126 D1:** ujemny agregat w obu częściach;
  brak podstaw do promocji. Dodatnie indeksy nie dowodzą informacji ponad
  ekspozycję long. Nie odrzuca to wieloletniego, zdywersyfikowanego TSMOM z
  literatury: nasza próba i horyzont są inne, a rollover niezweryfikowany.
  EURPLN ma późne p-zero po Holm 0,004249, ale wszystkie sygnały są BUY,
  więc wynik jest identyczny z long-only; stress jest ujemny, a placebo po
  Holm wynosi 0,246438. Sześć bloków i ograniczona bootstrapowa próba zerowa
  nie uzasadniają odczytywania małego p jako mocnego dowodu. Nie pomijamy tego
  nominalnie dodatniego testu ani nie nazywamy go przewagą sygnału.
- **M2, rewersja FX:** wszystkie trzy rynki ujemne w późnej części po progu;
  stress ujemny wszędzie. Nie ma podstaw do dokładania filtrów RSI/ADX na tej
  samej historii, aby uratować wynik.
- **M3, wybicie z ekspansją:** ujemny agregat; OIL ujemne w obu częściach.
  GOLD ma tylko 6 zdarzeń. Dodatni ruch sześciu obserwacji nie uzasadnia
  wybrania GOLD jako zwycięzcy. Brak dowodu, nie twierdzenie o niemożliwości trendów.
- **M4, para indeksów:** +0,397 bp po progu w całości, ale −2,664 bp stress;
  wczesna część ujemna, CI obejmuje zero, placebo po Holm nieistotne.
  Nominalne późne p placebo około 0,032 nie uprawnia do selekcji po 17 próbach.
- **M5/M6:** nie testowano rentowności. Wąskie gardło stanowią dane o
  oczekiwaniach i dostępności, nie brak kolejnego oscylatora.

Bootstrap wykorzystuje tylko 6–13 bloków w całości, zwykle 3–6 późnych;
to mało, a sąsiednie bloki również mogą zależeć od siebie. CI nie należy
interpretować jako precyzyjnego prawdopodobieństwa przyszłego zysku.
W DETAILS.md są wszystkie okresy, benchmarki, placebo, opisowe PF i obsunięcia
sumy markoutów. **PF i obsunięcie rachunku oraz expectancy w R: NIEWERYFIKOWALNE**,
bo nie określono wykonywalnego portfela, SL, sizingu, finansowania i Bid/Ask.

## Maksymalnie trzy kierunki uzasadnione mechanizmem, nie rankingiem P&L

1. **M1, powolny trend między klasami aktywów:** najmocniejsze zewnętrzne
   podstawy dla hipotezy cenowej, lecz obecna implementacja nie przeszła testu.
   Minimalny kolejny krok to sprawdzenie dostępności co najmniej 5 lat D1
   z opisem rollowania i kosztów dla tych ekspozycji. Gdy brak zgodności CFD,
   futures można badać wyłącznie jako inny rynek; nie przenosić jego netto.
   Jeden zamrożony test znaku zwrotu vs matched long-only i cash, bez siatki.
2. **M5, kontynuacja po surprise makro na EURUSD/GBPUSD:** zbierać już
   autoryzowanym archiwum forecast z wersją przed publikacją i pierwszy actual
   z czasem odbioru; najpierw potwierdzić, że w ogóle powstają poprawne pary.
   Do ilościowego testu potrzeba także 24 wcześniejszych surprises i Bid/Ask
   po opóźnionym wejściu. Pozyskanie licencjonowanej historii konsensusu
   wymaga osobnej oceny źródła; oficjalny actual sam nie wystarcza.
3. **M6, inventory surprise OIL:** najpierw audyt jednego legalnego źródła
   oczekiwań oraz pierwszych odczytów EIA w tej samej jednostce. To konkretny
   brak blokujący mechanizm; nie wdrażamy feedu lub rozbudowy systemu w tej rundzie.
   Test po 5-min opóźnieniu, z kontekstem produktów i kosztami publikacji,
   musi wykazać ruch pozostający po początkowym skoku.

To priorytety zbierania dowodów, **nie trzy wybrane zyskowne strategie**. M4
nie otrzymuje pierwszeństwa tylko dlatego, że miał dodatnią średnią bazową.
M7/M8 pozostają rozsądnymi dalszymi hipotezami sesyjnymi po odblokowaniu UTC
i danych M1; GOLD real yields wymaga osobnego as-of źródła.

## Jak odróżnić przewagę od przypadku

Przed zobaczeniem nowych zwrotów zamrozić sygnał, źródło, latency, koszty,
benchmark, statystykę, liczbę prób i datę zakończenia. Zachować wszystkie
publikacje i NO TRADE, nie wymieniać słabego okna. Pierwszy poprawny replay
potwierdzi mechanikę, nie edge. Ustalić minimalny ekonomiczny efekt delta i
moc testu; przy niezależnych zdarzeniach orientacyjnie n≈(1,96+0,84)^2×(sigma/delta)^2,
następnie zwiększyć n o zależność i wielokrotność. Nie obiecujemy, że 30, 100
czy jedna doba wystarczy. NFP daje około 12 publikacji rocznie, EIA około 52:
kilka dni forward nie rozstrzygnie tych hipotez.

Wymagane potwierdzenie: przedział średniego realnego netto ponad zero i ponad
ekonomiczny próg, stabilność chronologiczna, wynik względem benchmarku,
odporność na koszty, zgodność replay z cenami DEMO oraz korekta wielu prób.
Po porażce nie stroić tej samej próby i nadal nazywać jej niezależną.

## Decyzje

| Obszar | Decyzja |
|---|---|
| Ograniczone badania mechanizmów na starych danych | GO wyłącznie eksploracyjne |
| Wybranie strategii do handlu / potwierdzenie netto | NO-GO |
| Pełny backtest bieżącego forward | NO-GO: UTC, feed, kontekst i wykonanie |
| Odporność aktywnego DEMO | NO-GO: niewdrożone Recovery i zachowana kwarantanna |

Zakończono tę rundę bez rozbudowy infrastruktury i bez transakcji. Kod i
oczyszczone agregaty przeznaczono na osobną gałąź GitHub; prywatne dane,
historia rachunku i surowe wyniki zdarzeń pozostają lokalnie.
