# COT ponad trend: wyniki eksperymentu

**NIE potwierdzono dodatkowej informacji ani przewagi po rzeczywistych kosztach.** Osiem zapisanych prób:2FX ×2 horyzonty ×2 opóźnienia. Wszystkie Holm8=1 w końcowym okresie2022–2025. Bez optymalizacji i bez zmiany kierunku hipotezy.

To warunkowy test na obecnych wersjach historycznych COT i referencjach Fed. Nie certyfikowany PIT backtest, nie P&L TMS. Daty obserwacji są opóźnione zgodnie z protokołem; brak first-vintage nadal blokuje wniosek o rzeczywistej historycznej wykonalności. Kwoty poniżej to **bps na wspólną okazję**, także gdy B wybiera cash; nie bps na wybrane wejście.

## Końcowy blok2022–2025, wszystkie próby

| Rynek / horyzont / lag | n / B / kwartały | A | B | B−A | 95%CI kwartały | Holm8 | Δ przy dopasowanej ekspozycji | p losowego filtra |
|---|---:|---:|---:|---:|---|---:|---:|---:|
| EURUSD/w1/lag14 | 176 / 86 / 16 | -4.01 | -0.62 | 3.39 | [-10.54, 18.18] | 1.00 | 1.34 | 0.433 |
| EURUSD/w4/lag14 | 45 / 23 / 15 | -22.86 | -28.54 | -5.68 | [-47.82, 46.60] | 1.00 | -16.86 | 0.985 |
| EURUSD/w1/lag28 | 178 / 87 / 16 | -5.50 | -6.70 | -1.20 | [-15.03, 13.49] | 1.00 | -4.01 | 0.853 |
| EURUSD/w4/lag28 | 46 / 23 / 15 | -30.09 | -17.21 | 12.88 | [-24.28, 50.49] | 1.00 | -2.16 | 0.468 |
| GBPUSD/w1/lag14 | 176 / 89 / 16 | -1.06 | -7.64 | -6.58 | [-19.72, 5.92] | 1.00 | -7.11 | 0.944 |
| GBPUSD/w4/lag14 | 45 / 19 / 15 | 0.67 | -45.95 | -46.62 | [-103.83, 5.00] | 1.00 | -46.23 | 1.000 |
| GBPUSD/w1/lag28 | 178 / 97 / 16 | -3.18 | -8.94 | -5.76 | [-13.00, 2.01] | 1.00 | -7.21 | 0.958 |
| GBPUSD/w4/lag28 | 46 / 25 / 15 | -8.65 | 6.95 | 15.59 | [-25.90, 52.60] | 1.00 | 11.64 | 0.143 |

Horyzonty nakładają się między osobnymi wariantami;3 518 zapisanych par łącznie NIE jest liczbą niezależnych transakcji. W obrębie wariantu okna1/4 tygodnie nie zachodzą na siebie. EURUSD i GBPUSD mają wspólny czynnik USD. Końcowa część ma tylko4 bloki roczne; kwartały nadal mogą być zależne.

## Stabilność chronologiczna — główne opóźnienie14dni

| Wariant | Część | n / B | A | B | B−A | CI roczne B−A |
|---|---|---:|---:|---:|---:|---|
| EURUSD/w1/lag14 | discovery | 348 / 188 | 3.79 | 0.43 | -3.36 | [-10.27, 3.71] |
| EURUSD/w1/lag14 | walk_forward | 178 / 93 | 6.84 | 0.76 | -6.08 | [-10.52, -3.20] |
| EURUSD/w1/lag14 | confirmation | 176 / 86 | -4.01 | -0.62 | 3.39 | [-5.71, 11.57] |
| EURUSD/w4/lag14 | discovery | 88 / 46 | 25.09 | 32.43 | 7.34 | [-21.30, 33.25] |
| EURUSD/w4/lag14 | walk_forward | 43 / 19 | 20.94 | 19.56 | -1.38 | [-37.91, 18.15] |
| EURUSD/w4/lag14 | confirmation | 45 / 23 | -22.86 | -28.54 | -5.68 | [-38.79, 30.90] |
| GBPUSD/w1/lag14 | discovery | 348 / 196 | 3.28 | -2.98 | -6.27 | [-15.72, 2.18] |
| GBPUSD/w1/lag14 | walk_forward | 178 / 105 | -7.42 | -1.44 | 5.98 | [-4.23, 17.99] |
| GBPUSD/w1/lag14 | confirmation | 176 / 89 | -1.06 | -7.64 | -6.58 | [-19.22, 5.40] |
| GBPUSD/w4/lag14 | discovery | 88 / 48 | 0.01 | -4.14 | -4.14 | [-42.32, 36.04] |
| GBPUSD/w4/lag14 | walk_forward | 43 / 23 | -53.75 | -14.15 | 39.61 | [3.20, 85.59] |
| GBPUSD/w4/lag14 | confirmation | 45 / 19 | 0.67 | -45.95 | -46.62 | [-98.56, 7.56] |

