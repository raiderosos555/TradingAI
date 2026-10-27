> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# EDGE_HYPOTHESES — trzy jawne hipotezy

Stan audytu: 2026-10-24T18:09:09.311248+00:00. Badanie offline; bez nowych zleceń, zmian DEMO, konfiguracji, Execution Engine i Risk Managera. Kwoty w PLN, o ile nie zaznaczono inaczej.

**Wykryty błąd ceny wykonania:** wszystkie siedem kontraktów zgłasza `chart_mode=1` (Last). Rekonstrukcja pełnej godziny 22.10 13:00–14:00 UTC z ticków odtworzyła zapisany OHLC dokładnie z Last dla każdego instrumentu; OHLC Bid różni się. Oba replays zakładają OHLC Bid. Poniższe PnL/PF są więc wynikami oryginalnego, niepoprawnie przyjętego modelu ceny, a nie zweryfikowanego wykonania. Nie naprawiono ich po cichu; wymagana jest osobna walidacja na Bid/Ask.

Poniżej formalizacja trzech już badanych alternatyw wobec lokalnych reguł; nie dodano ML ani czwartej rodziny. Rozszerzenie zakresu wskaźników, liczby filtrów lub dobieranie godzin po tym audycie tworzyłoby nowe testowanie i wymagałoby nowego protokołu. Wszystkie trzy obecnie **nie spełniają kryterium stabilnej przewagi**.

## Reguły wspólne

Siedem skonfigurowanych kontraktów. Decyzja po zamknięciu H1 j; dostępne co najmniej 201 wcześniejszych świec, luka między aktualną i poprzednią ≤2h. Wykonanie następny open Bid/Ask z opisanym modelem kosztów. Jedna pozycja na symbol, maks. dwie w portfelu, limity 0,1% / 0,2% / 0,5%, te same maksymalne loty i limity spreadu/ATR. Stop bazowy 2 ATR14 od ceny wykonania, TP 2 odległości SL. Bez TP1, BE i trailing. SL przed TP przy nieznanej kolejności; po ≥120h na początku świecy zamknięcie przy jej końcu (zatem nominalnie 121h, dłużej przy luce); koniec segmentu zamyka pozycje. To odmienne zarządzanie niż DEMO i tylko izolowana hipoteza.

## H1 — kontynuacja wybicia w trendzie (`trend_breakout`)

Mechanizm: utrzymywanie się kierunkowego ruchu po opuszczeniu wcześniejszego kanału. BUY, gdy close[j] > maksimum high[j−20:j] + 0,1 ATR14[j] oraz EMA50[j] > EMA200[j]. SELL lustrzanie poniżej minimum low −0,1 ATR i EMA50 < EMA200. Wyjścia według reguł wspólnych.

Powinna działać w trwałych ruchach, słabnąć przy powrotach do kanału, nagłych lukach i zmianach trendu. Diagnoza OIL potwierdza, że powrót do kanału często współwystępuje ze stratą, ale nie usprawiedliwia filtrowania wejść przyszłą świecą. Metoda: wspólny portfel, zamrożone reguły, trzy kolejne okresy, WF i sąsiednie SL. Odrzucenie tej konfiguracji: strata w większości okresów i brak dodatniej dolnej granicy niezależnej expectancy. Ryzyko overfittingu: średnie/wysokie po obejrzeniu historii; dowolny nowy filtr H4 wymaga osobnego, przyszłego testu.

## H2 — wejście po cofnięciu (`trend_pullback`)

Mechanizm: mniejsza skłonność do kupowania końca impulsu niż przy pogoni za wybiciem. BUY: EMA50 > EMA200 + 0,5 ATR; low[j] ≤ EMA50; close[j] > EMA50 oraz close[j] > open[j]. SELL: EMA50 < EMA200 −0,5 ATR; high[j] ≥ EMA50; close[j] < EMA50 i close[j] < open[j]. Wyjścia wspólne.

Powinna działać w trendach z uporządkowanymi korektami; zawodzić przy odwróceniu trendu i silnym ruchu przez średnią. Test identyczny z H1, bez wyboru najlepszego SL po końcowym okresie. Odrzucenie: brak stabilności znaku PnL przy SL 1,75/2/2,25 ATR, ujemna przyszła expectancy lub niewystarczająca próba. Ryzyko overfittingu wysokie: SL 1,75 poprawił niektóre oglądane odcinki, ale to nie daje prawa go promować.

## H3 — powrót do średniej w konsolidacji (`range_reversion`)

Mechanizm: odbicia wewnątrz równowagi, zamiast kontrtrendowego wejścia podczas silnego trendu. Wymagane |EMA50−EMA200| <0,5 ATR. BUY, gdy close < EMA50−1,5 ATR oraz RSI14<30; SELL, gdy close > EMA50+1,5 ATR oraz RSI14>70. Wyjścia wspólne.

Powinna działać w spokojnej konsolidacji; zawodzić po przejściu w trwały trend, zmianie wyceny makro lub szerokim spreadzie. Test na wspólnym portfelu i pełnej chronologii, z raportowaniem wszystkich odrzuconych wejść. Odrzucenie: brak dodatniej expectancy, mała liczba wejść, koncentracja wyniku lub załamanie po kosztach. Ryzyko overfittingu wysokie z powodu małych prób (bazowo 22/28/25 w segmentach).

## Wspólna ocena i briefing

`validation_protocol.json` zamrożono przed nową siatką 54 komórek: tylko SL 1,75/2/2,25, TP zawsze 2R, koszty ×1/×2. Bazowe 2 ATR nie zostało zastąpione zwycięzcą. Nie ma dodatniego wyniku w każdym z trzech okresów kosztu bazowego dla żadnej z dziewięciu kombinacji rodzina×SL. Wyniki w `VALIDATION_REPORT.md`.

Briefing/news jest dodatkowym **czynnikiem do porównania** tych hipotez, a nie czwartą wdrażaną strategią czy automatyczną zgodą. Przed przyszłą próbą można zamrozić porównanie: wszystkie sygnały vs sygnały zgodne z kompletnym, wcześniej otrzymanym kontekstem, przy identycznym Risk Managerze i kosztach. Najpierw obserwacja w shadow, bez usuwania transakcji z pierwotnego dziennika. Nie ma dziś danych, by określić wpływ wiadomości na expectancy.

Kryterium dopuszczenia do dłuższego forward: poprawna metodologia wykonania, zamrożony kontrakt danych i kosztów, z góry określony okres oceny oraz brak selekcji po wynikach. Próg minimum 100 nowych transakcji i co najmniej 3 miesiące jest dolnym minimum obserwacyjnym, nie gwarancją mocy statystycznej. Wymagana dodatnia dolna granica blokowego CI po uzgodnionej korekcie prób, dodatnia expectancy w kosztach ×2, stabilność okresów i brak naruszeń limitów. Inaczej wydłużyć próbę według z góry ustalonego planu albo odrzucić; nie analizować codziennie do pierwszej istotności.
