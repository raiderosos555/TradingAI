> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Ciągły test DEMO: 25–30 października 2026

Nowe wejścia są autoryzowane od niedzieli **25.10, 21:00 Warszawa** do piątku
**30.10, 23:00 Warszawa**. Są to godziny działania testu, a nie deklaracja godzin
sesji brokera. System czeka na świeże kwotowania, zamknięte świece i komplet bramek.
Nie wymusza transakcji o godzinie rozpoczęcia. LIVE pozostaje wyłączony.

Podstawą jest istniejące polecenie operatora samodzielnych testów DEMO.
Zakres i SHA-256 konfiguracji zapisuje `state/runtime-authorization.json`.
`config.local.json` zachowuje DRY_RUN; zadania korzystają z osobnego `config.demo.json`.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

## Procesy i zegar

Harmonogram Windows uruchamia dwa zadania w zwykłej, zalogowanej sesji użytkownika:
`TradingAI-DEMO-engine` oraz `TradingAI-DEMO-baseline`. Używają lokalnego Python,
bez haseł i bez wywołań modeli. Restart po awarii ustawiono co minutę. Blokady
procesów zapobiegają dwóm wykonawcom na tym samym rachunku.

Engine skanuje rynki co około minutę, zarządza pozycjami co około 10 sekund,
eksportuje raport co 30 minut i briefingi o 09:00/18:00 Warszawa. Czasy są orientacyjne:
wywołania MT5 mogą potrwać dłużej. SL/TP pozostają zleceniami po stronie brokera.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

Zmiana czasu wymaga dwóch kolejnych świeżych eksportów EA oraz zgodnych świeżych
ticków z co najmniej dwóch instrumentów. Dopuszczone przesunięcia serwera to +1h/+2h.
Jeżeli broker użyje innego przesunięcia lub dowody się nie zgadzają, silnik się blokuje.
Po restarcie potwierdzanie zegara może potrwać około 5 minut. W weekend oczekiwanie
na świeże ticki jest prawidłowe. Po otwarciu rynku wymagane są także aktualne świece.

Komputer musi pozostać włączony, użytkownik zalogowany, MT5 połączony z DEMO,
a TradingAIObserver podpięty. Procesy odświeżają licznik bezczynności Windows;
ekran może się wyłączyć. Ręczne uśpienie, wylogowanie, odłączenie sieci czy aktualizacja
Windows nadal mogą zatrzymać działanie. Nie jest to wdrożenie na serwerze wysokiej dostępności.

## Stan, zatrzymanie i ponowne uruchomienie

W PowerShell, z `C:\TradingAI`:

```powershell
.\.venv\Scripts\python.exe tools\runtime_status.py
.\.venv\Scripts\python.exe -m trading_ai --config config.demo.json stop
```

STOP blokuje nowe wejścia i anuluje własne pendingi, kiedy broker pozwala na operację.
Przy `stop_policy=manage` istniejące pozycje nadal są chronione przez przypisane reguły.
Nie oznacza to automatycznego zamknięcia wszystkich pozycji.

Trwałe cofnięcie autoryzacji strategii, dostępne również podczas działania:

```powershell
.\.venv\Scripts\python.exe -m trading_ai --config config.demo.json revoke-strategy
```

Całkowite wyłączenie obu procesów (pozostają tylko SL/TP u brokera):

```powershell
Set-Content -LiteralPath C:\TradingAI\state\runtime\DISABLED -Value 'operator stop'
Stop-ScheduledTask -TaskName TradingAI-DEMO-engine
Stop-ScheduledTask -TaskName TradingAI-DEMO-baseline
Disable-ScheduledTask -TaskName TradingAI-DEMO-engine
Disable-ScheduledTask -TaskName TradingAI-DEMO-baseline
```

Nie kasować dziennika ani kwarantanny, żeby wymusić wejścia. Zmiana zatwierdzonej
konfiguracji blokuje nowe zlecenia. Po końcu okna testu nie są odnawiane zgody na
wejścia; ochrona istniejących pozycji pozostaje aktywna. Przedłużenie wymaga nowego,
jawnego zakresu testu, nie uruchamia się bezterminowo.

Stan i logi: `state/runtime/*-status.json`, `state/runtime/*.log`.
Raporty: `exchange/outbox`. Wyniki testu historycznego: `exchange/research`.

## Odbiór

Przejście testów programistycznych i uruchomienie procesów nie potwierdza zyskowności.
Zapis rzeczywistego następnego UTC 00:00, przejście DST oraz działanie po otwarciu
sesji wymagają jeszcze obserwacji podczas tych zdarzeń. Dalsza ocena jakości strategii
opiera się na wynikach badawczych i przyszłym forward DEMO.
