# Mines External Game + Table Session Plan

Documento operativo per valutazione CTO.

## Stato del documento

- Tipo: piano architetturale e funzionale.
- Scopo: descrivere esigenza, problema, target finale e percorso di implementazione.
- Stato: proposta da discutere prima dell'implementazione.
- Ambito: Mines, piattaforma, wallet/ledger, game launch, access session, sicurezza, futura integrazione esterna.
- Non implementa codice.
- Non sostituisce i documenti canonici in `docs/word/` e `docs/runtime/`.

## Executive summary

Oggi Mines e la piattaforma CasinoKing sono gia' separati in modo concettuale, ma vivono ancora nello stesso backend applicativo.

Mines ha un proprio frontend, API dedicate, engine server-authoritative, RNG/fairness e payout runtime. La piattaforma possiede invece player, wallet, ledger, round economiche, access session e settlement.

Il passo proposto e' far evolvere Mines verso un modello "external game ready": anche se nel breve resta nello stesso repository e nello stesso ambiente locale, il gioco deve comportarsi come se parlasse con una piattaforma esterna tramite un contratto esplicito.

In parallelo viene introdotto un nuovo concetto funzionale: il player non deve giocare direttamente con tutto il saldo disponibile. All'ingresso del gioco deve scegliere quanto "portare al tavolo", con limite massimo di perdita per sessione pari a 100 CHIP o al saldo disponibile se inferiore.

La proposta chiave e':

- il saldo reale resta sempre sulla piattaforma
- Mines non possiede mai fondi
- la table session definisce un budget/perdita massima per sessione
- ogni puntata resta validata dalla piattaforma
- ogni movimento economico resta scritto nel ledger double-entry
- Mines diventa gradualmente separabile tramite gateway/contratto, prima internamente e poi via HTTP/API

## Preambolo: problema da risolvere

Il progetto nasce con due anime:

1. piattaforma casino
2. giochi proprietari, con Mines come primo modulo

Nel codice attuale Mines e piattaforma sono gia' distinguibili, ma non sono ancora completamente indipendenti:

- Mines chiama moduli platform interni tramite `round_gateway.py`
- il game launch token esiste, ma oggi e' opzionale su diversi endpoint Mines
- wallet e ledger sono correttamente platform-owned, ma il confine non e' ancora un contratto esterno pienamente formalizzato
- la sessione di accesso al gioco esiste, ma non contiene ancora un budget massimo portato al tavolo
- il frontend Mines mostra il saldo e permette puntate, ma non obbliga il player a scegliere un limite di sessione prima di entrare nel gioco

Questo crea tre problemi prospettici.

### Problema 1: riuso esterno del gioco

Se domani Mines deve essere integrato in un'altra piattaforma, non basta copiare la UI o il modulo game. Serve un contratto chiaro:

- come il player viene autorizzato
- chi possiede il saldo
- come si apre una sessione
- come si apre una round
- come si registra una puntata
- come si registra una vincita
- come si chiude una sessione
- come si gestiscono crash, timeout e retry
- quali token e garanzie di sicurezza sono richieste

Senza questo contratto, il gioco resta legato implicitamente alla piattaforma corrente.

### Problema 2: rischio di esposizione dell'intero saldo

Anche se tecnicamente il player non "porta" davvero tutto il credito nel gioco, l'esperienza attuale puo' far percepire il saldo completo come immediatamente disponibile nel contesto Mines.

Il requisito nuovo e':

> Il player deve poter perdere in una sessione Mines al massimo 100 CHIP, oppure al massimo il proprio saldo disponibile se inferiore a 100.

Esempi:

| Saldo disponibile | Default ingresso Mines | Massimo selezionabile |
| --- | ---: | ---: |
| 350 CHIP | 100 CHIP | 100 CHIP |
| 100 CHIP | 100 CHIP | 100 CHIP |
| 63 CHIP | 63 CHIP | 63 CHIP |
| 5 CHIP | 5 CHIP | 5 CHIP |

Il player puo' scegliere un importo inferiore, ma non superiore al massimo consentito.

### Problema 3: sicurezza e chiarezza dei confini

Per produzione e integrazioni esterne, Mines non deve fidarsi del frontend e non deve fidarsi di dati economici passati dal client.

La piattaforma deve restare il punto autorevole per:

- autenticazione
- saldo
- limiti di sessione
- ledger
- idempotenza
- riconciliazione
- audit

