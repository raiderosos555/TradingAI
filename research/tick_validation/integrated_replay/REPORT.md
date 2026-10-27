> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Adapter zintegrowanego replay — uzupełnienie po execution_readiness

**Wykonano brakujący rdzeń chronologicznego adaptera portfela. GO dla kontrolowanych testów tego rdzenia; NO-GO dla historycznego wyniku 22.10 i przewagi inwestycyjnej.** Nie uruchomiono kolejnego poszukiwania strategii. Ta praca uzupełnia wskazany wcześniej brak integracji, potrzebny do żądanego wiarygodnego backtestu.

## Nowy dowód techniczny

`adapter.py` używa zamrożonych SignalEngine, RiskManager, ExecutionEngine i PositionManager z etapu 2. Dwa instrumenty działają we wspólnym wirtualnym rachunku, z jednym dziennikiem, wspólnymi slotami i limitem ryzyka. Trzeci instrument jest blokowany po zajęciu dwóch slotów zamrożonej konfiguracji. Aktywny limit DEMO równy 7 nie został przeniesiony do badań.

Adapter:

- przyjmuje uporządkowany strumień ticków, kalendarza i stanu połączenia; nie naprawia kolejności sortowaniem;
- zachowuje indeksy dostawcy i zerowe kwotowania; dla równoczesnych zdarzeń różnych strumieni wymaga źródłowej kolejności globalnej;
- buduje H1 z Last, publikuje dopiero zamknięte świece i wymaga 200 prawdziwych świec warm-up; nie tworzy świec w pustych godzinach;
- prowadzi osobne czasy Bid/Ask; Last/volume ich nie odświeża; zerowy snapshot unieważnia cenę, bez fallback do cache;
- uruchamia zarządzanie co 10 s i skan co 60 s według jawnego zegara modelu; podczas synchronicznego oczekiwania na fill nadal przetwarza napływające ticki i brokerowe SL/TP;
- wymaga trwałego INTENT zamrożonego ExecutionEngine przed realizacją; późniejsza cena, przekroczony spread, luka i timeout podlegają kontrolom oraz kwarantannie;
- wycenia cały portfel, nalicza jawnie zadane prowizje/opłaty oraz przelicza wynik przez wskazany Bid/Ask FX; brak FX nie staje się zerowym kosztem;
- mierzy wycenę i obsunięcie na zdarzeniach oraz zmianach rachunku. Brak wyceny przy ekspozycji oznacza niepełną ścieżkę i `null` dla pełnego netto/drawdown;
- zachowuje pozycje na końcu próbki; nie dopisuje sztucznego zamknięcia. Raport nieukończonego przebiegu zachowuje faktyczne modelowe fille, lecz nie podaje ich jako pełnego wyniku.

**23 automatyczne testy** obejmują m.in. wspólny rachunek, limit slotów/ryzyka, BUY/SELL, późniejszy fill, TP1/BE/trailing, SL podczas rozłączenia, nieaktualny FX, opłaty, identyczne milisekundy, zerowe ceny, świecę jeszcze niezamkniętą oraz kwarantannę po luce. Dwa ponowne uruchomienia kontrolnego BUY dają identyczny kompletny wynik, łącznie z identyfikatorami i czasami dziennika.

## Porównanie ze starym silnikiem — wyłącznie kontrola syntetyczna

Oba modele otrzymały te same 200 świec poprzedzających i tę samą pełną godzinę kontrolną. Stary silnik otrzymał OHLC Last zgodnie z dotychczasowym, błędnym założeniem Bid; nowy wykorzystał faktyczne strony z kontrolnej taśmy. Kalendarz kontrolny jest odświeżany chronologicznie i pozostaje CLEAR. Parametrów reguł strategii nie strojono.

| Przypadek | Netto starego modelu | Netto nowego modelu | Wejścia stary / nowy |
|---|---:|---:|---:|
| BUY | 16,20 jednostek konta testowego | 12,56 | 1 / 1 |
| SELL | 15,84 jednostek konta testowego | 12,56 | 1 / 1 |

To wynik **wymyślonego kontrolnego rynku**, nie transakcji historycznych GOLD. Różnica łączy bazę cenową, chronologię fillów i zarządzanie; nie jest izolowanym oszacowaniem kosztu spreadu. Pełne poziomy, expectancy R, prowizje oraz drawdown są zapisane w `control-comparison.final.json`. Nie ma podstaw do przenoszenia dodatnich wartości na rzeczywistą strategię.

## Co nadal blokuje dzień 22.10

`historical-preflight.json` potwierdza cztery braki: zaakceptowanego UTC, historycznej polityki kontraktu/kosztów, kalendarza dostępnego wtedy oraz znormalizowanej taśmy UTC z rozstrzygnięciem remisów między strumieniami. Dane raw i FX z poprzednich etapów zachowano. Sprawdzenie źródeł publicznych brokera nie dało wystarczającego dowodu raw→UTC dla tej doby; szczegóły i źródła w `SOURCE_REVIEW.md`.

Adapter ma także jawne granice, które trzeba dopasować do udokumentowanych warunków brokera przed uruchomieniem historii:

- Obsługuje market OPEN/CLOSE i zmianę SL/TP, czyli żądania dwóch zamrożonych lokalnych strategii. Pending i zewnętrzne briefingi nie są częścią tego rdzenia.
- Obecny model marży jest jawnym współczynnikiem na lot; nie jest ogólnym modelem dynamicznej marży brokera.
- Przekroczenie zadeklarowanego rolloveru przy otwartej pozycji przerywa przebieg. Nie zaimplementowano jeszcze naliczeń overnight ani kolejnej doby/baseline.
- Opóźnienie, poślizg, zasada ceny TP i faza cyklu są jawne, ale kontrolne wartości nie są historycznie skalibrowane.
- Wiek od ostatniej zmiany obu stron jest zachowawczym testem świeżości; nie stanowi dowodu, że niezmieniona cena przestała być ważna. Reguła ważności niezmienionych kwotowań wymaga dowodu dostawcy/ciągłości.
- Adapter jest API dla zweryfikowanej taśmy UTC. Nie istnieje jeszcze zaakceptowany zestaw wejściowy pozwalający automatycznie przetworzyć raw 22.10 na wiarygodny pełny replay. `preflight.py` jest audytem braków, nie uniwersalnym certyfikatorem przyszłych danych.

**Decyzja końcowa: GO — rdzeń integracji i kontrolowana porównywalność; NO-GO — historyczny replay 22.10, ocena rentowności i promocja strategii.** Następne prace mają dotyczyć konkretnych brakujących dowodów i dostosowania modelu do potwierdzonych warunków, a nie strojenia strategii. Działającego DEMO, jego zegara, ryzyka i obsługi kwotowań w tym uzupełnieniu nie zmieniono.
