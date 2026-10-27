> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Otwarte ograniczenia po testach kontrolowanych

Etap 2A rozszerza etap 1 o 35 testów polityki. Nie stanowi potwierdzenia pełnej zgodności wykonania ani dopuszczenia do ponownego badania strategii.

1. **Historia ticków:** nadal tylko siedem kompletnych, wcześniej zachowanych godzin (371 167 rekordów). Nowe żądania historii przekraczały limit czasu; nie wiadomo, ile historii broker rzeczywiście udostępnia. Timeout obejmował inicjalizację i pobranie, więc nie dowodzi braku danych. Brak nowych rzeczywistych danych w etapie 2A.
2. **Czas:** zaobserwowano zmianę relacji zegara EA do UTC z +7200 na +3600 s. Nie dowodzi to mapowania wszystkich historycznych epoch ticków. Lista zaakceptowanych historycznych segmentów UTC pozostaje pusta. Syntetyczne testy UTC nie wypełniają tej luki. Nie zmieniono czasu działającego DEMO.
3. **Kontrakty i koszty:** brakuje historycznej ważności parametrów siedmiu kontraktów, komisji, swapu/rollover i konwersji do PLN. Kontrolowany kontrakt USD i jawne koszty testowe nie są ich zamiennikiem.
4. **Wykonanie:** nie ma kalibracji opóźnienia, poślizgu, płynności, requote, częściowych fillów brokera, reguł TP przy lukach ani wyścigu modyfikacji SL z wykonaniem serwerowym. Częściowe zamknięcie TP1 przetestowano; częściowe wykonanie pojedynczego zlecenia to osobny, jeszcze niezamodelowany przypadek. Nieobsługiwane brokerowe return codes i zlecenia pending jawnie przerywają pracę harnessu.
5. **Sesje i świece:** pozostają do empirycznego potwierdzenia historyczne sesje i granice H1/H4/D1. Testy DST i jawnych stref sprawdzają mechanikę, nie przypisują strefy brokerowi.
6. **Portfel:** testy używają jednego sztucznego kontraktu. Nie wykonano pełnego replay wielu instrumentów, współdzielonych slotów, skorelowanej ekspozycji, kalendarza i zmian margin. Ryzyko korzysta z zamrożonego RiskManagera, ale nie daje to pokrycia wszystkich jego ścieżek.
7. **Sygnały:** harness otrzymuje kontrolowane plany; nie buduje pełnych sygnałów strategii z Last. Podłączenie niezmienionego SignalEngine do chronologicznych zamkniętych świec i tickowego wykonania pozostaje dalszym etapem. Brak ticku nie może zostać zastąpiony OHLC bez osobnego oznaczenia wyniku jako innego modelu.
8. **Rozłączenie:** testuje brak aplikacji przy nadal dostępnych tickach serwera oraz zatrzymanie po przerwanym send. Nie odtwarza utraconych zdarzeń serwera podczas braku danych, aktywacji pending ani pełnego restartu i uzgodnienia niepewnych fillów.
9. **Briefingi:** archiwizacja kompletnych przyszłych briefingów z publikacją, pierwszym odbiorem, identyfikatorem planu, SL/TP, NO TRADE/HOLD/CANCEL pozostaje osobnym krokiem. Ten harness nie importuje briefingów i nie nadaje im uprawnień. Docelowy kanał pozostaje SHADOW.

Pełne porównanie historyczne powinno rozpocząć się dopiero po jawnej decyzji o pokrytym zakresie, potwierdzeniu czasu/kontraktów/kosztów, rozszerzeniu testów wykonania i zachowaniu niezmienionych reguł strategii. Wszystkie dotychczas oglądane dane pozostają eksploracyjne; nie służą promocji strategii.
