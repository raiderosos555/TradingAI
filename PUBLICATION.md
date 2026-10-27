# Kontrola przed pierwszą publikacją — 27.10.2026

Cel: prywatny przegląd kodu i raportów, bez dostępu do rachunku i bez wdrożenia.
Repozytorium docelowe zweryfikowano przez połączenie GitHub jako prywatne, dostępne
do zapisu, z pustą listą gałęzi. W instalacji źródłowej nie było repozytorium Git.
Lokalny checkout publikacyjny ma remote `origin` i gałąź `main`.

## Wykluczenia

- Stan i bazy runtime: około 2,53 GB, w tym baza rynku około 2,25 GB.
- `docs.zip`: około 493 MB; środowisko `.venv`: około 67 MB.
- Exchange: około 69 MB. Badania lokalne: około 126 MB; eksport obejmuje tylko
  dozwolone źródła i zredagowane raporty, bez surowych danych.
- Hasła/tokeny/`.env`, prywatne konfiguracje i autoryzacje, numery rachunku,
  dziennik transakcji, paczki cohort, XML zadań, logi i pliki binarne.

Rozmiary są przybliżeniem jednego odczytu; archiwizacja nadal zwiększa lokalne bazy.
Nie zainstalowano Git LFS ani nie dodano dużych plików.

## Kontrole

- Skan 351 tekstowych plików źródłowych i konfiguracji; znane wzorce haseł,
  tokenów i kluczy nie dały trafień. Wykryto lokalne ścieżki użytkownika i identyfikatory terminala.
- Dane konta i autoryzacji wykryto w konfiguracji i usunięto z eksportu.
  Dodatkowy przegląd usunął tabele z numerami i wynikami rzeczywistych transakcji.
- Indeks Git i wszystkie lokalne obiekty, także nieosiągalne, są sprawdzane
  przed commitem. Lokalna lista prywatnych wartości jest poza repozytorium.
- **186 testów rdzenia przeszło offline** w kopii. Nie użyto połączenia MT5 ani
  nie uruchomiono narzędzi wdrożeniowych, handlowych lub instalujących zadania.
- Źródła aktywnego silnika, konfiguracje i źródła kolektora nie zostały zmienione.

## Granice i pozostałe ryzyka

Skan heurystyczny nie gwarantuje wykrycia każdego możliwego sekretu. Raporty
zostały zredagowane; nie są pełnym, samowystarczalnym archiwum reprodukcji badań.
Brak prywatnych danych i oryginalnych manifestów jest zamierzony. Nie uruchamiano
ponownie pełnych badań ani testów awarii Harmonogramu podczas przygotowania Git.

Lokalny Git Credential Manager nie ma jeszcze uwierzytelnienia do tego repozytorium.
Dostęp przez aplikację jest potwierdzony; nie skopiowano z niej tokenów. Przed
standardowym `git push` potrzebne będzie normalne logowanie GitHub przez Credential
Manager. Nie wpisywać tokenów w pliki ani w remote URL.

Pierwszy push pozostaje zablokowany do zgody właściciela. GitHub nie będzie
automatycznie aktualizowany; każda następna kopia wymaga eksportu i przeglądu.
Żadna kontrola publikacji nie potwierdza przewagi inwestycyjnej.
