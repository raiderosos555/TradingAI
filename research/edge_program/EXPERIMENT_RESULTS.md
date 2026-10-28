# Wyniki edge-program-v1 — 28.10.2026

**36 porównań, 0 istotnych przyrostów po Holm36. Nie potwierdzono przewagi po rzeczywistych kosztach.**

Pytanie nowe wobec poprzedniej rundy: wartość dodana wskaźnika do prostego benchmarku; bez ponownego strojenia EMA20/50. Cztery rodziny T/R/F/X z STRATEGY_HYPOTHESES.md zapisano przed obliczeniem.

Pomiary: raw 27.04–23.10.2026; early do31.07, late od01.08. Oba okresy były wcześniej oglądane. Wcześniejsze świece służą rozgrzewce. 5871 par-okazji łącznie to powtarzające się okna różnych modeli, NIE 5871 niezależnych transakcji. W obrębie reguły okna nie nakładają się; korelacje między rynkami i blokami pozostają.

Wszystkie wielkości cenowe w bps Last na okazję, także cash. G=gross markout; K=próg spreadu; B=G−K, A=benchmark po tym samym progu. Delta=B−A. S=stress B. **B nie jest netto brokera**, a wewnętrzny klucz JSON net oznacza jedynie markout minus próg. Brak SL/sizingu/pełnego wykonania: PF, drawdown kapitału i R nieweryfikowalne, nie zero.

