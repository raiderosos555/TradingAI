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

## Weryfikacja publicznych źródeł 29–30.10.2026

Sprawdzono [podręcznik MT5 dla OANDA TMS](https://help.oanda.com/eu/pl/faqs/mt5-user-guide-eu.htm).
Dotyczy właściwej spółki, lecz w odczytanej treści nie znaleziono definicji
historycznych `time_msc` Python ani reguł ich konwersji na UTC. Opis końca
świecy dziennej nie zastępuje takiej definicji.

[Komunikat TMS](https://www.tms.pl/aktualnosci/zmiana-czasu-w-europie-5)
jest indeksowany jako zmiana godzin handlu od 29.03.2026. Bezpośredni odczyt
zwrócił głównie formularz i treści ogólne. Nie uzyskano dowodu semantyki API.
Harmonogram sesji sam nie określa kodowania czasu ticków; nie przyjęto offsetu.

[Dokumentacja OANDA UK](https://www.oanda.com/uk-en/trading/standard-account/differences/)
opisuje zegar MT5 związany z końcem dnia w Nowym Jorku. Dotyczy innej spółki;
nie przenosimy tej reguły na TMS. Nie znaleziono wystarczającego publicznego
potwierdzenia; nie dowiedziono, że nigdzie nie istnieje. Nie powtarzać tych
samych zapytań bez nowego źródła lub odpowiedzi brokera.

Nadal potrzebny jest opis interfejsu od OANDA TMS wraz ze sprawdzalnym
historycznym przykładem. Pytania powyżej pozostają niewysłaną wiadomością;
żadnego kontaktu z brokerem nie wykonano.

Właściciel 29.10 wybrał pozostawienie skryptu EIA bez instalacji
(EIA_PILOT_PLAN.md). Nie jest to oczekiwanie na działający proces:
pilot nie ma zaplanowanego automatycznego wykonania. Nie omijamy decyzji
przez inną usługę, automatyzację ani uruchomienie skryptu w tle.

Brak nowego wyniku strategii. Historyczny replay EIA pozostaje NO-GO z powodu
UTC, dostępności pierwszych publikacji, pełnych okien Bid/Ask i kosztów.
Punktowe próbki ticków ani dzisiejszy plik EIA nie usuwają tych braków.
