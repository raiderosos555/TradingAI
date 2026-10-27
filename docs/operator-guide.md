> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Obsługa lokalnego systemu

Aktualizacja 24.10: dla działających zadań Windows i `config.demo.json` obowiązuje
[instrukcja ciągłego testu DEMO](demo-runtime.md). Poniższe polecenia ogólne dla
`config.local.json` opisują także ręczne uruchomienie; nie uruchamiać drugiego silnika
na tym samym stanie. STOP/resume/revoke-strategy działają podczas pracy silnika;
pozostałe narzędzia modyfikujące stan wymagają jego zatrzymania.

## Instalacja i konfiguracja

W obecnym środowisku Python 3.12 i pakiet MetaTrader5 są już w `C:\TradingAI\.venv`.
Przy nowej instalacji użyj 64-bitowego Pythona zgodnego z oficjalnym pakietem:

```powershell
Set-Location C:\TradingAI
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e '.[mt5]'
```

Tylko przy nowej konfiguracji skopiuj `config.json` do `config.local.json`; nie nadpisuj
istniejącej konfiguracji. `probe` odczytuje rachunek i katalogi. Wpisz dokładny numer
i serwer, następnie `inventory` i jawne mapowanie kontraktów. Terminal musi być
zalogowany ręcznie. Program nie przechowuje hasła ani nie zmienia rachunku.

W obecnej konfiguracji `trading_enabled:false` blokuje aktywne wejścia we wszystkich
instrumentach. Spread, dopuszczalne odchylenie wejścia, poślizg i bufor kosztów należy
ustalić osobno dla każdego kontraktu. `*_points` są punktami `symbol_info.point`,
odległości zarządzania są cenami, `cost_buffer_per_lot` jest kwotą w walucie rachunku.
Wartości startowe są parametrami podglądu, a nie zweryfikowanymi kosztami brokera.

Odczytany czas kwotowań tego brokera jest przesunięty o +7200 sekund względem UTC;
potwierdzono to eksportem MQL5. Lokalna konfiguracja ma jawną korektę 7200, domyślna 0.
Adapter normalizuje czas danych oraz odwrotnie przelicza zakresy historii i termin
pendingu. Zachowuje surowe czasy brokera. Korekta nie jest zgadywana i nie jest
automatycznym kalendarzem historycznych zmian czasu. Zmiana strefy serwera/DST wymaga
ponownego sprawdzenia; przyszłe lub stare ticki blokują wykonanie. Zmiana korekty
wymaga restartu adaptera i używa osobnej przestrzeni archiwum.

## Dzienny limit

Początek doby ryzyka: 00:00 UTC. `day-start` wymaga potwierdzonego equity z tej chwili:

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

Nie wpisuj bieżącego equity jako początku dnia. Zapis jest niezmienny w danej dobie.
Pracujący kolektor może użyć zapisanego stanu z pierwszych 5 sekund doby UTC; jeżeli
takiego stanu brak, wymaga potwierdzenia operatora. Częstotliwość kolekcji nie gwarantuje
trafienia w to okno. Wpłaty/wypłaty i inne nietransakcyjne zdarzenia blokują nowe wejścia
do uzgodnienia; limit nie jest resetowany w trakcie dnia. Brak baseline blokuje wejścia
i wywołuje regułę anulowania własnych pendingów. Nie blokuje sam w sobie redukcji pozycji.

## Sygnały i aktywacja DEMO

Przenieś kompletny JSON atomowo do `exchange/inbox`, po walidacji:

```powershell
.\.venv\Scripts\python.exe -m trading_ai validate exchange\inbox\plan.json
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json approve exchange\inbox\plan.json --signal ID
```

Zgoda wiąże dokładną treść i rachunek. Wygasłego planu nie można zatwierdzić. Alternatywnie,
po ustawieniu aktywnego trybu i dokładnych parametrów, operator może autoryzować lokalne
strategie na maksymalnie 24 godziny:

```powershell
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json authorize-strategy --until DATA_ISO_Z_TIMEZONE
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json revoke-strategy
```

Przed pierwszym rzeczywistym DEMO potrzebna jest osobna zgoda użytkownika po wynikach
testów. Sama instalacja, logowanie i podłączenie obserwatora nie są zgodą na handel.
Po zgodzie i konfiguracji: `mode:DEMO`, wybrane `trading_enabled:true`, algotrading
i Python API dozwolone w terminalu, zgoda na plan/politykę oraz świadome uruchomienie:

```powershell
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json run --activate DEMO:NUMER_RACHUNKU --watch --interval 10
```

Nie uruchomiono tego polecenia podczas wdrożenia. Algorytmiczne zarządzanie wymaga
działającego procesu, terminala, świeżych danych i przejścia Risk Managera.

## Zarządzanie

BE przenosi SL na cenę otwarcia po progu R; nie jest BE po wszystkich kosztach.
Trailing wyłącznie zacieśnia SL po osiągnięciu co najmniej 1R i odległości trailing.
TP1 realizuje zadaną część początkowych lotów raz. Za mała część/pozostałość blokuje
TP1 i pozostawia ochronę serwerową. TP2 jest także zleceniem ochronnym u brokera.
Unieważnienie używa Bid dla BUY i Ask dla SELL. Pending ma serwerowy termin ważności.

