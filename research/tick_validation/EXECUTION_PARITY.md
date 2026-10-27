> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Zgodność wykonania — stan po etapie 1

Etap 1, raport 2026-10-25T07:50:23.638758+00:00. Wyłącznie badanie danych, cen i czasu. Brak zleceń, zmian produkcyjnych, strojenia strategii i pełnego ponownego backtestu. Wszystkie dane historyczne są eksploracyjne.

**Nie potwierdzono jeszcze zgodności pełnego symulatora z Position Managerem.** Zakończono testy prymitywów cenowych i czasu. Reguły produkcyjne odczytano z `trading_ai/manager.py`, `risk.py` i `execution.py`; nie zmieniano ich.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

Production PositionManager sprawdza STOP_CLOSE, INVALIDATION, TP2, TP1, BREAK_EVEN, TRAILING, po pierwszej potwierdzonej operacji czeka na następny cykl. Risk Manager ogranicza operacje aplikacji przy szerokim spreadzie, sprawdza freeze/stops, a dla TP1 wolumen i minimalną resztę. SL/TP już na serwerze nie mogą być mylone z operacją aplikacji zablokowaną przez spread. Tego rozróżnienia pełny replay jeszcze nie implementuje.

Testy automatyczne: 30 uruchomionych, 0 błędnych asercji, 0 błędów wykonania. Szczegóły w `test_model.py`, `tests.txt` i `tests.json`. Nie są testami rentowności ani pełnej zgodności Risk/Position Managera.

Polecenie offline: `.\.venv\Scripts\python.exe -m unittest discover -s research\tick_validation -p test_model.py -v`. Fixtures testowe są jawnie syntetyczne i nie zastępują brakujących historycznych ticków.
