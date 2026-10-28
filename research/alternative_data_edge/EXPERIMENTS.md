# Eksperymenty z nowymi danymi — alternative-data-v1

**Wykonano4 rodziny,6 głównych porównań oraz6 z góry określonych testów opóźnienia. Żadne nie przeszło Holm6 ani Holm48.**

Reguły zapisano w HYPOTHESES.md przed obliczeniem. Nie zmieniano ich po wynikach. Testujemy dodatkową informację z Cboe względem tego samego momentum20, nie ponownie dobór EMA. Dane cenowe: D1 brokera, raw27.04–23.10.2026, split01.08, wcześniejsze świece warm-up.

Wszystkie stare ceny są eksploracyjne. Pozyskanie nowego predyktora nie czyni starych zwrotów niezależnym holdoutem. Wiersze Cboe po23.10 nie mogą wejść do okien; nie wykorzystano forward do wyboru hipotezy.

## Poziomy dowodu

1. Zaobserwowana zależność: opóźnione IV w stosunku do późniejszego markoutu Last, obliczona lokalnie.
2. Wartość dodana: sparowana różnica B−A, wobec tego samego modelu bez IV; dodatkowo kontrola cenowej ATR.
3. Markout po progach: poniższe B/A/stress to bps na okazję, z cash; nie netto wykonania.
4. Wykonalność Bid/Ask i pełne koszty: nieweryfikowalne.
5. Potwierdzony edge: NIE.

## Wszystkie wyniki

| Test | n early | n late | B aktywne late | bloki late | Delta early | A late | B late | Delta late | CI95 Delta | B stress late | B minus ATR late | p Holm48 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| V/US500/VIX/lag3 | 13 | 11 | 11 | 6 | 22.295 | -51.282 | -51.282 | 0.000 | 0.000, 0.000 | -68.187 | -62.063 | 1.000 |
| V/US500/VIX/lag7 | 13 | 11 | 7 | 6 | 30.856 | -51.282 | -60.315 | -9.033 | -32.344, 9.814 | -71.073 | -71.096 | 1.000 |
| V/US100/VIX/lag3 | 13 | 11 | 11 | 6 | 33.067 | -89.939 | -89.939 | 0.000 | 0.000, 0.000 | -106.373 | -38.687 | 1.000 |
| V/US100/VIX/lag7 | 13 | 11 | 7 | 6 | 30.249 | -89.939 | -72.734 | 17.205 | -73.645, 103.687 | -83.193 | -21.481 | 1.000 |
| T/US500/VIX9D/lag3 | 13 | 11 | 11 | 6 | 18.457 | -51.282 | -51.282 | 0.000 | 0.000, 0.000 | -68.187 | -62.063 | 1.000 |
| T/US500/VIX9D/lag7 | 13 | 11 | 11 | 6 | 24.188 | -51.282 | -51.282 | 0.000 | 0.000, 0.000 | -68.187 | -62.063 | 1.000 |
| T/US100/VIX9D/lag3 | 13 | 11 | 11 | 6 | 33.628 | -89.939 | -89.939 | 0.000 | 0.000, 0.000 | -106.373 | -38.687 | 1.000 |
| T/US100/VIX9D/lag7 | 13 | 11 | 11 | 6 | 20.539 | -89.939 | -89.939 | 0.000 | 0.000, 0.000 | -106.373 | -38.687 | 1.000 |
| O/OIL/OVX/lag3 | 12 | 10 | 3 | 6 | 24.310 | -155.550 | -88.788 | 66.762 | -146.724, 309.431 | -94.828 | -68.254 | 1.000 |
| O/OIL/OVX/lag7 | 12 | 10 | 4 | 6 | 142.382 | -155.550 | -178.516 | -22.966 | -326.180, 287.562 | -186.629 | -157.982 | 1.000 |
| G/GOLD/GVZ/lag3 | 12 | 10 | 4 | 6 | -43.882 | 40.495 | 27.979 | -12.516 | -117.750, 99.352 | 21.153 | 56.432 | 1.000 |
| G/GOLD/GVZ/lag7 | 12 | 10 | 5 | 6 | -66.011 | 40.495 | 68.614 | 28.119 | -53.405, 110.896 | 60.085 | 97.068 | 1.000 |

