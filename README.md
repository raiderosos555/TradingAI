# TradingAI — kod i raporty badawcze

Prywatne repozytorium do przeglądania kodu Python/MQL5, testów i zanonimizowanych
raportów. Ta kopia jest oddzielona od działającej instalacji. Synchronizacja Git
nie wdraża zmian do DEMO, nie uruchamia MT5 i nie autoryzuje handlu.

## Stan badań

Przewaga inwestycyjna nie została potwierdzona. Najnowsze wnioski w tej kopii:

- [Odzyskiwanie DEMO po rozłączeniu](research/demo_recovery/REPORT.md)
- [Propozycja nadzoru — niewdrożona](research/demo_recovery/PROPOSAL.md)
- [Przyszła walidacja i zbieranie danych](research/forward_validation/REPORT.md)
- [Rdzeń replay](research/tick_validation/integrated_replay/REPORT.md)
- [Audyt przewagi](research/edge_audit/VALIDATION_REPORT.md)

Raporty opisują stan w podanych w nich datach. GitHub nie odczytuje na żywo rachunku,
kwotowań ani procesu DEMO. NO-GO dotyczące odporności, kompletności danych i
wiarygodności replay nie jest oceną rentowności strategii.

## Zawartość i ograniczenia

`trading_ai/` to rdzeń, `mql5/` to źródła obserwatora, `tests/` to testy offline,
`tools/` to narzędzia projektu, `research/` to kod badań i raporty.
Pełne ticki, dzienniki, wykonania, konfiguracje rachunku, autoryzacje i oryginalne
manifesty dowodowe pozostają lokalnie. Odnośniki raportów do tych plików nie będą
dostępne na GitHub. Zamrożone kopie kodu służą do audytu; same nie odtworzą badań
wymagających wyłączonych prywatnych danych lub manifestów.

Usunięte fragmenty raportów są oznaczone. Identyfikatory i ścieżki terminala w
kopii kodu są przykładowe. Historyczny domyślny kapitał w `portfolio_research.py`
zastąpiono syntetycznym `100000.0` z powodów prywatności; nie przeliczano raportów
i nie należy porównywać nowych wyników uruchomionych z tym domyślnym kapitałem
z historycznymi. Reguły strategii, Execution Engine, Risk Manager i Position
Manager nie zostały zmienione. Szczegóły: [zasady synchronizacji](SYNC.md).

## Testy offline

W nowym katalogu środowiska, z Pythonem 3.11+:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m unittest discover -s sync_tools -p test_scan.py -v
```

Nie jest potrzebne połączenie z MT5. `config.json` oraz
`examples/config.demo.example.json` są szablonami DRY_RUN z wyłączonymi silnikiem,
zbieraniem i LIVE, bez konta i autoryzacji. Nie kopiować ich na aktywną instalację.
Nie uruchamiać narzędzi wdrożeniowych ani badawczych wskazujących lokalną
instalację tylko po to, aby przejrzeć repozytorium.

## Dostęp ChatGPT

Repozytorium pozostaje prywatne. Należy udostępnić je oficjalnemu połączeniu GitHub
w aplikacji, z dostępem do tego repozytorium. Sama obecność adresu repozytorium
w rozmowie nie nadaje dostępu. Po zatwierdzonym pushu kod i raporty można czytać
przez połączenie GitHub; świeżość zależy od ostatniej zatwierdzonej synchronizacji.
