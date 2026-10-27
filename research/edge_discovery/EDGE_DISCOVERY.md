# EDGE_DISCOVERY — badanie przewagi, 27.10.2026

**Czy znaleziono wiarygodną przewagę: NIE.** Nie jest to dowód, że przewaga nie istnieje. Dla oceny rzeczywistego netto po wszystkich kosztach nadal jest **ZA MAŁO DANYCH**. Poniższe liczby są rzeczywistymi obliczeniami na zapisanych danych brokera; nie są wygenerowanym P&L ani wynikami rachunku.

Przetestowano **8 rodzin / 53 kombinacje**, 11,332 nienakładających się wewnątrz kombinacji zdarzeń H1. Odrębnie przeliczono 102 markoutów Bid/Ask z jednej doby; 6 zdarzeń nie uzyskało świeżych stron na wejściu lub wyjściu w limicie 10 s. Nie zmieniano parametrów po wyniku, nie wykonano transakcji i nie użyto forward do wyboru reguł.

Po usunięciu tożsamości rodziny to 8181 różnych kierunkowych odcinków H1 oraz 63 odcinki tickowe. One również mogą nakładać się czasowo i korelować; nie są liczbą niezależnych transakcji.

## 1. Co faktycznie zbadano

Wspólne warunki: sygnał wyłącznie z zamkniętych H1, wejście po zamknięciu, wyjście czasowe po 4h, 120 barów rozgrzewki, najwyżej jedna ekspozycja na daną kombinację w danym czasie. H1 mierzy późniejszy ruch Last. Ticki mierzą BUY Ask→Bid / SELL Bid→Ask. Nie ma intrabar SL/TP ani zarządzania DEMO w tym badaniu; oba istniejące algorytmy DEMO pozostają zamrożonym punktem odniesienia, a ich dawny niewiarygodny P&L nie jest benchmarkiem liczbowym.

| Hipoteza | Proponowany mechanizm, nie udowodniony fakt | Mierzalny sygnał |
|---|---|---|
| trend | Persistence of slow information/flows | BUY if EMA20 > EMA50, SELL otherwise |
| momentum | Delayed response to order flow | Direction of close minus close six completed bars ago; absolute move >= 0.5 ATR14 |
| extreme_reversion | Temporary inventory pressure unwinds | Oppose the last one-bar close move if absolute move > 2 ATR14 |
| breakout | Stop orders and information beyond established range | Close outside high/low of previous 20 bars; follow break |
| false_breakout | Failed price discovery and trapped breakout traders | High breaches prior 20-bar high but closes below: SELL; symmetric BUY; reject double-sided breach |
| volatile_momentum | Information arrival can strengthen continuation | Momentum rule only when ATR14 > 1.25 times its preceding 100-bar median |
| clock_breakout | Participation and liquidity differ during the day | Break previous six-bar range; entry raw clock hour 14..17; NOT a verified New York/London session |
| cross_momentum | Related equity/FX markets transmit common flows | Follow matched leader six-bar momentum >= 0.5 leader ATR; only four predeclared directed pairs |

Dane wymagane: H1 Last i wcześniejsze ATR/EMA dla wszystkich rodzin; wspólne znaczniki leader/follower dla cross_momentum; potwierdzone UTC i sesje do interpretacji clock_breakout jako konkretnej giełdy. Do wykonania każda wymaga Bid/Ask, czasu, kontraktu i kosztów z danej chwili. Falsyfikacja każdej: brak dodatniej średniej po kosztach i stabilności w zamrożonym późniejszym oknie; dla wybicia także zanik ruchu po przekroczeniu poziomu, dla rewersji dalsza kontynuacja ekstremum, dla cross — brak zysku followera po opóźnieniu, dla sesji — brak stabilności po prawidłowym UTC, dla reżimu — brak kontynuacji poza pojedynczym epizodem zmienności.

## 2. Audyt dostępnych danych

