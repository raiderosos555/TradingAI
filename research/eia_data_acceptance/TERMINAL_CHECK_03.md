# Kontrola po wyłączeniu Algo Trading — 29.10.2026

Uzupełnia TERMINAL_CHECK_02.md. Prywatne dowody: `ticks-v3/summary.json`
i `ticks-v3/permissions.json`; poprzednich prób nie nadpisano.

Izolacja procesu, danych oraz tożsamość DEMO nadal PASS. Teraz
`terminal.trade_allowed=false`, `terminal.dlls_allowed=false`.
Jednak `account.trade_allowed=true` i `account.trade_expert=true`:
nie potwierdzono połączenia tylko do odczytu. Sonda zatrzymana przed
żądaniem ticków, 0 historycznych zapytań w tej próbie.

Odczyt dziennika terminala badawczego wykazał autoryzację i włączenie handlu
na rachunku DEMO, następnie wyłączenie Algo Trading. W sprawdzonym zapisie
nie było kolejnej autoryzacji inwestorskiej. Nie uznajemy deklaracji logowania
za dowód zmiany uprawnień, gdy API nadal wykazuje prawo do handlu.

[Dokumentacja MetaQuotes](https://www.mql5.com/en/docs/runtime/tradepermission)
rozróżnia wyłączenie automatycznego handlu w terminalu od prawa rachunku do
handlu. Opisuje `ACCOUNT_TRADE_ALLOWED=false` między innymi dla połączenia
hasłem inwestorskim. Sam przycisk Algo Trading nie przełącza sesji w ten tryb.

Poproszono właściciela o ponowne logowanie osobnym hasłem inwestorskim lub
informację, że go nie posiada; bez przekazywania hasła w czacie. Do czasu
potwierdzenia uprawnień sonda pozostaje zablokowana zgodnie z PLAN.md.
Nie zmieniono DEMO, nie wysłano zleceń, nie uruchomiono dużego pobrania.

**NO-GO dla pobrania sondy przy obecnych uprawnieniach.** Nie dowodzi to braku
historycznych ticków u brokera. Ocena danych EIA i brak potwierdzonej przewagi
pozostają bez zmian. Następną uzasadnioną próbę zapisać w nowym katalogu.