n to okazje na stałej siatce, nie liczba niezależnych transakcji. Późna próbka ma6 bloków14dni i tylko10–11 okazji na model. Wspólne rynki/okresy są skorelowane. CI95 są marginalne opisowe; skorygowane p kontrolują wielokrotność przy ograniczonej kalibracji bootstrap.

## Benchmark C i placebo D — główne lag3

| Test | gross B | próg spreadu B | B/aktywne | long po progu | cenowy ATR | p Delta Holm6 | p thinning Holm6 | p sign Holm6 |
|---|---|---|---|---|---|---|---|---|
| V/US500/VIX/lag3 | -50.377 | 0.905 | -51.282 | -3.238 | 10.781 | 1.000 | 1.000 | 1.000 |
| V/US100/VIX/lag3 | -89.505 | 0.434 | -89.939 | -10.586 | -51.253 | 1.000 | 1.000 | 1.000 |
| T/US500/VIX9D/lag3 | -50.377 | 0.905 | -51.282 | -3.238 | 10.781 | 1.000 | 1.000 | 1.000 |
| T/US100/VIX9D/lag3 | -89.505 | 0.434 | -89.939 | -10.586 | -51.253 | 1.000 | 1.000 | 1.000 |
| O/OIL/OVX/lag3 | -87.548 | 1.240 | -295.959 | 261.981 | -20.534 | 1.000 | 1.000 | 1.000 |
| G/GOLD/GVZ/lag3 | 28.404 | 0.426 | 69.947 | -38.535 | -28.454 | 1.000 | 1.000 | 1.000 |

Cash=0 jest jawnie zdefiniowanym benchmarkiem, nie substytutem brakującego wyniku. Thinning zachowuje liczbę aktywnych okien w każdym bloku; signed placebo odwraca signed markout blokami, pozostawiając koszt.

## Stabilność reżimów — wszystkie warianty, cała próba

| Test | Delta ATRlow | Delta ATRhigh | Delta trendup | Delta trenddown |
|---|---|---|---|---|
| V/US500/VIX/lag3 | -1.936 | 65.323 | -2.043 | 54.435 |
| V/US500/VIX/lag7 | 1.012 | 56.506 | 5.056 | 35.125 |
| V/US100/VIX/lag3 | 0.000 | 47.764 | 0.000 | 61.411 |
| V/US100/VIX/lag7 | -3.204 | 70.061 | 16.309 | 43.605 |
| T/US500/VIX9D/lag3 | 0.000 | 47.988 | 0.000 | 39.990 |
| T/US500/VIX9D/lag7 | 0.000 | 62.890 | 10.576 | 20.679 |
| T/US100/VIX9D/lag3 | 0.000 | 48.574 | 0.000 | 62.452 |
| T/US100/VIX9D/lag7 | 0.000 | 29.668 | 19.136 | -8.329 |
| O/OIL/OVX/lag3 | 40.143 | 65.541 | 32.214 | 50.117 |
| O/OIL/OVX/lag7 | 28.323 | 313.598 | 32.214 | 87.230 |
| G/GOLD/GVZ/lag3 | -56.575 | 42.242 | 94.403 | -66.104 |
| G/GOLD/GVZ/lag7 | -38.943 | 18.691 | 94.403 | -57.821 |

## Dostępność i koszty

