> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# TradingAI — zbiorczy raport po etapie 11

**26.10.2026. Decyzja główna: NO-GO dla ogłoszenia wiarygodnego wyniku netto historycznej strategii, jej promocji lub LIVE. GO dla zamknięcia etapu 11 jako walidacji danych.** Nie uruchomiono kolejnego etapu badań. Ocena poniżej dotyczy dowodów o określonym zakresie, a nie deklaracji, że cały system został certyfikowany.

## 1. Co zostało technicznie potwierdzone?

| Obszar | Potwierdzone | Granica dowodu |
|---|---|---|
| Dane i cena sygnału | Jedna doba raw 22.10 na siedmiu instrumentach: 5 401 052 ticki. 213 istniejących świec H1/H4/D1 odtworzonych z aktualizacji Last, łącznie z tick_volume; cztery puste przedziały H1 bez sztucznych świec | Udane żądanie nie gwarantuje wszystkich ticków serwera. Tylko jedna doba, nie wielomiesięczny zbiór |
| Bid/Ask i kolejność | BUY otwierany po Ask, zamykany po Bid; SELL odwrotnie. Testy luk, spreadu, opóźnienia oraz zachowania kolejności. Siedem starszych godzin zgadza się z pełną dobą rekord po rekordzie | Zgodność kwotowania nie gwarantuje rzeczywistego fillu, płynności lub poślizgu |
| Jakość ticków | Jeden zerowy Bid/Ask w GOLD pozostaje jawny; ważny Last tworzy świecę, ale taki rekord nie może realizować zlecenia. Następny poprawny tick ma tę samą milisekundę | Diagnostyka nie jest jeszcze kompletnym adapterem wykonania obsługującym tę sytuację w replay |
| Reguły zarządzania | Kontrolowane testy z zamrożonym rzeczywistym RiskManager/ExecutionEngine/PositionManager: SL/TP, TP1, BE, trailing, loty, limity dzienne, kwarantanna, opóźnienia i rozłączenie | Nie jest to pełna empiryczna zgodność wszystkich reguł z brokerem ani zintegrowany historyczny portfel |
| Rozliczenia | 504/504 bieżące kalkulacje dla siedmiu instrumentów odtworzone odpowiednimi hipotezami. CFD odpowiadają konwersji USDPLN; EURUSD/GBPUSD — USDPLN.pro; EURPLN bez FX. Dla GOLD/US500/US100 siatka rozróżnia zaokrąglenie USD przed FX | Aktualne reguły kalkulatora nie dowodzą historycznej taryfy, konwersji ani zaokrągleń; OIL/FX nie rozróżniają obu wariantów zaokrąglenia pośredniego |
| Czas | Mechanika jawnych mapowań UTC, niejednoznaczności DST i granic świec jest testowana; surowe czasy zachowane | Brak zaakceptowanego mapowania UTC dla całej doby 22.10. Obserwacji bieżących nie ekstrapolowano wstecz |
| Briefing | Izolowane archiwum SHADOW: pełne dane źródłowe, publikacja, pierwszy odbiór, wersje, plan_id, SL/TP, NO TRADE/HOLD/CANCEL, kontrola dostępności w danym momencie | Brak automatycznego odczytu historii ChatGPT; testy archiwum nie dowodzą otrzymania kompletnego rzeczywistego przyszłego briefingu. Kontekst nie autoryzuje zleceń |
| Powtarzalność | Zamrożone źródła i konfiguracje, SHA-256, lokalne skrypty, 14 testów etapu 11; wcześniejsze manifesty sprawdzone | Zielone testy mechaniki nie są testem rentowności |

Dowody: [etap 11](REPORT.md), `comparison.json`, `manifest.json`; wcześniejsze raporty w `../stage2`, `../stage4`, `../stage6`–`../stage10` oraz `../../shadow_briefings`. Pierwotne pięć raportów w katalogu nadrzędnym opisuje stan etapu 1 i pozostaje niezmienne; **ten raport aktualizuje ich wnioski**.

