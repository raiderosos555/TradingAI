> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Odtworzenie kontroli

Katalog roboczy: `C:\TradingAI`. Wszystkie testy mają własne katalogi stanu, zmienną LOCALAPPDATA tylko w procesie testowym i broker w pamięci. Nie włączają MetaTrader5 ani nie wysyłają nowych zleceń na rachunek.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s research/demo_recovery -p test_recovery.py -v
.\.venv\Scripts\python.exe -m unittest discover -s research/demo_recovery -p test_window.py -v
.\.venv\Scripts\python.exe research/demo_recovery/window_audit.py --out research/replay_readiness/20261027
```

Ostatnie polecenie przed 27.10 16:00 UTC zapisuje PENDING_WINDOW_END. Po tym terminie wykonuje audyt lokalny. Nie nadpisuje istniejącego REPORT.md — dla rewizji należy wskazać nowy katalog.

Regresja istniejącego runtime na kandydacie:

```powershell
@'
import sys, pathlib, unittest
p=pathlib.Path('research/demo_recovery/candidate').resolve()
sys.path.insert(0,str(p))
import trading_ai.runtime
assert pathlib.Path(trading_ai.runtime.__file__).resolve().is_relative_to(p)
r=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.discover('tests',pattern='test_runtime.py'))
raise SystemExit(not r.wasSuccessful())
'@ | .\.venv\Scripts\python.exe -
```

`prepare.py` tworzy kopię tylko raz i odmawia zastąpienia istniejącej. W pierwszym uruchomieniu kopię config.json dodano osobno po ujawnieniu brakującej zależności fixture; obecny skrypt uwzględnia ją przy tworzeniu nowego środowiska. Pierwsze błędy testów wynikały z brakującej kopii konfiguracji i ubogiej historii SimBroker; fixture uzupełniono o pola identyfikacyjne obecne w odpowiedzi brokera. Nie zmieniano klas produkcyjnych w celu uzyskania zielonych testów. Końcowe wyniki: 13 + 21 + 5.

Testy zapisują własne dowody (`collision-test-evidence.json`); przed ponowną próbą zachować istniejący katalog raportu lub utworzyć kopię całego środowiska badawczego. Manifest poświadcza stan przekazany w tym zadaniu, nie późniejsze wyniki kolejnych uruchomień.

Testy Harmonogramu były uruchomione jako osobne `TradingAI-Lab-Recovery-*` i usunięte. Nie uruchamiać instalatora produkcyjnego `tools/install_demo_runtime.ps1` ani nie stosować patcha na aktywnym źródle bez zgody użytkownika. XML i wyniki testów są zachowane; przy ponownej próbie używać wyłącznie nazw z prefiksem Lab, skryptu lab_exit.py i katalogów badawczych.

Automatyzacja jednorazowego audytu: `tradingai-audyt-okna-27-10`, 27.10.2026 17:10 Europe/Warsaw, ten sam czat. Nie jest nadzorcą DEMO i nie ma uruchamiać ani modyfikować silnika. Zbieranie danych odbywa się nadal lokalnie przez istniejące zadanie Windows.
