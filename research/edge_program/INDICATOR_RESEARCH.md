# Wartość dodana wskaźników — 28.10.2026

Pytanie brzmi: czy reprezentacja informacji poprawia prognozę lub decyzję
względem prostego benchmarku? Deterministyczny wskaźnik nie wnosi informacji
spoza historii ceny, z której powstał. Może być użytecznym skrótem wobec
ograniczonego modelu bazowego; taki przyrost trzeba jednak zmierzyć poza próbą.
Nie sumujemy głosów EMA/MACD/RSI jak trzech niezależnych źródeł informacji.

## Dowody wspierające efekty i ich ograniczenia

| Praca pierwotna | Rynek/horyzont i rzeczywisty wniosek | Granica zastosowania |
|---|---|---|
| [Brock, Lakonishok, LeBaron1992](https://www.technicalanalysis.org.uk/moving-averages/BrLL92.pdf) | DJIA1897–1986, dzienne średnie i wybicia; różnice warunkowych zwrotów wobec modeli bootstrap | Historyczna informacja nie dowodzi netto obecnego CFD ani trwałego wyboru reguły |
| [Bajgrowicz, Scaillet2012](https://www.sciencedirect.com/science/article/pii/S0304405X1200116X), [wersja autorów](https://www.scaillet.ch/pdfs/BajSca.pdf) | 7846 reguł DJIA I1897–VII2011; problemy selekcji ex ante i trwałości, małe koszty znoszą wyniki | Przeciwdowód do rankingu wskaźników po najlepszej krzywej; nie dowód, że każdy mechanizm na każdym rynku nie istnieje |
| [Park, Irwin2004 — przegląd](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=603481) | 92 nowsze badania:58 dodatnich,24 ujemne,10 mieszane; powracają snooping, wybór ex post i uproszczone koszty | Liczba pozytywnych publikacji nie jest prawdopodobieństwem sukcesu strategii; tu cytowana wersja WP2004 |
| [Moskowitz, Ooi, Pedersen2012](https://fairmodel.econ.yale.edu/ec439/mosk.pdf) | 58 futures/forward,1985–2009, trwałość własnego zwrotu na horyzontach1–12miesięcy | Najmocniejsza podstawa dla wolniejszych trendów, nie szczególnej EMA na OIL/US100 ani EMA20 intraday |
| [Kim, Tse, Wald2016](https://www.sciencedirect.com/science/article/pii/S1386418116301379) | 55 futures1985–2013; znaczenie volatility scaling, podobnie skalowany benchmark wyjaśnia część efektu | Kontrolować budżet ryzyka i long-only. ATR może zmieniać ekspozycję bez informacji kierunkowej |
| [Neely, Weller, Ulrich2009 / WP](https://fraser.stlouisfed.org/files/docs/publications/frbsl_wp/2006-046.pdf) | FX, dawne reguły MA/filter i późniejsze OOS; część premii zanika do początku lat90. | Oczekiwać zmienności reżimów i niepewności, nie stałego reklamowanego win rate |
| [Nagel2012](https://www.nber.org/system/files/working_papers/w17653/w17653.pdf) | Akcje USA1998–2010, krótkie rewersje jako kompensacja za płynność zależna od napięcia rynku | Klient CFD płacący spread nie otrzymuje automatycznie premii market makera |
| [Gao i in.2018](https://www.sciencedirect.com/science/article/pii/S0304405X18301351) | SPY1993–2013, relacja początku i końca sesji | Reguła cash-session, nie arbitralna godzina raw MT5; wymaga poprawnego UTC/DST i późniejszych lat |
| [Breedon, Ranaldo2011](https://www.snb.ch/public/asset/en/www-snb-ch/publications/research/working-papers/2011/working_paper_2011_04/publications0_en/working_paper_2011_04.n.pdf) | EBS1997–2007, godziny lokalne, przepływy FX i firm quotes | Inna płynność niż TMS, zwłaszcza GBPUSD; nie uprawnia do syntetycznego spreadu |
| [Lucca, Moench](https://www.newyorkfed.org/medialibrary/media/research/staff_reports/sr512.pdf) oraz [Kurov, Wolfe, Gilbert2021](https://doi.org/10.1016/j.frl.2020.101781) | Premia przed FOMC w starej próbie; późniejsze badanie wskazuje zanik po2015 | Konkretny przykład zaniku efektu; nie używać pre-FOMC drift jako dowodu post-news momentum |
| [Andersen i in.2003](https://public.econ.duke.edu/~boller/Published_Papers/aer_03.pdf) | FX1992–1998,5-min dane i oczekiwania MMS; surprise wiąże się ze skokiem ceny | To mocna podstawa mechanizmu informacyjnego, nie dowód kontynuacji po opóźnionym wejściu |
| [Bauer, Swanson2022/2023](https://www.nber.org/system/files/working_papers/w29939/w29939.pdf) | Zaskoczenia monetarne częściowo zależą od wcześniejszej informacji | Surprise Fed nie jest prostą zmianą stopy; ex-post oczyszczanie nie może wyciekać do decyzji |
| [Chebbi, Hmedat](https://onlinelibrary.wiley.com/doi/full/10.1002/ijfe.2747) | III2012–X2018, surprise zapasów i zwroty crude futures, różnice okresów | Potrzebny konsensus zmiany zapasów; sama zmienność po publikacji nie daje dodatniego netto |
| [Barsky i in.2021](https://www.chicagofed.org/publications/chicago-fed-letter/2021/464) | GOLD, realne stopy i oczekiwania, m.in.1971–2021; relacje różne w czasie | Mechanizm kosztu alternatywnego jest sensowny, lecz korelacja nie jest niezależnym sygnałem handlowym |
| [Tetlock2007](https://doi.org/10.1111/j.1540-6261.2007.01232.x) | Konkretny korpus WSJ1984–1999, presja i rewersja związana z pesymizmem tekstu | Nie przenosi się bezpośrednio na RSS/LLM; wymagane etykiety, deduplikacja i historia pierwszej dostępności |

To ukierunkowany przegląd źródeł pierwotnych, nie kompletny systematyczny
meta-review. Nie znaleziono w nim podstaw do uniwersalnego, opłacalnego po
kosztach rankingu RSI/MACD/ADX dla naszych siedmiu CFD.

## Co konkretnie porównujemy

| Rodzina | Co mierzy / możliwe zastosowanie | Kontrola wartości dodanej / status |
|---|---|---|
| EMA/SMA, trend | Wygładzony poziom, wolne dostosowanie informacji | D1/5bar vs znak20bar zwrotu i long/cash; wykonano21 porównań razem z MACD |
| RSI, mean reversion | Względna skala dodatnich/ujemnych zmian; ekstremum może też być trendem | FX H4/8h vs prosty z-score, wspólne okazje i cash; wykonano3 |
| MACD, momentum | Różnica wygładzeń tej samej ceny | Testowana linia12−26, bez mnożenia wariantów histogramu. Nie traktować jako niezależnego potwierdzenia EMA |
| ADX | Siła directional movement, bez kierunku | Cztery rynki, filtr≥25 vs Donchian i losowe odrzucenie tej samej liczby sygnałów |
| ATR | Skala ryzyka/zmienności, nie znak oczekiwanego zwrotu | Cztery rynki, filtr relatywnego ATR vs wybicie; nie badano nowego sizingu |
| Bollinger | Standaryzowane odchylenie ceny | Przy jednakowym oknie/SD pasma±2 odpowiadają z-score±2. To algebraiczny benchmark RSI, nie drugi niezależny edge |
| Donchian/breakout | Przekroczenie poprzedniego zakresu, potencjalna kontynuacja | Bazowa reguła dla8 testów filtrów; brak dowodu, że każdy parametr20 jest ekonomicznie wyjątkowy |
| False breakout | Wyjście poza zakres i nieutrzymanie ruchu | Cztery H4/8h porównania vs zwykły fade na tych samych oknach. Bez rekonstruowania niewidocznej kolejności high/low |
| Sesyjne | Przepływy przy otwarciu/zamknięciu, zmienna płynność | Nowego testu nie wykonano: brak dostatecznie długiego, potwierdzonego UTC i Bid/Ask. Nie stroimy godzin raw |
| Makro | Nowa informacja względem oczekiwań | NFP/CPI/Fed/EIA: potrzebne zgodne jednostki, first print i preforecast; mechanizmy A/B zdefiniowane, bez fikcyjnego wyniku |
| Fundamenty/międzyrynkowe | Realny koszt pieniądza, USD, carry i relacje aktywów | GOLD/US yields, EURPLN/PLN−EUR OIS; porównanie do prostego trendu po dostępności danych. Wysoka korelacja indeksów nie dowodzi stacjonarnej pary |

Najsilniejsze podstawy badawcze mają **wolniejsze trendy i reakcja na surprise
makro**, z innymi ograniczeniami: trendy wymagają lat i finansowania, makro
wymaga PIT i sprawdzenia ruchu pozostałego po opóźnieniu. Rewersje mają
uzasadnienie mikrostrukturalne, ale klient CFD ponosi inny koszt płynności.

Wykonane nowe testy nie wykazały istotnej wartości dodanej po Holm36.
To nie dowód równości ani nieistnienia całych rodzin: próbka jest krótka,
a nieliczne różnice sygnałów powodują szerokie lub zdegenerowane przedziały.
Wyniki liczbowe, wszystkie próby i reżimy są w EXPERIMENT_RESULTS.md.
