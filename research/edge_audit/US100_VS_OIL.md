> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# US100_VS_OIL — porównanie

Stan audytu: 2026-10-24T18:09:09.311248+00:00. Badanie offline; bez nowych zleceń, zmian DEMO, konfiguracji, Execution Engine i Risk Managera. Kwoty w PLN, o ile nie zaznaczono inaczej.

**Wykryty błąd ceny wykonania:** wszystkie siedem kontraktów zgłasza `chart_mode=1` (Last). Rekonstrukcja pełnej godziny 22.10 13:00–14:00 UTC z ticków odtworzyła zapisany OHLC dokładnie z Last dla każdego instrumentu; OHLC Bid różni się. Oba replays zakładają OHLC Bid. Poniższe PnL/PF są więc wynikami oryginalnego, niepoprawnie przyjętego modelu ceny, a nie zweryfikowanego wykonania. Nie naprawiono ich po cichu; wymagana jest osobna walidacja na Bid/Ask.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

| Rynek | Okres | N | Netto | PF | Śr. R | SD R | DD H1 | Seria strat |
|---|---|---|---|---|---|---|---|---|
| US100 | development | 103 | -178.033 | 0.805 | -0.041 | 1.181 | 355.967 | 9 |
| US100 | validation | 46 | 201.069 | 1.935 | 0.345 | 1.255 | 62.078 | 4 |
| OIL | development | 76 | -536.111 | 0.745 | -0.143 | 1.175 | 687.293 | 7 |
| OIL | validation | 52 | -267.847 | 0.814 | -0.093 | 1.171 | 532.881 | 8 |

## Skąd zysk i czy koniec był słabszy?

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

| Rynek | Część końcowego okresu | N | Netto | Śr. R |
|---|---|---|---|---|
| US100 | first_third | 15 | 90.359 | 0.511 |
| US100 | middle_third | 15 | 63.715 | 0.387 |
| US100 | last_third | 16 | 46.995 | 0.150 |
| US100 | last5 | 5 | -31.912 | -0.498 |
| OIL | first_third | 17 | -101.902 | -0.198 |
| OIL | middle_third | 17 | -304.565 | -0.289 |
| OIL | last_third | 18 | 138.620 | 0.191 |
| OIL | last5 | 5 | 76.819 | 0.304 |

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

| Rynek | Najlepsze 1 | Najlepsze 3 | Najlepsze 5 | Wynik po usunięciu 5 |
|---|---|---|---|---|
| US100 | 38.546 | 96.973 | 148.922 | 52.148 |
| OIL | 97.899 | 290.589 | 476.293 | -744.140 |

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

## Kierunek, interwały i ATR

| Rynek/okres | Mediana ATR ceny | Mediana ryzyka PLN | Mediana SL/ATR | Mediana spread/ATR |
|---|---|---|---|---|
| US100-development | 110.537 | 13.670 | 1.502 | 0.010 |
| US100-validation | 90.006 | 11.442 | 1.503 | 0.012 |
| OIL-development | 0.706 | 45.930 | 1.537 | 0.057 |
| OIL-validation | 0.727 | 47.875 | 1.537 | 0.055 |

| Rynek | Wymiar | Wartość | N | Netto | Śr. R |
|---|---|---|---|---|---|
| US100 | trend_H4 | DOWN | 14 | 71.923 | 0.385 |
| US100 | trend_H4 | RANGE | 14 | 14.609 | -0.005 |
| US100 | trend_H4 | UP | 18 | 114.537 | 0.586 |
| US100 | trend_D1 | RANGE | 22 | 78.575 | 0.345 |
| US100 | trend_D1 | UP | 24 | 122.495 | 0.346 |
| US100 | direction | BUY | 24 | 102.443 | 0.384 |
| US100 | direction | SELL | 22 | 98.626 | 0.302 |
| US100 | volatility | HIGH | 14 | 99.980 | 0.470 |
| US100 | volatility | LOW | 5 | 27.215 | 0.777 |
| US100 | volatility | MID | 27 | 73.875 | 0.201 |
| OIL | trend_H4 | DOWN | 15 | -332.710 | -0.384 |
| OIL | trend_H4 | RANGE | 11 | 207.187 | 0.430 |
| OIL | trend_H4 | UP | 26 | -142.324 | -0.146 |
| OIL | trend_D1 | RANGE | 15 | 151.558 | 0.241 |
| OIL | trend_D1 | UP | 37 | -419.405 | -0.228 |
| OIL | direction | BUY | 29 | 103.648 | 0.092 |
| OIL | direction | SELL | 23 | -371.495 | -0.326 |
| OIL | volatility | HIGH | 8 | -115.817 | -0.310 |
| OIL | volatility | LOW | 10 | 42.481 | 0.139 |
| OIL | volatility | MID | 34 | -194.510 | -0.110 |