## 2. Co konkretnie blokuje poprawny historyczny backtest?

1. **Czas dla wybranego okresu.** Surowe znaczniki są znane, lecz dokładne powiązanie z UTC nie ma zatwierdzonego dowodu dla 22.10. Dotyczy to wygasania sygnałów, dziennego limitu i kalendarza. Dla ograniczonego testu wystarczy potwierdzić jego okres; nie trzeba najpierw rozwiązywać całej historii DST.
2. **Historyczne koszty i specyfikacje.** Brak potwierdzonej polityki kontraktu, prowizji/opłat, FX w chwilach realizacji oraz swapu, jeżeli wystąpi utrzymanie pozycji przez rollover. Cztery krótkie próbki USDPLN nie pokrywają pełnej doby wszystkich potencjalnych fillów. Zero nie może zastępować nieznanego kosztu.
3. **Brak kompletnego replay strategia–wykonanie–portfel.** Są przetestowane elementy, ale nie ma jeszcze jednego zweryfikowanego przebiegu z zamrożonym SignalEngine, stanem rachunku, niezależnym Risk Managerem, opóźnieniem, niedostępnymi kwotowaniami, częściowymi wyjściami i ciągłością zarządzania. Zasady aktywacji pending i częściowych fillów nadal mają ograniczony dowód empiryczny. To praca integracyjna, nie poszukiwanie lepszych parametrów.
4. **Kontekst dostępny w danym momencie.** Dla reguł korzystających z kalendarza trzeba mieć właściwe historyczne wydarzenia i ich ówczesną dostępność. Przyszłe rewizje i obecne newsy nie mogą być wstawiane do historii. Brak dawnych briefingów nie blokuje strategii, które ich nie używały; blokuje twierdzenia o skuteczności wariantu z takim filtrem. Nie można wyłączyć aktywnej reguły i nazwać tego niezmienioną strategią.
5. **Początek i koniec próby.** Silnik używa 200 świec H1 do kontekstu. Jedna doba ticków nie wystarcza do rozgrzewki; trzeba jawnie użyć wcześniejszych, zamkniętych świec Last z właściwym czasem. Trzeba także zdefiniować kapitał początkowy i stan portfela symulacji, przenosić dzienną bazę ryzyka i raportować pozycje otwarte na końcu. Nie wolno zamykać ich dowolnie tylko po to, aby policzyć korzystny PF.

Brak wielomiesięcznej historii **nie blokuje samego testu technicznego na jednym dniu**. Blokuje wnioskowanie o stabilnej przewadze w wielu okresach. W etapie 11 nie obliczono nowego netto, PF, expectancy w R ani drawdown; dawny wniosek o niepotwierdzonej przewadze pozostaje aktualny.

## 3. Jakie jest minimalne kolejne badanie i dlaczego jest konieczne?

Proponowane minimum to **jeden z góry określony replay zamrożonych reguł na już pobranej dobie 22.10**, bez poszerzania siatki parametrów i bez szukania lepszego okresu po zobaczeniu wyniku. Nie rozpoczęto go automatycznie.

Przed nim potrzebne są tylko dane i integracja wymagane dla tej konkretnej doby:

- potwierdzenie jej czasu UTC i stosowanych granic doby/sesji;
- komplet właściwych FX oraz udokumentowana polityka kontraktu/opłat dla tego okresu, a także dane kalendarza wymagane przez zamrożone reguły;
- wcześniejsze 200 zamkniętych H1 Last do rozgrzewki, bez przyszłych świec;
- jedna ścieżka replay z zamrożonym Risk Managerem i Position Managerem, testem niewykonywalnego ticka GOLD, świeżości kwotowań, luk i identycznego stanu pozycji/rachunku po znanych przypadkach.

Wynik minimalnego testu: liczba sygnałów i odmów, wykonane wejścia, poziomy fillów, koszty, pozycje nierozstrzygnięte, a metryki netto/R/DD/PF tylko tam, gdzie dane i liczba zamkniętych transakcji na to pozwalają. PF przy braku strat lub braku transakcji nie może być przedstawiany jako dowód przewagi. Porównanie ze starym modelem ma używać tych samych reguł i tego samego okresu.

