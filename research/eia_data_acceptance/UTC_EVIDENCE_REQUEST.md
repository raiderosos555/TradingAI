# Brakujący dowód czasu TMS — treść do ewentualnej konsultacji

Nie wysłano wiadomości. Nie ma potrzeby przekazywania hasła ani historii rachunku.
Potrzebujemy odpowiedzi odnoszącej się konkretnie do OANDA TMS MT5 i OILWTI.pro,
nie do oferty OANDA innego kraju, CSV eksportowanego z GUI ani kalendarza MT5.

1. Czy pola `time` / `time_msc` zwracane przez Python MetaTrader5
   `copy_ticks_range` dla OILWTI.pro w marcu–maju 2026 są epoch UTC, czy
   kodują czas serwera jako pozorny UTC? Czy parametr zapytania ma tę samą oś?
2. Jeśli występuje przesunięcie, prosimy o historyczny harmonogram zmiany
   offsetów i dokładne chwile przejść, szczególnie 8 i 29 marca 2026.
3. Czy polityka dotyczy identycznie ticków, otwarcia świec, historii deals
   oraz kalendarza? Jeżeli nie, prosimy rozdzielić te interfejsy.
4. Czy istnieje przykład ticka z tego okresu z niezależnie potwierdzoną
   godziną UTC lub dokument techniczny, który pozwoli sprawdzić mapowanie?
5. Czy historyczne Bid/Ask/flags zachowują rzeczywiste aktualizacje stron,
   a Last pochodzi z odrębnego strumienia? Jak oznaczane są przerwy i brak kwotowań?

Dowód akceptacji: odpowiedź/dokument z datą, źródłem, zakresem kontraktów i
obowiązywania, sprawdzalny przykład oraz brak sprzeczności z lokalnymi danymi.
Nie wybierać offsetu maksymalizującego reakcję na news lub wynik strategii.

Równoległy brak po stronie EIA: potwierdzenie niezmienności datowanego wydania
albo odtwarzalna historia rewizji, a także faktyczna pierwsza dostępność
informacji. Harmonogram i HTTP Last-Modified nie wystarczają do ścisłego
testu szybkiej reakcji. Alternatywa to prospektywne rejestrowanie pierwszego
odbioru kolejnych wydań z istniejącym forward, według planu ustalonego przed
oglądaniem reakcji. Nie zastępujemy konsensusu tygodniową zmianą zapasów.