discovery=2011–2017; walk_forward=2018–2021; confirmation=2022–2025. Ostatnia nazwa jest etykietą podziału, nie stwierdzeniem potwierdzenia edge. Roczne foldy nie uczą parametrów. Wszystkie te okresy po tej analizie są widziane; nie wolno ich ponownie nazwać niezależnymi po strojeniu.

## Progi kosztowe — ostatni blok, wszystkie próby

Base:5bps za okazję +2bps/tydzień. Stress:15bps +5bps/tydzień. Cash nie ponosi progu. Progi są hipotetyczne i nie są historyczną prowizją/spreadem/finansowaniem TMS.

| Wariant | A base | B base | Δ base | A stress | B stress | Δ stress | Δ stress dopasowana ekspozycja |
|---|---:|---:|---:|---:|---:|---:|---:|
| EURUSD/w1/lag14 | -11.01 | -4.04 | 6.97 | -24.01 | -10.39 | 13.61 | 1.34 |
| EURUSD/w4/lag14 | -35.86 | -35.18 | 0.68 | -57.86 | -46.43 | 11.43 | -16.86 |
| EURUSD/w1/lag28 | -12.50 | -10.12 | 2.38 | -25.50 | -16.48 | 9.02 | -4.01 |
| EURUSD/w4/lag28 | -43.09 | -23.71 | 19.38 | -65.09 | -34.71 | 30.38 | -2.16 |
| GBPUSD/w1/lag14 | -8.06 | -11.18 | -3.12 | -21.06 | -17.76 | 3.30 | -7.11 |
| GBPUSD/w4/lag14 | -12.33 | -51.44 | -39.11 | -34.33 | -60.73 | -26.40 | -46.23 |
| GBPUSD/w1/lag28 | -10.18 | -12.76 | -2.57 | -23.18 | -19.84 | 3.34 | -7.21 |
| GBPUSD/w4/lag28 | -21.65 | -0.12 | 21.53 | -43.65 | -12.08 | 31.57 | 11.64 |

Poprawa delty po podniesieniu kosztów może wynikać wyłącznie z mniejszej ekspozycji B. Dlatego dodatnia Δ stress sama nie stanowi przewagi informacyjnej; wymagamy kontroli ekspozycji, niepewności i placebo. Nie policzono fikcyjnego R, lotów, brokerowego Profit Factor ani obsunięcia rachunku.

## Kontrole — ostatni blok

| Wariant | long-only | short-only | cash | losowy filtr średnia | COT52tyg n | B na wspólnym n | placebo52tyg |
|---|---:|---:|---:|---:|---:|---:|---:|
| EURUSD/w1/lag14 | 4.27 | -4.27 | 0 | -1.25 | 160 | 0.16 | 3.66 |
| EURUSD/w4/lag14 | 7.30 | -7.30 | 0 | -0.99 | 41 | -31.19 | -2.24 |
| EURUSD/w1/lag28 | 2.69 | -2.69 | 0 | -2.53 | 162 | -6.04 | -3.09 |
| EURUSD/w4/lag28 | -0.59 | 0.59 | 0 | -19.25 | 42 | -23.75 | -9.66 |
| GBPUSD/w1/lag14 | 1.10 | -1.10 | 0 | -0.29 | 160 | -8.00 | -1.74 |
| GBPUSD/w4/lag14 | -7.68 | 7.68 | 0 | 3.47 | 41 | -54.50 | 5.28 |
| GBPUSD/w1/lag28 | -1.04 | 1.04 | 0 | -1.81 | 162 | -10.04 | -0.88 |
| GBPUSD/w4/lag28 | -16.81 | 16.81 | 0 | -21.23 | 42 | 2.50 | -26.71 |

## Roczne foldy i reżimy, lag14 — bez ponownego dopasowania

