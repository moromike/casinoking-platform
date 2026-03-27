# CasinoKing - Documento 30

Separazione prodotti: piattaforma, gioco, aggregatore

Stato del documento

- Questo documento e' operativo e vincolante per la nuova fase di architettura prodotto.
- Integra `Documento 21`, `Documento 22` e `Documento 23`.
- Non sostituisce i documenti canonici di financial core, API e Mines, ma ne ridefinisce il perimetro applicativo target.

## 1. Problema da risolvere

La fase precedente ha confermato un problema strutturale:

- `sito player`
- `backoffice`
- `frontend gioco Mines`

sono stati trattati troppo a lungo come superfici dello stesso prodotto frontend.

Questo ha prodotto:

- contaminazione tra sito e gioco
- regressioni UX
- confusione tra dominio platform e dominio game
- difficolta' nel rendere Mines realmente embeddabile o riusabile

## 2. Decisione architetturale

CasinoKing va trattato come ecosistema di prodotti distinti:

1. `Platform`
2. `Game`
3. `Aggregator`

## 3. Definizione dei prodotti

### 3.1 Platform

La piattaforma e' il prodotto che gestisce:

- autenticazione
- identita' del player
- wallet
- ledger
- reporting
- backoffice
- stato amministrativo del giocatore
- sessione di accesso del giocatore alla piattaforma
- orchestrazione finanziaria della round session

La piattaforma non renderizza il gioco come responsabilita' primaria.

### 3.2 Game

Il gioco `Mines` e' un prodotto separato.

Il gioco gestisce:

- configurazioni runtime supportate
- motore RNG
- fairness
- board generation
- reveal logic
- payout model matematico
- round state interno del gioco

Il gioco non gestisce:

- wallet
- ledger
- accounting
- promo
- player account
- backoffice platform

### 3.3 Aggregator

L'aggregatore e' la shell che ospita i giochi.

Nel primo stadio puo' coincidere con il sito web player.
Nel modello target resta comunque un dominio distinto:

- catalogo giochi
- homepage/lobby
- promo/banner
- entry al gioco
- iframe/embed o launch route del gioco
- handoff token tra platform e game

## 4. Vincolo di separazione

Il gioco non deve essere una vista del sito.

Il sito non deve essere una vista del gioco.

Il backoffice non deve condividere componenti concettuali con il frame del gioco.

## 5. Stato attuale del codebase

Oggi il repository contiene:

- backend unico FastAPI
- frontend web Next.js
- una prima route `/mines` separata a livello di componente

Stato reale del coupling backend:

- `auth`, `wallet`, `ledger`, `game_sessions` e `mines` vivono nello stesso backend
- `Mines` oggi e' accoppiato direttamente alla finanza platform
- start/cashout del gioco postano direttamente su wallet/ledger

Questa fase e' ancora transitoria.

## 6. Stato target

### 6.1 Backend target

Il target e':

- `platform-backend`
- `mines-backend`

con contratto API esplicito tra i due.

### 6.2 Frontend target

Il target e':

- `web-platform`
- `mines-frontend`
- eventuale `admin-frontend` separato o area dedicata del web-platform

### 6.3 Aggregator target

Il target applicativo e':

- il player entra dal sito/aggregatore
- il sito autentica e prepara il launch
- il gioco riceve un token di launch
- il gioco comunica con il proprio backend
- la piattaforma resta il source of truth finanziario

## 7. No-go espliciti

- niente nuovo ritorno a un frontend unico concettualmente monolitico
- niente UI game appesa alla lobby platform
- niente finanza duplicata nel game backend
- niente wallet/ledger dentro il frontend gioco
- niente backoffice dentro la shell gioco

## 8. Regola operativa

Ogni nuova modifica va classificata prima in uno di questi domini:

- `platform`
- `game`
- `aggregator`

Se una modifica tocca due domini insieme, va esplicitato il contratto tra i due prima di implementarla.