| Instrument | H1 | Pierwsza etykieta raw | Ostatnia etykieta raw | Luki >1h | Ticki 22.10 | Niepoprawne Bid/Ask |
|---|---|---|---|---|---|---|
| GOLD | 2973 | 2026-04-27T02:00:00 | 2026-10-23T22:00:00 | 129 | 977204 | 1 |
| US500 | 2969 | 2026-04-27T02:00:00 | 2026-10-23T22:00:00 | 129 | 1393823 | 0 |
| OIL | 2973 | 2026-04-27T02:00:00 | 2026-10-23T22:00:00 | 129 | 600008 | 0 |
| EURPLN | 3117 | 2026-04-27T02:00:00 | 2026-10-23T22:00:00 | 25 | 94204 | 0 |
| EURUSD | 3117 | 2026-04-27T02:00:00 | 2026-10-23T22:00:00 | 25 | 277031 | 0 |
| GBPUSD | 3116 | 2026-04-27T02:00:00 | 2026-10-23T22:00:00 | 26 | 432782 | 0 |
| US100 | 2969 | 2026-04-27T02:00:00 | 2026-10-23T22:00:00 | 129 | 1626000 | 0 |

**Raw oznacza surową oś liczbową brokera, nie potwierdzone UTC.** Nie stosowano stałego offsetu. Wszystkie siedem serii to Last; nie zamieniono ich w Bid/Ask przez dodanie spreadu. Dane H1 27.04–23.10 były już oglądane. Podział raw 01.08 rozdziela okres wczesny i późny wyłącznie dla kontroli stabilności. Liczba obserwacji niezależnego potwierdzenia wynosi **0**.

Po rozgrzewce rzeczywiście ocenione zdarzenia obejmują **04.05–31.07 (65 dni)** oraz **03.08–23.10 (60 dni)**. Świece z końca kwietnia są tylko wcześniejszym wejściem do wskaźników.

| Instrument | H4 liczba | D1 liczba |
|---|---|---|
| GOLD | 1548 | 261 |
| US500 | 1546 | 262 |
| OIL | 1548 | 261 |
| EURPLN | 1607 | 312 |
| EURUSD | 1607 | 312 |
| GBPUSD | 1607 | 312 |
| US100 | 1546 | 262 |

H4/D1 to około rok zapisanego kontekstu do odkrywania dłuższych zależności, niewykorzystany do strojenia tego przebiegu. Baza runtime zawiera bars/ticks/snapshots/deals/orders; jest zapisem zbierania i wykonania, nie automatycznie kompletną historią badawczą. Nie mieszano jej z nową próbą potwierdzającą. Wszystkie 42 czterogodzinne bloki pobrania 22.10 mają zapisane dane; pokrycie zakresów zapytań nie dowodzi kompletności historii u brokera ani poprawności każdej ciszy sesyjnej.

| Zbiór | Dozwolone zastosowanie | Czego nie dowodzi |
|---|---|---|
| H1/H4/D1 Last | odkrywanie sygnałów i odrzucanie słabych mechanizmów | wykonania i netto |
| Bid/Ask/Last raw 22.10 | wstępne markouty cen stron, diagnostyka kosztów i braków | przewagi wielodniowej, UTC, kosztów całkowitych |
| Trzy okna spreadu 22.10 | jawny próg kosztowy / scenariusz stresu | rocznej taryfy i historycznego spreadu |
| cohort-20261026-v1 | niezależny forward zamrożonych reguł, audyt integralności | zbioru do strojenia nowych hipotez |
| Stare backtesty | diagnoza błędu Last/Bid i kosztów | dodatniego oczekiwanego P&L |

## 3. Wyniki H1: ruch po progu kosztów, nie netto rachunku

**U = ATR14 w jednostkach ceny**, nie rzeczywiste R transakcji. W kolumnie po progu odejmujemy najwyższy obserwowany P95 spreadu z trzech historycznych okien. Stres = 2× ten spread + 0,05 U na łączne nieskalibrowane prowizje i poślizg. Spread z H1 nie jest używany. To nie poprawia Last na ceny wykonania; rzeczywiste netto R, cash P&L i DD rachunku są **n/d**, nie zero.