| Wariant | Rok | n / B | A | B | Δ |
|---|---|---:|---:|---:|---:|
| EURUSD/w1/lag14 | 2011 | 52 / 29 | 17.11 | -2.28 | -19.39 |
| EURUSD/w1/lag14 | 2012 | 50 / 28 | -5.88 | -3.03 | 2.85 |
| EURUSD/w1/lag14 | 2013 | 41 / 26 | -13.02 | -10.99 | 2.03 |
| EURUSD/w1/lag14 | 2014 | 52 / 28 | 25.67 | 15.55 | -10.12 |
| EURUSD/w1/lag14 | 2015 | 50 / 26 | 2.28 | -2.88 | -5.16 |
| EURUSD/w1/lag14 | 2016 | 52 / 25 | -1.38 | 10.19 | 11.57 |
| EURUSD/w1/lag14 | 2017 | 51 / 26 | -2.35 | -6.36 | -4.01 |
| EURUSD/w1/lag14 | 2018 | 48 / 30 | 2.86 | -0.42 | -3.28 |
| EURUSD/w1/lag14 | 2019 | 31 / 11 | 2.54 | -1.67 | -4.22 |
| EURUSD/w1/lag14 | 2020 | 50 / 25 | 17.56 | 4.72 | -12.84 |
| EURUSD/w1/lag14 | 2021 | 49 / 27 | 2.54 | -0.58 | -3.12 |
| EURUSD/w1/lag14 | 2022 | 52 / 20 | 11.37 | 11.64 | 0.27 |
| EURUSD/w1/lag14 | 2023 | 36 / 25 | -3.14 | -15.26 | -12.12 |
| EURUSD/w1/lag14 | 2024 | 48 / 25 | -9.89 | -1.18 | 8.71 |
| EURUSD/w1/lag14 | 2025 | 40 / 16 | -17.71 | -2.70 | 15.01 |
| EURUSD/w4/lag14 | 2011 | 13 / 7 | 89.38 | 49.53 | -39.85 |
| EURUSD/w4/lag14 | 2012 | 13 / 7 | -4.63 | 33.00 | 37.63 |
| EURUSD/w4/lag14 | 2013 | 11 / 6 | -3.32 | 26.05 | 29.37 |
| EURUSD/w4/lag14 | 2014 | 13 / 7 | 125.76 | 69.61 | -56.16 |
| EURUSD/w4/lag14 | 2015 | 13 / 7 | -52.08 | -38.00 | 14.08 |
| EURUSD/w4/lag14 | 2016 | 13 / 6 | 10.23 | 37.26 | 27.03 |
| EURUSD/w4/lag14 | 2017 | 12 / 6 | 4.30 | 49.94 | 45.64 |
| EURUSD/w4/lag14 | 2018 | 13 / 7 | -11.70 | 12.54 | 24.24 |
| EURUSD/w4/lag14 | 2019 | 7 / 2 | 25.88 | -35.44 | -61.32 |
| EURUSD/w4/lag14 | 2020 | 12 / 5 | 54.98 | 53.34 | -1.64 |
| EURUSD/w4/lag14 | 2021 | 11 / 5 | 19.22 | 25.98 | 6.76 |
| EURUSD/w4/lag14 | 2022 | 13 / 6 | 31.99 | -17.74 | -49.73 |
| EURUSD/w4/lag14 | 2023 | 9 / 5 | -75.26 | -66.67 | 8.59 |
| EURUSD/w4/lag14 | 2024 | 13 / 9 | -0.31 | -15.24 | -14.94 |
| EURUSD/w4/lag14 | 2025 | 10 / 3 | -76.32 | -25.55 | 50.77 |
| GBPUSD/w1/lag14 | 2011 | 52 / 28 | 5.26 | -12.40 | -17.67 |
| GBPUSD/w1/lag14 | 2012 | 50 / 29 | -10.12 | -5.98 | 4.15 |
| GBPUSD/w1/lag14 | 2013 | 41 / 28 | -16.51 | -10.98 | 5.53 |
| GBPUSD/w1/lag14 | 2014 | 52 / 31 | 16.65 | 20.47 | 3.82 |
| GBPUSD/w1/lag14 | 2015 | 50 / 25 | -8.97 | -8.92 | 0.05 |
| GBPUSD/w1/lag14 | 2016 | 52 / 26 | 31.35 | 2.14 | -29.21 |
| GBPUSD/w1/lag14 | 2017 | 51 / 29 | 0.10 | -7.34 | -7.44 |
| GBPUSD/w1/lag14 | 2018 | 48 / 26 | 7.74 | -1.32 | -9.07 |
| GBPUSD/w1/lag14 | 2019 | 31 / 18 | -26.88 | -2.05 | 24.84 |
| GBPUSD/w1/lag14 | 2020 | 50 / 32 | -23.89 | -14.18 | 9.71 |
| GBPUSD/w1/lag14 | 2021 | 49 / 29 | 6.85 | 11.84 | 4.99 |
| GBPUSD/w1/lag14 | 2022 | 52 / 24 | 22.08 | -3.60 | -25.68 |
| GBPUSD/w1/lag14 | 2023 | 36 / 22 | -13.49 | -21.36 | -7.86 |
| GBPUSD/w1/lag14 | 2024 | 48 / 26 | -2.58 | -0.81 | 1.77 |
| GBPUSD/w1/lag14 | 2025 | 40 / 17 | -18.14 | -8.77 | 9.38 |
| GBPUSD/w4/lag14 | 2011 | 13 / 7 | 22.59 | -62.16 | -84.75 |
| GBPUSD/w4/lag14 | 2012 | 13 / 7 | -51.80 | -46.66 | 5.13 |
| GBPUSD/w4/lag14 | 2013 | 11 / 8 | -89.38 | 6.75 | 96.13 |
| GBPUSD/w4/lag14 | 2014 | 13 / 7 | 27.95 | 24.50 | -3.46 |
| GBPUSD/w4/lag14 | 2015 | 13 / 7 | -19.23 | 7.40 | 26.63 |
| GBPUSD/w4/lag14 | 2016 | 13 / 6 | 88.95 | 22.19 | -66.76 |
| GBPUSD/w4/lag14 | 2017 | 12 / 6 | 7.80 | 22.78 | 14.98 |
| GBPUSD/w4/lag14 | 2018 | 13 / 7 | -27.60 | -25.53 | 2.07 |
| GBPUSD/w4/lag14 | 2019 | 7 / 4 | -123.48 | -17.76 | 105.72 |
| GBPUSD/w4/lag14 | 2020 | 12 / 7 | -114.18 | -40.32 | 73.85 |
| GBPUSD/w4/lag14 | 2021 | 11 / 5 | 25.63 | 30.16 | 4.54 |
| GBPUSD/w4/lag14 | 2022 | 13 / 6 | 65.94 | -49.49 | -115.42 |
| GBPUSD/w4/lag14 | 2023 | 9 / 5 | -103.59 | -129.09 | -25.50 |
| GBPUSD/w4/lag14 | 2024 | 13 / 5 | 75.72 | 20.77 | -54.95 |
| GBPUSD/w4/lag14 | 2025 | 10 / 3 | -87.92 | -53.27 | 34.65 |

