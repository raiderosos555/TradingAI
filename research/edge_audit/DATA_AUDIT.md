> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# DATA_AUDIT — dane i metodologia

Stan audytu: 2026-10-24T18:09:09.311248+00:00. Badanie offline; bez nowych zleceń, zmian DEMO, konfiguracji, Execution Engine i Risk Managera. Kwoty w PLN, o ile nie zaznaczono inaczej.

**Wykryty błąd ceny wykonania:** wszystkie siedem kontraktów zgłasza `chart_mode=1` (Last). Rekonstrukcja pełnej godziny 22.10 13:00–14:00 UTC z ticków odtworzyła zapisany OHLC dokładnie z Last dla każdego instrumentu; OHLC Bid różni się. Oba replays zakładają OHLC Bid. Poniższe PnL/PF są więc wynikami oryginalnego, niepoprawnie przyjętego modelu ceny, a nie zweryfikowanego wykonania. Nie naprawiono ich po cichu; wymagana jest osobna walidacja na Bid/Ask.

**Nie potwierdzono wiarygodnej, powtarzalnej przewagi.** Dane nadają się do diagnozy i odtwarzania symulacji, lecz brak pełnego historycznego modelu wykonania i kosztów uniemożliwia certyfikację rentowności. Historia była wielokrotnie oglądana; nie jest niezależnym holdoutem.

## Zakres i pochodzenie

Rzeczywiste źródła: `trading_ai/strategy.py`, `backtest.py`, `portfolio_research.py`, `analyzer.py`, `manager.py`, `risk.py`, `execution.py`, `broker.py`; konfiguracje w katalogu głównym. Dane H1 i manifest: `exchange/research/history-20261024/`. Starsze wyniki: `exchange/backtests/`. Archiwum briefingu: `exchange/briefing-archive/`. Dziennik: `state/journal.sqlite3`; bieżące logi: `state/runtime/`.

Zidentyfikowano 88 plików zawierających listę transakcji: 14 starszych, 28 walidacyjnych, 28 ablacji i 18 portfelowych. Łącznie 4294 rekordy — wielokrotnie te same okresy/sygnały, a nie 4294 niezależne obserwacje. Zachowano kopie 88 wyników w `inputs/artifacts/`, źródeł i konfiguracji w `source_snapshot/`, kopię SQLite przez read-only backup oraz SHA-256 130 pierwotnych plików. `integrity_check.json` potwierdza ich niezmienność.

Manifest i wszystkie siedem hashy danych H1 przeszły kontrolę. 21 234 świece H1; zamówiony zakres 27.04–24.10.2026, ostatnie świece 23.10. Rok kontekstu H4/D1 pobrano oddzielnie wyłącznie do odczytu. Pliki `data_quality.json/csv` oraz `inputs/gaps-*.json` zawierają dokładne zakresy i luki.

| Rynek | H1 N | Pierwsza świeca | Ostatnia świeca | Luki >1h | Największa luka h |
|---|---|---|---|---|---|
| GOLD | 2973 | 2026-04-27T00:00:00+00:00 | 2026-10-23T20:00:00+00:00 | 129 | 54.000 |
| US500 | 2969 | 2026-04-27T00:00:00+00:00 | 2026-10-23T20:00:00+00:00 | 129 | 54.000 |
| OIL | 2973 | 2026-04-27T00:00:00+00:00 | 2026-10-23T20:00:00+00:00 | 129 | 54.000 |
| EURPLN | 3117 | 2026-04-27T00:00:00+00:00 | 2026-10-23T20:00:00+00:00 | 25 | 49.000 |
| EURUSD | 3117 | 2026-04-27T00:00:00+00:00 | 2026-10-23T20:00:00+00:00 | 25 | 49.000 |
| GBPUSD | 3116 | 2026-04-27T00:00:00+00:00 | 2026-10-23T20:00:00+00:00 | 26 | 49.000 |
| US100 | 2969 | 2026-04-27T00:00:00+00:00 | 2026-10-23T20:00:00+00:00 | 129 | 54.000 |

We wszystkich sprawdzonych szeregach H1/H4/D1 brak duplikatów, odwróconej kolejności i niepoprawnego OHLC. To nie dowód pełności: luki obejmują weekendy, sesje i potencjalne braki. Nie mamy archiwalnego harmonogramu brokera, więc nie oznaczono wszystkich luk jako prawidłowych. Dostępność historii terminala zależy także od ustawienia liczby świec. [Dokumentacja MT5](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py).

## Ustalenia metodologiczne i wpływ poprawek

| Rynek | Ticki w godzinie | Maks. różnica OHLC Last | Maks. różnica OHLC Bid | Mediana Last−Bid pkt |
|---|---|---|---|---|
| GOLD | 76518 | 0.000 | 0.300 | 18.000 |
| US500 | 86742 | 0.000 | 0.400 | 4.000 |
| OIL | 49354 | 0.000 | 0.020 | 2.000 |
| EURPLN | 5030 | 0.000 | 0.0003 | 2.000 |
| EURUSD | 21524 | 0.000 | 2e-05 | 1.000 |
| GBPUSD | 30138 | 0.000 | 3e-05 | 2.000 |
| US100 | 101861 | 0.000 | 0.600 | 6.000 |