Mines deve restare autorevole per:

- stato di gioco
- reveal safe/mine
- payout potenziale
- fairness
- RNG

Il confine deve essere esplicito.

## Stato attuale sintetico

### Comunicazione attuale

Oggi il flusso e':

```text
Browser player
  -> frontend Mines
    -> backend API /games/mines/*
      -> Mines service
        -> round_gateway.py
          -> platform rounds service
            -> wallet / ledger / DB
```

Mines e platform sono moduli separati, ma ancora nello stesso backend.

### Token attuale

Esiste `game_launch_token`.

Componenti:

- `POST /games/mines/launch-token`
- `POST /games/mines/launch/validate`
- header `X-Game-Launch-Token`
- JWT firmato con `settings.jwt_secret`
- audience `casinoking-mines`
- issuer `casinoking-platform`
- scadenza configurabile

Limite attuale:

- il token viene validato se presente
- in alcuni endpoint Mines e' opzionale
- la protezione primaria resta il bearer token player

### Access session attuale

Esiste `game_access_sessions`.

Flussi:

- create access session
- ping access session
- timeout dopo inattivita'
- auto-cashout per round Mines attiva in caso di timeout

Limite attuale:

- non contiene ancora `session_budget_amount`
- non contiene ancora `loss_limit_amount`
- non traccia in modo esplicito la perdita residua della sessione

### Wallet/ledger attuale

Il saldo e' platform-owned.

Allo start round:

- la piattaforma valida il wallet
- scala la puntata
- scrive ledger transaction `bet`
- scrive ledger entries double-entry
- aggiorna wallet snapshot

Al cashout:

- la piattaforma accredita payout
- scrive ledger transaction `win`
- scrive ledger entries double-entry
- aggiorna wallet snapshot

Alla perdita:

- la puntata era gia' stata scalata allo start
- la round viene chiusa come `lost`
- non viene accreditato payout

Questo modello va mantenuto.

## Obiettivo funzionale: Table Session

### Definizione

La Table Session e' la sessione di gioco Mines con budget di rischio massimo scelto dal player all'ingresso.

Non e' un portafoglio separato.
Non e' un trasferimento di fondi al gioco.
Non e' un credito posseduto da Mines.

E' un limite autorizzativo platform-owned.

### Regola di default

Quando il player entra in Mines:

```text
default_table_amount = min(wallet_balance_available, 100)
max_table_amount = min(wallet_balance_available, 100)
```

Il player puo':

- accettare il default
- ridurre manualmente l'importo
- aumentarlo solo fino a `max_table_amount`

Non puo':

- superare 100 CHIP
- superare il saldo disponibile
- inserire 0 o importi negativi
- usare un importo non valido

### Esempi

#### Caso A: saldo alto

```text
Saldo wallet: 350
Proposta ingresso: 100
Massimo selezionabile: 100
```

Se il player sceglie 80:

```text
session_budget_amount = 80
session_loss_limit_amount = 80
```

#### Caso B: saldo medio

```text
Saldo wallet: 63
Proposta ingresso: 63
Massimo selezionabile: 63
```

#### Caso C: saldo insufficiente

```text
Saldo wallet: 0
Ingresso Mines non disponibile
```

### Perdita massima

La perdita massima per sessione non e' calcolata su ogni singola puntata, ma sull'effetto netto/perdita consumata dentro la sessione.

Per MVP si propone un modello prudente:

```text
session_loss_consumed = somma delle puntate perse nella sessione
```

Prima di aprire una nuova round:

```text
session_loss_consumed + bet_amount <= session_loss_limit_amount
```

Se la condizione non e' rispettata:

```text
ROUND_LIMIT_EXCEEDED
```

Nota CTO:

Esiste una scelta di prodotto/contabilita' da confermare:

1. Limite sulla perdita lorda: ogni bet consuma budget se persa, le vincite non aumentano il budget.
2. Limite sulla perdita netta: vincite e perdite vengono compensate, consentendo piu' gioco se il player vince.

Per la prima implementazione si raccomanda il modello 1, piu' semplice e conservativo.

## Obiettivo architetturale: Mines come gioco esterno

### Target logico

Il target non e' "spostare subito cartelle e servizi".

Il target corretto e':

```text
Mines Game
  non conosce direttamente wallet internals
  non scrive direttamente ledger
  non decide se il player ha saldo sufficiente
  non possiede table budget
  chiede alla Platform tramite contratto

Platform
  autorizza player e sessione
  possiede saldo
  applica table budget
  apre round economiche
  registra bet/win/loss
  mantiene ledger e snapshot coerenti
```

