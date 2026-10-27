# Protokół screeningu v1 — zapisany przed obliczeniem wyników

Badanie wyłącznie eksploracyjne, osiem rodzin, 53 predefiniowane kombinacje
rodzina–instrument. Brak grid search i zmiany parametrów po obejrzeniu wyniku.
Kod `protocol.py` jest konfiguracją wersjonowaną, a wyniki zawierają jej SHA256.

H1: Last z 27.04–23.10.2026; surowa oś brokera. Podział w raw 01.08:
wcześniejszy okres odkrywania i późniejszy test stabilności na również wcześniej
oglądanych danych. Żaden z nich nie jest niezależnym holdoutem.
ATR jest prostą średnią 14 true ranges, EMA inicjalizowana pierwszym close;
120 świec rozgrzewki. Wyjście czasowe po czterech godzinach, sygnał po zamknięciu
świecy, pierwszy następny open służy wyłącznie do markoutu Last.
Nie symulujemy SL, TP ani TP1/BE/trailing na H1. Jednostka **U = ATR14 w cenie**,
nie realne ryzyko zlecenia R. Nie wolno podpisać wyniku jako netto R/P&L.
Zamysł przyszłej reguły: wyjście czasowe 4h, ryzyko zmiany ceny mierzone ATR;
ewentualny SL wymaga nowego, uprzednio zamrożonego protokołu tickowego.

Nie nakładamy zdarzeń w ramach jednej kombinacji. Uwzględniamy tylko ciągłe
cztery godziny, wejścia raw 06..19 i koniec w tej samej raw dobie; brakujące
świece i przejścia doby nie otrzymują interpolowanych cen. To ogranicza, lecz
przy nieznanym UTC NIE dowodzi braku rolloveru. Nie używamy kalendarza/newsów,
których historycznych wersji wtedy nie mamy.

Koszt progowy H1: najwyższy P95 spreadu w trzech dawnych 15-minutowych próbkach
22.10, dzielony przez ATR. To empirycznie oparty scenariusz, nie dowód kosztu
każdej transakcji ani zamiana Last w Bid/Ask. Stres: 2x ten spread + 0.05 U
łącznie na nieskalibrowane prowizje/poślizg. Dodatkowo podajemy surowy ruch przed
progiem. Wynik dodatni nie oznacza wykonania ani zysku po pełnych kosztach.

Ticki 22.10: te same sygnały H1 i horyzont, opóźnienie 250 ms, pierwszy dostępny
poprawny snapshot w ciągu 10 s, wiek obu stron od flag aktualizacji <=10 s.
Zero/crossed quote unieważnia snapshot; po nim wymagane aktualizacje obu stron.
Last-only nie odświeża wieku Bid/Ask. Nie podstawiamy starszej ceny. BUY:
Ask→Bid, SELL: Bid→Ask. Drugi, ustalony z góry odczyt przy opóźnieniu 1000 ms.
Stres: obserwowane strony + 2 punkty poślizgu na stronę + 0.05 U opłat.
Prowizje, swap, FX, marża i faktyczne brokerowe fille nie są znane dla tych
hipotetycznych zdarzeń. To warunkowe markouty wykonalnych stron, nie pełny replay.

Niepewność: 4000 replik bootstrapu pięciodniowych bloków kalendarza dostępnych
sesji, wspólne dni dla instrumentów. 95% przedziały i orientacyjne przedziały
z korektą Bonferroniego na 53 testy. Skrajne kwantyle przy 4000 replik są
niestabilne; nie są certyfikatem istotności, a nieznanej wcześniejszej liczby
prób nie da się nimi naprawić. Dni nie są udowodnionymi niezależnymi obserwacjami.
PF i DD są wyłącznie opisem sekwencji markoutów U; nie krzywą rachunku.

Kandydatura do dalszych badań (nie promocja): dodatnia średnia po progu w obu
okresach, dodatni stres w późniejszym, >=30 zdarzeń w każdym, dodatnia średnia
w co najmniej 60% dostępnych miesięcy. Maksymalnie dwie rodziny spełniające te
warunki, preferowane szersza stabilność między rynkami i mechanizm, nie P&L.
Jeżeli brak — zero kandydatów, bez obniżania progów. Ticki jednej doby są
diagnostyką kosztów, nie kolejnym filtrem dobranym pod najlepszy dzień.

Nowe forward od 26.10 pozostają zarezerwowane dla zamrożonych strategii DEMO.
Audyt integralności może je czytać, ale nie bierze udziału w screeningu.
Nowa hipoteza wymaga własnego protokołu i późniejszej próby rozpoczynającej się
po jej zamrożeniu, jednego końcowego odczytu i uwzględnienia wszystkich testów.
