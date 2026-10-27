> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Rzeczywiste pokrycie historii ticków i próba kwietniowa

## Najważniejszy wynik

Zestawienie wszystkich zamrożonych rzeczywistych pobrań z etapów 1–9 zawiera **657 250 rekordów**, ale po uzgodnieniu nakładających się pobrań tylko **634 030 unikalnych rekordów w obrębie instrumentów**. Różnica 23 220 nie jest dodatkową historią. Nie stwierdzono sprzeczności pomiędzy nakładającymi się próbkami.

Żaden z tych wyników nie dowodzi wielomiesięcznego ciągłego pokrycia. Tylko EURUSD ma pobraną i uzgodnioną pełną dobę raw 22.10.2026. Dla pozostałych sześciu instrumentów mamy godzinę raw 22.10.2026 15:00–16:00 oraz krótkie odrębne próbki. Wszystkie przedziały w raporcie i JSON są współrzędnymi raw API; historyczna zgodność z UTC pozostaje niepotwierdzona.

| Symbol | Zapisane rekordy | Po uzgodnieniu powtórzeń | Suma rozłącznych przedziałów udanych żądań |
|---|---:|---:|---|
| EURPLN.pro | 5 217 | 5 217 | 1 godz. 2 min |
| EURUSD.pro | 298 901 | 277 377 | 24 godz. 2 min |
| GBPUSD.pro | 30 892 | 30 892 | 1 godz. 2 min |
| GOLD.pro | 79 080 | 77 384 | 1 godz. 2 min |
| OILWTI.pro | 49 877 | 49 877 | 1 godz. 1 min |
| US100.pro | 102 987 | 102 987 | 1 godz. 1 min |
| US500.pro | 90 107 | 90 107 | 1 godz. 3 min |
| USDPLN — pomocniczy FX | 80 | 80 | 2 min |
| USDPLN.pro — pomocniczy FX | 109 | 109 | 2 min |

Suma czasu żądań nie jest ciągłym zakresem ani certyfikatem kompletności serwera. Dokładne osobne przedziały, pierwsze/ostatnie obserwowane czasy, źródła i SHA-256 zapisano w `coverage_inventory.json`. Wynik obejmuje dane FX, ale nie sumuje jednakowego znacznika czasu różnych instrumentów jako jednej obserwacji.

## Nowa próba i ograniczenie dostępności

Z góry zapisano plan uzupełnienia niesprawdzonych kwietniowych próbek US100, US500, następnie ponowienia OIL. Pierwsze żądanie `US100.pro`, raw 27.04.2026 12:00–12:01, zakończyło się timeoutem po 40,094 s. Import, inicjalizacja, identyfikacja rachunku DEMO i odczyt symbolu powiodły się; ostatnią fazą była `TICKS_START`. Zakończono wyłącznie proces badawczy. Nie restartowano terminala.

Zgodnie z ustalonym limitem serię przerwano. US500 i OIL mają stan `NOT_ATTEMPTED_AFTER_ERROR`, a nie „brak danych”. Wcześniejszy timeout OIL z etapu 3 pozostaje osobnym dowodem. Timeout US100 nie jest pustą odpowiedzią API i nie wyznacza najstarszej dostępnej daty.

Niezależny odczyt nazw i rozmiarów plików cache terminala pokazuje:

- US100: miesięczne pliki `.tkc` od sierpnia do października 2026.
- EURPLN, EURUSD, GBPUSD i OIL: pliki od kwietnia do października 2026.
- GOLD i US500: pliki od października 2025 do października 2026.

To stan katalogu podczas odczytu, nie dowód pełnego pokrycia tych miesięcy. Plików binarnych nie dekodowano i nie użyto jako zastępstwa ticków API. Różnica cache US100 uzasadnia sprawdzenie granicy dostępności w oddzielnym, ograniczonym pomiarze, zamiast zakładania, że ticki obejmują ten sam okres co świece H1.

## Uzgadnianie i kontrola jakości

Moduł `coverage.py` zachowuje kolejność dostawcy i wszystkie rekordy o tym samym milisekundowym czasie, w tym całkowicie identyczne powtórzone wiersze wewnątrz pobrania. Usuwa jedynie wielokrotne liczenie zgodnych danych pobranych ponownie w nakładającym się przedziale.

Wspólne przedziały są sprawdzane w całości: zgodna musi być obecność znaczników czasu, liczba rekordów, ich kolejność oraz wszystkie osiem oryginalnych pól ticka. Brak pojedynczej grupy czasowej, zmiana kolejności albo sprzeczność pustego i niepustego pobrania oznacza konflikt; wtedy licznik uzgodnionych rekordów pozostaje `null`. Nie wybieramy arbitralnie wygodniejszej wersji.

Walidacja odrzuca cofającą się chronologię, niepoprawny Bid/Ask, dane poza żądanym przedziałem i niespójne sekundy/milisekundy. W starych plikach zawierających zarówno czas przeliczony, jak i `broker_raw_time*`, bierze wyłącznie oryginalne kolumny raw. Nie zakłada stałego offsetu i nie sortuje błędnego strumienia. Udane zakresy łączone są tylko wtedy, gdy nachodzą na siebie lub stykają się; dziury pozostają jawne.

## Testy i odtworzenie

12 testów obejmuje identyczne ticki w tej samej milisekundzie, częściowe nakładanie, konflikt kolejności, brak rekordu, pustą odpowiedź, półotwarte granice, przerwy, nieprawidłowe ceny i stare kolumny czasowe. Manifest zawiera konfigurację wersji 1, kod, wynik, fazy nieudanej próby oraz snapshot katalogu cache. Weryfikacja ponownie oblicza cały inwentarz offline i sprawdza niezmienność chronionego kodu DEMO oraz etapów 1–9.

```powershell
# Z katalogu C:\TradingAI; offline, bez połączenia z brokerem:
.\.venv\Scripts\python.exe research/tick_validation/stage10/verify.py
```

## Co nadal blokuje pełny replay

Nie mamy kompletnego tickowego okresu porównawczego dla siedmiu instrumentów, historycznego UTC/DST ani historycznie potwierdzonych warunków kontraktów, konwersji i kosztów. Obecny inwentarz ma zapobiec traktowaniu sumy próbek i powtórnych pobrań jako pełnej historii.

Nie uruchomiono pełnego backtestu, nie optymalizowano parametrów, nie wyliczono nowych metryk rentowności i nie wysłano zleceń. Zebrane wcześniej dane pozostają eksploracyjne. Zegar, kod i konfiguracje działającego DEMO nie zostały zmienione.
