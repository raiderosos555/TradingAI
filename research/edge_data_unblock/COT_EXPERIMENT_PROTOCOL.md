# Zamrożony protokół COT: informacja ponad trend

Wersja 1, zapis przed obliczeniem zależności sygnał–przyszła cena. Jedna rodzina,
dwa rynki EURUSD/GBPUSD; wybór na podstawie dostępności pełnego szeregu Fed,
nie wyniku. COT pozostałych czterech kontraktów służy audytowi dostępności.
Nie używamy oglądanych wcześniej danych TMS z 2026 r. ani cohort forward.

## Pytanie i ograniczenie identyfikacji

Czy narastanie netto pozycji leveraged funds, zgodne z trendem, poprawia
przyszły ruch ceny względem identycznego trendu? Uzasadnienie: stopniowe
przepływy spekulacyjnego kapitału mogą podtrzymywać trend; alternatywnie
pozycjonowanie jest tylko spóźnioną reakcją lub oznaką zatłoczenia.
Nie odwrócimy znaku hipotezy po zobaczeniu wyniku.

Dane Fed są referencyjnymi noon buying rates, nie kwotowaniem realizacji
TradingAI. COT i Fed to obecne wersje historycznych szeregów. Brak pełnego
rejestru first-vintage i faktycznych publikacji **uniemożliwia certyfikację
point-in-time**. Wykonujemy warunkowy test predykcyjny z konserwatywnym
opóźnieniem, a nie pozorny backtest wykonalnego P&L. Dodatni wynik nie
potwierdza edge i musi zostać odtworzony na dowodach dostępności informacji.
Ścisły test wykonania/niezależne potwierdzenie pozostaje zablokowane.

## Stałe reguły

- Ceny: Fed EURUSD i GBPUSD w USD za jednostkę waluty, tylko 2010–2025.
  Rok 2010 rozgrzewa trend; decyzje od 05.01.2011 do końca 2025.
- COT: TFF futures-only, kody 099741 i 096742; wyłącznie leveraged funds.
  `net_share=(long-short)/open_interest`; zmiana od czterech raportów wcześniej.
  Wymagamy odstępu 26–30 dni i ciągłości kolejnych raportów 6–8 dni.
- Główne opóźnienie COT: najnowszy report_date nie późniejszy niż data decyzji
  minus 14 dni, wiek maksymalnie 21 dni. Opóźnienie jest założeniem badawczym,
  nie rzeczywistym published_at. Jedna z góry zapisana kontrola: 28 dni
  (wiek maksymalnie 35 dni). Nie wybieramy lepszego opóźnienia.
- Wyłączamy wszystkie raporty z okresów zakłóceń publikacji i odbudowy:
  01.10–15.11.2013, 18.12.2018–29.03.2019, 24.01–14.04.2023,
  30.09–31.12.2025. Wyłączenie dotyczy całego pięcioraportowego okna;
  nie przenosimy poprzedniej obserwacji przez lukę. To konserwatywne maski,
  a nie odtworzone release timestamps. Zmiana daty pozycji na poniedziałek
  jest dopuszczalna w granicach 6–8 dni; żadnego wpisania wtorku na siłę.
- A: znak 26-tygodniowej zmiany ceny; oba punkty referencyjne wyznaczamy
  as-of daty decyzji minus 14 dni i minus kolejne 182 dni, najbliższa starsza
  istniejąca cena maksymalnie 7 dni wcześniej. To opóźnienie uwzględnia
  tygodniowy tryb publikacji H.10 i święta, ale nie certyfikuje rewizji.
- B: identyczny kierunek A tylko gdy `direction * delta_net_share > 0`;
  inaczej cash. Zero/niepełne dane: brak obserwacji, nie syntetyczny kurs.
- C: long-only, short-only, cash oraz A pomnożone przez ekspozycję B.
- D: COT sprzed 52 raportów oraz 999 losowych filtrów o identycznej liczbie
  aktywnych obserwacji w każdym roku i kierunku A. Losowe przesunięcia maski
  w obrębie roku/kierunku; nie niezależne losowanie pojedynczych zysków.
  To kontrola statystyczna, nie wykonywalna strategia ze znajomością ekspozycji roku.
- Horyzonty 1 i 4 tygodnie. Niepokrywające się daty od środy 05.01.2011,
  odpowiednio krok 7/28 dni. Wejście i wyjście: referencyjna cena tego dnia;
  brak wartości oznacza pominięcie całej pary, bez przesuwania do lepszej sesji.
  Nie ma SL/TP, lewarowania ani wielkości lota: nie raportujemy R ani netto.

## Chronologia, niepewność i koszty

- 2011–2017: część odkrywcza; 2018–2021: stabilność/walk-forward;
  2022–2025: ostatni, wcześniej nieoglądany blok czasowy tego testu.
  Nie nazywamy go dowodem niezależnego point-in-time. Obserwacje przekraczające
  granice tych części odrzucamy. W corocznych foldach nic nie jest trenowane.
- Cztery testy podstawowe (2 rynki × 2 horyzonty), cztery wrażliwości (lag28).
  Rodzina ośmiu porównań; korekta Holm dla wszystkich, bez selekcji najlepszego.
- Główna statystyka: średni B−A w bps na wspólną okazję, dodatkowo B−A
  przy porównywalnej ekspozycji i rangowanie względem losowego filtra.
  95% CI: bootstrap całych kwartałów (4999 replik, seed 20261029).
  Test jednostronny przewagi: bootstrap wycentrowanych delt, korekta Holm8.
  Dodatkowa wrażliwość CI: bloki roczne; mało bloków oznacza dużą niepewność.
  Rynki są skorelowane; nie sumujemy ich obserwacji jako niezależnych.
- Oprócz surowego markoutu raportujemy odejmowane progi kosztowe:
  0 bps, 5 bps + 2 bps/tydzień, 15 bps + 5 bps/tydzień aktywnej ekspozycji.
  Są to hipotetyczne obciążenia, NIE oszacowane spready/swap TMS. Brak rzeczywistych
  kosztów wyklucza wniosek o ich przetrwaniu. Każda okazja jest osobną ekspozycją.
- Raport: liczba okazji i wejść B, bloki, średnie A/B/C/D, delta/CI/p/Holm,
  roczne foldy, trend wzrostowy/spadkowy, wysoka/niska zmienność wyznaczana
  wyłącznie z wcześniejszych cen i wcześniejszej mediany. Opisowy stosunek
  dodatnich/ujemnych markoutów i obsunięcie ich sumy nie są PF/DD rachunku.

Kandydat wymaga dodatniej delty po rygorystycznym progu kosztowym, dolnej CI>0,
Holm<0,05, przewagi nad kontrolą ekspozycji i placebo oraz stabilności w częściach
czasowych. Żaden wynik nie upoważnia do strojenia, wdrożenia DEMO lub LIVE.
Jeśli warunek nie jest spełniony, kierunek w tej zdefiniowanej postaci odrzucamy
do promocji; nie twierdzimy, że obalono wszystkie możliwe zastosowania COT.
