Status: ACTIVE
Last meaningful update: 2026-09-04

# Contratto API Seamless Wallet v1 — UNICO CONTRATTO VALIDO

Integrazione piattaforma ↔ gioco in modello **seamless wallet**.

## 0. Stato e precedenza

- Questo documento e' **l'unico contratto API valido** per l'integrazione
  piattaforma ↔ gioco. Risolve le riconciliazioni **RIC-01** e **RIC-02**
  (Fase 3, 2026-09-04).
- Recepisce il **Documento 31** (direzione ufficiale: seamless wallet) e il
  **Documento 34** (set di endpoint scelto).
- **Il Documento 35 e' SUPERATO**: gli endpoint `/internal/platform/rounds/...`
  e `/internal/games/mines/launch` **non esistono e non devono essere
  implementati**. Del Documento 35 restano validi solo il mapping dal codice
  attuale (sez. 6) e l'idea dell'adapter `platform_round_gateway` (sez. 7).
- In caso di conflitto con qualunque altro documento, vale questo.

### Perche' e' stato scelto il set del Documento 34

1. Coerenza col Documento 31: il namespace `/internal/v1/seamless-wallet/`
   nomina esplicitamente il modello scelto; `/internal/platform/` (Doc. 35) e'
   generico.
2. Versionamento esplicito `/v1/`, presente solo nel Documento 34.
3. Un solo endpoint di settlement (`/rounds/settle` con campo `outcome`)
   invece di due (`settle-won` / `settle-lost`): superficie minore, estensibile
   a esiti futuri (`void`, `rollback`) senza nuovi path.
4. Il Documento 35 dichiara di «integrare» il 34 ma ne cambia gli endpoint
   senza deprecarlo: e' la fonte della contraddizione RIC-02.

## 1. Modello

Seamless wallet (Documento 31, sez. 2 e 10):

- **il wallet appartiene alla piattaforma**
- **il ledger appartiene alla piattaforma**
- **il gioco non gestisce conti, saldi o posting**
- il gioco possiede RNG, fairness, board, reveal e stato tecnico della partita
- la piattaforma contabilizza apertura e chiusura della round
- durante i reveal **nessuna scrittura finanziaria**

## 2. Entita'

| Entita' | Owner | Significato |
| --- | --- | --- |
| `play_session` | piattaforma | presenza del player nel gioco, da ingresso a uscita (audit, analytics) |
| `platform_round` | piattaforma | round **finanziaria**: si apre con la bet, si chiude con lo settle |
| `game_round` | gioco | round **tecnica**: board, fairness, reveal, esito |
| `game_launch_token` | piattaforma | token di handoff che autorizza il lancio del gioco |

### 2.1 `game_launch_token`

JWT emesso dalla piattaforma, verificato dal backend gioco con la chiave/issuer
della piattaforma.

Claim minimi:

- `iss`, `aud`
- `sub` = `player_id`
- `platform_session_id`
- `play_session_id`
- `game_code`
- `iat`, `exp` (TTL breve, consigliato <= 5 minuti)
- `nonce`

Regole: monouso (legato a una sola apertura valida del gioco); non sostituisce
il bearer piattaforma generale; mai riusato per backoffice o API non-gioco.

## 3. Trasporto e autenticazione server-to-server

- Solo HTTPS; in locale, rete interna Docker.
- Ogni chiamata server-to-server porta `Authorization: Bearer <service_token>`
  rilasciato dal backend chiamato al backend chiamante (una credenziale per
  direzione).
- Gli importi sono **stringhe decimali** (mai float). Valuta MVP: `CHIP`.
- Ogni richiesta finanziaria porta una `idempotency_key` obbligatoria.

## 4. API Platform → Game

### `POST /internal/v1/game-launch/validate`

Vive nel **backend gioco**. Valida il `game_launch_token` e apre/conferma la
sessione tecnica di gioco.

Request:

```json
{
  "game_launch_token": "jwt"
}
```

Response:

```json
{
  "game_code": "mines",
  "player_id": "uuid",
  "platform_session_id": "uuid",
  "play_session_id": "uuid",
  "game_play_session_id": "uuid",
  "expires_at": "2026-09-04T12:00:00Z"
}
```

## 5. API Game → Platform

Vivono nel **backend piattaforma**.

### `POST /internal/v1/seamless-wallet/rounds/open`

Apre la round finanziaria: verifica saldo, registra il debit della puntata,
crea il `platform_round`.

Request:

```json
{
  "play_session_id": "uuid",
  "game_code": "mines",
  "player_id": "uuid",
  "idempotency_key": "uuid-or-stable-key",
  "bet_amount": "5",
  "currency": "CHIP",
  "game_config": {
    "grid_size": 25,
    "mine_count": 3
  }
}
```

