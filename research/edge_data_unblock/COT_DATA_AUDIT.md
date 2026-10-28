# COT i ceny: audyt danych, 29.10.2026

**Odblokowano 5010 rekordów COT z lat 2010–2025, sześć kontraktów; nie certyfikowano first-vintage.**

## Transport i rozmiar

Python urllib/OpenSSL ponownie zatrzymał się na handshake TLS (10 s); w poprzedniej rundzie występował też błąd certyfikatu. Ten sam mały URL przez Windows curl/Schannel zwrócił HTTP200, ssl_verify_result=0. Nie wyłączano TLS, walidacji certyfikatu ani revocation. Wybrano działający stos systemowy, bez zmian globalnego trust store. Dokładna pierwotna przyczyna łańcucha certyfikatów/transportu OpenSSL pozostaje nierozstrzygnięta.

Zatwierdzony limit 5 000 000 B: zużyto **4 492 081 B**, wliczając 1 MB uciętego HTML i błędne próby formatu. Ucięty HTML, puste odpowiedzi HTTP200 i strona formularza nie są używane jako ceny. Poprawne kompletne HTML zweryfikowano przed parsowaniem. Końcowy skrypt pobiera bezpośrednio działający format.

[Oficjalny ZIP TFF 2024](https://www.cftc.gov/files/dea/history/fut_fin_txt_2024.zip): HEAD HTTP200, Content-Length=563591 B. Pierwszy HEAD zgłosił curl63 z powodu limitu 16384 B porównanego z Content-Length; nie był to błąd TLS. Treści ZIP nie pobrano, bo po diagnostyce zostało 507919 B zatwierdzonego budżetu. Schemat zweryfikowano na prawidłowym API; zgodności wszystkich rekordów API z ZIP nie deklarujemy.

## Mapowanie i pokrycie

| Rynek | Kod | Klasyfikacja | Rekordy | Pierwsza–ostatnia data pozycji | Największy odstęp dni |
|---|---|---|---:|---|---:|
| GOLD | 088691 | Disaggregated / managed money | 835 | 2010-01-05 – 2025-12-30 | 8 |
| OIL WTI | 067651 | Disaggregated / managed money | 835 | 2010-01-05 – 2025-12-30 | 8 |
| US500 | 13874A | TFF / leveraged funds | 835 | 2010-01-05 – 2025-12-30 | 8 |
| US100 | 209742 | TFF / leveraged funds | 835 | 2010-01-05 – 2025-12-30 | 8 |
| EURUSD | 099741 | TFF / leveraged funds | 835 | 2010-01-05 – 2025-12-30 | 8 |
| GBPUSD | 096742 | TFF / leveraged funds | 835 | 2010-01-05 – 2025-12-30 | 8 |

API: [TFF futures-only](https://publicreporting.cftc.gov/resource/gpe5-46if.json) i [Disaggregated futures-only](https://publicreporting.cftc.gov/resource/72hh-3qpy.json). Ograniczono projekcję do daty, kodu, OI, long, short i FutOnly. Sortowanie po kodzie i dacie, limit4000 na zbiór; odpowiedzi poniżej limitu. Unikalne pary kod–data; dodatnie OI, 0≤long/short≤OI. Nie zmieszano futures z combined, TFF z Disaggregated ani z Legacy.

GOLD=COMEX Gold, OIL=NYMEX WTI physical, nie Brent. US500=E-mini S&P500, US100=Nasdaq mini; nie sklejamy kodów z consolidated 13874+/20974+. Nazwa GBP zmieniła się w 2022, kod pozostał ten sam. EURPLN nie ma w tym zbiorze bezpośredniego odpowiednika. COT to agregat pozycji we wszystkich terminach kontraktu, nie cena kontraktu wykonania.

Pobranie nie dowodzi ciągłości klasyfikacji każdego tradera: [CFTC wyjaśnia zmiany Form40 i klasyfikacji](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm). Dlatego zmiana netto nie jest czystym przepływem transakcyjnym.

## Dostępność informacji

Normalny harmonogram: wtorkowe pozycje publikowane w piątek o15:30 America/New_York; święta mogą przesuwać termin. [CFTC schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm). Daty pozycji zachowano również wtedy, gdy są poniedziałkowe. API nie dostarcza dla każdego rekordu historycznego published_at/received_at ani pełnego zestawu rewizji.

Reguła użycia w eksperymencie: po14 dniach od daty pozycji (kontrola28), wyłączenie całych pięcioraportowych okien dotykających zakłóceń. To konserwatywne **założenie**, nie udowodniony najwcześniejszy czas użycia. Bez release evidence najwcześniejszy czas faktycznie udowodniony dla pobranej wersji to jej obecny odbiór zapisany w manifeście. Żadna obserwacja nie wchodzi w decyzję we wtorek jej pomiaru.

Wyłączenia obejmują [shutdown2013](https://www.cftc.gov/PressRoom/PressReleases/6745-13), [catch-up2019](https://www.cftc.gov/PressRoom/PressReleases/7864-19), [incydent ION2023](https://www.cftc.gov/PressRoom/PressReleases/8655-23) i zaległości2025 z [oficjalnych komunikatów](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm). Dokładne konserwatywne maski w zamrożonym protokole. Historyczne TFF sprzed2010 zostały opublikowane retrospektywnie; test zaczyna decyzje w2011, nie w2006.

Nie wykonano vintage replay. Znane korekty/reklasyfikacje pozostają istotną niepewnością. [Warunki CFTC](https://www.cftc.gov/sites/default/files/cftc/cftcprivacy.htm): dane urzędowe public domain, z podaniem źródła; nie publikujemy surowego pakietu.

## Faktyczna próbka cen FX

| Rynek | Poprawne obserwacje 2010–2025 | Pierwsza–ostatnia | ND, bez imputacji |
|---|---:|---|---:|
| EURUSD | 4001 | 2010-01-04 – 2025-12-31 | 173 |
| GBPUSD | 4001 | 2010-01-04 – 2025-12-31 | 173 |

Brak weekendów jest cechą kalendarza H.10; ND nie zastąpiono kursem poprzedniego dnia. Do porównania wymagane są rzeczywiste referencje w obu datach. Najstarsze surowe strony zawierają2000–2026, ale filtr analityczny dopuszcza wyłącznie2010–2025. Ceny i daty Fed nie są cenami ani godzinami realizacji CFD TMS.

## Powtarzalność

Protokół SHA256: `b2c4254a66180a92714cb44ee575e5ef6e8a48c60c22d0edfb108d8f8f1eb949`. Kod obliczeń SHA256: `1223b8d7de895b362b9622860a682ccd68f8b5acf773e91dc149e10aaac3d100`. Manifesty URL/odbiór/rozmiar/SHA256 oraz pełne odrzucenia są lokalnie w private/. Poniżej hashe właściwych wejść:

| Plik wejściowy | SHA256 |
|---|---|
| tff.raw | `e8c5f9e91d6ba9703dceac7e4f9ef723ad4a54a92be4284fcadd3149b1def1f3` |
| disagg.raw | `ce5a93c0fa60cfb7e831f7dea302440433228f0eb4ed4da26b0cf1a9f46fef7d` |
| fed_eur_complete.raw | `63c83d3633b12eb2b32f8a23e3dd0ba4d548ea2c80fc3f71d4bf73fd9b0c0b31` |
| fed_gbp_complete.raw | `5e55d0b7886bcf117eb5369ab761fffe8467a4c0054b8eee3ef642201dc2ce20` |