To sumy obu lokalnych rodzin wyłącznie jednego przebiegu. Rozbicie po rodzinie i jego CI znajduje się w `subgroup_statistics.csv`. H4/D1 są opisowym kontekstem znanym przy wejściu, nie dowodem przyczynowym. Podgrupy bywają bardzo małe; nie ustalamy na ich podstawie nowych produkcyjnych filtrów.

Godziny otwarcia końcowego US100 — pełny rozkład zamiast wyboru kilku szczęśliwych godzin:

| Godzina UTC | N | Netto | Śr. R |
|---|---|---|---|
| 1 | 3 | -20.429 | -0.538 |
| 2 | 1 | -12.489 | -0.991 |
| 4 | 1 | 5.476 | 0.498 |
| 5 | 1 | -12.364 | -0.991 |
| 6 | 1 | 25.998 | 1.973 |
| 7 | 5 | -28.484 | -0.401 |
| 8 | 2 | -2.162 | -0.164 |
| 9 | 1 | 13.857 | 0.828 |
| 10 | 2 | -21.233 | -0.989 |
| 11 | 2 | 23.314 | 1.354 |
| 12 | 3 | 41.504 | 1.391 |
| 13 | 1 | 25.951 | 1.146 |
| 14 | 8 | 49.662 | 0.427 |
| 15 | 5 | 43.238 | 0.741 |
| 16 | 2 | 42.601 | 1.964 |
| 17 | 1 | 19.574 | 0.833 |
| 18 | 1 | -12.583 | -0.991 |
| 19 | 2 | -8.028 | -0.197 |
| 20 | 2 | 20.910 | 0.494 |
| 23 | 2 | 6.757 | 0.486 |

## Stres kosztowy przy tej samej liczbie transakcji

| Rynek | Koszty × | N | Netto | PF | Śr. R |
|---|---|---|---|---|---|
| OIL | 1 | 52 | -267.847 | 0.814 | -0.093 |
| OIL | 2 | 52 | -435.721 | 0.718 | -0.163 |
| OIL | 3 | 52 | -603.595 | 0.635 | -0.234 |
| US100 | 1 | 46 | 201.069 | 1.935 | 0.345 |
| US100 | 2 | 46 | 195.103 | 1.897 | 0.334 |
| US100 | 3 | 46 | 189.137 | 1.859 | 0.322 |

Zachowano daty, kierunki, wolumeny, pierwotny mianownik R i ścieżkę wyjść. Dodatkowy koszt to (m−1) × [spread × point × cash_factor × volume + 2 × slippage × point × cash_factor × volume + prowizja − swap]. To jawny rachunek kontrfaktyczny stałej ścieżki; nie nowa symulacja wykonania. Zmieniony spread mógłby zmienić moment SL/TP, a więc wynik rzeczywisty. Nie uchylono limitu spreadu.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

## Niepewność i selekcja

| Rynek/okres | N | Śr. R | CI95 blok 5 | CI z korektą 7 rynków |
|---|---|---|---|---|
| US100/development | 103 | -0.041 | [-0.297; 0.216] | [-0.384; 0.313] |
| US100/validation | 46 | 0.345 | [0.043; 0.627] | [-0.075; 0.721] |
| OIL/development | 76 | -0.143 | [-0.373; 0.087] | [-0.455; 0.169] |
| OIL/validation | 52 | -0.093 | [-0.355; 0.174] | [-0.447; 0.277] |

30 000 resampli, bloki 3/5/10 i stałe ziarno zapisano w `uncertainty_sensitivity.json/csv`. Dla US100 końcowego blok 5 daje około [0,043; 0,627] R, ale po korekcie samych siedmiu porównań około [−0,075; 0,721] R. Faktyczna liczba prób jest większa (strategie, filtry, podgrupy), więc nawet ta korekta jest niepełna. Selekcja US100 do produkcji na podstawie tych wyników byłaby nieuzasadniona.
