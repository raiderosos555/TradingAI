> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Pozostałe ograniczenia i kolejny etap

Etap 1, raport 2026-10-25T07:50:23.638758+00:00. Wyłącznie badanie danych, cen i czasu. Brak zleceń, zmian produkcyjnych, strojenia strategii i pełnego ponownego backtestu. Wszystkie dane historyczne są eksploracyjne.

**Decyzja po pierwszej weryfikacji:** baza do poprawnego rozdzielenia cen jest gotowa i przetestowana. Pełna wiarygodność historycznego backtestu nie została jeszcze osiągnięta.

1. Dostępność: potwierdzona jest jedna godzina ticków na siedmiu rynkach. Nowe odczyty miały timeout; nie wiemy, ile historii broker udostępnia. Kolejna kolekcja powinna zaczynać od jednego krótkiego, znanego okna, ze znacznikiem fazy IPC/odczytu i limitem procesu. Nie restartować DEMO ani terminala dla badania.

2. Czas: +7200 potwierdzone punktowo w dawnych dealach, +3600 obecnie w EA. Trzeba osobno potwierdzić świeże raw ticki względem UTC po otwarciu oraz uzyskać historyczną politykę/dowody DST. Nie rozciągać punktowego dowodu na sześć miesięcy. Akceptowane segmenty UTC pozostają puste.

3. Sesje/świece: wyznaczanie H1/H4/D1 jest przetestowane dla jawnych granic i DST, ale nie potwierdzono historycznych sesji tego brokera. Brak polityki oznacza brak certyfikacji świec i dziennej bazy.

4. Model pozycji: następny etap to kontrolowane testy różnicowe SL/TP, TP1, BE, trailing, freeze, spread, limitów dziennych i rozłączeń względem zamrożonego rzeczywistego Position Managera. Obecne funkcje nie są jego kompletnym zamiennikiem.

5. Koszty: specyfikacja bieżąca nie zastępuje historycznej. Brak potwierdzonego FX, prowizji, swapu/rollover i wykonania zleceń. Nie przyjmujemy automatycznie zerowych kosztów ani starego przelicznika.

6. Briefing: kompletne przyszłe archiwum SHADOW pozostaje kolejnym etapem. Obecny etap nie wdraża automatycznego pobierania ChatGPT ani autoryzacji. W audycie istnieje szkic formatu; docelowy zapis wymaga zachowania pełnej treści, czasu publikacji i pierwszego odbioru, plan_id, poziomów i NO TRADE/HOLD/CANCEL. Nie traktować uciętego archiwum jako kompletnego planu.

Nie optymalizowano parametrów. Ujemny wynik poprawnego modelu będzie prawidłowym wynikiem badania. Po przedstawieniu tego etapu można kontynuować kontrolowane testy zgodności, a dopiero po ich przejściu przeliczyć niezmienione strategie.

## Wersjonowanie i odtworzenie

`config.v1.json` określa zakres próbek i puste listy zweryfikowanych mapowań/kontraktów. `bounded_manifest.v2.json` opisuje ograniczenia pobierania. `stage1_manifest.json` przechowuje SHA-256 kodu, konfiguracji, dowodów i raportów. `production_integrity.json` sprawdza niezmienność kodu/config DEMO, a nie naturalnie aktualizowanych logów/baseline.

Odtworzenie offline: uruchom `analyze_stage1.py`, następnie `report_stage1.py` i testy. Korzysta z kopii ticków w `evidence/` oraz zachowanych artefaktów poprzedniego audytu i manifestu H1. Nie uruchamiaj starego `collect.py` do ponownej kolekcji — pierwsza próba nie miała limitu pojedynczego zapytania. Nowe kolekcje powinny mieć nowy numer wersji i nadzór procesu.

Nie wysłano zleceń. Nie zmieniono Execution Engine, Risk Managera, ustawień terminala, czasu Windows ani konfiguracji działającego DEMO.
