"""Offline verification of the fixed 12 tiny samples; no MT5 calls or returns."""
import argparse,hashlib,json,math,statistics
from datetime import datetime
from pathlib import Path
from collect_tables import DATES

def analyze(folder):
    manifest=json.loads((folder/'summary.json').read_text())
    expected=['2026-'+d.replace('_','-') for d in DATES]
    if [m['day'] for m in manifest]!=expected:raise ValueError('Incomplete fixed sample')
    results=[]
    for day,m in zip(DATES,manifest):
        blob=(folder/(day+'.json')).read_bytes()
        if hashlib.sha256(blob).hexdigest()!=m['sha256']:raise ValueError('Hash mismatch')
        r=json.loads(blob)
        if not r['continue'] or not all(r['gate'].values()) or r['api_error'][0]!=1:
            raise ValueError('Probe gate or API failure')
        lo=round(datetime.fromisoformat(r['request_api_utc']).timestamp()*1000);hi=lo+1000
        if any(not lo<=x['time_msc']<=hi for x in r['raw_rows']):raise ValueError('Out of range')
        ticks=[x for x in r['raw_rows'] if x['time_msc']<hi]
        if not ticks or any(a['time_msc']>b['time_msc'] for a,b in zip(ticks,ticks[1:])):
            raise ValueError('Empty/unordered')
        if any(not(math.isfinite(x['bid']) and math.isfinite(x['ask']) and 0<x['bid']<=x['ask']) for x in ticks):
            raise ValueError('Invalid quotes')
        # MetaQuotes TICK_FLAG_BID=2, ASK=4, LAST=8. No fabricated left-edge state.
        spreads=[x['ask']-x['bid'] for x in ticks]
        unflagged={side:sum(a[side]!=b[side] and not (b['flags']&flag)
                            for a,b in zip(ticks,ticks[1:])) for side,flag in [('bid',2),('ask',4)]}
        observed_updates={side:sum(bool(x['flags']&flag) for x in ticks) for side,flag in [('bid',2),('ask',4),('last',8)]}
        for key in ('bid','ask','last'):
            if observed_updates[key]!=r[key+'_flag_updates']:raise ValueError('Flag count mismatch')
        if len(ticks)!=r['ticks_in_second']:raise ValueError('Count mismatch')
        known_bid=known_ask=False;known_both=0
        for x in ticks:
            known_bid|=bool(x['flags']&2);known_ask|=bool(x['flags']&4)
            known_both+=int(known_bid and known_ask)
        results.append({'date':r['day'],'ticks':len(ticks), 'updates':observed_updates,
          'spread_min':min(spreads),'spread_median':statistics.median(spreads),'spread_max':max(spreads),
          'last_without_bid_ask_update':sum(bool(x['flags']&8) and not(x['flags']&6) for x in ticks),
          'duplicate_timestamps':len(ticks)-len({x['time_msc'] for x in ticks}),
          'unflagged_price_changes':unflagged,'rows_after_both_observed_updates':known_both,
          'first_tick_ms_into_second':ticks[0]['time_msc']-lo,
          'last_tick_ms_into_second':ticks[-1]['time_msc']-lo,
          'max_internal_gap_ms':max((b['time_msc']-a['time_msc'] for a,b in zip(ticks,ticks[1:])),default=0)})
    return {'samples':results,'total_ticks':sum(x['ticks'] for x in results),
            'last_only_ticks':sum(x['last_without_bid_ask_update'] for x in results),
            'historical_utc_verified':False,'full_window_coverage_verified':False,
            'quote_freshness_verified':False,'source_bytes':sum((folder/(d+'.json')).stat().st_size for d in DATES)}

