> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Zgodność wykonania i integracja

**GO dla kontrolowanych testów integracji; NO-GO dla deklaracji zgodnego historycznego replay portfela.**

`integrated_control.py` łączy rzeczywiste, zamrożone klasy SignalEngine → RiskManager → ExecutionEngine → PositionManager z `stage2/source_snapshot`. Kontrola hashy jest wykonywana przed importem. Reguły obu strategii nie są optymalizowane. Kontrolowane świece, konto, kontrakt, kalendarz i koszty są jawnie syntetyczne.

| Kontrola | Wynik |
|---|---|
| BUY po Ask, wyjście po Bid | PASS: wejście 100,02; częściowe wyjście 102,07 |
| SELL po Bid, wyjście po Ask | PASS: wejście 100,00; częściowe wyjście 97,99 |
| Pełny łańcuch zarządzania | BUY i SELL: OPEN, TP1, BREAK_EVEN, TRAILING potwierdzone, pozostała część zamknięta przez server TP |
| Wolumen | 0,04 wejście → 0,02 TP1 → 0,02 pozostała część |
| Kalendarz blokujący / brak pliku | Brak wykonania |
| Brak autoryzacji / baseline / połączenia | Brak wykonania |
| Zerowe kwotowanie po wygenerowaniu sygnału | Brak wykonania |
| Osobny czas stron i ponowny odczyt | Brak odświeżania przez Last; brak użycia starej ceny; ograniczona liczba odczytów |

Łącznie **18 testów** w tym katalogu: 8 integracyjnych i 10 prototypu kwotowań. Dodatkowo **186 testów produkcyjnych** przeszło przy zmianie limitu DEMO. Wcześniejsze testy etapów 2 i 7 pozostają dowodem kontrolowanych przypadków SL, luk, opóźnienia i rozłączenia; nie zostały podniesione do rangi kalibracji brokera.

Syntetyczny broker realizuje TP po pierwszej dostarczonej cenie, również gdy jest korzystniejsza od poziomu TP. To założenie fixture, nie potwierdzona reguła historycznych limit-fillów TMS. Nie używamy tego rachunku do oceny rentowności.

## Przerwy zarządzania DEMO

Rzeczywisty Risk Manager sprawdza kwotowanie również przy operacjach zarządzania. Zera i nieaktualny tick zatrzymują więc BE, trailing i zamknięcie programowe. W historii audytu wystąpiło 213 decyzji `bid: outside permitted range` (US100), 1102 decyzje stale/future/crossed oraz 2839 decyzji dotyczących spreadu. Są to **liczby powtarzanych decyzji reguł**, nie liczby awarii ani ich łączny czas.

Nie można uznać wszystkich blokad za nieuzasadnione: przy zerze cena wykonania jest nieznana, a część ograniczeń spreadu/minimalnego lota jest prawidłowa. Słabość adaptera polega na utożsamieniu czasu zdarzenia Last z aktualnością kwotowania. Stan RUNNING nie oznacza, że każdy instrument ma wykonywalną cenę.

Brokerowe SL/TP pozostają niezależne od aplikacji. Audyt wykazał rzeczywiste zamknięcia przez SL i potwierdzone przesunięcia stopów; nie dowodzi to ciągłej dostępności zarządzania aplikacyjnego.

Po restarcie związanym z limitami, od 08:10 UTC do końca obserwowanego zarządzania o 09:58 UTC nie zapisano w zebranym wycinku blokad zarządzania z powodu zer/starego ticka/spreadu. Występowały m.in. prawidłowe blokady TP1 przy minimalnym locie. O 12:44:20–12:44:40 UTC silnik RUNNING, 0 pozycji, 0 zleceń, 0 nierozstrzygniętych operacji; 21/21 punktowych snapshotów miało dodatni Bid/Ask. Ta próbka nie certyfikuje stabilności ciągłej.
