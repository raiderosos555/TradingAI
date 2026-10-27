> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Recovery v2 — mechanizm i niezmienniki

Dispatcher `supervisor.py` jest krótkim procesem uruchamianym niezależnie przez
Harmonogram. Launcher sam jest procesem silnika. Rejestruje rzeczywisty PID i
Windows creation time, dzięki czemu redirector venv i ponowne użycie PID nie
stają się dowodem obecności starego właściciela. Brak uprawnień do odczytu procesu
oznacza UNKNOWN i zakaz startu, nie domniemaną śmierć.

Oddzielna baza SQLite nadzoru używa WAL i synchronous FULL. Trwały START_RESERVED
powstaje przed Popen. Jeżeli nie wiadomo, czy proces powstał, nadzorca czeka na
rejestrację, a potem przechodzi do interwencji. Nie powtarza niejednoznacznego
startu. Przed startem bada blokady, a launcher i sam runtime ponownie uzyskują
blokady na cały czas pracy. TOCTOU między badaniem a startem nie daje dostępu do
brokera przed uzyskaniem blokad runtime.

Pierwsze uruchomienie ma attempt=0. Po jego zakończeniu nadzorca czeka co najmniej
60 s. Trzy kolejne nieudane restarty mają attempt=1/2/3; następne opóźnienia to
120 i 240 s. Po trzecim nieudanym restarcie stan RETRIES_EXHAUSTED jest trwały.
Wywoływanie dispatchera co minutę może dodać do oczekiwania czas do następnego
triggera; nie skraca minimalnego backoffu. Samo istnienie procesu nie zeruje
licznika. Wymagane jest 300 s postępu RUNNING/WAITING z dowodem czasu, bez STOP
i kwarantanny. Restart nadzorcy nie resetuje licznika ani kolejki oczekiwania.

Postęp jest zapisywany do bazy nadzoru przy wywołaniu status_file, niezależnie od
powodzenia os.replace dla telemetrycznego JSON. Żywy PID bez postępu daje
ALERT_STALLED_NO_REPLACEMENT. Nie ma automatycznego kill. BLOCKED z aktualnym
postępem pozostaje widoczny w zdarzeniach OBSERVE/status; nie jest uznawany za
zdrowe odzyskanie i nie resetuje licznika. Pełne tracebacki wyjątków runtime są
w jego logu, nieobsłużone wyjątki również w console.log launchera i bazie nadzoru.
stdout/stderr każdego uruchomienia są przechwytywane do osobnego pliku. Błędy
dispatchera trafiają do osobnego pliku przy konfiguracji.

DISABLED blokuje uruchomienie. STOP i REVOKED mają nadal dotychczasową semantykę
Risk Managera/runtime; nadzorca ich nie kasuje i nie pisze do journal.sqlite3.
Nie odnawia autoryzacji konta ani okresu DEMO. Dotychczasowe odświeżanie polityki
strategii wewnątrz ważnej autoryzacji runtime pozostaje częścią niezmienionych
reguł; nie jest dodatkową zgodą nadawaną przez nadzorcę.

Synchronizacja po restarcie korzysta z oryginalnego ExecutionEngine.reconcile
przed PositionManagerem. Nie ma nowego kodu wysyłającego zlecenia ani retry dla
INTENT/UNCERTAIN. Nawet odzyskanie procesu nie omija niezgodności brokerowej,
brakującego kontekstu, historycznych problemów kwotowań czy bramek czasu.

Baza i konfiguracja nadzoru nie są źródłem prawdy o transakcjach; pozostają nim
broker i istniejący dziennik. Uszkodzona/brakująca baza nadzoru po instalacji oraz
zmiana przypiętego kodu/configu blokują start. Inicjalizacja nie nadpisuje stanu.
