# Mały odbiór EIA/OIL

Wynik w [REPORT.md](REPORT.md). Zakres zamrożony w [PLAN.md](PLAN.md).
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

Po ręcznym uruchomieniu osobnego terminala i zalogowaniu inwestorskim:

```powershell
python research/eia_data_acceptance/probe_ticks.py --out research/eia_data_acceptance/private/ticks-v2
```

`ticks-v1` jest zachowanym dowodem odmowy: osobny proces nie działał.
Nie nadpisywać go. Sonda nie uruchamia terminala, nie autoryzuje rachunku,
nie wybiera symbolu automatycznie ani nie wysyła transakcji.
Nie przechodzi do następnej daty po pustej/błędnej próbce.
Proces klienta ma 10 s limitu; terminal może kontynuować synchronizację w tle.
Nawet udana sonda nie certyfikuje mapowania historycznego czasu na UTC.

Źródła, tożsamość rachunku, diagnostyka i ticki pozostają lokalnie w `private/`.
Do repo trafia wyłącznie kod, plan i oczyszczony raport. Nie publikować `.raw`,
baz ani konfiguracji rachunku. Push wymaga odrębnej zgody właściciela.
