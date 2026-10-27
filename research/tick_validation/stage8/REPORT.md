> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Etap 8 — FX i zaokrąglenia wyniku pieniężnego

Badanie odczytowe 25.10.2026. **Odtworzono 96/96 bieżących wyliczeń order_calc_profit** dla US500.pro przy jawnej formule opisanej poniżej. Nie wysyłano nowych zleceń i nie zmieniano konfiguracji ani parametrów strategii. To diagnostyka kalkulatora i rozliczenia, nie optymalizacja ani pełny backtest.

## Dane i hipoteza rachunku

API odkryło dwie istniejące serie walutowe: `USDPLN.pro` i `USDPLN`. Nie zgadywano sufiksu i nie zmieniano wyboru symboli w terminalu. Pobrano 189 historycznych ticków obu serii z dwóch minut obejmujących trzy wcześniejsze zamknięcia DEMO. Historia pozostała na surowej osi czasu API; do porównania użyto wyłącznie wcześniejszych kwotowań, w wieku 719–6155 ms. Przyjęty limit wieku 10 s pochodzi z istniejącej konfiguracji, nie z dopasowania do wyników.

Bieżąca specyfikacja US500.pro: mnożnik kontraktu 50, waluta wyniku USD, rachunek PLN. Dla trybów CFD dokumentacja podaje wynik w walucie instrumentu jako zmianę ceny × wielkość kontraktu × loty. [MetaQuotes — tryby kalkulacji](https://www.mql5.com/en/docs/constants/environment_state/marketinfoconstants).

Ta formuła sama nie określa zaokrągleń i wewnętrznej ścieżki FX. Zbadano następujące warianty:

1. Przeliczenie niezaokrąglonego wyniku USD, a potem zaokrąglenie PLN.
2. Najpierw zaokrąglenie USD do 2 miejsc (połówki od zera), następnie konwersja: dodatni wynik po Bid, ujemny po Ask, a na końcu zaokrąglenie PLN do 2 miejsc.

Oba warianty sprawdzono z obiema odkrytymi seriami USDPLN. Ceny FX normalizowano do zadeklarowanej precyzji 4 miejsc, usuwając wyłącznie reprezentacyjny szum float. **Nie dopasowywano mnożnika kontraktu ani kursu do zapisanego PnL.**

## Bieżąca siatka diagnostyczna

Siatka została ustalona przed wywołaniami: BUY/SELL × wolumeny 0,001; 0,002; 0,01; 0,1 × 12 dodatnich/ujemnych zmian ceny. Łącznie **96 wywołań order_calc_profit**. To obliczenia tylko do odczytu, nie order_send ani order_check. Kwotowania przed i po siatce były identyczne. Są to ostatnie kwotowania dostępne w weekendowym terminalu, a nie świeży rynek niedzielny.

| Seria FX | USD zaokrąglane przed konwersją | Wyniki zgodne z API |
|---|---|---:|
| USDPLN.pro | Nie | 24/96 |
| USDPLN.pro | Tak | 42/96 |
| USDPLN | Nie | 64/96 |
| **USDPLN** | **Tak** | **96/96** |

Bieżące `trade_tick_value_profit=19,45` i `trade_tick_value_loss=19,85` są również zgodne z kursem `USDPLN` Bid 3,89 / Ask 3,97 dla ticku ceny 0,1 i mnożnika 50. Seria `.pro` ma inne kwotowania. Wyniki silnie wspierają opisany model **dla obecnego stanu kalkulatora i zbadanej siatki**; nie są deklaracją niezmiennych reguł brokera w całej historii lub dla wszystkich instrumentów.

## Trzy wcześniejsze zamknięcia DEMO

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

**Te trzy małe zamknięcia nie identyfikują historycznej ścieżki FX:** po zaokrągleniu zarówno USDPLN, jak i USDPLN.pro dają te same kwoty groszowe. Historyczna ważność mnożnika 50 także nie została niezależnie potwierdzona. Dlatego `historical_model_approved=false` pozostaje właściwym statusem, mimo zgodności rachunku.

## Znaczenie częściowych zamknięć

Przy zmianie ceny −0,9 i parametrach bieżącej siatki:

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

To różnica arytmetyki per wykonanie, nie efekt strategii. Backtester ze stałym liniowym mnożnikiem i jednym końcowym zaokrągleniem nie odtwarza tego zachowania na małych wolumenach. Zmiana modelu może zmienić wyniki w obie strony; nie wyciągnięto wniosku o poprawie rentowności.

## Implementacja i ograniczenia

`cash.py` używa Decimal oraz jawnych reguł waluty i zaokrąglenia. `diagnostic_profit` służy porównaniu hipotez. `historical_net` odmawia działania bez potwierdzonej historycznej polityki, źródła dowodu i zakresu ważności. Prowizja, swap i fee muszą być jawne; brak danych nie oznacza zera. Koszty te są osobnymi pozycjami kasowymi — order_calc_profit nie jest dowodem ich historycznej wysokości.

**9 testów automatycznych** sprawdza znaki BUY/SELL, zaokrąglenia, konwersję po odpowiedniej stronie, różnicę częściowych zamknięć oraz odrzucenie brakującej polityki/kosztów. Wszystkie przeszły. Chronione pliki produkcyjne i wcześniejsze etapy pozostają niezmienione.

Odtworzenie offline z C:\TradingAI:

```powershell
.\.venv\Scripts\python.exe research\tick_validation\stage8\analyze.py
```

`inputs/` przechowuje odkryte symbole, ticki FX, specyfikację i wszystkie 96 wyników API. `comparison.json` zawiera również wyniki modeli niezgodnych, wszystkie warianty historycznych kwotowań i jawne ograniczenia. `manifest.json` zapisuje hashe. Nie wolno przenieść obecnej reguły na wielomiesięczny backtest bez historii kontraktu, ścieżki konwersji i zasad kosztów. Wszystkie dotychczasowe dane pozostają eksploracyjne.
