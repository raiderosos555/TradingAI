# RESEARCH_REVIEW — mechanizmy rynku, 27.10.2026

Wykonano ukierunkowany przegląd źródeł pierwotnych: publikacji naukowych,
wersji autorów oraz banków centralnych. To nie kompletny przegląd systematyczny
całej literatury ani zapewnienie, że efekt istnieje w 2026 r. Przegląd i dobór
mechanizmów poprzedzają nowe obliczenia. Wcześniejsze EMA20/50 OIL/US100 nie
stanowią kryterium wyboru. Nie pobierano danych cenowych z publikacji jako
zamiennika kwotowań naszego brokera.

## Najważniejszy wniosek zewnętrzny

Najmocniejsze podstawy do postawienia hipotez mają: wolniejsze trendy,
zaskoczenia względem oczekiwań makro, informacje o zapasach ropy, kompensacja
za dostarczanie płynności i specyficzne przepływy sesyjne. **Istnienie reakcji
ceny nie oznacza możliwości wejścia po tej reakcji z dodatnim netto.** Ocena
szans dla naszego brokera jest wnioskiem badawczym, nie wynikiem cytowanych prac.

## Badania i granice transferu

| ID / źródło pierwotne | Data, dane i horyzont | Wniosek źródła | Koszty, ograniczenie i falsyfikacja u nas |
|---|---|---|---|
| S1 [Moskowitz, Ooi, Pedersen — Time series momentum](https://fairmodel.econ.yale.edu/ec439/mosk.pdf) | JFE 2012; 58 płynnych futures/forward, 1985–2009; momentum 1–12 miesięcy | Trwałość własnych zwrotów i efekty portfelowe między klasami aktywów | Nie dowodzi EMA H1 ani netto CFD. Sprawdzić przewagę sygnału nad równie skalowanym long-only i finansowanie; zanik po tym porównaniu obala transfer. |
| S2 [Kim, Tse, Wald — Time series momentum and volatility scaling](https://www.sciencedirect.com/science/article/pii/S1386418116301379) | 2016; 55 futures, 1985–2013 | Znaczna część wyniku zależy od skalowania zmiennością; podobne skalowanie benchmarku zmniejsza wyjątkowość TSMOM | Kontrargument do prostego utożsamienia dodatniej krzywej z informacją sygnału. Dlatego benchmark ma te same okna i ekspozycję. |
| S3 [Nagel — Evaporating Liquidity](https://www.nber.org/system/files/working_papers/w17653/w17653.pdf) | WP 2011 / RFS 2012; akcje USA, 1998–2010, krótkie rewersje | Wynagrodzenie za dostarczanie płynności zależy od napięcia rynku i VIX | Płacący spread klient CFD nie jest dostawcą płynności. Transfer na indeks/FX jest słabszą hipotezą. Brak rewersji po spreadzie albo wyjaśnienie bounce bid/ask ją obala. |
| S4 [Bajgrowicz, Scaillet — Technical trading revisited](https://www.sciencedirect.com/science/article/pii/S0304405X1200116X) | JFE 2012; DJIA, dzienne reguły, 7 846 wariantów; źródło opisuje historyczne badanie długookresowe. Pełny PDF nie otworzył się ponownie; dokładny zakres dat nie jest tu niezależnie potwierdzony | Wybór skutecznych reguł ex ante i trwałość są problemem; niskie koszty znoszą historyczną rentowność | Nie jest dowodem przeciw każdemu rynkowi, ale wymusza koszt, benchmark, wielokrotność i prawdziwy holdout. Nie używamy rankingu najlepszego wskaźnika. |
| S5 [Lo, Mamaysky, Wang — Foundations of Technical Analysis](https://www.nber.org/papers/w7613) | WP / JF 2000; akcje USA 1962–1996, rozkłady dziennych zwrotów | Niektóre obiektywnie rozpoznawane wzorce zawierają informację warunkową | Informacja w rozkładzie nie jest automatycznie transakcją po kosztach; brak przewagi nad prostą kontrolą obala ekonomiczne zastosowanie. |
| S6 [Andersen, Bollerslev, Diebold, Vega — Micro Effects of Macro Announcements](https://public.econ.duke.edu/~boller/Published_Papers/aer_03.pdf) | AER 2003; pięć kursów USD, 5-min kwotowania 03.01.1992–30.12.1998, oczekiwania MMS i realizacje | Zaskoczenia wywołują szybkie, asymetryczne skoki cen | Dotyczy odkrywania ceny, nie gotowej strategii CFD. Po wykluczeniu pierwszego skoku i doliczeniu kosztów dalszy ruch może wynosić zero. Wymagane oczekiwania znane przed publikacją. |
| S7 [Gao, Han, Li, Zhou — Market intraday momentum](https://www.sciencedirect.com/science/article/pii/S0304405X18301351) | JFE 2018; SPY TAQ 01.02.1993–31.12.2013, półgodzinne odcinki sesji USA | Początkowy ruch, obejmujący odniesienie do wcześniejszego zamknięcia, pomaga przewidywać ostatnie pół godziny | Nie należy zastępować cash open godziną raw CFD. U nas niezweryfikowane UTC i brak długiego M30/BidAsk blokują replikację; koszt i późniejsze lata mogą usunąć efekt. |
| S8 [Breedon, Ranaldo — Intraday patterns in FX returns and order flow](https://www.snb.ch/public/asset/en/www-snb-ch/publications/research/working-papers/2011/working_paper_2011_04/publications0_en/working_paper_2011_04.n.pdf) | SNB WP 2011-04, tekst XI 2010; EBS I 1997–początek VI 2007, sześć par, agregacja godzinowa | Efekty godzin lokalnych i przepływu zleceń; w próbie autorów strategia EURUSD | Firm bid/offer i transakcje rynku międzybankowego; udział EBS w GBPUSD poniżej 5%. Nie certyfikuje spreadu CFD. Bez UTC/DST nie testujemy „Londynu”. |
| S9 [Lucca, Moench — The Pre-FOMC Announcement Drift](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr512.pdf) | WP 2011, rewizja 2013 / JF 2015; USA IX 1994–III 2011, 24h przed FOMC | Nadwyżkowe zwroty przed zaplanowanymi decyzjami | To premia przed wydarzeniem, nie post-news momentum ani sygnał z później odczytanego komunikatu. Mało zdarzeń i ryzyko zmiany strukturalnej. |
| S10 [Kurov, Wolfe, Gilbert — The disappearing pre-FOMC announcement drift](https://doi.org/10.1016/j.frl.2020.101781) | FRL 2021; przedłużenie próby do XII 2019 | Autorzy wskazują zanik badanego efektu po 2015 r. | Konkretny kontrprzykład dla trwałości anomalii. Nie wdrażamy historycznego efektu kalendarzowego bez nowego testu. |
| S11 [Chebbi, Hmedat — Inventory information arrival and the crude oil futures market](https://onlinelibrary.wiley.com/doi/full/10.1002/ijfe.2747) | Online 2022 / tom 2024; 27.03.2012–02.10.2018; tygodniowe informacje o zapasach ropy | Zaskoczenia zapasów wiążą się odwrotnie ze zwrotami ropy; zależność zmienia się między okresami | Sama zmiana zapasów bez oczekiwań nie jest surprise. Brak kontynuacji po pierwszej reakcji, koszty lub odmienne wiadomości o produktach obalają prosty kierunkowy transfer. |
| S12 [Bjursell, Gentle, Wang — Inventory announcements, jump dynamics, volatility and trading volume](https://www.sciencedirect.com/science/article/pii/S0140988314002771) | Energy Economics, publikacja po 2014; intraday I 1990–I 2008; ropa, heating oil, gaz NYMEX | Wydarzenia zapasowe łączą się ze skokami, wolumenem i zmianą zmienności | Wyższa zmienność nie wyznacza kierunku ani dodatniego netto. Test skoku i test kontynuacji to odrębne pytania. |
| S13 [Barsky i in. — What Drives Gold Prices?](https://www.chicagofed.org/publications/chicago-fed-letter/2021/464) | Chicago Fed Letter 464, XI 2021; m.in. kwartalne 1971Q1–2021Q1 oraz roczne/dzienne specyfikacje | Realne stopy, inflacyjne oczekiwania i warunki makro wiążą się ze złotem; relacje zmieniają się w czasie | To regresje zależności, nie bezpośredni algorytm intraday. Bez historycznych real yields/oczekiwań as-of i niezależnej predykcji — nieweryfikowalne u nas. |
| S14 [Gatev, Goetzmann, Rouwenhorst — Pairs Trading](https://www.nber.org/papers/w7032) | WP 1999: akcje USA 1962–1997, formacja par i półroczny handel; późniejsza publikacja RFS 2006 ma inną wersję próby | Wyniki relative value przewyższają konserwatywne koszty w znacznej części historycznej próby; część efektu mikrostrukturalna | Akcje dobrane jako pary nie są tym samym co US100/US500. Wysoka korelacja nie dowodzi stacjonarności spreadu; dwie nogi podwajają problemy kosztu i wykonania. |
| S15 [Neely, Weller, Ulrich — Adaptive Markets Hypothesis](https://fraser.stlouisfed.org/files/docs/publications/frbsl_wp/2006-046.pdf) | Rewizja WP 08.03.2007 / JFQA 2009; historyczny FX, reguły z lat 70./80. i późniejsze prawdziwe OOS | Część dawnych premii MA/filter zanika do początku lat 90.; niepewność średnich jest wysoka | Dowód na potrzebę monitorowania zmian, nie zgoda na ciągłe strojenie. Pełnego kalendarza każdej podpróby nie odtwarzano. |
| S16 [Tetlock — Giving Content to Investor Sentiment](https://doi.org/10.1111/j.1540-6261.2007.01232.x) | JF 2007; kolumna WSJ, 1984–1999; dzienne dane | Pesymizm tekstu wiąże się z presją cenową i późniejszą rewersją | Konkretny korpus, nie dowód dla RSS BBC ani odpowiedzi LLM. Zmiana języka, powtórzenia newsów i pierwsza dostępność mogą całkowicie zmienić wynik. |

Nie twierdzimy, że wszystkie prace wykazały dodatni wynik po rzeczywistych
kosztach. W wielu przypadkach mierzą reakcję, korelację albo zwrot brutto.
S4/S15 są ostrzeżeniem przed nietrwałością, S2 przed myleniem alokacji ryzyka z
sygnałem, S10 przed przenoszeniem starej anomalii na nowy okres. Braki dostępu
do pełnych tabel i zakresów są jawnie oznaczone, zamiast uzupełniane domysłem.

## Wskaźniki: pomiar, rola, falsyfikacja

Poniższe definicje są operacyjną interpretacją miar, nie rankingiem ich
rentowności. [Dokumentacja MetaQuotes](https://www.mql5.com/en/docs/indicators)
potwierdza dostępność implementacji; dokumentacja nie jest dowodem edge.

| Miara | Co mierzy / rola | Co rzeczywiście uzasadnia jej użycie i co je obala |
|---|---|---|
| SMA / EMA | Średnia okna / średnia z malejącymi wagami; stan trendu i wygładzenie | S1 wspiera mechanizm trendu w innych horyzontach, nie magiczny okres. Wymagane porównanie z samym znakiem zwrotu i long-only; S2/S4/S15 ograniczają transfer. |
| RSI | Stosunek wygładzonych wzrostów do spadków, skala 0–100 | Miara asymetrii ruchów. „Wykupienie” może oznaczać silny trend, nie pewną rewersję. Dodatnia inkrementalna wartość poza prostym odchyleniem ceny musi być zmierzona. |
| MACD | Różnica dwóch EMA i jej linia wygładzenia | Inna parametryzacja trendu, a nie niezależny głos od EMA. Odrzucić jako dodatkowy filtr, gdy nie poprawia niezależnego wyniku względem prostego trendu. |
| ADX / DI | Wygładzona względna siła directional movement względem true range; ADX nie podaje znaku | Możliwy filtr reżimu, nie prognoza zwrotu. Próg wybrany po wyniku zwiększa data snooping. W tej rundzie nie szukamy „najlepszego ADX”. |
| ATR | True range uwzględniający poprzedni close, następnie wygładzenie | Skala ruchu/ryzyka; nie kierunek. Zmienność może pomóc sizingowi bez przewagi sygnału (S2). Trzeba podać SMA/RMA i sposób warm-up. |
| Bollinger / z-score | Odległość od średniej względem odchylenia; szerokość pasma opisuje zmienność | Nadaje jednoznaczną definicję ekstremum; przekroczenie nie dowodzi powrotu. Trend i news mogą utrzymać ekstremum. |
| Donchian | Maksimum/minimum wcześniejszego zakresu, bez bieżącej świecy | Jednoznaczna definicja wybicia. Dowód ekonomiczny dla konkretnego progu słabszy niż ogólne momentum; S4 obejmuje ostrzeżenie o regułach technicznych. |
| Efficiency ratio | abs(Ct−Ct−n) / suma abs zmian po drodze | Opis kierunkowości; prosty filtr oddzielający oscylację od trendu. Nie optymalizujemy progu po wynikach. |
| Zmienność zrealizowana / spread względny | Ryzyko ruchu / bezpośredni koszt cenowy i stan kwotowań | Są warunkami wykonalności. Wysoka zmienność sama nie jest kierunkowym edge; spread musi pochodzić z Bid/Ask. |
| Wolumen, OBV, VWAP, imbalance | Aktywność/rozkład obrotu lub presja zleceń | Tick_volume CFD nie jest globalnym wolumenem giełdy ani order flow. Bez właściwego feedu nie wolno nazywać go instytucjonalnym popytem. |
| Surprise makro | (pierwszy actual − forecast dostępny wcześniej) / skala historycznych niespodzianek | S6/S11 uzasadniają reakcję na nową informację. Brak wcześniejszej prognozy, rewizji lub wejścia po pierwszym skoku obala rzetelność testu. |
| Real yield / różnica stóp / krzywa futures | Koszt alternatywny złota, oczekiwania polityki, carry i zapasy | S13 wspiera mechanizm złota. Nie mamy dowodu, że różnica stóp banków centralnych jest zarabiającym carry CFD EURPLN; wymagane forwards i rzeczywiste finansowanie. |

## Wnioski według rynku

- **GOLD:** wolniejsze momentum jako hipoteza cenowa; realne stopy i dolar jako
  mechanizm fundamentalny, wymagający nowego as-of źródła. Intraday po CPI/Fed:
  znak zależy także od reakcji stóp i oczekiwań, więc sam „wysoki CPI = BUY” odpada.
- **US500 / US100:** premia rynkowa jest koniecznym benchmarkiem; osobno
  sesyjna kontynuacja, ryzyko makro i relative value. Nie zakładamy stacjonarności
  różnicy indeksów o innych wagach sektorowych.
- **OIL:** zapasy względem konsensusu i struktura terminowa mają bardziej
  specyficzny mechanizm niż dowolny oscylator. Prostego wybicia cenowego można
  tanio użyć do odrzucania, ale nie zastępuje ono informacji o zapasach.
- **EURUSD / GBPUSD:** zaskoczenia makro, lokalne godziny przepływu i czasowe
  odchylenia od równowagi; skoki po newsach mogą być zbyt szybkie dla naszego wejścia.
- **EURPLN:** lokalna polityka NBP/EBC, oczekiwana różnica stóp, płynność i risk-off.
  Brak bezpośredniego dowodu rentowności EURPLN w cytowanych pracach; transfer
  z dużych par FX otrzymuje niższą ocenę, a spread może dominować mały ruch.

Najpierw badamy mechanizm i odpowiedni horyzont. Nie sumujemy EMA, MACD i RSI
jako trzech niezależnych dowodów. Makro/news mają dostarczać dostępne wtedy
informacje, a nie późniejszą narrację wyjaśniającą wykres.
