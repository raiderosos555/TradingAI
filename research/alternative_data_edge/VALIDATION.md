# Walidacja kodu i przygotowanie publikacji — 28.10.2026

Obliczenia zakończone, bez powtarzania analiz dla lepszego wyniku.

- edge_program:6 testów automatycznych PASS przed obliczeniem36porównań.
- alternative_data_edge:5 testów PASS przed obliczeniem6porównań głównych
  i6zaplanowanych diagnostyk opóźnienia.
- Niezależna kontrola6151row-level pomiarów: chronologia, granice podprób,
  algebra gross−cost, cash, kosztstress oraz zgodność agregatów PASS.
- 14hashy OHLC,5hashy indeksów,2protokoły i kod obliczeniowy zgodne z przebiegiem.
- 27chronionych plików silnika/konfiguracji zgodne z poprzednim manifestem;
  brak zmian w strategiach, Risk Managerze, LIVE i konfiguracji archiwizacji.
- Odczyt statusu kolektora o18:00:54 UTC: COLLECTING, świeży zapis. To pojedynczy
  odczyt, nie dowód bezlukowej pracy całego dnia ani nowy audyt Recovery.
- Wcześniejszy odczyt kontrolny MT5: połączenie, obecne brokerowe SL/TP,
  LIVE wyłączony, kwarantanna zachowana. Odporność DEMO nie jest certyfikowana.
- Brak wysłanych zleceń, brak zmian autoryzacji lub stanu pozycji, brak restartu
  terminala, silnika lub kolektora. Zakończono tylko własne procesy sond po timeout.

`private/validation-v1.json` zawiera lokalny wynik weryfikacji. FAIL przy
zmianie hasha nie jest zastępowany nowym oczekiwaniem. PASS kodu nie znosi
ograniczeń as-of, ceny Last, kosztu i małej próby.

Publikowany zakres: tylko pliki MD/PY na najwyższym poziomie dwóch katalogów
badawczych. Brak CSV, JSON, zip, kont, prywatnych odpowiedzi API, ceny wykonania
konkretnej pozycji czy baz tickowych. Repo docelowe zweryfikowane jako prywatne.
Skan przed commitem obejmuje index i historię Git oraz lokalną listę danych
poufnych. Jest heurystyczny, nie gwarantuje rozpoznania każdej postaci sekretu.
Push pozostaje wstrzymany do osobnej zgody zgodnie z ostatnią instrukcją.
