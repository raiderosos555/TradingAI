# Mały odbiór EIA/OIL

Wynik tabel w [REPORT.md](REPORT.md); najnowszy wynik 12 udanych sond w
[TICK_AVAILABILITY.md](TICK_AVAILABILITY.md). Wcześniejszy timeout zachowany w
[TICK_PROBE_RESULT.md](TICK_PROBE_RESULT.md). Zakres w [PLAN.md](PLAN.md),
z jawną korektą dostępu [PLAN_AMENDMENT_01.md](PLAN_AMENDMENT_01.md).
Nowsza kontrola czasu i brakującego actual w kalendarzu:
[DATA_READINESS_UPDATE.md](DATA_READINESS_UPDATE.md). Oficjalny bieżący
endpoint EIA działa mimo 404 adresu archiwalnego ostatniego wydania.
Brak testu strategii, brak P&L; aktywnego terminala nie wolno używać do tych sond.

Z katalogu projektu, istniejącym Pythonem:

```powershell
python research/eia_data_acceptance/test_acceptance.py
python research/eia_data_acceptance/validate_tables.py
```

Test integralności rzeczywistych źródeł wymaga prywatnego `tables-v1`;
w oczyszczonym repo zostanie jawnie pominięty. Pozostałe testy są offline.
Walidator odmawia nadpisania dowodu. `validate(folder)` umożliwia ponowny
odczyt/weryfikację bez zapisu. Hash źródeł jest w prywatnym manifeście.

`collect_tables.py` pobiera wyłącznie 12 ustalonych małych tabel, ponownie
wykorzystując wcześniejszy plik 04.03.2026; nie uruchamiać drugi raz bez powodu.
Zależy od istniejącego `edge_data_unblock/fetch.py` (TLS Schannel, limit rozmiaru).
Dokładny moment odbioru nie był instrumentowany w downloaderze; nie utożsamiać
czasu rozpoczęcia żądania z odbiorem ani historyczną publikacją.

Po ręcznym uruchomieniu osobnego terminala DEMO, z wyłączonym Algo i DLL,
można wykonać sondę odczytową. Hasło inwestorskie nie jest wymagane; skrypt
nie ma wywołań handlowych. **v5 zakończyła się timeoutem; po pojawieniu się
cache wykonano uzasadnioną v6: 12/12 odpowiedzi. Nie ponawiać bez nowej przyczyny.**

```powershell
python research/eia_data_acceptance/probe_ticks.py --out research/eia_data_acceptance/private/ticks-v7
```

`ticks-v1`–`ticks-v6` są zachowanymi dowodami kolejnych kontroli.
Nie nadpisywać ich. Sonda nie uruchamia terminala, nie autoryzuje rachunku,
nie wybiera symbolu automatycznie ani nie wysyła transakcji.
Nie przechodzi do następnej daty po pustej/błędnej próbce.
Proces klienta ma 10 s limitu; terminal może kontynuować synchronizację w tle.
Nawet udana sonda nie certyfikuje mapowania historycznego czasu na UTC.

Offline `analyze_tick_samples.analyze(folder)` ponownie sprawdza hashe i
oblicza metryki z surowych odpowiedzi. `report(result)` renderuje oczyszczony
raport v6. Uruchomienie skryptu przez CLI zapisuje quality.json/READOUT.md
wyłącznie gdy jeszcze nie istnieją; nie nadpisuje dowodów. Bez połączenia MT5.

Źródła, tożsamość rachunku, diagnostyka i ticki pozostają lokalnie w `private/`.
Do repo trafia wyłącznie kod, plan i oczyszczony raport. Nie publikować `.raw`,
baz ani konfiguracji rachunku. Push wymaga odrębnej zgody właściciela.
