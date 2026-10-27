> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Dane do replay 22.10 — stan 26.10.2026

**NO-GO dla kompletnej doby UTC.** Dane poniżej zachowują surowy czas API. Etykieta daty w tym układzie nie jest dowodem daty UTC.

| Wejście | Potwierdzony zakres | Ograniczenie |
|---|---|---|
| Siedem instrumentów | Etap 11: 5 401 052 ticki, 42 okna żądań; raw 22.10 00:00–23.10 00:00 | Dostępność zwrócona przez API, nie certyfikat kompletności historii serwera |
| Świece sygnałowe | 213 świec Last zgodnych z OHLC i tick_volume; 4 puste H1 | Nie należy interpretować ich jako Bid |
| Warm-up | 200 wcześniejszych zamkniętych H1 na każdy z 7 instrumentów; pliki `*-warmup.json` | Granica przed raw 22.10 00:00; po ustaleniu UTC należy ponownie wybrać właściwą granicę |
| USDPLN | 126 629 ticków, 6 okien po 4 godziny | Polityka historycznej konwersji nadal niepotwierdzona |
| USDPLN.pro | 160 216 ticków, 6 okien po 4 godziny | Jak wyżej; nie wolno dowolnie zamieniać tych dwóch serii |
| UTC | Brak zaakceptowanego segmentu dla 22.10 | Dowody +7200 z 23.10 dotyczą obserwowanych operacji, nie całej wcześniejszej doby |
| Kalendarz | Znalezione kopie pobrane po 22.10 | Brak wersji dostępnej wtedy; zamrożony Risk Manager wymaga aktualnego kalendarza |
| Kontrakty/koszty | Bieżące kontrakty i wcześniejsze próby kalkulacji | Brak potwierdzonych warunków obowiązujących 22.10, prowizji, swapu i modelu poślizgu/opóźnienia |

Obie serie FX zaczynają się w raw `1792627200545`, kończą w `1792713590320`; nie mają zerowych/crossed Bid/Ask w pobranym zbiorze. Największy odstęp między rekordami to 371 189 ms. Nie dowodzi on ani awarii, ani kompletności; nie wypełniono go sztucznymi cenami. `fx-collection.json` zawiera okna, wyniki, hashe i identyfikatory procesów.

**Raw doba nie musi pokrywać doby UTC 22.10.** Jeżeli później zostanie udowodnione przesunięcie +7200, doba UTC wymaga raw 22.10 02:00–23.10 02:00; obecny zbiór nie obejmuje jej ostatnich dwóch godzin. To przykład konsekwencji warunkowej, nie przyjęcie tego offsetu.

Per-symbol kolejność rekordów, w tym rekordów o identycznej milisekundzie, musi zostać zachowana. MT5 nie dostarcza tutaj wspólnego numeru sekwencji dla różnych instrumentów. Kolejność między instrumentami z tym samym czasem może wpływać na wspólne limity portfela; arbitralne sortowanie po nazwie nie jest dowodem rzeczywistej kolejności.

Wszystkie dotychczas oglądane dane są **eksploracyjne**. Brakujące kwotowania, kalendarz, UTC i koszty nie zostały zastąpione danymi syntetycznymi.