def report(r):
    lines=['# OIL: dostęp historyczny potwierdzony punktowo — 29.10.2026','',
      '**GO dla dostępności 12 małych próbek; NO-GO dla pełnego replay newsowego i potwierdzenia przewagi.**','',
      'Ten wynik zastępuje wniosek o niedokończonym odczycie z TICK_PROBE_RESULT.md. Nie zmienia danych poprzedniej próby.',
      '', '## Powód jednej ponownej próby','',
      'Po timeoutcie v5 pojawiły się cache OIL marzec–październik 2026: 8 plików, 214 794 095 B (204,84 MiB). '
      'Plik marca został zapisany o 08:39:28 UTC, już po poprzedniej kontroli. To nowy dowód uzasadniający v6 z identycznym limitem 10 s i tymi samymi datami. '
      'Nie wywoływano dodatkowego pobrania miesięcy: synchronizację kontynuował MT5 po zakończeniu jednosekundowego żądania. '
      'Rozmiar cache nie jest pomiarem transferu sieciowego. Wcześniejszy limit procesu i limit zwracanych rekordów nie ograniczają wewnętrznego transferu terminala.',
      '', '## Niezależna kontrola zapisanych odpowiedzi','',
      f'12/12 odpowiedzi API Success; {r["total_ticks"]} rekordów, {r["source_bytes"]} bajtów prywatnych plików JSON z metadanymi. '
      'Sprawdzono SHA256, komplet ustalonych dat, zakresy, nieujemną kolejność czasu, dodatnie i niekrzyżujące się Bid/Ask oraz liczby flag. '
      'W badanych sąsiednich rekordach nie ma zmiany ceny Bid/Ask bez odpowiadającej flagi.',
      '', '| Data | Ticki | Bid update | Ask update | Last bez Bid/Ask update | Spread min–max w jednostkach ceny |',
      '|---|---:|---:|---:|---:|---:|']
    for x in r['samples']:
        lines.append(f'| {x["date"]} | {x["ticks"]} | {x["updates"]["bid"]} | {x["updates"]["ask"]} | {x["last_without_bid_ask_update"]} | {x["spread_min"]:.3f}–{x["spread_max"]:.3f} |')
    lines+=['', f'{r["last_only_ticks"]}/{r["total_ticks"]} rekordów ma zmianę Last bez flag zmiany Bid/Ask. '
      'Last ani czas ostatniego ticka nie dowodzą aktualizacji obu stron. Zachowano kolejność API i wielokrotne rekordy o tej samej milisekundzie; '
      'nie deduplikowano ich po timestampie. Czas w ms nie ujawnia rzeczywistego porządku wewnątrz jednej milisekundy.',
      '', 'Każda próbka obejmuje tylko jedną sekundę surowej osi API. Wiersze przed pierwszą zaobserwowaną aktualizacją obu stron '
      'nie otrzymują sztucznego czasu odświeżenia. Nawet obserwacja obu flag nie potwierdza pełnej wykonalności ani latencji brokera. '
      'Brak ticka w części sekundy nie jest automatycznie luką transferu — może oznaczać brak zdarzenia. Nie dowiedziono kompletności dłuższych okien.',
      '', '## Ograniczenia, które nadal blokują wynik strategii','',
      '- Dokumentacja Python opisuje UTC, lecz wcześniejsze dowody na tym rachunku wskazywały przesunięcia czasu. Nie wolno przenieść obecnego offsetu na marzec–maj ani ustalać go przez dopasowanie skoku ceny do EIA.',
      '- Próbki pobrano przy planowych etykietach czasu publikacji; nie nazywamy ich potwierdzonymi cenami w chwili EIA.',
      '- Archiwalne tabele EIA nie mają zweryfikowanego first-print/published_at; historyczny konsensus nie został pozyskany.',
      '- Brak pełnych okien, historycznych specyfikacji/kosztów i modelu poślizgu. Spread tej sekundy nie jest kosztem całej transakcji.',
      '- Nie liczono markoutów, P&L, R ani rentowności. 12 wydarzeń to odbiór danych, nie niezależny dowód edge.',
      '', '## Jeden następny krok','',
      'Uzgodnić semantykę historycznych timestampów Python MT5 dla feedu TMS i pierwszą dostępność wydań EIA przed dopasowaniem cen do wydarzeń. '
      'Nie rozpoczynać dużego eksportu na podstawie samego sukcesu API. Gotowy zakres pytań do brokera w UTC_EVIDENCE_REQUEST.md; nie wysłano wiadomości. '
      'Większe okna wymagają odrębnej zgody oraz uwzględnienia faktu, że MT5 może synchronizować znacznie więcej danych niż zwraca.',
      '', 'Aktywny DEMO, strategie, Risk Manager, LIVE i kwarantanna pozostają bez zmian. Dalszy forward musi być oddzielony od danych obejrzanych przy odbiorze. '
      'Ta runda jest postępem w dostępności danych, nie potwierdzeniem rentowności.','']
    return '\n'.join(lines)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('folder',type=Path);a=p.parse_args()
    result=analyze(a.folder)
    with (a.folder/'quality.json').open('x',encoding='utf-8') as f:json.dump(result,f,indent=2)
    with (a.folder/'READOUT.md').open('x',encoding='utf-8') as f:f.write(report(result))
    print(json.dumps(result,indent=2))
