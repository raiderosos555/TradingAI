# Rejestr mechanizmów — wersja 1

Definicje ustalono po przeglądzie literatury i dostępności danych, przed pierwszym
uruchomieniem nowych eksperymentów. Historia była już oglądana w innych badaniach:
to rejestr eksploracyjny, nie niezależna prerejestracja. Wersję parametrów zawiera
`protocol.py`; nie uruchamiamy siatki wariantów. „Wejście” w testach OHLC oznacza
pomiar od kolejnego open Last, a nie symulowane zlecenie brokera.

## Pierwsze sześć mechanizmów

| ID / zakres | Mechanizm, dane i wskaźniki | Dokładny sygnał i pomiar | Koszt i falsyfikacja |
|---|---|---|---|
| M1 / uniwersalny: wszystkie 7 | Powolne dostosowanie do informacji i przepływy utrzymujące trend; S1/S2/S15. D1 Last; znak zwrotu, bez EMA | Znak C[t]/C[t−126]−1. Po zamknięciu t pomiar od open[t+1] do open[t+6], pięć dostępnych D1; kolejne zdarzenie dopiero po wyjściu. 126 świec nie jest dokładnie półroczem: FX zawiera niedzielne świece. Brak skalowania zmiennością; kontrola long-only ma identyczną ekspozycję i okna | Spread, finansowanie, rollover i skoki kontraktów. Brak przewagi względem long-only, niestabilny znak w podpróbach lub zanik po rzeczywistych kosztach obala tę implementację; nie obala całej literatury TSMOM |
| M2 / klasa FX: EURPLN, EURUSD, GBPUSD | Tymczasowa presja płynnościowa i powrót ceny; transfer S3 na FX jest słaby. H1 Last, z-score i efficiency ratio | Średnia i sample SD z 20 wcześniejszych close, bez bieżącego. abs(z)>2 i ER20<0,3; sygnał przeciwny do z. Pomiar następne open → open dwie godziny później. Sygnał w raw godzinach 6–19, cały pomiar tego samego raw dnia, bez luk. To filtr zegara brokera, nie etykieta Londynu | Spread i poślizg mogą pochłonąć całą rewersję. Brak ruchu przeciw ekstremum lub przewaga tylko przed odjęciem spreadu falsyfikuje zastosowanie. Nie nazywamy klienta CFD dostawcą płynności |
| M3 / surowce: GOLD, OIL | Napływ informacji wyprowadza cenę z zakresu; dowody dla tej konkretnej reguły słabsze niż dla wolnego trendu. H4, Donchian, SMA ATR | Close poza high/low poprzednich 20 H4, ATR14 >1,25 × mediana poprzednich 60 wartości ATR. Kierunek wybicia. Następne open → open po dwóch H4, wymagane ciągłe 8h i ciągłość od sygnału. Bez SL/TP lub wyboru najlepszego hold | Spread, skoki, finansowanie. Zanik po kosztach albo brak przewagi wobec long-only i placebo obala tę implementację. ATR jest stanem zmienności, nie drugim głosem za kierunkiem |
| M4 / para indeksów: US100–US500 | Wspólne czynniki mogą tworzyć przejściowe odchylenia; S14 tylko analogią z akcji. H1 zsynchronizowane po raw czasie, bez forward fill | OLS log(US100)=a+b log(US500) z poprzednich 120 close. Bieżący residual / sample SD residuali treningowych, abs(z)>2, 0,25≤b≤4. Kierunek przeciwny do z; zamrożone b przez cztery godziny od kolejnego open. Zwrot pary = d×(r100−b×r500)/(1+abs(b)). Ten sam raw dzień i ciągłe godziny | Ważone koszty obu nóg, margin, minimalny lot, niesynchroniczne wykonanie. Brak rewersji, dryf relacji lub koszt dwóch nóg obala transfer. Korelacja nie dowodzi kointegracji; nie twierdzimy, że parametry modelu są stacjonarne |
| M5 / USD makro: EURUSD, GBPUSD | Reakcja na nowe informacje o polityce/wzroście; S6. As-of konsensus i pierwszy actual dla US nonfarm payrolls, ticki obu stron, potwierdzony UTC | Pierwszy actual minus ostatni forecast otrzymany przed publikacją; skala SD 24 wcześniejszych surprises. abs(z)≥1; dodatni surprise → SELL pary USD-quote, ujemny → BUY. Wejście najwcześniej 5 minut po odebraniu actual, wyjście 30 minut później. Pomiar kontynuacji pomija początkowy skok | NIEWERYFIKOWALNA: brak sparowanych publikacji as-of i historii 24 surprises. Falsyfikacja: brak ruchu po opóźnionym wejściu, odwrotny znak w reżimie lub koszt wyższy od kontynuacji. Dane revised actual nie zastępują pierwszego odczytu |
| M6 / OIL: zapasy EIA | Zaskoczenie podażą wobec konsensusu; S11/S12. Pierwsza publikacja crude inventories, prognoza, jednostki i rewizje | Surprise actual−forecast / SD 24 wcześniejszych; abs(z)≥1, kierunek przeciwny do surprise. Pierwsze wykonywalne Bid/Ask co najmniej 5 min po odbiorze, wyjście po 30 min. Jedna pozycja; równoległe informacje o produktach zapisane jako kontekst, bez dostrajania filtra | NIEWERYFIKOWALNA: EIA Today in Energy RSS nie zawiera takiej historii konsensusu. Falsyfikacja: cały efekt przed wejściem, brak trwałości po spreadzie, silne sprzeczne informacje. Wyższa zmienność nie wystarcza |

