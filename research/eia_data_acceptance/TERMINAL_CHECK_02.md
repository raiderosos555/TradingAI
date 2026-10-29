# Ponowna kontrola terminala badawczego — 29.10.2026

Uzupełnienie REPORT.md po potwierdzeniu przez właściciela, że drugie okno
pozostaje otwarte. Dowody poprzedniej próby `ticks-v1` zachowane.

## Co odblokowano

Kontrola `ticks-v2` potwierdziła:

- oddzielny uruchomiony proces terminala badawczego;
- oddzielny katalog danych portable;
- połączenie z tym samym rachunkiem DEMO i serwerem co w lokalnej konfiguracji;
- wyłączone DLL.

## Dlaczego sonda nie pobrała ticków

API zwróciło `terminal.trade_allowed=true`, `account.trade_allowed=true`
i `account.trade_expert=true`. Zatem warunek wyłączonego Algo Trading oraz
rachunku tylko do odczytu nie jest spełniony. Nie rozstrzygamy, jakiego hasła
użyto — oceniamy rzeczywiste uprawnienia zwrócone przez terminal.

Sonda zatrzymała się w kontroli uprawnień przed `copy_ticks_range`.
W tej próbie wykonano **0 żądań historycznych ticków**. Nie jest to wynik
negatywny dostępności historii OIL u brokera. Nie wysyłano zleceń ani nie
zmieniano ustawień terminali. Diagnostyka IPC dotyczyła wyłącznie terminala
badawczego; zapisano osobno kontrolę uprawnień bez danych identyfikujących konto.

Właściciel otrzymał prośbę o wyłączenie Algo Trading i ponowne zalogowanie
hasłem inwestorskim wyłącznie w oknie badawczym. Nie prosić o hasło w czacie.
Po potwierdzeniu powtórzyć tę samą ograniczoną sondę, zachowując `ticks-v2`
i używając nowego katalogu `ticks-v3`. Nie obniżać wymagań uprawnień.

**GO: izolacja procesu/danych oraz zgodność tożsamości DEMO.**
**NO-GO: uprawnienia terminala badawczego, pobranie próbki i pełny replay.**
Pozostałe blokady pierwszej publikacji EIA, historycznego UTC, aktualności
Bid/Ask i kosztów opisane w REPORT.md pozostają. Nie przeprowadzono nowego
testu strategii ani nie zmieniono wniosku o braku potwierdzonej przewagi.