| Rodzina | N wcz./póź. | Dni wcz./póź. | Śr. wcz. po progu U | Śr. późna brutto U | Śr. późna po progu U | Późny stres U | PF proxy późny | DD proxy późny U | CI95 późne U |
|---|---|---|---|---|---|---|---|---|---|
| trend | 1796/1676 | 65/60 | -0.066 | 0.043 | -0.037 | -0.166 | 0.945 | 153.221 | [-0.145; 0.072] |
| momentum | 1513/1398 | 65/60 | -0.064 | 0.065 | -0.016 | -0.148 | 0.976 | 117.566 | [-0.143; 0.109] |
| extreme_reversion | 142/128 | 53/51 | 0.176 | -0.260 | -0.351 | -0.491 | 0.674 | 48.013 | [-0.855; 0.154] |
| breakout | 488/464 | 65/60 | -0.101 | 0.068 | -0.012 | -0.142 | 0.985 | 74.176 | [-0.292; 0.255] |
| false_breakout | 529/507 | 65/60 | -0.060 | -0.052 | -0.131 | -0.260 | 0.840 | 80.388 | [-0.270; 0.011] |
| volatile_momentum | 262/223 | 54/52 | -0.071 | 0.057 | 0.005 | -0.098 | 1.010 | 13.745 | [-0.164; 0.153] |
| clock_breakout | 312/303 | 63/60 | -0.189 | -0.068 | -0.135 | -0.252 | 0.853 | 72.038 | [-0.488; 0.197] |
| cross_momentum | 829/762 | 65/60 | -0.099 | 0.106 | 0.061 | -0.035 | 1.087 | 45.424 | [-0.131; 0.241] |

PF/DD są opisem zsumowanych zdarzeń o równych jednostkach U, nie wykonalnym portfelem. Instrumenty i hipotezy współwystępują; nie dodajemy ich liczebności jako niezależnych transakcji. Bootstrap losuje wspólne pięciodniowe bloki dla rynków. Liczba dni to liczba klastrów, a nie dowód niezależności. Zależność między tygodniami i zmiany reżimu mogą dalej zaniżać niepewność.

| Rodzina | Orientacyjny CI skorygowany na 53 testy, późny U |
|---|---|
| trend | [-0.201; 0.133] |
| momentum | [-0.219; 0.208] |
| extreme_reversion | [-1.245; 0.534] |
| breakout | [-0.475; 0.487] |
| false_breakout | [-0.348; 0.108] |
| volatile_momentum | [-0.307; 0.271] |
| clock_breakout | [-0.732; 0.419] |
| cross_momentum | [-0.257; 0.350] |

Korekta jest tylko diagnostyczna: ekstremalne kwantyle z 4000 replik są mało precyzyjne, dane były wcześniej wielokrotnie używane, a podgrupy zwiększają liczbę oglądanych wyników. Nie traktujemy pojedynczego CI wykluczającego zero jako potwierdzenia przewagi. Wyniki wszystkich instrumentów, miesięcy, godzin raw i reżimów są w DETAIL_RESULTS.md; nie ukryto ujemnych komórek.

## 4. Jedna doba rzeczywistych stron Bid/Ask

Pierwszy świeży, dodatni snapshot po opóźnieniu 250 ms; zero/crossed quote nie jest zastępowane starszą ceną. Zachowano kolejność ticków i wiek stron oparty na flagach Bid/Ask, odrębny od Last/volume. Wiek zmiany <=10 s jest konserwatywnym warunkiem badania, nie dowodem wygaśnięcia niezmienionej oferty. Wynik poniżej jest **po obserwowanym spreadzie, przed nieznanymi opłatami**. Brak zaakceptowanego UTC nie przeszkadza mierzyć względnego ruchu na jednej osi, ale blokuje wiarygodną interpretację sesji, rolloveru i kalendarza.

| Rodzina | Markouty | Śr. po Bid/Ask U | Śr. obciążenie spreadem U | Stres U | 1 s opóźnienia U |
|---|---|---|---|---|---|
| trend | 27 | -0.338 | 0.051 | -0.433 | -0.332 |
| momentum | 24 | -0.136 | 0.053 | -0.232 | -0.141 |
| extreme_reversion | 3 | -2.268 | 0.125 | -2.405 | -2.265 |
| breakout | 11 | 0.633 | 0.045 | 0.550 | 0.682 |
| false_breakout | 14 | -0.071 | 0.038 | -0.156 | -0.076 |
| volatile_momentum | 3 | 0.657 | 0.015 | 0.596 | 0.655 |
| clock_breakout | 6 | -0.695 | 0.028 | -0.773 | -0.700 |
| cross_momentum | 14 | -0.594 | 0.026 | -0.669 | -0.600 |