W M1–M4 nie ma sizingu, limitów portfela, SL/TP, BE ani trailingu. To testy
oczekiwanego ruchu w ustalonym horyzoncie, a nie zamiennik zintegrowanego replay.
Próba obejmuje 13 relacji mechanizm–rynek oraz 4 agregaty. Agregat waży zdarzenia
równo, więc rynki z częstszymi sygnałami mają większą wagę; nie jest portfelem.

## Pozostałe konkretne hipotezy, bez eksperymentów w tej rundzie

| ID / zakres | Definicja, mechanizm i horyzont | Wymagania, koszt i falsyfikacja |
|---|---|---|
| M7 / US500, US100 | S7: znak zmiany od poprzedniego cash close do 10:00 New York; wejście 15:30, wyjście 16:00 tego dnia, kierunek początkowego ruchu | Cash calendar, DST, M1 i Bid/Ask; spread na zamknięciu. Obala brak przewagi nad long-only i losowym kierunkiem przy tych samych godzinach. Nieweryfikowalne z obecnym raw UTC |
| M8 / EURUSD, GBPUSD | S8: SELL waluty lokalnej w jej godzinach; osobno BUY EURUSD/GBPUSD 09–12 New York oraz SELL 09–12 Europe/London, bez łączenia nakładających się okien | Prawidłowy UTC/DST i sesyjne spready. Spread i niestabilność kierunku między latami falsyfikują. Nie utożsamiamy różnych lokalnych rynków; implementacja wymaga prerejestracji konfliktów okien |
| M9 / GOLD | S13: przeciwny znak 20-dniowej zmiany realnego rentownościowego benchmarku US 10Y; decyzja po pierwszym odebranym zamknięciu danych, wejście następnej sesji, hold 5 sesji | Licencjonowany lub jawny as-of real yield i ceny USD; koszt finansowania. Sama korelacja równoczesna nie wystarcza: predykcja musi pokonać GOLD long-only i cenowe momentum |
| M10 / EURPLN | Oczekiwana polityka: zmiana 1M oczekiwanej różnicy stóp PLN−EUR z krzywych OIS; dodatnia zmiana → SELL EURPLN, hold tydzień od następnej sesji | Historyczne as-of OIS PL/EUR, NBP/EBC i właściwy carry CFD; proxy stopą bieżącą niedopuszczalne. Brak predykcji po finansowaniu lub risk-off obala mechanizm. Bez danych nieweryfikowalne |
| M11 / indeksy, GOLD, OIL | S16 jako analogia: zaskoczenie sentymentu pełnych wiadomości względem poprzednich 30 dni; zamrożony model tekstowy, skrajne decyle, wejście po 15 min, kontynuacja do 1h i odrębna rewersja 1h–D1 | Pierwszy odbiór, pełen tekst, deduplikacja, wersja modelu, brak leakage szkoleniowego. BBC RSS nie wystarcza; brak dodatkowej informacji poza ruchem ceny i kosztami obala. Kierunek zależny od rynku musi być zdefiniowany przed testem |

M7–M11 są projektami falsyfikacji, nie zleceniem wdrożenia źródeł ani nową
kampanią optymalizacji. Najpierw trzeba ocenić jeden brakujący zbiór, który
odblokuje wartościową hipotezę.

