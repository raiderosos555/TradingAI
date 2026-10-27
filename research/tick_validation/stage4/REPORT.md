> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Etap 4 — wcześniejsze wykonania DEMO a rzeczywiste ticki

Badanie odczytowe 25.10.2026. Materiał: **pięć wykonanych wcześniej operacji US500.pro, dwie pozycje z 23.10**, w tym jedno częściowe zamknięcie. To testy techniczne operatora, nie transakcje ocenianej strategii. Nie otwarto nowych pozycji i nie zmieniano konfiguracji DEMO.

## Ceny wykonania

Pobrano 2338 ticków z dwóch minut surowej osi czasu API, obejmujących zapisane czasy brokerowych wykonań. Do porównania wykorzystano ostatnią grupę ticków o jednakowym timestampie, nie późniejszą niż wykonanie. Żaden przyszły tick nie wybiera ceny. Jeśli kilka rekordów w tej milisekundzie ma różne odpowiednie ceny, wynik pozostaje zbiorem możliwości — nie wybiera się najlepszego.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

Wszystkie pięć cen zgadza się z odpowiednim Bid/Ask poprzedzającej grupy ticków oraz kwotowaniem w odpowiedzi brokera. Ceny w tych grupach nie były niejednoznaczne. Częściowe zamknięcie pokazuje jednak **0,2 punktu indeksowego pogorszenia względem niezależnie sprawdzonej ceny preflight**. Dla obecnego `point=0,1` to 2 jednostki point MT5; historycznej ważności dzisiejszej specyfikacji nie zakłada się globalnie. Spread wynosił w tych momentach 0,7 punktu indeksowego.

Wniosek: aktualny Bid/Ask przy wykonaniu jest zgodny z próbką, ale zastąpienie go wcześniejszą ceną decyzji z zerowym opóźnieniem może zniekształcić wynik. Pięć operacji nie wystarcza do kalibracji rozkładu poślizgu, opóźnienia ani modelu brokerowych SL/TP. Częściowe zamknięcie w tej próbce było poleceniem operatora; nie dowodzi historycznej realizacji automatycznego TP1.

## Rzeczywiste rozliczenie

Źródłem są zachowane brokerowe deale w raporcie `exchange/outbox/20261023T194453-3b5d0e08.json`, z oryginalnymi `broker_raw_time_msc`, ticket/order/position_id, cenami, wolumenami i kosztami. Potwierdzono zgodność deal↔journal↔wynik order_send i pełne zamknięcie wolumenów.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

W pięciu dealach broker zaraportował prowizję, fee i swap po zero. Dotyczy to tylko tej próbki krótkich operacji; nie ustanawia zerowych kosztów przyszłych ani innych kontraktów. Wynik PLN odczytano z brokera — **nie odtworzono go niezależnie z historycznego FX i specyfikacji kontraktu**. Dane nie służą do dopasowania mnożnika przeliczeniowego do znanego wyniku.

## Zegary i opóźnienie — oddzielne wielkości

Każdy journal zawiera czas hosta przy trwałym zapisie intent i późniejsze potwierdzenie. Przy założeniu, że timestamp dealu oznacza wykonanie pomiędzy tymi zdarzeniami, można ograniczyć różnicę zegarów:

`raw_deal − confirmed_host ≤ różnica_zegarów ≤ raw_deal − intent_host`.

Przecięcie pięciu takich przedziałów wynosi około **7 200 085,8–7 200 110,3 ms**, czyli 2 h i dodatkowe 85,8–110,3 ms. To warunkowa lokalna zgodność zegarów w tych dwóch krótkich oknach, nie niezależna certyfikacja czasu. Dodatkowa różnica może obejmować niesynchronizację zegarów i semantykę timestampów. Czas surowy dealu minus hostowy intent **nie jest czystym opóźnieniem wykonania**.

Nie przyjęto nowego globalnego offsetu, strefy IANA, harmonogramu DST ani segmentu mapowania dla całej historii. Dane nadal nie potwierdzają granic sesji/H1/H4/D1. Dla tych porównań tick↔deal użyto wspólnej surowej osi API, więc nie potrzeba globalnej korekty UTC.

## Odtwarzanie i ograniczenia

- `inputs/broker-report.json`: dokładna kopia wcześniejszego raportu; SHA-256 w `collection.json`.
- `inputs/ticks-*/`: świeżo odczytana historia raw, fazy API i bieżąca specyfikacja, bez normalizacji czasu.
- `comparison.json`: pięć pełnych dopasowań, grupy wcześniejszych ticków, preflight, faktyczne kwoty i warunkowe przedziały zegara.
- `test_analysis.py`: kontrola kierunku BUY/SELL, braku przyszłych ticków, duplikatów timestampów, wieku i chronologii oraz obliczeń przedziału.
- `validation.json`, `manifest.json`: wyniki weryfikacji i hashe.

Odtworzenie offline z C:\TradingAI:

```powershell
.\.venv\Scripts\python.exe research\tick_validation\stage4\validate.py
```

Nie uruchomiono pełnego backtestu ani nie zmieniono parametrów strategii. Zakres dowodów pozostaje wąski: jeden instrument, pięć market fillów, brak rzeczywistych SL/TP, pending fillów, luki, overnight, innych wolumenów i okresów. Wszystkie oglądane dane są eksploracyjne. Następny replay wymaga modelu opóźnienia, konwersji FX, historycznych kontraktów/kosztów i wiarygodnego zegara, zamiast dopasowywania ich do tych pięciu realizacji.
