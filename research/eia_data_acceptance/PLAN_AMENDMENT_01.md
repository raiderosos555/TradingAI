# Korekta warunku dostępu — przed sondą ticks-v4, 29.10.2026

Właściciel nie posiada osobnego hasła inwestorskiego. Ponowna lektura jego
instrukcji wymaga izolowanego, bezpiecznego środowiska i zakazuje transakcji
oraz obciążania aktywnego terminala; nie nakazuje hasła inwestorskiego.
Warunek ten został dodany przez agenta do PLAN.md i niepotrzebnie blokował
wyłącznie odczytowe zapytania. Nie zmieniamy ani nie resetujemy hasła rachunku.

Oryginalny PLAN.md i zapis jego hasha pozostają niezmienione. Ta jawna korekta
dotyczy tylko uprawnień wymaganych do odczytu, przed pierwszym zapytaniem o ticki.
Daty, rozmiary sond, kolejność, limity czasu i kryteria jakości są niezmienione.

Pozostają obowiązkowe: osobny już uruchomiony terminal i katalog portable,
połączenie z dokładnie właściwym DEMO, wyłączone Algo Trading i DLL.
Uprawnienia rachunku do handlu zapisujemy jako metadane. **Nie nazywamy sesji
brokera sesją inwestorską ani rachunkiem bez uprawnień do handlu.**

Sonda wykonuje wyłącznie initialize/shutdown połączenia IPC, terminal_info,
account_info, symbol_info, copy_ticks_range i last_error. Test AST kontroluje
listę bezpośrednich wywołań MT5. Sprawdzono też importowane pomocnicze funkcje:
wykrywają działający proces i odczytują ścieżkę danych aktywnego terminala.
Brak login, order_send, order_check, symbol_select i zmiany konfiguracji.
Test kodu nie stanowi sandboxa ani dowodu blokady dowolnych innych programów;
dotyczy wyłącznie przejrzanej sondy.

Po udanej kontroli uruchomić pojedynczy przebieg ticks-v4, nie nadpisując v1–v3.
Stop po pierwszym błędzie/pustej lub niewykonywalnej próbce. Timeout klienta
nie gwarantuje zatrzymania pobierania w tle przez osobny terminal; nie ponawiać
automatycznie. Bez dużej kampanii, transakcji, zmiany DEMO ani pushu.

Uzupełnienie przed ticks-v5: v4 przeszła kontrolę izolacji/uprawnień, ale
zatrzymał ją własny warunek widoczności OIL w Market Watch. OIL istnieje,
`select=false`. Dokumentacja [copy_ticks_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py)
opisuje żądanie po nazwie symbolu bez wymogu wcześniejszego symbol_select.
Usunięto warunek widoczności; symbol nadal musi istnieć. Nie zmieniamy
Market Watch przez API. v5 będzie pierwszym rzeczywistym żądaniem ticków,
o ile pozostałe warunki przejdą. Błąd API zakończy próbę bez ponawiania.