| Test | n early | n late | aktywnych late | bloków late | Delta early | G late | K late | B late | A late | Delta late | CI95 Delta | S late | p Holm36 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| T/GOLD/SMA | 12 | 10 | 10 | 6 | -85.717 | 79.207 | 1.058 | 78.149 | 40.495 | 37.654 | 0.000, 112.963 | 61.091 | 1.000 |
| T/GOLD/EMA | 12 | 10 | 10 | 6 | -85.717 | -7.443 | 1.058 | -8.501 | 40.495 | -48.996 | -146.988, 0.000 | -25.559 | 1.000 |
| T/GOLD/MACD | 12 | 10 | 10 | 6 | 0.000 | 60.386 | 1.058 | 59.328 | 40.495 | 18.833 | 0.000, 56.500 | 42.271 | 1.000 |
| T/US500/SMA | 13 | 11 | 11 | 6 | -17.336 | -8.072 | 0.905 | -8.977 | -51.282 | 42.305 | 0.000, 98.499 | -25.882 | 1.000 |
| T/US500/EMA | 13 | 11 | 11 | 6 | -17.336 | -23.460 | 0.905 | -24.364 | -51.282 | 26.918 | -28.210, 98.499 | -41.269 | 1.000 |
| T/US500/MACD | 13 | 11 | 11 | 6 | 44.178 | -15.432 | 0.905 | -16.337 | -51.282 | 34.945 | -26.198, 97.808 | -33.242 | 1.000 |
| T/US100/SMA | 13 | 11 | 11 | 6 | 38.474 | 35.265 | 0.434 | 34.831 | -89.939 | 124.770 | 20.555, 275.062 | 18.397 | 1.000 |
| T/US100/EMA | 13 | 11 | 11 | 6 | 67.188 | -6.234 | 0.434 | -6.668 | -89.939 | 83.271 | -34.973, 269.994 | -23.102 | 1.000 |
| T/US100/MACD | 13 | 11 | 11 | 6 | 77.503 | -151.621 | 0.434 | -152.055 | -89.939 | -62.116 | -186.348, 0.000 | -168.489 | 1.000 |
| T/OIL/SMA | 12 | 10 | 10 | 6 | 79.925 | -86.606 | 4.479 | -91.085 | -155.550 | 64.465 | -375.339, 463.787 | -111.565 | 1.000 |
| T/OIL/EMA | 12 | 10 | 10 | 6 | 79.925 | 193.838 | 4.479 | 189.359 | -155.550 | 344.909 | -140.930, 824.955 | 168.880 | 1.000 |
| T/OIL/MACD | 12 | 10 | 10 | 6 | -99.346 | -2.331 | 4.479 | -6.810 | -155.550 | 148.740 | -278.013, 514.047 | -27.289 | 1.000 |
| T/EURUSD/SMA | 15 | 14 | 14 | 6 | -14.303 | 28.230 | 0.262 | 27.968 | 26.221 | 1.747 | 0.000, 4.892 | 14.135 | 1.000 |
| T/EURUSD/EMA | 15 | 14 | 14 | 6 | -23.356 | 26.483 | 0.262 | 26.221 | 26.221 | 0.000 | 0.000, 0.000 | 12.388 | 1.000 |
| T/EURUSD/MACD | 15 | 14 | 14 | 6 | 9.980 | 11.688 | 0.262 | 11.427 | 26.221 | -14.795 | -41.425, 0.000 | -2.406 | 1.000 |
| T/GBPUSD/SMA | 15 | 14 | 14 | 6 | 19.901 | 20.387 | 0.447 | 19.940 | 17.774 | 2.166 | -2.815, 8.881 | 5.922 | 1.000 |
| T/GBPUSD/EMA | 15 | 14 | 14 | 6 | 19.901 | 20.387 | 0.447 | 19.940 | 17.774 | 2.166 | -2.815, 8.881 | 5.922 | 1.000 |
| T/GBPUSD/MACD | 15 | 14 | 14 | 6 | 13.077 | -9.514 | 0.447 | -9.961 | 17.774 | -27.735 | -57.133, -1.083 | -23.980 | 1.000 |
| T/EURPLN/SMA | 15 | 14 | 14 | 6 | -7.487 | -6.354 | 1.613 | -7.967 | 0.211 | -8.178 | -18.571, 0.000 | -23.152 | 1.000 |
| T/EURPLN/EMA | 15 | 14 | 14 | 6 | -7.487 | -4.199 | 1.613 | -5.813 | 0.211 | -6.024 | -18.571, 4.308 | -20.998 | 1.000 |
| T/EURPLN/MACD | 15 | 14 | 14 | 6 | 14.364 | 4.435 | 1.613 | 2.821 | 0.211 | 2.611 | -8.525, 16.197 | -12.363 | 1.000 |
| R/EURUSD/RSI | 196 | 168 | 19 | 6 | 0.632 | 0.037 | 0.030 | 0.008 | 0.231 | -0.223 | -2.769, 1.710 | -0.324 | 1.000 |
| R/GBPUSD/RSI | 196 | 168 | 16 | 6 | 1.231 | 0.413 | 0.043 | 0.370 | -0.018 | 0.389 | -0.650, 1.321 | 0.074 | 1.000 |
| R/EURPLN/RSI | 196 | 168 | 14 | 6 | 0.066 | 0.403 | 0.134 | 0.269 | -0.457 | 0.726 | -0.117, 1.650 | -0.087 | 1.000 |
| F/GOLD/ADX | 193 | 168 | 13 | 6 | 0.117 | 0.589 | 0.082 | 0.508 | 0.557 | -0.049 | -1.294, 0.870 | 0.220 | 1.000 |
| F/GOLD/ATR | 193 | 168 | 16 | 6 | -0.027 | 1.315 | 0.102 | 1.213 | 0.557 | 0.656 | -0.065, 1.758 | 0.858 | 1.000 |
| F/OIL/ADX | 193 | 168 | 12 | 6 | -0.976 | -6.948 | 0.302 | -7.250 | -7.119 | -0.131 | -5.444, 5.145 | -7.743 | 1.000 |
| F/OIL/ATR | 193 | 168 | 13 | 6 | -4.524 | -6.565 | 0.332 | -6.897 | -7.119 | 0.222 | -6.897, 6.398 | -7.435 | 1.000 |
| F/US500/ADX | 185 | 161 | 7 | 6 | 0.443 | -0.432 | 0.039 | -0.471 | 2.329 | -2.800 | -5.934, -0.362 | -0.626 | 1.000 |
| F/US500/ATR | 185 | 161 | 13 | 6 | 0.624 | 2.086 | 0.073 | 2.013 | 2.329 | -0.316 | -1.230, 0.382 | 1.724 | 1.000 |
| F/US100/ADX | 185 | 161 | 11 | 6 | -0.090 | 0.430 | 0.030 | 0.401 | 2.380 | -1.979 | -6.054, 1.169 | 0.189 | 1.000 |
| F/US100/ATR | 185 | 161 | 16 | 6 | 0.316 | 1.773 | 0.043 | 1.730 | 2.380 | -0.650 | -2.939, 0.993 | 1.421 | 1.000 |
| X/GOLD/falsebreak | 193 | 168 | 15 | 6 | 2.289 | -0.044 | 0.094 | -0.138 | 1.942 | -2.079 | -6.468, 1.771 | -0.470 | 1.000 |
| X/OIL/falsebreak | 193 | 168 | 25 | 6 | -1.148 | 2.560 | 0.667 | 1.892 | -2.636 | 4.528 | 0.917, 8.730 | 0.828 | 0.702 |
| X/US500/falsebreak | 185 | 161 | 19 | 6 | -0.377 | 0.022 | 0.107 | -0.085 | -0.756 | 0.671 | 0.051, 1.350 | -0.507 | 0.892 |
| X/US100/falsebreak | 185 | 161 | 23 | 6 | 1.921 | 0.672 | 0.062 | 0.610 | -0.832 | 1.442 | -1.714, 4.537 | 0.167 | 1.000 |

