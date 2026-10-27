> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Etap 6 — chronologia świec i opóźnione kandydatury ceny

Badanie offline, 25.10.2026. Użyto zachowanej doby EURUSD: **277 031 ticków**. Nie pobierano nowych danych ani nie uruchamiano pełnego backtestu. Kod produkcyjny, parametry strategii i stan DEMO pozostają niezmienione.

## Chronologia

`Timeline` przetwarza ticki po kolei. Świece techniczne powstają z aktualizacji Last, a aktualny Bid/Ask jest osobnym kwotowaniem. Tick dokładnie na granicy należy do nowej świecy. Świeca poprzednia jest publikowana dopiero po osiągnięciu jej końca przez zegar odtwarzania. Rekordy o tej samej milisekundzie zachowują kolejność dostawcy. Nie ma sortowania cofniętych danych, kopiowania poprzedniego zamknięcia w miejsce pustej świecy ani wykorzystywania przyszłych ticków.

Na rzeczywistej dobie uzyskano te same **24 H1, 6 H4 i 1 D1**, co w agregacji offline i źródłowych świecach brokera, wraz z dokładnym tick_volume. Ostatnie trzy świece (H1/H4/D1) zamknięto jawnym zdarzeniem zegara na końcu pobranego przedziału. To zdarzenie nie tworzy nowego ticku ani ceny realizacji; ostatni kwotowany czas pozostaje bez zmian. Stare kwotowanie może zostać odrzucone przez limit wieku.

Test wykorzystujący niezmieniony, zamrożony SignalEngine na jawnych syntetycznych świecach H1 wykazał, że skrajna aktualizacja Last świecy jeszcze otwartej nie zmienia analizy świec zamkniętych. Nie jest to historyczny test sygnałów ani rentowności. Snapshoty zwracane odbiorcom są kopiami, więc późniejsze aktualizacje nie zmieniają wcześniejszych wyników.

## Czas jako jawna bramka

Adapter `utc_market` wymaga jednoznacznych, zweryfikowanych segmentów mapowania czasu. Dla rzeczywistej doby EURUSD lista jest nadal pusta — adapter odmawia przekazania jej strategii jako danych UTC. W testach użyto wyłącznie oznaczonych mapowań syntetycznych.

Wykryto dodatkowy warunek zgodności: zamrożony analizator interpretuje długości H1/H4/D1 jako stałe. Adapter odrzuca mapowanie, które dałoby inną długość UTC, np. 23-godzinną D1 przy DST. Nie wolno bez osobnego rozwiązania przekazać takiej świecy i twierdzić, że analizator prawidłowo rozpoznaje moment jej zamknięcia. Nie zmieniano produkcyjnej logiki czasu.

## Cena późniejsza niż decyzja

`QuoteQueue` przyjmuje identyfikator zamiaru, BUY/SELL, OPEN/CLOSE, czas decyzji, jawne dodatnie opóźnienie, maksymalne oczekiwanie i limit spreadu. Wybiera pierwszy kwalifikujący się tick. Tick decyzji i inne ticki z tą samą milisekundą nie mogą wykonać zamiaru przy wymaganym dodatnim opóźnieniu. Zbyt szeroki spread odrzuca kandydaturę; kolejka nie czeka na korzystniejszą cenę. Brak ticku w oknie kończy się EXPIRED_NO_QUOTE.

**Wyjściem jest QUOTE_CANDIDATE, nie zlecenie ani fill.** Wszystkie wyniki mają `orders_authorized=false`. Kolejka nie zastępuje Risk Managera, kontraktu, brokerowego order_check ani rozliczenia kosztów. Pełne połączenie z tymi elementami pozostaje do wykonania. Dodatnie opóźnienia testów są parametrami przypadków kontrolowanych; nie zostały skalibrowane na rynku ani dobrane pod PnL.

## Walidacja i odtwarzanie

**18 testów automatycznych** obejmuje niewidoczność świecy otwartej, granice, Last, duplikaty, brak danych, niezmienność snapshotów, zegar i DST, zamrożony SignalEngine oraz kolejkę opóźnionej ceny. `result.json` zawiera także 31 rzeczywistych zdarzeń publikacji świec i porównanie ze źródłami.

```powershell
.\.venv\Scripts\python.exe research\tick_validation\stage6\run.py
```

`run.py` sprawdza hashe wcześniejszych etapów i chronionych plików produkcyjnych. `manifest.json` utrwala źródła, wyniki i dokumentację tego etapu. Nie utworzono nowych sygnałów historycznej strategii ani metryk PF/expectancy/drawdown. Wszystkie dotychczasowe dane pozostają eksploracyjne.
