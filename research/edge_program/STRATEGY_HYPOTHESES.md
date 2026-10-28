# Hipotezy i protokół przed obliczeniami — edge-program-v1

Nowe pytanie: czy wskaźnik wnosi wartość ponad prostą cenę/zwrot/zmienność?
Nie powtarzamy rankingu starych strategii. Reguły poniżej i protocol.py zapisano
przed pierwszym obliczeniem wyników tej rundy. Stara historia pozostaje
eksploracyjna, także po chronologicznym podziale; nie jest nowym holdoutem.

## Cztery rodziny eksperymentów

| Rodzina | Rynek/horyzont/mechanizm | Reguła zamrożona | Benchmark i falsyfikacja |
|---|---|---|---|
| T: wygładzenie trendu | Wszystkie 7; D1, pięć kolejnych dostępnych świec. Stopniowe dostosowanie informacji i przepływów | Trzy osobne reprezentacje: sign(C−SMA20), sign(C−EMA20), sign(EMA12−EMA26). Średnie zawierają bieżący zakończony close. EMA seed pierwszą średnią; nie badamy parametrów MACD signal/histogram | W tych samych oknach sign(C/C[t−20]−1), dodatkowo BUY i cash. Zanik przyrostu względem prostej dynamiki falsyfikuje przydatność konkretnej transformacji, nie całą rodzinę trendu |
| R: RSI kontra proste ekstremum | EURUSD/GBPUSD/EURPLN; H4, 8h. Tymczasowa presja i rewersja | Wilder RSI14<30 BUY, >70 SELL, inaczej cash. Alternatywa bazowa: z=(C−średnia poprzednich 20 close)/sample SD; z<−2 BUY, z>2 SELL, inaczej cash | Wszystkie wspólne okazje pomiarowe, także cash; różnica średniego markoutu po progu. Liczba aktywnych sygnałów i ekspozycja osobno. RSI bez trwałego przyrostu nie uzasadnia kolejnego filtra |
| F: siła/zmienność przy wybiciu | GOLD/OIL/US500/US100; H4, 8h. Trend i reżim informacji | Bazowe wybicie close poza max high/min low poprzednich 20 H4. Osobno filtr Wilder ADX14≥25; osobno ATR14/C większe od mediany poprzednich 60 takich wartości. Nie łączymy filtrów | Bazowe wybicie bez filtra; dodatkowo losowy filtr o tej samej liczbie aktywnych pozycji w każdym 14-dniowym bloku. Sam spadek liczby transakcji nie dowodzi informacji. Brak lepszego wyboru niż losowe odrzucanie falsyfikuje filtr |
| X: fałszywe wybicie | GOLD/OIL/US500/US100; H4, 8h. Nieutrzymany ruch poza zakres i potencjalne zlecenia stop | High>max wcześniejszych20 high, close<ten max oraz low≥min wcześniejszych20 low → SELL. Symetrycznie low<min, close>min, high≤max → BUY. Świeca przebijająca obie strony wykluczona | W dokładnie tych samych oknach prosty fade −sign(C/C[t−1]−1), plus cash. Jeśli kierunek z geometrii świecy nie poprawia prostego fade, brak dodatkowej informacji |

To 21+3+8+4 = **36 zaplanowanych porównań**, bez szukania najlepszego okresu.
BB/z-score są algebraicznie tą samą miarą odchylenia przy zgodnym oknie i SD;
nie liczymy Bollingera jako dodatkowego niezależnego sygnału. D1 to surowe świece
brokera z możliwymi niedzielnymi fragmentami, a nie jednolite sesje cash.

Każde okno: zamknięcie i sygnał na i; pomiar od open[i+1] do open[i+1+h],
h=5 D1 lub 2 H4. Siatka okazji co h świec od indeksu 80, niezależna od wyniku
i sygnału. Bez nakładania wewnątrz reguły. H4 musi mieć ciągłe stemple od
sygnału do wyjścia; D1 przerwa między świecami najwyżej 4 dni. Nie interpolujemy.
Wykluczenie niekompletnych przyszłych okien jest analizą kompletnych przypadków,
nie wykonywalną regułą przewidującą brak danych. Brak SL/TP, sizingu i portfela.

## Czas, koszty, niepewność i próby

- Źródła: istniejące H4/D1; 14 plików, hashe ze wcześniejszego audytu. Raw
  27.04–23.10.2026; granica podprób 01.08.2026. Okna przecinające granicę
  odrzucamy. Dane forward nie są czytane do obliczenia wyników.
- Wartości w bps **Last**, nie P&L. Próg kosztu dla aktywnej pozycji: największy
  p95 spreadu z trzech starych okien 22.10 × point / cena wejścia. Stress:
  2× ten próg +2 bps kosztów +2 bps/dobę utrzymania. Cash koszt zero.
  To analiza wrażliwości, nie poświadczenie historycznego Bid/Ask, prowizji,
  finansowania, kwotowania czy rollowania. Nowe tabele brokera nie zastępują
  automatycznie pełnej osi historycznych kosztów.
