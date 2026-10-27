> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Zakres projektu i stan odbioru

Stan: 24.10.2026. Wdrożono moduły pełnego projektu, a integrację ChatGPT jako
dodatkowy transport. Kod, odczyt oraz pierwsze aktywne wykonanie DEMO są zweryfikowane.
Odbiór funkcji jest opisany poniżej; pozostają braki w walidacji operacyjnej i jakości
strategii. Bieżące ustalenia: [audyt 24.10](project-audit-20261024.md).
Aktualna suite: 168 testów OK. Liczba 142 w opisach odbioru poniżej dotyczy 23.10.

| Wymaganie projektu | Implementacja | Weryfikacja / pozostałe warunki |
|---|---|---|
| 1. Windows, Python, oficjalny MT5, dane lokalnie | .venv, broker.py, SQLite, konfiguracja lokalna | Połączony rzeczywisty DEMO; bez haseł w kodzie |
| 2. OHLCV/ticki, 7 interwałów, wskaźniki, stan rachunku | collector, broker, indicators, observer + MQL5 | 49 serii, 7 ticków, 9 PNG, 174 obiekty; brak wskaźnika na wykresie do testu buforów |
| 3. Trend, S/R, wybicia, momentum, zmienność, sygnał JSON | analyzer, strategy, models | Testy i replay; brak deklaracji rentowności |
| 4. BUY/SELL, LIMIT/STOP, zmiany i anulowanie | risk, execution, CLI | Wszystkie sześć typów przyjęte na DEMO: BUY/SELL US500 i cztery pendingi EURUSD; SL pendingów i anulowania potwierdzone |
| 5. BE, trailing, TP1/TP2, invalidation, własność, restart | manager, journal, execution | 142 testy; na DEMO pełne/częściowe zamknięcie i odzyskanie aktywnej pozycji w nowym procesie; wyzwalacze cenowe/netting symulacyjnie |
| 6. Twardy Risk Manager i STOP | risk, models, CLI | 0,25% / 1% / 2 sloty, dodatkowo 0,5% ryzyka łącznego; brak baseline blokuje wejścia |
| 7. Walidacja każdej operacji, idempotencja, recovery | risk, execution, journal | Podwójna bramka, trwały zamiar, rzeczywisty stan, częściowe fill, timeout, luka pendingu |
| 8. DRY_RUN / DEMO / LIVE | CLI, risk, config | Osobny runtime DEMO na 25–30.10; główna konfiguracja DRY_RUN; LIVE wyłączony |
| 9. Briefingi rano/wieczorem, JSON/MD, wyniki i R | briefings, reporter, sync | Raporty rzeczywistego stanu wygenerowane; harmonogram lokalny podczas --watch |
| 10. Rozdzielone moduły, praca lokalna bez ciągłego AI | trading_ai/ | Brak wywołań modeli; jawne strategie deterministyczne; brak nowego sygnału AI bez importu |
| 11. Testy etapowe, DEMO po zgodzie, instrukcja LIVE | tests, tools, dokumentacja | 142 testy OK; 16 potwierdzonych operacji DEMO po zgodzie; końcowo płaski rachunek, brak kwarantanny |
| 12. Kompletny katalog i instrukcja | C:\TradingAI, README, docs | Kod, przykłady, schemat, testy, instalacja, STOP, obsługa awarii |

## Dodatkowa integracja z briefingiem

Import poranny/wieczorny JSON, weryfikacja aktualności/struktury, niezależne ryzyko,
lokalne zgody, reguły pozycji, eksport rzeczywistych wyników i uzasadnień JSON/Markdown
oraz interfejs przyszłego adaptera są zaimplementowane. Broker jest źródłem prawdy.
Brak bezpośredniego dostępu do historii ChatGPT i automatycznego wysyłania danych.

## Odbiór DEMO po zgodzie

Operator zezwolił na samodzielne testy DEMO, w tym dalsze próby bez pytania o każdą
operację. Zgoda jest zapisana w dzienniku i plikach state/demo-*-consent.json.
Przed każdą dyspozycją nadal obowiązują wszystkie limity i niezależny Risk Manager.
Dowód: [demo-validation.json](demo-validation.json), szczegóły [validation.md](validation.md).

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

Podczas BUY LIMIT wykryto skrócenie ważności przez brokera do pełnej minuty.
Zatrzymano wykonanie, dodano regresje, uzgodniono istniejące zlecenie i anulowano je.
Brak ponownego wysłania. Wydłużenie ważności pozostaje niedopuszczalne.

## Stan końcowy i granice weryfikacji

Główna konfiguracja oraz stare konfiguracje prób pozostają DRY_RUN. Dwa uruchomione
zadania Windows korzystają z osobnej konfiguracji DEMO z ograniczonym oknem 25–30.10,
minimalnymi lotami i dodatkowymi filtrami spreadu. LIVE pozostaje wyłączony.
Wszystkie siedem rynków jest objęte skanerem. [Instrukcja pracy ciągłej](demo-runtime.md).

Kod BE/trailing/TP1/TP2, unieważnienia, STOP, netting, awarii/rozłączeń i recovery jest
pokryty testami symulacyjnymi. Nie twierdzimy, że wszystkie warianty wykonano na
rzeczywistym brokerze. Zweryfikowano restart programu; fizyczny restart terminala
z aktywną pozycją nie był testowany. Nie było dostępnego niestandardowego wskaźnika
na wykresie do testu buforów. Rentowność strategii pozostaje niepotwierdzona.

Kalendarz MT5 jest włączony w Risk Managerze. Automatyczny strumień newsów i połączenie
z historią ChatGPT nie są uruchomione; wymagany jawny interfejs JSON/Markdown oraz
protokół przyszłego adaptera działają. Zapis znalezionego briefingu jest fragmentem
z oznaczeniem niekompletności — nie jest autoryzowanym planem transakcyjnym.
