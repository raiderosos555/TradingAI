> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# TRADE_DIAGNOSTICS — przyczyny wyników

Stan audytu: 2026-10-24T18:09:09.311248+00:00. Badanie offline; bez nowych zleceń, zmian DEMO, konfiguracji, Execution Engine i Risk Managera. Kwoty w PLN, o ile nie zaznaczono inaczej.

**Wykryty błąd ceny wykonania:** wszystkie siedem kontraktów zgłasza `chart_mode=1` (Last). Rekonstrukcja pełnej godziny 22.10 13:00–14:00 UTC z ticków odtworzyła zapisany OHLC dokładnie z Last dla każdego instrumentu; OHLC Bid różni się. Oba replays zakładają OHLC Bid. Poniższe PnL/PF są więc wynikami oryginalnego, niepoprawnie przyjętego modelu ceny, a nie zweryfikowanego wykonania. Nie naprawiono ich po cichu; wymagana jest osobna walidacja na Bid/Ask.

Całość: `trades_enriched.json/csv` (4294 rekordy, każdy ze źródłem i indeksem), `run_statistics.json/csv` (88 przebiegów), `subgroup_statistics.json/csv` (6493 grupy). Nie sumować powtarzanych wariantów. 3666 rekordów ma zweryfikowane odtworzenie pól wejścia; 628 starszych ma jawne UNKNOWN. Brakujące pola nie zostały odgadnięte z PnL.

## Obecne strategie — podstawowy okres od 31.08

| Rynek | N | Netto | PF | Śr. R | Mediana R | SD R | Wygrana śr. | Strata śr. | DD H1 | Seria strat | Mediana h |
|---|---|---|---|---|---|---|---|---|---|---|---|
| GOLD | 48 | -21.474 | 0.924 | -0.031 | -0.985 | 1.198 | 13.046 | -10.085 | 94.905 | 5 | 9.500 |
| US500 | 56 | -34.818 | 0.790 | -0.101 | -0.959 | 1.183 | 6.252 | -4.746 | 48.398 | 6 | 6.500 |
| US100 | 46 | 201.069 | 1.935 | 0.345 | 0.456 | 1.255 | 16.003 | -10.751 | 62.078 | 4 | 8.000 |
| OIL | 52 | -267.847 | 0.814 | -0.093 | -0.948 | 1.171 | 61.726 | -43.656 | 532.881 | 8 | 6.000 |
| EURUSD | 54 | -106.298 | 0.609 | -0.092 | -0.843 | 1.014 | 7.189 | -8.762 | 133.574 | 4 | 6.000 |
| EURPLN | 33 | -74.035 | 0.448 | -0.274 | -0.797 | 0.863 | 5.463 | -6.097 | 79.035 | 6 | 5.000 |
| GBPUSD | 49 | -60.624 | 0.752 | -0.110 | -0.869 | 1.026 | 9.191 | -8.429 | 110.191 | 6 | 5.000 |

R to netto / początkowy zarezerwowany budżet ryzyka, obejmujący także bufor kosztów. Nie jest identyczne z czystą odległością entry–SL. PF liczymy z sum zysków i strat w PLN; dodatni średni R może współistnieć ze stratą PLN, gdy przegrywają transakcje z większym początkowym ryzykiem. DD H1 jest raportowanym mark-to-market; `closed_equity_DD_PLN` w CSV to osobna krzywa zaksięgowanych pełnych wyników, bez ścieżki częściowych realizacji.

| Rynek | Strategia | N | Netto | PF | Śr. R | CI95 śr. R |
|---|---|---|---|---|---|---|
| EURPLN | local_false_breakout_v1 | 19 | -23.983 | 0.622 | -0.143 | — |
| EURPLN | local_breakout_v1 | 14 | -50.052 | 0.291 | -0.453 | — |
| EURUSD | local_false_breakout_v1 | 34 | -15.996 | 0.880 | -0.016 | [-0.279; 0.254] |
| EURUSD | local_breakout_v1 | 20 | -90.302 | 0.346 | -0.221 | [-0.712; 0.194] |
| GBPUSD | local_false_breakout_v1 | 36 | -41.389 | 0.759 | -0.114 | [-0.345; 0.146] |
| GBPUSD | local_breakout_v1 | 13 | -19.234 | 0.735 | -0.096 | — |
| GOLD | local_false_breakout_v1 | 35 | 8.778 | 1.048 | 0.035 | [-0.354; 0.391] |
| GOLD | local_breakout_v1 | 13 | -30.252 | 0.692 | -0.208 | — |
| OIL | local_false_breakout_v1 | 31 | -18.833 | 0.977 | 0.013 | [-0.511; 0.655] |
| OIL | local_breakout_v1 | 21 | -249.013 | 0.598 | -0.249 | [-0.530; 0.059] |
| US100 | local_false_breakout_v1 | 31 | 85.150 | 1.528 | 0.295 | [-0.120; 0.675] |
| US100 | local_breakout_v1 | 15 | 115.919 | 3.157 | 0.449 | — |
| US500 | local_false_breakout_v1 | 37 | -15.058 | 0.836 | -0.123 | [-0.410; 0.167] |
| US500 | local_breakout_v1 | 19 | -19.760 | 0.733 | -0.058 | — |

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

