DA CORREGGERE
ce2301d5289ee00cb94c14575d4a31521f67a33ae8031f6b56e78f083d77d002

Revisore: Kimi (motore diverso dall'autore, Claude). Data: 2026-09-07.
Oggetto: secondo blocco di PROPOSTA-campi-obbligatori.md (righe 308-384),
aggiornamento di tests/integration/test_seamless_parita_contabile.py.
Metodo: impronta ricalcolata con `sed -n '308,384p' | sha256sum`; confronto
riga per riga col file attuale; lettura integrale dei sei collaudi seamless in
casinoking-platform/tests/integration/. Ragionamento sul codice: NON ho rieseguito
la suite (stack e db non avviati in questa sessione).

1. Impronta: SI, coincide. Ricalcolata: ce2301d5289ee00cb94c14575d4a31521f67a33ae8031f6b56e78f083d77d002,
   identica a quella dichiarata (riga 76 della proposta). Verificata per controllo
   anche quella del primo blocco (righe 79-304): a68b87eb...99c1, coincide.

2. Il blocco AGGIUNGE soltanto. Nessun assert cancellato, indebolito o reso meno
   stringente. Conteggio: file attuale 3 assert (righe 38, 58, 61 del file attuale);
   testo proposto 3 assert (righe 353, 380, 383 della proposta), identici nel testo,
   incluso quello contabile finale `Decimal(data["balance_after"]) == Decimal("1015.00")`.
   Le uniche differenze: reserve_payload guadagna 4 campi (righe 333-336 proposta)
   con commento (329-332); commit_payload guadagna 5 campi (363-369) con commento
   (367-368); `is_win: True` e' solo spostato in fondo al dizionario (riga 48 attuale
   -> riga 370 proposta), stesso valore. Copertura intatta.

3. Firma HMAC valida, ordine corretto. Reserve: payload completato a riga 337,
   corpo serializzato riga 345, firma calcolata riga 346 SUL corpo, invio righe
   348-352 con `content=body_res` — gli stessi byte firmati. Commit: payload
   completato riga 371, corpo riga 372, firma riga 373, invio righe 375-379 con
   `content=body_com`. La firma e' sempre calcolata dopo la costruzione del corpo
   e sul corpo effettivamente spedito. (Nota ininfluente: usa `json.dumps` senza
   separators compatti, a differenza degli altri collaudi; irrilevante perche'
   firma e invio usano lo stesso oggetto.)

4. Valori coerenti. `provider_code: "ck_collaudo"` (righe 333 e 363) coincide con
   l'intestazione x-provider-id (righe 351 e 378): nessun caso di incoerenza
   collaudato in silenzio. `reserve_tx_id: "tx_res_001"` (riga 369) punta esattamente
   al tx_id della reserve precedente (riga 327). `currency: "EUR"` come in tutti gli
   altri collaudi seamless. nonce distinti fra reserve e commit (righe 336, 366).
   Nessuna osservazione.

5. SI, con i due blocchi insieme test_seamless_parita_contabile.py torna verde.
   Ragionamento: con il blocco 1 applicato, ReserveRequest richiede 10 campi
   (9 base + amount) e vieta gli extra (extra="forbid", riga 128); il payload
   proposto ne manda esattamente 10 (righe 322-337) -> niente 422. CommitRequest
   ne richiede 12 (base + amount, is_win, reserve_tx_id); il payload ne manda
   esattamente 12 (righe 356-371) -> niente 422. Gli handler del blocco 1
   (righe 172-303) non leggono nessuno dei campi nuovi: la logica contabile e'
   byte-identica all'attuale, quindi saldi e risposte non cambiano. HMAC valido
   (punto 3), guardia fuori_produzione invariata. Il collaudo resta verde sul
   merito, non perche' sia stato annacquato.

6. SI, restano ALTRI tre file che i due blocchi insieme farebbero passare da
   verde a rosso. Censimento di tests/integration/ (casinoking-platform):

   - test_seamless_parita_contabile.py — corretto dal blocco 2: resta VERDE.
   - test_seamless_campi_obbligatori.py — i 6 rossi di design: _payload completo
     (righe 57-75) -> diventa VERDE. Esito atteso corretto.
   - test_seamless_fornitore_sospeso.py — RICONFERMATO SALVO: i quattro campi di
     protocollo ci sono in _payload (righe 26-36) e reserve_tx_id e' passato in
     tutte le commit (righe 135, 198) e rollback (righe 167, 213). Resta VERDE.
   - test_seamless_scrive_davvero.py — DIVENTA ROSSO: _payload (righe 26-38) non
     conosce reserve_tx_id. Commit senza reserve_tx_id alle righe 94-97 (assert 200
     riga 98) e 118-121 (assert 200 riga 122), rollback alle righe 141-143 (assert
     200 riga 144): tutti ricevono 422. Tre collaudi su quattro persi.
   - test_seamless_ordine_operazioni.py — DIVENTA ROSSO: _payload (righe 24-47)
     senza reserve_tx_id; gli assert 200 sulle commit alle righe 99, 131, 136, 155,
     179, 213, 246 ricevono 422. Falliscono TUTTI e sei i test del file, compresi
     quelli che attendono 4xx: la commit di preparazione, che si aspettano 200,
     fallisce prima.
   - test_seamless_controlli_di_casa.py — PARZIALMENTE ROSSO: i quattro test di
     sola reserve (righe 68-106) restano verdi (payload completi, atteso 4xx);
     test_reg02 (riga 109) fallisce: commit righe 120-124 (atteso 200) e rollback
     righe 140-144 (atteso 200) senza reserve_tx_id -> 422.

   Totale: 10 collaudi in 3 file da verde a rosso. Il criterio dichiarato dalla
   proposta stessa ("nessun altro collaudo deve peggiorare", riga 72) fallirebbe.

VERDETTO (tre righe).
Il blocco in se' e' corretto e pulito: impronta esatta, solo aggiunte, nessun
assert toccato, firma HMAC valida, valori coerenti, e parita_contabile torna verde.
Ma la correzione e' incompleta: lo stesso rilievo che ha bocciato il blocco 1 vale
per scrive_davvero (3 test), ordine_operazioni (6 test) e controlli_di_casa (1 test).
DA CORREGGERE: la proposta deve aggiornare anche quei tre file (reserve_tx_id su
commit e rollback) prima di passare alla firma di Michele.
