> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Porównanie starego i poprawionego backtestu — bramka etapu 1

Etap 1, raport 2026-10-25T07:50:23.638758+00:00. Wyłącznie badanie danych, cen i czasu. Brak zleceń, zmian produkcyjnych, strojenia strategii i pełnego ponownego backtestu. Wszystkie dane historyczne są eksploracyjne.

**Pełnego ponownego backtestu nie uruchomiono.** Zgodnie z kolejnością prac najpierw przedstawiamy weryfikację danych/cen/czasu. Zgodność zarządzania pozycją i historyczne koszty pozostają niepotwierdzone; porównanie PnL teraz byłoby przedwczesne.

| Metryka | Status |
|---|---|
| Liczba sygnałów | NIE BADANO — reguły strategii niezmienione, brak nowego replay |
| Wykonane wejścia | NIE BADANO — brak pełnej symulacji |
| Poziomy realizacji | Sprawdzono tylko dobór strony kwotowania |
| Netto, PF, expectancy R, drawdown | NIE WYLICZONO |
| Wpływ prowizji | Nieznana zweryfikowana historyczna taryfa |
| Wpływ spreadu | Dynamiczny spread widoczny w rzeczywistych tickach; bez oszacowania wpływu na wynik strategii |

## Kontrola formuły ceny na identycznym rekordzie

| Rynek | Stara formuła BUY | Dostępny Ask | Różnica | Stara formuła SELL | Dostępny Bid | Różnica |
|---|---|---|---|---|---|---|
| EURPLN | 4.3703 | 4.3702 | 0.0001 | 4.3698 | 4.3698 | 0 |
| EURUSD | 1.12056 | 1.12053 | 3e-05 | 1.12051 | 1.12052 | -1e-05 |
| GBPUSD | 1.33739 | 1.33737 | 2e-05 | 1.33734 | 1.33734 | 0 |
| GOLD | 4088.13 | 4088.27 | -0.14 | 4088.08 | 4087.8 | 0.28 |
| OIL | 99.76 | 99.72 | 0.04 | 99.68 | 99.68 | 0 |
| US100 | 29498.3 | 29497.5 | 0.8 | 29496.8 | 29496.4 | 0.4 |
| US500 | 7726.1 | 7725.5 | 0.6 | 7725 | 7724.8 | 0.2 |

Stara formuła: open Last + dawny stały spread + 2 punkty slippage dla BUY oraz Last −2 punkty dla SELL. Nowa kolumna pokazuje wyłącznie kwotowanie Ask/Bid bez wymyślonej realizacji i poślizgu. To demonstracja błędnego podstawienia ceny, nie porównanie dwóch transakcji strategii i nie prognoza poprawy PnL. Różnica może działać w obie strony.

Pełne porównanie po kolejnej bramce: identyczne zamrożone reguły i sygnały Last, wspólny zakres potwierdzonych ticków, uzgodnione UTC/kontrakty/koszty, testy zgodności Position Managera, następnie porównanie sygnałów, wejść, fillów, opłat, netto, PF, R i DD. Wszystkie stare dane pozostają eksploracyjne; bez promowania parametrów.
