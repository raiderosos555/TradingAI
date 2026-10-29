# OIL: dostęp historyczny potwierdzony punktowo — 29.10.2026

**GO dla dostępności 12 małych próbek; NO-GO dla pełnego replay newsowego i potwierdzenia przewagi.**

Ten wynik zastępuje wniosek o niedokończonym odczycie z TICK_PROBE_RESULT.md. Nie zmienia danych poprzedniej próby.

## Powód jednej ponownej próby

Po timeoutcie v5 pojawiły się cache OIL marzec–październik 2026: 8 plików, 214 794 095 B (204,84 MiB). Plik marca został zapisany o 08:39:28 UTC, już po poprzedniej kontroli. To nowy dowód uzasadniający v6 z identycznym limitem 10 s i tymi samymi datami. Nie wywoływano dodatkowego pobrania miesięcy: synchronizację kontynuował MT5 po zakończeniu jednosekundowego żądania. Rozmiar cache nie jest pomiarem transferu sieciowego. Wcześniejszy limit procesu i limit zwracanych rekordów nie ograniczają wewnętrznego transferu terminala.

## Niezależna kontrola zapisanych odpowiedzi

12/12 odpowiedzi API Success; 285 rekordów, 65920 bajtów prywatnych plików JSON z metadanymi. Sprawdzono SHA256, komplet ustalonych dat, zakresy, nieujemną kolejność czasu, dodatnie i niekrzyżujące się Bid/Ask oraz liczby flag. W badanych sąsiednich rekordach nie ma zmiany ceny Bid/Ask bez odpowiadającej flagi.

| Data | Ticki | Bid update | Ask update | Last bez Bid/Ask update | Spread min–max w jednostkach ceny |
|---|---:|---:|---:|---:|---:|
| 2026-03-04 | 32 | 11 | 11 | 21 | 0.040–0.040 |
| 2026-03-11 | 32 | 12 | 11 | 20 | 0.040–0.040 |
| 2026-03-18 | 33 | 10 | 9 | 23 | 0.040–0.040 |
| 2026-03-25 | 38 | 9 | 8 | 29 | 0.040–0.040 |
| 2026-04-01 | 27 | 8 | 7 | 19 | 0.040–0.060 |
| 2026-04-08 | 21 | 7 | 6 | 14 | 0.040–0.040 |
| 2026-04-15 | 14 | 4 | 3 | 10 | 0.040–0.040 |
| 2026-04-22 | 21 | 6 | 5 | 15 | 0.040–0.040 |
| 2026-04-29 | 17 | 4 | 4 | 13 | 0.040–0.040 |
| 2026-05-06 | 11 | 3 | 2 | 8 | 0.040–0.040 |
| 2026-05-13 | 12 | 3 | 2 | 9 | 0.040–0.040 |
| 2026-05-20 | 27 | 3 | 2 | 24 | 0.040–0.040 |

205/285 rekordów ma zmianę Last bez flag zmiany Bid/Ask. Last ani czas ostatniego ticka nie dowodzą aktualizacji obu stron. Zachowano kolejność API i wielokrotne rekordy o tej samej milisekundzie; nie deduplikowano ich po timestampie. Czas w ms nie ujawnia rzeczywistego porządku wewnątrz jednej milisekundy.

Każda próbka obejmuje tylko jedną sekundę surowej osi API. Wiersze przed pierwszą zaobserwowaną aktualizacją obu stron nie otrzymują sztucznego czasu odświeżenia. Nawet obserwacja obu flag nie potwierdza pełnej wykonalności ani latencji brokera. Brak ticka w części sekundy nie jest automatycznie luką transferu — może oznaczać brak zdarzenia. Nie dowiedziono kompletności dłuższych okien.

## Ograniczenia, które nadal blokują wynik strategii

- Dokumentacja Python opisuje UTC, lecz wcześniejsze dowody na tym rachunku wskazywały przesunięcia czasu. Nie wolno przenieść obecnego offsetu na marzec–maj ani ustalać go przez dopasowanie skoku ceny do EIA.
- Próbki pobrano przy planowych etykietach czasu publikacji; nie nazywamy ich potwierdzonymi cenami w chwili EIA.
- Archiwalne tabele EIA nie mają zweryfikowanego first-print/published_at; historyczny konsensus nie został pozyskany.
- Brak pełnych okien, historycznych specyfikacji/kosztów i modelu poślizgu. Spread tej sekundy nie jest kosztem całej transakcji.
- Nie liczono markoutów, P&L, R ani rentowności. 12 wydarzeń to odbiór danych, nie niezależny dowód edge.

## Jeden następny krok

Uzgodnić semantykę historycznych timestampów Python MT5 dla feedu TMS i pierwszą dostępność wydań EIA przed dopasowaniem cen do wydarzeń. Nie rozpoczynać dużego eksportu na podstawie samego sukcesu API. Gotowy zakres pytań do brokera w UTC_EVIDENCE_REQUEST.md; nie wysłano wiadomości. Większe okna wymagają odrębnej zgody oraz uwzględnienia faktu, że MT5 może synchronizować znacznie więcej danych niż zwraca.

Aktywny DEMO, strategie, Risk Manager, LIVE i kwarantanna pozostają bez zmian. Dalszy forward musi być oddzielony od danych obejrzanych przy odbiorze. Ta runda jest postępem w dostępności danych, nie potwierdzeniem rentowności.