CI opisowe, nie jednoczesne przedziały po korekcie. Holm dotyczy p; przy nielicznych blokach bootstrap ma słabą kalibrację. CI [0,0] przy identycznych decyzjach nie jest dowodem równoważności populacyjnej.

## Placebo, ekspozycja i benchmark long

| Test | aktywnych A late | B/aktywne | long po progu | zgodność B/A | p sign placebo Holm36 | p thinning Holm8 |
|---|---|---|---|---|---|---|
| T/GOLD/SMA | 10 | 78.149 | -38.535 | 0.900 | 0.630 | nie dotyczy |
| T/GOLD/EMA | 10 | -8.501 | -38.535 | 0.900 | 1.000 | nie dotyczy |
| T/GOLD/MACD | 10 | 59.328 | -38.535 | 0.900 | 1.000 | nie dotyczy |
| T/US500/SMA | 11 | -8.977 | -3.238 | 0.818 | 1.000 | nie dotyczy |
| T/US500/EMA | 11 | -24.364 | -3.238 | 0.727 | 1.000 | nie dotyczy |
| T/US500/MACD | 11 | -16.337 | -3.238 | 0.727 | 1.000 | nie dotyczy |
| T/US100/SMA | 11 | 34.831 | -10.586 | 0.727 | 1.000 | nie dotyczy |
| T/US100/EMA | 11 | -6.668 | -10.586 | 0.727 | 1.000 | nie dotyczy |
| T/US100/MACD | 11 | -152.055 | -10.586 | 0.909 | 1.000 | nie dotyczy |
| T/OIL/SMA | 10 | -91.085 | 261.981 | 0.600 | 1.000 | nie dotyczy |
| T/OIL/EMA | 10 | 189.359 | 261.981 | 0.400 | 1.000 | nie dotyczy |
| T/OIL/MACD | 10 | -6.810 | 261.981 | 0.500 | 1.000 | nie dotyczy |
| T/EURUSD/SMA | 14 | 27.968 | -21.012 | 0.929 | 1.000 | nie dotyczy |
| T/EURUSD/EMA | 14 | 26.221 | -21.012 | 1.000 | 1.000 | nie dotyczy |
| T/EURUSD/MACD | 14 | 11.427 | -21.012 | 0.929 | 1.000 | nie dotyczy |
| T/GBPUSD/SMA | 14 | 19.940 | -5.513 | 0.786 | 1.000 | nie dotyczy |
| T/GBPUSD/EMA | 14 | 19.940 | -5.513 | 0.786 | 1.000 | nie dotyczy |
| T/GBPUSD/MACD | 14 | -9.961 | -5.513 | 0.786 | 1.000 | nie dotyczy |
| T/EURPLN/SMA | 14 | -7.967 | 9.597 | 0.857 | 1.000 | nie dotyczy |
| T/EURPLN/EMA | 14 | -5.813 | 9.597 | 0.786 | 1.000 | nie dotyczy |
| T/EURPLN/MACD | 14 | 2.821 | 9.597 | 0.714 | 1.000 | nie dotyczy |
| R/EURUSD/RSI | 29 | 0.068 | -1.539 | 0.869 | 1.000 | nie dotyczy |
| R/GBPUSD/RSI | 25 | 3.890 | -0.758 | 0.851 | 1.000 | nie dotyczy |
| R/EURPLN/RSI | 27 | 3.230 | -0.666 | 0.851 | 1.000 | nie dotyczy |
| F/GOLD/ADX | 19 | 6.562 | -0.775 | 0.964 | 1.000 | 1.000 |
| F/GOLD/ATR | 19 | 12.740 | -0.775 | 0.982 | 1.000 | 1.000 |
| F/OIL/ADX | 26 | -101.499 | 12.013 | 0.917 | 1.000 | 1.000 |
| F/OIL/ATR | 26 | -89.127 | 12.013 | 0.923 | 1.000 | 1.000 |
| F/US500/ADX | 21 | -10.836 | -0.078 | 0.913 | 1.000 | 1.000 |
| F/US500/ATR | 21 | 24.927 | -0.078 | 0.950 | 0.630 | 1.000 |
| F/US100/ADX | 27 | 5.867 | 0.394 | 0.901 | 1.000 | 1.000 |
| F/US100/ATR | 27 | 17.408 | 0.394 | 0.932 | 1.000 | 1.000 |
| X/GOLD/falsebreak | 15 | -1.544 | -0.775 | 0.958 | 1.000 | nie dotyczy |
| X/OIL/falsebreak | 25 | 12.716 | 12.013 | 0.958 | 1.000 | nie dotyczy |
| X/US500/falsebreak | 19 | -0.721 | -0.078 | 0.963 | 1.000 | nie dotyczy |
| X/US100/falsebreak | 23 | 4.272 | 0.394 | 0.925 | 1.000 | nie dotyczy |

