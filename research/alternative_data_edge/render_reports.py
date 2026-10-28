"""Aggregate-only reports; no account, raw prices, or API response publication."""
import argparse,json
from pathlib import Path
import alternative_experiments as A
from render_results import f,table
E=A.E

def main(root):
    here=Path(__file__).resolve().parent;d=E.read(here/'private/results-v1.json')
    primary=[k for k in d['tests'] if k.endswith('lag3')]
    rows=[]
    for k,t in d['tests'].items():
        a,b=t['early'],t['late'];ci=b.get('ci_delta')
        rows.append([k,a['n'],b['n'],b['active'],b['blocks'],f(a.get('delta')),f(b.get('base')),f(b.get('mean')),
            f(b.get('delta')),', '.join(map(f,ci)) if ci else 'nieweryfikowalne',f(b.get('stress')),
            f(b.get('delta_price_filter')),f(b.get('p_delta_holm48'))])
    out=['# Eksperymenty z nowymi danymi — alternative-data-v1','',
         '**Wykonano4 rodziny,6 głównych porównań oraz6 z góry określonych testów opóźnienia. Żadne nie przeszło Holm6 ani Holm48.**','',
         'Reguły zapisano w HYPOTHESES.md przed obliczeniem. Nie zmieniano ich po wynikach. Testujemy dodatkową informację z Cboe względem tego samego momentum20, nie ponownie dobór EMA. Dane cenowe: D1 brokera, raw27.04–23.10.2026, split01.08, wcześniejsze świece warm-up.','',
         'Wszystkie stare ceny są eksploracyjne. Pozyskanie nowego predyktora nie czyni starych zwrotów niezależnym holdoutem. Wiersze Cboe po23.10 nie mogą wejść do okien; nie wykorzystano forward do wyboru hipotezy.','',
         '## Poziomy dowodu','',
         '1. Zaobserwowana zależność: opóźnione IV w stosunku do późniejszego markoutu Last, obliczona lokalnie.',
         '2. Wartość dodana: sparowana różnica B−A, wobec tego samego modelu bez IV; dodatkowo kontrola cenowej ATR.',
         '3. Markout po progach: poniższe B/A/stress to bps na okazję, z cash; nie netto wykonania.',
         '4. Wykonalność Bid/Ask i pełne koszty: nieweryfikowalne.',
         '5. Potwierdzony edge: NIE.','',
         '## Wszystkie wyniki','',
         table(['Test','n early','n late','B aktywne late','bloki late','Delta early','A late','B late','Delta late','CI95 Delta','B stress late','B minus ATR late','p Holm48'],rows),'',
         'n to okazje na stałej siatce, nie liczba niezależnych transakcji. Późna próbka ma6 bloków14dni i tylko10–11 okazji na model. Wspólne rynki/okresy są skorelowane. CI95 są marginalne opisowe; skorygowane p kontrolują wielokrotność przy ograniczonej kalibracji bootstrap.','',
         '## Benchmark C i placebo D — główne lag3','',
         table(['Test','gross B','próg spreadu B','B/aktywne','long po progu','cenowy ATR','p Delta Holm6','p thinning Holm6','p sign Holm6'],[
            [k]+[f(d['tests'][k]['late'].get(x)) for x in ('gross','cost','per_active','long','price_filter','p_delta_holm6','p_thinning_holm6','p_placebo_holm6')] for k in primary]),'',
         'Cash=0 jest jawnie zdefiniowanym benchmarkiem, nie substytutem brakującego wyniku. Thinning zachowuje liczbę aktywnych okien w każdym bloku; signed placebo odwraca signed markout blokami, pozostawiając koszt.','',
         '## Stabilność reżimów — wszystkie warianty, cała próba','',
         table(['Test','Delta ATRlow','Delta ATRhigh','Delta trendup','Delta trenddown'],[
            [k]+[f(v[x].get('delta')) for x in ('vol/low','vol/high','trend/up','trend/down')] for k,v in d['regimes'].items()]),'',
         '## Dostępność i koszty','',
         'Lag3 oznacza datę IV starszą o72h+3h marginesu od raw sygnału; lag7 o168h+3h. Nie znamy first publication każdego wiersza Cboe ani pełnej historii offsetów brokera. Dlatego to diagnostyka opóźnionych zależności, a NIE certyfikowany test wejść po historycznej dostępności. Lag nie naprawia rewizji i nie jest dowodem UTC.',
         'D1 mierzymy next-open→open po5 dostępnych świecach. Koszt: max p95 spreadu z3 starych okien22.10 / Last entry. Stress:2×spread+2bps+2bps/dobę. Prowizja/swap/rollover/FX/slippage nie zostały odtworzone; nie liczymy fikcyjnego PF, drawdown kapitału ani R.',
         'Filtr może poprawić średnią tylko dlatego, że usuwa ekspozycję na stratną bazę. Dlatego wymagamy przewagi nad losowym filtrem i kontrolą ATR, a nie samej dodatniej różnicy B−A.','',
         table(['Test','siatka','gap','boundary','brak wyjścia','brak/stale IV','zaakceptowane'],[
            [k,v.get('grid_opportunities',0),v.get('gap',0),v.get('boundary',0),v.get('missing_exit',0),v.get('missing_or_stale_index',0),v['accepted_with_index']] for k,v in d['filters'].items()]),'',
         '## Odtwarzalność','',f"Wynik {d['at']}; seed20261028,4000losowań,14dni/blok. Hash protokołu `{d['registry_sha256']}`, kodu `{d['code_hash']}`, prywatnego wyniku `{E.sha(here/'private/results-v1.json')}`.",'',
         table(['Indeks','n','pierwsza data','ostatnia data','SHA256'],[[k,v['rows'],v['first'],v['last'],v['sha256']] for k,v in d['coverage'].items()]),'',
         'Surowe pliki i row-level wyniki nie trafiają do Git. Komendy w README.md. Pięć nowych testów automatycznych przeszło przed obliczeniem; użyte syntetyczne fixtures sprawdzają wyłącznie mechanikę, nie wyniki rynku.']
    (here/'EXPERIMENTS.md').write_text('\n'.join(out)+'\n',encoding='utf-8')
    verdict=['# EDGE_VERDICT — 28.10.2026','',
        '**NIE: nie znaleziono wiarygodnej przewagi po rzeczywistych kosztach.** Zbadane filtry nie uzasadniają promocji; dla COT/makro brakuje określonych danych, więc ich wynik pozostaje nieweryfikowalny.','',
        'Poniżej późna część eksploracji (01.08–23.10 raw). A/B są bps Last na okazję po progu spreadu; nie broker P&L. Wszystkie główne p Holm6 i Holm48=1.000.','',
        table(['Rynek','Mechanizm','Źródło','Liczba obserwacji','Wynik bazowy A','Z nową informacją B','Koszty','Istotność','Werdykt'],[
            [k.split('/')[1],k.split('/')[0],k.split('/')[2],f"{d['tests'][k]['late']['n']} okazji / {d['tests'][k]['late']['active']} aktywnych B / 6 bloków",
             f(d['tests'][k]['late'].get('base')),f(d['tests'][k]['late'].get('mean')),
             'próg; stress '+f(d['tests'][k]['late'].get('stress')),'brak po Holm','nie promować'] for k in primary]+[
            ['EURUSD','COT / stopy','CFTC / ALFRED','nieweryfikowalne','nieweryfikowalne','nieweryfikowalne','brak pełnego modelu','nieweryfikowalne','brak zbioru as-of'],
            ['GBPUSD','COT / stopy','CFTC / ALFRED','nieweryfikowalne','nieweryfikowalne','nieweryfikowalne','brak pełnego modelu','nieweryfikowalne','brak zbioru as-of'],
            ['EURPLN','stopy / risk-off','NBP / ECB / GPR','nieweryfikowalne','nieweryfikowalne','nieweryfikowalne','brak OIS/kosztów','nieweryfikowalne','brak zbioru as-of']]),'',
        '## Decyzje o nowych filtrach','',
        '- VIX i VIX9D/VIX: w późnych głównych oknach nie odfiltrowały żadnego wejścia; przyrost dokładnie0. To brak nowej decyzji w tej próbce, nie dowód równoważności populacyjnej.',
        '- OVX: późny markout z filtrem mniej ujemny niż baza, ale nadal ujemny; gorszy niż prosta kontrola ATR. Przy7d lag znak przyrostu się odwraca. Brak przewagi nad placebo.',
        '- GVZ: główny filtr obniża markout względem bazy w obu podpróbach. Dodatni bezwzględny markout nie jest wartością dodaną. Wrażliwość7d zmienia znak późnego przyrostu, bez istotności.',
        '- Żadnej z sześciu badanych konfiguracji nie nominujemy do wdrożenia ani nie dostrajamy progów.',
        '- COT, real yields, EIA i GPR nie mają tu policzonego wyniku strategii; brak wartości nie jest zerem.','',
        '## Co pozostaje uzasadnione naukowo','',
        'Dwa kierunki badawcze, a nie wybrani zwycięzcy: (1) reakcja na informację EIA po pierwszym skoku, (2) wolniejsze pozycjonowanie COT w relacji do momentum. Pierwszy wymaga first print i wykonalnych kwotowań; drugi kalendarza faktycznych publikacji i dłuższych cen. Nie uruchamiamy obu naraz: jeden następny zbiór określa NEXT_STEP.md.',
        'Żaden kierunek nie otrzymał statusu potwierdzonego kandydata po kosztach. Nowy predyktor nadal trzeba porównać do ceny, USD/vol i placebo w niewykorzystanym okresie; co najmniej20 bloków to minimum techniczne, nie gwarancja mocy statystycznej.','',
        '## Osobne bramki','',
        '- **GO**: ograniczone badanie statystyczne offline na opóźnionych danych z jawnymi ograniczeniami.',
        '- **NO-GO**: deklaracja poprawnego historycznego as-of i netto; brak vintage/UTC/kosztów.',
        '- **NO-GO**: zmiana DEMO lub uruchomienie LIVE na podstawie tych wyników.',
        '- Odporność DEMO nie jest tu ponownie certyfikowana. Odczyt kontrolny wcześniejszej części pracy potwierdził obecność brokerowych SL/TP; kwarantanna i WAITING pozostają odrębną blokadą. Niczego nie wdrażano.']
    (here/'EDGE_VERDICT.md').write_text('\n'.join(verdict)+'\n',encoding='utf-8')
    old=E.read(root/'research/market_mechanisms/private/feasibility.json')
    probe=E.read(here/'private/broker-range-probe-v1.json')['requests']
    br=['# Historia brokera: zakres potwierdzony, nie domniemany','',
        'OANDA TMS, chart_mode=LAST dla wszystkich7. Poniższe daty są interpretacją liczby raw jako daty kalendarzowej, **nie certyfikatem UTC**. Nie zmieniono konfiguracji terminala, liczby świec ani symboli.','',
        '## Istniejące lokalne archiwa','',
        table(['Rynek','TF','n','pierwszy raw','ostatni raw'],[[r['alias'],r['tf'],r['n'],r['first_raw'],r['last_raw']] for r in old['ohlc']]),'',
        '## Nowa sonda range z limitem czasu','',
        table(['Rynek','API/TF','zakres żądany od','rekordów','Bid/Ask dodatnie','status'],[
            [r['alias'],r['kind'],r['start'],r.get('n','nieweryfikowalne'),r.get('positive_bid_ask','nie dotyczy'),r.get('status','OK')] for r in probe]),'',
        'M1:22.10.2026 12:00–13:00,61świec/rynek. Ticks:12:00:00–12:00:01, odczyt rzeczywistych Bid/Ask w krótkiej próbce, bez dopisywania cen. Granice API mogą być inkluzywne. Poszczególny sukces nie dowodzi pełnej doby ani lat bez luk.',
        'GOLD H1:2świece z15.01.2024. Następne US500 H1 przekroczyło15s; zatrzymano wyłącznie własne procesy sondy i nie wysłano pozostałych26żądań. Brak odpowiedzi nie oznacza braku historii. Wcześniejsza sonda copy_rates_from D1 także nie odpowiedziała; dlatego zastosowano zewnętrzny deadline.',
        '**Najdłuższy możliwy zakres serwera pozostaje nieustalony.** Udowodniony punkt starszej dostępności to2024 H1 GOLD; dla innych instrumentów są archiwa lokalne i krótka próbka22.10. Nie ogłaszamy2025 początkiem historii serwera.','',
        '## Jakość, czas i koszty','',
        '- H1/H4/D1 z istniejących archiwów; M1 nowo potwierdzony. Nie badano wszystkich pozostałych interwałów.',
        '- Brak pełnej historycznej mapy UTC/DST. Nie używamy stałego offsetu do testów sesyjnych lub EIA. Potrzebny współczesny dowód server-vs-UTC i osobne datowane dowody historyczne.',
        '- Historia brokerowych spreadów, prowizji, finansowania, przeliczenia FX i rollover nie jest kompletna. Archiwalne specyfikacje i swapy TMS z edge_program/DATA_SOURCES.md pomagają, lecz nie tworzą automatycznie pełnego modelu.',
        '- Dodatnie Bid/Ask jednej sekundy nie certyfikują aktualności każdej strony ani okresów zerowych kwotowań. Last/volume i zmiany stron należy rozdzielać po flags i czasie.',
        '- Nie policzono różnic kwotowań TMS–Dukascopy/TrueFX: brak dopasowanych próbek w obu feedach. Ich ticki mogą służyć replikacji mechanizmu, nie dowodowi netto TMS.',
        '- Nie pobrano masowych archiwów, nie zmieniono aktywnego DEMO ani kolektora.','',
        'Wniosek: małe zapytania range potrafią zwrócić rzeczywiste dane. Zakup innego feedu nie jest jeszcze uzasadniony samą nieskuteczną sondą starej historii. Następna próba powinna mieć mały, jawny zakres i działać poza aktywną sesją terminala.']
    (here/'BROKER_HISTORY.md').write_text('\n'.join(br)+'\n',encoding='utf-8')
    print('Rendered experiments, verdict and broker history')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);main(ap.parse_args().root)
