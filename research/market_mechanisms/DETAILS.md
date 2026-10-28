# Szczegóły wszystkich obliczeń

Wszystkie liczby cenowe poniżej są bps markoutów Last lub ich scenariusza, NIE netto rachunku.
PF*: suma dodatnich/suma ujemnych markoutów po progu. DD*: obsunięcie sumy markoutów grupowanej po raw dniu wyjścia; nie portfel.

## early

| Test | N | Bloki | Po progu | Long kontrola | Delta | CI95 | p-zero | p-placebo | PF* | DD* |
|---|---|---|---|---|---|---|---|---|---|---|
| M1/GOLD | 13 | 7 | -21.299 | -102.132 | 80.834 | [-150.799, 94.16] | 0.618595 | 0.611097 | 0.850 | 935.278 |
| M1/US500 | 13 | 7 | 26.085 | 26.085 | 0.000 | [-43.538, 92.442] | 0.227443 | 0.236941 | 1.600 | 261.848 |
| M1/OIL | 13 | 7 | -103.662 | -103.662 | 0.000 | [-512.265, 346.868] | 0.671832 | 0.669833 | 0.713 | 4057.013 |
| M1/EURPLN | 16 | 7 | 10.235 | 10.235 | 0.000 | [-4.557, 23.015] | 0.062234 | 0.125969 | 2.256 | 41.463 |
| M1/EURUSD | 16 | 7 | 7.860 | -13.895 | 21.755 | [-19.967, 30.271] | 0.253437 | 0.283429 | 1.413 | 96.239 |
| M1/GBPUSD | 16 | 7 | -20.685 | -8.044 | -12.641 | [-52.719, 12.344] | 0.891527 | 0.856036 | 0.482 | 438.618 |
| M1/US100 | 13 | 7 | 24.745 | 24.745 | 0.000 | [-120.787, 175.988] | 0.352662 | 0.372157 | 1.248 | 829.473 |
| M2/EURPLN | 85 | 7 | -0.745 | -1.254 | 0.509 | [-2.271, 0.351] | 0.856286 | 0.146463 | 0.740 | 73.942 |
| M2/EURUSD | 79 | 7 | 0.075 | 0.225 | -0.150 | [-2.282, 2.89] | 0.462884 | 0.417146 | 1.017 | 87.046 |
| M2/GBPUSD | 92 | 7 | 0.086 | 1.260 | -1.174 | [-2.48, 2.776] | 0.473632 | 0.341665 | 1.019 | 97.079 |
| M3/GOLD | 3 | 1 | 20.798 | -41.170 | 61.968 | n/a: <2 bloki | 1.000000 | 1.000000 | 1.562 | 82.709 |
| M3/OIL | 8 | 3 | -44.425 | 72.270 | -116.695 | [-162.513, 45.34] | 0.742064 | 0.623594 | 0.567 | 487.539 |
| M4/US100-US500 | 57 | 6 | -0.721 | -2.003 | 1.282 | [-3.061, 1.748] | 0.719570 | 0.475131 | 0.835 | 108.444 |
| M1/ALL | 100 | 7 | -10.051 | -22.018 | 11.967 | [-66.699, 49.794] | 0.616596 | 0.603849 | 0.894 | 3746.049 |
| M2/ALL | 256 | 7 | -0.193 | 0.106 | -0.299 | [-2.054, 1.726] | 0.617096 | 0.268933 | 0.951 | 172.367 |
| M3/ALL | 11 | 3 | -26.637 | 41.332 | -67.969 | [-162.513, 45.34] | 0.742064 | 0.623594 | 0.686 | 487.539 |
| M4/ALL | 57 | 6 | -0.721 | -2.003 | 1.282 | [-3.061, 1.748] | 0.719570 | 0.475131 | 0.835 | 108.444 |

## late