Pełna modyfikacja pendingu zachowuje wolumen, symbol, kierunek i typ. Nowe wejście,
SL/TP, ważność i reguły wymagają nowego ID i niezależnego zatwierdzenia. Ryzyko jest
przeliczane ponownie. Zmiana typu/kierunku wymaga anulowania i nowego planu.

```powershell
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json amend-pending nowy-plan.json --signal NOWE_ID --original-signal STARE_ID --ticket TICKET --activate DEMO:NUMER_RACHUNKU
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json tighten-pending --signal ID --ticket TICKET --sl NOWY_SL --activate DEMO:NUMER_RACHUNKU
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json cancel --signal ID --ticket TICKET --request-id UNIKALNE_ID --activate DEMO:NUMER_RACHUNKU
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json close --signal ID --ticket TICKET --request-id UNIKALNE_ID --volume LOTY --activate DEMO:NUMER_RACHUNKU
```

Pominięcie `--volume` zamyka całość. Każda operacja przechodzi tę samą bramkę. System
wiąże magic, strategię, zlecenie otwarcia i `POSITION_IDENTIFIER`; używa aktualnego
ticketu. Na netting pozycje mieszane, obce wejścia lub odwrócenie blokują przejęcie.
Na hedging zarządza wyłącznie konkretną własną pozycją.

## STOP i restart

| Polityka | Skutek polecenia `stop` |
|---|---|
| manage (domyślna) | Blokuje wejścia, anuluje własne pendingi, kontynuuje reguły pozycji |
| freeze | Blokuje wszystkie lokalne dyspozycje; pendingi i SL/TP na serwerze nadal działają |
| flatten | Blokuje wejścia, próbuje anulować własne pendingi i zamknąć własne pozycje |

STOP jest sprawdzany przed kolejną dyspozycją; nie cofa dyspozycji już wysłanej.
`resume` usuwa marker STOP, ale nie usuwa kwarantanny wykonania. Ctrl+C zatrzymuje
proces i pozostawia zlecenia serwerowe. Brak połączenia/aktywacji może uniemożliwić
również lokalne zamknięcie.

```powershell
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json reconcile
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json reconcile --accept-partial-id open:ID --note 'Opis ręcznej weryfikacji historii i braku reszty zlecenia'
```

Nie kasuj bazy, aby powtórzyć niepewne zlecenie. Historia musi jednoznacznie potwierdzić
wykonanie. Częściowy wynik może zostać przyjęty tylko po weryfikacji faktycznego wolumenu,
ochrony i braku pozostałego pendingu; nie powoduje dosłania wolumenu. Kwarantanna blokuje
wszystkie kolejne dyspozycje lokalne. Serwerowe SL/TP działają niezależnie.
Używaj jednego dziennika na konto. Blokada procesu nie obejmuje innych urządzeń i kont Windows.

W próbach tego brokera termin pendingu został skrócony do pełnej minuty. Weryfikacja
dopuszcza dokładny żądany termin lub początek tej samej minuty (do 59 sekund wcześniej).
Nigdy nie przyjmuje późniejszego terminu. Rzeczywisty termin znajduje się w raporcie
brokera; może skrócić dostępne okno realizacji sygnału.

Kontrola po wykonaniu obejmuje cenę wejścia i zamknięcia (również częściowego),
z limitem zapisanym w chwili dyspozycji. Przekroczenia wykrytego po wykonaniu nie
można cofnąć: powoduje kwarantannę i wymaga wyjaśnienia, bez ponowienia dyspozycji.
Późniejsze zwiększenie limitu w konfiguracji nie zatwierdza historycznego przekroczenia.
Korzystny poślizg jest dozwolony. Starszy zamiar zamknięcia bez zapisanej ceny
odniesienia i limitu nie może być automatycznie uznany za potwierdzony.

## Obserwator wykresów

Skompilowany EA jest w katalogu danych MT5: `MQL5/Experts/TradingAI`. Przeciągnij
TradingAIObserver na jeden wykres; odczytuje wszystkie otwarte wykresy co 30 sekund.
Handel i DLL mogą pozostać wyłączone. Po aktualizacji trzeba podmienić działający
egzemplarz. Eksport: `MQL5/Files/TradingAI`. Odczyt:

```powershell
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json observer
```

Obiekty mają nazwę, typ, tekst i do trzech kotwic ceny/czasu. Bufory wskaźników są
odczytywane z dołączonych wskaźników, od zamkniętej świecy (shift=1), domyślnie do 8
buforów; niedostępny bufor ma null. Brak wskaźnika na wykresie oznacza pustą listę.
To dane pomocnicze; silnik strategii liczy własne wskaźniki z OHLCV. Eksport nie nadaje
obiektom wykresu uprawnień do handlu. Zrzut PNG pokazuje stan wykresu w chwili eksportu.

## Późniejsze wdrożenie LIVE

LIVE nie został aktywowany. Wymaga osobnej decyzji operatora, testów wykonania DEMO,
zweryfikowanych kosztów/kontraktów, baseline, kontroli restartu i planu obsługi awarii.
Techniczne blokady: `mode:LIVE`, `live_enabled:true`, konto na `live_allowlist`, zgodny
realny typ konta i serwer, zgody na plany/politykę, `--activate LIVE:NUMER_RACHUNKU`.
Każda jest sprawdzana przed operacją. Wynik symulacji nie potwierdza rentowności.