## Stabilność: wszystkie reżimy, cała próba

| Test | Delta ATRlow | Delta ATRhigh | Delta trendup | Delta trenddown |
|---|---|---|---|---|
| T/GOLD/SMA | -37.745 | -8.023 | 75.308 | -60.506 |
| T/GOLD/EMA | -68.368 | -70.780 | 0.000 | -89.327 |
| T/GOLD/MACD | 0.000 | 31.389 | 0.000 | 11.078 |
| T/US500/SMA | 3.605 | 34.297 | 7.508 | 17.474 |
| T/US500/EMA | -5.303 | 34.297 | -1.896 | 17.474 |
| T/US500/MACD | 3.314 | 179.148 | -8.005 | 183.799 |
| T/US100/SMA | 16.444 | 180.665 | 82.287 | 67.679 |
| T/US100/EMA | -13.989 | 222.141 | 26.013 | 192.457 |
| T/US100/MACD | -45.552 | 111.949 | -40.193 | 143.934 |
| T/OIL/SMA | 64.161 | 128.233 | 128.724 | 40.997 |
| T/OIL/EMA | 211.763 | 128.233 | 128.724 | 241.315 |
| T/OIL/MACD | -62.825 | 496.305 | -373.295 | 234.401 |
| T/EURUSD/SMA | -8.640 | 0.000 | 6.944 | -14.804 |
| T/EURUSD/EMA | -15.924 | 0.000 | 4.721 | -22.348 |
| T/EURUSD/MACD | -2.610 | 0.000 | 15.265 | -12.519 |
| T/GBPUSD/SMA | 14.947 | 0.000 | 27.108 | 0.209 |
| T/GBPUSD/EMA | 14.947 | 0.000 | 27.108 | 0.209 |
| T/GBPUSD/MACD | -2.696 | -18.975 | -11.069 | -3.489 |
| T/EURPLN/SMA | -13.341 | 0.000 | -3.189 | -13.521 |
| T/EURPLN/EMA | -11.567 | 0.000 | -3.189 | -11.201 |
| T/EURPLN/MACD | 16.404 | -2.238 | 3.380 | 15.225 |
| R/EURUSD/RSI | -0.224 | 0.752 | 0.070 | 0.382 |
| R/GBPUSD/RSI | 0.660 | 1.029 | 0.966 | 0.708 |
| R/EURPLN/RSI | 0.312 | 0.450 | 0.860 | -0.213 |
| F/GOLD/ADX | 0.381 | -0.430 | 0.384 | -0.184 |
| F/GOLD/ATR | 0.502 | 0.000 | 1.741 | -0.649 |
| F/OIL/ADX | -1.680 | 0.706 | -1.607 | 0.648 |
| F/OIL/ATR | -4.286 | 0.000 | -5.371 | 1.356 |
| F/US500/ADX | -0.498 | -1.668 | -2.046 | 0.199 |
| F/US500/ATR | 0.363 | 0.000 | -0.092 | 0.546 |
| F/US100/ADX | -1.205 | -0.728 | -3.503 | 1.943 |
| F/US100/ATR | -0.264 | 0.000 | -0.718 | 0.538 |
| X/GOLD/falsebreak | 2.283 | -2.530 | -0.561 | 0.786 |
| X/OIL/falsebreak | -2.983 | 6.752 | -3.964 | 8.048 |
| X/US500/falsebreak | 0.359 | -0.152 | -0.486 | 0.882 |
| X/US100/falsebreak | 4.824 | -1.502 | 2.937 | 0.274 |