| Test | N | Bloki | Po progu | Long kontrola | Delta | CI95 | p-zero | p-placebo | PF* | DD* |
|---|---|---|---|---|---|---|---|---|---|---|
| M1/GOLD | 11 | 6 | -28.120 | 25.985 | -54.105 | [-218.026, 137.597] | 0.620845 | 0.611347 | 0.816 | 1440.683 |
| M1/US500 | 11 | 6 | 12.869 | 12.869 | 0.000 | [-52.603, 62.377] | 0.349913 | 0.338915 | 1.288 | 193.791 |
| M1/OIL | 11 | 6 | -149.333 | 196.866 | -346.199 | [-533.347, 228.897] | 0.781305 | 0.726318 | 0.511 | 2917.235 |
| M1/EURPLN | 14 | 6 | 9.597 | 9.597 | 0.000 | [0.952, 16.563] | 0.000250 | 0.014496 | 1.818 | 45.488 |
| M1/EURUSD | 14 | 6 | 9.706 | -21.012 | 30.718 | [-26.614, 46.049] | 0.323919 | 0.293927 | 1.566 | 217.413 |
| M1/GBPUSD | 14 | 6 | -9.961 | -5.513 | -4.449 | [-41.001, 21.955] | 0.730567 | 0.709073 | 0.612 | 248.427 |
| M1/US100 | 11 | 6 | 28.412 | 28.412 | 0.000 | [-110.73, 149.622] | 0.331167 | 0.355661 | 1.301 | 516.415 |
| M2/EURPLN | 83 | 6 | -1.686 | -0.260 | -1.426 | [-3.588, -0.141] | 0.968258 | 0.569358 | 0.549 | 142.477 |
| M2/EURUSD | 76 | 6 | -0.220 | -1.101 | 0.881 | [-1.725, 1.101] | 0.638590 | 0.453387 | 0.933 | 95.312 |
| M2/GBPUSD | 84 | 6 | -0.712 | -1.555 | 0.843 | [-1.811, 0.433] | 0.896776 | 0.652837 | 0.831 | 128.197 |
| M3/GOLD | 3 | 1 | 35.752 | 35.752 | 0.000 | n/a: <2 bloki | 1.000000 | 1.000000 | 4.361 | 0.000 |
| M3/OIL | 5 | 3 | -116.613 | -147.645 | 31.032 | [-314.13, 100.053] | 0.958010 | 0.632592 | 0.214 | 683.116 |
| M4/US100-US500 | 61 | 6 | 1.442 | 0.860 | 0.582 | [-0.136, 3.888] | 0.098225 | 0.032492 | 1.384 | 57.528 |
| M1/ALL | 86 | 6 | -15.897 | 31.029 | -46.925 | [-52.133, 9.862] | 0.824544 | 0.629343 | 0.814 | 2115.286 |
| M2/ALL | 243 | 6 | -0.891 | -0.971 | 0.080 | [-2.144, 0.245] | 0.919270 | 0.592352 | 0.763 | 305.656 |
| M3/ALL | 8 | 3 | -59.476 | -78.871 | 19.395 | [-314.13, 51.827] | 0.637091 | 0.632592 | 0.385 | 683.116 |
| M4/ALL | 61 | 6 | 1.442 | 0.860 | 0.582 | [-0.136, 3.888] | 0.098225 | 0.032492 | 1.384 | 57.528 |

## all

