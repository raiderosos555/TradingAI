# Edge program — research offline

Nowe pytanie o wartość dodaną wskaźników, 36 zamrożonych porównań, bez grids.
Czytaj EXPERIMENT_RESULTS.md; interpretacja wyłącznie jako markout Last.
Nowy zakres z dodatkowymi danymi: `../alternative_data_edge/`.

Z katalogu tego badania, istniejącym Pythonem projektu:

```powershell
..\..\.venv\Scripts\python.exe -m unittest test_experiments.py -v
..\..\.venv\Scripts\python.exe experiments.py --root ..\.. --out private\results-reproduction.json
..\..\.venv\Scripts\python.exe render_results.py --root ..\..
```

Obliczenie wymaga prywatnych14 OHLC JSON, wcześniejszego manifestu
market_mechanisms/private/feasibility.json oraz cost-sample-20261022/summary.json.
Nie odtworzy się z samego oczyszczonego GitHuba bez uprawnionych danych.
Nowa ścieżka wyniku chroni stary plik; nie powtarzać obliczeń bez powodu.
Renderer czyta oryginalny results-v1.json. Surowe dane, rekordy rachunku,
próbki API i wyniki szczegółowe zostają w private/.

acquire_samples.py wykonuje4 małe publiczne żądania. probe_history.py jest
zapisem pierwszej nieudanej sondy: limity liczby rekordów **nie ograniczają
czasu blokującego IPC**. Nie uruchamiać jej ponownie w aktywnym terminalu;
nowa ograniczona czasowo sonda znajduje się w alternative_data_edge.
Żaden skrypt badawczy nie wysyła zleceń ani nie zmienia strategii.

Sześć testów mechaniki przeszło przed obliczeniami. Nie są dowodem edge.
Podział chronologiczny nie przywraca niezależności wcześniej oglądanym danym.
Kod/protokół i hashe wejść są jawne; brak danych nie oznacza wyniku zero.