### Target futuro fisico

Fase futura:

```text
Mines backend/service
  -> HTTP/API adapter
    -> Platform game API
      -> wallet/ledger/platform rounds
```

Oggi:

```text
Mines service
  -> round_gateway.py
    -> platform rounds service interno
```

La transizione deve essere graduale:

1. stabilizzare contratto interno
2. rendere gateway indipendente dai dettagli DB/platform
3. rendere token/sessione obbligatori
4. introdurre API platform coerenti
5. solo dopo sostituire chiamate interne con adapter HTTP

## Principio contabile non negoziabile

La table session non deve bypassare wallet/ledger.

Sono vietati:

- saldo interno al gioco non riconciliato
- update diretto del balance da Mines
- budget sessione calcolato solo lato frontend
- payout affidato al client
- settlement senza idempotenza

Sono obbligatori:

- ledger come fonte contabile primaria
- wallet snapshot aggiornato insieme al ledger
- double-entry
- idempotency key su start/cashout/settlement
- transazioni DB coerenti
- ownership user/session

## Modello dati proposto

### Opzione A: estendere `game_access_sessions`

Aggiungere campi:

```text
table_budget_amount numeric(18,6)
loss_limit_amount numeric(18,6)
loss_consumed_amount numeric(18,6) default 0
currency_code / chip_unit se necessario futuro
closed_reason
```

Vantaggi:

- semplice
- coerente con access session gia' esistente
- riduce nuove tabelle
- collega timeout e auto-cashout alla stessa sessione

Svantaggi:

- `game_access_sessions` diventa anche table session economica
- nel tempo potrebbe servire separare presence session e table budget

### Opzione B: nuova tabella `game_table_sessions`

Campi:

```text
id
access_session_id
user_id
game_code
wallet_account_id
table_budget_amount
loss_limit_amount
loss_consumed_amount
status
created_at
closed_at
closed_reason
```

Vantaggi:

- piu' pulita concettualmente
- separa presenza tecnica da sessione economica
- piu' adatta a giochi futuri

Svantaggi:

- piu' lavoro iniziale
- piu' join e test

### Raccomandazione

Per un progetto che punta a separare giochi e piattaforma, la scelta migliore e':

```text
creare game_table_sessions
```

Motivo:

- access session = presenza tecnica
- table session = budget e limite economico
- round = singola mano/partita

Separare questi tre concetti evita ambiguita' future.

## Nuovi concetti e responsabilita'

| Concetto | Proprietario | Responsabilita' |
| --- | --- | --- |
| Player auth | Platform | Identita', token player, ruolo |
| Wallet | Platform | Saldo snapshot, conto wallet |
| Ledger | Platform | Fonte contabile primaria |
| Access session | Platform | Presenza nel gioco, ping, timeout |
| Table session | Platform | Budget massimo e perdita massima sessione |
| Platform round | Platform | Bet, payout, status economico |
| Mines round | Mines | Board, celle, mine, stato gioco |
| RNG/fairness | Mines | Seed, board hash, nonce, verifica |
| Skin/UI | Mines frontend | Presentazione |

## Flusso funzionale target

### 1. Player apre Mines

```text
Player authenticated
  -> frontend Mines load
    -> GET wallet snapshot
    -> POST /games/mines/launch-token
    -> POST /access-sessions
    -> mostra Table Entry Screen
```

La schermata ingresso mostra:

- saldo disponibile
- importo proposto
- massimo consentito
- input importo
- conferma ingresso

### 2. Player conferma importo da portare al tavolo

```text
POST /platform/game-table-sessions
```

Payload concettuale:

```json
{
  "game_code": "mines",
  "access_session_id": "...",
  "wallet_type": "cash",
  "table_budget_amount": "100.000000"
}
```

La piattaforma valida:

- player autenticato
- access session attiva
- game code supportato
- wallet attivo
- saldo disponibile
- importo > 0
- importo <= 100
- importo <= saldo disponibile

Risposta:

```json
{
  "table_session_id": "...",
  "game_code": "mines",
  "wallet_type": "cash",
  "table_budget_amount": "100.000000",
  "loss_limit_amount": "100.000000",
  "loss_consumed_amount": "0.000000",
  "loss_remaining_amount": "100.000000",
  "status": "active"
}
```

