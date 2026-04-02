# CasinoKing - Documento 35

Contratto API operativo v1 tra platform-backend e Mines-backend

Stato del documento

- Documento operativo nuovo.
- Integra i Documenti 11, 30, 31, 32 e 34.
- Non sostituisce il contratto API canonico della piattaforma; definisce il contratto di integrazione interno target tra i due backend.

## 1. Obiettivo

Definire il primo contratto API operativo e implementabile per la migrazione da:

- backend Mines che oggi fa anche settlement

a:

- backend Mines come motore gioco puro
- backend piattaforma come seamless wallet e settlement authority

## 2. Principi

1. il gioco non tocca wallet o ledger
2. la piattaforma non decide board, reveal o payout runtime
3. ogni round ha:
   - un identificativo platform
   - un identificativo game
4. i reveal non generano posting finanziari intermedi

## 3. Entita' minime

### 3.1 `game_launch_token`

Emesso dalla piattaforma e consumato dal backend gioco.

Campi minimi:

- `token`
- `player_id`
- `platform_session_id`
- `game_code`
- `issued_at`
- `expires_at`
- `nonce`

### 3.2 `platform_round_id`

Identificativo round finanziaria lato piattaforma.

### 3.3 `game_session_id`

Identificativo round tecnica lato Mines.

## 4. Flusso target

### 4.1 Launch

1. web/aggregatore autentica il player sulla piattaforma
2. platform-backend emette `game_launch_token`
3. frontend gioco apre il backend Mines con quel token
4. Mines-backend valida il token e apre una `play session` tecnica

### 4.2 Bet / open round

1. frontend gioco invia config round e amount a Mines-backend
2. Mines-backend valida config e supporto runtime
3. Mines-backend chiama platform-backend per aprire la round finanziaria
4. platform-backend risponde con `platform_round_id`
5. Mines-backend crea `game_session_id` legato a `platform_round_id`

### 4.3 Reveal

1. frontend gioco chiama Mines-backend
2. Mines-backend esegue RNG/reveal
3. Mines-backend restituisce stato tecnico aggiornato
4. nessuna scrittura finanziaria piattaforma in questa fase

### 4.4 Close round lost

1. la round termina su mina
2. Mines-backend chiama platform-backend con esito perso
3. platform-backend chiude la round finanziaria senza payout

### 4.5 Close round won

1. il player incassa
2. Mines-backend calcola payout finale
3. Mines-backend chiama platform-backend con esito vinto e payout
4. platform-backend registra payout e chiude la round

## 5. API target

## 5.1 Platform -> Game

### `POST /internal/games/mines/launch`

Scopo:

- validare il `game_launch_token`
- aprire una play session tecnica lato gioco

Request minima:

```json
{
  "game_launch_token": "..."
}
```

Response minima:

```json
{
  "play_session_id": "uuid",
  "player_id": "uuid",
  "game_code": "mines",
  "token_valid": true,
  "expires_at": "2026-03-27T15:00:00Z"
}
```

## 5.2 Game -> Platform

### `POST /internal/platform/rounds/open`

Scopo:

- aprire la round finanziaria e debitare la puntata

Request minima:

```json
{
  "player_id": "uuid",
  "platform_session_id": "uuid",
  "game_code": "mines",
  "game_launch_token_nonce": "string",
  "bet_amount": "5.000000",
  "currency_code": "CHIP",
  "game_config": {
    "grid_size": 25,
    "mine_count": 3
  },
  "idempotency_key": "..."
}
```

Response minima:

```json
{
  "platform_round_id": "uuid",
  "status": "opened",
  "wallet_balance_after": "995.000000"
}
```

### `POST /internal/platform/rounds/{platform_round_id}/settle-lost`

Scopo:

- chiudere la round come persa

Request minima:

```json
{
  "game_session_id": "uuid",
  "final_state": {
    "safe_reveals_count": 2,
    "mine_trigger_cell": 7
  },
  "idempotency_key": "..."
}
```

Response minima:

```json
{
  "platform_round_id": "uuid",
  "status": "lost",
  "payout_amount": "0.000000"
}
```

### `POST /internal/platform/rounds/{platform_round_id}/settle-won`

Scopo:

- chiudere la round come vinta e registrare il payout

Request minima:

```json
{
  "game_session_id": "uuid",
  "payout_amount": "12.340000",
  "final_multiplier": "2.4680",
  "final_state": {
    "safe_reveals_count": 3
  },
  "idempotency_key": "..."
}
```

Response minima:

```json
{
  "platform_round_id": "uuid",
  "status": "won",
  "wallet_balance_after": "1007.340000",
  "ledger_transaction_id": "uuid"
}
```

## 5.3 Game-native public API che resta nel backend Mines

Questi endpoint restano nel dominio gioco:

- `GET /games/mines/config`
- `GET /games/mines/fairness/current`
- `POST /games/mines/reveal`
- `GET /games/mines/session/{session_id}`
- `GET /games/mines/session/{session_id}/fairness`

Questi endpoint vanno pero' riallineati a payload di dominio gioco puro.

## 6. Mapping dal modello attuale al target

### Oggi

- `POST /games/mines/start`:
  - valida config
  - debita il wallet
  - crea ledger tx
  - crea game session

### Target

Split in due passaggi:

1. `POST /internal/platform/rounds/open`
2. `POST /games/mines/start` oppure `POST /internal/games/mines/rounds`

Nota:

- nel periodo transitorio si puo' lasciare `POST /games/mines/start`, ma facendolo passare attraverso il gateway platform

### Oggi

- `POST /games/mines/cashout`:
  - calcola stato
  - accredita wallet
  - scrive ledger
  - chiude sessione

### Target

Split in:

1. chiusura tecnica round lato Mines
2. `settle-won` lato platform

### Oggi

- chiusura su mina accade in `reveal_cell()` senza notifica platform

### Target

- `reveal_cell()` produce esito tecnico
- adapter/gateway notifica `settle-lost`

## 7. Adapter temporaneo consigliato

Durante la migrazione va introdotto un adapter interno:

- `app/modules/integration/platform_round_gateway.py`

Interfaccia minima:

- `open_round(...)`
- `settle_round_lost(...)`
- `settle_round_won(...)`

Prima versione:

- chiama funzioni Python interne del dominio piattaforma

Versione target:

- client HTTP autenticato verso platform-backend esterno

## 8. Decisione operativa

Prima di toccare ancora la grafica o la UX di Mines, i prossimi passi backend devono essere:

1. introdurre il gateway di boundary
2. far passare `start_session()` dal gateway
3. far passare la chiusura lost/won dal gateway
4. ridurre i campi finanziari esposti da session payload lato Mines
