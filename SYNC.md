# Synchronizacja i prywatność

Ta kopia nie jest instalacją produkcyjną. Pierwszy push wymaga zgody właściciela
po zapoznaniu się z listą plików i wynikami skanowania. Nie utworzono automatycznej
synchronizacji ani wdrożeń. Oryginalne dowody badań są zachowane poza Git.

## Eksport kolejnej wersji

1. Wykonać `sync_tools/export_project.py --source <lokalny-projekt> --dest <nowy-pusty-katalog> --audit <prywatny-katalog-audytu>`.
2. Przejrzeć różnice eksportu względem repozytorium. Zachować README, SYNC,
   narzędzia skanowania i hooki. Eksporter tworzy materiały do przeglądu, nie
   kompletny release; nie przenosi Git, prywatnego audytu ani autoryzacji.
3. Zaktualizować listę publikowanych plików, testy oraz dokumentację redakcji.
   Nie przywracać automatycznie pominiętych danych/manifestów.
4. Uruchomić skan indeksu i wszystkich lokalnych obiektów Git, także nieosiągalnych:
   `python sync_tools/scan.py --staged --history --deny <prywatna-lista.json>`.
5. Zrobić lokalny commit; przed wysłaniem sprawdzić prywatność zdalnego repozytorium
   i brak nieoczekiwanej historii. Nie używać force-push. Wysyłać tylko przejrzany commit.

## Zakres skanowania

Scanner sprawdza znane formaty tokenów, klucze prywatne, hasła w literałach,
poświadczenia w URL, osobiste e-maile/ścieżki/SID, lokalną listę wartości prywatnych,
zabronione ścieżki, pliki binarne i pliki powyżej 1 MiB. Listę prywatnych wartości
przechowuje się poza repozytorium. Wynik zawiera tylko regułę, plik i numer linii.

Skan jest heurystyczny; nie dowodzi nieobecności nowych lub zakodowanych sekretów.
Przed commitem wykonano również przegląd konfiguracji i podejrzanych identyfikatorów.
Pliki z dowodami zawierające konto, pozycje, transakcje, XML Harmonogramu, logi,
ticki i prywatne JSON nie są publikowane. Duże bazy nie są przeniesione do Git LFS.

Raporty stanowią zredagowane kopie, a nie oryginalne, zapieczętowane dowody.
`SOURCE_MAP.json` opisuje hash źródła i kopii; nie zastępuje lokalnych manifestów
badań. Test konfiguracji slotów korzysta z bezpiecznego szablonu w examples.
Testy CompleteTests jawnie włączają silnik wyłącznie we własnej konfiguracji
symulatora w pamięci; bezpieczna konfiguracja domyślna repozytorium go wyłącza.
Zmieniono wyłącznie kopie: identyfikatory/ścieżki i historyczny domyślny kapitał
opisany w README. Wyniki badań nie były optymalizowane ani przeliczane.

## Lokalne zabezpieczenia Git

Hook pre-commit uruchamia skan. Hook pre-push dodatkowo wymaga lokalnego pliku
`.git/first-push-approved`, który operator tworzy dopiero po zgodzie właściciela.
Plik ten nie jest częścią repozytorium. Hooki są dodatkową kontrolą, można je
technicznie ominąć; nie zastępują świadomego przeglądu ani zgody.

Po świeżym klonowaniu trzeba jawnie ustawić `core.hooksPath=.githooks` oraz
`tradingai.scanPython` na lokalnego Pythona. Opcjonalne `tradingai.denyFile`
wskazuje prywatną listę kontrolną poza repozytorium. Hasła i tokeny nie mogą
trafić do URL remote ani plików projektu; używać systemowego Git Credential Manager.
