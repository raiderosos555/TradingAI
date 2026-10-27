> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Etap 2A — kontrolowane testy polityki wykonania

Data badania: 2026-10-25. **35 testów poprawnych; pełna zgodność z wykonaniem brokera pozostaje niepotwierdzona.** Nie uruchomiono pełnego backtestu, nie optymalizowano strategii, nie wysłano zleceń do MT5. Raport uzupełnia zamrożony raport etapu 1 w katalogu nadrzędnym.

## Metoda i granice wniosku

`source_snapshot/` zawiera 26 plików kodu i konfiguracji z SHA-256. Harness używa rzeczywistych, zamrożonych klas PositionManager, RiskManager i ExecutionEngine z brokerem wyłącznie w pamięci. Oczekiwane ceny, wolumeny i wyniki pieniężne zapisano w testach jako niezależnie obliczone wartości. Jest to test zgodności adaptera i przebiegu reguł, **nie niezależna implementacja całej polityki, empiryczny test realizacji brokera ani walidacja strategii**.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

## Wyniki

| Obszar | Potwierdzony wynik kontrolowany |
|---|---|
| Wejście BUY / SELL | BUY po Ask, SELL po Bid; spread od razu wpływa na equity |
| Wyjście SELL | Po Ask, także gdy sam Bid nie przekroczył SL |
| TP1 | Część oryginalnego wolumenu zaokrąglana w dół; jednokrotna realizacja; poprawna reszta |
| TP1 → BE → trailing | Po jednej operacji w cyklu; BUY i SELL przetestowane |
| BE | SL na cenie otwarcia; nie zapewnia wyniku netto zero po prowizji |
| Trailing | BUY zaokrąglany w dół, SELL w górę; stops/freeze blokują nieprawidłową zmianę |
| TP2 | Serwerowe zamknięcie całej pozycji przy skoku przez oba TP; osobny test jednostkowy reguły aplikacji TP2 |
| SL / luka | Cena pierwszego dostępnego kwotowania, bez fikcyjnej realizacji na przeskoczonym poziomie SL |
| Spread | Blokuje nowe wejście i działania aplikacji, nie wyłącza już ustawionego SL serwera |
| Minimum lota | Za mały wolumen blokuje wejście; niepoprawna częściowa realizacja zachowuje SL/TP |
| Ryzyko | Weryfikacja equity z floating PnL i prowizją, dziennego limitu, baseline nowej doby UTC, cash adjustment i margin |
| Priorytety | STOP_CLOSE poprzedza TP1; invalidation może zamknąć przed SL |
| Rozłączenie | Brak BE aplikacji; serwer nadal może zamknąć; reconnect nie dubluje wyjścia |
| Niepewne wysłanie | Trwały intent blokuje automatyczne ponowienie po przerwaniu send |
| Chronologia | Zachowana kolejność rekordów z tą samą milisekundą; cofnięcie czasu odrzucane |
| Brak ticków | Brak interpolacji i przypisywania wcześniejszego czasu realizacji; nie dowodzi braku zdarzeń w luce |

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

To przykłady arytmetyki testowej, a nie wyniki historyczne lub szacunek rentowności.

## Stary OHLC a polityka produkcyjna

Przegląd zamrożonego `trading_ai/backtest.py` potwierdza różnice wymagające usunięcia w przyszłym replay:

1. Stary model utożsamia OHLC z Bid i dodaje stały spread; etap 1 wykazał Last dla siedmiu kontraktów.
2. Stary model może w jednej świecy wykonać TP1 i zastosować kandydatów BE/trailing; produkcyjny manager kończy cykl po jednej potwierdzonej operacji.
3. Stary model realizuje TP1 na poziomie TP1 minus slippage; aplikacja używa dostępnego kwotowania w chwili cyklu.
4. Stary model wylicza próg R z sygnałowego `entry`; RiskManager używa `entry_reference` zapisanego przy otwarciu. To może być różna wartość.
5. Stary trailing nie odtwarza pełnej siatki ceny i brokerowych stops/freeze. Produkcja sprawdza je niezależnie.
6. Stary model wyznacza baseline dnia z własnego bieżącego equity i stałych kosztów; produkcja wymaga potwierdzonego baseline UTC. Przy niezweryfikowanym mapowaniu czasu historycznego nie można uznać tych dni za równoważne.

Jest to porównanie kodu i przypadków kontrolowanych. **Nie obliczono nowych PF, expectancy, drawdown ani różnic liczby transakcji.** Porównanie historii wymaga dalszych danych i bramek z REMAINING_LIMITATIONS.md.

## Artefakty i odtworzenie

Uruchomienie z `C:\TradingAI`:

```powershell
.\.venv\Scripts\python.exe research\tick_validation\stage2\run.py
```

Konfiguracja: `config.v1.json`. Testy: `test_parity.py`. Wynik: `tests.json`, `tests.txt`. Pełne konfiguracje przypadków, kwotowania, decyzje, ledger i końcowe stany: `traces.json`. Hash kodu produkcyjnego przed/po: `source_manifest.json`, `production_integrity.json`. Hash artefaktów: `manifest.json`.

Nowe wersje produkcji wymagają nowego snapshotu/etapu; `freeze.py` nie nadpisuje odmiennej kopii. Stan roboczy SQLite każdego przypadku powstaje w lokalnym `scratch/` i jest usuwany po teście. Produkcyjne state/exchange oraz konfiguracje nie są modyfikowane.
