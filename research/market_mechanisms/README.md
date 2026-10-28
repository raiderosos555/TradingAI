# TradingAI — ograniczone badanie mechanizmów rynku

Zacznij od **EDGE_RESEARCH_RESULTS.md**. Przegląd źródeł: RESEARCH_REVIEW.md;
dostępność danych: DATA_FEASIBILITY.md; definicje i ranking przed obliczeniami:
HYPOTHESIS_REGISTRY.md. DETAILS.md pokazuje każdy rynek i obie podpróby,
INPUT_HASHES.md przypina dane i kod. DEMO_AUDIT_RECEIPT.md jest osobnym odbiorem
wcześniej uruchomionego audytu; nie stanowi kolejnego etapu Recovery.

Wersja mechanisms-v1: 4 mechanizmy cenowe obliczone, 2 newsowe nieweryfikowalne.
822 zdarzenia to markouty Last, nie wykonania ani net P&L. Stara historia jest
eksploracyjna. Kod nie łączy się z MT5, nie wysyła zleceń i nie zapisuje do DEMO.

## Odtworzenie lokalne

Python 3 + NumPy (dokładne wersje w raporcie wyników). Dane brokera, rachunku,
SQLite i per-event JSON nie są publikowane. Sama kopia GitHub pozwala na audyt
kodu i agregatów, ale pełne odtworzenie liczb wymaga prywatnych źródeł o hashach
z INPUT_HASHES.md oraz zapisanej migawki private/feasibility.json. Nie należy
ponownie pobierać dzisiejszych świec i udawać, że to te same dane.

Z katalogu research/market_mechanisms, w środowisku z NumPy:

```powershell
python -m unittest discover -s . -p test_experiment.py -v
python experiment.py --root C:/TradingAI --out private/reproduction.json
python verify.py --root C:/TradingAI
python report.py --base .
```

Eksperyment odmawia nadpisania pliku wyniku. Oryginał to private/results-v1.json;
odtworzenie powinno zgadzać się w events/results/filters/relationships, z wyjątkiem
znacznika wykonania i rozszerzonej listy pomocniczych skryptów. Report.py czyta
oryginał i odtwarza Markdown bez ponownego testu strategii.

`audit_data.py --root C:/TradingAI --out NOWY_KATALOG` tworzy nową migawkę
metadanych. Nie odtworzy dawnych liczników rosnącej bazy. Nie uruchamiać go
zamiast zapisanego audytu i nie nadpisywać zapieczętowanych dowodów.
`receipt.py` służy wyłącznie odbiorowi już istniejącego raportu i lokalnego
odczytu brokera; odmawia nadpisania odbioru. Nie jest cyklicznym monitorem.

## Granice testów

Testy jednostkowe mają sztuczne kontrolowane liczby wyłącznie do weryfikacji
arytmetyki i przyczynowości; żaden taki wynik nie trafia do raportu rynkowego.
Sprawdzają zależność od prefiksu danych, znak/normalizację pary, brak wypełniania
luk, kolejność signal→next open, brak nakładania, Holm i deterministyczność.
verify.py sprawdza hashe źródeł, niezmienność aktywnego kodu/config, granice
podprób, rzeczywistą arytmetykę zdarzeń i kompletność raportów.

Nie podmieniamy Last na Bid/Ask, nie certyfikujemy UTC/DST, nie rozstrzygamy
historycznej wykonalności kontraktów. Nie deklarujemy przewagi ani wdrożenia.
Nie dobieramy na podstawie tej rundy nowych parametrów.
