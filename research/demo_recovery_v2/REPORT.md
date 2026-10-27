> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Recovery v2 — ukończenie nadzoru i warunki dalszej walidacji

Stan: 27.10.2026, około 13:52 Europe/Warsaw. Aktywnego DEMO nie zmieniono.
Nowa wersja jest przygotowana w osobnym katalogu i nie została wdrożona.
Nie wysłano żadnego zlecenia MT5 w ramach testów. Istniejący kolektor działa dalej.

## 1. Co ukończono

Kompletny dispatcher, launcher i trwały dziennik SQLite nadzoru zastępują samą
klasę SupervisorPolicy z poprzedniego etapu. Implementacja identyfikuje właściciela
przez PID i czas utworzenia, zapisuje zamiar startu przed Popen, zachowuje trzy
oryginalne blokady i dodatkową blokadę launchera. Nie ponawia niejednoznacznego
startu ani transakcji. Po trzech nieudanych restartach trwale wymaga interwencji.

Przygotowano opóźnienia 60/120/240 s, kontrolę heartbeat, alarm bez zabijania
żywego procesu, pełne tracebacki i przechwytywanie stdout/stderr. Zachowano
oryginalne reconcile, kwarantannę, STOP, autoryzacje i limity. Mechanizm nie ma
API wysyłania zleceń i nie zapisuje do dziennika transakcji.

Przygotowano osobny przypięty hashami release, backup konfiguracji/kodu/XML,
guard migracji oraz skrypty wdrożenia i rollbacku wymagające jawnej zgody.
Wdrożenie nie nadpisze źródeł wykorzystywanych przez kolektor forward.
Szczegóły: [DESIGN.md](DESIGN.md), [MIGRATION.md](MIGRATION.md).

## 2. Rzeczywiste wyniki testów

| Próba | Wynik |
|---|---|
| Regresja całego rdzenia na kandydacie | **186/186 PASS** |
| Integracja launchera, procesów i trwałego stanu | **16/16 PASS** |
| Błąd połączenia MT5 i autoryzacji w brokerze offline | Runtime ponawia połączenie bez śmierci procesu; brak importu MT5 |
| Otwarty plik JSON blokujący os.replace | Kandydat kontynuuje; traceback zachowany, dziennik operacji nieosłabiony |
| Nagłe zakończenie właściciela i nowy proces nadzorcy | Nowy właściciel po backoffie, stan zachowany |
| Żywy proces bez postępu | Alarm; żadnego drugiego właściciela ani kill |
| Równoczesne dispatchery / istniejąca blokada silnika | Jedna rezerwacja/właściciel; konkurent nie uruchamia brokera |
| Broker w pamięci wykonał zlecenie przed awarią | Nowy proces potwierdza istniejące wykonanie bez resend |
| Brak dowodów wykonania | UNCERTAIN zachowane, brak resend |
| STOP i cofnięta autoryzacja po realnym restarcie procesu | Zachowane; wejście nadal blokowane |
| Niejednoznaczna rezerwacja, cofnięcie zegara, zmiana configu | Fail closed, wymagana interwencja |
| Pełny Harmonogram Windows, cztery kolejne procesy fixture | Start początkowy + trzy nieudane restarty, potem trwały CIRCUIT_OPEN |
| Niezależny Harmonogram podczas pracy właściciela | Dwa kolejne odpytywania tego samego żywego właściciela |
| Fizyczny restart Windows / ponowne logowanie MT5 | **NIEWYKONANE** — przerwałoby istniejącą archiwizację i DEMO |

Razem **202 automatyczne testy** oraz dwie odrębne próby z rzeczywistymi zadaniami
Harmonogramu. Testy jednostkowe/integracyjne używają krótkich opóźnień; próba
Harmonogramu używa pełnych 60/120/240 s. Zmierzone oczekiwania wyniosły około
120,3 / 120,0 / 242,2 s, bo dispatcher działa na minutowym triggerze z jitterem.
Każdy start nastąpił po zapisanym terminie retry_at; żaden backoff nie został
skrócony. Po otwarciu obwodu dodatkowe uruchomienie dispatchera nadal zwróciło
INTERVENTION bez kolejnego procesu. Oba zadania LAB usunięto.

Testy z nowym procesem dispatchera sprawdzają trwałość po utracie procesów;
nie są fizycznym restartem Windows ani dowodem automatycznego logowania terminala.
Pełne wyniki są w lokalnym evidence/, w tym scheduler-result-verified.json.
Początkowy problem zamknięcia połączenia SQLite w initialize naprawiono i serię
testów ponowiono; wcześniejszy nieudany wynik zachowano.

## 3. Gotowość Recovery do wdrożenia

**GO warunkowe dla kontrolowanej migracji pod nadzorem operatora**, po ponownym
preflight i jawnej zgodzie na zakres z MIGRATION.md. Jest to zgoda na nadzór
procesu, nie na usunięcie kwarantanny ani wznowienie wejść. Skrypty migracji mają
sprawdzoną składnię i guard; nie uruchomiono ich na produkcyjnym DEMO.

