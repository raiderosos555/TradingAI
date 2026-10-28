"""Render summaries from saved results without recalculating any hypothesis."""
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent;PRIVATE=HERE/'private'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def f(x):return 'NA' if x is None else f'{x:.2f}'
def ci(x):return 'NA' if x is None else '['+', '.join(f(v) for v in x)+']'
def write(name,parts):
    p=HERE/name
    if p.exists():raise RuntimeError('Refuse overwrite '+name)
    p.write_text('\n'.join(parts)+'\n',encoding='utf-8')

def main():
    d=read(PRIVATE/'experiment-v1.json');v=read(PRIVATE/'validation-v1.json')
    audit=['# COT i ceny: audyt danych, 29.10.2026','',
      '**Odblokowano 5010 rekordów COT z lat 2010–2025, sześć kontraktów; nie certyfikowano first-vintage.**','',
      '## Transport i rozmiar','',
      'Python urllib/OpenSSL ponownie zatrzymał się na handshake TLS (10 s); w poprzedniej rundzie występował też błąd certyfikatu. Ten sam mały URL przez Windows curl/Schannel zwrócił HTTP200, ssl_verify_result=0. Nie wyłączano TLS, walidacji certyfikatu ani revocation. Wybrano działający stos systemowy, bez zmian globalnego trust store. Dokładna pierwotna przyczyna łańcucha certyfikatów/transportu OpenSSL pozostaje nierozstrzygnięta.','',
      'Zatwierdzony limit 5 000 000 B: zużyto **4 492 081 B**, wliczając 1 MB uciętego HTML i błędne próby formatu. Ucięty HTML, puste odpowiedzi HTTP200 i strona formularza nie są używane jako ceny. Poprawne kompletne HTML zweryfikowano przed parsowaniem. Końcowy skrypt pobiera bezpośrednio działający format.','',
      '[Oficjalny ZIP TFF 2024](https://www.cftc.gov/files/dea/history/fut_fin_txt_2024.zip): HEAD HTTP200, Content-Length=563591 B. Pierwszy HEAD zgłosił curl63 z powodu limitu 16384 B porównanego z Content-Length; nie był to błąd TLS. Treści ZIP nie pobrano, bo po diagnostyce zostało 507919 B zatwierdzonego budżetu. Schemat zweryfikowano na prawidłowym API; zgodności wszystkich rekordów API z ZIP nie deklarujemy.','',
      '## Mapowanie i pokrycie','',
      '| Rynek | Kod | Klasyfikacja | Rekordy | Pierwsza–ostatnia data pozycji | Największy odstęp dni |',
      '|---|---|---|---:|---|---:|']
    mapping=[('GOLD','088691','Disaggregated / managed money'),('OIL WTI','067651','Disaggregated / managed money'),('US500','13874A','TFF / leveraged funds'),('US100','209742','TFF / leveraged funds'),('EURUSD','099741','TFF / leveraged funds'),('GBPUSD','096742','TFF / leveraged funds')]
    for name,code,kind in mapping:
        s=d['cot_audit'][code];audit.append(f"| {name} | {code} | {kind} | {s['rows']} | {s['first']} – {s['last']} | {s['max_gap_days']} |")
    audit+=['','API: [TFF futures-only](https://publicreporting.cftc.gov/resource/gpe5-46if.json) i [Disaggregated futures-only](https://publicreporting.cftc.gov/resource/72hh-3qpy.json). Ograniczono projekcję do daty, kodu, OI, long, short i FutOnly. Sortowanie po kodzie i dacie, limit4000 na zbiór; odpowiedzi poniżej limitu. Unikalne pary kod–data; dodatnie OI, 0≤long/short≤OI. Nie zmieszano futures z combined, TFF z Disaggregated ani z Legacy.','',
      'GOLD=COMEX Gold, OIL=NYMEX WTI physical, nie Brent. US500=E-mini S&P500, US100=Nasdaq mini; nie sklejamy kodów z consolidated 13874+/20974+. Nazwa GBP zmieniła się w 2022, kod pozostał ten sam. EURPLN nie ma w tym zbiorze bezpośredniego odpowiednika. COT to agregat pozycji we wszystkich terminach kontraktu, nie cena kontraktu wykonania.','',
      'Pobranie nie dowodzi ciągłości klasyfikacji każdego tradera: [CFTC wyjaśnia zmiany Form40 i klasyfikacji](https://www.cftc.gov/MarketReports/CommitmentsofTraders/index.htm). Dlatego zmiana netto nie jest czystym przepływem transakcyjnym.','',
      '## Dostępność informacji','',
      'Normalny harmonogram: wtorkowe pozycje publikowane w piątek o15:30 America/New_York; święta mogą przesuwać termin. [CFTC schedule](https://www.cftc.gov/MarketReports/CommitmentsofTraders/ReleaseSchedule/index.htm). Daty pozycji zachowano również wtedy, gdy są poniedziałkowe. API nie dostarcza dla każdego rekordu historycznego published_at/received_at ani pełnego zestawu rewizji.','',
      'Reguła użycia w eksperymencie: po14 dniach od daty pozycji (kontrola28), wyłączenie całych pięcioraportowych okien dotykających zakłóceń. To konserwatywne **założenie**, nie udowodniony najwcześniejszy czas użycia. Bez release evidence najwcześniejszy czas faktycznie udowodniony dla pobranej wersji to jej obecny odbiór zapisany w manifeście. Żadna obserwacja nie wchodzi w decyzję we wtorek jej pomiaru.','',
      'Wyłączenia obejmują [shutdown2013](https://www.cftc.gov/PressRoom/PressReleases/6745-13), [catch-up2019](https://www.cftc.gov/PressRoom/PressReleases/7864-19), [incydent ION2023](https://www.cftc.gov/PressRoom/PressReleases/8655-23) i zaległości2025 z [oficjalnych komunikatów](https://www.cftc.gov/MarketReports/CommitmentsofTraders/HistoricalSpecialAnnouncements/index.htm). Dokładne konserwatywne maski w zamrożonym protokole. Historyczne TFF sprzed2010 zostały opublikowane retrospektywnie; test zaczyna decyzje w2011, nie w2006.','',
      'Nie wykonano vintage replay. Znane korekty/reklasyfikacje pozostają istotną niepewnością. [Warunki CFTC](https://www.cftc.gov/sites/default/files/cftc/cftcprivacy.htm): dane urzędowe public domain, z podaniem źródła; nie publikujemy surowego pakietu.','',
      '## Faktyczna próbka cen FX','',
      '| Rynek | Poprawne obserwacje 2010–2025 | Pierwsza–ostatnia | ND, bez imputacji |','|---|---:|---|---:|']
    for k,s in d['price_audit'].items():audit.append(f"| {k} | {s['rows']} | {s['first']} – {s['last']} | {s['ND']} |")
    audit+=['','Brak weekendów jest cechą kalendarza H.10; ND nie zastąpiono kursem poprzedniego dnia. Do porównania wymagane są rzeczywiste referencje w obu datach. Najstarsze surowe strony zawierają2000–2026, ale filtr analityczny dopuszcza wyłącznie2010–2025. Ceny i daty Fed nie są cenami ani godzinami realizacji CFD TMS.','',
      '## Powtarzalność','',f"Protokół SHA256: `{d['protocol_hash']}`. Kod obliczeń SHA256: `{d['code_hash']}`. Manifesty URL/odbiór/rozmiar/SHA256 oraz pełne odrzucenia są lokalnie w private/. Poniżej hashe właściwych wejść:",'','| Plik wejściowy | SHA256 |','|---|---|']
    for k in ('tff.raw','disagg.raw','fed_eur_complete.raw','fed_gbp_complete.raw'):audit.append(f"| {k} | `{d['source_hashes'][k]}` |")
    write('COT_DATA_AUDIT.md',audit)

    out=['# COT ponad trend: wyniki eksperymentu','',
      '**NIE potwierdzono dodatkowej informacji ani przewagi po rzeczywistych kosztach.** Osiem zapisanych prób:2FX ×2 horyzonty ×2 opóźnienia. Wszystkie Holm8=1 w końcowym okresie2022–2025. Bez optymalizacji i bez zmiany kierunku hipotezy.','',
      'To warunkowy test na obecnych wersjach historycznych COT i referencjach Fed. Nie certyfikowany PIT backtest, nie P&L TMS. Daty obserwacji są opóźnione zgodnie z protokołem; brak first-vintage nadal blokuje wniosek o rzeczywistej historycznej wykonalności. Kwoty poniżej to **bps na wspólną okazję**, także gdy B wybiera cash; nie bps na wybrane wejście.','',
      '## Końcowy blok2022–2025, wszystkie próby','',
      '| Rynek / horyzont / lag | n / B / kwartały | A | B | B−A | 95%CI kwartały | Holm8 | Δ przy dopasowanej ekspozycji | p losowego filtra |',
      '|---|---:|---:|---:|---:|---|---:|---:|---:|']
    for k,res in d['results'].items():
        s=res['confirmation'];out.append(f"| {k} | {s['n']} / {s['selected']} / {s['quarters']} | {f(s['A']['mean'])} | {f(s['B']['mean'])} | {f(s['delta'])} | {ci(s['inference']['ci'])} | {f(s['holm8'])} | {f(s['exposure_matched_delta'])} | {s['random_filter']['upper_tail_p']:.3f} |")
    out+=['','Horyzonty nakładają się między osobnymi wariantami;3 518 zapisanych par łącznie NIE jest liczbą niezależnych transakcji. W obrębie wariantu okna1/4 tygodnie nie zachodzą na siebie. EURUSD i GBPUSD mają wspólny czynnik USD. Końcowa część ma tylko4 bloki roczne; kwartały nadal mogą być zależne.','',
      '## Stabilność chronologiczna — główne opóźnienie14dni','',
      '| Wariant | Część | n / B | A | B | B−A | CI roczne B−A |','|---|---|---:|---:|---:|---:|---|']
    for k,res in d['results'].items():
        if not k.endswith('lag14'):continue
        for period in ('discovery','walk_forward','confirmation'):
            s=res[period];out.append(f"| {k} | {period} | {s['n']} / {s['selected']} | {f(s['A']['mean'])} | {f(s['B']['mean'])} | {f(s['delta'])} | {ci(s['annual_ci'])} |")
    out+=['','discovery=2011–2017; walk_forward=2018–2021; confirmation=2022–2025. Ostatnia nazwa jest etykietą podziału, nie stwierdzeniem potwierdzenia edge. Roczne foldy nie uczą parametrów. Wszystkie te okresy po tej analizie są widziane; nie wolno ich ponownie nazwać niezależnymi po strojeniu.','',
      '## Progi kosztowe — ostatni blok, wszystkie próby','',
      'Base:5bps za okazję +2bps/tydzień. Stress:15bps +5bps/tydzień. Cash nie ponosi progu. Progi są hipotetyczne i nie są historyczną prowizją/spreadem/finansowaniem TMS.','',
      '| Wariant | A base | B base | Δ base | A stress | B stress | Δ stress | Δ stress dopasowana ekspozycja |',
      '|---|---:|---:|---:|---:|---:|---:|---:|']
    for k,res in d['results'].items():
        b=res['confirmation']['hurdles']['base'];s=res['confirmation']['hurdles']['stress'];out.append(f"| {k} | {f(b['A'])} | {f(b['B'])} | {f(b['delta'])} | {f(s['A'])} | {f(s['B'])} | {f(s['delta'])} | {f(s['exposure_matched_delta'])} |")
    out+=['','Poprawa delty po podniesieniu kosztów może wynikać wyłącznie z mniejszej ekspozycji B. Dlatego dodatnia Δ stress sama nie stanowi przewagi informacyjnej; wymagamy kontroli ekspozycji, niepewności i placebo. Nie policzono fikcyjnego R, lotów, brokerowego Profit Factor ani obsunięcia rachunku.','',
      '## Kontrole — ostatni blok','',
      '| Wariant | long-only | short-only | cash | losowy filtr średnia | COT52tyg n | B na wspólnym n | placebo52tyg |',
      '|---|---:|---:|---:|---:|---:|---:|---:|']
    for k,res in d['results'].items():
        s=res['confirmation'];z=s['lag52_placebo'];out.append(f"| {k} | {f(s['long_only'])} | {f(s['short_only'])} | 0 | {f(s['random_filter']['mean'])} | {z['n']} | {f(z['B'])} | {f(z['placebo'])} |")
    out+=['','## Roczne foldy i reżimy, lag14 — bez ponownego dopasowania','',
      '| Wariant | Rok | n / B | A | B | Δ |','|---|---|---:|---:|---:|---:|']
    for k,res in d['results'].items():
        if not k.endswith('lag14'):continue
        for y,s in res['annual'].items():out.append(f"| {k} | {y} | {s['n']} / {s['selected']} | {f(s['A']['mean'])} | {f(s['B']['mean'])} | {f(s['delta'])} |")
    out+=['','| Wariant | Zmienność (cała próba) | n | Δ |','|---|---|---:|---:|']
    for k,res in d['results'].items():
        if not k.endswith('lag14'):continue
        for regime,s in res['regimes'].items():out.append(f"| {k} | {regime} | {s['n']} | {f(s.get('delta'))} |")
    out+=['','Próg high/low korzysta tylko z wcześniejszych cen i wcześniejszej mediany; nie stanowi dodatkowo dobieranej strategii. Zestawienia są opisowe, nie nowymi potwierdzeniami. Szczegółowe odrzucenia i wyniki obu kierunków są w zapisanym JSON.','',
      '## Decyzja','',
      '**Odrzucamy promocję tej zamrożonej hipotezy COT.** Brak istotnej delty, zmiany znaku między horyzontami/opóźnieniami i brak certyfikacji as-of nie uzasadniają dalszego strojenia. Nie obalono wszystkich zastosowań COT ani wszystkich rynków — cztery kontrakty poza FX nie były testowane cenowo. Żadnego kandydata do DEMO.','',
      f"Walidacja:11 testów automatycznych PASS; niezależna kontrola {v['arithmetic_rows']} wierszy, hashy protokołu/kodu/8 artefaktów PASS. {v['protected_files']} chronionych plików runtime/config bez zmian. Kolektor w chwili {v['collector']['at']}: {v['collector']['status']}, zgodność konfiguracji zamrożonej={v['collector']['configuration_matches_frozen']}. Nie jest to audyt odporności DEMO.",
      '',f"Hash protokołu `{d['protocol_hash']}`; wyniki obliczone {d['at']}. Kod/źródła/protokół oraz niekorzystne wyniki pozostają zapisane. Surowe archiwa i szczegółowe wyniki JSON zostają lokalnie."]
    write('COT_EXPERIMENT_RESULTS.md',out)

if __name__=='__main__':main()
