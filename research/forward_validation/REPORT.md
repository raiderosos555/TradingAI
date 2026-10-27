> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Przyszła walidacja TradingAI — uruchomienie zbierania danych

Stan dowodów: 2026-10-26T18:19:28.502542+00:00. Raport dotyczy uruchomienia rejestratora, nie wyniku strategii.

**GO: pasywne zbieranie przyszłych danych. NO-GO: twierdzenie o przewadze lub pełnej zgodności replay z DEMO.**

## Co rzeczywiście działa

- Zadanie Windows `TradingAI-Forward-Evidence` działa lokalnie, bez modelu i bez API wysyłania zleceń.
- Dane: `C:\TradingAI\state\forward_validation\cohort-20261026-v1`.
- Surowe Bid/Ask/Last, wolumeny, flagi oraz kolejność odpowiedzi MT5: 7 instrumentów i 2 strumienie FX.
- Na moment audytu **45841 ticków**, **135 zgodnych nakładek**, **0 błędów integralności**. Ticki powtórzone w nakładkach nie są ponownie liczone; identyczne ticki wewnątrz odpowiedzi pozostają zachowane.
- Pierwszy pełny odczyt: po 220 zamkniętych H1, H4 i D1 dla wszystkich 7 instrumentów. Surowe historyczne znaczniki nie zostały uznane za zweryfikowane UTC.
- Specyfikacje kontraktów i bieżące kalkulacje profit/margin, pozycje, zlecenia i historia transakcji brokera są zapisywane w paczkach. Wykonania zawierają cenę, wolumen, commission, fee, swap i profit.
- Zachowane wersje kalendarza: **4**, newsów: **2**. Pełne bajty JSON, pierwsze otrzymanie i błędy odczytu są przechowywane osobno. Nie przypisujemy nowej wersji do wcześniejszej decyzji.
- Dziennik: **773** zaobserwowanych nowych zdarzeń; wersje operacji, sygnałów i ustawień zapisane niezależnie. Pierwszy zrzut wcześniejszego stanu nie staje się nową próbą forward.
- 13 testów rejestratora/weryfikacji i 13 testów archiwum kontekstu przeszło. Kontrolowany restart wyłącznie rejestratora odtworzył kursory; nakładki po wznowieniu są sprawdzane jak pozostałe. Dane dzisiejsze są rozruchem i kalibracją.

| Strumień | Ticki w rozłącznych odcinkach | Nakładki zgodne | Niewykonywalne Bid/Ask |
|---|---:|---:|---:|
| EURPLN.pro | 2452 | 15 | 0 |
| EURUSD.pro | 1840 | 15 | 0 |
| GBPUSD.pro | 4802 | 15 | 0 |
| GOLD.pro | 4972 | 15 | 0 |
| OILWTI.pro | 3196 | 15 | 0 |
| US100.pro | 16528 | 15 | 0 |
| US500.pro | 6496 | 15 | 0 |
| USDPLN | 2573 | 15 | 0 |
| USDPLN.pro | 2982 | 15 | 0 |

## Czas i luki

Ocena całego dotychczasowego odcinka: `INSUFFICIENT_CORROBORATION`. Początkowo dwa odrębne eksporty kalendarza, równoczesne odczyty czasu ticków i raport NTP Windows potwierdzały offset +3600 s, przy oszacowanej niepewności zegara około 1,55 s. Po przerwie sieciowej raport NTP dał oszacowanie około 8,16 s, powyżej zadeklarowanego progu 2 s, więc pełen odcinek nie został zaakceptowany. Trzy niezależne odczyty NTP o 18:20:21–23 UTC pokazały odchylenie około 0,160–0,164 s i RTT 0,037–0,041 s (`ntp-direct-probe.txt`); nie dowodzą one jakości czasu w trakcie wcześniejszej przerwy. Nie zmieniano zegara Windows ani konfiguracji czasu DEMO. Surowe ticki pozostają niezmienione.

Nie rozszerzamy tego ustalenia na 22.10, historyczny DST ani czas poza obserwowanym zakresem. Przed replay potrzebna jest mapa segmentów czasu dla wybranego odcinka i jawne potraktowanie decyzji przy granicach niepewności czasowej. Raport `verification.final.json` przechowuje dokładny zakres i dowody.