| Test | N | Bloki | Po progu | Long kontrola | Delta | CI95 | p-zero | p-placebo | PF* | DD* |
|---|---|---|---|---|---|---|---|---|---|---|
| M1/GOLD | 24 | 13 | -24.425 | -43.412 | 18.987 | [-136.706, 73.862] | 0.689828 | 0.639340 | 0.834 | 1857.252 |
| M1/US500 | 24 | 13 | 20.028 | 20.028 | 0.000 | [-27.62, 63.768] | 0.192952 | 0.204699 | 1.455 | 261.848 |
| M1/OIL | 24 | 13 | -124.595 | 34.080 | -158.675 | [-427.129, 166.883] | 0.785804 | 0.772807 | 0.629 | 4372.482 |
| M1/EURPLN | 30 | 13 | 9.937 | 9.937 | 0.000 | [1.875, 17.979] | 0.005999 | 0.015746 | 2.012 | 70.475 |
| M1/EURUSD | 30 | 13 | 8.721 | -17.216 | 25.938 | [-13.093, 29.434] | 0.220445 | 0.221445 | 1.480 | 301.099 |
| M1/GBPUSD | 30 | 13 | -15.681 | -6.863 | -8.818 | [-38.937, 7.488] | 0.906523 | 0.886778 | 0.529 | 517.708 |
| M1/US100 | 24 | 13 | 26.426 | 26.426 | 0.000 | [-75.629, 123.712] | 0.295926 | 0.309673 | 1.271 | 829.473 |
| M2/EURPLN | 168 | 13 | -1.210 | -0.763 | -0.447 | [-2.347, -0.213] | 0.981505 | 0.245939 | 0.633 | 203.964 |
| M2/EURUSD | 155 | 13 | -0.070 | -0.425 | 0.356 | [-1.525, 1.519] | 0.529118 | 0.412397 | 0.982 | 148.258 |
| M2/GBPUSD | 176 | 13 | -0.295 | -0.083 | -0.211 | [-1.657, 1.262] | 0.654586 | 0.423394 | 0.933 | 180.716 |
| M3/GOLD | 6 | 2 | 28.275 | -2.709 | 30.984 | [20.798, 35.752] | 0.000250 | 0.243439 | 2.186 | 82.709 |
| M3/OIL | 13 | 6 | -72.190 | -12.313 | -59.877 | [-183.083, 33.543] | 0.917271 | 0.791552 | 0.400 | 1070.603 |
| M4/US100-US500 | 118 | 12 | 0.397 | -0.523 | 0.920 | [-1.152, 2.036] | 0.318670 | 0.097976 | 1.098 | 108.444 |
| M1/ALL | 186 | 13 | -12.754 | 2.509 | -15.263 | [-48.354, 22.336] | 0.735816 | 0.722819 | 0.859 | 4380.532 |
| M2/ALL | 499 | 13 | -0.533 | -0.418 | -0.115 | [-1.644, 0.631] | 0.821295 | 0.344914 | 0.861 | 463.792 |
| M3/ALL | 19 | 6 | -40.464 | -9.280 | -31.184 | [-147.991, 32.872] | 0.797801 | 0.778055 | 0.549 | 963.347 |
| M4/ALL | 118 | 12 | 0.397 | -0.523 | 0.920 | [-1.152, 2.036] | 0.318670 | 0.097976 | 1.098 | 108.444 |

## Wszystkie odrzucenia obserwacji

| Test | Powody i liczby |
|---|---|
| M1/GOLD | raw_signals=130, overlap=96, split_boundary=5, unobserved_exit=5, accepted_markouts=24 |
| M1/US500 | raw_signals=130, overlap=96, split_boundary=5, unobserved_exit=5, accepted_markouts=24 |
| M1/OIL | raw_signals=130, overlap=96, split_boundary=5, unobserved_exit=5, accepted_markouts=24 |
| M1/EURPLN | raw_signals=155, overlap=120, split_boundary=3, unobserved_exit=2, accepted_markouts=30 |
| M1/EURUSD | raw_signals=155, overlap=120, split_boundary=3, unobserved_exit=2, accepted_markouts=30 |
| M1/GBPUSD | raw_signals=155, overlap=120, split_boundary=3, unobserved_exit=2, accepted_markouts=30 |
| M1/US100 | raw_signals=130, overlap=96, split_boundary=5, unobserved_exit=5, accepted_markouts=24 |
| M2/EURPLN | raw_signals=265, overlap=81, cross_raw_day=5, gap=3, raw_hour_filter=8, accepted_markouts=168 |
| M2/EURUSD | raw_signals=261, overlap=60, cross_raw_day=7, raw_hour_filter=39, accepted_markouts=155 |
| M2/GBPUSD | raw_signals=274, raw_hour_filter=25, overlap=57, gap=5, cross_raw_day=11, accepted_markouts=176 |
| M3/GOLD | raw_signals=9, overlap=2, gap=1, accepted_markouts=6 |
| M3/OIL | raw_signals=15, overlap=2, accepted_markouts=13 |
| M4/US100-US500 | raw_signals=424, gap=84, overlap=222, accepted_markouts=118 |

Przy jednym bloku bootstrap daje zdegenerowany punkt; nie jest to przedział niepewności. Dlatego pokazano n/a, a p jest konserwatywnie ustawione na 1. Surowy wynik arytmetyczny w JSON zachowano bez nadpisania.

