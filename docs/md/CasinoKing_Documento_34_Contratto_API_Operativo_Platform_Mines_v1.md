# CasinoKing - Documento 34

Contratto API operativo v1 tra platform-backend e mines-backend

Stato del documento

- Documento operativo nuovo.
- Traduce Documento 31 in un primo contratto tecnico implementabile.
- Non sostituisce Documento 05, Documento 11 o i documenti canonici Mines.
- Serve come base di lavoro per la prima migrazione reale del backend.

## 1. Obiettivo

Definire un contratto tecnico concreto tra:

- `platform-backend`
- `mines-backend`

in modo da separare:

- lifecycle finanziario della round
- lifecycle tecnico del gioco

senza rompere wallet, ledger, fairness o idempotenza.

## 2. Principio guida

Il backend piattaforma decide se la round puo' partire e contabilizza l'esito finale.

Il backend Mines decide:

- configurazione valida
- board
- reveal
- stato tecnico della round
- payout finale teorico

## 3. Domini e ownership

### 3.1 Platform-backend

Possiede:

- player identity
- admin identity
- platform session
- seamless wallet
- ledger
- accounting della round
- reporting
- play session lato piattaforma
- issue e verifica del `game_launch_token`

### 3.2 Mines-backend

Possiede:

- game runtime config
- RNG
- fairness
- seed lifecycle
- board generation
- reveal per click
- technical round session
- payout result finale

## 4. Oggetti concettuali da distinguere

### 4.1 `play_session`

Sessione estesa dal momento in cui il player entra nel gioco al momento in cui esce.

Ownership:

- piattaforma

### 4.2 `platform_round`

Round finanziaria. Parte quando la piattaforma accetta la bet e termina quando la piattaforma registra esito finale.

Ownership:

- piattaforma

### 4.3 `game_round`

Round tecnica del gioco. Parte quando Mines crea board/fairness e termina quando il gioco ha esito finale.

Ownership:

- Mines

## 5. Token di handoff

## 5.1 Nome

`game_launch_token`

## 5.2 Scopo

Permettere a `mines-backend` di sapere che:

- il player e' stato autenticato dalla piattaforma
- il lancio del gioco e' autorizzato
- il token vale solo per `game_code = mines`
- esiste una `play_session` piattaforma valida

## 5.3 Claim minimi richiesti

- `iss`
- `aud`
- `sub` = `player_id`
- `platform_session_id`
- `play_session_id`
- `game_code`
- `issued_at`
- `expires_at`
- `nonce`

## 5.4 Regole

- TTL breve
- monouso o comunque legato a una sola apertura valida del gioco
- non sostituisce il bearer piattaforma generale
- non deve essere riusato per backoffice o altre API player non gioco

## 6. API target v1

Le API qui sotto sono il primo set minimo raccomandato.

## 6.1 Platform -> Game

### `POST /internal/v1/game-launch/validate`

Scopo:

- validare il `game_launch_token`
- aprire o confermare una `game play session`

Request minima:

```json
{
  "game_launch_token": "jwt-or-equivalent"
}
```

Response minima:

```json
{
  "game_code": "mines",
  "player_id": "uuid",
  "platform_session_id": "uuid",
  "play_session_id": "uuid",
  "game_play_session_id": "uuid",
  "expires_at": "2026-03-27T12:00:00Z"
}
```

Note:

- questa API vive nel backend Mines
- il token viene verificato con chiave/issuer piattaforma

## 6.2 Game -> Platform

### `POST /internal/v1/seamless-wallet/rounds/open`

Scopo:

- aprire la round finanziaria
- verificare il saldo
- registrare il bet debit lato piattaforma

Request minima:

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

Response minima:

```json
{
  "platform_round_id": "uuid",
  "wallet_balance_after_bet": "995",
  "accepted_bet_amount": "5",
  "currency": "CHIP",
  "opened_at": "2026-03-27T12:00:00Z"
}
```