### 3. Player inizia una round Mines

```text
POST /games/mines/start
```

Payload futuro:

```json
{
  "table_session_id": "...",
  "grid_size": 25,
  "mine_count": 3,
  "bet_amount": "5.000000",
  "wallet_type": "cash"
}
```

Platform valida:

```text
table_session active
same user
same game_code
bet_amount <= loss_remaining_amount
wallet still available
```

Poi:

- scala puntata dal wallet
- scrive ledger `bet`
- crea platform round
- Mines crea game round

### 4. Player rivela una cella safe

```text
POST /games/mines/reveal
```

Se safe:

- Mines aggiorna stato round
- Mines aggiorna payout potenziale
- nessun movimento ledger

### 5. Player rivela una mina

Se mine:

- Mines chiude round come lost
- Platform round chiusa lost
- perdita della puntata consumata nella table session

Aggiornamento:

```text
loss_consumed_amount += bet_amount
loss_remaining_amount = loss_limit_amount - loss_consumed_amount
```

### 6. Player fa cashout

```text
POST /games/mines/cashout
```

Se cashout:

- Platform accredita payout
- ledger `win`
- wallet snapshot aumenta
- platform round chiusa won
- Mines round chiusa won

Per MVP conservativo:

- una round vinta non aumenta il loss limit
- eventuale perdita consumata resta quella delle round perse

### 7. Player chiude sessione

Serve endpoint esplicito:

```text
POST /platform/game-table-sessions/{id}/close
```

Effetto:

- table session status = closed
- access session puo' essere chiusa o restare separata secondo UX
- nessun saldo da restituire, perche' il saldo non era stato trasferito al gioco

### 8. Timeout o crash

Se il player sparisce:

- access session va in timeout
- eventuale round active viene auto-cashout secondo regola esistente
- table session viene chiusa o marcata timed_out
- audit disponibile

Regola proposta:

```text
timeout access session -> close table session as timed_out
```

Se esiste round active:

- se nessuna safe reveal: refund/cashout pari alla bet secondo logica attuale
- se safe reveal > 0: cashout payout corrente

Questa regola va confermata con CTO per coerenza prodotto.

## API target interne/esterne

### Platform Game API

Queste API rappresentano il contratto che Mines dovrebbe usare come se fosse esterno.

| API | Scopo | Owner |
| --- | --- | --- |
| `POST /platform/game-launch/issue` | Emissione launch token | Platform |
| `POST /platform/game-launch/validate` | Validazione token | Platform |
| `POST /platform/game-access-sessions` | Presenza tecnica nel gioco | Platform |
| `POST /platform/game-access-sessions/{id}/ping` | Keepalive | Platform |
| `POST /platform/game-table-sessions` | Creazione table session con budget | Platform |
| `GET /platform/game-table-sessions/{id}` | Stato budget/sessione | Platform |
| `POST /platform/game-table-sessions/{id}/close` | Chiusura sessione | Platform |
| `POST /platform/game-rounds/open` | Apertura round economica/bet | Platform |
| `POST /platform/game-rounds/settle-win` | Settlement win/cashout | Platform |
| `POST /platform/game-rounds/settle-loss` | Settlement loss | Platform |
| `GET /platform/wallet/snapshot` | Saldo visualizzabile | Platform |

### Mines Game API

Queste restano lato gioco.

| API | Scopo | Owner |
| --- | --- | --- |
| `GET /games/mines/config` | Config runtime/presentation | Mines |
| `GET /games/mines/fairness/current` | Fairness corrente | Mines |
| `POST /games/mines/start` | Start round Mines | Mines + Platform boundary |
| `POST /games/mines/reveal` | Reveal cella | Mines |
| `POST /games/mines/cashout` | Cashout round | Mines + Platform boundary |
| `GET /games/mines/session/{id}` | Stato round | Mines |
| `GET /games/mines/session/{id}/fairness` | Dati fairness round | Mines |

## Sicurezza

### Locale

In locale puo' restare:

```text
HTTP
JWT
localhost / docker network
```

Il focus locale deve essere:

- correttezza funzionale
- idempotenza
- coerenza ledger/snapshot
- test di concorrenza
- ownership sessione

### Produzione

In produzione saranno necessari almeno:

- HTTPS/TLS obbligatorio
- `game_launch_token` obbligatorio
- scadenza breve token
- validazione audience/issuer/game_code
- ownership player/token/session
- idempotency key obbligatoria per movimenti economici
- rate limit su endpoint sensibili
- audit log
- CORS configurato solo per origini autorizzate