Stres tickowy = dodatkowo 2 punkty na stronę i 0,05 U opłat. Są to jawne scenariusze, nie oszacowania rzeczywistej prowizji. Zmiana zbioru dostępnych wejść przy 1 s jest raportowana osobno w szczegółach. Nie ustalono pełnego efektu zerowych kwotowań na wszystkie historyczne zlecenia. To jedna wspólna doba rynkowa, nie kilkadziesiąt niezależnych prób; dodatni wynik tej doby nie wybiera kandydata. Średnie dotyczą tylko zdarzeń z dostępnym wejściem i wyjściem. Brak strony przy wyjściu w rzeczywistej strategii mógłby oznaczać pozostającą otwartą pozycję; nie uznajemy go za transakcję o zerowym wyniku. Ta selekcja dostępnych par może obciążać średnią i blokuje traktowanie tabeli jako wyniku całej polityki.

## 5. Odrzucenia i najwyżej dwóch kandydatów

| Rodzina | Dodatnie miesiące | Mniejsza liczba dodatnich rynków spośród dwóch okresów | Decyzja według wcześniejszych progów |
|---|---|---|---|
| trend | 1/6 | 3 | ODRZUCENIE w screeningu: niedodatnia średnia wczesna po progu kosztu; niedodatnia średnia późna po progu kosztu; późny stres kosztów niedodatni; mniej niż 60% dodatnich miesięcy |
| momentum | 3/6 | 3 | ODRZUCENIE w screeningu: niedodatnia średnia wczesna po progu kosztu; niedodatnia średnia późna po progu kosztu; późny stres kosztów niedodatni; mniej niż 60% dodatnich miesięcy |
| extreme_reversion | 3/6 | 3 | ODRZUCENIE w screeningu: niedodatnia średnia późna po progu kosztu; późny stres kosztów niedodatni; mniej niż 60% dodatnich miesięcy |
| breakout | 2/6 | 2 | ODRZUCENIE w screeningu: niedodatnia średnia wczesna po progu kosztu; niedodatnia średnia późna po progu kosztu; późny stres kosztów niedodatni; mniej niż 60% dodatnich miesięcy |
| false_breakout | 2/6 | 1 | ODRZUCENIE w screeningu: niedodatnia średnia wczesna po progu kosztu; niedodatnia średnia późna po progu kosztu; późny stres kosztów niedodatni; mniej niż 60% dodatnich miesięcy |
| volatile_momentum | 2/6 | 4 | ODRZUCENIE w screeningu: niedodatnia średnia wczesna po progu kosztu; późny stres kosztów niedodatni; mniej niż 60% dodatnich miesięcy |
| clock_breakout | 1/6 | 1 | ODRZUCENIE w screeningu: niedodatnia średnia wczesna po progu kosztu; niedodatnia średnia późna po progu kosztu; późny stres kosztów niedodatni; mniej niż 60% dodatnich miesięcy |
| cross_momentum | 3/6 | 2 | ODRZUCENIE w screeningu: niedodatnia średnia wczesna po progu kosztu; późny stres kosztów niedodatni; mniej niż 60% dodatnich miesięcy |

**Zero rodzin stosowanych łącznie na zadanych rynkach spełnia komplet wcześniej zapisanych progów.** Nie obniżono kryteriów ani nie zmieniono tego werdyktu.

Odrzucenie dotyczy konkretnej definicji i horyzontu 4h. Nie dowodzi, że cała klasa trend/rewersja/wybicie nie może działać. Dodatni wynik pojedynczego instrumentu lub godziny pozostaje hipotezą post hoc, nie niezależnym odkryciem.

### Jeden trop do niezależnej falsyfikacji: trend na OIL i US100

**Selekcja po obejrzeniu podgrup**, opisana oddzielnie w POSTHOC_SELECTION.md; nie przejście pierwotnej bramki i nie potwierdzony edge. Dwie konkretne wersje tej samej hipotezy zasługują na zamrożenie i przyszłą falsyfikację: EMA20/EMA50, horyzont 4h, OIL oraz US100. Parametrów nie zmieniono. Powód: dostateczna liczba zdarzeń w obu częściach, dodatni znak w obu okresach i 5/6 miesięcy, dodatni wynik w ustalonym stresie kosztów. Selekcja nie opiera się na najwyższym historycznym P&L. Oba przedziały niepewności zawierają zero, a mały margines po stresie może zniknąć po prawdziwych opłatach.

| Rynek trend | N wcz./póź. | Wcz. po progu U | Póź. po progu U | Późny stres U | Dodatnie miesiące | CI95 późne U | CI skorygowane U |
|---|---|---|---|---|---|---|---|
| OIL | 254/239 | 0.114 | 0.153 | 0.040 | 5/6 | [-0.081; 0.383] | [-0.267; 0.512] |
| US100 | 254/239 | 0.127 | 0.101 | 0.034 | 5/6 | [-0.113; 0.325] | [-0.217; 0.453] |

