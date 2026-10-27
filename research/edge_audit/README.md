> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Audyt przewagi TradingAI

**Werdykt: przewaga niepotwierdzona. Kontynuować badania; nie promować strategii na podstawie obecnych backtestów.**

Najważniejszy nowy błąd: świece brokera są oparte na Last, a symulacje zakładały Bid. Potwierdzono to rekonstrukcją godziny ticków wszystkich siedmiu kontraktów. Ponadto spread GOLD przyjęty w walidacji wynosił 1 punkt, podczas gdy próbki tickowe miały mediany 24–31 punktów. Wyników nie poprawiano niejawnie.

- [Dane i metodologia](DATA_AUDIT.md)
- [Diagnostyka wszystkich zapisanych transakcji](TRADE_DIAGNOSTICS.md)
- [US100 a OIL](US100_VS_OIL.md)
- [Trzy hipotezy](EDGE_HYPOTHESES.md)
- [Walidacja, walk-forward i wrażliwość](VALIDATION_REPORT.md)
- [Rekomendacja i odtworzenie analizy](NEXT_STEPS.md)

Zakres: 21 234 H1, 88 pierwotnych przebiegów, 4294 rekordy transakcji (nakładające się badania), 54 komórki analizy wrażliwości. 628 najstarszych rekordów ma brakujące atrybuty oznaczone UNKNOWN; nie dopisano im kierunku ani strategii.

JSON/CSV znajdują się obok raportów. `verification.json` dokumentuje kontrole zgodności, `integrity_check.json` niezmienność pierwotnych plików, `inputs/frozen-originals/` ich kopie. Katalog `isolated/` zawiera badawcze wyniki bez uprawnień wykonawczych.

DEMO, jego konfiguracja, Execution Engine i Risk Manager pozostały bez zmian. Audyt nie wysłał zleceń. Brak niezależnego holdoutu oraz danych do potwierdzenia wpływu briefingu/newsów.