## Decyzje

- T: nie wykazano trwałej wartości wygładzenia ponad prosty zwrot20. Dodatni pojedynczy markout nie uprzywilejowuje OIL/US100.
- R: RSI nie wykazał przyrostu po wielokrotności wobec prostego odchylenia. Nie dodawać go jako niezależnego głosu.
- F: brak potwierdzenia, że ADX/ATR poprawiają dobór wejść ponad bazę i kontrolę redukcji ekspozycji.
- X: pojedyncze dodatnie różnice pozostają nieistotne po korekcie. Nie promować false breakout.
- Zero nominacji strategii do wdrożenia. To odrzucenie uzasadnienia promocji tych reguł, nie dowód nieistnienia wszystkich mechanizmów.
- Makro A/B/C: nie obliczono brakujących surprise ani P&L. Nowe źródła i małe próbki w DATA_SOURCES.md; dodatkowe dane IV są oddzielnym eksperymentem alternative_data_edge.

## Koszty i odrzucenia danych

| Rynek | próg spreadu w jednostkach ceny |
|---|---|
| GOLD | 0.460 |
| US500 | 0.700 |
| US100 | 1.300 |
| OIL | 0.040 |
| EURUSD | 0.000 |
| GBPUSD | 0.000 |
| EURPLN | 0.001 |

Próg to max p95 z3 okien22.10, nie historyczny spread każdego wejścia. Stress2×próg+2bps+2bps/dobę. Nie uwzględnia wiernie prowizji, swapów, rolloverów, FX ani slippage; luka wykonania pozostaje.

| Test | siatka | luki | granice | brak wyjścia | przyjęto |
|---|---|---|---|---|---|
| T/GOLD/SMA | 26 | 0 | 2 | 2 | 22 |
| T/GOLD/EMA | 26 | 0 | 2 | 2 | 22 |
| T/GOLD/MACD | 26 | 0 | 2 | 2 | 22 |
| T/US500/SMA | 26 | 0 | 1 | 1 | 24 |
| T/US500/EMA | 26 | 0 | 1 | 1 | 24 |
| T/US500/MACD | 26 | 0 | 1 | 1 | 24 |
| T/US100/SMA | 26 | 0 | 1 | 1 | 24 |
| T/US100/EMA | 26 | 0 | 1 | 1 | 24 |
| T/US100/MACD | 26 | 0 | 1 | 1 | 24 |
| T/OIL/SMA | 26 | 0 | 2 | 2 | 22 |
| T/OIL/EMA | 26 | 0 | 2 | 2 | 22 |
| T/OIL/MACD | 26 | 0 | 2 | 2 | 22 |
| T/EURUSD/SMA | 31 | 0 | 1 | 1 | 29 |
| T/EURUSD/EMA | 31 | 0 | 1 | 1 | 29 |
| T/EURUSD/MACD | 31 | 0 | 1 | 1 | 29 |
| T/GBPUSD/SMA | 31 | 0 | 1 | 1 | 29 |
| T/GBPUSD/EMA | 31 | 0 | 1 | 1 | 29 |
| T/GBPUSD/MACD | 31 | 0 | 1 | 1 | 29 |
| T/EURPLN/SMA | 31 | 0 | 1 | 1 | 29 |
| T/EURPLN/EMA | 31 | 0 | 1 | 1 | 29 |
| T/EURPLN/MACD | 31 | 0 | 1 | 1 | 29 |
| R/EURUSD/RSI | 403 | 37 | 0 | 2 | 364 |
| R/GBPUSD/RSI | 403 | 37 | 0 | 2 | 364 |
| R/EURPLN/RSI | 403 | 37 | 0 | 2 | 364 |
| F/GOLD/ADX | 389 | 27 | 0 | 1 | 361 |
| F/GOLD/ATR | 389 | 27 | 0 | 1 | 361 |
| F/OIL/ADX | 389 | 27 | 0 | 1 | 361 |
| F/OIL/ATR | 389 | 27 | 0 | 1 | 361 |
| F/US500/ADX | 388 | 41 | 0 | 1 | 346 |
| F/US500/ATR | 388 | 41 | 0 | 1 | 346 |
| F/US100/ADX | 388 | 41 | 0 | 1 | 346 |
| F/US100/ATR | 388 | 41 | 0 | 1 | 346 |
| X/GOLD/falsebreak | 389 | 27 | 0 | 1 | 361 |
| X/OIL/falsebreak | 389 | 27 | 0 | 1 | 361 |
| X/US500/falsebreak | 388 | 41 | 0 | 1 | 346 |
| X/US100/falsebreak | 388 | 41 | 0 | 1 | 346 |