Nie wybrano ekstremalnej rewersji EURUSD (19/11 obserwacji), volatility-momentum GOLD (28/26) ani US500 (39/29), mimo niektórych wyższych średnich: za małe próby w części chronologicznej. Cross-momentum EURUSD ma dodatnie części i 5/6 miesięcy, ale w stresie pozostaje zaledwie około 0,007 U; odkładamy ten trzeci trop ze względu na mały margines względem nieznanych kosztów. To jakościowy, jawnie post hoc wybór dwóch przypadków do podważenia na nowych danych, nie kolejny test potwierdzający.

## 6. Minimalny kolejny pomiar rzeczywistej wartości

1. Zachować obecny forward zamrożonych strategii i zakończyć audyt jakości już wyznaczonego okna. Nie dobierać na nim nowych godzin, progów, instrumentów ani parametrów.

2. Dla ewentualnej nowej rodziny najpierw zapisać jeden protokół decyzji, horyzont, faktyczne koszty, minimalny istotny ekonomicznie efekt, regułę zatrzymania i plan wielokrotnych testów. Próbę rozpocząć po tym zamrożeniu. Nie przenosić hipotezy do DEMO.

3. Minimalne brakujące dowody do pełnego netto: poprawne UTC wybranego odcinka; historyczne Bid/Ask bez nieoznaczonych luk; rzeczywista taryfa prowizji/finansowania, specyfikacja i FX; kalibracja opóźnienia/poślizgu. Tylko dla strategii używających makro potrzebne są wersje kontekstu dostępne w chwili decyzji. Nie jest konieczna rozbudowa Supervisora do badań offline.

4. Na niezależnym okresie wymagamy dodatniego netto po pełnych kosztach oraz dodatniej dolnej granicy przedziału uwzględniającego zależności i liczbę kandydatów. Długość próby dobrać analizą mocy do minimalnego efektu i zmienności z odrębnego okresu kalibracyjnego; 100 transakcji czy 60 sesji same w sobie nie gwarantują mocy. Zakaz przerywania po pierwszym korzystnym wyniku.

Jeżeli nie ma kandydata, kolejne zadanie powinno być małym badaniem nowego mechanizmu (np. dłuższy horyzont na H4 z finansowaniem albo zdarzenia makro z archiwum as-of), z jawnym dopisaniem go do rejestru prób. Nie uruchomiono go automatycznie ani nie rozpoczęto kolejnego etapu infrastruktury.

## 7. DEMO i zbieranie danych — odrębne od wyniku badań

Odczyt tylko do odczytu: 2026-10-27T17:42:19.666617+00:00. Terminal połączony: True; otwarte pozycje: 1; wszystkie z brokerowym SL/TP: True; nierozstrzygnięte operacje: 1; silnik WAITING; kolektor COLLECTING. LIVE wyłączone. Obecność SL/TP nie dowodzi ciągłego BE/trailing. Recovery nie wdrożono, kwarantanny nie czyszczono.

**NO-GO dla pełnej odporności operacyjnej DEMO. GO dla tego screeningu eksploracyjnego. NO-GO dla twierdzenia o potwierdzonej przewadze lub wdrożenia nowych strategii.** Oddzielny raport zakończonego okna forward jest audytem jakości, nie źródłem selekcji nowych reguł.

## Odtworzenie i publikacja

Konfiguracja: protocol.py i PROTOCOL.md. Kod: screen.py, report.py, inventory.py. Testy: test_screen.py. Wyniki lokalne: results-v1/results.json, events.json, tick_events.json, latency_events.json. Źródła mają hashe w INPUT_HASHES.md; nie publikujemy surowych ticków, baz, rachunku ani szczegółów pozycji. Dokładne źródła danych trzeba posiadać lokalnie — sam publiczny zestaw kodu i tabel nie zastępuje danych. Gałąź research/edge-discovery-20261027; bez zmian aktywnego kodu. Przygotowanie synchronizacji nie oznacza pushu.

Wyniki po błędzie technicznym pierwszego uruchomienia zostały policzone ponownie bez zmiany reguł. Błąd dotyczył nadpisania pól rekordów tickowych, test regresji obejmuje ten przypadek.
