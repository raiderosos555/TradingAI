> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Kalendarz ekonomiczny MT5

Źródło: oficjalne funkcje MQL5 `CalendarValueHistory` i `CalendarEventById`.
TradingAIObserver 1.10 eksportuje USD, EUR, GBP i PLN co 300 sekund, od doby wstecz
do siedmiu dni naprzód. Nie wysyła dyspozycji i nie wymaga DLL ani klucza płatnego API.
W obecnym terminalu odczyt został potwierdzony po przeładowaniu EA przez operatora.

```powershell
Set-Location C:\TradingAI
.\.venv\Scripts\python.exe -m trading_ai --config config.local.json calendar
```

Eksport terminala: `MQL5/Files/TradingAI/calendar_<login>.json`.
Raport czytelny dla operatora: `exchange/economic-calendar.json` oraz sekcja każdego
raportu JSON/Markdown. Zawiera terminy w czasie Warszawy, nazwę, walutę, wagę,
aktualną/poprzednią wartość, prognozę oraz jednostkę/mnożnik w JSON. Puste wartości
nie są zamieniane w zera. Waga dostawcy nie przewiduje kierunku ruchu ceny.

## Reguły

W `config.local.json` filtr jest włączony. Domyślnie blokuje nowe wejścia od 30 minut
przed do 15 minut po wydarzeniu o wadze 3. Progi są konfigurowalne w sekcji `calendar`.
Informacja o wydarzeniach o mniejszej wadze nadal jest widoczna w raporcie.

| Instrument | Waluty wydarzeń |
|---|---|
| GOLD, US500, US100, OIL | USD |
| EURUSD | EUR, USD |
| GBPUSD | GBP, USD |
| EURPLN | EUR, PLN |

Nowy pending jest odrzucany również wtedy, gdy jego termin ważności przecina
przyszłe okno wydarzenia. Istniejący własny pending podlega anulowaniu po wejściu
w okno lub utracie wiarygodnego kalendarza. Anulowanie nadal przechodzi normalne
kontrole konta, aktywacji, własności, freeze i order_check. Kalendarz nie wymusza
zamykania istniejących pozycji i nie blokuje z tego powodu ich ochrony/redukcji.

Brak pliku, niepełna odpowiedź API, błędne konto, rozbieżna strefa czasowa, brak
pokrycia walut/zakresu, pusty feed lub wiek powyżej 900 sekund oznaczają UNAVAILABLE
i blokadę nowych wejść. Nie oznaczają braku wydarzeń. Zmiana ustawień kalendarza
unieważnia hash autoryzacji nowych sygnałów lokalnej strategii.

Czasy MQL5 są czasem serwera. Obserwator jawnie przelicza je na UTC i podaje offset,
który musi zgadzać się z adapterem Python. Jeśli godzina publikacji jest nieznana,
blokada obejmuje całą datę serwera, wraz z oknami ochronnymi.

Kalendarz nie obejmuje wszystkich nagłych wiadomości, geopolityki, niespodziewanych
wypowiedzi ani zmian płynności. Dla OIL samo mapowanie USD nie jest pełnym modelem
ryzyka ropy. Na tej podstawie nie zwiększamy wolumenu ani nie tworzymy kierunku BUY/SELL.

Dokumentacja: [CalendarValueHistory](https://www.mql5.com/en/docs/calendar/calendarvaluehistory),
[struktury kalendarza](https://www.mql5.com/en/docs/constants/structures/mqlcalendar).
