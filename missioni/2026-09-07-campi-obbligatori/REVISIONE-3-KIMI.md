APPROVATA

# Revisione terza — Kimi, 7/09/2026 — proposta campi obbligatori (rev3)

Scope: i tre blocchi nuovi (scrive_davvero, ordine_operazioni, controlli_di_casa);
per i blocchi 1 e 2 solo il riscontro delle impronte.

## 1. Impronte

Ricalcolate con `sed -n` sui byte strettamente fra i marcatori. Tutte e cinque
coincidono con la tabella del dossier:

| Blocco | Righe estratte | Impronta |
|---|---|---|
| router.py | 139-364 | `a68b87eb...99c1` COINCIDE |
| parita_contabile.py | 368-444 | `ce2301d5...d002` COINCIDE |
| scrive_davvero.py | 448-611 | `aa73d7e9...f7a0` COINCIDE |
| ordine_operazioni.py | 615-886 | `4fc5f789...57fe` COINCIDE |
| controlli_di_casa.py | 890-1059 | `9ff9b6c6...a412` COINCIDE |

Blocchi 1 e 2: le impronte coincidono anche con quelle registrate in
REVISIONE-1-KIMI.md (`a68b87eb...99c1`) e REVISIONE-2-KIMI.md (`ce2301d5...d002`).
Invariati da quando li ho approvati nel merito.

## 2. Copertura: nessun assert sparito

Conteggio delle istruzioni `assert` (non delle chiamate agli helper `_assert_*`):

| File | Attuale | Proposto |
|---|---|---|
| scrive_davvero | 15 | 15 |
| ordine_operazioni | 16 | 16 |
| controlli_di_casa | 9 | 9 |

Le cifre 15/15, 16/16, 9/9 del dossier sono CONFERMATE (e anche 3/3 su
parita_contabile). Righe TOLTE, elenco completo dai diff: nessuna contiene
un'asserzione, un controllo o una condizione. Sono solo:

- scrive_davvero: 3 righe `game_session_id, _reserve_tx_id = _open_reserve(...)`
  (rinomina della variabile) e 3 chiamate `_payload(...)` senza `reserve_tx_id`
  (righe attuali 93, 118, 140);
- ordine_operazioni: 6 rinomine `_reserve_tx_id` e 6 chiamate `_payload` senza il
  campo (righe attuali 87, 121, 148, 153, 161, 172, 177, 185, 201, 222, 234, 255);
- controlli_di_casa: la firma `def _open_reserve(...) -> None` (riga 60), la riga
  `tx_id=f"controlli-reserve-{uuid4().hex}"` dentro l'argomento (riga 63), e due
  chiamate `_open_reserve(...)` il cui valore era buttato via (righe 118, 138).

Zero righe tolte con contenuto di verifica.

## 3. Le asserzioni sopravvissute sono ancora le stesse

SI. In controlli_di_casa `_open_reserve` (proposto, righe 961-967): `tx_id` e'
costruito alla riga 961, passato a `_payload` alla riga 963 (`tx_id=tx_id`) e
restituito alla riga 967. E' letteralmente la stessa variabile: il valore che
finisce nel payload spedito e' quello restituito. Nessun assert e' diventato
vacuo: le condizioni attorno (`assert response.status_code == 200` in
`_open_reserve`, i `_assert_rejected_without_balance_change`, i conteggi sul
registro in scrive_davvero) sono immutate.

## 4. reserve_tx_id punta alla trattenuta giusta

SI, in tutti i casi:

- scrive_davvero: ogni test usa il `reserve_tx_id` restituito dalla propria
  `_open_reserve` (proposto: righe 545-549, 570-574, 594-596). Il valore e'
  `response.json()["tx_id"]`, cioe' quello che risponde la piattaforma: coincide
  con quello spedito perche' il router (blocco 1, riga 266) risponde
  `"tx_id": req.tx_id`, cioe' fa eco al tx_id della richiesta. Stesso valore.
- ordine_operazioni: `_open_reserve` restituisce il tx_id che il test ha spedito
  (righe 686-693); per l'eco del router e' lo stesso valore di scrive_davvero.
  Ogni commit/rollback porta il `reserve_tx_id` della propria sessione.