## Reżimy oraz definicje

A: (EMA20−EMA50)/ATR14 ≥0,5; B: ≤−0,5; C: pomiędzy tymi progami. To jawna, opisowa definicja trendu/konsolidacji dla audytu, nie oryginalny filtr strukturalny strategii. H1/H4/D1 korzystają wyłącznie z zakończonych świec; ich czasy zapisano per trade. Oryginalny trend struktury jest osobnym polem. D: ATR14 w górnych 20% ostatnich maksymalnie 200 zamkniętych H1; E: dolne 20%. D/E nakładają się na A/B/C. F: niedostępne — brak wiarygodnego, historycznego archiwum makro z czasem pierwszej dostępności.

Dla każdego przebiegu, instrumentu i rozpoznanej strategii CSV zawiera podział po reżimie, kierunku, godzinie UTC, dniu tygodnia, miesiącu i przyczynie wyjścia. Godzina Warszawy uwzględnia DST, lecz pierwotny czas brokera nadal wymaga weryfikacji. Podgrupy <30 oznaczono `small_group`; przy N<20 nie pokazujemy przedziału blokowego, bo zbyt mało bloków daje pozorną precyzję. Pozostałe CI są opisowym bootstrapem 600 prób bloków po 5 chronologicznych transakcji, bez korekty wielokrotnego przeszukiwania.

## Pomiar cofnięć i jakości wybicia

`MAE/MFE_pre_exit_price_R` wykorzystują pełne świece przed świecą wyjścia; `including_exit` włącza całą świecę wyjścia, która może zawierać ruch po zamknięciu pozycji. To zakresy ekstremów cen, nie dokładne MAE/MFE wykonania, nie PnL po kosztach i nie wynik częściowych zamknięć. Null oznacza brak wystarczających świec. Bez ticków nie można rozstrzygnąć kolejności dotknięć.

`reclosed_inside_prior_range_first3h` sprawdza powrót close do kanału poprzednich 20 świec w pierwszych trzech godzinach lub do wyjścia. Może obejmować close świecy, na której wcześniej wykonano SL. Jest diagnozą po transakcji, **nie dopuszczalnym filtrem wejścia** bez nowej reguły czekania i nowej ceny wykonania.

| Rynek/okres | Powrót do kanału | N breakout | Netto | Śr. R |
|---|---|---|---|---|
| US100-development | False | 19 | 8.559 | 0.097 |
| US100-development | True | 14 | -92.248 | -0.304 |
| US100-validation | False | 10 | 153.650 | 1.009 |
| US100-validation | True | 5 | -37.731 | -0.672 |
| OIL-development | False | 18 | 429.806 | 0.520 |
| OIL-development | True | 6 | -190.584 | -0.700 |
| OIL-validation | False | 12 | -69.872 | -0.132 |
| OIL-validation | True | 9 | -179.141 | -0.405 |

## Konkretne stratne wejścia

| Rynek | Wejście UTC | Kierunek | Entry | SL | TP | SL/ATR | Lot | Ryzyko PLN | Netto | H4/D1 | Powrót w 3h |
|---|---|---|---|---|---|---|---|---|---|---|---|
| US100 | 2026-10-22T19:00:00+00:00 | SELL | 29079.900 | 29265.200 | 28709.800 | 1.502 | 0.001 | 14.500 | -14.389 | DOWN/RANGE | True |
| US100 | 2026-10-15T07:00:00+00:00 | SELL | 29789.500 | 29968.200 | 29432.700 | 1.502 | 0.001 | 13.988 | -13.877 | DOWN/UP | True |
| US100 | 2026-09-14T08:00:00+00:00 | SELL | 28916.900 | 29041.200 | 28668.800 | 1.503 | 0.001 | 9.772 | -9.660 | RANGE/RANGE | False |
| OIL | 2026-09-24T16:00:00+00:00 | BUY | 96.540 | 95.120 | 99.330 | 1.524 | 0.010 | 58.183 | -56.118 | DOWN/UP | True |
| OIL | 2026-09-22T11:00:00+00:00 | SELL | 89.530 | 90.860 | 86.920 | 1.534 | 0.010 | 54.682 | -52.619 | DOWN/UP | True |
| OIL | 2026-09-21T15:00:00+00:00 | SELL | 92.200 | 93.500 | 89.660 | 1.534 | 0.010 | 53.515 | -51.479 | RANGE/UP | False |

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

Wpływ kosztów i podgrupy H4/D1 szczegółowo przedstawia `US100_VS_OIL.md`. Zgodność kierunku H4/D1 nie gwarantuje rentowności: w końcowym OIL wszystkie trzy podgrupy H4 breakout były stratne (N=5–10). Nie należy wybierać godzin czy progów ATR na podstawie najwyższej małej podgrupy.
