# Jeden następny krok — próbka odbiorcza NFP point-in-time

Wąskim brakującym zbiorem jest **24 kolejnych publikacji NFP z2019–2020**:
kompatybilny konsensus miesięcznej zmiany payrolls sprzed publikacji, pierwszy
actual, późniejsze rewizje oraz dowody czasu ich dostępności. Wybór wynika z
mechanizmu informacyjnego i możliwości kontroli BLS, nie rankingu markoutów.

Pierwszy dostawca do weryfikacji: Econoday Historical Economic Data;
alternatywa tego samego zbioru: Trading Economics Calendar Point-in-Time.
Adresy i zakresy w DATA_SOURCES.md. **Cena obu: wymaga indywidualnej wyceny;
nie uzyskano wiążącej kwoty.** Nie wysłano wiadomości ani nie zakupiono usługi.
To propozycja małej próbki do oceny przed decyzją o zakupie, nie polecenie
pozyskania pełnego archiwum. FXMacroData50 USD/mies. nie zastępuje tego zbioru.

Wymagane kolumny: stabilny event ID; okres referencyjny; jednostka tys.osób;
forecast median i liczebność/panel; forecast_available_at UTC i evidence;
first_actual, actual_published_at, vendor_received_at; revised values oraz
revision_available_at; typ/miejsce źródła. Rozdzielić zmianę zatrudnienia od
poziomu, miesięczny konsensus od kwartalnej prognozy i czas planowany od odbioru.

Warunki odbioru:24/24 zdarzeń bez domyślnego wypełniania; forecast istnieje
przed publikacją; first print zgodny z datowanym BLS; DST America/New_York
zamiast stałego offsetu; umowa pozwala utrwalić próbkę do wewnętrznego researchu.
Brak pola lub nieudokumentowana rekonstrukcja czasu oznacza odrzucenie wiersza.
Próbka24 nie potwierdza edge — sprawdza, czy warto nabyć większy zbiór.

Po odbiorze dopiero przygotować ograniczone Bid/Ask EURUSD w oknach
[-10,+60]min tych wydarzeń. Najpierw TMS, potem próbka innego OTC feedu jako
oddzielna replikacja mechanizmu. Hipoteza A1 jest zamrożona; trzeba uzyskać
24 wcześniejsze zdarzenia do skali surprise, nie wyliczać jej z przyszłości.
Żadnych opłat ani większego pobrania bez zgody. Alternatywny feed nie dowodzi
wykonania u brokera i nie uzupełnia automatycznie jego kosztów.

**Czy potrzebujemy płatnych danych?** Do obecnych testów wskaźników i małych
eksperymentów IV — nie. Do tego historycznego konsensusu — prawdopodobnie tak,
o ile próbka potwierdzi brak dostępnego legalnego odpowiednika. Nie kupować
pakietu cenowego ani news sentiment zamiast dokładnie tego brakującego pola.

Aktualizacja zakresu właściciela w trakcie pracy: nowa runda COT/IV/makro jest
w `../alternative_data_edge/`; jej NEXT_STEP.md określa bieżący priorytet.
Powyższy odbiór NFP zachowujemy jako konkretny wariant dla kierunku news,
bez uruchamiania równoległego programu zakupów.