## Odtwarzalność

Wynik zapisany 2026-10-28T13:15:45.825839+00:00; Python 3.12.14, NumPy 2.5.4; seed20261028,4000 bootstrap,14dni/blok.
Hash protokołu przed wynikiem: `2d01de4bdd8684e3f80d412e5b3974f528f7ccc28fcd5955bae7933b7813454a`. Hash lokalnego wyniku: `4e2537456c4cbc103276a8db532b1ab1def8f83d9bae3059d3aa56a0412f0e7b`.

| Wejście | świece | SHA256 |
|---|---|---|
| research/edge_audit/inputs/GOLD-D1.json | 261 | 084c1fbf22efefe759b3cf7deb4f4a6d310a5f41dcf432d1e0962d1f95808089 |
| research/edge_audit/inputs/GOLD-H4.json | 1548 | 61f9210625d8b3d2868b4038b0a2e52b81e029b97ef4a7291a7203756b4349d4 |
| research/edge_audit/inputs/US500-D1.json | 262 | 30c2561ebd15f173e52328a2c75b4493893eada10b709d027c4b58f366dcbf75 |
| research/edge_audit/inputs/US500-H4.json | 1546 | e1465de987cf28a8c6f48b11fc65b5f1dce2edbb96300b198688c6379dc1789b |
| research/edge_audit/inputs/US100-D1.json | 262 | f2219bf4b95d421890bdc8f8e7858997713e6b4f9a38d82184c410aef40bc254 |
| research/edge_audit/inputs/US100-H4.json | 1546 | 153a88a92e85013e4771475ebb64c94cbe34851e4916d339f899820d21746190 |
| research/edge_audit/inputs/OIL-D1.json | 261 | 26e620cc15660205b03c608ac90d4459feef345336574735eb2a2fd7f073d9c5 |
| research/edge_audit/inputs/OIL-H4.json | 1548 | 050b3352eb7986f2fb42cef2ad31f3f476ea21e53714584669a4f4a497bd1521 |
| research/edge_audit/inputs/EURUSD-D1.json | 312 | 006e737a30c44941f762acc9d19e2374193cddb52770b10422312c242f8ed75b |
| research/edge_audit/inputs/EURUSD-H4.json | 1607 | fde8a3457e4ab46657b6c09231696e1d80a7f6f651cef3f2dd6cd9a913d1caee |
| research/edge_audit/inputs/GBPUSD-D1.json | 312 | c542772dbcfd187088993ef2bfbcbc2544e509d2ba6a3c7f5ea95ee13ad0ddcc |
| research/edge_audit/inputs/GBPUSD-H4.json | 1607 | d239d6b5c7849d2be10533f01a1e99209a588d8869b2249e1b40c66a7af07ccc |
| research/edge_audit/inputs/EURPLN-D1.json | 312 | 49bdfa8d6c0e006f299490fe4d274eca652c2fce819677772719ac9607bd3a34 |
| research/edge_audit/inputs/EURPLN-H4.json | 1607 | 58766b6590bbc63c2dc6343d1b95f6b2aae9297ed051435f283574e0f62a889f |

| Kod podczas obliczenia | SHA256 |
|---|---|
| experiments.py | 6e0794b705ebaf8f23509c1dc48db91de3c1db700f6096ae026cd75adc80ffdf |
| probe_history.py | 7436e196ba2249378c4af234168d51b305995c10a4f4cf328e8864a76783e2e9 |
| protocol.py | 501b0300ff86eca4ed3062a022393b6f7c0682e6557516ec89d7aa67ee7701ce |
| test_experiments.py | 3a200dcd5b33ee63b707f7978a2169e7a558b77ba5aa29fdc1a3361508ea06ee |

Komendy i granice odtworzenia z prywatnymi wejściami: README.md. Nie pobierano nowych ticków do tych obliczeń.
