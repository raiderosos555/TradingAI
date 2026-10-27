> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Porównanie starego i poprawionego modelu

**Nie ma jeszcze wiarygodnego porównania liczbowego.** Pełny historyczny replay czterech modułów nie został uruchomiony: wymagania UTC, warunków rozliczeń i kontekstu dostępnego w chwili decyzji pozostają niespełnione. Wyników nie zapisano jako zero; w `analysis.json` mają wartość `null`.

| Element | Stary backtester | Wymagany replay tickowy |
|---|---|---|
| Świece | Traktuje OHLC jako Bid | Last dla oryginalnych sygnałów; osobny Bid/Ask do wykonania |
| Spread/FX | Stały spread i mnożnik gotówkowy | Dynamiczne strony i udowodniona konwersja historyczna |
| Realizacja | Open następnej świecy, SL pierwszy przy niejednoznaczności | Kolejność ticków, brak fill na zerowym kwotowaniu, jawny model opóźnienia i poślizgu |
| Zarządzanie | Własna logika raz na świecę; zmieniony SL od następnej | Zamrożony Position Manager i harmonogram aplikacji, niezależne brokerowe SL/TP |
| Portfel | Instrumenty osobno | Wspólny Risk Manager, limity, margin, baseline i sekwencja zdarzeń |
| Kalendarz | Nie odtwarza historycznego filtra | Wersja dostępna w chwili decyzji, bez późniejszych rewizji |

Różnice liczby sygnałów, wykonanych wejść, poziomów fill, netto, Profit Factor, expectancy w R, drawdown oraz wpływ spreadu/prowizji: **N/D — brak poprawnego wspólnego eksperymentu**. Nie uruchomiono starego silnika z arbitralnymi zerowymi kosztami tylko po to, aby wypełnić tabelę.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

Zmiana aktywnego DEMO z 2 do 7 slotów nie została przeniesiona do zamrożonego badania. Wszystkie oglądane dane pozostają eksploracyjne; żadnych parametrów strategii nie dobrano do wyniku.