| Wariant | Zmienność (cała próba) | n | Δ |
|---|---|---:|---:|
| EURUSD/w1/lag14 | high | 225 | 1.25 |
| EURUSD/w1/lag14 | low | 457 | -3.79 |
| EURUSD/w1/lag14 | unknown | 20 | -10.34 |
| EURUSD/w4/lag14 | high | 48 | 14.98 |
| EURUSD/w4/lag14 | low | 108 | 0.57 |
| EURUSD/w4/lag14 | unknown | 20 | -22.45 |
| GBPUSD/w1/lag14 | high | 317 | -4.60 |
| GBPUSD/w1/lag14 | low | 365 | -0.16 |
| GBPUSD/w1/lag14 | unknown | 20 | -38.06 |
| GBPUSD/w4/lag14 | high | 74 | -2.46 |
| GBPUSD/w4/lag14 | low | 82 | 3.25 |
| GBPUSD/w4/lag14 | unknown | 20 | -42.17 |

Próg high/low korzysta tylko z wcześniejszych cen i wcześniejszej mediany; nie stanowi dodatkowo dobieranej strategii. Zestawienia są opisowe, nie nowymi potwierdzeniami. Szczegółowe odrzucenia i wyniki obu kierunków są w zapisanym JSON.

## Decyzja

**Odrzucamy promocję tej zamrożonej hipotezy COT.** Brak istotnej delty, zmiany znaku między horyzontami/opóźnieniami i brak certyfikacji as-of nie uzasadniają dalszego strojenia. Nie obalono wszystkich zastosowań COT ani wszystkich rynków — cztery kontrakty poza FX nie były testowane cenowo. Żadnego kandydata do DEMO.

Walidacja:11 testów automatycznych PASS; niezależna kontrola 3518 wierszy, hashy protokołu/kodu/8 artefaktów PASS. 27 chronionych plików runtime/config bez zmian. Kolektor w chwili 2026-10-28T23:13:56.383133+00:00: COLLECTING, zgodność konfiguracji zamrożonej=True. Nie jest to audyt odporności DEMO.

Hash protokołu `b2c4254a66180a92714cb44ee575e5ef6e8a48c60c22d0edfb108d8f8f1eb949`; wyniki obliczone 2026-10-28T23:10:54.631323+00:00. Kod/źródła/protokół oraz niekorzystne wyniki pozostają zapisane. Surowe archiwa i szczegółowe wyniki JSON zostają lokalnie.
