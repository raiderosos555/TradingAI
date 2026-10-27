> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Etap 7 — opóźniony fill i niezależny Risk Manager

Badanie kontrolowane 25.10.2026. **12 testów przeszło.** Użyto zamrożonych produkcyjnych RiskManager, ExecutionEngine i Journal oraz brokera działającego wyłącznie w pamięci. Parametry strategii, konfiguracja DEMO i zegar terminala nie zostały zmienione. Brak nowych rzeczywistych zleceń i pełnego backtestu.

## Co połączono

`DelayedBroker` rozszerza wcześniejszy broker kontrolowany. ExecutionEngine wykonuje niezależne kontrole ryzyka i order_check, ponawia preflight, zapisuje trwały intent, a następnie wywołuje send. Wewnątrz tego wywołania broker przesuwa wirtualny czas przez jawnie dostarczone ticki, aż do pierwszego ticku po zadanym opóźnieniu. Po drodze utrzymuje serwerowe SL/TP. Fill odbywa się po aktualnym Bid/Ask, a odpowiedź wraca do niezmienionego mechanizmu weryfikacji ExecutionEngine.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

## Wyniki kontrolowane

| Przypadek | Wynik |
|---|---|
| Za szeroki spread przed wysłaniem | Risk Manager blokuje; brak żądania i brak zużycia przyszłych ticków |
| Brak baseline dobowego | Nowe wejście zablokowane przed send |
| Późniejszy BUY / SELL | Fill odpowiednio po nowym Ask / Bid, a nie po kwotowaniu decyzji |
| Nadmierny niekorzystny poślizg | Fill i pozycja pozostają; ExecutionEngine oznacza UNCERTAIN i blokuje kolejne żądania |
| Spread rozszerza się po wysłaniu | Nie cofa się fikcyjnie wcześniejszego wysłania; rzeczywisty w modelu fill i strata spreadu pozostają w ledgerze |
| TP1 | Opóźniony Bid, częściowy wolumen, prowizja oraz pozostałość zgodne z oczekiwanym rachunkiem |
| SL serwera podczas oczekiwania na close | Serwer zamyka raz; spóźniony close nie tworzy drugiego zamknięcia ani odwróconej pozycji |
| Brak ticku w oknie | Timeout bez fikcyjnego fillu, kwarantanna, brak automatycznej ponownej próby |
| Luka unieważnia SL nowego wejścia | Model serwera odrzuca request; brak pozycji |
| Cena cofa się podczas wysłania BE | Model serwera odrzuca nowy SL zbyt blisko ceny; dotychczasowy SL pozostaje |
| Bezpośredni send bez trwałego intent | Odrzucenie przez adapter badawczy |

Przykład istotny dla wiarygodności wyniku: akceptowalny preflight BUY przy Ask 100,02 może zakończyć się fillem 100,12 po opóźnieniu. Ponieważ przekracza zapisane dopuszczalne odchylenie, status staje się UNCERTAIN. Nie oznacza to braku transakcji: pozycja i koszty istnieją i muszą pozostać w wyniku symulacji. Inaczej backtester usuwałby niekorzystne wykonania.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

## Założenia i ograniczenia

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

## Odtworzenie

```powershell
.\.venv\Scripts\python.exe research\tick_validation\stage7\run.py
```

`traces.json` przechowuje konfigurację przypadku, ceny, intent/status, deale, prowizje, stan pozycji i konta. `validation.json` i `tests.txt` zawierają wyniki; `manifest.json` — hashe. Walidacja sprawdza też wcześniejsze etapy i niezmienione pliki produkcyjne. Następny etap pełnego replay nadal wymaga zegara, kosztów i wspólnego portfela; nie uruchomiono nowych poszukiwań parametrów strategii.
