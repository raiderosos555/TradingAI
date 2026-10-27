"""Render sanitized, reviewable research evidence from saved calculations only."""
import argparse,json,hashlib
from pathlib import Path
from datetime import datetime,timezone
import protocol as P

def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def f(v):return 'n/d' if v is None else f'{v:.3f}'
def ci(v):return 'n/d' if v is None else f'[{f(v[0])}; {f(v[1])}]'
def table(headers,rows):
    return '\n'.join(['| '+' | '.join(headers)+' |','|'+'|'.join(['---']*len(headers))+'|',*['| '+' | '.join(map(str,r))+' |' for r in rows]])

def run(folder):
    d=read(folder/'results-v1/results.json');events=read(folder/'results-v1/events.json');ticks=read(folder/'results-v1/tick_events.json')
    inv=read(folder/'private/inventory.json');health=read(folder/'private/demo-readonly.json')
    summaries={(r['family'],r['period']):r for r in d['summary']}
    candidates=[];verdicts=[]
    for fam in P.FAMILIES:
        early=summaries[fam,'early'];late=summaries[fam,'late']
        months=[r for r in d['subgroups'] if r['family']==fam and r['group']=='month']
        positive=sum(r['mean']>0 for r in months)
        reasons=[]
        if early['n']<30 or late['n']<30:reasons.append('mniej niż 30 zdarzeń w jednym okresie')
        if early['mean'] is None or early['mean']<=0:reasons.append('niedodatnia średnia wczesna po progu kosztu')
        if late['mean'] is None or late['mean']<=0:reasons.append('niedodatnia średnia późna po progu kosztu')
        if late.get('stress',-1)<=0:reasons.append('późny stres kosztów niedodatni')
        if positive<.6*len(months):reasons.append('mniej niż 60% dodatnich miesięcy')
        breadth=min(sum(r['mean']>0 for r in d['by_instrument'] if r['family']==fam and r['period']==p) for p in ['early','late'])
        if not reasons:candidates.append((breadth,fam))
        verdicts.append([fam,f'{positive}/{len(months)}',str(breadth),'ODRZUCENIE w screeningu: '+ '; '.join(reasons) if reasons else 'spełnia wstępne progi; brak niezależnego potwierdzenia'])
    selected=[fam for _,fam in sorted(candidates,key=lambda x:(-x[0],x[1]))[:2]]
    # Post-hoc market-specific observations; NOT a replacement for frozen family gate.
    leads=[]
    for alias in ('OIL','US100'):
        early=next(r for r in d['by_instrument'] if r['family']=='trend' and r['alias']==alias and r['period']=='early')
        late=next(r for r in d['by_instrument'] if r['family']=='trend' and r['alias']==alias and r['period']=='late')
        rr=[r for r in events if r['family']=='trend' and r['alias']==alias]
        months={m:sum(r['after_hurdle'] for r in rr if r['month']==m) for m in {r['month'] for r in rr}}
        leads.append([alias,f"{early['n']}/{late['n']}",f(early['mean']),f(late['mean']),f(late['stress']),
                      f"{sum(v>0 for v in months.values())}/{len(months)}",ci(late['ci95']),ci(late['ci_familywise'])])
    writeup=[]
    writeup += ['# EDGE_DISCOVERY — badanie przewagi, 27.10.2026',
      '**Czy znaleziono wiarygodną przewagę: NIE.** Nie jest to dowód, że przewaga nie istnieje. '
      'Dla oceny rzeczywistego netto po wszystkich kosztach nadal jest **ZA MAŁO DANYCH**. '
      'Poniższe liczby są rzeczywistymi obliczeniami na zapisanych danych brokera; nie są wygenerowanym P&L ani wynikami rachunku.',
      f"Przetestowano **8 rodzin / 53 kombinacje**, {len(events):,} nienakładających się wewnątrz kombinacji zdarzeń H1. "
      f"Odrębnie przeliczono {len(ticks)} markoutów Bid/Ask z jednej doby; "
      f"{len(d['tick_missed'])} zdarzeń nie uzyskało świeżych stron na wejściu lub wyjściu w limicie 10 s. "
      'Nie zmieniano parametrów po wyniku, nie wykonano transakcji i nie użyto forward do wyboru reguł.',
      f"Po usunięciu tożsamości rodziny to {len({(r['alias'],r['raw_entry'],r['raw_exit'],r['direction']) for r in events})} "
      f"różnych kierunkowych odcinków H1 oraz {len({(r['alias'],r['raw_entry'],r['raw_exit'],r['direction']) for r in ticks})} "
      'odcinki tickowe. One również mogą nakładać się czasowo i korelować; nie są liczbą niezależnych transakcji.',
      '## 1. Co faktycznie zbadano',
      'Wspólne warunki: sygnał wyłącznie z zamkniętych H1, wejście po zamknięciu, wyjście czasowe po 4h, '
      '120 barów rozgrzewki, najwyżej jedna ekspozycja na daną kombinację w danym czasie. '
      'H1 mierzy późniejszy ruch Last. Ticki mierzą BUY Ask→Bid / SELL Bid→Ask. '
      'Nie ma intrabar SL/TP ani zarządzania DEMO w tym badaniu; oba istniejące algorytmy DEMO pozostają zamrożonym punktem odniesienia, '
      'a ich dawny niewiarygodny P&L nie jest benchmarkiem liczbowym.',
      table(['Hipoteza','Proponowany mechanizm, nie udowodniony fakt','Mierzalny sygnał'],[[k,*P.DESCRIPTIONS[k]] for k in P.FAMILIES]),
      'Dane wymagane: H1 Last i wcześniejsze ATR/EMA dla wszystkich rodzin; wspólne znaczniki leader/follower dla cross_momentum; '
      'potwierdzone UTC i sesje do interpretacji clock_breakout jako konkretnej giełdy. '
      'Do wykonania każda wymaga Bid/Ask, czasu, kontraktu i kosztów z danej chwili. '
      'Falsyfikacja każdej: brak dodatniej średniej po kosztach i stabilności w zamrożonym późniejszym oknie; '
      'dla wybicia także zanik ruchu po przekroczeniu poziomu, dla rewersji dalsza kontynuacja ekstremum, '
      'dla cross — brak zysku followera po opóźnieniu, dla sesji — brak stabilności po prawidłowym UTC, '
      'dla reżimu — brak kontynuacji poza pojedynczym epizodem zmienności.',
      '## 2. Audyt dostępnych danych',
      table(['Instrument','H1','Pierwsza etykieta raw','Ostatnia etykieta raw','Luki >1h','Ticki 22.10','Niepoprawne Bid/Ask'],
        [[r['alias'],r['bars'],r['first_raw'],r['last_raw'],r['gaps_over_1h'],
          next(x['ticks'] for x in d['tick_data'] if x['alias']==r['alias']),
          next(x['invalid_quotes'] for x in d['tick_data'] if x['alias']==r['alias'])] for r in d['data']]),
      '**Raw oznacza surową oś liczbową brokera, nie potwierdzone UTC.** Nie stosowano stałego offsetu. '
      'Wszystkie siedem serii to Last; nie zamieniono ich w Bid/Ask przez dodanie spreadu. '
      'Dane H1 27.04–23.10 były już oglądane. Podział raw 01.08 rozdziela okres wczesny i późny wyłącznie dla kontroli stabilności. '
      'Liczba obserwacji niezależnego potwierdzenia wynosi **0**.',
      'Po rozgrzewce rzeczywiście ocenione zdarzenia obejmują **04.05–31.07 (65 dni)** oraz '
      '**03.08–23.10 (60 dni)**. Świece z końca kwietnia są tylko wcześniejszym wejściem do wskaźników.',
      table(['Instrument','H4 liczba','D1 liczba'],[[s,next(r['n'] for r in inv['context'] if r['alias']==s and r['tf']=='H4'),next(r['n'] for r in inv['context'] if r['alias']==s and r['tf']=='D1')] for s in P.SYMBOLS]),
      'H4/D1 to około rok zapisanego kontekstu do odkrywania dłuższych zależności, niewykorzystany do strojenia tego przebiegu. '
      'Baza runtime zawiera bars/ticks/snapshots/deals/orders; jest zapisem zbierania i wykonania, '
      'nie automatycznie kompletną historią badawczą. Nie mieszano jej z nową próbą potwierdzającą. '
      'Wszystkie 42 czterogodzinne bloki pobrania 22.10 mają zapisane dane; '
      'pokrycie zakresów zapytań nie dowodzi kompletności historii u brokera ani poprawności każdej ciszy sesyjnej.',
      table(['Zbiór','Dozwolone zastosowanie','Czego nie dowodzi'],[
        ['H1/H4/D1 Last','odkrywanie sygnałów i odrzucanie słabych mechanizmów','wykonania i netto'],
        ['Bid/Ask/Last raw 22.10','wstępne markouty cen stron, diagnostyka kosztów i braków','przewagi wielodniowej, UTC, kosztów całkowitych'],
        ['Trzy okna spreadu 22.10','jawny próg kosztowy / scenariusz stresu','rocznej taryfy i historycznego spreadu'],
        ['cohort-20261026-v1','niezależny forward zamrożonych reguł, audyt integralności','zbioru do strojenia nowych hipotez'],
        ['Stare backtesty','diagnoza błędu Last/Bid i kosztów','dodatniego oczekiwanego P&L']]),
      '## 3. Wyniki H1: ruch po progu kosztów, nie netto rachunku',
      '**U = ATR14 w jednostkach ceny**, nie rzeczywiste R transakcji. W kolumnie po progu odejmujemy '
      'najwyższy obserwowany P95 spreadu z trzech historycznych okien. Stres = 2× ten spread + 0,05 U '
      'na łączne nieskalibrowane prowizje i poślizg. Spread z H1 nie jest używany. '
      'To nie poprawia Last na ceny wykonania; rzeczywiste netto R, cash P&L i DD rachunku są **n/d**, nie zero.',
      table(['Rodzina','N wcz./póź.','Dni wcz./póź.','Śr. wcz. po progu U','Śr. późna brutto U','Śr. późna po progu U','Późny stres U','PF proxy późny','DD proxy późny U','CI95 późne U'],
        [[fam,f"{summaries[fam,'early']['n']}/{summaries[fam,'late']['n']}",f"{summaries[fam,'early']['days']}/{summaries[fam,'late']['days']}",
          f(summaries[fam,'early']['mean']),f(summaries[fam,'late'].get('gross')),f(summaries[fam,'late']['mean']),
          f(summaries[fam,'late'].get('stress')),f(summaries[fam,'late']['pf']),f(summaries[fam,'late']['dd']),ci(summaries[fam,'late'].get('ci95'))] for fam in P.FAMILIES]),
      'PF/DD są opisem zsumowanych zdarzeń o równych jednostkach U, nie wykonalnym portfelem. '
      'Instrumenty i hipotezy współwystępują; nie dodajemy ich liczebności jako niezależnych transakcji. '
      'Bootstrap losuje wspólne pięciodniowe bloki dla rynków. Liczba dni to liczba klastrów, a nie dowód niezależności. '
      'Zależność między tygodniami i zmiany reżimu mogą dalej zaniżać niepewność.',
      table(['Rodzina','Orientacyjny CI skorygowany na 53 testy, późny U'],[[fam,ci(summaries[fam,'late'].get('ci_familywise'))] for fam in P.FAMILIES]),
      'Korekta jest tylko diagnostyczna: ekstremalne kwantyle z 4000 replik są mało precyzyjne, '
      'dane były wcześniej wielokrotnie używane, a podgrupy zwiększają liczbę oglądanych wyników. '
      'Nie traktujemy pojedynczego CI wykluczającego zero jako potwierdzenia przewagi. '
      'Wyniki wszystkich instrumentów, miesięcy, godzin raw i reżimów są w DETAIL_RESULTS.md; nie ukryto ujemnych komórek.',
      '## 4. Jedna doba rzeczywistych stron Bid/Ask',
      'Pierwszy świeży, dodatni snapshot po opóźnieniu 250 ms; zero/crossed quote nie jest zastępowane starszą ceną. '
      'Zachowano kolejność ticków i wiek stron oparty na flagach Bid/Ask, odrębny od Last/volume. '
      'Wiek zmiany <=10 s jest konserwatywnym warunkiem badania, nie dowodem wygaśnięcia niezmienionej oferty. '
      'Wynik poniżej jest **po obserwowanym spreadzie, przed nieznanymi opłatami**. '
      'Brak zaakceptowanego UTC nie przeszkadza mierzyć względnego ruchu na jednej osi, '
      'ale blokuje wiarygodną interpretację sesji, rolloveru i kalendarza.',
      table(['Rodzina','Markouty','Śr. po Bid/Ask U','Śr. obciążenie spreadem U','Stres U','1 s opóźnienia U'],
        [[r['family'],r['n'],f(r['mean']),f(r.get('mean_hurdle')),f(r.get('stress')),
          f(next(x['mean'] for x in d['latency_1s_summary'] if x['family']==r['family']))] for r in d['tick_summary']]),
      'Stres tickowy = dodatkowo 2 punkty na stronę i 0,05 U opłat. Są to jawne scenariusze, '
      'nie oszacowania rzeczywistej prowizji. Zmiana zbioru dostępnych wejść przy 1 s jest raportowana osobno w szczegółach. '
      'Nie ustalono pełnego efektu zerowych kwotowań na wszystkie historyczne zlecenia. '
      'To jedna wspólna doba rynkowa, nie kilkadziesiąt niezależnych prób; dodatni wynik tej doby nie wybiera kandydata. '
      'Średnie dotyczą tylko zdarzeń z dostępnym wejściem i wyjściem. Brak strony przy wyjściu w rzeczywistej strategii '
      'mógłby oznaczać pozostającą otwartą pozycję; nie uznajemy go za transakcję o zerowym wyniku. '
      'Ta selekcja dostępnych par może obciążać średnią i blokuje traktowanie tabeli jako wyniku całej polityki.',
      '## 5. Odrzucenia i najwyżej dwóch kandydatów',
      table(['Rodzina','Dodatnie miesiące','Mniejsza liczba dodatnich rynków spośród dwóch okresów','Decyzja według wcześniejszych progów'],verdicts),
      ('**Kandydaci do nowej niezależnej próby: '+', '.join(selected)+'.** To jedynie przejście screeningu, bez zgody na handel.' if selected else
       '**Zero rodzin stosowanych łącznie na zadanych rynkach spełnia komplet wcześniej zapisanych progów.** Nie obniżono kryteriów ani nie zmieniono tego werdyktu.'),
      'Odrzucenie dotyczy konkretnej definicji i horyzontu 4h. Nie dowodzi, że cała klasa trend/rewersja/wybicie nie może działać. '
      'Dodatni wynik pojedynczego instrumentu lub godziny pozostaje hipotezą post hoc, nie niezależnym odkryciem.',
      '### Jeden trop do niezależnej falsyfikacji: trend na OIL i US100',
      '**Selekcja po obejrzeniu podgrup**, opisana oddzielnie w POSTHOC_SELECTION.md; nie przejście pierwotnej bramki i nie potwierdzony edge. '
      'Dwie konkretne wersje tej samej hipotezy zasługują na zamrożenie i przyszłą falsyfikację: '
      'EMA20/EMA50, horyzont 4h, OIL oraz US100. Parametrów nie zmieniono. '
      'Powód: dostateczna liczba zdarzeń w obu częściach, dodatni znak w obu okresach i 5/6 miesięcy, '
      'dodatni wynik w ustalonym stresie kosztów. Selekcja nie opiera się na najwyższym historycznym P&L. '
      'Oba przedziały niepewności zawierają zero, a mały margines po stresie może zniknąć po prawdziwych opłatach.',
      table(['Rynek trend','N wcz./póź.','Wcz. po progu U','Póź. po progu U','Późny stres U','Dodatnie miesiące','CI95 późne U','CI skorygowane U'],leads),
      'Nie wybrano ekstremalnej rewersji EURUSD (19/11 obserwacji), volatility-momentum GOLD (28/26) '
      'ani US500 (39/29), mimo niektórych wyższych średnich: za małe próby w części chronologicznej. '
      'Cross-momentum EURUSD ma dodatnie części i 5/6 miesięcy, ale w stresie pozostaje zaledwie około 0,007 U; '
      'odkładamy ten trzeci trop ze względu na mały margines względem nieznanych kosztów. '
      'To jakościowy, jawnie post hoc wybór dwóch przypadków do podważenia na nowych danych, nie kolejny test potwierdzający.',
      '## 6. Minimalny kolejny pomiar rzeczywistej wartości',
      '1. Zachować obecny forward zamrożonych strategii i zakończyć audyt jakości już wyznaczonego okna. '
      'Nie dobierać na nim nowych godzin, progów, instrumentów ani parametrów.',
      '2. Dla ewentualnej nowej rodziny najpierw zapisać jeden protokół decyzji, horyzont, faktyczne koszty, '
      'minimalny istotny ekonomicznie efekt, regułę zatrzymania i plan wielokrotnych testów. '
      'Próbę rozpocząć po tym zamrożeniu. Nie przenosić hipotezy do DEMO.',
      '3. Minimalne brakujące dowody do pełnego netto: poprawne UTC wybranego odcinka; '
      'historyczne Bid/Ask bez nieoznaczonych luk; rzeczywista taryfa prowizji/finansowania, '
      'specyfikacja i FX; kalibracja opóźnienia/poślizgu. Tylko dla strategii używających makro '
      'potrzebne są wersje kontekstu dostępne w chwili decyzji. Nie jest konieczna rozbudowa Supervisora do badań offline.',
      '4. Na niezależnym okresie wymagamy dodatniego netto po pełnych kosztach oraz dodatniej dolnej granicy '
      'przedziału uwzględniającego zależności i liczbę kandydatów. Długość próby dobrać analizą mocy '
      'do minimalnego efektu i zmienności z odrębnego okresu kalibracyjnego; 100 transakcji czy 60 sesji '
      'same w sobie nie gwarantują mocy. Zakaz przerywania po pierwszym korzystnym wyniku.',
      'Jeżeli nie ma kandydata, kolejne zadanie powinno być małym badaniem nowego mechanizmu '
      '(np. dłuższy horyzont na H4 z finansowaniem albo zdarzenia makro z archiwum as-of), '
      'z jawnym dopisaniem go do rejestru prób. Nie uruchomiono go automatycznie ani nie rozpoczęto kolejnego etapu infrastruktury.',
      '## 7. DEMO i zbieranie danych — odrębne od wyniku badań',
      f"Odczyt tylko do odczytu: {health['at']}. Terminal połączony: {health['connected']}; "
      f"otwarte pozycje: {len(health['positions'])}; wszystkie z brokerowym SL/TP: {health['all_positions_have_broker_sl_tp']}; "
      f"nierozstrzygnięte operacje: {health['uncertain_operations']}; silnik {health['engine']['status']}; kolektor {health['collector']['status']}. "
      'LIVE wyłączone. Obecność SL/TP nie dowodzi ciągłego BE/trailing. Recovery nie wdrożono, kwarantanny nie czyszczono.',
      '**NO-GO dla pełnej odporności operacyjnej DEMO. GO dla tego screeningu eksploracyjnego. '
      'NO-GO dla twierdzenia o potwierdzonej przewadze lub wdrożenia nowych strategii.** '
      'Oddzielny raport zakończonego okna forward jest audytem jakości, nie źródłem selekcji nowych reguł.',
      '## Odtworzenie i publikacja',
      'Konfiguracja: protocol.py i PROTOCOL.md. Kod: screen.py, report.py, inventory.py. '
      'Testy: test_screen.py. Wyniki lokalne: results-v1/results.json, events.json, tick_events.json, latency_events.json. '
      'Źródła mają hashe w INPUT_HASHES.md; nie publikujemy surowych ticków, baz, rachunku ani szczegółów pozycji. '
      'Dokładne źródła danych trzeba posiadać lokalnie — sam publiczny zestaw kodu i tabel nie zastępuje danych. '
      'Gałąź research/edge-discovery-20261027; bez zmian aktywnego kodu. Przygotowanie synchronizacji nie oznacza pushu.',
      'Wyniki po błędzie technicznym pierwszego uruchomienia zostały policzone ponownie bez zmiany reguł. '
      'Błąd dotyczył nadpisania pól rekordów tickowych, test regresji obejmuje ten przypadek.']
    (folder/'EDGE_DISCOVERY.md').write_text('\n\n'.join(writeup)+'\n',encoding='utf-8')
    details=['# Szczegółowe wyniki — wyłącznie eksploracyjne markouty U',
      'Nie są to wyniki netto rachunku ani niezależne testy. Wszystkie komórki zachowane, bez selekcji po rentowności.',
      table(['Rodzina','Instrument','Okres','N','Dni','Brutto U','Po progu U','Stres U','PF proxy','DD proxy U','CI95 U'],
        [[r['family'],r['alias'],r['period'],r['n'],r['days'],f(r.get('gross')),f(r['mean']),f(r.get('stress')),f(r['pf']),f(r['dd']),ci(r.get('ci95'))] for r in d['by_instrument']]),
      '## Okresy i reżimy',table(['Rodzina','Podział','Wartość','N','Śr. po progu U','Stres U'],
        [[r['family'],r['group'],r['value'],r['n'],f(r['mean']),f(r.get('stress'))] for r in d['subgroups']]),
      '## Ticki i płynność',table(['Rynek','Pierwszy raw','Ostatni raw','Maks. cisza s','Konserwatywnie niewykonywalne ticki','Spread P50 cena','Spread P95 cena'],
        [[r['alias'],r['first_raw'],r['last_raw'],r['max_gap_seconds'],r['conservative_ineligible'],r['spread_p50'],r['spread_p95']] for r in d['tick_data']]),
      'Cisza nie jest automatycznie utratą danych; niezweryfikowane sesje nie pozwalają rozstrzygnąć każdej przerwy. '
      'Wszystkie czasy raw zachowują etykietę bez deklaracji UTC. P50/P95 tickowo ważone, nie czasowo.',
      '## Markouty Bid/Ask 22.10',table(['Rynek','Rodzina','Kierunek','Wejście raw','Wyjście raw','Po spreadzie U','Dodatkowy koszt zerujący ruch (cena)'],
        [[r['alias'],r['family'],'BUY' if r['direction']>0 else 'SELL',r['raw_entry'],r['raw_exit'],f(r['after_hurdle']),r['break_even_extra_price']] for r in ticks]),
      'Dodatkowy koszt zerujący ruch to signed move po spreadzie; wartość ujemna oznacza stratę już bez dodatkowych opłat.',
      '## Opóźnienie 1 s',table(['Rodzina','N','Śr. po spreadzie U'],[[r['family'],r['n'],f(r['mean'])] for r in d['latency_1s_summary']]),
      '## Zdarzenia bez pełnego markoutu',table(['Rynek','Rodzina','Wejście raw','Powód'],[[r['alias'],r['family'],r['raw_entry'],r['reason']] for r in d['tick_missed']]),
      '## Progi spreadu H1 (jednostki ceny)',table(['Rynek','Próg'],[[s,d['cost_hurdles_price'][s]] for s in P.SYMBOLS])]
    (folder/'DETAIL_RESULTS.md').write_text('\n\n'.join(details)+'\n',encoding='utf-8')
    hashes=['# Hash wejść i wyników',f"Protokół {d['protocol']} SHA256 {d['protocol_sha256']}",f"screen.py SHA256 {d['script_sha256']}",
      table(['Ścieżka względem prywatnego katalogu danych','SHA256'],[[x['path'],x['sha256']] for x in d['source_hashes']]),
      table(['Wynik lokalny','SHA256'],[[p.name,hashlib.sha256(p.read_bytes()).hexdigest()] for p in sorted((folder/'results-v1').glob('*.json'))])]
    (folder/'INPUT_HASHES.md').write_text('\n\n'.join(hashes)+'\n',encoding='utf-8')
    print(json.dumps(dict(selected=selected,event_count=len(events),tick_count=len(ticks),decisions=verdicts),ensure_ascii=False))

if __name__=='__main__':
    run(Path(__file__).resolve().parent)
