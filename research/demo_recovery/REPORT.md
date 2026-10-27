> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# TradingAI — odzyskiwanie DEMO po rozłączeniu

Stan: 27.10.2026 rano, Europe/Warsaw. Nie wdrożono zmian aktywnego DEMO ani rejestratora cohort-20261026-v1. Limity, strategia i wyłączony LIVE zachowane.

## Decyzje

| Obszar | Decyzja | Uzasadnienie |
|---|---|---|
| Odporność operacyjna aktywnego DEMO | **NO-GO** | Uruchomiony pozostaje dotychczasowy kod. Błąd publikacji statusu i nieskuteczne wznowienie odtworzono; poprawka oraz nadzór nie są wdrożone. |
| Kompletność danych okna 27.10 | **NO-GO do uznania próby za kompletną / oczekiwanie** | Okno 09:00–17:00 jeszcze się nie zakończyło. Rejestrator pracuje; po oknie nastąpi osobny audyt. |
| Wiarygodność pełnego backtestu | **NO-GO** | Nadal brak zaakceptowanej mapy czasu i zgodności historii ticków z ceną widzianą przy decyzji; pozostają kontekst, stan początkowy i kolejność między strumieniami. |

Żadna z tych decyzji nie potwierdza ani nie obala przewagi inwestycyjnej. Nie optymalizowano strategii.

## Przyczyna zakończenia procesu: co wiemy

Potwierdzono lukę w obsłudze błędów: `runtime.run` próbuje opublikować status także wewnątrz `except` i `finally`. `atomic_write` kończy się `os.replace`. Na Windows otwarcie docelowego pliku przez czytelnika bez współdzielenia usuwania może zablokować zastąpienie. Wtedy wyjątek z raportowania przerywa obsługę pierwotnego błędu MT5, a kolejne zapisanie STOPPED również kończy się wyjątkiem.

W kontrolowanym procesie z kopią oryginalnego runtime:

- sam błąd autoryzacji MT5 został obsłużony i wykonano następną próbę połączenia;
- ten sam błąd z blokadą odczytu pliku statusu dał **PermissionError / WinError 5, exit 1**, niezmieniony plik docelowy i pozostawiony plik tymczasowy STOPPED;
- kopia z poprawką przetrwała ten sam scenariusz i kontynuowała ponawianie połączenia.

Ślad rzeczywistej awarii jest zgodny z tym scenariuszem: `engine-status.json.10844.tmp`, 72 bajty, STOPPED o 18:15:56.892189 UTC, podczas gdy ostatni opublikowany status pochodził z 18:15:49 UTC. Zachowano oryginalny plik i traceback reprodukcji.

**Poziom pewności:** wada i mechanizm exit 1 są odtworzone; to mocne wyjaśnienie incydentu. Nie zachował się traceback rzeczywistego procesu, dlatego nie twierdzimy, że ustalono konkretny proces blokujący plik ani wszystkie szczegóły pierwotnej awarii. Rejestrator oraz inne narzędzia również odczytują status i mogły być uczestnikiem kolizji; nie ma dowodu przypisującego ją konkretnemu czytelnikowi. Brak zdarzenia Application Error nie dowodzi awarii natywnej DLL. Nie znaleziono takiego dowodu.

## Dlaczego wznowienie było nieskuteczne

Zadanie miało już `RestartOnFailure`, interwał minutowy, Count=999 i `MultipleInstances=IgnoreNew`. Błędne byłoby stwierdzenie, że nie ustawiono restartów. Zwykły trigger uruchamiał je przy logowaniu; nie było niezależnego cyklicznego wywołania. Dziennik TaskScheduler/Operational był wyłączony, stderr `pythonw` nie był przechwytywany.

Skopiowano ustawienia do dwóch całkowicie izolowanych zadań: start ręczny i start czasowy. Oba skrypty zapisały po jednym uruchomieniu i zwróciły 1. Po ponad czterech minutach nie odnotowano drugiego skutecznego wywołania skryptu. To reprodukuje **nieskuteczność wznowienia na tej konfiguracji**, ale nie pozwala nazwać wewnętrznej przyczyny zachowania usługi Windows ani stwierdzić, że nie było żadnej wewnętrznej próby. Zadania testowe usunięto.

