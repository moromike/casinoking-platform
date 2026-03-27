# CasinoKing - Documento 32

Piano di migrazione dalla struttura attuale alla separazione piattaforma / gioco / aggregatore

Stato del documento

- Documento operativo nuovo.
- Integra Documento 15 e Documenti 21-23.
- Traduce la nuova architettura target in step eseguibili.

## 1. Obiettivo

Portare il repository dalla situazione attuale:

- frontend monolitico quasi unico
- backend Mines ancora accoppiato alla finanza

alla situazione target:

- web platform separato
- Mines separato
- integrazione via API

## 2. Stato attuale

### 2.1 Frontend

- `web`, `account`, `login/register`, `admin` sono ancora governati da `casinoking-console.tsx`
- `Mines` e' appena stato estratto in un componente standalone dedicato

### 2.2 Backend

- auth, wallet, ledger, admin sono in dominio piattaforma
- Mines ha gia' moduli propri per:
  - runtime
  - fairness
  - randomness
  - service
- ma `service.py` di Mines tocca ancora direttamente ledger/wallet

## 3. Ordine corretto di migrazione

### Fase 1 - separazione frontend reale

Obiettivo:

- togliere definitivamente Mines dal monolite web

Task:

1. mantenere `/mines` su frontend dedicato standalone
2. rimuovere dal vecchio console monolith il ramo Mines residuo
3. separare `web platform` dal contenitore unico

Deliverable:

- `frontend/web`
- `frontend/mines`

### Fase 2 - formalizzazione API platform <-> game

Obiettivo:

- introdurre contratti chiari tra piattaforma e gioco

Task:

1. definire `game_launch_token`
2. definire `open round`
3. definire `close round won/lost`
4. definire modello di sessione gioco estesa vs round session

Deliverable:

- API doc operativa coerente con Documento 31

### Fase 3 - disaccoppiamento finanziario di Mines

Obiettivo:

- togliere a Mines la responsabilita' diretta su ledger/wallet

Task:

1. spostare il debito iniziale round in dominio piattaforma
2. spostare il payout finale in dominio piattaforma
3. lasciare in Mines solo:
   - config
   - board
   - fairness
   - reveal
   - payout result

Deliverable:

- backend Mines come motore gioco puro

### Fase 4 - aggregatore esplicito

Obiettivo:

- rendere il sito un launcher/aggregatore e non un contenitore di gioco

Task:

1. catalogo giochi
2. shell lancio
3. apertura standalone o embed
4. passaggio token e contesto

Deliverable:

- web player con ruolo chiaro di aggregatore

## 4. Cosa NON fare

- non separare subito in piu' repo se prima non sono chiari i contratti
- non riscrivere backend finanziario senza prima fissare il seamless wallet
- non rifare la grafica del gioco prima di aver chiuso i confini di prodotto
- non mantenere due fonti di verita' per round e payout

## 5. Prossimi step raccomandati

1. pulire `casinoking-console.tsx` togliendo completamente Mines residuo
2. progettare il `game_launch_token`
3. disegnare gli endpoint platform <-> Mines
4. introdurre un adapter temporaneo che mantenga compatibilita' col backend attuale
5. solo dopo procedere col refactor finanziario interno

## 6. Decisione finale

La migrazione non va trattata come redesign cosmetico.

Va trattata come separazione di prodotti e responsabilita':

- prodotto piattaforma
- prodotto gioco
- prodotto aggregatore

Ogni task futuro va classificato in una di queste tre aree prima di essere implementato.