Ownership:

- piattaforma

Effetti:

- crea transazione `bet`
- scrive ledger
- aggiorna wallet snapshot

### `POST /internal/v1/seamless-wallet/rounds/settle`

Scopo:

- chiudere la round finanziaria con esito finale

Request minima:

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

Response minima:

```json
{
  "platform_round_id": "uuid",
  "status": "settled",
  "wallet_balance_after_settlement": "1007.70",
  "ledger_transaction_id": "uuid",
  "settled_at": "2026-03-27T12:03:00Z"
}
```

Per round persa:

```json
{
  "platform_round_id": "uuid",
  "game_code": "mines",
  "player_id": "uuid",
  "idempotency_key": "uuid-or-stable-key",
  "outcome": "lost",
  "payout_amount": "0",
  "currency": "CHIP",
  "game_result": {
    "safe_reveals_count": 1,
    "multiplier_final": "0",
    "reason": "mine"
  }
}
```

Ownership:

- piattaforma

Effetti:

- se `won`: registra win credit e chiude la round
- se `lost`: chiude la round senza credit

### `POST /internal/v1/seamless-wallet/play-sessions/close`

Scopo:

- notificare alla piattaforma la chiusura della presenza del player nel gioco

Questa API e' opzionale nella prima iterazione.

## 7. Sequenza operativa v1

## 7.1 Entrata nel gioco

1. player autenticato sulla piattaforma
2. piattaforma crea `play_session`
3. piattaforma emette `game_launch_token`
4. frontend gioco chiama `mines-backend /game-launch/validate`

## 7.2 Bet

1. frontend gioco invia a Mines:
   - `grid_size`
   - `mine_count`
   - `bet_amount`
2. Mines valida configurazione
3. Mines chiama `platform /rounds/open`
4. piattaforma apre la round finanziaria
5. Mines crea la round tecnica e la lega a `platform_round_id`

## 7.3 Reveal

1. frontend gioco chiama solo Mines
2. Mines aggiorna board e payout potenziale
3. nessuna scrittura finanziaria durante i reveal

## 7.4 Chiusura round

### Caso `mine`

1. Mines chiude la round tecnica come persa
2. Mines chiama `platform /rounds/settle` con `outcome=lost`
3. piattaforma chiude la round finanziaria

### Caso `cashout`

1. Mines chiude la round tecnica come vinta
2. Mines calcola payout finale
3. Mines chiama `platform /rounds/settle` con `outcome=won`
4. piattaforma registra il credit

## 8. Idempotenza

## 8.1 `rounds/open`

L'idempotency key deve essere generata dal dominio gioco per il tentativo di apertura round.

Regola:

- stessa key + stesso payload = stessa risposta
- stessa key + payload diverso = conflitto

## 8.2 `rounds/settle`

L'idempotency key deve essere specifica della chiusura round.

Regola:

- un round non puo' essere regolato due volte con outcome incompatibili

## 9. Mappatura dal codice attuale

Oggi il coupling si trova in:

- [backend/app/modules/games/mines/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/service.py)

### 9.1 Funzioni che vanno spezzate

- `start_session()`
- `cashout_session()`

### 9.2 Cosa resta in Mines

- validazione configurazione
- fairness artifact generation
- board creation
- `reveal_cell()`
- calcolo multiplier / payout finale
- technical session state

### 9.3 Cosa va spostato in platform

- lookup wallet
- balance check
- bet debit
- ledger transaction creation
- ledger entry creation
- wallet snapshot update
- financial close round

## 10. Decisione operativa

La prima implementazione di migrazione non deve separare tutto in una volta.

Va introdotto prima un adapter esplicito:

- lato Mines: `platform_round_gateway`
- lato Platform: `game_round_settlement_service`

Solo dopo questo adapter si potra' togliere la scrittura diretta su ledger/wallet dal service Mines.