To badanie jest konieczne, ponieważ sprawdza, czy błąd Last→Bid i koszty zmieniają transakcje oraz wynik przy niezmienionej logice. **Nadal nie ustali statystycznie wiarygodnej wartości inwestycyjnej.** Następnym uzasadnionym krokiem dopiero po przejściu tej bramki byłby z góry zamknięty protokół forward, np. 20 kolejnych pełnych sesji jako pierwsze okno operacyjne, z rejestracją wszystkich sygnałów, kosztów i odmów. Dwadzieścia sesji nie jest gwarancją wystarczającej próby; kryterium liczby niezależnych transakcji i niepewności wyniku trzeba określić przed oceną. Nie przedłużać ani nie kończyć badania według tego, czy pojawił się zysk.

## 4. Czy możemy testować zamrożone strategie na ograniczonych tickach?

**Tak jako docelowy, ograniczony test techniczny; jeszcze nie jako wiarygodny backtest ekonomiczny uruchamiany dziś.** Dane dla jednej doby siedmiu instrumentów już są, więc nie trzeba masowo pobierać kolejnych miesięcy. Najpierw trzeba domknąć wskazane mapowanie czasu, koszty/kalendarz i integrację replay. Dopóki ich brakuje, dopuszczalny jest audyt cen/chronologii i jawne scenariusze wrażliwości, ale nie raport „rzeczywistej rentowności”.

Zamrażamy istniejące `local_breakout_v1` i `local_false_breakout_v1` wraz z konfiguracją, selektorem, limitami i zarządzaniem. Obie reguły nie powinny być uruchamiane osobno w sposób omijający selektor lub wspólne limity portfela. Nie wybieramy wyłącznie instrumentu, który wcześniej wyglądał najlepiej. Wszystkie dotychczas oglądane dane pozostają eksploracyjne, także 22.10.

## 5. Czy DEMO jest stabilne?

**Proces działa i zarządza obecnymi pozycjami walutowymi, ale nie potwierdzono stabilności wieloinstrumentowego DEMO.** Audyt tylko do odczytu z 26.10, **08:20:05–08:20:25 czasu Warszawy** (07:20 UTC), obejmował trzy próbki oraz ostatnie operacje i decyzje. Źródła: `demo_health.json`, `demo_management_interruptions.json`. Końcowa kontrola wykryła błąd wstępnej oceny: sam wiek ticka nie dowodzi dostępności Bid/Ask.

