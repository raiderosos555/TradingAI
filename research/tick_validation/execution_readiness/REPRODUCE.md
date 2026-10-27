> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Odtworzenie lokalne

Z katalogu `C:\TradingAI`:

```powershell
.\.venv\Scripts\python.exe research/tick_validation/execution_readiness/verify.py
.\.venv\Scripts\python.exe -m unittest discover -s research/tick_validation/execution_readiness -p test_*.py -v
```

Pierwsze polecenie weryfikuje manifest bieżącego badania, niezmienność zahashowanych plików etapu 11, zamrożonych źródeł oraz jedyną autoryzowaną zmianę konfiguracji DEMO. Wykonuje też 18 testów bez kontaktu z MT5. Późniejsza autoryzowana zmiana aktywnego kodu/config może wymagać nowego audytu; nie wolno wtedy przepisywać starych hashy.

`integrated_control.py` odtwarza dwa jawnie syntetyczne przebiegi czterech silników. `prepare.py` wyciąga 200 poprzednich H1. `analyze.py` liczy lokalnie jakość FX i analizuje zapisane odczyty/dziennik. Te skrypty zapisują wyniki: do ponownego eksperymentu używać kopii katalogu, nie nadpisywać zamkniętego manifestu.

`collect_fx.py`, `collect.py` i `run_demo_audit.py` służyły do ograniczonych czasowo odczytów MT5. Nie należy ich ponownie uruchamiać w zamkniętym katalogu. Dane źródłowe, błędy pierwszych prób, pełne próbki i ślady kontrolne zostały zachowane; brak dowodu nie jest zastępowany domyślną wartością.

Nie istnieje jeszcze zatwierdzony parametr umożliwiający pełny replay historyczny mimo brakujących danych. `config.v1.json` dokumentuje ten stan. Weryfikator nie stanowi uprawnienia do handlu i nie może zmienić decyzji NO-GO na GO na podstawie samych przechodzących fixtures.