Osobny test niezależnego triggera minutowego z IgnoreNew dał dwa wykonania skryptu w odstępie około 60 s, pomimo exit 1 pierwszego. To uzasadnia dodatkowy, niezależny nadzór zamiast polegania wyłącznie na tej opcji Harmonogramu. Dokumentacja Microsoft opisuje [RestartOnFailure](https://learn.microsoft.com/en-us/windows/win32/taskschd/taskschedulerschema-restartonfailure-settingstype-element) oraz [zbieranie diagnostyki zadań](https://learn.microsoft.com/en-us/troubleshoot/windows-server/system-management-components/troubleshoot-scheduled-tasks-not-running); lokalne wyniki testów są w scheduler-lab-result.json i periodic-lab-result.json.

## Blokady, konto i uzgodnienie pozycji

Oryginalne trzy blokady silnika są blokadami systemowymi, nie samą obecnością pliku. Test rzeczywistych procesów potwierdził odrzucenie drugiego właściciela oraz odzyskanie blokady po śmierci pierwszego, bez kasowania pliku blokady. Nadzorca nie powinien usuwać blokad ani uruchamiać zastępstwa tylko dlatego, że JSON statusu jest stary.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

Istniejące klasy Execution/Risk Manager, na brokerze w pamięci, przeszły testy odzyskania wykonanego zlecenia bez ponownego send, idempotencji oraz kwarantanny przy brakach, częściowym fill, niejednoznaczności i innym rachunku. Restart nie przedłuża autoryzacji ani nie kasuje revocation. Podczas badań nie wysłano żadnego zlecenia do MT5.

## Poprawka i testy

- **13 testów odzyskiwania**: tests.txt.
- **21 istniejących testów runtime** uruchomionych na kopii z poprawką: runtime-regression.txt.
- **5 testów granic i pokrycia okna**: window-tests.txt.
- Trzy zadania testowe Windows; wszystkie odłączone/usunięte po zapisaniu wyników. Aktywne zadanie DEMO pozostało identyczne z eksportem początkowym.

Łącznie **39 testów automatycznych przeszło**. Poprawka dotyczy jednego modułu w izolowanej kopii: candidate/trading_ai/runtime.py. Diff: runtime-candidate.patch. Architektura nadzoru, ograniczenia i warunki migracji: **PROPOSAL.md**. Pełen launcher produkcyjny z trwałym licznikiem restartów nie jest jeszcze wdrożony ani zatwierdzony; nie utożsamiamy testów elementów z gotowością całego systemu.

## Okno 27.10 i dalszy pomiar

Nie przerywano rejestratora PID 11812 ani nie zmieniano jego zamrożonych źródeł. Ciągłość jego procesu i najnowszą paczkę zapisano w validation-state.final.json. Sama obecność paczek nie poświadcza kompletności ticków.

Audyt pierwszego okna **09:00–17:00 Europe/Warsaw / 08:00–16:00 UTC** zaplanowano jednorazowo na **27.10 o 17:10** w tym czacie, automatyzacja `tradingai-audyt-okna-27-10`. Obliczenia wykona lokalny `window_audit.py`, wynik zostanie zapisany do `research/replay_readiness/20261027/`. Przed końcem okna skrypt odmawia uznania go za ukończone; obecny preflight ma PENDING_WINDOW_END.

Zakres: hashe i łańcuch odbiorów, zakresy każdego strumienia i ich luki przy jawnie kandydackim offsecie, brakujące/nieudane paczki, wersje kontekstu, świece dostępne przed startem, stan pozycji i dowody zegara. Pełne pokrycie zakresów żądań API nie oznacza kompletnego feedu ani zweryfikowanego UTC. Raport oddzieli te ustalenia. Nie będzie optymalizacji, wyboru strategii po wyniku ani promocji rentowności jednej doby.

Zgodnie z punktem 4 prośby użytkownika **wdrożenie do aktywnego DEMO wymaga odrębnego zatwierdzenia**. Nie wprowadzono tej zmiany automatycznie.
