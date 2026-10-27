> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Kontynuacja po etapie 11 — decyzja i wykonane prace

**Decyzja: GO dla dalszej walidacji technicznej; NO-GO dla wiarygodnego wyniku historycznego, uznania pełnej stabilności DEMO i badania przewagi.** To nie jest deklaracja zakończenia pełnego replay. Konkretne blokady są wymienione poniżej; parametrów strategii nie optymalizowano.

## Stan wykonania

- Potwierdzono związek zerowych Bid/Ask ze zdarzeniami Last/volume. Nowy odczyt odtworzył problem OIL również w `symbol_info()`. Oddzielne czasy aktualizacji stron zapisano w `analysis.json`.
- Zebrano 286 845 ticków USD/PLN w dwóch seriach oraz przygotowano 7 × 200 wcześniejszych zamkniętych H1. Wcześniejszy zbiór 5 401 052 ticków i zamrożone źródła zachowano bez zmian.
- Połączono cztery zamrożone moduły w kontrolowanym przebiegu BUY i SELL, z aktywnym filtrem kalendarza. Potwierdzono TP1, BE, trailing i server TP. **18/18 nowych testów** przeszło.
- Przygotowano minimalny prototyp ponownego odczytu po zerowej cenie. Nie korzysta ze starej ceny i nie autoryzuje zleceń. **Nie wdrożono go do DEMO**; wymagane jest osobne zatwierdzenie.
- Nie uzupełniono dowodem UTC dla 22.10, historycznego kalendarza ani pełnych warunków rozliczeń. Dlatego **pełny historyczny adapter/replay i liczbowe porównanie ze starym backtesterem pozostają niewykonane**. Metryki zapisano jako `null`, nie 0.

## DEMO i zatwierdzona zmiana slotów

Na podstawie nowej instrukcji użytkownika podniesiono limit liczby pozycji i zarezerwowanych zleceń z **2 do 7**. Pozostaje jedna ekspozycja na instrument, minimalne loty, 0,1% limitu ryzyka pojedynczej transakcji, 0,2% łącznie oraz 0,5% dziennego limitu strat. Budżet ryzyka może zablokować dodatkowe wejście mimo wolnego slotu. LIVE pozostało wyłączone.

Zmodyfikowano wyłącznie konfigurację DEMO i walidator limitu: do 7 tylko w DEMO; w LIVE/DRY_RUN nadal do 2. Autoryzację powiązano z nowym hashem. Zamrożony backtest zachował stary limit. **186/186 testów produkcyjnych** przeszło. Rejestr migracji: `state/config-migrations/demo-slots-20261026-validated/`.

Pierwsza próba zmiany samej konfiguracji ujawniła dodatkowy limit w walidatorze i spowodowała przejściowy BLOCKED (log 08:05:49 UTC). Przywrócono konfigurację o 08:06 UTC; później wykonano testy i kontrolowany restart. Po ponownym potwierdzeniu zegara zarządzanie wznowiono o 08:10 UTC. Ten incydent jest zachowany w dzienniku; nie opisujemy migracji jako bezprzerwowej.

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

## Odpowiedzi decyzyjne

1. **Technicznie potwierdzone:** Last jako baza świec, zachowana kolejność danych w obrębie instrumentu, poprawne strony wykonania w kontrolach, kompletna współpraca czterech klas na fixtures, działające blokady kalendarza/autoryzacji/kwotowań i dostępność FX/warm-up.
2. **Przeszkody historycznego backtestu:** niepotwierdzone UTC i przez to zakres doby; brak kalendarza dostępnego wtedy; niepotwierdzone historyczne koszty/kontrakt/FX; nieukończony adapter historycznego portfela; brak wspólnej kolejności dla identycznych czasów różnych instrumentów.
3. **Minimalne kolejne badanie:** jeden instrument, jeden wiarygodnie zmapowany odcinek, potwierdzone koszty i kalendarz, bez strojenia. Jeśli kalendarza 22.10 nie ma, przejść na nowy kompletnie archiwizowany odcinek, zamiast zmieniać zamrożone reguły.
4. **Ograniczony wiarygodny replay teraz:** możliwe testy mechaniki i sygnałów na danych eksploracyjnych; **nie** pełny wynik ekonomiczny zamrożonej polityki 22.10. Nie utożsamiamy braku wykonania z zerową rentownością.
5. **Stabilność DEMO:** proces i zarządzanie po restarcie działają; brokerowe zabezpieczenia działały. Wcześniejsze zerowe/stare kwotowania powodowały przerwy, więc **NO-GO dla twierdzenia o pełnej stabilności**. Krótkie poprawne próbki nie usuwają tego ograniczenia.

Szczegóły: [dane](DATA_COVERAGE.md), [kwotowania i proponowana poprawka](PRICE_MODEL.md), [integracja](EXECUTION_PARITY.md), [porównanie](BACKTEST_COMPARISON.md), [pozostałe wymagania](REMAINING_LIMITATIONS.md). Wszystkie dane oglądane dotychczas pozostają eksploracyjne.
