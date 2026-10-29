# Odbiór danych EIA + OIL — 29.10.2026

Kontynuacja zaakceptowanej małej próby. Celem jest kompletność dowodów,
nie pomiar wyniku ani wybór dat po ruchu ceny. Nie zmieniamy DEMO.

Stałe 12 dat:2026-03-04,03-11,03-18,03-25,04-01,04-08,04-15,04-22,
04-29,05-06,05-13,05-20. Tylko małe tabele i metadane; do5MB łącznie.
Ponownie wykorzystujemy wcześniej pobraną tabelę04.03, zachowując jej czas
odbioru i hash. Pozostałe pliki pobieramy po jednym, HTTPS z walidacją TLS.

Dla każdej daty zachowujemy oddzielnie: datę referencyjną, planowany czas
publikacji (America/New_York → UTC przez zoneinfo), rzeczywisty published_at
(NULL bez dowodu), obecny received_at, URL/hash, bieżącą archiwalną wartość
crude ex-SPR, gasoline, distillates i jawnie podaną zmianę tygodniową.
Nie nazywamy aktualnie pobranego archiwum dowodem pierwszego odczytu.

Test jakości: unikalne daty i pola, zgodny tydzień, arytmetyka tabeli,
porównanie wartości za ten sam tydzień w dwóch sąsiednich wydaniach.
Zgodność11 par nie dowodzi niezmienności od publikacji; różnica jest sygnałem
korekty/zmiany definicji wymagającym wyjaśnienia. Nie przepisujemy jej automatycznie.

Do odczytu MT5 przygotowano osobny katalog C:\TradingAI-ResearchMT5,
tryb portable, bez skopiowanych loginów/robotów, Algo/DLL wyłączone.
Po ręcznej autoryzacji sprawdzić ścieżki procesu/danych, serwer DEMO,
tryb tylko odczytu i tożsamość rachunku zgodną z lokalną konfiguracją.
Nie otwierać ani nie zamykać pozycji, nie przenosić kwarantanny.

Najpierw maksymalnie12 zakresów1s, limit10s procesu na żądanie, stop po
błędzie lub niewykonywalnych stronach. Timestamp zwrócony przez API jest
surowym czasem źródła; sam zgodny zakres nie dowodzi mapowania historycznego UTC.
Bez dowodu mapowania nie określamy próbek jako kwotowań w chwili publikacji.
Sonda nie autoryzuje automatycznie dużej kampanii512MiB.

Akceptacja ścisłego replay wymaga każdego elementu dla wszystkich12 zdarzeń:
pierwsza wersja informacji z dowodem dostępności przed decyzją, czas UTC,
pełne okno właściwych Bid/Ask, ich aktualność, specyfikacja i koszty kontraktu.
Brak elementu → NO-GO; żadnego wymyślonego markoutu ani P&L.
