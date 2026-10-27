> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# VALIDATION_REPORT — walidacja i jej ograniczenia

Stan audytu: 2026-10-24T18:09:09.311248+00:00. Badanie offline; bez nowych zleceń, zmian DEMO, konfiguracji, Execution Engine i Risk Managera. Kwoty w PLN, o ile nie zaznaczono inaczej.

**Wykryty błąd ceny wykonania:** wszystkie siedem kontraktów zgłasza `chart_mode=1` (Last). Rekonstrukcja pełnej godziny 22.10 13:00–14:00 UTC z ticków odtworzyła zapisany OHLC dokładnie z Last dla każdego instrumentu; OHLC Bid różni się. Oba replays zakładają OHLC Bid. Poniższe PnL/PF są więc wynikami oryginalnego, niepoprawnie przyjętego modelu ceny, a nie zweryfikowanego wykonania. Nie naprawiono ich po cichu; wymagana jest osobna walidacja na Bid/Ask.

**Wynik niezależnej walidacji: brak dostępnej niezależnej próby.** Wszystkie poniższe testy na danych do 23.10.2026 są eksploracyjne. Nie zmieniono końcowego okresu w prawdziwie nową próbę przez ponowne nazwanie go walk-forward.

## Odtwarzalność i kontrole

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

Causal-prefix checks: 7 instrumentów ×3 punkty czasu, zgodność wcześniejszych wskaźników i propozycji. Kontrole portfela: maks. 2 sloty, rezerwacja ≤0,2%, uzgodnienie PnL, identyczność bazowego replay. Nie testują historycznego margin, rzeczywistego poślizgu, bieżących broker permissions ani pełnej zgodności Risk Managera.

## Chronologia

Oryginalny podział lokalny: przed 31.08 oraz od 31.08 do końca dostępnej historii, z 200 świecami warmup przed segmentem. Nowszy portfel: trzy równe odcinki czasu od 27.04 do 24.10, każdy start z [PRIVATE AMOUNT OMITTED] PLN i bez pozycji. To trzy testy stabilności; wyników różnych hipotez nie sumujemy jako jednej strategii.

## Wspólny portfel — bazowe SL 2 ATR

| Rodzina | Okres | Koszty × | N | Netto | PF | Śr. R | SD R | CI95 R | DD PLN |
|---|---|---|---|---|---|---|---|---|---|
| trend_breakout | 1 | 1 | 65 | -55.843 | 0.903 | -0.013 | 1.321 | [-0.380; 0.380] | 150.607 |
| trend_breakout | 1 | 2 | 64 | 6.257 | 1.011 | -0.066 | 1.303 | [-0.453; 0.338] | 125.112 |
| trend_breakout | 2 | 1 | 81 | -403.142 | 0.520 | -0.275 | 1.162 | [-0.532; -0.004] | 428.702 |
| trend_breakout | 2 | 2 | 73 | -69.250 | 0.895 | -0.097 | 1.257 | [-0.390; 0.209] | 289.579 |
| trend_breakout | 3 | 1 | 80 | -134.203 | 0.831 | -0.166 | 1.246 | [-0.457; 0.167] | 257.948 |
| trend_breakout | 3 | 2 | 73 | -222.217 | 0.728 | -0.229 | 1.180 | [-0.528; 0.075] | 363.074 |
| trend_pullback | 1 | 1 | 71 | -129.508 | 0.763 | -0.289 | 1.175 | [-0.550; -0.031] | 234.842 |
| trend_pullback | 1 | 2 | 58 | -229.222 | 0.529 | -0.379 | 1.097 | [-0.661; -0.084] | 290.635 |
| trend_pullback | 2 | 1 | 98 | 192.531 | 1.219 | -0.037 | 1.279 | [-0.286; 0.250] | 197.831 |
| trend_pullback | 2 | 2 | 85 | 183.022 | 1.243 | -0.112 | 1.275 | [-0.413; 0.213] | 298.171 |
| trend_pullback | 3 | 1 | 86 | -250.117 | 0.689 | -0.109 | 1.274 | [-0.442; 0.233] | 433.985 |
| trend_pullback | 3 | 2 | 73 | -58.503 | 0.922 | 0.025 | 1.297 | [-0.295; 0.327] | 379.100 |
| range_reversion | 1 | 1 | 22 | -136.953 | 0.380 | -0.131 | 1.237 | [-0.604; 0.450] | 161.373 |
| range_reversion | 1 | 2 | 14 | -48.044 | 0.555 | -0.163 | 1.324 | [-0.748; 0.374] | 65.346 |
| range_reversion | 2 | 1 | 28 | 18.338 | 1.069 | -0.057 | 1.281 | [-0.508; 0.408] | 180.422 |
| range_reversion | 2 | 2 | 19 | -15.102 | 0.927 | -0.186 | 1.230 | [-0.698; 0.483] | 147.321 |
| range_reversion | 3 | 1 | 25 | -67.342 | 0.667 | -0.119 | 1.287 | [-0.542; 0.292] | 102.261 |
| range_reversion | 3 | 2 | 15 | -64.712 | 0.565 | -0.260 | 1.373 | [-0.935; 0.344] | 114.461 |

## Wrażliwość SL, bez wyboru zwycięzcy

