# Walidacja tej rundy

- 7 testów automatycznych: PASS. Kontrolowane sztuczne fixtures sprawdzają
  wyłącznie kod; nie są danymi ani wynikami badań rynku.
- Weryfikacja 21 plików OHLC i źródła kosztu po SHA256: PASS.
- Weryfikacja 822 zapisanych zdarzeń: kolejność czasowa, rozłączne ekspozycje
  wewnątrz relacji, granica podpróby, cena wejścia/wyjścia, dwie nogi pary,
  koszt progu i gorszy stress: PASS.
- Hashe kodu eksperymentu, parametrów i rejestru zgodne z pierwszym uruchomieniem.
  Nie zmieniono parametrów po wyniku i nie powtarzano ekranu w poszukiwaniu zysku.
- 27 chronionych plików aktywnego kodu/konfiguracji niezmienionych względem
  migawki audytu. Zero zleceń w ramach tego zadania. Odczyt brokera tylko read-only.
- Pełne wyniki, wersje Python/NumPy i hashe lokalnie zachowane. Raporty pokazują
  wszystkie 13 relacji i 4 agregaty, benchmarki, placebo i wielokrotność.

Znalezioną przy przeglądzie degenerację bootstrapu przy jednym bloku oznaczono
w raporcie jako brak interpretowalnego CI; wynik źródłowy zachowano. P dla mniej
niż dwóch bloków jest konserwatywnie ustawione na 1. Mała liczba pozostałych
bloków nadal ogranicza wiarygodność inferencji.

To walidacja obliczeń eksploracyjnych. Nie potwierdza historycznego UTC, jakości
wykonania, kosztów, kompletności feedu, niezależności próby ani przewagi.

Publikacja obejmuje wyłącznie Markdown i Python z tego katalogu. Dane wejściowe,
per-event JSON, SQLite, tożsamość rachunku, konfiguracje DEMO i runtime są
wykluczone. Przed commitem/pushem obowiązuje istniejący skan indexu i całej
lokalnej historii Git z prywatną deny-listą. Skan heurystyczny nie stanowi
matematycznego dowodu braku dowolnie zakodowanego sekretu.
