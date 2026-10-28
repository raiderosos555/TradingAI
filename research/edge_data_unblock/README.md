# Edge data unblock

Jeden zamrożony eksperyment COT ponad trend na nowej historii FX2010–2025.
Przeczytaj najpierw NEXT_DECISION.md i COT_EXPERIMENT_RESULTS.md. Wyniki są
warunkowymi markoutami cen referencyjnych, nie brokerowym P&L ani certyfikacją PIT.

Raporty: HISTORY_ACCESS.md, COT_DATA_AUDIT.md, COT_EXPERIMENT_PROTOCOL.md,
COT_EXPERIMENT_RESULTS.md, EIA_FEASIBILITY.md, NEXT_DECISION.md.

## Odtwarzanie bez sieci i bez terminala

W katalogu instalacji `C:\TradingAI` użyto istniejącego Pythona3.12 i NumPy.
Nie instalowano frameworku ani zależności. Polecenia:

```powershell
.venv\Scripts\python.exe -m unittest discover -s research\edge_data_unblock -p test_cot.py -v
.venv\Scripts\python.exe research\edge_data_unblock\cot_experiment.py
.venv\Scripts\python.exe research\edge_data_unblock\validate.py
.venv\Scripts\python.exe research\edge_data_unblock\render_reports.py
```

Każdy wynik jest write-once; powtórzenie w istniejącym katalogu kończy się
odmową nadpisania. Do reprodukcji użyć osobnej kopii katalogu badania z tymi
samymi wejściami, protocol-lock.json i private/local-before.json; wyniki
porównywać, nie nadpisywać. Validator chronionych plików wymaga lokalnego
projektu i kolektora — nie jest testem dostępnym w samym oczyszczonym repo.
Testy unittest nie wymagają tych prywatnych plików ani dostępu do sieci.

`private/package-v1/` przechowuje surowe źródła i metadane każdej próby,
łącznie z nieudaną próbą HTML/pustymi CSV. Tylko tff.raw, disagg.raw,
fed_eur_complete.raw i fed_gbp_complete.raw są wejściami cenowo-pozycyjnymi.
Protokół i kod obliczeń zahashowano; seed20261029. Wynik JSON przechowuje
wszystkie obserwacje, przyczyny pominięć, wszystkie8 prób i niekorzystne wyniki.
Raport zawiera hashe4 właściwych wejść; kompletne manifesty są lokalne.

## Pozyskanie, ograniczenia i bezpieczeństwo

`acquire_package.py` to końcowa wersja bounded downloadera dla zatwierdzonego
pakietu do5MB. Nie uruchamiać ponownie bez powodu; pobranie nowych wersji
źródeł nie odtwarza historycznej wersji ich treści. Dane pobierano po zgodzie
użytkownika; rzeczywisty łączny transfer treści podczas tej kampanii4 492 081B,
z uwzględnieniem błędnych formatów. Zapisane metadane zachowują te błędy.
Końcowy kod pomija niedziałające formaty; nie ukrywa ich historycznych wyników.

`fetch.py` używa curl.exe/Schannel, HTTPS, weryfikacji certyfikatów, deadline
35s (+40s procesu) i limitu rozmiaru. Brak retry, paginacji, tokenów, zakupów.
`diagnostics.py` wykonuje małe sondy i odczyt lokalnych dowodów; nie publikować
jego surowego wyjścia. `eia_feasibility.py` to12 HEAD i jeden mały CSV, nie
kampania tickowa. `isolated_mt5_probe.py` to przygotowany, **niewykonany** plan
sond historycznych; wymaga odrębnego uruchomionego terminala bez handlu.

Nie użyto brokerowego API do wysyłania zleceń. LIVE, strategie, Risk Manager,
Supervisor, kwarantanna i cohort forward pozostały bez zmian. Nie oceniano
wyniku strategii na nowej kohorcie forward. Surowe dane, JSON, logi, lokalne
tożsamości i runtime są wykluczone z publikacji; repo zawiera raporty i kod.

Wyniki opisowe mają udokumentowane pochodzenie: CFTC i Federal Reserve Board.
Źródła oraz ograniczenia licencji podano w raportach. Dalsze strojenie COT
na obejrzanych okresach i deklarowanie niezależnego sukcesu jest niedopuszczalne.
