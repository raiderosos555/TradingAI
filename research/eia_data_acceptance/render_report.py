"""Render sanitized acceptance evidence. Raw files and identities stay private."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
from validate_tables import HERE,validate

def main():
    root=HERE.parents[1]
    r=validate(HERE/'private/tables-v1')
    baseline=json.loads((root/'research/edge_data_unblock/private/local-before.json').read_text())['protected_hashes']
    changed=[p for p,h in baseline.items() if hashlib.sha256((root/p).read_bytes()).hexdigest()!=h]
    status=json.loads((root/'state/forward_validation/cohort-20261026-v1/status.json').read_text())
    evidence={'at':datetime.now(timezone.utc).isoformat(),'protected_files':len(baseline),
              'changed':changed,'collector':{k:status.get(k) for k in ('status','at','configuration_matches_frozen')}}
    out=HERE/'private/local-after-v1.json'
    if out.exists():raise RuntimeError('Refuse overwrite')
    out.write_text(json.dumps(evidence,indent=2),encoding='utf-8')
    if changed:raise RuntimeError('Protected files changed: inspect before reporting')
    lines=['# EIA + OIL: odbiór małej próby — 29.10.2026','',
      '**GO: integralność datowanych tabel EIA. NO-GO: ścisły replay publikacji i wykonania OIL.**','',
      'To odbiór danych, nie test strategii. Nie obliczono markoutu, P&L ani R. COT pozostaje odrzucony w zamrożonej postaci.','',
      '## Co rzeczywiście uzyskano','',
      '- 12 kolejnych tabel: 04.03–20.05.2026, 78 773 bajty. Nowe pobranie 11 tabel: 72 214 bajtów; pierwsza próbka ponownie użyta z oryginalnym hashem.',
      '- 36 obserwacji zmian zapasów: ropa bez SPR, benzyna, destylaty. Wszystkie hashe, okresy i kontrole arytmetyki PASS.',
      '- 33 porównania poziomu tego samego tygodnia w sąsiednich wydaniach: 33 zgodne, 0 różnic. To nie dowodzi braku wcześniejszych rewizji.',
      '- 8 testów automatycznych PASS, w tym DST, uszkodzona arytmetyka, duplikaty, oddzielanie sekcji oraz blokady uprawnień/izolacji terminala.',
      '', '## Dane archiwalne (zmiany w mln baryłek)','',
      '| Data wydania | Planowany UTC | Ropa bez SPR | Benzyna | Destylaty |',
      '|---|---|---:|---:|---:|']
    for e in r['events']:
        lines.append('| '+e['release_date']+' | '+e['scheduled_utc'][11:16]+' | '+' | '.join(e['stocks'][k]['change'] for k in ('crude','gasoline','distillates'))+' |')
    lines += ['', '## Czas i pierwsza dostępność','',
      'Planowe 10:30 America/New_York przeliczono przez zoneinfo: 04.03 = 15:30 UTC, pozostałe daty = 14:30 UTC po zmianie DST. '
      'Żadna z tych dat nie jest wyjątkiem w [harmonogramie EIA](https://www.eia.gov/petroleum/supply/weekly/schedule.php). '
      '[Archiwum wydania 04.03](https://www.eia.gov/petroleum/supply/weekly/archive/2026/2026_03_04/wpsr_2026_03_04.php) podaje datę wydania i tydzień referencyjny; nie dostarcza dowodu dokładnego pierwszego odbioru.',
      '', 'Dla wszystkich 12 rekordów `published_at=null`, `first_print_verified=false`, brak konsensusu sprzed publikacji. '
      'Metadane Last-Modified z poprzedniej próby HEAD w wielu przypadkach poprzedzają publikację i nie są jej timestampem. '
      'Downloader zachował dokładny czas rozpoczęcia żądania, a nie ukończenia odbioru: `request_started_utc` zachowano; `received_at_exact=null`. '
      'Nie przemianowano czasu żądania na historyczny pierwszy odbiór. Zachowano URL, SHA256 i pliki źródłowe prywatnie.',
      '', '## OIL i izolacja terminala','',
      'Użytkownik potwierdził logowanie, ale dwie kontrole procesów i sonda wykazały wyłącznie aktywny terminal; osobny proces badawczy nie był uruchomiony. '
      'Sonda przerwana przez `require_running` przed initialize i przed żądaniem historycznych ticków. '
      '**0 wykonanych zapytań tickowych, 0 potwierdzonych okien OIL.** To brak gotowego terminala, nie dowód braku historii u brokera. '
      'Poproszono o pozostawienie drugiego okna otwartego; oczekujemy potwierdzenia.',
      '', 'Kod wymaga tego samego rachunku DEMO, osobnego katalogu procesu i danych, uprawnień inwestorskich oraz wyłączonych Algo/DLL. '
      'Limit: 12 zakresów po 1 sekundzie, 10 s na proces; stop po pierwszym błędzie/pustej lub niewykonywalnej próbce. '
      'Nawet pozytywne Bid/Ask nie dowodzą ich aktualności; zachowane są flagi zmian Bid/Ask/Last. '
      'Surowy timestamp API nie certyfikuje historycznego UTC. Timeout klienta nie gwarantuje zatrzymania synchronizacji osobnego terminala.',
      '', '## Co konkretnie blokuje eksperyment','',
      '1. Terminal badawczy nieobecny w kontroli procesów; brak potwierdzonej dostępności ticków dla tych dat.',
      '2. Brak dowodu pierwszych wersji/actual-time oraz konsensusu sprzed publikacji — nie można nazywać zmian zapasów zaskoczeniem rynku.',
      '3. Niezweryfikowana historyczna oś czasu brokera, pełne okna Bid/Ask, luki i świeżość kwotowań.',
      '4. Brak przypisanych do dat specyfikacji, kosztów i rolloveru CFD OIL. Dzisiejsza specyfikacja nie zastępuje historycznej.',
      '', '## Jeden następny krok','',
      'Dokończyć minimalną sondę dostępności w uruchomionym terminalu badawczym. Nie pobierać dużych okien przed jej odbiorem. '
      'Jeżeli sonda przejdzie, połączyć dowód historycznego UTC z dowodem first-availability EIA; dopiero wtedy zatwierdzić ograniczone okna i zamrozić test reakcji po opóźnieniu. '
      'Bez konsensusu wolno rozważyć osobno zdefiniowany test reakcji ceny po wydarzeniu, ale nie test surprise; nadal wymaga poprawnego czasu i wykonania.',
      '', '## Ochrona DEMO i status','',
      f'{len(baseline)} chronionych plików: hashe identyczne z bazą. Nie zmieniano aktywnego DEMO, strategii ani Risk Managera; nie wysyłano zleceń. '
      f'Odczyt kolektora: `{evidence["collector"]["status"]}`, czas statusu `{evidence["collector"]["at"]}`, zgodność konfiguracji `{evidence["collector"]["configuration_matches_frozen"]}`. '
      'Nie jest to ponowna certyfikacja odporności operacyjnej DEMO; wcześniejsze blokady pozostają.',
      '', '| Decyzja | Wynik |','|---|---|',
      '| Integralność pobranych tabel | GO |',
      '| Kompletność danych EIA/OIL do ścisłego replay | NO-GO |',
      '| Wiarygodny backtest po kosztach | NO-GO |',
      '| Potwierdzona przewaga | NIE wykazana; w tej próbie nie testowano strategii |',
      '| Duże pobranie / push | Nie wykonano; wymagają odrębnej zgody |','']
    (HERE/'REPORT.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps(evidence))

if __name__=='__main__':main()