**NO-GO dla deklaracji pełnej bezobsługowej odporności na restart Windows.**
Brak rzeczywistej próby reboot/login/MT5 po restarcie. W sesji Interactive po
reboocie wymagane jest logowanie użytkownika. Nie dodano autologowania terminala.
Nadzór nie naprawia problemów kwotowań ani nie omija bramki czasu.

## 4. Aktualne DEMO — dodatkowy problem wymagający uwagi

Odczyty przed i po próbach potwierdziły połączenie, wyłączony LIVE, brokerowe SL/TP
dla aktualnych pozycji oraz wykonalne kwotowania w tej próbce. Proces silnika i
kolektor zachowały swoje PID. Hashe aktywnego kodu, konfiguracji, kolektora oraz
XML obu oryginalnych zadań pozostały identyczne.

Jednocześnie wykryto **UNCERTAIN przy OPEN**: TP zwrócone przez brokera różni się
od żądania o około **2,22e-16**, przy tym samym poziomie siatki cen. Dokładne
porównanie float w ExecutionEngine.verify odrzuca potwierdzenie. Odczytowy test
oryginalnego verify zwrócił False, a kopia operacji w pamięci z dokładną wartością
brokerową True. Nie zapisano korekty do dziennika, nie kasowano kwarantanny i nie
zmieniano poziomów u brokera. Szczegóły finansowe i identyfikatory pozostają lokalnie.

Ostatnie 100 odczytanych decyzji zarządzania miało blokadę niepewnej operacji.
**NO-GO dla twierdzenia, że DEMO ma pełną sprawność operacyjną.** Ochrona SL/TP
u brokera jest obecna, lecz BE/trailing i inne operacje aplikacji są blokowane.
SL/TP nie gwarantują ceny realizacji przy luce. Sam restart nie usuwa tej przyczyny.

## 5. Pierwsze okno forward

**PENDING_WINDOW_END.** W chwili tego raportu 27.10 09:00–17:00 Europe/Warsaw
jeszcze trwa. Nie przedstawiamy audytu nieukończonej próby jako końcowego wyniku.
Kolektor nadal zapisuje cohort-20261026-v1, również okres kwarantanny. Nie wybiera
się w zamian korzystniejszego dnia. Kontrola hashy źródeł/tasku nie dowodzi jeszcze
kompletności ticków ani kontekstu.

Istniejący jednorazowy audyt o **17:10** pozostaje aktywny; jego instrukcję
uzupełniono o wyniki Recovery v2, kwarantannę i porównanie operacji z historią MT5
tylko do odczytu. Wyniki trafią do research/replay_readiness/20261027/. Nie utworzono
drugiego monitora, nie zmieniono harmonogramu kolektora. Rozdzielone decyzje:

| Obszar | Decyzja teraz |
|---|---|
| Odporność mechanizmu Recovery w kontrolowanej sesji | GO dla przetestowanego zakresu; wdrożenie oczekuje zgody |
| Pełna sprawność aktywnego DEMO | NO-GO: kwarantanna blokuje zarządzanie aplikacyjne |
| Akceptacja kompletności okna forward | NO-GO teraz / PENDING do zamknięcia i audytu |
| Wiarygodny pełny replay | NO-GO do przejścia bramek danych i wykonania |
| Potwierdzenie Trading Edge | Niepotwierdzone; ten etap nie estymował przewagi |

## 6. Co nadal blokuje wiarygodny replay

Nie ma jeszcze zaakceptowanej mapy UTC i niepewności całego wybranego odcinka,
potwierdzonej zgodności kwotowania widzianego przez silnik z historią ticków,
pełnego uzgodnienia początkowego portfela i sekwencji między instrumentami.
Polling kalendarza nie dowodzi automatycznie dokładnej wersji użytej przy każdej
decyzji. Koszty i rzeczywiste wykonania muszą być rozliczone z historią brokera,
z uwzględnieniem kwarantanny, blokad i niewykonalnych kwotowań.

## 7. Jeden następny krok w kierunku Trading Edge

**Po 17:00 zweryfikować zamknięte, z góry wybrane okno 27.10 i wskazać jego
kwalifikację do replay albo dokładnie brakujące dowody.** Bez wyboru strategii,
parametrów ani sesji po wyniku. Tylko jeśli bramki przejdą, porównać zamrożony
replay z zapisanym DEMO. Okres kwarantanny musi pozostać w porównaniu.

Rozwiązanie porównania TP na siatce wymaga osobnej małej poprawki i testów;
to potrzeba bezpieczeństwa i wiarygodności wykonania, nie nowa funkcja strategii.
Nie wdrożono jej w tym etapie. Jedna doba pozostaje kontrolą odtwarzania, a nie
dowodem przewagi. Protokół dalszego forward i zamrożone strategie pozostają bez zmian.

## GitHub

Przygotowywana aktualizacja obejmuje kod i dokumenty Recovery v2 w oczyszczonej
kopii. Prywatne konfiguracje, dowody brokerowe, runtime, ticki i bazy są pominięte.
Poprzedni commit jest już opublikowany; nowy commit wymaga osobnego zatwierdzenia
przed push. Lista plików i wyniki skanu są zapisywane lokalnie w publication/.