Response:

```json
{
  "platform_round_id": "uuid",
  "wallet_balance_after_bet": "995",
  "accepted_bet_amount": "5",
  "currency": "CHIP",
  "opened_at": "2026-09-04T12:00:00Z"
}
```

Effetti lato piattaforma: transazione `bet`, scrittura ledger (double-entry,
via funzione contabile unica), aggiornamento wallet snapshot.

### `POST /internal/v1/seamless-wallet/rounds/settle`

Chiude la round finanziaria con esito finale. Un solo endpoint per vincita e
perdita.

Request (vincita):

```json
{
  "platform_round_id": "uuid",
  "game_code": "mines",
  "player_id": "uuid",
  "idempotency_key": "uuid-or-stable-key",
  "outcome": "won",
  "payout_amount": "12.70",
  "currency": "CHIP",
  "game_result": {
    "safe_reveals_count": 4,
    "multiplier_final": "2.5400",
    "reason": "cashout"
  }
}
```

Request (perdita): `outcome: "lost"`, `payout_amount: "0"`,
`game_result.reason: "mine"`.

Response:

```json
{
  "platform_round_id": "uuid",
  "status": "settled",
  "wallet_balance_after_settlement": "1007.70",
  "ledger_transaction_id": "uuid",
  "settled_at": "2026-09-04T12:03:00Z"
}
```

Effetti: se `won` registra il credit della vincita; se `lost` chiude senza
credit. Una round gia' regolata non puo' essere regolata di nuovo con esito
incompatibile.

### `POST /internal/v1/seamless-wallet/play-sessions/close` (opzionale, v1)

Notifica la fine della presenza del player nel gioco (chiusura `play_session`).

## 6. Idempotenza

- `rounds/open`: la chiave e' generata dal dominio gioco per il tentativo di
  apertura. Stessa chiave + stesso payload = stessa risposta; stessa chiave +
  payload diverso = conflitto (`409 idempotency_conflict`).
- `rounds/settle`: la chiave e' specifica della chiusura. Retry con stessa
  chiave e stesso esito = stessa risposta, senza doppio posting.

## 7. Errori

Envelope unico:

```json
{
  "error": {
    "code": "insufficient_funds",
    "message": "Saldo insufficiente per la puntata richiesta",
    "request_id": "uuid"
  }
}
```

| HTTP | Codice | Quando |
| --- | --- | --- |
| 400 | `invalid_request` | payload malformato o configurazione gioco non supportata |
| 401 | `invalid_token` / `token_expired` | `game_launch_token` o service token non valido/scaduto |
| 402 | `insufficient_funds` | saldo insufficiente su `rounds/open` |
| 404 | `round_not_found` | `platform_round_id` sconosciuto su `settle` |
| 409 | `idempotency_conflict` | stessa chiave, payload diverso |
| 409 | `round_already_settled` | settle su round gia' chiusa con esito incompatibile |

## 8. Sequenze

### 8.1 Entrata nel gioco

1. Player autenticato sulla piattaforma.
2. La piattaforma crea la `play_session` ed emette il `game_launch_token`.
3. Il frontend gioco chiama `POST /internal/v1/game-launch/validate` sul
   backend gioco.

### 8.2 Bet / apertura round

1. Il frontend gioco invia configurazione e puntata al backend gioco.
2. Il backend gioco valida la configurazione.
3. Il backend gioco chiama `rounds/open` sulla piattaforma.
4. La piattaforma apre la round finanziaria e risponde con `platform_round_id`.
5. Il backend gioco crea la round tecnica legata a `platform_round_id`.

### 8.3 Reveal

1. Il frontend gioco chiama solo il backend gioco.
2. Il backend gioco aggiorna board e payout potenziale.
3. Nessuna scrittura finanziaria.

### 8.4 Chiusura round

- Su mina: il gioco chiude la round tecnica come persa e chiama
  `rounds/settle` con `outcome=lost`.
- Su cashout: il gioco chiude la round tecnica come vinta, calcola il payout
  finale e chiama `rounds/settle` con `outcome=won`.

## 9. Stato di attuazione (onesta' documentale)

Oggi il codice **non rispetta ancora** questo contratto: `start_session()` e
`cashout_session()` del backend Mines fanno debit/credit diretto su wallet e
ledger (Documento 31, sez. 9). L'attuazione e' l'impegno **INT-01** della
Fase 3, con l'adapter `platform_round_gateway` (lato gioco) e
`game_round_settlement_service` (lato piattaforma) come primo passo
(Documento 34, sez. 10). Questo documento descrive il **target vincolante**:
ogni nuova API o refactor deve andare in questa direzione.
