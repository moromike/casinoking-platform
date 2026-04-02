# CasinoKing - Documento 34

Mappatura del codebase attuale rispetto alla target architecture Platform / Game / Aggregator

Stato del documento

- Documento operativo nuovo.
- Integra i Documenti 30, 31, 32 e 33.
- Serve a tradurre la separazione teorica in una lista concreta di file, endpoint e boundary da migrare.

## 1. Obiettivo

Fissare in modo verificabile:

1. quali file appartengono gia' in modo pulito al dominio corretto
2. quali file oggi mescolano ancora `platform` e `game`
3. quali endpoint e funzioni vanno toccati per primi
4. quali adapter temporanei conviene introdurre per migrare senza rompere il prodotto

## 2. Classificazione attuale dei domini

### 2.1 Dominio gia' chiaramente piattaforma

File chiave:

- `backend/app/api/routes/auth.py`
- `backend/app/api/routes/wallets.py`
- `backend/app/api/routes/ledger.py`
- `backend/app/api/routes/admin.py`
- `backend/app/modules/auth/service.py`
- `backend/app/modules/wallet/service.py`
- `backend/app/modules/ledger/service.py`
- `backend/app/modules/admin/service.py`

Responsabilita' attuali corrette:

- autenticazione player/admin
- bootstrap identita' e wallet iniziali
- wallet snapshot
- ledger reporting
- backoffice
- controlli amministrativi

### 2.2 Dominio gia' chiaramente gioco Mines

File chiave:

- `backend/app/modules/games/mines/runtime.py`
- `backend/app/modules/games/mines/randomness.py`
- `backend/app/modules/games/mines/fairness.py`

Responsabilita' attuali corrette:

- configurazioni supportate
- payout runtime
- RNG
- seed lifecycle
- fairness verify/rotate/current

### 2.3 Dominio ancora misto

File chiave:

- `backend/app/api/routes/mines.py`
- `backend/app/modules/games/mines/service.py`

Problema:

- la superficie API e il service Mines espongono e implementano insieme:
  - lifecycle tecnico della partita
  - lifecycle finanziario della round

Questo e' il coupling principale ancora aperto.

## 3. Endpoint attuali che mescolano gioco e finanza

### 3.1 `POST /api/v1/games/mines/start`

File:

- `backend/app/api/routes/mines.py`
- `backend/app/modules/games/mines/service.py`

Problema attuale:

- l'endpoint appare come endpoint di gioco
- ma `start_session()`:
  - legge `wallet_accounts`
  - controlla il saldo
  - crea `ledger_transactions`
  - crea `ledger_entries`
  - aggiorna `wallet_accounts.balance_snapshot`
  - crea `game_sessions`

Target:

- il backend gioco non deve piu' debitare il saldo
- il round debit deve appartenere alla piattaforma
- Mines deve ricevere o ottenere un `platform_round_id` gia' aperto

### 3.2 `POST /api/v1/games/mines/cashout`

File:

- `backend/app/api/routes/mines.py`
- `backend/app/modules/games/mines/service.py`

Problema attuale:

- l'endpoint appare come chiusura tecnica di gioco
- ma `cashout_session()`:
  - legge wallet
  - crea transazione ledger di vincita
  - crea ledger entries
  - aggiorna il wallet snapshot
  - chiude la sessione

Target:

- Mines deve produrre il payout finale
- la piattaforma deve contabilizzare e chiudere la round finanziaria

### 3.3 `POST /api/v1/games/mines/reveal`

File:

- `backend/app/api/routes/mines.py`
- `backend/app/modules/games/mines/service.py`

Stato:

- questo endpoint e' quasi gia' nel dominio corretto

Perche':

- `reveal_cell()` aggiorna stato tecnico, reveal, multiplier e potential payout
- non fa posting ledger

Resta da verificare:

- il modello dati di `game_sessions` va mantenuto nel backend gioco o sdoppiato in record platform + record game

### 3.4 `GET /api/v1/games/mines/session/{session_id}`

File:

- `backend/app/api/routes/mines.py`
- `backend/app/modules/games/mines/service.py`

Problema:

- oggi il concetto di `game_session` porta dentro anche riferimenti finanziari come:
  - `start_ledger_transaction_id`
  - `wallet_balance_after_start`
  - `wallet_type`

Target:

- lato gioco il dettaglio sessione deve essere tecnico
- lato piattaforma i dettagli finanziari devono stare nel dominio round/wallet/ledger

### 3.5 `GET /api/v1/games/mines/sessions`

File:

- `backend/app/api/routes/mines.py`
- `backend/app/modules/games/mines/service.py`

Problema:

- la lista sessioni espone ancora un oggetto ibrido tra history gioco e history conto

Target:

- history gioco separata dalla history economica
- eventuale aggregazione lato web platform o account

## 4. Funzioni backend da rifattorizzare per prime

### 4.1 `start_session()`

File:

- `backend/app/modules/games/mines/service.py`

Da spezzare in:

1. validazione config + creazione contesto gioco
2. chiamata o adapter verso `platform round open`
3. persistenza sessione tecnica Mines con riferimento al `platform_round_id`

### 4.2 `cashout_session()`

File:

- `backend/app/modules/games/mines/service.py`

Da spezzare in:

1. verifica che il cashout sia ammesso
2. determinazione del payout finale
3. chiamata o adapter verso `platform round settle won`
4. chiusura tecnica sessione Mines

### 4.3 chiusura su mina dentro `reveal_cell()`

File:

- `backend/app/modules/games/mines/service.py`

Oggi:

- chiude lo stato sessione Mines come `lost`

Target:

- oltre alla chiusura tecnica, dovra' esistere una notifica o adapter verso `platform round settle lost`
- questa parte non deve creare posting finanziari dentro Mines

## 5. Boundary naturali da introdurre

### 5.1 Adapter `platform_round_gateway`

Scopo:

- isolare subito Mines dal dettaglio di wallet/ledger senza separare ancora in due repo o due servizi fisici

Metodi iniziali:

- `open_round(...)`
- `settle_round_won(...)`
- `settle_round_lost(...)`

Nel breve periodo:

- adapter interno nello stesso codebase

Nel target:

- client HTTP o RPC verso platform-backend

### 5.2 Adapter `game_launch_gateway`

Scopo:

- validare il contesto di ingresso nel gioco

Metodi iniziali:

- `issue_game_launch_token(...)` lato platform
- `validate_game_launch_token(...)` lato game

### 5.3 Distinzione esplicita tra due record

Record target:

1. `platform_play_session` / `platform_round`
2. `mines_game_session`

Motivo:

- oggi `game_sessions` porta insieme dati tecnici e dati finanziari
- la migrazione deve ridurre questo accoppiamento

## 6. Primo ordine corretto di intervento sul codice

1. introdurre il boundary `platform_round_gateway`
2. far passare `start_session()` attraverso il gateway
3. far passare la chiusura win/loss attraverso il gateway
4. togliere gradualmente dal payload Mines i campi finanziari non di dominio gioco
5. solo dopo separare il servizio fisicamente

## 7. Decisione operativa

Ogni nuova modifica backend deve essere classificata come:

- `platform`
- `game`
- `integration boundary`

Se una modifica tocca `backend/app/modules/games/mines/service.py` e introduce direttamente nuovo codice wallet/ledger, va considerata regressione architetturale rispetto alla direzione ufficiale.
