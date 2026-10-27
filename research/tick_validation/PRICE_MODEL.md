> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Last, Bid, Ask i czas — etap 1

Etap 1, raport 2026-10-25T07:50:23.638758+00:00. Wyłącznie badanie danych, cen i czasu. Brak zleceń, zmian produkcyjnych, strojenia strategii i pełnego ponownego backtestu. Wszystkie dane historyczne są eksploracyjne.

## Model sygnału i wykonania

`model.py` jest izolowanym modułem badawczym bez importu MetaTrader5 i bez mechanizmu wysyłania zleceń. Last służy do potencjalnego budowania świec sygnałowych. Domyślna agregacja Last uwzględnia tylko ticki z flagą aktualizacji Last (bit 8), aby przeniesiona wartość Last na ticku samego Bid/Ask nie tworzyła sztucznego nowego sygnału. Brak Last daje brak świecy, a nie zastępcze Bid.

| Operacja | Cena dostępna na ticku |
|---|---|
| Otwarcie BUY | Ask |
| Zamknięcie BUY / kontrola SL i TP | Bid |
| Otwarcie SELL | Bid |
| Zamknięcie SELL / kontrola SL i TP | Ask |

`first_executable_quote` wymaga ticku późniejszego niż moment decyzji o jawną dodatnią latencję (domyślny parametr testowy 1 ms, nie zmierzony poślizg). Nie przeskakuje szerokiego spreadu w poszukiwaniu korzystniejszej ceny. Luka przekraczająca limit oczekiwania blokuje wykonanie. Cena jest dostępnym kwotowaniem, nie gwarancją pełnej realizacji wolumenu; płynność, slippage i opóźnienia wymagają osobnego modelu.

| Rynek | Last w pierwszym rekordzie | Bid | Ask | Błąd OHLC Last z aktualizacji | Błąd OHLC Bid |
|---|---|---|---|---|---|
| EURPLN | 4.37 | 4.3698 | 4.3702 | 0 | 0.0003 |
| EURUSD | 1.12053 | 1.12052 | 1.12053 | 0 | 2e-05 |
| GBPUSD | 1.33736 | 1.33734 | 1.33737 | 0 | 3e-05 |
| GOLD | 4088.1 | 4087.8 | 4088.27 | 0 | 0.3 |
| OIL | 99.7 | 99.68 | 99.72 | 0 | 0.02 |
| US100 | 29497 | 29496.4 | 29497.5 | 0 | 0.6 |
| US500 | 7725.2 | 7724.8 | 7725.5 | 0 | 0.4 |

We wszystkich siedmiu przypadkach Last z flagowanych aktualizacji odtwarza oryginalny OHLC dokładnie. Bid nie jest tym samym szeregiem. Użycie właściwej strony ceny zostało sprawdzone na rzeczywistych rekordach, a nie tylko na przykładach syntetycznych.

## Koszty i kontrakty

Spread wynika bezpośrednio z Bid/Ask i nie jest ponownie odejmowany jako osobna opłata. `cash_result` wymaga jawnych danych FX/cash factor, prowizji i swapu; None lub NaN blokuje PnL. Funkcja pozwala wyraźnie podać zero, ale nie dowodzi historycznej prawdziwości tej wartości. `validate_contract` sprawdza okres ważności specyfikacji, identyfikator dowodu, siatkę wolumenu, minimum/maksimum i siatkę cen. Bieżący snapshot kontraktu nie został automatycznie uznany za historyczny.

Nie policzono historycznego netto, ponieważ kompletność kosztów, kontraktów i wykonania nie została potwierdzona. Przyszła warstwa musi dodatkowo sprawdzić stops/freeze, prawa handlu, margin, częściowe realizacje i historyczną taryfę. Walidator siatki cen nie zastępuje pełnego Risk Managera.

## Mapowanie czasu

Nie ma domyślnego odjęcia 7200 ani 3600 s. `to_utc` wymaga dokładnie jednego zweryfikowanego segmentu czasowego z identyfikatorem dowodu. Poza zakresem, przy nieznanym offsetcie lub niejednoznaczności jesiennej zmiany czasu odmawia mapowania. Surowa kolejność umożliwia weryfikację cen, ale nie wystarcza do limitu dziennego UTC ani dopasowania publikacji makro.

Pięć istniejących dealów z 23.10 daje różnicę surowego czasu brokera do czasu UTC zapisu zamiaru od 7200.110274 do 7200.126528 s. Wspiera to +7200 s w tych obserwacjach (z latencją około 0,11–0,13 s); nie wyznacza całego historycznego harmonogramu.

Zapis EA z 24.10 wskazuje server−GMT=7200 s, świeże eksporty z 25.10 wskazują 3600 s. Windows raportuje synchronizację SNTP; surowy wynik kontroli zapisano w `evidence/clock-*.json`. Potwierdza to zmianę relacji zegarów, lecz nie dokładną chwilę przestawienia ani kodowanie nowych ticków po DST. W niedzielę brak świeżych notowań nie pozwala potwierdzić tego ostatniego.

Dokumentacja Python MT5 opisuje znaczniki jako UTC, co wymaga uzgodnienia z zaobserwowaną rozbieżnością na tym rachunku. EA TimeGMT zależy od zegara i ustawień komputera, więc nie jest niezależnym źródłem czasu. [API ticków](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py), [TimeGMT](https://www.mql5.com/en/docs/dateandtime/timegmt).

Nie przypisano brokerowi strefy Europe/Warsaw. Testy tej strefy sprawdzają wyłącznie mechanikę 23/25-godzinnego D1, 3/5-godzinnego H4 przecinającego zmianę czasu, nieistniejącą i powtórzoną godzinę H1 oraz przedziały [open, close). Bez dowodu polityki sesyjnej takie granice nie mogą zostać użyte do produkcyjnej historii brokera. Działającego DEMO nie modyfikowano.
