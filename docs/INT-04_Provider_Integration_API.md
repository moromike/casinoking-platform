# INT-04: Seamless Wallet API — Guida per i fornitori di gioco

*Versione 2.0 — allineata al codice l'8/09/2026, chiusura della Fase 9.*

**La versione 1.0 di questo documento era falsa in ogni campo tecnico**: nominava
`player_id`, `transaction_id` e la valuta `EUR`, che nel prodotto non esistono. Chi ci si
fosse basato avrebbe scritto un'integrazione che non funziona. E' il motivo per cui questo
file ora dichiara la data in cui e' stato verificato contro il codice.

Questo documento definisce come un fornitore esterno (per esempio M&M Games) parla con la
piattaforma CasinoKing. **Il fornitore non gestisce mai il saldo del giocatore.**

---

## 1. Autenticazione

Ogni richiesta e' firmata in HMAC con la chiave condivisa del fornitore.

**`provider_code` viaggia dentro il corpo della richiesta, non solo nell'intestazione.**
L'intestazione sceglie la chiave con cui verificare; l'identita' che vale e' quella
firmata. Se le due non coincidono, la richiesta e' rifiutata.

## 2. Campi obbligatori su OGNI richiesta

**Nessun campo ha un valore predefinito**, per scelta: su un percorso che muove denaro un
dato inventato e' peggio di un errore.

| Campo | Cos'e' |
|---|---|
| `user_id` | il giocatore |
| `game_session_id` | **il round**, non la sessione di gioco lunga |
| `game_code` | il gioco |
| `wallet_type` | quale portafoglio |
| `tx_id` | l'anti-doppione: identifica **questa** operazione |
| `provider_code` | il fornitore, firmato |
| `currency` | **la valuta del conto, che si RIFIUTA se diversa: non viene convertita** |
| `timestamp` | senza, una richiesta intercettata resta valida per sempre |
| `nonce` | l'anti-rigioco, distinto da `tx_id` |

## 3. Le tre rotte

### `POST /api/v1/seamless/wallet/reserve`
Trattiene l'importo della puntata. In piu' ai campi comuni: `amount`.

### `POST /api/v1/seamless/wallet/commit`
Chiude il round. In piu': `amount`, `is_win`, e **`reserve_tx_id`**.

**`reserve_tx_id` e' obbligatorio e non e' una formalita':** senza, «accredita mille euro»
sarebbe una richiesta valida per chiunque abbia la chiave del fornitore, e la chiave
diventerebbe una stampante di denaro. La piattaforma lo confronta con quello conservato
sul round.

### `POST /api/v1/seamless/wallet/rollback`
Annulla la trattenuta e **restituisce i soldi**. In piu': **`reserve_tx_id`**, obbligatorio
per la stessa ragione — un annullamento che non dice *quale* trattenuta annulla risponderebbe
«riuscito» muovendo i soldi sbagliati.

## 4. Ripetere una richiesta e' sicuro — leggere prima di implementare i ritentativi

**La stessa operazione ripetuta identica restituisce la prima risposta e non muove denaro
una seconda volta.** Vale per `reserve`, `commit` e `rollback`.

«Identica» significa **la stessa in tutto**: stesso round, stessa valuta, stesso
`reserve_tx_id`, stesso importo. Se qualcosa diverge **non e' un ritentativo**: e' una
richiesta diversa con una chiave gia' usata, e viene **rifiutata con un conflitto**, non
accettata.

La risposta porta `already_exists`: `false` la prima volta, `true` sul ritentativo.

## 5. Gli errori — cosa fare quando arriva un rifiuto

**Un rifiuto `4xx` non va mai ritentato.** Porta sempre `retryable: false`, ed e' la
piattaforma che ve lo dice: non lo dovete dedurre dal codice HTTP.

**Un `5xx` e' un guasto nostro** ed e' l'unico caso in cui ha senso riprovare.

L'elenco delle traduzioni e' **chiuso**: ogni condizione imputabile al chiamante ha un
codice suo. Tutto cio' che non e' in elenco resta un `500`, perche' e' un guasto vero e
deve urlare — **non ve lo attribuiamo**.

| Codice | Cosa e' successo | Cosa fare |
|---|---|---|
| `CK.WALLET.INSUFFICIENT_BALANCE` | il giocatore non ha abbastanza saldo | chiedergli di ricaricare |
| `CK.SEAMLESS.CURRENCY_MISMATCH` | valuta diversa da quella del conto | correggere la valuta |
| `CK.SEAMLESS.AMOUNT_BELOW_MINIMUM` | importo sotto il minimo | correggere l'importo |
| `CK.SEAMLESS.AMOUNT_ABOVE_MAXIMUM` | importo oltre il massimo | correggere l'importo |
| `CK.SEAMLESS.ROUND_NOT_FOUND` | il round non esiste | verificare `game_session_id` |
| `CK.SEAMLESS.GAME_NOT_FOUND` | `game_code` sconosciuto | verificare il codice gioco |
| `CK.SEAMLESS.GAME_CODE_INVALID` | `game_code` non valido | verificare il codice gioco |
| `CK.SEAMLESS.IDEMPOTENCY_KEY_TOO_LONG` | `tx_id` oltre il limite | accorciarlo |
| `CK.LEDGER.IDEMPOTENCY_CONFLICT` | stessa chiave, richiesta **diversa** | **non ritentare**: la richiesta e' cambiata |
| `CK.GAME.ROUND_CLOSED` | il round e' gia' chiuso | non ritentare |
| `CK.AUTH.PLAYER_SUSPENDED` | il giocatore e' sospeso | vedi sotto |

## 6. Giocatori sospesi

Un giocatore sospeso — per autoesclusione, antiriciclaggio o frode — **non puo' aprire un
round nuovo**: la `reserve` viene rifiutata e il saldo non si muove.

**Ma puo' chiudere quelli gia' aperti.** `commit` e `rollback` di un round in corso
continuano a funzionare, di proposito: bloccargli anche la chiusura significherebbe
tenergli i soldi dentro.

---

*Verificato contro il codice l'8/09/2026. Se modificate il confine seamless, questo
documento va aggiornato nello stesso commit: la versione 1.0 e' rimasta falsa per mesi.*
