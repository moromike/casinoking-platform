# CasinoKing - Documento 31

Contratto target di integrazione tra piattaforma e gioco Mines in modello seamless wallet

Stato del documento

- Documento operativo nuovo.
- Integra Documento 05, Documento 06, Documento 11, Documento 21 e Documento 23.
- Serve a chiarire cosa appartiene al backend piattaforma e cosa appartiene al backend gioco.

## 1. Obiettivo

Definire il modello corretto di integrazione tra piattaforma e gioco Mines quando il gioco e' prodotto separato ma integrato con wallet seamless della piattaforma.

## 2. Modello scelto

Il modello target e' `seamless wallet`.

Questo significa:

- il wallet appartiene alla piattaforma
- il ledger appartiene alla piattaforma
- il gioco non gestisce conti, saldi o posting
- il gioco interroga il proprio backend per RNG e reveal
- la piattaforma contabilizza l'apertura e la chiusura della round

## 3. Cosa appartiene al backend gioco

Il backend Mines possiede:

- configurazioni supportate
- numero mine supportato per layout
- numero celle supportato per layout
- payout runtime
- fairness model
- seed hash / nonce / board hash
- generazione board
- reveal di ogni click
- stato tecnico interno della partita
- determinazione del payout finale teorico della round

## 4. Cosa appartiene al backend piattaforma

Il backend piattaforma possiede:

- autenticazione player/admin
- sessione utente
- wallet
- ledger
- idempotenza finanziaria
- reporting
- sessione economica della round
- sessione complessiva di presenza del player nel gioco
- autorizzazione al lancio del gioco
- accredito/addebito finale

## 5. Ciclo target della round

### 5.1 Entrata nel gioco

1. Il player entra dal sito/aggregatore.
2. La piattaforma autentica il player.
3. La piattaforma emette un `game launch token`.
4. Il frontend gioco usa quel token per aprire una sessione tecnica col backend Mines.

### 5.2 Bet / inizio round

1. Il player sceglie configurazione e puntata nel frontend gioco.
2. Il frontend gioco invia richiesta al backend Mines.
3. Il backend Mines valida la configurazione di gioco.
4. Il backend Mines chiede alla piattaforma di aprire la round finanziaria.
5. La piattaforma:
   - verifica il saldo
   - registra la puntata
   - crea il round record piattaforma
   - restituisce un `platform_round_id`
6. Il backend Mines crea la propria sessione tecnica e la lega al `platform_round_id`.

### 5.3 Reveal

Per ogni click:

1. il frontend gioco chiama il backend Mines
2. il backend Mines usa il proprio RNG/fairness
3. il backend Mines restituisce:
   - risultato reveal
   - stato round
   - payout potenziale aggiornato

Durante il reveal non deve essere effettuata alcuna scrittura finanziaria.

## 5.4 Fine round

Quando la round termina:

- se il player perde:
  - il backend Mines notifica la chiusura con payout `0`
  - la piattaforma chiude la round finanziaria come persa

- se il player incassa:
  - il backend Mines invia alla piattaforma il payout finale
  - la piattaforma registra il payout
  - aggiorna wallet/ledger
  - chiude la round finanziaria come vinta

## 6. Token di integrazione

Serve introdurre un token dedicato di integrazione gioco.

## 6.1 Nome logico

`game_launch_token`

## 6.2 Contenuto minimo

- player_id
- platform_session_id
- game_code
- issued_at
- expires_at
- nonce
- opzionale: device/session fingerprint

## 6.3 Scopo

Permettere al backend gioco di sapere:

- chi e' il player
- quale piattaforma ha autorizzato il lancio
- per quale gioco
- entro quale finestra temporale

## 7. API target tra piattaforma e gioco

### 7.1 Piattaforma -> gioco

- `launch game session`
- `validate launch token`
- opzionale `heartbeat / close launch session`

### 7.2 Gioco -> piattaforma

- `open round / place bet`
- `close round lost`
- `close round won`
- opzionale `player left game`

## 8. Regola sulle sessioni

Esistono due concetti distinti:

### 8.1 Sessione di gioco estesa

Da quando il player entra nel gioco a quando esce.

Serve per:

- audit
- presenza nel gioco
- aggancio al launch token
- analytics

### 8.2 Sessione di round / partita

Da quando la puntata viene accettata a quando la round finisce.

Serve per:

- contabilita'
- esito della partita
- payout
- riconciliazione

## 9. Stato attuale del codebase

Oggi questo modello non e' ancora rispettato completamente.

In particolare:

- `start_session` di Mines effettua oggi direttamente il debito wallet/ledger
- `cashout_session` di Mines effettua oggi direttamente il credito wallet/ledger
- `reveal_cell` aggiorna lo stato gioco lato backend Mines, che e' corretto

Quindi la parte da rompere e' questa:

- il backend Mines oggi fa sia `motore di gioco` sia `motore finanziario della round`

## 10. Decisione

Da questo momento la direzione ufficiale e':

- backend Mines = motore gioco
- backend piattaforma = motore finanziario / seamless wallet

Ogni nuova API o refactor deve andare in questa direzione.
