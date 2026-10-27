> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Kontrolowane wdrożenie Recovery v2 — jeszcze niewykonane

Właściciel wymaga osobnej zgody przed wdrożeniem. Skrypty deploy/rollback domyślnie
odmawiają działania; parametr `-Approved` wolno podać dopiero po tej zgodzie.
Przygotowano kopię konfiguracji, kodu i XML obu zadań w prywatnym backupie.

## Zakres zmiany

Osobny katalog `release/` zawiera kopię aplikacji oraz zmieniony wyłącznie runtime:
odporna publikacja statusu i pełne tracebacki. Risk Manager, Execution Engine,
Position Manager i strategie pozostają identyczne. Aktywne źródła projektu nie
będą nadpisywane. Jest to istotne dla hashy istniejącego kolektora forward.

Nowe zadanie `TradingAI-DEMO-Recovery` wywołuje dispatcher co minutę i przy
logowaniu tego samego użytkownika. Stare `TradingAI-DEMO-engine` zostaje wyłączone,
ale jego akcja i kod pozostają dostępne do rollbacku. Baseline, News i Forward
Evidence nie są modyfikowane. To sesja Interactive, więc po fizycznym restarcie
Windows potrzebne są logowanie operatora, uruchomiony MT5 i zalogowane konto.
Nie dodano autologowania ani przechowywania hasła terminala.

## Przebieg po zgodzie

1. Powtórzyć odczyt brokera: tożsamość DEMO, SL/TP, kwarantanna, historia oraz
   aktualność kolektora. Zweryfikować hashe i XML starego zadania. Jeżeli od
   przeglądu zmienił się kod/config, zatrzymać procedurę i odświeżyć przegląd.
2. Wyłączyć wyłącznie trigger starego silnika. Utworzyć jego DISABLED i czekać na
   kooperacyjne zakończenie oraz zwolnienie trzech blokad i blokady launchera.
   Maksymalnie 180 s; brak zwolnienia oznacza przerwanie migracji i diagnostykę,
   nigdy automatyczne zabicie procesu. Brokerowe SL/TP pozostają u brokera.
3. Jednorazowo zainicjalizować nowy dziennik nadzoru. Istniejącego dziennika nie
   resetować. Zarejestrować nowe zadanie i usunąć tylko własny DISABLED.
4. Włączyć dispatcher. Nowy silnik przechodzi dotychczasowe bramki konta, czasu,
   trwałego dziennika, reconcile i Risk Managera. Nie omija oczekiwania na dwa
   eksporty EA. Po migracji przerwa zarządzania może więc być dłuższa niż sam
   restart procesu; nie deklarować natychmiastowego BE/trailingu.
5. Potwierdzić jednego właściciela, zgodność pozycji i ochrony, brak ponownego
   send, zachowanie STOP/REVOKED i aktualny status kolektora. Obserwować co najmniej
   dwa wywołania zadania oraz pięć minut poprawnej pracy po przejściu bramek czasu.

Polecenie po wyraźnej zgodzie, z katalogu badania:

```powershell
.\deploy_after_approval.ps1 -Approved
```

## Kwarantanna wykryta przed migracją

Odczyt wykazał odrzucenie potwierdzenia OPEN z powodu różnicy reprezentacji TP
około 2,22e-16; oba poziomy należą do tej samej siatki ceny. Oryginalne `verify`
zwróciło False; tylko w kopii obiektu w pamięci ustawienie dokładnej wartości
brokera dało True. Nie zapisano tego wyniku w dzienniku. Nie jest to upoważnienie
do wyczyszczenia kwarantanny ani zmiany ochrony pozycji.

Wdrożenie Recovery nie naprawi tej weryfikacji. Może być zatwierdzone jako
kontrolowane wdrożenie samego nadzoru, z zachowaniem kwarantanny, ale nie jako
wznowienie niezawodnego handlu lub zarządzania. Odrębna mała poprawka wymaga
testów porównania na siatce kontraktu i osobnego przeglądu przed zastosowaniem.

## Rollback

```powershell
.\rollback_after_approval.ps1 -Approved
```

Skrypt wyłącza wyłącznie nowe zadanie, kooperacyjnie zatrzymuje właściciela,
sprawdza zwolnienie blokad i wznawia oryginalne zadanie. Nigdy nie odtwarza starej
bazy operacji, nie usuwa blokad ani kwarantanny i nie cofa historii.

Jeśli migracja przerwała się z pozostawionym DISABLED, automatyczny rollback
odmawia usunięcia istniejącego znacznika. Operator musi najpierw ustalić jego
właściciela, potwierdzić zwolnienie blokad i stan brokera, a potem jawnie usunąć
wyłącznie znacznik pozostawiony przez tę migrację i uruchomić stare zadanie.
Nie restartować na ślepo zawieszonego procesu ani terminala.

## Warunki decyzji

GO może dotyczyć wyłącznie nadzorowanej migracji w sesji operatora, po spełnieniu
odczytu ochrony i integralności oraz zgodzie. Pełny restart Windows nie został
wykonany: przerwałby działające DEMO i zbieranie okna forward. Odtworzenie stanu
po śmierci procesów i działanie triggera logowania nie zastępują takiej próby.
NO-GO dla deklaracji pełnej odporności na fizyczny reboot i bezobsługowej pracy.
