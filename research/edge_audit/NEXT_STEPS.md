> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# NEXT_STEPS — decyzja i kolejność prac

Stan audytu: 2026-10-24T18:09:09.311248+00:00. Badanie offline; bez nowych zleceń, zmian DEMO, konfiguracji, Execution Engine i Risk Managera. Kwoty w PLN, o ile nie zaznaczono inaczej.

**Wykryty błąd ceny wykonania:** wszystkie siedem kontraktów zgłasza `chart_mode=1` (Last). Rekonstrukcja pełnej godziny 22.10 13:00–14:00 UTC z ticków odtworzyła zapisany OHLC dokładnie z Last dla każdego instrumentu; OHLC Bid różni się. Oba replays zakładają OHLC Bid. Poniższe PnL/PF są więc wynikami oryginalnego, niepoprawnie przyjętego modelu ceny, a nie zweryfikowanego wykonania. Nie naprawiono ich po cichu; wymagana jest osobna walidacja na Bid/Ask.

**Rekomendacja: kontynuować badania; nie ogłaszać przewagi ani nie wybierać US100 do produkcji na podstawie rankingu.** Obecne warianty nie spełniają kryteriów stabilności i niezależnej walidacji. Odrzucić ich promocję jako „zyskownej strategii”; nie jest to dowód, że żadna strategia na tych rynkach nie może działać.

1. Uzgodnić czas brokera i UTC na surowych tickach, uwzględniając historyczne DST. Uzupełnić historyczne sesje, tryb Bid/Last, zmiany kontraktów, koszty, rollover i przewalutowanie. Artefakt końcowy: wersjonowany manifest z coverage, brakami i źródłami, bez uzupełniania luk fikcyjnymi świecami.

2. Zbudować osobny replay tickowy wykorzystujący zamrożone reguły rzeczywistego Position Managera oraz audytowalny odpowiednik kontroli ryzyka. Porównać wejścia, TP1→TP2, BE, trailing, invalidation, limit spreadu dla zamknięć, minimum lot, slippage i dzienną bazę. Najpierw porównanie na stałych przypadkach; nie zmieniać działającego Risk/Execution bez osobnego uzasadnienia i zgody.

3. Zachować trzy ograniczone hipotezy z EDGE_HYPOTHESES; nie przeszukiwać dziesiątek progów do pierwszego dodatniego PF. Obecny SL 1,75 w pullback jest tylko ciekawostką eksploracyjną, nie nowym zwycięzcą. Protokół kolejnego badania należy zamrozić przed zobaczeniem nowych wyników.

4. Archiwizować przyszły briefing/news jako jawny eksport/API z pierwszym czasem odbioru, źródłem, wersją i hashem, osobno od uprawnień do handlu. Zachować również NO TRADE i odwołania HOLD/CANCEL. WIG20/DAX dopiero po weryfikacji dostępnego kontraktu brokera i zgodności rodzaju rynku; nie utożsamiać indeksu cash, futures i CFD.

5. Przygotować przyszły shadow/forward na późniejszych, niewykorzystanych danych: co najmniej 3 miesiące i 100 transakcji jako minimum, potem ocena wystarczalności próby. Zamrożone okresy oceny, wspólny portfel, rzeczywiste koszty i kryterium dodatniej dolnej granicy expectancy po korekcie prób. Brak minimalnej liczby lub szeroki CI oznacza „brak rozstrzygnięcia”, a nie przewagę. Oceniać także stabilność, koncentrację i koszty ×2.

6. Warunek odrzucenia/zmiany hipotezy: straty w kolejnych wcześniej ustalonych okresach, brak odporności na sąsiednie parametry/koszty, dominacja kilku transakcji albo naruszenia reguł. Każda zmiana parametrów rozpoczyna nowy, oznaczony eksperyment; jego wcześniejszy test nie staje się ponownie holdoutem.

Działające DEMO pozostawiono w istniejącym stanie i z dotychczasową autoryzacją. Ten audyt nie wyłączył ani nie włączył jego przyszłych zleceń, nie podniósł limitów i nie jest nową zgodą na handel. Stan WAITING i stara dzienna baza wymagają ponownej oceny przez istniejące bramki na początku sesji; nie zostały zastąpione ręcznym obejściem.

## Pakiet i odtworzenie

Sześć raportów: DATA_AUDIT, TRADE_DIAGNOSTICS, US100_VS_OIL, EDGE_HYPOTHESES, VALIDATION_REPORT, NEXT_STEPS. Główne liczby: `trades_enriched.csv`, `run_statistics.csv`, `subgroup_statistics.csv`, `matched_trade_cost_stress.csv`, `observed_cost_sensitivity.csv`, `sensitivity.csv`, `walk_forward.csv`, `uncertainty_sensitivity.csv`. Każdy ma odpowiednik JSON. Źródła, hashe, snapshot dziennika oraz historyczne wyniki są zachowane. Pełne kopie 130 pierwotnych plików są dodatkowo w `inputs/frozen-originals/`.

W katalogu C:\TradingAI uruchomić kolejno poniższe polecenia. Nie łączą się z MT5; wymagają zachowanych źródeł danych i Pythona z numpy. Dwa osobne skrypty `download_context.py` / `read_contracts.py` są jedynie opcjonalnym odczytem MT5 i nie są potrzebne do odtworzenia zapisanej analizy.

```powershell
.\.venv\Scripts\python.exe research\edge_audit\analyze.py
.\.venv\Scripts\python.exe research\edge_audit\refresh_statistics.py
.\.venv\Scripts\python.exe research\edge_audit\validate_isolated.py
.\.venv\Scripts\python.exe research\edge_audit\briefing_research.py
.\.venv\Scripts\python.exe research\edge_audit\facts.py
.\.venv\Scripts\python.exe research\edge_audit\write_reports.py
.\.venv\Scripts\python.exe research\edge_audit\verify_audit.py
```

Dodatkowy stres oparty na zebranym spreadzie odtwarza polecenie `.\.venv\Scripts\python.exe research\edge_audit\observed_costs.py` przed generowaniem raportów. `price_basis_check.json` jest zachowanym dowodem z ticków; jego ponowne pobranie przez `check_price_basis.py` wymaga wyłącznie odczytu MT5 i nie jest konieczne do odtworzenia raportów.

Pełnej historycznej reprodukowalności 14 najstarszych przebiegów nie można odzyskać bez dawnego źródła/config. Ich dane wynikowe są zachowane, metryki policzone, brakujące atrybuty jawnie oznaczone. Wyniki nowszych przebiegów mają opisany zakres kontroli zgodności.
