# EDGE_VERDICT — 28.10.2026

**NIE: nie znaleziono wiarygodnej przewagi po rzeczywistych kosztach.** Zbadane filtry nie uzasadniają promocji; dla COT/makro brakuje określonych danych, więc ich wynik pozostaje nieweryfikowalny.

Poniżej późna część eksploracji (01.08–23.10 raw). A/B są bps Last na okazję po progu spreadu; nie broker P&L. Wszystkie główne p Holm6 i Holm48=1.000.

| Rynek | Mechanizm | Źródło | Liczba obserwacji | Wynik bazowy A | Z nową informacją B | Koszty | Istotność | Werdykt |
|---|---|---|---|---|---|---|---|---|
| US500 | V | VIX | 11 okazji / 11 aktywnych B / 6 bloków | -51.282 | -51.282 | próg; stress -68.187 | brak po Holm | nie promować |
| US100 | V | VIX | 11 okazji / 11 aktywnych B / 6 bloków | -89.939 | -89.939 | próg; stress -106.373 | brak po Holm | nie promować |
| US500 | T | VIX9D | 11 okazji / 11 aktywnych B / 6 bloków | -51.282 | -51.282 | próg; stress -68.187 | brak po Holm | nie promować |
| US100 | T | VIX9D | 11 okazji / 11 aktywnych B / 6 bloków | -89.939 | -89.939 | próg; stress -106.373 | brak po Holm | nie promować |
| OIL | O | OVX | 10 okazji / 3 aktywnych B / 6 bloków | -155.550 | -88.788 | próg; stress -94.828 | brak po Holm | nie promować |
| GOLD | G | GVZ | 10 okazji / 4 aktywnych B / 6 bloków | 40.495 | 27.979 | próg; stress 21.153 | brak po Holm | nie promować |
| EURUSD | COT / stopy | CFTC / ALFRED | nieweryfikowalne | nieweryfikowalne | nieweryfikowalne | brak pełnego modelu | nieweryfikowalne | brak zbioru as-of |
| GBPUSD | COT / stopy | CFTC / ALFRED | nieweryfikowalne | nieweryfikowalne | nieweryfikowalne | brak pełnego modelu | nieweryfikowalne | brak zbioru as-of |
| EURPLN | stopy / risk-off | NBP / ECB / GPR | nieweryfikowalne | nieweryfikowalne | nieweryfikowalne | brak OIS/kosztów | nieweryfikowalne | brak zbioru as-of |

## Decyzje o nowych filtrach

- VIX i VIX9D/VIX: w późnych głównych oknach nie odfiltrowały żadnego wejścia; przyrost dokładnie0. To brak nowej decyzji w tej próbce, nie dowód równoważności populacyjnej.
- OVX: późny markout z filtrem mniej ujemny niż baza, ale nadal ujemny; gorszy niż prosta kontrola ATR. Przy7d lag znak przyrostu się odwraca. Brak przewagi nad placebo.
- GVZ: główny filtr obniża markout względem bazy w obu podpróbach. Dodatni bezwzględny markout nie jest wartością dodaną. Wrażliwość7d zmienia znak późnego przyrostu, bez istotności.
- Żadnej z sześciu badanych konfiguracji nie nominujemy do wdrożenia ani nie dostrajamy progów.
- COT, real yields, EIA i GPR nie mają tu policzonego wyniku strategii; brak wartości nie jest zerem.

## Co pozostaje uzasadnione naukowo

Dwa kierunki badawcze, a nie wybrani zwycięzcy: (1) reakcja na informację EIA po pierwszym skoku, (2) wolniejsze pozycjonowanie COT w relacji do momentum. Pierwszy wymaga first print i wykonalnych kwotowań; drugi kalendarza faktycznych publikacji i dłuższych cen. Nie uruchamiamy obu naraz: jeden następny zbiór określa NEXT_STEP.md.
Żaden kierunek nie otrzymał statusu potwierdzonego kandydata po kosztach. Nowy predyktor nadal trzeba porównać do ceny, USD/vol i placebo w niewykorzystanym okresie; co najmniej20 bloków to minimum techniczne, nie gwarancja mocy statystycznej.

## Osobne bramki

- **GO**: ograniczone badanie statystyczne offline na opóźnionych danych z jawnymi ograniczeniami.
- **NO-GO**: deklaracja poprawnego historycznego as-of i netto; brak vintage/UTC/kosztów.
- **NO-GO**: zmiana DEMO lub uruchomienie LIVE na podstawie tych wyników.
- Odporność DEMO nie jest tu ponownie certyfikowana. Odczyt kontrolny wcześniejszej części pracy potwierdził obecność brokerowych SL/TP; kwarantanna i WAITING pozostają odrębną blokadą. Niczego nie wdrażano.
