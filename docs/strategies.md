> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Jawne strategie i walidacja wyników

Parametry są w sekcji `engine`. Domyślnie H1, 200 zamkniętych świec, 60 świec
struktury, 20 świec wsparcia/oporu. Bieżąca świeca nie jest używana do wskaźników.
Wsparcie/opór dla wybicia nie zawiera świecy sygnałowej.

`local_breakout_v1`: BUY po zamknięciu ponad poprzednim oporem o co najmniej
0,1 ATR, przy trendzie UP, EMA20 > EMA50, dodatnim histogramie MACD i RSI 50–80.
SELL jest symetryczny: DOWN, EMA20 < EMA50, histogram ujemny, RSI 20–50.

`local_false_breakout_v1`: wybicie knotem i zamknięcie z powrotem w zakresie,
przy konsolidacji (zakres <= 6 ATR). Fałszywe wybicie dołem i RSI < 50 daje BUY;
górą i RSI > 50 daje SELL. Nie jest to model uczenia maszynowego ani deklaracja
przewagi inwestycyjnej. Jeśli obie gałęzie pasują, pierwszeństwo ma breakout.

SL leży poza ekstremum świecy sygnałowej i co najmniej 1,5 ATR od aktualnego wejścia,
z uwzględnieniem siatki cenowej i minimalnych odległości brokera. TP2 = 2R,
TP1 = 1R dla połowy początkowego wolumenu, BE po 1R, trailing = 1 ATR.
Ważność = 2 interwały od zamknięcia świecy, maksymalnie 24 godziny. Ryzyko <= 0,25%.
ID jest związane z symbolem, strategią, świecą i konfiguracją; istniejący plan nie
zmienia treści przy każdym ticku. Zmiana planu wymaga nowego ID.

Autoryzacja strategii wiąże hash parametrów, ryzyka, symboli, rachunku, trybu i korekty
czasu. Wygasa najpóźniej po 24 godzinach. Zmiana konfiguracji lub `revoke-strategy`
blokuje nowe wejścia; zachowuje przypisane reguły ochrony już otwartych pozycji.
Import ChatGPT nie może sam nadać sobie tej autoryzacji.

## Backtest

Replay wykorzystuje archiwum OHLCV, sygnał z zamkniętych świec i wejście na otwarciu
kolejnej. Gdy świeca dotyka SL i TP, przyjmuje SL jako pierwszy. Nowy trailing/BE
obowiązuje od następnej świecy. Uwzględnia spread, poślizg, prowizję i uproszczony swap.
Brak świeżego setupu po przerwie sesyjnej jest pomijany i raportowany.

```powershell
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json backtest --instrument GOLD --contract examples\backtest-contract.json --costs examples\backtest-costs.json
```

Pliki przykładowe są wyłącznie ilustracyjne. `cash_per_price_unit_per_lot` jest jawnym
przelicznikiem pieniężnym; rzeczywiste historyczne FX i zmienne koszty wymagają osobnych
danych. OHLC nie modeluje kolejki zleceń, tickowego przebiegu wewnątrz świecy, zmian
depozytu ani harmonogramu swapów. To badanie jednej strategii/instrumentu, nie pełny
historyczny replay rachunku wielu instrumentów.

`tools/validate_strategies.py` uruchamia dwa ilustracyjne scenariusze kosztów na
zarchiwizowanych świecach brokera. Używa aktualnego przelicznika kontraktu i stałych
kosztów, więc nie dowodzi historycznej rentowności. JSON zawiera transakcje, R,
krzywą equity, obsunięcie i ograniczenia. Przed oceną inwestycyjną potrzebna jest
dłuższa próba poza okresem doboru parametrów oraz historyczne koszty/FX.
