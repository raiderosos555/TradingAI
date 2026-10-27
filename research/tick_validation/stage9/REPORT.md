> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Rozliczenia wszystkich siedmiu kontraktów — diagnostyka bieżąca

## Wynik

Zebrano 504 odpowiedzi `order_calc_profit` (72 na instrument), 25.10.2026 od 19:33:23.843 do 19:33:24.029 UTC zegara hosta. Nie wysłano zleceń. Z góry zapisany zestaw obejmował BUY/SELL, minimum wolumenu, minimum + 1 krok oraz minimum + 9 kroków, a także przesunięcia cen o ±1, ±2, ±3, ±9, ±10 i ±11 ticków. Wszystkie argumenty były zgodne z aktualnymi krokami ceny i wolumenu kontraktu.

**Nie istnieje jedna potwierdzona ścieżka konwersji wspólna dla wszystkich instrumentów.** Poniższe hipotezy odtworzyły wszystkie wyniki w badanej siatce:

| Instrument | Waluta wyniku | Zgodna ścieżka diagnostyczna | Zgodność | Czy siatka rozróżnia zaokrąglenie USD przed konwersją? |
|---|---|---|---|---|
| GOLD | USD | USDPLN, zaokrąglenie USD → FX → zaokrąglenie PLN | 72/72 | Tak; bez niego 44/72 |
| US500 | USD | USDPLN, zaokrąglenie USD → FX → zaokrąglenie PLN | 72/72 | Tak; bez niego 56/72 |
| US100 | USD | USDPLN, zaokrąglenie USD → FX → zaokrąglenie PLN | 72/72 | Tak; bez niego 32/72 |
| OIL | USD | USDPLN → PLN | 72/72 | Nie; oba warianty 72/72 |
| EURUSD | USD | USDPLN.pro → PLN | 72/72 | Nie; oba warianty 72/72 |
| GBPUSD | USD | USDPLN.pro → PLN | 72/72 | Nie; oba warianty 72/72 |
| EURPLN | PLN | Bez konwersji walutowej | 72/72 | Nie dotyczy |

Zachowano wszystkie hipotezy i przypadki w `comparison.json`, także te niezgodne. To klasyfikacja zachowania bieżącego kalkulatora na skończonej siatce. Wynik nie identyfikuje wszystkich wewnętrznych reguł brokera i nie potwierdza ich obowiązywania historycznie.

## Co dokładnie sprawdzono

Aktualne kontrakty GOLD, US500, OIL i US100 mają `trade_calc_mode=4`; EURPLN, EURUSD i GBPUSD mają `trade_calc_mode=0`. Oba tryby stosują bazowo różnicę ceny × wielkość kontraktu × loty, ze znakiem zależnym od kierunku. Wzór pochodzi z [dokumentacji właściwości symboli MQL5](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants). Dokumentacja ta nie jest dowodem szczegółowej ścieżki FX ani zaokrągleń zaobserwowanych w tym badaniu.

Dla każdego wywołania zachowano obie kandydatury FX przed i po kalkulacji. Bid, Ask i czas obserwacji muszą być identyczne w obu odczytach, inaczej przypadek zostaje oznaczony jako wyłączony z porównania. Żaden z 504 przypadków nie wymagał wyłączenia; kalkulator nie zwrócił błędu. Zysk USD przeliczano przez Bid, stratę przez Ask. EURPLN nie korzysta z FX. Ceny użyte jako argumenty kalkulatora są jawną siatką diagnostyczną, nie historią fillów ani sztucznie uzupełnionymi tickami.

Zapis float np. `-3.9699999999999998` jest porównywany z kwotą `-3.97` tylko wtedy, gdy różnica mieści się w dwóch jednostkach reprezentacji binarnej (ULP) wartości API. Surowa wartość oraz reszta reprezentacji pozostają w raporcie. Wartości rzeczywiście poza siatką grosza są odrzucane; testy obejmują `0.104` i `0.105`. Nie zastosowano szerokiej tolerancji pieniężnej.

## Ograniczenia i wpływ na replay

- To bieżący kalkulator i bieżące specyfikacje, z ostatnimi dostępnymi weekendowymi kwotowaniami. Spójny bracket FX nie oznacza świeżego rynku ani nie wyklucza niewidocznej zmiany pomiędzy odczytami. Nie przyjęto nowego historycznego offsetu czasu.
- Różnica ścieżki FX między instrumentami wyklucza bezwarunkowe stosowanie modelu US500 do całego portfela. Przyszła polityka kosztów musi być wersjonowana według kontraktu i okresu obowiązywania.
- Dla OIL i par walutowych legalna siatka nie generuje rozróżniających wartości ułamkowego centa USD. Nie uznano zaokrąglenia pośredniego za potwierdzone tam, gdzie oba warianty dają ten sam wynik.
- `order_calc_profit` nie jest wykonaniem zlecenia. Nie dowodzi dostępnej płynności, rzeczywistego poślizgu, akceptacji SL/TP, dostępności margin ani poprawności spreadu przy wejściu. Zebrano właściwości kontraktów, ale ich wartości nie są historycznym archiwum.
- To wynik brutto kalkulatora. Nie przyjęto domyślnie zerowych prowizji, swapu ani innych opłat. Nie wyliczono z niego netto strategii, PF, expectancy ani drawdown.
- Nadal brakuje wiarygodnego historycznego mapowania UTC/DST, pełnego pokrycia ticków oraz okresów obowiązywania kosztów i specyfikacji. Pełny ponowny backtest pozostaje nieuruchomiony. Wszystkie widziane dane są eksploracyjne.

## Weryfikacja i odtwarzanie

11 testów automatycznych przeszło, w tym kontrola kroków, limitu wolumenu, nieprawidłowych cen, zmiennego FX, kontraktu nieobsługiwanego, bezpośredniego PLN i reprezentacji float. Hashami potwierdzono niezmienność chronionego kodu/konfiguracji produkcyjnej oraz etapów 1–8.

Z katalogu `C:\TradingAI` uruchom:

```powershell
.\.venv\Scripts\python.exe research/tick_validation/stage9/verify.py
```

Weryfikator działa offline, ponownie oblicza porównania z zamrożonego `capture.json`, uruchamia testy i sprawdza manifesty bez zmiany danych. `config.json` ma wersję schematu 1 i jest objęty SHA-256. Oryginalny odczyt był ograniczony do 40 sekund w odrębnym procesie; timeout kończy wyłącznie ten proces badawczy. Kolejny pomiar powinien powstać jako nowy zestaw danych; kolektor odmawia nadpisania istniejącego.

Nie zmieniono działającego DEMO, jego zegara, Risk Managera, strategii ani parametrów. `historical_policy_approved=false` i `accepted_historical_cost_policy=null` pozostają jawne.
