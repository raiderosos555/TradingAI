> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Wyniki walidacji — aktualizacja 24.10.2026

Aktualny [audyt projektu](project-audit-20261024.md),
[praca ciągła DEMO](demo-runtime.md) i
[test historyczny 28 przebiegów](../exchange/research/history-20261024/validation/report.md).
Opisy odbioru brokerskiego poniżej dokumentują próby z 23.10; później uruchomiono
oddzielną konfigurację ograniczonego testu DEMO. LIVE pozostaje wyłączony.

## Testy automatyczne

Python 3.12.14, dedykowane środowisko `.venv`:

```text
Ran 168 tests in 12.557s
OK
```

Pełny log: [test-results.txt](test-results.txt). Testy obejmują sześć typów wejść,
zmianę/anulowanie pendingów, BUY/SELL, pełne/częściowe zamknięcia, BE, trailing,
TP1/TP2, STOP, netting/hedging, własność, limity, brokerowe parametry kontraktu,
duplikaty i konflikty, zmianę konta/trybu podczas preflight, restart i blokady
procesów, rozłączenia, utraconą odpowiedź, częściowy fill, aktywację pendingu z luką,
cofnięcie autoryzacji strategii, wskaźniki, generowanie setupów, archiwum, backtest,
harmonogram i eksport. Dodano testy runtime, doby UTC, DST, autoryzacji i weryfikacji
historycznej. Wykonanie zleceń w tych testach korzysta z symulatora.

## Integracja z rzeczywistym terminalem — tylko odczyt

Oficjalny pakiet MetaTrader5 5.0.6231, zweryfikowany rachunek DEMO.
`tools/validate_mt5.py` ma wyłączoną metodę wysyłania zleceń.

- 49 serii OHLCV: 7 kontraktów × M1/M5/M15/M30/H1/H4/D1, po 200 świec.
- Ticki wszystkich 7 kontraktów, archiwum po 1200 świec H1 dla każdego.
- Analiza 7/7 w końcowym przebiegu. Starszy tick jest odrzucany, nie odmładzany.
- 7 wywołań `order_check`: wszystkie retcode 0.
- 0 pozycji przed i po; 0 wysłanych zleceń.
- Odczyt historii, zleceń, equity, depozytu i rzeczywistych parametrów kontraktów.

Dowód: [mt5-readonly-validation.json](mt5-readonly-validation.json).
`order_check` nie jest testem rzeczywistej realizacji zlecenia.

## Obserwator MQL5

Kompilacja: 0 błędów, 0 ostrzeżeń. Po podłączeniu poprawionej wersji przez operatora:
9 poprawnych i aktualnych JSON, 9 PNG (jeden obejrzany), 174 obiekty graficzne.
Zarejestrowano `server_minus_gmt_seconds=7200`, zgodne z korektą adaptera.
Na wykresach nie było dołączonych wskaźników: nie potwierdzono rzeczywistego odczytu
buforów niestandardowego wskaźnika, choć kod eksportu jest skompilowany.
Dowód: [observer-validation.json](observer-validation.json).

## Pierwotny replay strategii (23.10)

Wykonano 14 przebiegów: 7 instrumentów, po 1200 rzeczywistych świec H1, dwa scenariusze
kosztów. To badanie działania pipeline i wrażliwości na koszty. Prowizja/swap są
ilustracyjne, spread jest stały, historyczne FX niezweryfikowane. W wielu scenariuszach
wynik jest ujemny; OIL nie otworzył transakcji. **Rentowność nie została potwierdzona.**
Podsumowanie: [strategy-validation.json](strategy-validation.json); pełne transakcje
i krzywe: `exchange/backtests/`. Nie są to dane z rzeczywistego handlu.

## Uruchomienie całego procesu

Wykonano pojedynczy cykl z rzeczywistym MT5 w DRY_RUN oraz wygenerowano briefing
poranny i wieczorny. Nie było kompletnego setupu lokalnej strategii; brak dyspozycji
jest poprawnym rezultatem. Raporty zawierają stan brokera i eksport obserwatora.

## Rzeczywisty odbiór DEMO

Po zgodzie operatora na samodzielne testy DEMO wykonano 16 dyspozycji, wszystkie
ostatecznie CONFIRMED i z retcode 10009. Dowód: [demo-validation.json](demo-validation.json).

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

BUY LIMIT wykrył brokerowe zaokrąglenie terminu: żądano 1792784829 UTC, broker zapisał
1792784820. Początkowo uruchomiono kwarantannę i nie powtórzono zlecenia. Po dodaniu
kontroli dokładnego terminu lub wcześniejszego początku tej samej minuty, testach
regresji i ponownym odczycie stanu uzgodniono przyjęcie oraz anulowano istniejące
zlecenie. Przedłużenie ważności i inne zmiany nadal są odrzucane. Nie skasowano audytu.

Po odbiorze 23.10 główna konfiguracja i konfiguracje prób wróciły do DRY_RUN, wszystkie symbole były
wyłączone do aktywnych wejść, LIVE wyłączony. Wtedy nie działał stały proces.
Zgoda na autonomiczne testy DEMO jest zapisana; nie wymaga ponawiania w tym zakresie.

## Granice dowodu

Netting, cenowe wyzwalacze BE/trailing/TP1/TP2, luki, rozłączenia i awarie są pokryte
testami symulacyjnymi. Nie potwierdzono wszystkich tych scenariuszy na realnym
terminalu; nie restartowano fizycznie MT5 z aktywną pozycją. Potwierdzono restart
procesu Python i odzyskanie pozycji. Testy nie potwierdzają rentowności strategii.
LIVE nie był aktywowany. Historyczne koszty i pełny strumień newsów pozostają poza
potwierdzonym zakresem; briefing wykorzystuje dane MT5, kalendarz i jawny import.

## Rozszerzenie kalendarza i dostęp do briefingu

Dodatkowe 22 testy obejmują okna przed/po publikacji, zdarzenia bez dokładnej godziny,
pokrycie walut/czasu, stare/niekompletne dane, blokadę wejścia i przyszłego pendingu,
anulowanie własnego pendingu oraz zachowanie możliwości ochronnego zamknięcia.
Obserwator 1.10 skompilowano bez błędów/ostrzeżeń i przeładowano w MT5. Kalendarz
rzeczywistego terminala ma status READY; dowód w `calendar-validation.json`.

Przez narzędzie aplikacji znaleziono dzisiejszy poranny briefing w czacie „Wieczorny
briefing rynkowy”. Odczyt jest obcięty do 20 000 znaków, zapisany jako fragment w
`exchange/briefing-archive`; nie zaimportowano planów transakcyjnych. Widoczna decyzja
źródła to NO TRADE / 0 nowych zleceń. Nie włączono automatycznej synchronizacji czatów.

## Audyt poślizgu zamknięć

Dodano siedem testów: niekorzystny poślizg przy zamykaniu BUY i SELL, częściowe
zamknięcie, dopuszczalna granica, korzystna cena, błędny kierunek w historii oraz
zachowanie pierwotnego limitu wejścia po zmianie konfiguracji. Cena odniesienia i
limit w jednostkach ceny są zapisane w zamiarze przed wysłaniem. Przekroczenie przy
zamknięciu oznacza UNCERTAIN i kwarantannę, nawet gdy broker potwierdza brak pozycji;
nie próbuje się ponownie zamknąć już zamkniętej pozycji. Testy używają symulatora.

## Alternatywny pierwszy test US500

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]