- Terminal był połączony, PID silnika 4428 istniał, status aktualizował się jako RUNNING, a dziennik zawierał świeże decyzje zarządzania obiema pozycjami. Nie ma nierozstrzygniętych INTENT/UNCERTAIN ani kwarantanny w tej obserwacji.
- Wszystkie 21 odczytów miały wiek pod bieżącym offsetem runtime od około **−0,180 do 8,218 s**, w dopuszczonym zakresie −2…10 s. Jednak **5/21 odczytów miało Bid=Ask=0**: US500 we wszystkich trzech próbkach, US100 w pierwszej i OIL w drugiej. Są to rekordy z Last/volume i flags=24. Nie są dostępne do wykonania zlecenia. Nie zastąpiono ich Last ani wcześniejszą ceną. Pozostałe 16 odczytów miało poprawny Bid/Ask; w szczególności wszystkie sześć odczytów dla instrumentów dwóch otwartych pozycji było poprawnych. Małe wartości ujemnego wieku pozostają jawne. To odczyt względem hosta i bieżącego offsetu, nie certyfikat historycznego UTC.
- Broker potwierdza dwie pozycje: GBPUSD BUY 0,01, SL 1,33521 / TP 1,34067; EURUSD SELL 0,01, SL 1,12372 / TP 1,11900. Ich identyfikatory są powiązane z potwierdzonymi otwarciami w dzienniku i historii zleceń brokera. Nie ma zleceń oczekujących w próbkach.
- Dziennik ma potwierdzony BE i dwie modyfikacje trailing na wcześniejszej pozycji US100. Historia brokera zawiera jej zamknięcie z kodem powodu 4 (SL), po przeniesieniu stopa. To rzeczywisty dowód działania części zarządzania, nie dowód przewagi strategii. TP1 na minimalnym locie był prawidłowo wstrzymywany, gdy pozostawiałby niedopuszczalny wolumen.
- Nocny dziennik zawiera **2839 decyzji odmowy z powodu spreadu**, **1084 z łącznym powodem stale/future/crossed quote** i **213 z niepoprawnym Bid**. To liczby decyzji, często wielu reguł w jednej pętli — **nie liczby niezależnych awarii ani czas przestoju**. Zgrupowanie według pozycji i dziesięciosekundowych przedziałów znajduje się w osobnym pliku. Ostatnia odmowa stale/future/crossed była o 08:11:50 czasu Warszawy; późniejsze próbki i decyzje pokazują wznowienie.
- Odmowy są zachowaniem ochronnym, ale oznaczają okresową niedostępność programowego BE/trailing/wyjścia. Ochrona przez SL/TP pozostaje po stronie brokera; nie gwarantuje ceny bez poślizgu. Kod runtime przy niepotwierdzonym zegarze/połączeniu omija również cykl Position Managera. Nie należy uznać samego RUNNING za dowód nieprzerwanego zarządzania.

Nie odtworzono celowo awarii połączenia na działającym DEMO. Łączny komunikat stale/future/crossed nie pozwala z obecnego dziennika jednoznacznie ustalić każdej przyczyny. Osobnego, minimalnego sprawdzenia wymaga różnica pomiędzy ostatnim rekordem Last/volume a ostatnim rzeczywistym kwotowaniem Bid/Ask, jego własnym czasem oraz przyczyną odmowy Risk Managera. Bieżące snapshoty mają inne zachowanie niż prawie zawsze kompletne snapshoty w pobranej dobie historii. Nie wolno bez dowodu i testu zastępować zera ostatnią znaną ceną. Jest to konkretna przeszkoda stabilności wykonania, nie powód do zwiększania liczby transakcji. Nie wdrażano teraz zmian produkcyjnych; Risk Manager nadal odrzuca niepoprawne ceny.

Bieżący runtime używa offsetu +3600 w ramach istniejącego mechanizmu weryfikacji i wcześniejszej autoryzacji. Ten etap go nie zmieniał. Limity pozostają: 0,1% na transakcję, 0,2% łącznie, 0,5% dziennie, maksymalnie dwie pozycje. Audyt nie otwierał ani nie zamykał pozycji.

## Ostateczna bramka

| Decyzja | Zakres i uzasadnienie |
|---|---|
| **GO** | Zakończenie etapu 11: dane i ich ograniczenia są jawne, obliczenia zapisane, testy i manifesty zweryfikowane |
| **GO wyłącznie dla obserwacji; NO-GO dla deklaracji stabilności całego DEMO** | Silnik działa, aktualne pozycje FX mają SL/TP i poprawne ceny, ale 5/21 świeżych snapshotów innych rynków nie ma Bid/Ask. Istniejące blokady i limity pozostają bez zmian. Nie jest to nowa autoryzacja zleceń |
| **NO-GO teraz** | Wynik netto zamrożonych strategii jako wiarygodny historyczny backtest — brakuje danych czasu/kosztów/kontekstu i pełnego replay |
| **NO-GO** | Promocja strategii, stwierdzenie zyskownej przewagi, zwiększenie ryzyka albo LIVE — brak dowodów statystycznych i niezależnej walidacji forward |

Kolejnego etapu nie uruchomiono. Jego minimalny, konieczny zakres został uzasadniony powyżej; szeroka optymalizacja i kolejne dowolne próbki nie są teraz potrzebne.
