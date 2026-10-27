> Kopia do przeglądu kodu i badań. Dane prywatne usunięto; pełne dowody i manifesty pozostają lokalnie. Daty i decyzje dotyczą daty oryginalnego raportu, nie bieżącego stanu.

# Proponowany pierwszy test DEMO — jeszcze niewykonany

Cel: sprawdzić techniczną ścieżkę otwarcia, potwierdzenia stanu i zamknięcia jednej
pozycji przez Risk Manager, dziennik i oficjalne MT5 API. Nie jest to sygnał inwestycyjny
ani uruchomienie ciągłego autonomicznego handlu.

Proponowany zakres zgody operatora:

[Fragment z danymi finansowymi/rachunku pominięty w kopii do GitHub.]

Przed próbą pozostają wymagane: potwierdzone equity początku bieżącej doby UTC,
zatwierdzenie limitów/kosztów i osobna zgoda na opisany zakres. Każda operacja przejdzie
niezależny Risk Manager i order_check. Warunki są ponownie odczytywane tuż przed
wykonaniem; sama zgoda nie pomija żadnej blokady.

Późniejsza weryfikacja pendingów, TP1, BE, trailing i restartu terminala z aktywną
pozycją wymaga osobnego uzgodnionego scenariusza. Pierwsza próba open/close nie jest
automatycznie dowodem poprawności wszystkich rodzajów wykonania u tego brokera.
