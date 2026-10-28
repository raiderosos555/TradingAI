"""Render reviewed aggregates; no model fitting or access to live market data."""
import argparse,json,hashlib
from pathlib import Path
from collections import defaultdict
import experiment as E
import protocol as P


def fmt(x):return 'n/a' if x is None else f'{x:.3f}'
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+
                     ['| '+' | '.join(str(c) for c in row)+' |' for row in rows])


def render(base):
    f=E.read(base/'private/feasibility.json');d=E.read(base/'private/results-v1.json')
    counts={(r['alias'],r['tf']):r for r in f['ohlc']}
    rows=[]
    for name in P.ALIASES:
        rows.append([name,*[counts[name,tf]['n'] for tf in ('H1','H4','D1')],
                     counts[name,'H1']['real_volume_nonzero'],format(d['spread_price_hurdles'][name],'.9g')])
    coverage=table(['Rynek','H1','H4','D1','H1 real_volume >0','Próg spreadu w jednostkach ceny'],rows)
    news=table(['RSS','Liczba','Pierwszy odbiór UTC','Ostatni pierwszy odbiór UTC','Najmniejsze opóźnienie publikacja→odbiór [h]'],
               [[k,v['n'],v['first_seen'],v['last_seen'],fmt(v['first_receipt_lag_hours_min'])] for k,v in f['news'].items()])
    feasibility=f'''# DATA_FEASIBILITY — dane możliwe do uczciwego użycia

Punkt odcięcia audytu: {f['at']}. To migawka, a nie bieżąca liczba danych
rosnącego archiwum. Dane do eksperymentów pobrano wcześniej; nie odpytywano
terminala o nowe ceny na potrzeby selekcji. Źródła przypięto 21 hashami SHA256.

{coverage}

Pełna precyzja małych spreadów jest w INPUT_HASHES.md. H1: raw 27.04.2026
02:00–23.10.2026 22:00 (21 234 świece). H4: raw 24.10.2025 04:00–23.10.2026
20:00. D1: raw 26.10.2025–23.10.2026. Etykiety raw nie są potwierdzonym UTC.
Zapisane pole time z legacy przesunięciem −7200 nie jest używane w eksperymencie.
Nie zakładamy stałego przesunięcia brokera. Różna liczba D1 FX wynika również
z odmiennej budowy tygodnia/sesji; 126 D1 nie jest dokładnie 126 sesjami giełdowymi.

Wszystkie siedem kontraktów ma ustalony wcześniej chart_mode LAST. Nie wolno
przenosić spreadu na Last tak, jakby Last był Bid lub mid. H1/H4/D1 nadają się
do eksploracyjnych testów warunkowego ruchu, nie do deklaracji net execution.
Brak historii korekt/rollowania kontraktów dodatkowo ogranicza długi trend.
Niezerowy real_volume w indeksach i OIL jest polem brokera, bez certyfikacji
pełnego obrotu giełdowego; FX/GOLD mają w tym zbiorze zero. Tick_volume jest
liczbą zmian tickowych, nie wolumenem globalnego rynku lub order flow.

## Ticki, czas i inne interwały

Wcześniejszy audyt ticków 22.10 obejmuje 5 401 052 rekordy z 42 żądanych bloków:
GOLD 977 204; US500 1 393 823; OIL 600 008; EURPLN 94 204;
EURUSD 277 031; GBPUSD 432 782; US100 1 626 000. Chronologia wewnątrz pliku
i przypadki niewykonywalnych kwotowań są zachowane. To jedna doba; nie
powtarzano jej testów ani nie nazywano niezależną walidacją nowych hipotez.
Historyczne offsety i zgodność z feedem decyzji pozostają niezaakceptowane.

Runtime ma również M1/M5/M15/M30, zwykle krótkie paczki 200 świec w kilku
przestrzeniach konfiguracji. Nie sumujemy kolejnych kopii jako niezależnej,
ciągłej historii. Nie ma zatwierdzonego wieloletniego tape M1/M30 do sesyjnej
replikacji S7/S8. H1 relacje wyliczono wyłącznie na wspólnych dokładnych raw
timestampach, bez interpolacji; wspólny stempel nie gwarantuje jednoczesnego
wykonania dwóch kontraktów.

Forward cohort-20261026-v1 pozostaje zastrzeżony. Zakończone okno 27.10 ma
1 600 232 rekordy, 0 błędów hashy wybranych plików i warunkowe pokrycie żądań.
11 globalnych rewizji overlap, niecertyfikowane UTC, różnice historycznego
feedu i ceny decyzji oraz kontekst/wykonanie blokują pełny replay. Zobacz
DEMO_AUDIT_RECEIPT.md. Nie użyto zwrotów z forward do wyboru tych hipotez.

## Makro i informacje dostępne w danej chwili

Archiwum rozpoczęło zbieranie wersji kalendarza 26.10.2026. W migawce audytu:
296 wersji, 207 zdarzeń, 127 z prognozą zaobserwowaną przed planowanym czasem,
5 z jakimkolwiek actual, **0 par prognoza-przed + actual-po**. USD93, EUR103,
GBP11, PLN0. Jednostki występują w 207 rekordach. Pola previous istnieją w
schemacie, ale nie ma zaakceptowanej historii pierwszych publikacji i rewizji
previous/actual. Nie używamy dzisiejszego previous jako wiedzy z przeszłości.
Nawet obecność forecast/actual nie dowodzi prawidłowej latencji i czasu UTC.

**M5/M6 są NIEWERYFIKOWALNE**, nie mają wartości P&L równej zero. Historia
24 wcześniejszych niespodzianek i as-of konsensus są dodatkowymi brakami.

{news}

To tytuł, URL, znaczniki publikacji/odbioru i znormalizowany rekord, nie pełny
historyczny korpus artykułów ani surowe wszystkie wersje RSS. Zero kierunkowych
sygnałów we wszystkich czterech źródłach. Archiwum kontekstu zawiera 100 wersji
newsów w tej migawce; odtworzenie późniejszego nagłówka nie czyni go dostępnym
wcześniej. EIA Today in Energy nie jest taśmą pierwszego inventory actual i
konsensusu. BBC World nie jest precyzyjnym makro wire. Fed/EBC oficjalne
komunikaty nie zastępują historycznych oczekiwań rynku.

Briefing: tylko częściowy poranny zapis 23.10 (JSON i Markdown). Brak pełnego
zbioru przyszłych planów wraz ze wszystkimi NO TRADE/HOLD/CANCEL. Istnienie
kodu archiwizacji nie jest dowodem danych. Briefingi pozostają SHADOW.

## Koszty i klasy dopuszczalnych badań

Trzy 15-minutowe okna 22.10 dostarczają rzeczywistych spreadów, ważonych liczbą
ticków. Największe p95 to jawny próg analityczny, **nie historyczny spread każdej
transakcji**. Wcześniejszy odczyt historii zawiera 27 deal, z zerową prowizją i fee
w tych konkretnych zapisach oraz swap GOLD +0,04 PLN. Nie dowodzi zerowej taryfy
historycznej ani przyszłej; brak reprezentatywnego poślizgu, spreadu i finansowania.
Nie używamy aktualnego tick_value do historycznego wyniku PLN.

| Zastosowanie | Decyzja |
|---|---|
| Odkrywanie i odrzucanie hipotez cenowych, koszty jako scenariusz | GO eksploracyjne, z jawnymi ograniczeniami Last/raw |
| Makro/news backtest as-of | NO-GO: brak wcześniejszych prognoz/pierwszych publikacji i historii latencji |
| Sesyjne wzorce cash/FX | NO-GO: brak certyfikowanego czasu i długiej historii odpowiednich interwałów |
| Netto/PF/drawdown rachunku z tych OHLC | NO-GO: brak prawidłowego modelu wykonania i kosztów |
| Niezależny forward po zamrożeniu | Warunkowo: najpierw akceptacja czasu, feedu i as-of; nie stroić na wyniku |
'''
    (base/'DATA_FEASIBILITY.md').write_text(feasibility,encoding='utf-8')
    family=[]
    for m in ('M1','M2','M3','M4'):
        z=d['results'][m+'/ALL'];a=z['all'];l=z['late']
        family.append([m,a['n'],a['blocks'],fmt(a['gross']),fmt(a['hurdle']),fmt(z['early']['mean']),fmt(l['mean']),fmt(a['mean']),fmt(a['stress']),f"[{fmt(a['ci95'][0])}; {fmt(a['ci95'][1])}]",fmt(l['p_zero_holm'])])
    main=table(['Mechanizm','N','Bloki14d','Last brutto bp','Próg bp','Wczesne po progu','Późne po progu','Całość po progu','Stress bp','CI95 całość','p Holm późne'],family)
    detail=[]
    for k,v in d['results'].items():
        if k.endswith('/ALL'):continue
        a=v['all'];l=v['late']
        detail.append([k,a['n'],fmt(v['early'].get('mean')),fmt(l.get('mean')),fmt(a.get('stress')),
                       fmt(a.get('delta_benchmark')),fmt(l['p_zero_holm']),fmt(l['p_placebo_holm'])])
    market=table(['Hipoteza/rynek','N','Wczesne po progu','Późne po progu','Stress całość','Delta vs long bp','p Holm','Placebo Holm'],detail)
    result=f'''# EDGE_RESEARCH_RESULTS — pierwsze testy mechanizmów

**Wiarygodna przewaga po rzeczywistych kosztach: NIE POTWIERDZONA / ZA MAŁO
WIARYGODNYCH DANYCH. Żaden kandydat z tej rundy nie kwalifikuje się do wdrożenia.**
To wynik rzeczywistych obliczeń, a nie obietnica rentowności. Nie optymalizowano
parametrów ani nie zmieniano aktywnego DEMO. Eksperyment {P.VERSION}, znacznik
wykonania {d['at']}, Python {d['python']}, NumPy {d['numpy']}.

## Co wykonano

Przegląd 16 źródeł pierwotnych, audyt danych, rejestr 11 mechanizmów. Wybrano
6 odmiennych mechanizmów przed wynikami: cztery policzono, dwa makro odrzucono
na bramce dostępności danych. 13 relacji mechanizm–rynek, 4 agregaty, 822
niepokrywające się wewnątrz danej relacji zdarzenia. Zależności między rynkami
pozostają: nie jest to 822 niezależnych transakcji. Wyniki dawniej oglądane
stanowią wyłącznie eksplorację; żadnego zwrotu z forward nie użyto do selekcji.

Sygnały z okresu raw 27.04–23.10.2026, chronologiczny podział 01.08.2026.
H4/D1 korzystają z wcześniejszego warm-up od X 2025. Wszystkie wejścia pomiarowe
po zamknięciu świecy sygnału, na kolejnym open. Pomiary z brakującym przyszłym
odcinkiem pominięto, nie interpolowano: to analiza kompletnych przypadków,
mogąca mieć bias dostępności danych. Nie jest to wykonywalna reguła pomijania
przyszłej luki. Czas raw nie pozwala nazwać godzin sesją Londynu/Nowego Jorku.

## Wyniki zbiorcze

Wartości to **bps ruchu Last i scenariusza progu kosztowego**, nie zysk netto,
R ryzyka ani PLN. Próg bazowy pomija nieznaną historyczną prowizję/finansowanie;
stress zawiera 2× próg spreadu, 2 bp dodatkowego kosztu i 2 bp/dobę utrzymania.
Nie istnieje gwarancja, że stress ogranicza najgorszy realny koszt lub lukę.

{main}

M5 (makro FX) i M6 (zapasy OIL): **NIEWERYFIKOWALNE**, brak par forecast-before /
first-actual-after, historii skali surprises i zaakceptowanego czasu wykonania.
Nie wstawiono im zerowego ani hipotetycznie dodatniego wyniku.

## Wszystkie rynki, bez ukrywania nieudanych testów

{market}

Holm obejmuje 17 zaplanowanych porównań późnej podpróby. Korekty p-zero i
placebo są odrębne; nie wybieramy korzystniejszej. Podpróba późna była już
oglądana w innych badaniach, więc nawet skorygowana istotność nie byłaby
niezależnym potwierdzeniem. M4/ALL powtarza pojedynczą parę w zestawie 17:
konserwatywna korekta, nie drugi niezależny dowód.

## Co odrzucamy, a czego próba nie rozstrzyga

- **M1, uniwersalna implementacja 126 D1:** ujemny agregat w obu częściach;
  brak podstaw do promocji. Dodatnie indeksy nie dowodzą informacji ponad
  ekspozycję long. Nie odrzuca to wieloletniego, zdywersyfikowanego TSMOM z
  literatury: nasza próba i horyzont są inne, a rollover niezweryfikowany.
  EURPLN ma późne p-zero po Holm 0,004249, ale wszystkie sygnały są BUY,
  więc wynik jest identyczny z long-only; stress jest ujemny, a placebo po
  Holm wynosi 0,246438. Sześć bloków i ograniczona bootstrapowa próba zerowa
  nie uzasadniają odczytywania małego p jako mocnego dowodu. Nie pomijamy tego
  nominalnie dodatniego testu ani nie nazywamy go przewagą sygnału.
- **M2, rewersja FX:** wszystkie trzy rynki ujemne w późnej części po progu;
  stress ujemny wszędzie. Nie ma podstaw do dokładania filtrów RSI/ADX na tej
  samej historii, aby uratować wynik.
- **M3, wybicie z ekspansją:** ujemny agregat; OIL ujemne w obu częściach.
  GOLD ma tylko 6 zdarzeń. Dodatni ruch sześciu obserwacji nie uzasadnia
  wybrania GOLD jako zwycięzcy. Brak dowodu, nie twierdzenie o niemożliwości trendów.
- **M4, para indeksów:** +0,397 bp po progu w całości, ale −2,664 bp stress;
  wczesna część ujemna, CI obejmuje zero, placebo po Holm nieistotne.
  Nominalne późne p placebo około 0,032 nie uprawnia do selekcji po 17 próbach.
- **M5/M6:** nie testowano rentowności. Wąskie gardło stanowią dane o
  oczekiwaniach i dostępności, nie brak kolejnego oscylatora.

Bootstrap wykorzystuje tylko 6–13 bloków w całości, zwykle 3–6 późnych;
to mało, a sąsiednie bloki również mogą zależeć od siebie. CI nie należy
interpretować jako precyzyjnego prawdopodobieństwa przyszłego zysku.
W DETAILS.md są wszystkie okresy, benchmarki, placebo, opisowe PF i obsunięcia
sumy markoutów. **PF i obsunięcie rachunku oraz expectancy w R: NIEWERYFIKOWALNE**,
bo nie określono wykonywalnego portfela, SL, sizingu, finansowania i Bid/Ask.

## Maksymalnie trzy kierunki uzasadnione mechanizmem, nie rankingiem P&L

1. **M1, powolny trend między klasami aktywów:** najmocniejsze zewnętrzne
   podstawy dla hipotezy cenowej, lecz obecna implementacja nie przeszła testu.
   Minimalny kolejny krok to sprawdzenie dostępności co najmniej 5 lat D1
   z opisem rollowania i kosztów dla tych ekspozycji. Gdy brak zgodności CFD,
   futures można badać wyłącznie jako inny rynek; nie przenosić jego netto.
   Jeden zamrożony test znaku zwrotu vs matched long-only i cash, bez siatki.
2. **M5, kontynuacja po surprise makro na EURUSD/GBPUSD:** zbierać już
   autoryzowanym archiwum forecast z wersją przed publikacją i pierwszy actual
   z czasem odbioru; najpierw potwierdzić, że w ogóle powstają poprawne pary.
   Do ilościowego testu potrzeba także 24 wcześniejszych surprises i Bid/Ask
   po opóźnionym wejściu. Pozyskanie licencjonowanej historii konsensusu
   wymaga osobnej oceny źródła; oficjalny actual sam nie wystarcza.
3. **M6, inventory surprise OIL:** najpierw audyt jednego legalnego źródła
   oczekiwań oraz pierwszych odczytów EIA w tej samej jednostce. To konkretny
   brak blokujący mechanizm; nie wdrażamy feedu lub rozbudowy systemu w tej rundzie.
   Test po 5-min opóźnieniu, z kontekstem produktów i kosztami publikacji,
   musi wykazać ruch pozostający po początkowym skoku.

To priorytety zbierania dowodów, **nie trzy wybrane zyskowne strategie**. M4
nie otrzymuje pierwszeństwa tylko dlatego, że miał dodatnią średnią bazową.
M7/M8 pozostają rozsądnymi dalszymi hipotezami sesyjnymi po odblokowaniu UTC
i danych M1; GOLD real yields wymaga osobnego as-of źródła.

## Jak odróżnić przewagę od przypadku

Przed zobaczeniem nowych zwrotów zamrozić sygnał, źródło, latency, koszty,
benchmark, statystykę, liczbę prób i datę zakończenia. Zachować wszystkie
publikacje i NO TRADE, nie wymieniać słabego okna. Pierwszy poprawny replay
potwierdzi mechanikę, nie edge. Ustalić minimalny ekonomiczny efekt delta i
moc testu; przy niezależnych zdarzeniach orientacyjnie n≈(1,96+0,84)^2×(sigma/delta)^2,
następnie zwiększyć n o zależność i wielokrotność. Nie obiecujemy, że 30, 100
czy jedna doba wystarczy. NFP daje około 12 publikacji rocznie, EIA około 52:
kilka dni forward nie rozstrzygnie tych hipotez.

Wymagane potwierdzenie: przedział średniego realnego netto ponad zero i ponad
ekonomiczny próg, stabilność chronologiczna, wynik względem benchmarku,
odporność na koszty, zgodność replay z cenami DEMO oraz korekta wielu prób.
Po porażce nie stroić tej samej próby i nadal nazywać jej niezależną.

## Decyzje

| Obszar | Decyzja |
|---|---|
| Ograniczone badania mechanizmów na starych danych | GO wyłącznie eksploracyjne |
| Wybranie strategii do handlu / potwierdzenie netto | NO-GO |
| Pełny backtest bieżącego forward | NO-GO: UTC, feed, kontekst i wykonanie |
| Odporność aktywnego DEMO | NO-GO: niewdrożone Recovery i zachowana kwarantanna |

Zakończono tę rundę bez rozbudowy infrastruktury i bez transakcji. Kod i
oczyszczone agregaty przeznaczono na osobną gałąź GitHub; prywatne dane,
historia rachunku i surowe wyniki zdarzeń pozostają lokalnie.
'''
    (base/'EDGE_RESEARCH_RESULTS.md').write_text(result,encoding='utf-8')
    details=['# Szczegóły wszystkich obliczeń','',
             'Wszystkie liczby cenowe poniżej są bps markoutów Last lub ich scenariusza, NIE netto rachunku.',
             'PF*: suma dodatnich/suma ujemnych markoutów po progu. DD*: obsunięcie sumy markoutów grupowanej po raw dniu wyjścia; nie portfel.','']
    for period in ('early','late','all'):
        rows=[]
        for k,v in d['results'].items():
            a=v[period]
            rows.append([k,a['n'],a['blocks'],fmt(a.get('mean')),fmt(a.get('benchmark')),fmt(a.get('delta_benchmark')),
                         str([round(x,3) for x in a.get('ci95',[])]) if a['blocks']>=2 else 'n/a: <2 bloki',
                         f"{a['p_zero']:.6f}",f"{a['p_placebo']:.6f}",
                         fmt(a.get('descriptive_pf')),fmt(a.get('summed_markout_dd_bps'))])
        details.extend(['## '+period,'',table(['Test','N','Bloki','Po progu','Long kontrola','Delta','CI95','p-zero','p-placebo','PF*','DD*'],rows),''])
    details.extend(['## Wszystkie odrzucenia obserwacji','',
                    table(['Test','Powody i liczby'],[[k,', '.join(f'{x}={v}' for x,v in f.items())] for k,f in d['filters'].items()]),''])
    details.extend(['Przy jednym bloku bootstrap daje zdegenerowany punkt; nie jest to przedział niepewności. Dlatego pokazano n/a, a p jest konserwatywnie ustawione na 1. Surowy wynik arytmetyczny w JSON zachowano bez nadpisania.',''])
    details.extend(['## Korelacje godzinowe — opisowe, bez selekcji par','',
                    table(['A','B','Okres','N wspólnych godzin','Pearson'],[[x['a'],x['b'],x['period'],x['n'],fmt(x['correlation'])] for x in d['relationships']]),'',
                    'Korelacja równoczesna nie dowodzi predykcji, kointegracji ani niezależności sygnałów. Para M4 była wybrana przed jej policzeniem.'])
    # Fixed, untested regime descriptions: no search or significance claims.
    details.extend(['','## Kontrola reżimów sygnału (opisowa, bez strojenia)','',
                    'M1: znak trendu; M2: ER poniżej 0,15 / 0,15–0,30; M3: ekspansja ATR poniżej 1,5 / od 1,5; M4: abs(z) poniżej 3 / od 3.',
                    'Te dodatkowe przekroje powstały przy raportowaniu po obejrzeniu agregatów, więc są POST HOC. Nie są nowymi kandydatami ani częścią 17 testów potwierdzających.',''])
    regime=defaultdict(list)
    for r in d['events']:
        m=r['mechanism'];threshold={'M1':0,'M2':.15,'M3':1.5,'M4':3}[m]
        value=r['direction'] if m=='M1' else r['regime']
        regime[m+('/low' if value<threshold else '/high')].append(r)
    details.append(table(['Reżim post hoc','N','Last brutto','Po progu','Stress'],
        [[k,len(v),fmt(sum(r['gross'] for r in v)/len(v)),fmt(sum(r['after_hurdle'] for r in v)/len(v)),
          fmt(sum(r['stress'] for r in v)/len(v))] for k,v in sorted(regime.items())]))
    (base/'DETAILS.md').write_text('\n'.join(details)+'\n',encoding='utf-8')
    hashes=['# Źródła i odtwarzalność','', 'Nie publikujemy danych brokera. Ścieżki względne względem prywatnego korzenia projektu.','',
            table(['Źródło','Świece','SHA256'],[[x['path'],x['bars'],x['sha256']] for x in d['source_hashes']]),'',
            'Spread source SHA256: '+d['cost_source_sha256'], '',
            table(['Instrument','Próg spreadu price'],[[k,format(v,'.12g')] for k,v in d['spread_price_hurdles'].items()]),'',
            'Registry przed eksperymentem SHA256: '+d['registry_sha256'],'',
            table(['Kod podczas eksperymentu','SHA256'],d['code_hashes'].items()),'',
            'Prywatny plik results-v1.json SHA256: '+E.sha(base/'private/results-v1.json'),
            '', 'Raportowanie i odbiór audytu dodano po obliczeniach, nie zmieniając parametrów ani results-v1.json.']
    (base/'INPUT_HASHES.md').write_text('\n'.join(hashes)+'\n',encoding='utf-8')


if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--base',type=Path,default=Path(__file__).resolve().parent)
    render(ap.parse_args().base)