- controlli_di_casa, test_reg02: NON incrociate. Caso 1: `reserve_tx_id` aperto
  su `existing_game_session_id` (riga 1020) e usato nella commit sulla stessa
  sessione (riga 1024). Caso 3: `rollback_reserve_tx_id` aperto su
  `rollback_game_session_id` (riga 1041) e usato nel rollback sulla stessa
  sessione (riga 1045). Due variabili distinte, due sessioni distinte, nessun
  incrocio.

## 5. Firma HMAC

Regge in tutti e tre i file. `_post` (scrive righe 493-501, ordine 669-681,
controlli 933-941 del proposto) serializza il payload gia' completo —
`reserve_tx_id` e' aggiunto dentro `_payload`, prima — poi calcola
`hmac.new(secret, body, ...)` e spedisce `content=body`. La firma e' sempre
sugli stessi byte spediti, calcolata dopo la costruzione del corpo. Idem nel
blocco 2 (parita_contabile, righe 405-411 e 432-438).

## 6. reserve_tx_id non finisce su nessuna reserve

Verificato. In tutti e tre i `_payload` il campo e' aggiunto solo se non None
(scrive 488-489, ordine 664-665, controlli 928-929), e nessuna chiamata a
`/seamless/wallet/reserve` lo passa: ne' le `_open_reserve`, ne' le reserve
dirette (ordine riga 722-731; controlli righe 974, 985, 995, 1005, 1032, 1054).
Con `extra="forbid"` su `ReserveRequest` un campo di troppo darebbe 422: non
succede.

## 7. Nessun chiamante resta rotto

Censimento completo di `/seamless/wallet/` nel repository (8 file):

- i 4 collaudi della proposta: risanati dai blocchi;
- `test_seamless_campi_obbligatori.py`: omette i campi APPOSTA (e' il collaudo
  che prova il rifiuto, righe 119-180) e i suoi payload pieni hanno tutti i
  campi; diventa verde;
- `test_seamless_fornitore_sospeso.py`: ha GIA' tutti i campi, `reserve_tx_id`
  incluso (righe 24-43), e non compare in nessuno dei due elenchi di rossi:
  verde prima, verde dopo;
- `docs/INT-04_Provider_Integration_API.md` (righe 14-27): solo documentazione,
  non eseguibile. Nota, non blocco: i suoi esempi di body erano gia' vecchi
  (`player_id`, `transaction_id`) e ora lo sono di piu' — da aggiornare in un
  passo documentale, non in questa proposta;
- nessuno script, seme o altro file chiama queste rotte.

Distinzione verdi/rossi, stavolta misurata sugli elenchi e non contata a mano:
i collaudi VERDI che sarebbero diventati rossi senza i blocchi 3-5 sono quelli
di scrive_davvero (4), parita_contabile (1) e i due verdi di ordine_operazioni
— tutti coperti dalla proposta. I rossi gia' rossi (5 di controlli_di_casa, 4
di ordine_operazioni, lotti B/C/D) restano rossi: non sono una regressione.

## 8. La misura dichiarata e' credibile

Confronto diretto dei due elenchi: MISURA-prima ha 19 righe, MISURA-dopo 13.
`comm` mostra che la differenza e' ESATTAMENTE i sei collaudi di
test_seamless_campi_obbligatori.py (i 2 commit/rollback senza reserve_tx_id e i
4 parametrizzati currency/nonce/provider_code/timestamp), uno per uno quelli
elencati alle righe 116-121 del dossier. NESSUN collaudo compare solo nel
secondo elenco: zero verdi diventati rossi. Quanto al totale 657->663: coerente
con 19->13 (+6 verdi), ma non l'ho rieseguito io sullo stack — ho verificato la
coerenza interna degli elenchi, non la loro genuinita'. La controprova finale
resta il gate post-firma dichiarato alle righe 129-134 del dossier.

## Verdetto

Impronte esatte, copertura intatta, reserve_tx_id sempre della trattenuta giusta,
firma sempre sui byte spediti, nessun chiamante rotto rimasto, misura coerente.
I tre blocchi nati dal mio rilievo del secondo giro lo chiudono davvero.
La firma puo' arrivare; la condizione di arresto 5 resta la rete di sicurezza.
