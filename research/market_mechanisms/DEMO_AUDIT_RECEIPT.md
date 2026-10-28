# Odbiór audytu okna 27.10 — bez ponownego audytu

Pierwotny proces zakończył zapis raportu o 2026-10-27T18:37:29.466958+00:00. PID 11896 nie występował
podczas odbioru; nie uruchamiano następnego audytu. Dowody źródłowe zachowano.

Okno 09:00–17:00 Europe/Warsaw: 1 600 232 rekordy tickowe, 0 błędów hashy
wybranych paczek, 0 nieudanych pobrań w oknie. Żądane zakresy pokryte przy
kandydackim offsecie. Globalnie 11 niezgodności powtórnego pobrania nakładających
się ticków (provider revised overlap); to nie jest 11 uszkodzonych plików.
Nie oznacza to kompletnego feedu: cisza wymaga kontekstu sesji, a offset nie jest
zaakceptowaną historyczną mapą UTC. 95 obserwacji zegara hosta nie certyfikuje
czasu brokera. Nie policzono wyników strategii na forward.

Kontekst: 97 wersji kalendarza, 33 wersje newsów, 2751 runtime, 1 config.
Maksymalne przerwy obserwacji około 30,5 s, poprzednia obserwacja przed oknem
zachowana. **Nie dowodzi to, że każda decyzja silnika użyła dokładnie tej wersji.**

Odczyt brokera: 2026-10-28T12:23:52.123336+00:00. Terminal połączony, LIVE wyłączone, jedna otwarta
pozycja z brokerowym SL/TP, silnik WAITING, jedna operacja UNCERTAIN, kolektor
COLLECTING. Siedem kwotowań poprawnych w tym pojedynczym odczycie przy bieżącym
kandydackim offsecie; nie jest to dowód ciągłej aktualności.

Operacje okna powiązane po identyfikatorze deal z historią brokera: 2;
zgodne symbol/kierunek/cena/wolumen: 2. Operacje bez deal: 52;
historia deals nie potwierdza kolejnych historycznych zmian SL/TP. Również
wykonana operacja UNCERTAIN pozostaje w kwarantannie. Nie zmieniono jej statusu,
nie ponowiono zlecenia i nie uznano dopasowania deal za naprawę kontroli TP.

| Obszar | Decyzja | Przyczyna |
|---|---|---|
| Odporność DEMO | NO-GO | Recovery v2 niewdrożone; kwarantanna przerywa zarządzanie BE/trailing. Brokerowe SL/TP nie zastępują managera |
| Kompletność danych | NO-GO do certyfikacji | Pokrycie żądań warunkowe; UTC, rewizje feedu i luki niezaakceptowane |
| Pełny historyczny backtest | NO-GO | Brak potwierdzenia zgodności historycznej ceny i ceny decyzji, kolejności między strumieniami, kosztów i dokładnego kontekstu |

Automatyzacja tradingai-audyt-okna-27-10 usunięta po jednorazowym odbiorze.
Nie zmieniono zadań Windows, aktywnego DEMO ani kolektora. Brak deklaracji edge.