## Ranking przed obliczeniami

Skala 0–3, większe lepsze. Kolumny koszt/overfit oznaczają odporność na problem,
nie jego wysokość. To jawna ocena badacza, nie estymowane prawdopodobieństwo zysku.
„Dane” oznaczają obecne dane do wstępnego pomiaru, nie certyfikat net backtestu.

| ID | Dowody zewn. | Dane as-of | Mechanizm | Broker | Koszt | Overfit | Walidacja | Decyzja przed wynikiem |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| M1 | 3 | 2 | 3 | 2 | 1 | 2 | 2 | Tani test cenowy; priorytet wolnego horyzontu |
| M2 | 1 | 2 | 2 | 2 | 1 | 1 | 2 | Tani test odrzucający; słaby transfer płynności |
| M3 | 1 | 2 | 2 | 2 | 1 | 1 | 2 | Tani test odrzucający; odrębne wybicie |
| M4 | 1 | 2 | 2 | 1 | 1 | 1 | 1 | Tani test pary, bez deklaracji kointegracji |
| M5 | 3 | 0 | 3 | 1 | 0 | 2 | 1 | Wybrany mechanizm; bramka danych zamknięta |
| M6 | 2 | 0 | 3 | 1 | 0 | 2 | 1 | Wybrany mechanizm specyficzny OIL; bramka zamknięta |
| M7 | 2 | 0 | 2 | 2 | 1 | 2 | 1 | Odłożony: UTC, cash calendar, M1 |
| M8 | 2 | 0 | 2 | 2 | 1 | 2 | 1 | Odłożony: UTC i sesyjny spread |
| M9 | 2 | 0 | 3 | 2 | 1 | 2 | 1 | Odłożony: historyczne real yields as-of |
| M10 | 0 | 0 | 2 | 1 | 0 | 1 | 0 | Odłożony: OIS i carry, słabe bezpośrednie dowody |
| M11 | 1 | 0 | 2 | 1 | 0 | 0 | 0 | Odłożony: pełny korpus i model zamrożony przed próbą |

## Protokół statystyczny i kosztowy

- Wszystkie wyniki z istniejących danych są eksploracyjne. Okres sygnałów od
  27.04.2026, granica chronologiczna 01.08.2026, koniec 24.10.2026, po raw czasie.
  Zdarzenia przekraczające granicę podpróby są wykluczone. Żaden podzbiór nie jest
  nowym niezależnym holdoutem. Forward cohort nie służy do wyboru parametrów.
- Brak nakładania ekspozycji wewnątrz jednej relacji mechanizm–rynek; zależności
  między rynkami pozostają. Liczba zdarzeń nie jest liczbą niezależnych transakcji.
- Wyniki w bps Last (1 bp = 0,01%). Próg kosztu to największy z trzech zaobserwowanych
  p95 spreadu 22.10 pomnożony przez point i podzielony przez cenę wejścia. To
  scenariusz minimalnego progu, bez dowodu historycznej reprezentatywności.
- Stress: 2× ten próg +2 bps łącznie za prowizję/poślizg oraz 2 bps za każde
  24h czasu utrzymania, proporcjonalnie. Dla pary spready ważone bezwzględnymi
  ekspozycjami, dodatki naliczane na sumę notional. To założenia wrażliwości,
  nie zmierzone taryfy ani konwersja Last na Bid/Ask.
- Benchmark: zawsze long (dla pary long spread) w identycznych oknach, kosztach
  i bezwzględnej ekspozycji; gotówka =0. Placebo: odwrócenia kierunków wspólne
  dla 14-dniowych bloków, przy zachowaniu cen, terminów i kosztów; 4000 losowań,
  seed 20261027. Założenie symetrii znaków nie jest dowodem losowości rynku.
- Bootstrap blokowy 14 dni, wspólny między rynkami; 4000 powtórzeń, percentylowy
  CI95 średniej po progu. P jednostronne z wycentrowanego bootstrapu średniej,
  oddzielne p placebo. Holm dla 17 zaplanowanych testów późnej podpróby,
  osobno dla obu rodzajów p. Wcześniejszych nieznanych prób nie „naprawia” Holm.
- Mało bloków oznacza niestabilną inferencję. Nie ogłaszamy edge nawet przy
  nominalnym p<0,05; do nominacji potrzeba obu podprób dodatnich, przewagi nad
  long-only, odporności stress, dostatecznej liczby bloków i wykonywalnych cen.
