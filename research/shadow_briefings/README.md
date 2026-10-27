> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Archiwum przyszłych briefingów — SHADOW v1

Moduł przyjmuje pełny plik tekstowy UTF-8 (np. Markdown) i opis JSON. Zachowuje oryginalne bajty obu plików, publikację deklarowaną przez źródło, pierwszy lokalny odbiór, kolejne odbiory, identyfikatory planów, kierunek, wejście, SL/TP i decyzje **TRADE, NO TRADE, HOLD, CANCEL**. Służy wyłącznie do zbierania kontekstu i badań. Wszystkie wyjścia mają `mode=SHADOW`, `orders_authorized=false`.

Archiwum nie ma adaptera MT5 ani dostępu do autoryzacji zleceń. Format wyjściowy jest odrzucany przez produkcyjny walidator planów transakcyjnych — sprawdza to test. HOLD/CANCEL są archiwizowanymi decyzjami źródła; ich zapis nie zarządza rzeczywistymi pozycjami i zleceniami.

## Jawne przekazywanie danych

Użytkownik lub przyszły autoryzowany konektor dostarcza pobrany **kompletny** briefing i jego metadane. Interfejs integracyjny to `Archive.ingest(document_bytes, metadata_bytes)` albo poniższy CLI. Moduł nie pobiera historii czatów i nie uruchamia automatycznego monitorowania. Do wykorzystania przyszłego briefingu potrzebny będzie jego rzeczywisty eksport.

Komendy z C:\TradingAI (nazwy plików wejściowych są przykładami):

```powershell
.\.venv\Scripts\python.exe research\shadow_briefings\archive.py ingest --document C:\Briefings\poranny.md --metadata C:\Briefings\poranny.shadow.json
.\.venv\Scripts\python.exe research\shadow_briefings\archive.py as-of --at 2026-10-26T09:05:00+01:00
.\.venv\Scripts\python.exe research\shadow_briefings\archive.py export --id IDENTYFIKATOR_Z_ODBIORU --output C:\Briefings\eksport-001
```

Domyślny magazyn: `C:\TradingAI\research\shadow_briefings\archive\shadow.sqlite3`. Parametr `--root` przed komendą pozwala wybrać oddzielny magazyn. **Nie kierować nowych briefingów SHADOW do produkcyjnego exchange/inbox.** Dotychczasowy kontrakt importu transakcyjnego to osobny mechanizm.

`examples/` zawiera jawnie syntetyczny pełny dokument i metadane pokazujące wszystkie decyzje. Nie są rzeczywistym briefingiem ani sygnałami rynkowymi. Pola wymagane dla TRADE: plan_id, instrument, decision, kind, entry, sl, niepusta lista tp, valid_from, valid_until, reason. Dla pozostałych decyzji sl/tp muszą występować, ale mogą mieć wartość null, jeśli źródło ich nie podało. HOLD/CANCEL wymagają target_plan_id. Brak planów reprezentuje `plans: []`, a nie zmyślony plan.

## Wiarygodność czasu i wersji

- `source.published_at` ma jawny offset. `publication_evidence` opisuje, skąd pochodzi czas. To twierdzenie źródła, nie kryptograficznie zweryfikowana publikacja.
- `first_received_at` generuje proces przy zapisie transakcji. Nie można go nadpisać polem wejściowym. Zapis tego samego dokumentu i tych samych metadanych zachowuje pierwszy odbiór i dodaje obserwację.
- Zmiana choć jednego bajtu dokumentu lub metadanych tworzy osobny rekord, zachowując poprzednią wersję. To także dotyczy zmian formatowania JSON. `source.document_id` wiąże wersje tej samej wiadomości. Moduł nie wybiera automatycznie obowiązującego planu z konfliktujących wersji.
- `as-of` uwzględnia pierwszy odbiór i publikację; nie ujawnia późniejszych wersji ani późniejszych ponownych odbiorów. Briefing zaimportowany po czasie nie staje się informacją dostępną w przeszłości.
- `context_eligible` oznacza tylko poprawność metadanych, deklarowaną kompletność i dostępność do podanego momentu. Nie oznacza zgodności z cenami MT5, aktualności setupu, autoryzacji, kompletności faktycznie potwierdzonej zdalnie ani przydatności strategii. Czasowa ważność planów TRADE jest podana osobno w `plan_states`.
- Niekompletny dokument, nieznana publikacja, błędne metadane i cofnięcie zegara są jawne; wpis pozostaje zachowany, ale jest wyłączony z kwalifikowanego kontekstu. Dane niepoprawne nie są naprawiane przez zgadywanie.
- Zegar odbioru pochodzi z hosta. Bez niezależnego czasu i podpisu źródła nie stanowi dowodu przeciw manipulacji właściciela komputera. Hashy i zabezpieczeń SQLite nie należy traktować jak zewnętrznego notariusza.

## Trwałość i reprodukcja

SQLite zapisuje dokument, metadane i odbiór w jednej transakcji. Triggery odrzucają UPDATE/DELETE rekordów i odbiorów. SHA-256 identyfikatora sprawdzany przy odczycie obejmuje oryginalne dokumenty i metadane. Eksport tworzy JSON, Markdown i dwa dokładne pliki źródłowe; odmawia nadpisania odmiennego eksportu. Każdy nowy eksport z dodatkowymi odbiorami należy zapisać w nowym katalogu. Baza pozostaje źródłem prawdy, ponieważ komplet plików eksportu nie jest transakcją wieloplikową.

Limit pojedynczego wejścia wynosi 16 MiB. Większe wejście jest jawnie odrzucane, nigdy obcinane. Niepoprawne UTF-8 jest zachowywane binarnie i oznaczane jako błąd. Renderowany tekst może zawierać znak zastępczy; plik `.source` zachowuje oryginał.

```powershell
.\.venv\Scripts\python.exe research\shadow_briefings\validate.py
```

Wyniki i hashe: `validation/`. Testy używają odrębnych tymczasowych baz. Porównywane są również hashe zamrożonego kodu/konfiguracji produkcyjnej i raportów tick_validation. Wersję kontraktu określa `schema_version=shadow-briefing-1.0`, a snapshot walidacji zawiera hash implementacji, testów, dokumentacji i przykładów.

Wszystkie wcześniejsze dane pozostają eksploracyjne. Samo dodanie archiwum nie dowodzi przewagi ani nie ustanawia protokołu niezależnej próby forward. Pełny historyczny backtest pozostaje zależny od uzupełnienia ticków, czasu brokera, historycznych warunków kontraktów i kosztów.
