> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Kontrolowane testy wykonania — etap 2A

**35/35 testów przechodzi. Pełny backtest nie został uruchomiony.**

- [Wyniki i porównanie reguł](EXECUTION_PARITY.md)
- [Ograniczenia i warunki dalszej pracy](REMAINING_LIMITATIONS.md)
- [Konfiguracja v1](config.v1.json)
- [Wynik maszynowy](tests.json)
- [Pełne ślady przypadków](traces.json)

Raporty w katalogu nadrzędnym pozostają niezmienionym, zahashowanym wynikiem etapu 1. Ten katalog jest osobnym rozszerzeniem; nie zastępuje jego ustaleń o ograniczonym pokryciu ticków i niezweryfikowanym czasie historycznym.

Odtwarzanie offline z C:\TradingAI:

```powershell
.\.venv\Scripts\python.exe research\tick_validation\stage2\run.py
```

Tylko syntetyczny broker w pamięci. Bez połączenia z MT5, bez zmian produkcyjnych, bez optymalizacji strategii. Czas i koszty fixtures są jawne i nie oznaczają dowodów historycznych.