Per integrazione esterna reale valutare:

- firma HMAC delle richieste server-to-server
- secret per operator/partner
- IP allowlist
- mTLS tra game server e platform server
- rotazione chiavi
- replay protection
- correlation id su tutte le chiamate

## Cosa impedisce di barare

### Gia' oggi

Il player/frontend non puo':

- decidere board
- decidere mine
- decidere payout
- accreditarsi una vincita
- cambiare saldo direttamente
- usare sessione di un altro user senza ownership

Perche':

- backend Mines decide reveal e outcome
- backend platform valida wallet e ledger
- sessioni sono legate a user_id
- cashout/start usano idempotenza
- wallet rows vengono lockate in transazione

### Da rafforzare

Per target esterno:

- rendere launch token obbligatorio
- vincolare ogni round a table session
- rendere table session obbligatoria per start
- separare contratto platform/game
- evitare dipendenze dirette da internals platform nel game service

## UI proposta: Table Entry Screen

La schermata compare prima del gioco.

Contenuti funzionali:

- saldo disponibile
- importo massimo sessione
- importo proposto
- input importo
- controlli rapidi opzionali
- conferma ingresso
- errore se saldo insufficiente

Testi concettuali:

```text
Saldo disponibile: 350 CHIP
Porta al tavolo: [100]
Massimo perdita sessione: 100 CHIP
Entra nel gioco
```

Se saldo 63:

```text
Saldo disponibile: 63 CHIP
Porta al tavolo: [63]
Massimo perdita sessione: 63 CHIP
Entra nel gioco
```

Nota UX:

Questa schermata non deve sembrare un deposito reale al gioco.
Deve comunicare che e' un limite di sessione.

Possibile formulazione:

```text
Limite sessione Mines
Scegli quanto rendere disponibile per questa sessione.
```

## Risultato finale desiderato

Alla fine del percorso:

1. Il player entra in Mines solo dopo aver scelto un limite sessione.
2. Il limite massimo e' `min(wallet_balance, 100)`.
3. Mines non puo' superare quel limite di perdita.
4. Ogni round passa da validazione piattaforma.
5. Il saldo resta sempre nel wallet platform.
6. Ledger resta fonte primaria.
7. Mines resta server-authoritative sul gioco.
8. Platform resta authoritative su soldi, limiti e sessioni.
9. Il contratto platform/game e' esplicito.
10. Il gioco e' preparato per futura separazione fisica o integrazione esterna.

## Piano di implementazione proposto

### Fase 0 - Review CTO

Obiettivo:

- validare il modello table session
- scegliere perdita lorda vs perdita netta
- validare se creare nuova tabella `game_table_sessions`
- validare roadmap external game

Output:

- decisione architetturale
- eventuali correzioni a questo documento

### Fase 1 - Contratto e documentazione

Azioni:

