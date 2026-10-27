> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Audyt projektu — 24 października 2026

**Wniosek: mamy implementację funkcji i uruchomiony ograniczony test DEMO.
Nie mamy potwierdzonej przewagi inwestycyjnej ani pełnej walidacji pracy bez nadzoru.**

Audyt porównuje kod, konfigurację i dowody z oryginalnym projektem użytkownika
„Trading AI — MetaTrader 5 Autonomous Trading System” oraz dodatkową integracją
briefingów. Nie jest niezależnym audytem zewnętrznym. Nie wykonano nowych transakcji
w ramach tego sprawdzenia ani backtestu. LIVE pozostaje zablokowany.
Aktualny wynik: **168 testów automatycznych OK (12,557 s)**.

## Co jest zrobione

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

## Naprawy i uzupełnienia z tego audytu

1. Aktywny pending nie wymaga już odczytu własnego zlecenia z historii, w której
   jeszcze może go nie być. Usuwa to przyczynę przerwania cyklu zarządzania.
2. Rejestrator początku doby działa niezależnie od wolniejszego zbierania danych.
   Zapisuje wyłącznie świeży odczyt z pierwszych 5 sekund UTC; nie odtwarza go z wartości bieżącej.
3. Autoryzacja pracy ciągłej wiąże rachunek, dokładną konfigurację i czas testu.
   Aktualna konfiguracja jest czytana ponownie przed operacjami.
4. Zmiana czasu wymaga dwóch świeżych eksportów EA i zgodnych ticków dwóch kontraktów.
   Testy obejmują przejście +2h/+1h, niezgodne/stare dane i reset dowodów po zmianie.
5. STOP, resume i cofnięcie autoryzacji działają przy zajętej przez silnik blokadzie.
   Resume nie usuwa kwarantanny i nie odnawia cofniętej zgody.
6. Dodano limit maksymalnego lota oraz spread/ATR w niezależnej bramce ryzyka i replayu.
7. Raport zawiera ostatnie 2000 zdarzeń, aby nie kopiować rosnącego pełnego audytu
   co pół godziny. Pełna historia pozostaje w SQLite; operacje są nadal eksportowane.
8. Test badawczy ma zamrożone dane i konfigurację, kontrolę SHA-256, osobny okres
   weryfikacji, statystyki trafności/PF/R/DD i jawne ograniczenia.

## Czego jeszcze brakuje

| Priorytet | Brak / niepotwierdzona rzecz | Znaczenie i następny dowód |
|---|---|---|
| Wysoki | Potwierdzona przewaga strategii | 6 z 7 rynków stratnych w okresie weryfikacji. Potrzebne dalsze badania i przyszły forward; nie zwiększać ryzyka na podstawie tego testu |
| Wysoki | Pełny backtest zgodny z wykonaniem | Brak wspólnego portfela, historycznego kalendarza, tickowego zarządzania, dokładnych prowizji/swapów i serii FX. Obecny test jest przybliżeniem |
| Wysoki | Odbiór nocnego działania w rzeczywistym czasie | Procesy uruchomione; następny zapis UTC 00:00, weekendowe otwarcie i DST jeszcze nie nastąpiły podczas tego testu. Brak dowodów blokuje wejścia |
| Średni | Rzeczywiste cenowe wyzwolenie wszystkich reguł | BE/trailing/TP1/TP2, netting, luki i rozłączenia pokryto symulatorem; nie wszystkie warianty zostały wykonane u brokera |
| Średni | Fizyczny restart MT5 z aktywną pozycją | Sprawdzono restart procesu Python; test całego terminala pozostaje do wykonania w kontrolowanym DEMO |
| Średni | Odczyt buforów własnego wskaźnika | Eksporter skompilowany, ale na wykresie nie było wskaźnika do rzeczywistej weryfikacji |
| Średni | Pełna historia sesji/specyfikacji kontraktów | Aktualne kontrakty są odczytane; historyczne zmiany parametrów i strefy czasu nie są niezależnie potwierdzone |
| Operacyjny | Niezależna infrastruktura i powiadomienia | System zależy od tego komputera, zalogowanej sesji, sieci i MT5. Status/logi są lokalne; nie wdrożono zewnętrznego kanału alarmowego ani serwera zapasowego |
| Dodatkowy | Automatyczny adapter ChatGPT/newsów | Jawny transport plików działa. Bezpośrednia synchronizacja historii czatów i feed newsów nie działają; nie są warunkiem lokalnych strategii |

Kalendarz odczytywany na bieżąco pomaga blokować nowe wejścia, ale nie przewiduje
kierunku ruchu i nie jest pełnym strumieniem wiadomości. Przy minimalnych lotach
TP1 często nie może podzielić pozycji; jest wtedy pomijane zgodnie z ograniczeniami kontraktu.

## Wyniki historyczne

Okres danych: 27.04–23.10.2026; okres weryfikacji od 31.08. Konfigurację zamrożono
przed bieżącym przebiegiem, bez optymalizacji. Część danych była wcześniej użyta
w technicznym replayu, więc nie jest to całkowicie niewidziana próba.

| Instrument | Liczba transakcji | Trafność | Profit factor | Netto PLN |
|---|---:|---:|---:|---:|
| GOLD | 48 | 41,7% | 0,92 | −21,47 |
| US500 | 56 | 37,5% | 0,79 | −34,82 |
| OIL | 52 | 36,5% | 0,81 | −267,85 |
| EURPLN | 33 | 33,3% | 0,45 | −74,04 |
| EURUSD | 54 | 42,6% | 0,61 | −106,30 |
| GBPUSD | 49 | 40,8% | 0,75 | −60,62 |
| US100 | 46 | 56,5% | 1,94 | +201,07 |

Wartości netto dotyczą oddzielnych symulacji przy minimalnych lotach, po założonych
kosztach. Nie są wynikiem wspólnego rachunku ani prognozą. US100 ma dodatni wynik
na 46 transakcjach, lecz wynik okresu wcześniejszego był ujemny. Przy 3× spreadzie
limit kosztów zablokował tam wszystkie wejścia; nie ma dowodu odporności na wyższe koszty.

Pełne szczegóły, przedziały trafności i założenia:
[raport historyczny](../exchange/research/history-20261024/validation/report.md).

## Stan uruchomienia

Ograniczony forward DEMO: 25.10.2026 21:00 – 30.10.2026 23:00 Warszawa.
Limity: 0,1% na transakcję, 0,2% łącznie, 0,5% dziennie, maksymalnie 2 sloty,
lot najwyżej równy minimum kontraktu. Wszystkie siedem rynków pozostaje w skanerze;
nie wybrano US100 tylko dlatego, że wygrał ten historyczny fragment.

Potwierdzono uruchomienie obu zadań, świeże pliki statusu, połączenie z DEMO,
aktywne uprawnienia Python, kalendarz READY, brak pozycji i pendingów.
W sobotę nowe wejścia są zablokowane: okno jeszcze nie zaczęło się, ticki są stare,
a bieżącego początku doby nie zarejestrowano. Rejestrator oczekuje na kolejne UTC 00:00.

Dowody: `docs/test-results.txt`, `state/runtime/verification.json`,
`state/runtime-authorization.json`, `docs/demo-validation.json`, manifest i wyniki
w `exchange/research/history-20261024`.
Instrukcja uruchomienia, warunki i STOP: [demo-runtime.md](demo-runtime.md).
