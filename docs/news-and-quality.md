> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# News i poprawa jakości strategii

Wdrożono kolektor publicznych RSS: Fed (polityka pieniężna), ECB, EIA oraz BBC World.
Odczyt i status każdego źródła zapisują się lokalnie. Awaria jednego źródła daje PARTIAL,
brak nowych publikacji NO_RECENT_ITEMS, a stary odczyt STALE. Żaden z tych stanów
nie oznacza „rynek bez ryzyka”. Nie omijamy ograniczeń dostawców; niedostępne źródło
pozostaje oznaczone. Zapisujemy tytuł, link i daty; nie kopiujemy pełnych artykułów.

Źródła udostępniają RSS: [Fed](https://www.federalreserve.gov/feeds/feeds.htm),
[ECB](https://www.ecb.europa.eu/home/html/rss.pl.html),
[EIA](https://www.eia.gov/tools/rssfeeds/),
[BBC](https://support.bbc.co.uk/platform/feeds/NewsFeeds.htm).

## Co działa teraz

- Zadanie Windows TradingAI-News odświeża kontekst co 15 minut, niezależnie od MT5.
- `state/news/latest.md` i JSON zawierają najnowszy kontekst oraz dostępność źródeł.
- Raporty i briefingi 09:00/18:00 zawierają tę samą sekcję wiadomości.
- Pierwszy kontekst dostępny przy każdym lokalnym sygnale zostaje zapisany w dzienniku
  jako signal_news_context; późniejsze wiadomości nie nadpisują tego dowodu.
- SQLite zachowuje identyfikatory, wersje tytułów, czas publikacji i pierwszego odczytu;
  kolejne snapshoty są archiwizowane. Deduplikacja nie odmładza starej wiadomości.
- Mapowanie tematów na instrumenty jest jawne i przybliżone. Kierunek pozostaje
  UNDETERMINED: „wyższa inflacja” nie oznacza automatycznie BUY/SELL.
- Tekst wiadomości nie może zmieniać konfiguracji, zgód ani limitów i nie jest wykonywany.

## Etap obserwacyjny i docelowa decyzja

Aktualnie newsy są kontekstem raportowym (SHADOW_CONTEXT); nie zmieniają automatycznie
zleceń. Kalendarz nadal aktywnie blokuje wejścia wokół zaplanowanych publikacji.
Nie ma jeszcze dowodu, że klasyfikacja nagłówków poprawia wynik, więc nie przypisujemy
jej niezweryfikowanej wagi do sygnału.

Docelowo ocena łączy: wydarzenie i jego źródło, wynik względem oczekiwań,
potwierdzoną reakcję ceny, zgodność kierunku na wyższym interwale, strukturę wejścia,
spread/płynność, ryzyko wspólnego portfela. Rozbieżne interpretacje lub brak danych
powinny prowadzić do obserwacji albo blokady wejścia, a nie do zwiększania lota.

Brakuje bezpośrednich feedów NBP i BoE, pełnych wyników spółek, licencjonowanych
depesz o niskim opóźnieniu oraz historycznego archiwum newsów dostępnych w danej chwili.
RSS może dostarczać kontekst do briefingu, ale nie daje gwarancji szybkiej informacji
o nagłym zdarzeniu. Nie zakupiono płatnych usług i nie użyto historii konta ChatGPT.

## Badanie strategii

Uruchomiono rozdzielone warianty breakout_only i false_breakout_only na tych samych
zamrożonych danych, z kosztami. Wyniki są w
`exchange/research/history-20261024/candidates/report.md`. To badanie eksploracyjne:
historia była już oglądana. Warianty nie są automatycznie przenoszone do DEMO.

Oceniamy liczbę transakcji, trafność, PF, średnie R i obsunięcie. Wzrost trafności przy
gorszym wyniku po kosztach nie jest poprawą. Zmiana musi działać w kilku kolejnych
okresach i przejść nowy forward. Historycznych newsów nie wolno odtwarzać dzisiejszymi
artykułami: dostępność to co najmniej max(published_at, first_seen_at).

Kolejne braki z audytu pozostają jawne: portfel z limitem dwóch pozycji i wspólną
ekspozycją, wykonanie na tickach, rzeczywiste historyczne koszty/FX, filtr reakcji po
wydarzeniu, testy wyzwalaczy i restartu MT5. Zapis nocny UTC i DST muszą zostać
potwierdzone podczas rzeczywistych zdarzeń. Ta aktualizacja nie zamyka całego audytu.
