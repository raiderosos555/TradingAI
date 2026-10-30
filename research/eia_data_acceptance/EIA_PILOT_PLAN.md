# Gotowy jednorazowy odbiór przyszłego EIA — bez instalacji

Skrypt `capture_eia.py` jest gotowy i sprawdzony na rzeczywistej tabeli EIA
6599 B. Wynik testu oznaczono CALIBRATION, nie FORWARD. Każda próba zachowuje
treść, SHA256, początek żądania, granicę odbioru i czas zakończenia walidacji.
Przed walidacją dane nie są dostępne dla hipotetycznej decyzji. Zachowujemy
`published_at=null`, `first_print_verified=false`, `orders_authorized=false`.
Skok zegara, HTTP error, niewłaściwy tydzień lub błędna arytmetyka blokują
użycie próbki. Nie ma fallbacku do poprzedniej poprawnej wersji.

## Przygotowany zakres — nieuruchomiony

- Jedno nowe zadanie Windows: `TradingAI-EIA-20261104-Shadow`.
- **4 listopada 2026, 16:25–17:05 Europe/Warsaw** (15:25–16:05 UTC).
- Planowa publikacja 16:30 czasu Warszawy, 10:30 America/New_York;
  [harmonogram EIA](https://www.eia.gov/petroleum/supply/weekly/schedule.php).
- 40 prób co minutę od 16:25 do 17:04; tylko table1.csv z ir.eia.gov.
- Maksymalnie 64 KiB treści na żądanie, 2,5 MiB łącznie, bez opłat.
  Nagłówki/transport HTTPS nie są w tej sumie. Typowa obecna tabela ma 6599 B.
- Żadnego MT5, transakcji, analizy cen, zmiany DEMO, Risk Managera ani
  istniejących zadań/kolektora. Osobny katalog prywatny poza zamrożonym cohortem.
- Tylko jedno wykonanie; blokada duplikatu, brak automatycznego ponawiania
  po awarii. Spóźnione sloty są pomijane, nie odtwarzane późniejszymi danymi.
- Komputer musi być włączony, użytkownik zalogowany i internet dostępny.
  Zadanie nie budzi komputera i nie uruchamia się po terminie jako backfill.
- Plan `eia_pilot_20261104.json` zapisano przed wydarzeniem. To odbiór źródła,
  nie potwierdzająca próba strategii i nie dowód pierwszej globalnej publikacji.

Przygotowany instalator: `install_eia_pilot.ps1`. Zgodnie z decyzją właściciela pozostaje nieuruchomiony. Skrypt nie nadpisuje istniejącego
zadania, sprawdza lokalną strefę i termin, używa ograniczonych uprawnień
interaktywnego użytkownika bez przechowywania hasła. Nie został uruchomiony.

## Co dzięki temu będzie można sprawdzić

Czy mamy poprawną nową wartość actual przed potencjalną decyzją, kiedy nasz
system faktycznie ją poznał, jakie było opóźnienie obserwacji względem
harmonogramu i czy kolejne odpowiedzi zmieniały treść. Zapisujemy również
błędy i brak aktualizacji. Odstęp minutowy daje czas pierwszego *zaobserwowania*
z dokładnością do dostępnych prób, nie tickową rekonstrukcję publikacji.

Po odbiorze będzie można zaplanować mały replay z istniejącymi kwotowaniami
forward, jeśli ich UTC, kompletność i koszty zostaną potwierdzone. Bez tych
warunków nie liczymy wiarygodnego P&L. Jeden event nadal nie dowodzi edge.

## Stan

Kod i kontrolowany odczyt: GO. Instalacja: **NIE WYKONANA**.

Decyzja właściciela z 29.10.2026: „Pozostaw gotowy skrypt bez instalacji”.
Potwierdzono brak zadania `TradingAI-EIA-20261104-Shadow` w Harmonogramie.
Nie oczekujemy teraz zgody na instalację; skrypt pozostaje przygotowany.
Zaplanowany w pliku odbiór 4 listopada nie uruchomi się automatycznie.
Zamrożony protokół JSON pozostaje bez zmian; powyższa decyzja dokumentuje
stan wdrożenia, nie zmienia reguł badania.