- Główna statystyka: średnia różnica kandydat minus benchmark na wspólnych
  okazjach, w tym cash. Osobno wynik na aktywne okno; nie mieszać mianowników.
  Priorytet inferencji to późna część, ale nadal eksploracyjna.
- Bootstrap wspólnych 14-dniowych bloków, 4000 losowań, seed 20261028.
  CI95 różnicy i jednostronne przybliżone p dla przyrostu ponad zero; Holm36.
  Mała liczba bloków ogranicza kalibrację. Jednego bloku nie używamy do CI.
- Placebo: wspólne w blokach odwrócenia signed markoutów, koszty pozostają.
  Holm36 osobno. Dla 8 filtrów dodatkowo thinning-placebo z taką samą liczbą
  wejść/blok, Holm8; wynik diagnostyczny, nie nowa selekcja.
- Reżimy ustalone przed wynikiem: relatywna ATR14/C ponad/poniżej własnej
  mediany60 oraz znak zwrotu20. Raportujemy każdy przekrój bez wybierania
  „dobrego reżimu”. Wszystkie 36 prób i odrzucenia są publikowane.
- Bramka nominacji: dodatni przyrost w obu podpróbach i obu reżimach zmienności,
  dodatnia późna średnia stress, co najmniej 20 bloków późnych, Holm<0,05,
  przewaga nad placebo i poprawne ceny/koszty. Obecna krótka próba nie może
  spełnić bramki liczby bloków ani wykonania. To tani test odrzucający.

## Makro/news — trzy niezależne pytania, bez fikcyjnego backtestu

| ID | Sygnał i rynek | Okno i kontrola | Wymagane dowody |
|---|---|---|---|
| A1 NFP/CPI | EURUSD/GBPUSD: dodatni surprise US → SELL; GOLD i indeksy: hipoteza przeciwnego znaku, nie założenie ekonomiczne w każdym reżimie. Surprise względem konsensusu przed publikacją, skala z 24 wcześniejszych zdarzeń, abs(z)≥1 | Wejście po 5 min od pierwszego odbioru, wyjście po 30 min; porównanie z kierunkiem pierwszych 5 min i cash. Osobno NFP, headline CPI MoM oraz core CPI; nie scalać po wyniku | Pierwsze actual, pre-release forecast i revisions; gdy CPI headline/core dają przeciwne znaki, reguła NO TRADE zamrożona przed próbą. Bid/Ask, UTC i latency. Historyczne archiwum BLS nie dostarcza konsensusu |
| A2 Fed | Zmiana oczekiwanej ścieżki z futures stóp, nie różnica stopy Fed od poprzedniej decyzji; EURUSD/GBPUSD/GOLD/indeksy | Pełny 30-min pomiar surprise zakończony przed wejściem; wejście po 35 min, hold60min. Kontrola prostym pierwszym ruchem ceny. Odrębne statement/press conference | Terminowa krzywa futures i zamrożony sposób agregacji; gotowa ex-post ortogonalizacja akademicka nie jest sygnałem as-of. Opublikowane później współczynniki nie mogą wyciekać |
| B EIA | OIL: actual−konsensus crude inventories; dodatnie surprise → SELL; abs(z)≥1 z24 wcześniejszych | Po5min od odbioru, hold30min; benchmark pierwsza5min reakcja i cash; gasoline/distillates/cushing jako zapisany kontekst, bez dostrajania filtra | Pierwszy raport WPSR i właściwy forecast zmiany tygodniowej w mln baryłek. Nie mylić poziomu zapasów ze zmianą lub API z EIA. Potrzebne koszty i Bid/Ask po skoku |
| C real yields/OIS | GOLD: przeciwny znak 20-dniowej zmiany realnego US10Y; indeksy: ta sama hipoteza jako osobny test; EURPLN: wzrost oczekiwanej PLN−EUR stopy → SELL | Następna potwierdzona sesja po publikacji, hold5 sesji; benchmark cenowy trend20 i long-only | US real yields, polskie/eu OIS i znaczniki odbioru; ALFRED vintage day nie oznacza tickowego czasu. Stopy NBP/EBC i zrealizowane €STR nie są oczekiwaniami OIS |

Nie liczymy wyników A/B/C dopóki nie przejdą bramki wejść. Dostawcy, koszty,
licencje oraz najmniejsza próbka odbiorcza są w DATA_SOURCES.md i NEXT_EDGE_STEP.md.
Najwcześniejszy przyszły zbiór niezależny musi zaczynać się po zapieczętowaniu
tych reguł i mieć z góry ustalony koniec/liczbę zdarzeń, bez podglądania sukcesu.
