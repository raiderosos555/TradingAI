"""Render aggregate audit tables; never publishes account or raw market rows."""
import argparse,json
from pathlib import Path
from datetime import datetime,timezone
import experiments as E

def f(x):return 'nieweryfikowalne' if x is None else f'{x:.3f}'
def table(headers,rows):return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|']+['| '+' | '.join(map(str,r))+' |' for r in rows])
def main(root):
    here=Path(__file__).resolve().parent;d=E.read(here/'private/results-v1.json');rows=[]
    for k,t in d['tests'].items():
        a,b=t['early'],t['late'];ci=b.get('ci_delta')
        rows.append([k,a['n'],b['n'],b['active'],b['blocks'],f(a.get('delta')),f(b.get('gross')),f(b.get('cost')),
                     f(b.get('mean')),f(b.get('base')),f(b.get('delta')),
                     ', '.join(map(f,ci)) if ci else 'nieweryfikowalne',f(b.get('stress')),f(b.get('p_delta_holm'))])
    out=['# Wyniki edge-program-v1 — 28.10.2026','',
        '**36 porównań, 0 istotnych przyrostów po Holm36. Nie potwierdzono przewagi po rzeczywistych kosztach.**','',
        'Pytanie nowe wobec poprzedniej rundy: wartość dodana wskaźnika do prostego benchmarku; bez ponownego strojenia EMA20/50. Cztery rodziny T/R/F/X z STRATEGY_HYPOTHESES.md zapisano przed obliczeniem.','',
        'Pomiary: raw 27.04–23.10.2026; early do31.07, late od01.08. Oba okresy były wcześniej oglądane. Wcześniejsze świece służą rozgrzewce. 5871 par-okazji łącznie to powtarzające się okna różnych modeli, NIE 5871 niezależnych transakcji. W obrębie reguły okna nie nakładają się; korelacje między rynkami i blokami pozostają.','',
        'Wszystkie wielkości cenowe w bps Last na okazję, także cash. G=gross markout; K=próg spreadu; B=G−K, A=benchmark po tym samym progu. Delta=B−A. S=stress B. **B nie jest netto brokera**, a wewnętrzny klucz JSON net oznacza jedynie markout minus próg. Brak SL/sizingu/pełnego wykonania: PF, drawdown kapitału i R nieweryfikowalne, nie zero.','',
        table(['Test','n early','n late','aktywnych late','bloków late','Delta early','G late','K late','B late','A late','Delta late','CI95 Delta','S late','p Holm36'],rows),'',
        'CI opisowe, nie jednoczesne przedziały po korekcie. Holm dotyczy p; przy nielicznych blokach bootstrap ma słabą kalibrację. CI [0,0] przy identycznych decyzjach nie jest dowodem równoważności populacyjnej.','',
        '## Placebo, ekspozycja i benchmark long','',
        table(['Test','aktywnych A late','B/aktywne','long po progu','zgodność B/A','p sign placebo Holm36','p thinning Holm8'],[
            [k,t['late']['base_active'],f(t['late'].get('per_active')),f(t['late'].get('long')),f(t['late'].get('signal_agreement')),
             f(t['late'].get('p_placebo_holm')),f(t['late'].get('p_thinning_holm')) if k.startswith('F/') else 'nie dotyczy'] for k,t in d['tests'].items()]),'',
        '## Stabilność: wszystkie reżimy, cała próba','',
        table(['Test','Delta ATRlow','Delta ATRhigh','Delta trendup','Delta trenddown'],[
            [k]+[f(v[x].get('delta')) for x in ('vol/low','vol/high','trend/up','trend/down')] for k,v in d['regimes'].items()]),'',
        '## Decyzje','',
        '- T: nie wykazano trwałej wartości wygładzenia ponad prosty zwrot20. Dodatni pojedynczy markout nie uprzywilejowuje OIL/US100.',
        '- R: RSI nie wykazał przyrostu po wielokrotności wobec prostego odchylenia. Nie dodawać go jako niezależnego głosu.',
        '- F: brak potwierdzenia, że ADX/ATR poprawiają dobór wejść ponad bazę i kontrolę redukcji ekspozycji.',
        '- X: pojedyncze dodatnie różnice pozostają nieistotne po korekcie. Nie promować false breakout.',
        '- Zero nominacji strategii do wdrożenia. To odrzucenie uzasadnienia promocji tych reguł, nie dowód nieistnienia wszystkich mechanizmów.',
        '- Makro A/B/C: nie obliczono brakujących surprise ani P&L. Nowe źródła i małe próbki w DATA_SOURCES.md; dodatkowe dane IV są oddzielnym eksperymentem alternative_data_edge.','',
        '## Koszty i odrzucenia danych','',
        table(['Rynek','próg spreadu w jednostkach ceny'],[[k,f(v)] for k,v in d['spreads'].items()]),'',
        'Próg to max p95 z3 okien22.10, nie historyczny spread każdego wejścia. Stress2×próg+2bps+2bps/dobę. Nie uwzględnia wiernie prowizji, swapów, rolloverów, FX ani slippage; luka wykonania pozostaje.','',
        table(['Test','siatka','luki','granice','brak wyjścia','przyjęto'],[[k,v.get('grid_opportunities',0),v.get('gap',0),v.get('boundary',0),v.get('missing_exit',0),v.get('accepted_opportunities',0)] for k,v in d['filters'].items()]),'',
        '## Odtwarzalność','',f"Wynik zapisany {d['at']}; Python {d['python']}, NumPy {d['numpy']}; seed20261028,4000 bootstrap,14dni/blok.",
        f"Hash protokołu przed wynikiem: `{d['registry_sha256']}`. Hash lokalnego wyniku: `{E.sha(here/'private/results-v1.json')}`.",'',
        table(['Wejście','świece','SHA256'],[[x['path'],x['bars'],x['sha256']] for x in d['source_hashes']]),'',
        table(['Kod podczas obliczenia','SHA256'],list(d['code_hashes'].items())),
        '', 'Komendy i granice odtworzenia z prywatnymi wejściami: README.md. Nie pobierano nowych ticków do tych obliczeń.']
    (here/'EXPERIMENT_RESULTS.md').write_text('\n'.join(out)+'\n',encoding='utf-8')
    print('Rendered 36 comparisons')
if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--root',type=Path,required=True);main(ap.parse_args().root)
