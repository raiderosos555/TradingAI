> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Last, Bid/Ask i minimalna propozycja poprawki

**Potwierdzono objaw, nie pełną przyczynę po stronie dostawcy.** W audycie etapu 11 zerowe Bid/Ask wystąpiły 5 razy na 21 odczytów: US500 3, US100 1, OIL 1. Wszystkie miały `flags=24` (Last/volume). Znacznik całego ticka był świeży; nie był dowodem świeżego Bid/Ask.

Nowy eksperyment: 12 sparowanych odczytów na każdy z US500/US100/OIL. OIL odtworzył problem raz. `symbol_info_tick()` przed i po odczycie historii oraz `symbol_info()` zwróciły zera. Zamiana wyłącznie funkcji odczytu nie rozwiązuje problemu. W tej krótkiej próbie US500/US100 nie powtórzyły objawu; nie unieważnia to wcześniejszego dowodu.

`observations.json` przechowuje pełne próbki i 15-sekundowe wycinki historii. `analysis.json` wyodrębnia ostatnie zaobserwowane zdarzenia Bid (flaga 2), Ask (4), Last (8), volume (16) i ich osobne czasy. Okno historii może kończyć się wcześniej niż milisekundowy snapshot; nie udowodniono ciągłości aż do chwili odczytu. Żadnej poprzedniej ceny z tego okna nie uznano za wykonywalną.

Dokumentacja rozróżnia COPY_TICKS_INFO i COPY_TICKS_TRADE: [MQL5 Python copy_ticks_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py). Nie oznacza to, że broker gwarantuje ważność wcześniejszej ceny w obserwowanym przypadku zer.

## Propozycja do przeglądu — niewdrożona

Plik `quote_proposal.py` jest izolowanym prototypem bez zależności MT5 i bez możliwości wysyłania zleceń.

1. Przechowywać osobno cenę i czas aktualizacji obu stron. Last/volume nie odświeża wieku Bid ani Ask.
2. Zerowy snapshot zeruje zaufanie do poprzednich stron; nie wykonuje się fallback do cache.
3. Po zerze dopuścić najwyżej trzy dodatkowe odczyty. Funkcja `recover_fresh_pair` przyjmuje wyłącznie dodatni, niekrzyżujący się Bid/Ask z **późniejszego** zdarzenia aktualizacji obu stron (`flags & 6 == 6`), o wieku do 10 s. Ten sam czas bez numeru sekwencji nie wystarcza.
4. Brak takiego zdarzenia oznacza dalszą blokadę; bez pętli oczekiwania zatrzymującej cały silnik. Wersja produkcyjna potrzebuje również ograniczenia czasu wywołania API, logowania odczytów i osobnych kodów przyczyn.
5. Odzyskany snapshot przechodzi ponownie zwykły Risk Manager, w tym UTC, spread, SL/TP, wolumen, limity i autoryzację. Prototyp sam nie autoryzuje niczego.

Rozwiązanie jest celowo zachowawcze: może nadal odrzucać poprawne, niezmienione kwotowanie. Ciągła ważność niezmienionej ceny wymaga dodatkowego dowodu heartbeat/ciągłości; same flagi zmian tego nie dowodzą. W historycznym streamie identyczne milisekundy rozstrzyga oryginalny indeks dostawcy, nigdy dowolne przestawienie.

**Wdrożenie do aktywnego DEMO wymaga odrębnego zatwierdzenia użytkownika. Nie wdrożono tej poprawki.** Zmiana limitu liczby pozycji jest osobną, już autoryzowaną zmianą.
