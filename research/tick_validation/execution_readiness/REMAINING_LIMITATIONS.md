> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Warunki przed pierwszym wiarygodnym replay

1. **Czas.** Potrzebny dowód mapowania raw→UTC dla badanego okna i warm-up, wraz z granicami sesji. Aktualny offset ani kilka kotwic z następnej doby nie wystarczają. Nie zmieniono zegara aktywnego DEMO.
2. **Właściwy zakres doby.** Po mapowaniu UTC ustalić brakujące fragmenty ticków i ponownie przyciąć warm-up oraz FX. Nie utożsamiać raw 22.10 z 22.10 UTC.
3. **Kalendarz dostępny wtedy.** Zamrożone wejścia używają filtra kalendarza. Potrzebne archiwum wersji harmonogramu z czasem publikacji/odbioru oraz pokryciem całego horyzontu zleceń. Późniejszy kalendarz ani brak wydarzeń w pliku nie oznacza CLEAR. Nie znaleziono takiego archiwum dla 22.10. Nie wymyślono newsów i nie dopisano ich do reguł strategii.
4. **Kontrakt i koszty.** Potwierdzić obowiązujące wtedy tick size, lot/step, stops/freeze, filling/execution, waluty, margin, prowizję, swap oraz wybór i stronę konwersji FX/zaokrąglenia. Bieżące kalkulacje są kandydatem modelu, nie dokumentem historycznym. Tick nie gwarantuje fill ani płynności: opóźnienie/poślizg wymagają jawnego, skalibrowanego modelu i analizy wrażliwości.
5. **Integracja historyczna.** Kontrole czterech silników przeszły, ale pełny adapter portfela z danymi historycznymi, harmonogramem 10/60 s, margin i rachunkiem gotówkowym nie jest ukończony. Trzeba jawnie rozstrzygnąć granice próby, pozycje początkowe, brak wyceny oraz remisy czasów między instrumentami. Testy syntetyczne nie zastępują tej pracy.
6. **Dane niewykonywalne.** Zachować brak możliwości realizacji i oryginalny indeks ticka. Nie przesuwać stopa ani wyceny do wcześniejszej ceny. Model ważności niezmienionego Bid/Ask wymaga dowodu ciągłości.

## Minimalne następne badanie

Najpierw pozyskać brakujący dowód UTC i historyczny kalendarz dla jednego instrumentu oraz jego warunki rozliczeń. Dopiero wtedy wykonać jeden replay 22.10 zamrożonych reguł, z 200 H1 warm-up, indywidualnym rachunkiem i pełnym śladem decyzji; równolegle stary model na tym samym zakresie. Wersja jednego instrumentu usuwa nieznaną kolejność równoczesnych zdarzeń różnych rynków, ale nie usuwa kalendarza, kosztów ani UTC.

Jeśli wersji kalendarza z 22.10 nie da się odzyskać, **nie da się odtworzyć pełnej zamrożonej polityki tej doby**. Minimalną alternatywą jest pierwszy nowy odcinek z kompletnym, rejestrowanym na bieżąco kontekstem, tickami i niezależnymi kotwicami czasu. Takie zbieranie nie wymaga zmiany strategii, ale trzeba zapewnić archiwizację wersji zamiast nadpisywania plików. Nie uruchomiono automatycznie kolejnego etapu ani nowej automatyzacji.

Po pozytywnej walidacji integracji potrzebne są osobne, nieoglądane okresy i więcej transakcji do badania przewagi. Jedna doba może wykryć błędy modelu; nie potwierdzi stabilnej rentowności.