| Rodzina | SL ATR | Netto okres 1 | Netto okres 2 | Netto okres 3 | Dodatnie 3/3? |
|---|---|---|---|---|---|
| trend_breakout | 1.750 | -97.823 | 91.022 | -265.806 | False |
| trend_breakout | 2 | -55.843 | -403.142 | -134.203 | False |
| trend_breakout | 2.250 | 118.926 | -480.154 | 24.112 | False |
| trend_pullback | 1.750 | -184.710 | 32.572 | 263.158 | False |
| trend_pullback | 2 | -129.508 | 192.531 | -250.117 | False |
| trend_pullback | 2.250 | -122.510 | -8.647 | -239.233 | False |
| range_reversion | 1.750 | -69.841 | -101.854 | -80.851 | False |
| range_reversion | 2 | -136.953 | 18.338 | -67.342 | False |
| range_reversion | 2.250 | -163.686 | -119.759 | 61.717 | False |

Wszystkie 54 komórki wraz z kosztami ×2, liczbą wejść, zmiennością, CI i DD są w `sensitivity.json/csv`; szczegółowe transakcje w `isolated/sensitivity-*.json`. 18 to celowe odtworzenia istniejących przebiegów, 36 to nowe warianty wrażliwości. Zmiana SL zmienia czas zajęcia slotu, liczbę i skład transakcji. Poprawa po większych kosztach może pochodzić z odfiltrowania wejść i zmiany portfela; nie jest dowodem, że większe koszty pomagają.

## Walk-forward z wyborem wyłącznie z wcześniejszych odcinków

Przed okresem 2 wybór z okresu 1; przed okresem 3 z okresów 1+2. Porównano trzy bazowe rodziny, bez optymalizacji SL. Tryb rygorystyczny wymaga dodatniego netto i ≥30 transakcji w każdym wcześniejszym odcinku; inaczej CASH. Dodatkowo pokazano naiwny wybór najwyższego dotychczasowego PnL. Protokół zaprojektowano po obejrzeniu tej historii, dlatego wyniki są symulacją procedury, nie niezależnym OOS.

| Tryb | Koszty × | Test okres | Wybrano | N | Netto | Śr. R | DD PLN |
|---|---|---|---|---|---|---|---|
| strict_gate | 1 | 2 | CASH | 0 | 0 | — | 0 |
| permissive_comparator | 1 | 2 | trend_breakout | 81 | -403.142 | -0.275 | 428.702 |
| strict_gate | 1 | 3 | CASH | 0 | 0 | — | 0 |
| permissive_comparator | 1 | 3 | trend_pullback | 86 | -250.117 | -0.109 | 433.985 |
| strict_gate | 2 | 2 | trend_breakout | 73 | -69.250 | -0.097 | 289.579 |
| permissive_comparator | 2 | 2 | trend_breakout | 73 | -69.250 | -0.097 | 289.579 |
| strict_gate | 2 | 3 | CASH | 0 | 0 | — | 0 |
| permissive_comparator | 2 | 3 | trend_pullback | 73 | -58.503 | 0.025 | 379.100 |

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

## Koszty i niepewność

Zastosowano jawne opłaty i próbkę rzeczywistych spreadów jako kontrolę rzędu wielkości. Brak pełnych historycznych kosztów pozostaje blokadą wiarygodnego wniosku. Stała-ścieżka stress ×1/×2/×3 w `matched_trade_cost_stress.json` utrzymuje liczebność, a pełne portfelowe ×2 pozwala odrzucać wejścia. Oba rodzaje wyników raportujemy oddzielnie.

Bootstrap portfela: 2000 resampli bloków po 5 transakcji; wartości w małych próbach są tylko opisowe. Diagnostyka podgrup: 600 resampli, CI od N≥20. US100/OIL: 30 000 i wrażliwość na blok 3/5/10. Przedziały nie uwzględniają pełnego wielokrotnego testowania, niestacjonarności ani systematycznego błędu modelu wykonania. Końcowy dodatni US100 traci jednoznaczność nawet po korekcie tylko siedmiu rynków.

## Briefing i newsy — wynik weryfikacji

Import JSON, walidacja, autoryzacja treści i eksport raportów istnieją. Dziennik nie potwierdza wykonanej transakcji ze strategii `chatgpt_briefing_v1`. Jedyny zapis źródłowy 23.10 jest ucięty i ma decyzję NO TRADE; `execution_imported=false`. Syntetyczny `exchange/simulation/inbox/morning.json` nie jest rekomendacją historyczną.

News feed RSS działa jako SHADOW_CONTEXT: zachowuje czasy publikacji/pierwszej obserwacji i opis, nie zmienia kierunku ani zgody na wejście. Kalendarz MT5 stanowi odrębną blokadę bieżących nowych wejść; nie ma archiwum do testu kwiecień–październik. WIG20/DAX są w tekście briefingu, ale nie w mapowaniu kontraktów DEMO ani zbiorze siedmiu rynków.

Dodano `briefing_future_template.json` i `briefing_research.py`. Szablon jest celowo niekompletny i nieprzyjmowany przez wykonawcę. W przyszłym archiwum wymagane są published_at, first_seen_at, expiry, kompletność, dokładny broker_symbol, immutable ID, źródło i oryginalne poziomy. Porównanie bierze tylko kontekst otrzymany przed wejściem; wiele aktywnych planów oznacza AMBIGUOUS. Obecny eksport `briefing_comparison.json` ma 338 porównań i 0 kwalifikujących się historycznych kontekstów. Nie udowodniono poprawy dzięki newsom.

## Wniosek

Kontynuować badania metodologii i zbieranie przyszłych danych. Nie promować nowych konfiguracji do działającego DEMO na podstawie tego audytu. Szerszy forward może być etapem badania po usunięciu luk danych/modelu; obecne wyniki nie są podstawą deklaracji rentowności.
