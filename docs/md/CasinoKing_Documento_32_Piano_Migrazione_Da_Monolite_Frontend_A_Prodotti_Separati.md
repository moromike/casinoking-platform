# CasinoKing - Documento 32

Piano di migrazione da struttura mista a prodotti separati

Stato del documento

- Questo documento e' operativo.
- Definisce il piano di migrazione architetturale e di repository.
- Va letto insieme ai Documenti 30 e 31.

## 1. Obiettivo

Migrare da:

- backend unico con coupling game/platform
- frontend web che ha ospitato parti gioco

verso:

- prodotti separati
- contratti chiari
- domini piu' stabili

## 2. Principio di esecuzione

La migrazione non va fatta con big bang.

Va fatta per strati:

1. separazione frontend
2. contratti API
3. separazione backend
4. eventuale separazione repo/applicazioni

## 3. Fase 1 - separazione frontend immediata

Obiettivo:
fare in modo che il gioco non sia piu' una vista del sito.

Task:

- mantenere `/mines` su componente standalone
- ridurre l'uso di `casinoking-console.tsx` al solo web platform/backoffice
- evitare nuovi riferimenti di UI platform dentro il gioco

Done quando:

- `Mines` non e' piu' concettualmente legato alla lobby
- le regressioni di contaminazione UI smettono di avvenire

## 4. Fase 2 - separazione frontend a livello app

Obiettivo:
creare app distinte nel monorepo.

Target consigliato:

- `frontend/web`
- `frontend/mines`
- `backend/platform`

Opzionale:

- `frontend/admin`

Durante questa fase:

- il sito player vive in `frontend/web`
- Mines vive in `frontend/mines`
- il codice shared va in un package o in una cartella shared esplicita

## 5. Fase 3 - contratto platform/game

Obiettivo:
introdurre un boundary API vero tra platform e game.

Task:

- definire token di handoff
- definire launch contract
- definire settlement contract
- distinguere `play session` e `round session`

Done quando:

- il gioco puo' essere lanciato dalla platform senza dipendere dai componenti platform
- la finanza non e' piu' dentro la logica gioco

## 6. Fase 4 - estrazione Mines backend

Obiettivo:
spostare la logica di gioco in backend dedicato.

Resta in `platform-backend`:

- auth
- player/account
- wallet
- ledger
- reporting
- admin
- settlement

Passa a `mines-backend`:

- runtime config
- fairness
- rng
- reveal logic
- payout model
- round state interno

## 7. Fase 5 - aggregatore esplicito

Obiettivo:
rendere il sito host dei giochi un prodotto definito.

In questa fase l'aggregatore gestisce:

- lobby
- catalogo
- launch flow
- embed/iframe o route launch
- orchestrazione esterna della game session

## 8. Analisi del lavoro gia' fatto

### 8.1 Positivo

- backend finanziario e lifecycle sono gia' robusti
- Mines e' gia' server-authoritative
- runtime/fairness esistono gia'
- `/mines` e' gia' stato staccato dal contenitore generale a livello di route/component

### 8.2 Da cambiare

- coupling finanziario dentro `backend/app/modules/games/mines/service.py`
- bootstrap demo dentro backend unico
- eccessiva centralizzazione frontend in `casinoking-console.tsx`
- assenza di token di handoff platform -> game
- assenza di boundary API interno platform/game

## 9. Regola di priorita'

1. Prima separare i domini.
2. Poi rifinire la grafica.
3. Poi estrarre i backend.

Se si inverte quest'ordine, si rientra nel loop gia' emerso.
