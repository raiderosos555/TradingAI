> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Odtworzenie testów bez handlu

Pełny lokalny materiał znajduje się w katalogu badania. GitHub zawiera kopię
oczyszczoną; prywatne konfiguracje i surowe dowody są pominięte. Nie traktować
brakujących plików jako dowodu PASS. Testy wymagają Windows i dostępności kopii
konfiguracji używanych przez fixture; nigdy nie zastępować ich LIVE.

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s research/demo_recovery_v2 -p test_supervisor.py -v
```

16 testów uruchamia rzeczywisty launcher i silniki w pamięci, w katalogach
TemporaryDirectory. LAB zabrania importu MetaTrader5. Kończenie procesu dotyczy
wyłącznie procesu zarejestrowanego w bazie tego testu, ze zgodnym creation time.
Nie dotyka procesu aktywnego DEMO. Skrócone opóźnienia 0,15/0,3/0,6 s służą tej
serii; oddzielna próba Harmonogramu używa pełnych 60/120/240 s.

Próbę Harmonogramu należy prowadzić w nowej kopii katalogu dowodów i z nowymi
nazwami LAB; nie nadpisywać zapieczętowanych wyników. `install_lab.ps1` tworzy
tylko `TradingAI-Lab-RecoveryV2-crash` i `TradingAI-Lab-RecoveryV2-healthy`.
`scheduler_watch.py` obserwuje je lokalnie, a `finish_lab.ps1` usuwa tylko te dwa
zadania po potwierdzeniu ich akcji. Nigdy nie używać instalatora produkcyjnego
do testów mechaniki.

Pierwsza seria ujawniła niezamykanie połączenia SQLite po initialize, co na
Windows blokowało sprzątanie katalogu fixture. Połączenie jest teraz jawnie
zamykane. Wynik początkowy zachowano, a serię ponowiono. Popen pozostaje
przechowywany do odczytu zakończenia, bez blokowania dispatchera na czas życia
silnika; po tej korekcie ponowiono całą serię 16 testów.

Fizyczny restart Windows nie został wykonany. Test śmierci właściciela i nowego
procesu nadzorcy sprawdza odtworzenie trwałego stanu, a nie MT5 po restarcie OS.
Nie przeprowadzano destrukcyjnego testu odłączenia zasilania ani korupcji dysku.

Regresja 186 testów rdzenia używa `candidate/` na początku sys.path, z asercją
pochodzenia modułu runtime. Nie zmieniono aktywnego kodu, parametrów strategii,
limitu pozycji, ryzyka ani autoryzacji. Wersje kodu i dowodów identyfikuje manifest.
