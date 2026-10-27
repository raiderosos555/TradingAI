> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Publiczne źródła czasu — wynik dodatkowej weryfikacji

Sprawdzono źródła pierwotne brokera; nie zaakceptowano nowego segmentu UTC.

- [Instrukcja OANDA TMS MT5](https://help.oanda.com/eu/en/faqs/mt5-user-guide-eu.htm) identyfikuje serwer `EXAMPLE-DEMO-SERVER`. Sama instrukcja nie dostarczyła mapowania surowych timestampów Python API dla 22.10.2026.
- [Specyfikacja TMS Connect Professional z 05.06.2023](https://www.oanda.com/eu-en/sites/default/files/document_files/SIF%20TMS%20CONNECT%20PRO%20ENG%2005.06.2023.pdf) podaje godziny handlu w CET zimą i CEST latem. Jest to opis godzin sesji w starej specyfikacji; **nie dowodzi kodowania surowego czasu API ani obowiązywania parametrów kontraktów w 2026**. Nie przeniesiono starych kosztów do modelu.
- [OANDA UK MT5](https://www.oanda.com/uk-en/trading/platforms/metatrader-5/) opisuje GMT+2 zimą / GMT+3 latem. To inna oferta regionalna; nie utożsamiono jej z serwerem TMS, dla którego lokalne kotwice wskazywały inne przesunięcia.

Wniosek badawczy: wspólna marka OANDA, strefa czasowa centrali lub opis godzin handlu nie zastępują dowodu raw→UTC dla konkretnego serwera i okresu. Bramka UTC pozostaje zamknięta, zamiast wybierać wygodną regułę z innej oferty.
