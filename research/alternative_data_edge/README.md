# Alternative data edge — lokalny, odtwarzalny research

Wyniki i decyzje: EDGE_VERDICT.md. Wszystkie12 porównań: EXPERIMENTS.md.
Nie są as-of replay ani P&L brokera. Bez podpięcia do aktywnego silnika.

```powershell
..\..\.venv\Scripts\python.exe -m unittest test_alternative.py -v
..\..\.venv\Scripts\python.exe alternative_experiments.py --root ..\.. --out private\results-reproduction.json
..\..\.venv\Scripts\python.exe render_reports.py --root ..\..
```

Uruchamiać z tego katalogu. Wymagane istniejące private/samples-v1 z manifestem,
private/results-v1.json z poprzedniego edge_program i uprawnione OHLC lokalne.
Publiczny kod nie daje praw do danych. Czysty GitHub bez private nie odtworzy
liczb samodzielnie. Nowe pobranie bieżącego CSV może różnić się od zamrożonego
hashem; do reprodukcji używać przechowanej uprawnionej kopii, nie aktualizacji.

acquire.py wykonuje tylko5 małych CSV i2 próbki COT po1rekordzie, bez retries,
klucza, kont, paginacji ani ZIP. Każda odpowiedź≤1MiB. Nie uruchamiać rutynowo.
broker_probe.py to wyłącznie odczyt krótkich zakresów,15s na proces sondy,
abort całej kampanii na pierwszy timeout; wymaga już działającego terminala.
Nie uruchamiać dalszej kampanii na aktywnej sesji bez konkretnego celu.

Kod wykorzystuje NumPy i istniejące helpery edge_program, nie nowe zależności.
Testy: causal lag, brak danych vs cash, zgodność dat VIX/VIX9D, algebra kosztu
i liczba zaplanowanych porównań. Fixtures syntetyczne wyłącznie do testów kodu.
Szczegóły prywatnych odczytów rachunku nie są publikowane.

Publikacja: tylko wymienione MD/PY po przeglądzie i skanie. **Push wymaga
nowej zgody właściciela zgodnie z ostatnią instrukcją**. Raw CSV/JSON, konta,
historia wykonania i stan kolektora pozostają poza repozytorium publikacyjnym.
