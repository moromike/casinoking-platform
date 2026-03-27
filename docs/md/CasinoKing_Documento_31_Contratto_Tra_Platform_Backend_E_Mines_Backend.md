# CasinoKing - Documento 31

Contratto target tra platform backend e Mines backend

Stato del documento

- Questo documento e' operativo.
- Definisce il target di separazione backend.
- Integra i documenti canonici API e financial core con la nuova separazione di dominio.

## 1. Premessa

Il lavoro svolto finora mostra che il backend attuale contiene due responsabilita' fuse:

1. logica di gioco Mines
2. logica finanziaria platform

Questo documento definisce come vanno separate.

## 2. Responsabilita' del Platform Backend

Il `platform-backend` resta responsabile di:

- auth player/admin
- emissione token di accesso platform
- wallet
- ledger
- posting double-entry
- bonus / adjustment
- reporting
- owner-only access
- round financial settlement
- player gaming session a livello piattaforma

## 3. Responsabilita' del Mines Backend

Il `mines-backend` resta responsabile di:

- runtime config del gioco
- configurazioni supportate griglia/mine
- fairness seed rotation del gioco
- engine RNG
- generazione board
- valutazione reveal
- calcolo moltiplicatori e payout teorico
- stato round di gioco
- event stream del round

Il `mines-backend` non deve possedere wallet o ledger.

## 4. Round model target

La round di Mines va letta cosi':

1. platform autorizza la puntata
2. platform crea o prenota il contesto finanziario della round
3. mines-backend crea la round di gioco con config e bet_amount ricevuti
4. ogni click sulla board interroga il mines-backend
5. mines-backend aggiorna solo lo stato della round di gioco
6. a fine round il mines-backend restituisce il risultato finale
7. il platform-backend regola contabilmente il settlement finale

## 5. Modalita' di integrazione

L'integrazione deve essere di tipo `seamless wallet`.

Questo significa:

- il gioco non scala saldo da solo
- il gioco non accredita vincite da solo
- il platform backend e' l'unico sistema che modifica wallet e ledger

## 6. Token di handoff

Serve un token di launch / handoff tra platform e game.

Il token deve rappresentare almeno:

- `player_id`
- `platform_session_id`
- `game_code`
- `launch_time`
- `expiration`
- eventuali claims minime di autorizzazione

Il token non sostituisce il bearer platform per il backoffice o per le API generali.

## 7. Sessioni target

Occorre distinguere due livelli:

### 7.1 Platform play session

Sessione che va da:

- ingresso del giocatore nel gioco
- fino all'uscita del giocatore dal gioco

Serve per:

- tracking
- auditing
- analytics
- lifecycle esterno del gioco

### 7.2 Game round session

Sessione che va da:

- bet/start round
- fino a win/loss/cashout

Serve per:

- stato round
- replay
- fairness proof
- settlement finale

## 8. Contratti minimi target

### 8.1 Platform -> Mines

Endpoint/contract target di launch:

- apertura round
- passaggio config
- passaggio bet amount
- passaggio token handoff

### 8.2 Mines -> Platform

Contract target di settlement:

- `round_id`
- `result`
- `bet_amount`
- `final_payout_amount`
- `fairness_version`
- `nonce`
- `server_seed_hash`
- `board_hash`

Il settlement deve essere idempotente.

## 9. Stato attuale del codebase

Oggi questo contratto non esiste ancora.

Stato attuale:

- `start_session()` scala il wallet e posta ledger nel modulo Mines
- `cashout_session()` posta la vincita nel modulo Mines
- `auth/demo` crea player demo e credito bootstrap nel backend platform unico

Questa e' precisamente l'area da migrare.

## 10. Regola operativa

Ogni nuovo sviluppo su Mines backend deve evitare di aumentare il coupling finanziario esistente.

Se serve nuova logica finanziaria, va disegnata come responsabilita' del `platform-backend`, non del `mines-backend`.