Lag3 oznacza datę IV starszą o72h+3h marginesu od raw sygnału; lag7 o168h+3h. Nie znamy first publication każdego wiersza Cboe ani pełnej historii offsetów brokera. Dlatego to diagnostyka opóźnionych zależności, a NIE certyfikowany test wejść po historycznej dostępności. Lag nie naprawia rewizji i nie jest dowodem UTC.
D1 mierzymy next-open→open po5 dostępnych świecach. Koszt: max p95 spreadu z3 starych okien22.10 / Last entry. Stress:2×spread+2bps+2bps/dobę. Prowizja/swap/rollover/FX/slippage nie zostały odtworzone; nie liczymy fikcyjnego PF, drawdown kapitału ani R.
Filtr może poprawić średnią tylko dlatego, że usuwa ekspozycję na stratną bazę. Dlatego wymagamy przewagi nad losowym filtrem i kontrolą ATR, a nie samej dodatniej różnicy B−A.

| Test | siatka | gap | boundary | brak wyjścia | brak/stale IV | zaakceptowane |
|---|---|---|---|---|---|---|
| V/US500/VIX/lag3 | 26 | 0 | 1 | 1 | 0 | 24 |
| V/US500/VIX/lag7 | 26 | 0 | 1 | 1 | 0 | 24 |
| V/US100/VIX/lag3 | 26 | 0 | 1 | 1 | 0 | 24 |
| V/US100/VIX/lag7 | 26 | 0 | 1 | 1 | 0 | 24 |
| T/US500/VIX9D/lag3 | 26 | 0 | 1 | 1 | 0 | 24 |
| T/US500/VIX9D/lag7 | 26 | 0 | 1 | 1 | 0 | 24 |
| T/US100/VIX9D/lag3 | 26 | 0 | 1 | 1 | 0 | 24 |
| T/US100/VIX9D/lag7 | 26 | 0 | 1 | 1 | 0 | 24 |
| O/OIL/OVX/lag3 | 26 | 0 | 2 | 2 | 0 | 22 |
| O/OIL/OVX/lag7 | 26 | 0 | 2 | 2 | 0 | 22 |
| G/GOLD/GVZ/lag3 | 26 | 0 | 2 | 2 | 0 | 22 |
| G/GOLD/GVZ/lag7 | 26 | 0 | 2 | 2 | 0 | 22 |

## Odtwarzalność

Wynik 2026-10-28T17:51:09.319919+00:00; seed20261028,4000losowań,14dni/blok. Hash protokołu `e7bd5272a97fceee8341e7a43e6489f04c2b911627a8c6c928652e01fbbabd25`, kodu `6be1b8745d51ffe93f46214bedb76b5a6cc6590eb5f9c805fc80444edfe5f0fd`, prywatnego wyniku `4df578c1067ed60a89fe637677dd20709666062da4ccce9e9759cbd68481531b`.

| Indeks | n | pierwsza data | ostatnia data | SHA256 |
|---|---|---|---|---|
| VIX | 9303 | 01/02/1990 | 10/27/2026 | 6da7f149324ec456c80f6d7e96c90b5d3bcaa3d0f6a4274f7840542db9809265 |
| VIX9D | 3977 | 01/04/2011 | 10/27/2026 | 1d730a489e704a9d85b049de5d33ee8b2978c1d77525e0f567e0bf3d1427201f |
| VVIX | 5134 | 03/06/2006 | 10/27/2026 | 611efbe94b64aa31debb78cdc65cda51490b189d409e6c97580094ce1cb55ae9 |
| OVX | 4301 | 09/18/2009 | 10/27/2026 | 632285cda1b161520626f0ba588f6f7649e2fbf1fdfd3971d07be693c834fd48 |
| GVZ | 4301 | 09/18/2009 | 10/27/2026 | 6738c3ca1a7972494ae5b37c5d85a1cb06ab97e8e2fb463b25e7df9125d38b82 |

Surowe pliki i row-level wyniki nie trafiają do Git. Komendy w README.md. Pięć nowych testów automatycznych przeszło przed obliczeniem; użyte syntetyczne fixtures sprawdzają wyłącznie mechanikę, nie wyniki rynku.
