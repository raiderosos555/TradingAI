# Decyzja po odblokowaniu danych i teście COT

**COT w zamrożonej postaci: NO-GO do dalszej promocji. Przewaga po rzeczywistych
kosztach: NIE została wykazana. Nie stroimy filtra do dodatniego wyniku.**

| Pytanie | Odpowiedź oparta na tej rundzie |
|---|---|
| Kilka lat danych odblokowane? | Tak:5010 rekordów COT dla6 kontraktów i po4001 dziennych cen referencyjnych EURUSD/GBPUSD, 2010–2025. Nie:5lat kompletnego brokerowego H1/D1/Bid/Ask z kosztami. |
| Czy COT dodaje informację ponad cenę? | Nie potwierdzono:8 zapisanych prób, wszystkie Holm8=1. W lag14 trzy z czterech delt końcowego okresu są ujemne. |
| Statystycznie obiecujący mechanizm? | Żaden spełniający zapisane kryteria. Zmiana znaku przy lag28 nie upoważnia do wyboru tego wariantu po fakcie. |
| Zaostrzone koszty? | Wszystkie8 wariantów B w końcowym okresie ma ujemną średnią po hipotetycznym obciążeniu stress. Nie sprawdzono rzeczywistych historycznych kosztów TMS. |
| Co blokuje niezależną walidację? | Pełne first-vintage/published_at, dane wykonania CFD i kosztów, mało niezależnych bloków. Właśnie obejrzane okresy nie mogą być ponownie niezależnym potwierdzeniem po tuningu. |
| Zakup danych? | Nie rekomendujemy teraz subskrypcji dla ratowania odrzuconego filtra. EIA i ograniczony test dostępności OIL są możliwe bez nowego zakupu, ale jeszcze niekompletne. |

**Jeden następny krok o największej wartości:** odbiór małego pakietu
**12 EIA first publications + odpowiadające im Bid/Ask OIL**, według
EIA_FEASIBILITY.md. Najpierw12 jednosekundowych sond w odrębnym terminalu
i dowody publikacji/UTC; dopiero potem ograniczone okna. Plan i limit są
gotowe do zatwierdzenia. Nie wykonano tej kampanii i nie zmieniono aktualnego DEMO.

## Co zostało zamknięte

- TLS CFTC działa przez Schannel z pełną walidacją; uzyskano wieloletni
  zbiór, a nie tylko odpowiedź strony. Klasyfikacje i kody są rozdzielone.
- Test COT objął A/B/C/D, chronologię2011–2025, roczne foldy bez retreningu,
  placebo, kontrolę ekspozycji, koszty scenariuszowe, niepewność i Holm8.
- 11 testów mechaniki oraz niezależna walidacja3518 wierszy i hashy PASS.
- 27 chronionych plików silnika/konfiguracji pozostało niezmienionych.
  Kolektor odczytany przy walidacji: COLLECTING, świeży status, zamrożona
  konfiguracja zgodna. Nie zatrzymywano procesów ani archiwizacji.
- W MT5 znaleziono starszy cache; dokładnej przyczyny timeoutów i kompletności
  serwera nie udowodniono. Przygotowana sonda odrzuca aktywny terminal.
- FRED: poprawny endpoint odpowiada; vintage DFII10 blokuje brak klucza API.
  Instrukcja minimalnego odblokowania w HISTORY_ACCESS.md. Drugi eksperyment
  real yields nie został uruchomiony.

## Osobne decyzje

| Obszar | Decyzja | Znaczenie |
|---|---|---|
| Dostęp COT/Fed i odtwarzalna analiza warunkowa | GO | pobrane, zahashowane dane i wykonany test |
| Pełny historyczny backtest point-in-time po kosztach CFD | NO-GO | brak dowodów publikacji/rewizji oraz wykonania |
| Promocja zamrożonego COT | NO-GO | brak wartości dodanej; nie optymalizować dalej |
| Duża kampania EIA/OIL | NO-GO do czasu odbioru małej próby i zgody | istnieje plan i budżet, nie wynik |
| Odporność operacyjna DEMO | nie recertyfikowano | wcześniejsze blokady Recovery/kwarantanna pozostają; ten research ich nie usuwa |

Przygotowano wyłącznie oczyszczony commit lokalny. Push wymaga osobnej zgody
zgodnie z najnowszym załącznikiem. Zgoda na pakiet5MB nie jest zgodą na push,
zmiany operacyjne ani pobranie512MiB ticków.
