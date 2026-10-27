from pathlib import Path
import json,hashlib
A=Path(__file__).resolve().parent;ROOT=A.parents[2]
d=json.loads((A/'availability.json').read_text());rows=d['samples']
table=[]
for alias in ['EURPLN','EURUSD','GBPUSD','GOLD','OIL','US100','US500']:
    cells=[]
    for date in ['2026-04-27','2026-10-23']:
        match=[r for r in rows if r['alias']==alias and r['start'].startswith(date)]
        cells.append(str(match[0]['count']) if match and match[0]['status']=='OBSERVED' else 'TIMEOUT' if match else 'NIE BADANO')
    table.append('| '+alias+' | '+' | '.join(cells)+' |')
checks=[]
for r in json.loads((A.parent/'inputs/protected_hashes.json').read_text()):
    checks.append(dict(path=r['path'],unchanged=hashlib.sha256((ROOT/r['path']).read_bytes()).hexdigest()==r['sha256']))
assert all(r['unchanged'] for r in checks)
(A/'production_integrity.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
report='''# Etap 3 — odczyt rzeczywistych ticków i ponowna ocena zegara

2026-10-25. Wyłącznie odczyt DEMO i lokalne badanie danych. Bez zmiany czasu/config, zleceń, strojenia strategii i pełnego backtestu.

## Dostępność

Nowy pomiar rozdziela import biblioteki, initialize, metadane i copy_ticks_range. Pierwsza próba: inicjalizacja około 0,008 s (według zegara ściennego), odczyt 1696 ticków GOLD około 1,3 s. Nie zmieniano terminala ani biblioteki. Nie ustalono przyczyny wcześniejszych timeoutów i nie uznaje się ich za brak historii.

Poniżej liczby rekordów w przedziale **12:00:00–12:01:00 surowej osi API** każdego dnia. To nie są jeszcze potwierdzone godziny UTC. Koniec przedziału jest wyłączny. Żądania używają świadomych strefowo datetime, bez dodatkowego przesuwania czasu.

| Instrument | 27.04.2026 | 23.10.2026 |
|---|---:|---:|
'''+ '\n'.join(table)+'''

Dodatkowo powtórzono minutę GOLD z 22.10, raw 15:00–15:01: **1696 rekordów jest identycznych i w identycznej kolejności jak odpowiadający fragment wcześniejszej godzinnej próbki**. To sprawdzenie powtarzalności źródła, nie nowy niezależny materiał.

Łącznie pobrano 6525 rekordów w 12 udanych minutowych próbach; 1696 pokrywa się ze starym materiałem. Przybyło 4829 rekordów z innych okien. Wszystkie mają poprawne dodatnie Bid/Ask, nieprzekreślony spread i niemalejący time_msc. Zachowano rekordy o jednakowej milisekundzie. Sprawdzono cztery strony cenowe BUY/SELL na każdym ticku. Szczegółowe pierwsze/ostatnie czasy, luki wewnętrzne i spread są w availability.json.

Próba OIL z kwietnia przekroczyła 40 s. Log zatrzymał się na **TICKS_START**, po poprawnej inicjalizacji i odczycie symbolu. Zakończono wyłącznie proces tej próby; terminal i silnik pozostały uruchomione. Po tej próbie przerwano serię: kwietniowych US100 i US500 nie badano. TIMEOUT nie oznacza EMPTY. Obserwowane udane próbki nie dowodzą ciągłego pokrycia miesięcy ani najstarszej dostępnej daty.

## Czas — istotne doprecyzowanie

Źródło obserwatora używa `TimeTradeServer()-TimeGMT()`. MetaQuotes opisuje TimeTradeServer jako wyliczenie po stronie terminala zależne od ustawień czasu komputera; TimeGMT również uwzględnia lokalny czas i DST. Zatem weekendowa zmiana tego wyrażenia z +7200 do +3600 s **nie jest samodzielnym dowodem zmiany czasu serwera ani kodowania historycznych ticków**. Jest obserwacją arytmetyki klienta. [TimeTradeServer](https://www.mql5.com/en/docs/dateandtime/timetradeserver), [TimeGMT](https://www.mql5.com/en/docs/dateandtime/timegmt).

Nowe odczyty latest_tick nadal pochodzą z piątku. Zegar hosta i świeżo zapisany plik obserwatora nie czynią starego ticku świeżą kotwicą czasu. Dotychczasowe deal/intent kotwice z 23.10 wspierają +7200 s tylko wokół tych operacji. Nie potwierdzono dokładnej granicy DST ani przesunięć wiosną lub w starszych danych. Lista dopuszczonych segmentów historycznego mapowania UTC nadal jest pusta.

Dokumentacja Python MT5 deklaruje semantykę UTC. Rozbieżność z lokalnymi pomiarami wymaga wyjaśnienia na świeżych, zsynchronizowanych kotwicach; nie uprawnia do globalnego odjęcia stałej. [copy_ticks_range](https://www.mql5.com/en/docs/python_metatrader5/mt5copyticksrange_py).

Odnaleziona dokumentacja OANDA Europe Limited mówi o czasie związanym z końcem dnia w Nowym Jorku. Nie przypisano tej polityki polskiemu serwerowi EXAMPLE-DEMO-SERVER, ponieważ dotyczy innej jednostki/rodziny rachunków. [Dokumentacja OANDA Europe Limited](https://www.oanda.com/uk-en/trading/standard-account/differences/).

## Artefakty i dalsze kroki

- `captures/`: oryginalne ticki, bieżące specyfikacje (nie historyczne), fazy API, argumenty, timeout i SHA-256 dla każdej próby.
- `availability.json`: zakresy obserwowane, kolejność, Bid/Ask, spread i powtórzenie starej próbki.
- `clock_evidence/`, `clock_review.json`: kopia kodu obserwatora, eksportów i statusu procesu; wnioski i źródła czasu.
- `production_integrity.json`: kod/config zgodne z wcześniejszymi hashami.

Reprodukcja analizy offline: `.\\.venv\\Scripts\\python.exe research\\tick_validation\\stage3\\analyze.py`. Nowy odczyt API: `bounded_probe.py --alias EURUSD --start 2026-10-23T12:00:00+00:00 --end 2026-10-23T12:01:00+00:00`; zapisuje nowy, oddzielny katalog. `scan.py` to ograniczona seria próbek; nie pobiera całej historii.

Następny etap danych powinien rozszerzać pokrycie blokami z jawną mapą braków i kontrolą limitu czasu. Pełny replay nadal wymaga potwierdzenia historycznego zegara, sesji, warunków kontraktów, FX i kosztów. Żadna z nowych próbek nie stanowi oceny rentowności. Wszystkie oglądane dane pozostają eksploracyjne.
'''
(A/'REPORT.md').write_text(report,encoding='utf-8')
files=[p for p in A.rglob('*') if p.is_file() and '__pycache__' not in p.parts and p!=A/'manifest.json']
(A/'manifest.json').write_text(json.dumps(dict(stage='PHASED_RAW_TICK_AVAILABILITY',files=[dict(path=p.relative_to(A).as_posix(),sha256=hashlib.sha256(p.read_bytes()).hexdigest()) for p in sorted(files)]),indent=2),encoding='utf-8')
print('Report and manifest saved; protected production files unchanged:',len(checks))
