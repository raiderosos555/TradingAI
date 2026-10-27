# Dodatkowy inwentarz danych, tylko metadane

Nie odczytano wyników forward do wyboru strategii. Poniższe sumy runtime obejmują różne namespaces konfiguracji: nie są liczbą unikatowych ticków ani dowodem kompletności i nie były wejściem do screeningu.

| Instrument | Wiersze ticków runtime | Min raw ms | Max raw ms | Dostępne TF |
|---|---|---|---|---|
| GOLD | 1211149 | 1792740283568 | 1793123213987 | D1,H1,H4,M1,M15,M30,M5 |
| US500 | 694542 | 1792740283568 | 1793123215159 | D1,H1,H4,M1,M15,M30,M5 |
| OIL | 313632 | 1792740286685 | 1793123214148 | D1,H1,H4,M1,M15,M30,M5 |
| EURPLN | 155011 | 1792740306644 | 1793123213066 | D1,H1,H4,M1,M15,M30,M5 |
| EURUSD | 320862 | 1792740283814 | 1793123216371 | D1,H1,H4,M1,M15,M30,M5 |
| GBPUSD | 584761 | 1792740283872 | 1793123216117 | D1,H1,H4,M1,M15,M30,M5 |
| US100 | 2113897 | 1792740283567 | 1793123216283 | D1,H1,H4,M1,M15,M30,M5 |

Historyczny kontekst z edge_audit (raw, nie potwierdzone UTC):

| Instrument | TF | N | Pierwszy raw | Ostatni raw | SHA256 |
|---|---|---|---|---|---|
| GOLD | H4 | 1548 | 2025-10-24T04:00:00 | 2026-10-23T20:00:00 | 61f9210625d8b3d2868b4038b0a2e52b81e029b97ef4a7291a7203756b4349d4 |
| GOLD | D1 | 261 | 2025-10-26T00:00:00 | 2026-10-23T00:00:00 | 084c1fbf22efefe759b3cf7deb4f4a6d310a5f41dcf432d1e0962d1f95808089 |
| US500 | H4 | 1546 | 2025-10-24T04:00:00 | 2026-10-23T20:00:00 | e1465de987cf28a8c6f48b11fc65b5f1dce2edbb96300b198688c6379dc1789b |
| US500 | D1 | 262 | 2025-10-26T00:00:00 | 2026-10-23T00:00:00 | 30c2561ebd15f173e52328a2c75b4493893eada10b709d027c4b58f366dcbf75 |
| OIL | H4 | 1548 | 2025-10-24T04:00:00 | 2026-10-23T20:00:00 | 050b3352eb7986f2fb42cef2ad31f3f476ea21e53714584669a4f4a497bd1521 |
| OIL | D1 | 261 | 2025-10-26T00:00:00 | 2026-10-23T00:00:00 | 26e620cc15660205b03c608ac90d4459feef345336574735eb2a2fd7f073d9c5 |
| EURPLN | H4 | 1607 | 2025-10-24T04:00:00 | 2026-10-23T20:00:00 | 58766b6590bbc63c2dc6343d1b95f6b2aae9297ed051435f283574e0f62a889f |
| EURPLN | D1 | 312 | 2025-10-26T00:00:00 | 2026-10-23T00:00:00 | 49bdfa8d6c0e006f299490fe4d274eca652c2fce819677772719ac9607bd3a34 |
| EURUSD | H4 | 1607 | 2025-10-24T04:00:00 | 2026-10-23T20:00:00 | fde8a3457e4ab46657b6c09231696e1d80a7f6f651cef3f2dd6cd9a913d1caee |
| EURUSD | D1 | 312 | 2025-10-26T00:00:00 | 2026-10-23T00:00:00 | 006e737a30c44941f762acc9d19e2374193cddb52770b10422312c242f8ed75b |
| GBPUSD | H4 | 1607 | 2025-10-24T04:00:00 | 2026-10-23T20:00:00 | d239d6b5c7849d2be10533f01a1e99209a588d8869b2249e1b40c66a7af07ccc |
| GBPUSD | D1 | 312 | 2025-10-26T00:00:00 | 2026-10-23T00:00:00 | c542772dbcfd187088993ef2bfbcbc2544e509d2ba6a3c7f5ea95ee13ad0ddcc |
| US100 | H4 | 1546 | 2025-10-24T04:00:00 | 2026-10-23T20:00:00 | 153a88a92e85013e4771475ebb64c94cbe34851e4916d339f899820d21746190 |
| US100 | D1 | 262 | 2025-10-26T00:00:00 | 2026-10-23T00:00:00 | f2219bf4b95d421890bdc8f8e7858997713e6b4f9a38d82184c410aef40bc254 |

Baza runtime zawiera także snapshots, deals i orders. Dane rachunku i identyfikatory konfiguracji pozostają prywatne. Historyczne kopie danych pokrywają się; nie sumujemy ich jako niezależnych obserwacji.
