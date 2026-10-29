# OIL: pierwsza rzeczywista sonda historii — 29.10.2026

**Brak hasła inwestorskiego nie blokuje odczytowej sondy. Pierwsze zapytanie
historyczne zakończyło się timeoutem; brak materiału do replay.**

## Korekta wcześniejszego wymagania

Wymóg hasła inwestorskiego był dodatkowym ograniczeniem dodanym przez agenta,
a nie instrukcją właściciela. Zastąpiono go kontrolą rzeczywistego zakresu
operacji skryptu, zachowując osobny proces/dane, właściwy rachunek DEMO,
wyłączone Algo Trading i DLL. Nie zmieniono hasła ani uprawnień rachunku.
Sesji z prawem do handlu nie określamy jako sesji inwestorskiej.
Korektę zapisano w PLAN_AMENDMENT_01.md przed żądaniem historii.

## Wynik

| Kontrola/próba | Rzeczywisty wynik |
|---|---|
| v1 | Brak osobnego procesu; 0 zapytań tickowych |
| v2 | Izolacja poprawna; Algo włączone, prawa do handlu; 0 zapytań |
| v3 | Algo/DLL wyłączone; prawa rachunku nadal aktywne; 0 zapytań |
| v4 | Skorygowana kontrola dostępu PASS; własny warunek Market Watch zatrzymał sondę; 0 zapytań |
| v5 | Kontrole PASS; wysłano copy_ticks_range; timeout procesu klienta |

OIL istnieje, ale nie był wybrany w Market Watch. Usunięto nieudokumentowany
własny warunek wcześniejszego wyboru. Nie wywołano symbol_select. Oficjalny
[opis copy_ticks_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py)
przyjmuje nazwę symbolu; przykład nie wykonuje wcześniejszego wyboru symbolu.
Nie dowodzi to, że brak wyboru nie wpływa na zachowanie tego konkretnego serwera.

Zakres pierwszego żądania: **2026-03-04 15:30:00 do 15:30:01 UTC według
kontraktu API**, COPY_TICKS_ALL. Planowana sekunda oceny jest półotwarta;
ewentualny tick dokładnie na końcu byłby zachowany w raw i wyłączony z oceny.
Historyczne mapowanie czasu feedu brokera pozostaje niezweryfikowane.

Zapis fazy potwierdza przejście kontroli i dojście do wywołania copy_ticks_range.
Proces przekroczył twardy limit **10 s obejmujący także start i kontrolę IPC**;
nie jest to pomiar 10 s samej odpowiedzi serwera. Zatrzymano wyłącznie proces
klienta sondy. Nie zatrzymywano żadnego terminala ani kolektora.
**1 żądanie historyczne, 0 ukończonych odpowiedzi, 0 zwalidowanych ticków.**
Pozostałych 11 dat nie odpytywano. Nie wykonano ponowienia po timeout.

Dziennik terminala badawczego w odczycie 08:38:06 UTC nie zawierał dowodu
ukończenia pobrania tej sekundy. Znaleziono 3 pliki cache ticków; sama ich
obecność nie dowodzi pokrycia żądanej daty. Terminal może kontynuować
synchronizację w tle. Nie ustalono, czy przyczyną jest cold cache, wybór
symbolu, opóźnienie serwera czy brak historii. Nie deklarujemy braku danych.

## Walidacja i decyzja

9 testów PASS, w tym kontrola dozwolonych wywołań API, odmowa dla LIVE,
niewłaściwej tożsamości/ścieżki, włączonego Algo lub DLL. Testy kodu nie
zastępują sprzętowej/serwerowej blokady transakcji innych programów.
27 chronionych plików projektu bez zmian. Kolektor: COLLECTING,
status 08:38:06 UTC, konfiguracja zgodna z zamrożoną.

- **GO:** izolowana, ograniczona sonda odczytowa bez zmiany aktywnego DEMO.
- **NO-GO:** odebrany pakiet EIA/OIL i pełny replay — brak potwierdzonych ticków,
  osi UTC, first-availability EIA, historycznych kosztów i konsensusu.
- Nie testowano rentowności; brak potwierdzonej przewagi.

Najmniejszy kolejny krok: ustalić dostępność archiwum OIL z marca 2026
w terminalu badawczym lub dokumentacji/odpowiedzi brokera, zanim ponowimy API.
Nie wydłużamy samoczynnie limitu ani nie pobieramy pełnych okien. Nie wysłano
wiadomości do brokera. Niezależne dane EIA są zachowane, ale nie są jeszcze
certyfikowanymi pierwszymi publikacjami. Duża kampania i push nie wykonane.