Każda kolejna paczka sprawdza dokładną zgodność 2 sekund poprzedniego odcinka, łącznie z kolejnością i powtórzeniami. Wykrywamy cofnięcie czasu, brak ciągłości zakresów, puste odcinki, zmienione nakładki, zerowe/crossed Bid/Ask, ciszę pomiędzy tickami i skoki zegara hosta. **Cisza nie oznacza automatycznie zgubionych ticków ani kompletności feedu**; trzeba zestawić ją z sesją instrumentu. Nie odtwarzamy cen sztucznie.

## Zamrożony zakres przyszłego pomiaru

Protokół zapisano 2026-10-26T18:01:17.451682+00:00, przed wynikami wybranego okna. Pierwsze okno: **27.10.2026 08:00–16:00 UTC, czyli 09:00–17:00 Europe/Warsaw**. Wszystkie 7 instrumentów i obie istniejące strategie lokalne, bez zmiany parametrów. Limit 7 pozycji odzwierciedla wcześniej zatwierdzony stan DEMO; porównanie nie może po cichu użyć starszej konfiguracji z limitem 2.

Kolejne dni robocze w tych samych godzinach są rejestrowane także wtedy, gdy nie było transakcji lub dane okażą się niewystarczające. Nie zastępujemy słabego dnia lepszym. Jedna doba służy sprawdzeniu odtwarzania, nie wykazaniu przewagi. Protokół przewiduje pierwszy wniosek statystyczny dopiero po co najmniej 60 sesjach i 100 zamkniętych transakcjach; te progi nie gwarantują mocy statystycznej. Bieżąca autoryzacja handlu DEMO nadal kończy się 30.10; rejestrator jej nie przedłuża.

## Co pozostaje przed pierwszym wiarygodnym replay

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

To konkretne ograniczenia pierwszego porównania; nie rozpoczynamy kolejnego szerokiego strojenia ani badań parametrów. Automatyczny `readiness.json` jest bramką danych, **nie automatycznym uruchomieniem ani certyfikatem poprawnego backtestu**. Pełne porównanie cen, kosztów, zarządzania i P&L pozostaje oczekujące; wartości nie są zastępowane zerami.

## DEMO i oddzielny monitoring

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

### Dwa rzeczywiste problemy ujawnione w trakcie rejestracji

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

**Rozłączenie:** log terminala pokazuje utratę połączenia o 19:13:44 czasu lokalnego (18:13:44 UTC), ponowną autoryzację 19:15:49 i synchronizację 19:15:59. Rejestrator zachował nieudane paczki i wznowił pobieranie od wcześniejszych kursorów. Proces silnika PID 10844 zakończył się z kodem 1; nie uruchomił się sam. O 18:18 UTC uruchomiono istniejące zadanie DEMO bez zmiany źródeł i konfiguracji (PID 652); ponowna aktywacja wymagała standardowo dwóch eksportów zegara EA. Nie ustalono jeszcze przyczyny zakończenia procesu z kodem 1. Brak wykrycia błędnego Bid/Ask w poprawnie pobranych tickach nie oznacza ciągłości zarządzania podczas tej przerwy. Dowody: `terminal-network-excerpt.txt`, `demo-recovery-incident.json`, `demo-health.json`. **NO-GO dla twierdzenia, że DEMO jest odporny na rozłączenia.** Minimalna potrzebna poprawa to zdiagnozowanie zakończenia procesu i przetestowanie nadzoru restartów z weryfikacją stanu/kwotowań; nie wdrożono takiej poprawki.

## Działanie bez udziału modelu

Rejestrator sam pobiera kolejne paczki, zapisuje kontekst i dziennik oraz co 5 minut aktualizuje wstępną gotowość. Zadanie Windows ponawia uruchomienie co 2 minuty po zakończeniu procesu i przy logowaniu; blokada zapobiega podwójnemu zapisowi. Komputer, sesja użytkownika i połączony MT5 muszą działać. Wyłączenie komputera nie zostaje ukryte jako pełna obserwacja; późniejszy backfill ticków nie odtworzy dawnych wersji kalendarza.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

Rezerwa dysku 10 GiB blokuje następne pobrania ticków, nie działanie DEMO. Wszystkie błędy pozostają w archiwum; źródła, konfiguracja, paczki i lokalny łańcuch odbiorów mają hashe. Hashe lokalne wykrywają zmiany, ale nie stanowią zewnętrznie poświadczonego czasu.