## Korelacje godzinowe — opisowe, bez selekcji par

| A | B | Okres | N wspólnych godzin | Pearson |
|---|---|---|---|---|
| GOLD | US500 | early | 1523 | 0.535 |
| GOLD | US500 | late | 1316 | 0.411 |
| GOLD | OIL | early | 1525 | -0.370 |
| GOLD | OIL | late | 1318 | -0.310 |
| GOLD | EURPLN | early | 1525 | -0.376 |
| GOLD | EURPLN | late | 1318 | -0.282 |
| GOLD | EURUSD | early | 1525 | 0.593 |
| GOLD | EURUSD | late | 1318 | 0.471 |
| GOLD | GBPUSD | early | 1525 | 0.552 |
| GOLD | GBPUSD | late | 1318 | 0.463 |
| GOLD | US100 | early | 1523 | 0.481 |
| GOLD | US100 | late | 1316 | 0.367 |
| US500 | OIL | early | 1523 | -0.370 |
| US500 | OIL | late | 1316 | -0.362 |
| US500 | EURPLN | early | 1523 | -0.334 |
| US500 | EURPLN | late | 1316 | -0.269 |
| US500 | EURUSD | early | 1523 | 0.353 |
| US500 | EURUSD | late | 1316 | 0.269 |
| US500 | GBPUSD | early | 1523 | 0.373 |
| US500 | GBPUSD | late | 1316 | 0.303 |
| US500 | US100 | early | 1523 | 0.924 |
| US500 | US100 | late | 1316 | 0.877 |
| OIL | EURPLN | early | 1525 | 0.348 |
| OIL | EURPLN | late | 1318 | 0.248 |
| OIL | EURUSD | early | 1525 | -0.326 |
| OIL | EURUSD | late | 1318 | -0.167 |
| OIL | GBPUSD | early | 1525 | -0.309 |
| OIL | GBPUSD | late | 1318 | -0.140 |
| OIL | US100 | early | 1523 | -0.297 |
| OIL | US100 | late | 1316 | -0.334 |
| EURPLN | EURUSD | early | 1663 | -0.356 |
| EURPLN | EURUSD | late | 1428 | -0.249 |
| EURPLN | GBPUSD | early | 1663 | -0.386 |
| EURPLN | GBPUSD | late | 1426 | -0.301 |
| EURPLN | US100 | early | 1523 | -0.293 |
| EURPLN | US100 | late | 1316 | -0.211 |
| EURUSD | GBPUSD | early | 1663 | 0.841 |
| EURUSD | GBPUSD | late | 1426 | 0.830 |
| EURUSD | US100 | early | 1523 | 0.301 |
| EURUSD | US100 | late | 1316 | 0.199 |
| GBPUSD | US100 | early | 1523 | 0.315 |
| GBPUSD | US100 | late | 1316 | 0.205 |

Korelacja równoczesna nie dowodzi predykcji, kointegracji ani niezależności sygnałów. Para M4 była wybrana przed jej policzeniem.

## Kontrola reżimów sygnału (opisowa, bez strojenia)

M1: znak trendu; M2: ER poniżej 0,15 / 0,15–0,30; M3: ekspansja ATR poniżej 1,5 / od 1,5; M4: abs(z) poniżej 3 / od 3.
Te dodatkowe przekroje powstały przy raportowaniu po obejrzeniu agregatów, więc są POST HOC. Nie są nowymi kandydatami ani częścią 17 testów potwierdzających.

| Reżim post hoc | N | Last brutto | Po progu | Stress |
|---|---|---|---|---|
| M1/high | 125 | -5.712 | -7.191 | -23.661 |
| M1/low | 61 | -23.270 | -24.154 | -39.563 |
| M2/high | 338 | 0.150 | -0.606 | -3.528 |
| M2/low | 161 | 0.470 | -0.380 | -3.397 |
| M3/high | 3 | 50.389 | 45.340 | 37.624 |
| M3/low | 16 | -53.274 | -56.552 | -62.497 |
| M4/high | 13 | 1.052 | 0.320 | -2.745 |
| M4/low | 105 | 1.134 | 0.407 | -2.654 |
