# Czas i kontekst EIA: wynik kontroli 29.10.2026

## Co zmienia następny krok badania

**Historyczne próbki ticków są dostępne (12/12), ale sam kalendarz MT5 nie
dostarczył actual dla badanego wydarzenia EIA. Oficjalny bieżący plik EIA
zawiera tę wartość. Do przyszłej walidacji potrzebny jest bezpośredni zapis
tego źródła z rzeczywistym czasem odbioru, niezależnie od kalendarza.**

Nie wykonano badania wyników strategii, selekcji po P&L ani optymalizacji.
Nie zmieniono źródeł ani kodu działającego kolektora lub DEMO.

## Czas: dowód z istniejącej archiwizacji

Sprawdzono 27 snapshotów kwotowań z trzech zapieczętowanych batchy kolektora
z 29.10, około 17:53–17:56 UTC. Hash każdego źródła zgadza się z manifestem.
Użyto wyłącznie timestampów i granic odczytu; nie analizowano zwrotów cen.

- Surowy czas ticka minus czas odbioru hosta: od 3595,5535 do 3600,2047 s.
- Najszerszy przedział przed/po wywołaniu API: 1,0031 ms.
- Bezpośrednia kontrola NTP o 17:57:24–28 UTC: offset 0,2086–0,2114 s.
- `trading_ai.models.utcnow()` i `forward_validation.worker.now()` używają
  świadomie UTC (`datetime.now(timezone.utc)`). Journal zapisuje ten timestamp;
  worker zapisuje surowe `time_msc` bez korekty przed porównaniem.

W sprawdzonej ścieżce nie znaleziono błędu oznaczenia lokalnego czasu jako UTC.
Obserwacje wspierają surową oś brokera około UTC+3600 w tych punktach,
z różnicami wynikającymi m.in. z wieku ticka. Nie certyfikują dokładnej latencji,
całej doby ani historycznej polityki DST. Nie uzupełniono historycznych
segmentów UTC i nie zmieniono normalizacji czasu DEMO.

NTP jest bieżącą obserwacją, nie retrospektywnym certyfikatem zegara z marca.
Dokumentacja [Python MT5](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py)
opisuje UTC, więc rozbieżność na tym feedzie nadal wymaga wyjaśnienia przed
automatycznym łączeniem historycznych ticków z wydarzeniami.

## Dostępność EIA w zebranym forward

Skrypt `inspect_eia_receipts.py` otworzył archiwum SQLite wyłącznie mode=ro.
Zakres ustalony do kontroli: 28.10 14:20 UTC – 29.10 17:00 UTC.
Sprawdzono hashe 317 wersji kalendarza; 287 zawierało ten sam identyfikator
publikacji EIA Crude Oil Stocks Change, a w 30 wydarzenia już nie było.

We wszystkich 287 wersjach **actual=null**. Ostatni zapis zawierający
wydarzenie otrzymano 29.10 o 14:28:23 UTC. Przed planową publikacją istniał
zapis `forecast=-2.067`, `previous=-3.06`; forecast nie jest automatycznie
ankietowym konsensusem. Nie liczono z niego surprise ani wyniku strategii.

To dowód brakującego actual w naszym archiwum, a nie rozpoznana przyczyna
awarii dostawcy. Nie przesądza, czy winny jest feed, aktualizacja terminala
czy eksport. Nie wolno wstawić dzisiaj pozyskanej wartości wczorajszym
decyzjom i twierdzić, że była wtedy dostępna dla TradingAI.

## Mały test oficjalnego źródła

Datowany adres archiwum dla 28.10 zwrócił 404; zachowano także tę niekorzystną
odpowiedź (46 363 B). Sprawdzono [główną stronę WPSR](https://www.eia.gov/petroleum/supply/weekly/),
która kieruje bieżące dane do osobnej domeny `ir.eia.gov`.
404 archiwum nie oznacza braku opublikowanego raportu.

[Bieżąca table1.csv](https://ir.eia.gov/wpsr/table1.csv) dała HTTP200,
6599 B. Nagłówek potwierdza tydzień 23.10 i poprzedni tydzień 16.10.
[Oficjalne metadane JSON](https://ir.eia.gov/wpsr/psw00.json) odczytane w
przeglądarce źródeł wskazują release_date=2026-10-28, release_time=10:30 am.
Nie pobierano lokalnie wieloletniego szeregu z JSON.

| Zmiana zapasów, mln baryłek | Wartość w bieżącej tabeli |
|---|---:|
| Ropa komercyjna bez SPR | -1,892 |
| Benzyna | +3,870 |
| Destylaty | -1,462 |

Arytmetyka trzech wierszy PASS. Odpowiedź tabeli otrzymano **nie później niż
29.10.2026 18:02:42,132 UTC**; zapisano URL, SHA256, treść i ograniczenie czasu
odbioru. Nie jest to dowód pierwszego globalnego opublikowania ani niezmienności
od 28.10. Bieżący endpoint może zmieniać treść; archiwizacja musi zachowywać
każdą pobraną wersję i nigdy nie nadpisywać pliku poprzedniego wydania.

## Decyzja i minimalne odblokowanie

| Warunek | Decyzja |
|---|---|
| Punktowa dostępność starych ticków | GO, wynik wcześniejszej v6 |
| Bieżący oficjalny endpoint EIA i parser | GO, mała rzeczywista odpowiedź |
| Kalendarz MT5 jako jedyne źródło actual EIA | NO-GO dla sprawdzonego wydarzenia |
| Historyczne łączenie EIA i ticków po UTC | NO-GO, mapowanie nadal niezweryfikowane |
| Test rentowności / potwierdzenie edge | NO-GO, nie ma kompletnych danych wykonania i próby |

Następny minimalny krok ma konkretny sens badawczy: **zapisywać przyszłe
bieżące wydania bezpośrednio z table1.csv, z czasem odbioru, obok istniejącego
forward**. Decyzja eksperymentu może nastąpić dopiero po tym odbiorze, przy
potwierdzonym czasie kwotowań; brak odczytu oznacza brak zdarzenia do wykonania.
Nie potrzebujemy nowej architektury ani modelu sentymentu. Nie uruchomiono
nowego harmonogramu ani nie zmieniono zamrożonego cohortu w tej kontroli.
Reguły, opóźnienie i okres przyszłej próby należy utrwalić przed reakcjami cen.
Weryfikacja mechanizmu po kosztach wymaga później większej niezależnej próby;
nie wolno zastąpić jej samym poprawnym pobraniem pliku.
