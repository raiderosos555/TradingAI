> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Proponowane odzyskiwanie DEMO — nie wdrożono

Zakres: przywrócenie tej samej zatwierdzonej wersji po zakończeniu procesu. Bez zmiany parametrów strategii, limitów, czasu brokera, poświadczeń lub autoryzacji zleceń. LIVE pozostaje wyłączony. Wdrożenie wymaga osobnego zatwierdzenia zgodnie z punktem 4 zlecenia użytkownika.

## Minimalna poprawka przygotowana w kopii

`candidate/trading_ai/runtime.py` i `runtime-candidate.patch`:

1. Publikacja statusu podejmuje trzy ograniczone próby przy błędzie plikowym. Następnie zapisuje traceback do logu i zwraca False zamiast zrywać pętlę obsługi błędów. Dotyczy tylko pliku telemetrycznego statusu; **nie osłabia trwałości SQLite, INTENT ani walidacji zleceń**.
2. Wyjątek kończący program jest logowany z tracebackiem przed ponownym podniesieniem. Przyszły launcher musi dodatkowo przechwytywać stdout/stderr procesu do osobnego pliku, ponieważ sama awaria logowania też jest możliwa.

Tylko runtime.py różni się między kopią źródłową i kandydatem. Nie zmieniono kodu uruchomionego DEMO.

## Nadzór — projekt oparty na przetestowanych elementach

- Harmonogram co minutę uruchamia nadzorcę z `MultipleInstances=IgnoreNew`, niezależnie od działania `RestartOnFailure`. Przeprowadzono test dwóch kolejnych wywołań takiego zadania po exit 1.
- Nadzorca ma własną blokadę systemową, nie usuwa blokad silnika. Przed startem uwzględnia stan zadania i tożsamość procesu; sam PID lub stary JSON statusu nie wystarcza.
- Istniejący silnik nadal bierze trzy blokady systemowe: runtime/engine, katalog stanu oraz rachunek+serwer. Wszystkie są uzyskiwane **przed połączeniem z MT5**. Ich zwolnienie po śmierci procesu zapewnia system operacyjny. Zostało to sprawdzone przy rzeczywistym ubiciu wyłącznie procesu testowego.
- Żywy proces ze starym statusem oznacza alarm, nie zgodę na drugi silnik. Nie zabija się procesu na podstawie samego PID ani wieku statusu. Automatyczne zastępowanie zawieszonego procesu nie jest częścią zatwierdzonej propozycji.
- Restart dotyczy tylko zaobserwowanego zakończenia własnego procesu. Opóźnienia produkcyjne proponowane: 60/120/240 s, maksymalnie 3 nieskuteczne próby w serii, następnie stan wymagający interwencji. Licznik musi przetrwać restart nadzorcy. `supervisor.py` zawiera przetestowaną politykę stanów z krótkimi jednostkami testowymi; **nie jest jeszcze zainstalowanym, kompletnym launcherem produkcyjnym**.
- Nadzorca nie odnawia zgód, nie wpisuje equity, nie zmienia konta, nie włącza LIVE ani nie kasuje kwarantanny. Wznawia ten sam config/journal. DISABLED i wyłączenie zadania przez użytkownika mają pierwszeństwo.

## Ochrona przed ponownym zleceniem

Po starcie: potwierdzenie tego samego konta DEMO, połączenia i istniejących reguł czasu; odczyt pozycji, zleceń i historii; `ExecutionEngine.reconcile()` z trwałego dziennika; dopiero potem zwykły Position Manager i Signal Engine z niezależnym Risk Managerem.

INTENT bez odpowiedzi nie jest ponawiany. Jedno pasujące zlecenie z historii i pełne potwierdzenie wolumenu, właściciela i ochrony pozwala przyjąć istniejące wykonanie. Brak, niejednoznaczność, częściowe wykonanie albo niezgodność konta pozostawia blokadę. Zostało to przetestowane na kopii faktycznych klas Execution Engine/Risk Manager z brokerem wyłącznie w pamięci.

Obecna bramka zegara blokuje całą pętlę, również zarządzanie, do zebrania dwóch eksportów EA i świeżych ticków. Nadzorca nie omija tej bramki. SL/TP zapisane u brokera są odrębne od BE/trailingu wykonywanego przez aplikację; powrót terminala nie oznacza natychmiastowego powrotu całego zarządzania.

## Warunki przed zatwierdzonym wdrożeniem

Po ewentualnej zgodzie: zamknąć implementację launchera i trwałego licznika restartów, przetestować cały proponowany zestaw z zadaniem Windows oraz symulatorem, zachować kopię konfiguracji i hashy, wykonać kontrolowaną migrację jednego zadania. Nie zmieniać źródeł w locie. Po migracji potwierdzić pojedynczego właściciela, zgodność dziennika i pozycji, brak ponownego send oraz powrót zarządzania. Rollback przywraca poprzedni launcher/kod, ale nigdy nie cofa ani nie zastępuje journal.sqlite3.

**GO dla wyników testów poszczególnych elementów. NO-GO dla twierdzenia, że kompletny nadzór produkcyjny jest już wdrożony lub zweryfikowany.**