Dowód: `inputs/current_contracts.json`, `price_basis_check.json`, siedem surowych archiwów `inputs/basis-*.json.gz`. Python MT5 podaje stałe BID=0, LAST=1. Dla GOLD historyczne open Last=4088,10, Bid=4087,80, Ask=4088,27. Dla US100 Last=29497,0, Bid=29496,4, Ask=29497,5. Dodanie całego spreadu do Last nie daje rzeczywistej ceny Ask; Last nie jest też ceną zamknięcia BUY. Błąd może działać w obie strony, zmieniając także SL/TP i selekcję. Pełna godzina potwierdza problem w danych historycznych, lecz nie wyznacza poprawki dla wszystkich sześciu miesięcy. [Definicja chart_mode](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants).

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

Dokumentacja Python MT5 opisuje czasy wejściowe/wyjściowe jako UTC. Lokalna obserwacja przesunięcia nie jest podstawą do bezwarunkowego odejmowania obecnego offsetu dla dawnych dat. Analizy godzin, H4/D1 i przyszłego kalendarza są zatem warunkowe względem normalizacji czasu. [MT5 — czas danych](https://www.mql5.com/en/docs/python_metatrader5/mt5copyratesrange_py).

W `portfolio_research.py` SL/TP nie są dodatkowo zaokrąglane do tick size, a margin nie jest symulowany. W `backtest.py` odrzucenie przez spread/RR wykonuje `continue`, przez co pomija punkt płaskiej krzywej equity. Oryginalnych wyników nie naprawiono niejawnie. W izolacji rozszerzono jedynie eksport: wszystkie 18 portfelowych przebiegów odtworzyło identyczne oryginalne pola transakcji i PnL. Dla 2636 nowszych lokalnych transakcji sprawdzono zgodność signal_id i ceny wejścia; 628 starych rekordów pozostaje z nieznaną strategią/kierunkiem.

## Koszty: rzeczywista próbka a założenia

Zachowano próbkę ticków z 22.10: po 15 minut od 08:00, 13:30 i 20:30 UTC, siedem rynków. To 21 okien jednego dnia, nie estymacja pełnych sześciu miesięcy. Kwantyle są ważone liczbą ticków. Pliki źródłowe: `exchange/research/cost-sample-20261022/`.

| Rynek | 08:00 p50/p95 pkt | 13:30 p50/p95 | 20:30 p50/p95 |
|---|---|---|---|
| GOLD | 24.000/34.000 | 31.000/46.000 | 27.000/41.000 |
| US500 | 7.000/7.000 | 7.000/7.000 | 7.000/7.000 |
| US100 | 11.000/11.000 | 11.000/11.000 | 11.000/13.000 |
| OIL | 4.000/4.000 | 4.000/4.000 | 4.000/4.000 |
| EURUSD | 2.000/3.000 | 2.000/3.000 | 2.000/3.000 |
| EURPLN | 6.000/7.000 | 4.000/5.000 | 5.000/7.000 |
| GBPUSD | 4.000/6.000 | 3.000/5.000 | 3.000/5.000 |

Prowizji, rzeczywistego poślizgu, historycznego swapu i FX ta próbka nie potwierdza. Właściwości kontraktu rozróżniają m.in. chart_mode, typ naliczania swapu i wielkość kontraktu; bieżące wartości nie są archiwum zmian. [MT5 — właściwości instrumentów](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants).

**Spread H1 nie jest wiarygodnym zamiennikiem kosztu transakcji w tym zbiorze:** GOLD w bazowej walidacji ma 1 punkt, podczas gdy mediana tickowa w trzech oknach wynosi 24/31/27 punktów, P95 do 46. W próbce H1 13:00 pole spread=1 współistnieje z dużym rzeczywistym spreadem. EURPLN ma bazowo 1 punkt wobec P95 do 7. Stres ×3 od zaniżonej bazy nadal może być zbyt łagodny.

| Rynek | Bazowy spread pkt | Najwyższy obserwowany P95 pkt | N stałe | Netto po dodatkowym spreadzie | PF |
|---|---|---|---|---|---|
| EURPLN | 1.000 | 7.000 | 33 | -93.835 | 0.363 |
| EURUSD | 1.000 | 3.000 | 54 | -110.540 | 0.597 |
| GBPUSD | 1.000 | 6.000 | 49 | -70.260 | 0.719 |
| GOLD | 1.000 | 46.000 | 48 | -29.908 | 0.896 |
| OIL | 4.000 | 4.000 | 52 | -267.847 | 0.814 |
| US100 | 11.000 | 13.000 | 46 | 200.356 | 1.931 |
| US500 | 7.000 | 7.000 | 56 | -34.818 | 0.790 |

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

## Risk Manager i rzeczywiste operacje

W kopii dziennika jest 16 operacji CONFIRMED, pochodzących z testów `operator_demo_smoke_v1` i `operator_demo_acceptance_v1`. Nie są próbą wyników lokalnej strategii. Jest wcześniejsze zdarzenie UNCERTAIN, później uzgodnione; sam licznik zdarzeń historycznych nie oznacza obecnej niepewnej operacji. Źródła Risk Managera sprawdzają rachunek DEMO, uprawnienia, świeżość cen, zgodę na dokładną treść, strukturę, kalendarz, limity i siatkę cen/wolumenu. Execution Engine powtarza kontrolę po order_check. To kontrola bezpieczeństwa wykonania, nie dowód przewagi.

Snapshot runtime wskazuje WAITING na świeże notowania dwóch kontraktów oraz baseline z 23.10. To nie potwierdzenie gotowości sesji ani aktualnego equity początku następnej doby. Log zawiera także wcześniejszy błąd autoryzacji terminala. Nie zmieniano stanu ani nie wznawiano procesów w ramach audytu.