- aggiornare `ARCHITECTURE_ATLAS_MINES.md`
- aggiornare `ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
- definire codici:
  - `PLATFORM_GAMES_00650` Table session
  - `MINES_PLATFORM_00520` Table session boundary
  - `MINES_API_00230` Required launch/table session contract
- definire errori:
  - `TABLE_SESSION_REQUIRED`
  - `TABLE_SESSION_NOT_ACTIVE`
  - `TABLE_LIMIT_EXCEEDED`
  - `GAME_LAUNCH_TOKEN_REQUIRED`

### Fase 2 - Database

Preferenza:

```text
nuova tabella game_table_sessions
```

Campi minimi:

```text
id
access_session_id
user_id
game_code
wallet_account_id
wallet_type
table_budget_amount
loss_limit_amount
loss_consumed_amount
status
created_at
closed_at
closed_reason
```

Vincoli:

- user ownership
- amount > 0
- loss consumed >= 0
- status enum/logico
- FK a access session se presente
- FK a wallet account

### Fase 3 - Platform service

Creare modulo:

```text
backend/app/modules/platform/table_sessions/service.py
```

Responsabilita':

- create table session
- get table session
- validate table session for round start
- consume loss on lost round
- close table session
- timeout table session

### Fase 4 - API platform

Creare route:

```text
backend/app/api/routes/platform_table_sessions.py
```

Endpoint MVP:

- `POST /table-sessions`
- `GET /table-sessions/{id}`
- `POST /table-sessions/{id}/close`

Nota:

Il path esatto puo' essere deciso in implementation. Per target esterno si potra' rinominare in `/platform/game-table-sessions`.

### Fase 5 - Mines backend contract

Modificare start Mines:

- richiedere `table_session_id`
- validare table session via platform service/gateway
- bloccare bet se supera budget residuo
- collegare platform_round a table_session

Modificare loss:

- quando round lost, consumare perdita nella table session

Modificare cashout:

- nessun consumo perdita se round vinta, nel modello conservativo

### Fase 6 - Launch token

Rendere obbligatorio `X-Game-Launch-Token` per:

- start
- reveal
- cashout
- session read
- fairness read

Valutare eccezioni:

- admin verify
- endpoint public config/fairness current

### Fase 7 - Frontend Table Entry Screen

In `frontend/app/ui/mines/mines-standalone.tsx`:

- mostra schermata ingresso prima del gioco
- legge wallet snapshot
- default `min(balance, 100)`
- input controllato
- conferma crea table session
- passare `table_session_id` a start
- mostra budget residuo/session limit in modo chiaro

### Fase 8 - Test

Test minimi:

- saldo 350 -> default 100
- saldo 63 -> default 63
- importo > 100 rifiutato
- importo > saldo rifiutato
- start round senza table session rifiutato
- bet oltre residuo rifiutata
- perdita aggiorna `loss_consumed_amount`
- cashout non rompe limite
- timeout chiude sessione
- idempotenza start/cashout invariata
- wallet/ledger reconciliation invariata
- ownership table session: user A non usa sessione user B

### Fase 9 - External adapter

Solo dopo stabilizzazione:

- definire interface `PlatformGameClient`
- implementazione attuale interna
- implementazione futura HTTP
- test contract tra Mines e Platform

## Decisioni aperte per CTO

| Tema | Opzione consigliata | Da decidere |
| --- | --- | --- |
| Limite sessione | perdita lorda | confermare |
| Tabella | `game_table_sessions` separata | confermare |
| Token launch | obbligatorio su endpoint round | confermare rollout |
| Timeout | auto-cashout e close table session | confermare product behavior |
| Produzione | HTTPS + token obbligatorio | confermare requisiti extra |
| Integrazione esterna | adapter HTTP dopo contratto interno | confermare milestone |

## Rischi

### Rischio tecnico: ledger drift

Mitigazione:

- nessun update saldo fuori platform service
- test reconciliation
- transazioni DB
- idempotenza

### Rischio prodotto: confusione "porta al tavolo"

Mitigazione:

- copy chiaro: limite sessione, non deposito al gioco
- saldo resta sulla piattaforma
- budget residuo mostrato in modo comprensibile

### Rischio architetturale: separazione prematura

Mitigazione:

- prima contratto interno
- poi adapter
- solo dopo eventuale servizio esterno

### Rischio sicurezza produzione

Mitigazione:

- HTTPS
- token obbligatorio
- firma richieste server-to-server
- audit
- rate limit

## Glossario

| Termine | Significato |
| --- | --- |
| Platform | Sistema che possiede player, wallet, ledger, sessioni e settlement. |
| Mines | Gioco server-authoritative con engine, RNG, fairness e payout runtime. |
| Access session | Presenza tecnica del player dentro un gioco. |
| Table session | Sessione economica/logica con budget massimo di perdita. |
| Platform round | Round economica, bet, payout, ledger refs. |
| Mines round | Stato specifico del gioco: celle, mine, reveal, multiplier. |
| Launch token | Token firmato che autorizza il player ad aprire/usare il gioco. |
| Idempotenza | Garanzia che retry della stessa azione non duplicano movimenti economici. |
| Wallet snapshot | Saldo operativo materializzato. |
| Ledger | Fonte contabile primaria double-entry. |

## Sintesi per CTO

La proposta non e' spostare subito Mines fuori dal repository.

La proposta e' rendere Mines "external-ready" introducendo:

1. contratto platform/game esplicito
2. launch token obbligatorio
3. table session con limite massimo perdita 100 CHIP
4. saldo sempre platform-owned
5. settlement sempre platform-owned
6. Mines authoritative solo su gioco, RNG e payout
7. percorso graduale verso adapter HTTP e integrazione esterna

Questo riduce rischio, aumenta chiarezza architetturale e prepara il progetto a ospitare altri giochi o partner futuri.
