> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Odtworzenie

Z `C:\TradingAI`:

```powershell
.\.venv\Scripts\python.exe research/tick_validation/integrated_replay/verify.py
```

Wykonywane lokalnie: 23 testy, kontrola hashy artefaktów etapów 11 i execution_readiness, źródeł zamrożonych i plików aktywnego DEMO. Bez MetaTrader5, internetu i zleceń rzeczywistych. Zmiana aktywnej konfiguracji w przyszłości wymaga nowego audytu; nie należy zmieniać starych hashy.

`adapter.Replay` przyjmuje konfigurację, `PortfolioBroker`, iterator uporządkowanych zdarzeń UTC, osobny Journal, granice okna i jawny kapitał/baseline wirtualnego rachunku. `controls.py` pokazuje kompletny przykład obu stron i wielu instrumentów. Konto musi być `SIMULATOR`, terminal `IN_MEMORY_ONLY`.

`compare_control.py` agreguje pełną godzinę tego samego kontrolnego strumienia dla starego backtestera. Ostateczne wyniki: `control-results.final.json` oraz `control-comparison.final.json`. Wcześniejsze pliki z `prototype`, `before` lub bez `.final` są zachowanymi wynikami pośrednimi; nie są podstawą końcowego raportu.

`run_report()` zapisuje diagnostykę niepełnego przebiegu bez nadawania częściowemu rachunkowi statusu poprawnego backtestu. `preflight.py` dokumentuje konkretne niespełnione wymagania 22.10; nie ma flagi wymuszającej historyczne GO mimo braków.

Nie wykonywać regeneracji w zamkniętym katalogu. Do nowych danych/założeń skopiować źródła do nowego jawnie wersjonowanego eksperymentu, zachowując ten manifest.
