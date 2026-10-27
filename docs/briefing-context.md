> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Briefing jako pomoc w selekcji rynków

Proponowany podział: dane i setup pochodzą z MT5, kalendarz ogranicza moment wejścia,
a wiadomości/briefing wskazują tematy i rynki do obserwacji. Kierunkowy komentarz
nie zastępuje kompletnego setupu, SL, sizingu i kontroli ryzyka.

## Co już działa

- Lokalny poranny/wieczorny raport: struktura, EMA, RSI, MACD, ATR, propozycje z reguł,
  rzeczywiste pozycje, wyniki i decyzje. Godziny: 09:00 / 18:00 Europe/Warsaw podczas
  pracy procesu `run --watch`.
- Kalendarz ekonomiczny odczytywany przez obserwator MT5, prezentowany w raportach
  i sprawdzany przez niezależny Risk Manager.
- Plikowy import kompletnych planów z odrębną autoryzacją. Samo zapisanie analizy
  tekstowej nie autoryzuje zleceń.

## Proponowane rozszerzenie kontekstu wiadomości

Briefing pomocniczy powinien zawierać: czas aktualizacji, źródła, fakty, scenariusze,
instrumenty do obserwacji i warunki, które podważą dany scenariusz. LLM może wyjaśnić
raport MT5 i powiązać informacje. Nie powinien nadawać sobie zgód, zmieniać limitów
ani zastępować brakujących kwotowań. Na początek kontekst nie zwiększa ryzyka i nie
zmienia mechanicznych wejść; wpływ na selekcję można badać osobno na tych samych danych.

Automatyczny strumień wiadomości ani wywołania LLM do generowania komentarza nie
zostały uruchomione. Nie przedstawiamy lokalnego raportu wskaźników jako serwisu newsowego.

## Zapis czatu z aplikacji

23.10.2026 przez obsługiwane narzędzie aplikacji odczytano czat „Wieczorny briefing
rynkowy”. Znaleziono poranny briefing z tej daty, ze stanem analizy 08:57 CEST.
Widoczna decyzja: 0 nowych zleceń / NO TRADE. Wcześniej nie było go w lokalnym inbox.

Dostępny odczyt tej wiadomości ma limit 20 000 znaków i jest oznaczony jako truncated.
Zapisano dokładnie dostępny fragment do `exchange/briefing-archive/2026-10-23-morning.partial.json`
oraz `.md`, z ID źródła i flagą niekompletności. Nie jest to pełny eksport ani plan
przekazany do wykonania. Wewnętrzne znaczniki cytowań pozostają nierozwiązane.

Lokalny silnik Python nadal nie ma połączenia z historią ChatGPT. Jednorazowy odczyt
wykonał agent przez jawne narzędzie aplikacji na prośbę operatora. Nie skonfigurowano
automatycznego pobierania czatów ani wysyłania poleceń do innych rozmów.

Do pełnego przekazania najprościej poprosić źródłowy czat o plik Markdown całego
briefingu oraz osobny JSON według `docs/briefing-contract.md`, a pobrany JSON zapisać
w `exchange/inbox`. Jeśli nie ma nowych zleceń, JSON powinien zawierać `signals: []`.
Nie wolno odtwarzać aktywnych zleceń z historycznych tabel, statusów UNRESOLVED ani
samego biasu. Import nie zastępuje osobnej zgody i niezależnej kontroli ryzyka.
