# Jeden następny krok: mały pakiet EIA + OIL z dowodami dostępności

**Pozyskać i sprawdzić pierwszych12 kolejnych, datowanych publikacji WPSR od01.03.2026
oraz odpowiadające im okna Bid/Ask OIL u TMS [-10,+60]min.** Nie wybierać
dat po wielkości ruchu. Ten zbiór ma największą wartość jako następny test
nowej informacji, bo dotyczy konkretnego bilansu surowca i nie wymaga
dostrajania obecnych, słabych filtrów IV.

Źródła: [oficjalne archiwum EIA](https://www.eia.gov/petroleum/supply/weekly/archive/)
oraz ograniczone copy_ticks_range TMS. Pierwszy odbiór danych musi być
udowodniony datowanym artefaktem/publication metadata, a quote time powiązany
z UTC; harmonogram sam nie wystarczy. Pobranie surowych okien tickowych może
być większe od dotychczasowych sond, więc wymaga uzgodnionego limitu i zgody
przed kampanią. W tej rundzie nie uruchomiono tego pobrania.

Każdy rekord: release ID, data referencyjna, rzeczywisty published_at/received_at,
first-print crude ex-SPR, gasoline/distillates, production/imports, units,
revisions, źródło i hash. Ceny: osobne Bid/Ask/Last/flags, kolejność, jakość
stron, przerwy, specyfikacja kontraktu, prowizja/roll/swap jeśli dotyczy.
Brak dowodu czasu lub first print oznacza nieweryfikowalne zdarzenie, nie
oszacowany timestamp ani wypełnienie poprzednią wartością.

Pierwsze pytanie możliwe bez kupowania konsensusu: **czy znak zmiany zapasów
actual wnosi informację ponad pierwszy5-min ruch ceny do dalszego30-min
markoutu?** To model actual-context, nie surprise. Zamrozić osobny protokół
przed policzeniem odpowiedzi: kierunek przeciwny do zmiany zapasów, wejście
nie wcześniej niż5min po potwierdzonym odbiorze, wyjście po30min; identyczne
okna A=momentum pierwszych5min, B=kierunek actual-context, C=cash, D=placebo
etykiet eventów. Nie zmieniać istniejącej hipotezy true-surprise wstecznie.

12zdarzeń służy **odbiorowi jakości i falsyfikacji wykonania**, nie potwierdzeniu
edge. Niezależny test będzie wymagał większej próbki, z góry ustalonej liczby
zdarzeń/końca i mocy, bez kolejnego oglądania i strojenia tych samych danych.

Koszt źródła EIA0 USD, TMS w posiadanym dostępie; koszty pracy/transferu nie
są wyceną dostawcy. Jeśli broker nie udostępni starych ticków, najmniejszym
zamiennikiem jest przyszłe12 kolejnych wydarzeń z już pasywnie zbieranych
kwotowań i osobno legalnie archiwizowanych first publications. Nie zmieniać
silnika do tego celu. To wolniejsza ścieżka zbioru, nie obietnica zysku.

**Nie potrzebujemy jeszcze kupować danych**, żeby podjąć tę próbę. Do true
surprise potrzebny będzie ankietowy preconsensus; konkretni dostawcy i ceny
lub brak publicznej wyceny są w edge_program/DATA_SOURCES.md. FXMacroData
nie rozwiązuje tej luki, a feed futures nie zastępuje wykonania TMS.

Nie wybieramy teraz2–3 nowych strategii z krótkiej próby. EIA i COT pozostają
dwoma uzasadnionymi pytaniami badawczymi, ale tylko powyższy pakiet ma być
następnym krokiem. Obecne wyniki IV nie uzasadniają dalszej optymalizacji progów.
