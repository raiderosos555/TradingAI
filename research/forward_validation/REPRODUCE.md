> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Uruchomienie i kontrola

Wszystkie polecenia z `C:\TradingAI`. Nie uruchamiać ponownie `register.py` ani `install.ps1` dla istniejącego protokołu.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s research/forward_validation -p 'test_*.py' -v
.\.venv\Scripts\python.exe -m unittest discover -s research/forward_context -p 'test_*.py' -v
.\.venv\Scripts\python.exe research/forward_validation/verify_capture.py state/forward_validation/cohort-20261026-v1 --out research/forward_validation/verification.new.json
.\.venv\Scripts\python.exe research/forward_validation/review.py state/forward_validation/cohort-20261026-v1
Get-ScheduledTask -TaskName TradingAI-Forward-Evidence
Get-Content state/forward_validation/cohort-20261026-v1/status.json
```

`verify_capture.py` kontroluje łańcuch odbiorów, snapshot SQLite, hashe paczek i surowych danych, kolejność, nakładki, źródła oraz dowody czasu. Nie normalizuje ticków, nie usuwa luk i nie wysyła zleceń. Rosnące dane powodują naturalną zmianę wyniku audytu; poprzednie raporty należy zachować.

`review.py` jest lekkim podsumowaniem kolekcji. Nie odtwarza strategii i nie twierdzi, że sama zgodność nakładek dowodzi kompletności.

`protocol.v1.json` jest zamrożony. Kod rejestratora jest sprawdzany przy starcie; jego zmiana wymaga jawnej wersji/amendmentu. Kod analizy dodany po rejestracji ma osobny manifest w katalogu badania i nie zmienia kolekcji ani zasad strategii.

Zatrzymanie tylko rejestratora: utworzyć `state/forward_validation/cohort-20261026-v1/STOP_COLLECTOR`. Dla trwałego wyłączenia także wyłączyć zadanie `TradingAI-Forward-Evidence`; inaczej Harmonogram będzie ponawiał start zakończonego procesu. Wznowienie: usunąć wyłącznie ten plik, włączyć i uruchomić to samo zadanie. Silnika i terminala nie zatrzymywać w celu obsługi rejestratora. Kontrolowany test takiego wznowienia wykonano 26.10 w okresie kalibracyjnym.

Odtwarzalność danych: każda paczka ma `request.json`, surowy `*.ticks.json.gz`, specyfikacje, kalibracyjne kalkulacje, broker.json, result.json i manifest; łańcuch receipts wskazuje hash manifestu. Błędy, czas odbioru i zmiany kontekstu pozostają w SQLite. Po awarii niekompletna paczka nie przesuwa kursora. Mismatch nakładki zapisuje błąd, a kolekcja przyszłych danych trwa; nie oznacza to akceptacji uszkodzonego odcinka.
