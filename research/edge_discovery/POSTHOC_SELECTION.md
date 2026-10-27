# Jawna selekcja po screeningu

Ta notatka powstała **po** odczytaniu results-v1. Nie zmienia zamrożonego
PROTOCOL.md, kierunków, okien, horyzontu, progów ani wyników. Wszystkie osiem
rodzin w wersji łącznej nie przeszło pierwotnej bramki. Nie deklarujemy sukcesu.

Użytkownik oczekuje wskazania najwyżej 2–3 hipotez wartych przyszłej walidacji.
Nie należy utożsamiać ujemnej średniej rodziny na siedmiu rynkach z dowodem,
że każda jej wersja na pojedynczym instrumencie jest ujemna. Dlatego jawnie
odnotowujemy **jeden mechanizm w dwóch wersjach rynkowych**:

- trend EMA20/EMA50 na OIL, kierunek z zamkniętej H1, wyjście 4h;
- ta sama reguła na US100.

To tropy post hoc, wybrane z 53 kombinacji. Wybrano je z powodu dodatniego
znaku obu części chronologicznych, 5/6 dodatnich miesięcy, ponad 200 zdarzeń
w każdej części i dodatniego, choć małego marginesu w uprzednio określonym
stresie. Nie dlatego, że mają najwyższą średnią. Wykorzystanie tych samych
danych do wyboru wyklucza nazywanie ich niezależną walidacją. Oba CI obejmują 0.

Odrębna próba ma rozpocząć się dopiero po zapisaniu kompletnego protokołu
wykonania i uzasadnieniu kosztów. Obecne archiwum forward jest zarezerwowane
dla dotychczasowych strategii; nie wykorzystano jego wyniku do tej selekcji.
Nie uruchomiono nowych reguł w DEMO ani automatycznej pętli optymalizacji.
Jedna doba dodatnich markoutów breakout nie była kryterium wyboru.

Przed niezależną próbą trzeba ustalić minimalny ekonomicznie istotny efekt,
liczbę sesji na podstawie mocy z uwzględnieniem klastrowania, jednorazowy termin
oceny oraz korektę na dwie wybrane wersje. Koszt testujemy osobno dla każdego
instrumentu; wspólnej marży, ryzyka i sumy P&L nie wolno dopisywać bez modelu.
Nowa definicja SL, TP lub horyzontu byłaby nową hipotezą, a nie kontynuacją
walidacji tej samej reguły.
