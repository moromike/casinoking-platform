# Mines External Game + Table Session Plan

Documento operativo per valutazione CTO.

## Working agreement (per Claude / agenti AI che lavorano su questo piano)

- Il piano e' approvato. Procedere step-by-step senza chiedere conferma tra un commit e il successivo.
- Aggiornare questa pagina ad ogni step significativo: marker `[FATTA]` / `[DA FARE]` / `[PARZIALE]` sulle Fasi, riferimenti commit nello "Stato di avanzamento", aggiornare la tabella "Decisioni aperte".
- Committare e pushare dopo ogni feature logica, un commit alla volta. Questo e' il checkpoint reale.
- Fermarsi e chiedere solo se emerge: un workstream nuovo non concordato, un'ambiguita' di design irrisolta, una decisione product non specificata.
- Tenere il piano sempre allineato al codice cosi' un'altra istanza/modello puo' raccogliere il lavoro senza perdere contesto.
- I commit message includono i riferimenti delle precisazioni applicate (es. "applies CTO note 6: open_round atomic").

## Stato del documento

- Tipo: piano architetturale e funzionale.
- Scopo: descrivere esigenza, problema, target finale e percorso di implementazione.
- Stato: piano in corso di implementazione. Fasi 1-8 completate per il backend critical path, Admin force-close completato, Fase 9a completata; Fase 9b/c rinviata fino a decisione di pubblicazione/produzione. Vedi "Stato di avanzamento" qui sotto.
- Ambito: Mines, piattaforma, wallet/ledger, game launch, access session, sicurezza, futura integrazione esterna.
- Non sostituisce i documenti canonici in `docs/word/` e `docs/runtime/`.

## Stato di avanzamento (aggiornato 2026-05-04)

Sintesi rapida per CTO. Dettaglio completo nelle sezioni "Piano di implementazione" e "Decisioni aperte".

### Cosa e' stato fatto

| Fase | Stato | Riferimenti |
| --- | --- | --- |
| Fase 1 - Contratto e documentazione | FATTA | Atlas aggiornati con `MINES_FRONTEND_00145`, `MINES_PLATFORM_00520`, `PLATFORM_GAMES_00650` |
| Fase 2 - Database | FATTA | Migrazioni `0020__game_table_sessions.sql` e `0021__game_table_session_balance.sql` |
| Fase 3 - Platform service | FATTA | `backend/app/modules/platform/table_sessions/service.py` con lock atomici e auto-settle |
| Fase 4 - API platform | FATTA | `/table-sessions`, `/access-sessions/{id}/close`, `/auth/logout` |
| Fase 5 - Mines backend contract | FATTA | `rounds/service.py` aggancia `validate_and_reserve_round_exposure`, `consume_reserved_loss`, `release_reserved_loss` |
| Fase 6 - Launch token obbligatorio | FATTA | `start`, `reveal`, `cashout`, `session/{id}`, `session/{id}/fairness` richiedono `X-Game-Launch-Token`; bearer e launch token devono coincidere nel monolite |
| Fase 7 - Frontend Table Entry Screen | FATTA | Gate pre-game in `mines-standalone.tsx`, scelta wallet, importo controllato |
| Fase 8 - Test estesi backend | FATTA | Concorrenza stessa table session, retry start idempotente senza doppia riserva, timeout/cashout race, refund/cascade reconciliation, ownership cross-user |
| Fase 9a - `PlatformGameClient` in-process | FATTA | Nuovo `platform_client.py` con `PlatformGameClient`/`InProcessPlatformGameClient`; `round_gateway.py` diventa facciata compatibile e non importa piu' direttamente platform rounds |
| Cascade close (lifecycle) | FATTA (extra rispetto al piano) | login/logout/X/timeout/gate-confirm chiudono in cascata access_session + table_session + auto-cashout round attiva |
| Admin force-close (void session) | FATTA | Endpoint finance admin, reversal ledger `void`, chiusura access/table session, overlay player `SESSION_VOIDED_BY_OPERATOR`, reportistica finanziaria include bet+void |
| Test integration baseline | FATTA per backend critical path | 12 test integration nuovi (3 table session + 5 cascade close + 4 admin force-close) + test launch token required/invalid/expired/scope + edge case concorrenti Fase 8 |

### Cosa manca

| Tema | Stato | Note |
| --- | --- | --- |
| Fase 9b/c - HTTP adapter + contract test | RINVIATA | Implementazione HTTP futura + contract test tra in-process e HTTP. Riprendere quando Michele dira' "voglio pubblicare in produzione" |

### Decisione locale/produzione (2026-05-04)

Per il periodo in cui Michele lavora ancora in locale, la separazione completa via HTTP non viene implementata. Lo stato attuale e' sufficiente per continuare lo sviluppo locale perche':

- Fase 9a ha gia' introdotto il boundary `PlatformGameClient` in-process.
- Mines non importa piu' direttamente il service platform rounds tramite il gateway.
- I test di concorrenza/idempotenza e i contract test backend coprono il critical path locale.

Quando Michele dira' esplicitamente "voglio pubblicare in produzione", riprendere da Fase 9b/c:

- `HttpPlatformGameClient`
- endpoint platform-side equivalenti al contratto
- retry/timeout/error mapping HTTP-side
- contract test stesso scenario in-process vs HTTP
- sicurezza produzione: HMAC/mTLS/allowlist/replay protection/correlation id, secondo decisione deployment reale

### Cosa e' stato aggiunto rispetto al piano originale

Durante l'implementazione e' emerso un requisito non previsto inizialmente: **invariante "MAI piu' di una table_session attiva per user/gioco"**, con chiusura automatica delle sessioni residue su tutti gli eventi di lifecycle.

Implementato (commit `dd6d8ff`):

- login chiude tutte le sessioni precedenti e riapre pulito
- logout (`/auth/logout`) chiude tutto
- pulsante X nel gioco chiude la sessione corrente con cascade
- access session timeout (3 min inattivita') ora cascata anche su table_session
- `create_access_session` reso idempotente per supportare il reload pagina senza killare la round (Option A: resume su page load)
- `create_table_session` chiude orfani prima dell'INSERT
- rimossa la persistenza in localStorage del `tableSessionId` (causa del problema "il gate non compare al rientro")

Implementato nello step Admin force-close:

- endpoint finance admin `POST /admin/users/{user_id}/sessions/force-close`
- service dedicato `backend/app/modules/admin/session_force_close.py`
- nuovo audit `admin_actions.action_type = 'session_void'` e ledger `transaction_type = 'void'`
- chiusura atomica delle table/access session attive con `closed_reason = 'admin_voided'`
- round in volo marcata `platform_rounds.status = 'cancelled'` con reversal double-entry
- frontend Mines mostra overlay neutro "Sessione terminata" su `SESSION_VOIDED_BY_OPERATOR`
- backoffice player wallet espone il bottone force-close con conferma
- reportistica account/backoffice tratta il void come neutro: bet + void riportano delta banco netto 0

## Note CTO integrate prima dell'implementazione

Questa revisione incorpora quattro punti che sono stati risolti durante l'implementazione delle fasi 2-5:

1. La validazione del budget table session e la riserva/consumo dell'esposizione della puntata sono atomiche nella stessa transazione DB tramite `FOR UPDATE` sulla riga `game_table_sessions` (verificato in `validate_and_reserve_round_exposure`).
2. Il rollout su staging/produzione future seguira' la strategia "additivo + drain + enforcement" descritta in fondo a questo documento. In locale non e' applicabile.
3. Il limite MVP di 100 CHIP e' centralizzato in `TABLE_SESSION_MAX_CHIPS` in `backend/app/modules/platform/table_sessions/service.py`.
4. La regola di timeout/auto-cashout e' stata verificata contro `_auto_cashout_active_mines_round` esistente e ora si integra con la cascade close (commit `dd6d8ff`): cashout se safe_reveals > 0, refund se 0.

## Note CTO secondo giro (2026-05-03)

Precisazioni semantiche dopo la revisione del piano da parte del CTO. Da rispettare nelle implementazioni rimanenti.

### 1. Admin force-close: void come reversal tracciato, non cancellazione

La round annullata da admin **resta nel ledger**. Si scrive una transazione `void` di reversal in double-entry (debit house_cash, credit player wallet, importo = bet) che neutralizza la `bet` originale.

Risultato:

- netto P/L sulla round = 0
- audit trail completo: visibili sia la `bet` sia il `void`
- nessuna riga del ledger viene modificata o cancellata (ledger immutabile)

Formulazione corretta:

> "La round non produce P/L netto e viene neutralizzata con reversal ledger."

Formulazione da evitare:

> "La round non e' mai esistita ai fini contabili."

### 2. Admin force-close: scope limitato alle sessioni attive

L'operazione tocca **solo** stati `active`/`in-flight`:

- access_session attiva del player per il gioco indicato
- table_session attiva del player per il gioco indicato
- round in volo (con `loss_reserved > 0`)

**Non si toccano**:

- round gia' in stato `won` o `lost`
- transazioni ledger gia' settled
- sessioni gia' chiuse (`closed`, `timed_out`)

Storia immutabile, audit preservato.

### 3. Overlay player-side: testo neutro

Quando il backend risponde con `SESSION_VOIDED_BY_OPERATOR`, il frontend mostra un overlay con testo neutro che non espone il motivo operativo:

> "Sessione terminata. Rientra nel gioco per continuare."

Da evitare:

- "Sessione scaduta" — implica timeout automatico, semanticamente errato
- copy che riveli azioni admin o sospetti di abuso

### 4. Fase 6 vs Fase 9: chiarire la dipendenza dal bearer player

Esiste una tensione logica da non confondere.

**Stato attuale (monolite)**:

- bearer player + launch token coesistono
- Fase 6 stringe il modello attuale: ownership coerente tra i due, audience/issuer/game_code validati, scadenza breve

**Stato target (external-ready)**:

- il gioco non deve dipendere concettualmente dal bearer player
- l'autenticazione game-side passa solo per launch token (e/o auth server-to-server platform-game)
- Fase 9 deve **rimuovere la dipendenza** del game service dal bearer

Quindi la sequenza e':

1. Fase 6 - rendere obbligatori e coerenti bearer + launch token nel monolite
2. Fase 9 - rimuovere la dipendenza concettuale del gioco dal bearer

### 5. Fase 8: refund != mine hit

Il refund **non** si attiva quando il player clicca una mine. Mine hit = round persa, bet consumata, `loss_consumed += bet`.

Il refund si attiva solo quando una round attiva viene **interrotta da evento esterno** prima di qualsiasi reveal safe:

- timeout dell'access session con round attiva e `safe_reveals = 0`
- cascade close su login/logout/X con round attiva e `safe_reveals = 0`
- admin force-close su round attiva (sempre void/refund a prescindere dai safe_reveals, vedi punto 1)

Test corretto:

> "Refund su cascade/timeout con round active e `safe_reveals = 0`"

### 6. Fase 9: open_round resta atomico, no validate_table_session esposto

Nell'interfaccia `PlatformGameClient` (Fase 9) **non** esporre `validate_table_session` come operazione separata. Esporla rischia di re-introdurre il bug di atomicita' gia' risolto in Fase 3 (validazione e riserva separate da round-trip = race condition).

Interfaccia corretta:

```text
PlatformGameClient
  open_round(...)        # atomico: validate + reserve + debit + ledger bet
  settle_win(...)        # atomico: release reserve + credit + ledger win
  settle_loss(...)       # atomico: consume reserve + ledger loss
  void_round(...)        # admin: reversal + release reserve
  get_table_session_state(...)   # solo read-only per UI/status
```

Da evitare:

```text
PlatformGameClient
  validate_table_session(...)   # NO - rompe atomicita'
  reserve_exposure(...)         # NO - rompe atomicita'
  open_round(...)               # diventerebbe non-atomico
```

### 7. Test minimi nello stesso commit della feature

Ogni feature deve shippare con i suoi test minimi nello stesso commit. La "Fase 8 - Test estesi" e' riservata ai test cross-cutting di concorrenza/idempotenza/race condition, non ai test happy-path di feature singole.

Per il commit Admin force-close, i test minimi obbligatori sono:

- void idempotente (chiamare due volte lo stesso force-close non duplica il reversal)
- refund della bet in volo (loss_reserved rilasciato, table_balance ripristinato)
- log in `admin_actions` con admin_id, target_user_id, reason, timestamp
- reconciliation wallet/ledger invariata dopo il void
- cascade chiusura access_session + table_session
- ownership: admin senza permesso finance/support non puo' chiamare l'endpoint

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
- il game launch token e' obbligatorio sugli endpoint operativi Mines nel monolite
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

Il valore `100` e' un limite MVP di prodotto e non deve essere hardcoded nei service.

Configurazione minima raccomandata:

```text
TABLE_SESSION_MAX_CHIPS = 100
```

Per il primo rilascio puo' vivere come costante centralizzata lato platform/table session service o come setting applicativo. Non deve essere duplicata in frontend, Mines service, test e migration.

Evoluzione futura possibile:

- limite per `game_code`
- limite per operatore/partner esterno
- limite per VIP tier
- limite da backoffice, con audit delle modifiche

Il frontend puo' ricevere il massimo consentito dalla platform, ma non deve calcolarlo come fonte autorevole.

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

La perdita massima per sessione e' un limite economico platform-owned. Deve coprire anche la concorrenza tra richieste e i retry idempotenti.

Per MVP si propone un modello prudente basato su esposizione riservata:

```text
loss_reserved_amount = somma delle puntate di round aperte e non ancora chiuse
loss_consumed_amount = somma delle puntate perse definitivamente nella sessione
loss_available_amount = loss_limit_amount - loss_consumed_amount - loss_reserved_amount
```

Prima di aprire una nuova round:

```text
loss_consumed_amount + loss_reserved_amount + bet_amount <= loss_limit_amount
```

Se la condizione non e' rispettata:

```text
ROUND_LIMIT_EXCEEDED
```

Nota CTO obbligatoria:

La validazione della condizione e l'incremento di `loss_reserved_amount` devono avvenire nella stessa transazione DB che apre la platform round e registra la bet. La riga `game_table_sessions` deve essere letta con `SELECT ... FOR UPDATE` o lock equivalente.

Sequenza atomica raccomandata nello start round:

```text
BEGIN
  SELECT game_table_sessions WHERE id = :table_session_id FOR UPDATE
  validate ownership/status/game_code
  validate loss_consumed_amount + loss_reserved_amount + bet_amount <= loss_limit_amount
  update loss_reserved_amount += bet_amount
  debit wallet + ledger bet + wallet snapshot
  create platform round linked to table_session_id
  create Mines round
COMMIT
```

Effetto settlement:

- se la round perde: `loss_reserved_amount -= bet_amount` e `loss_consumed_amount += bet_amount`
- se la round vince/cashout: `loss_reserved_amount -= bet_amount`, senza aumentare `loss_consumed_amount`
- se la round viene rimborsata: `loss_reserved_amount -= bet_amount`, con refund ledger coerente se la bet era stata scalata

Questa distinzione evita che due start concorrenti superino il limite e consente di mantenere una UX piu' corretta rispetto al consumo immediato irreversibile della puntata.

Scelta di prodotto/contabilita' da confermare:

1. Limite sulla perdita lorda definitiva: le puntate perse consumano budget, le vincite non aumentano il budget.
2. Limite sulla perdita netta: vincite e perdite vengono compensate, consentendo piu' gioco se il player vince.

Per la prima implementazione si raccomanda il modello 1, piu' semplice e conservativo, con riserva atomica durante le round aperte.

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
loss_reserved_amount numeric(18,6) default 0
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
loss_reserved_amount
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
  "table_balance_amount": "100.000000",
  "loss_limit_amount": "100.000000",
  "loss_reserved_amount": "0.000000",
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
loss_consumed_amount + loss_reserved_amount + bet_amount <= loss_limit_amount
table_balance_amount >= bet_amount
wallet still available
```

Poi:

- locka `game_table_sessions` con `SELECT FOR UPDATE` o lock equivalente
- scala il saldo tavolo visibile `table_balance_amount -= bet_amount`
- riserva esposizione `loss_reserved_amount += bet_amount`
- scala puntata dal wallet
- scrive ledger `bet`
- crea platform round
- Mines crea game round

Questi passaggi devono stare nella stessa transazione DB. Non e' sufficiente validare prima e aggiornare dopo, perche' due start concorrenti dello stesso player potrebbero leggere lo stesso budget residuo e superare il limite.

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
- esposizione riservata convertita in perdita consumata nella table session

Aggiornamento:

```text
loss_reserved_amount -= bet_amount
table_balance_amount resta gia' ridotto dalla bet
loss_consumed_amount = perdita netta rispetto al budget iniziale
loss_remaining_amount = loss_limit_amount - loss_consumed_amount - loss_reserved_amount
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
- table session rilascia la bet riservata e accredita il payout totale sul saldo tavolo visibile

Per MVP conservativo:

- una round vinta non aumenta il loss limit
- eventuale perdita consumata resta quella delle round perse
- la riserva della puntata viene rilasciata: `loss_reserved_amount -= bet_amount`

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

Nota CTO obbligatoria prima di implementare:

Il documento assume che la logica attuale di `game_access_sessions` supporti gia' un auto-cashout coerente con questi due casi. Prima della Fase 5 va verificato nel codice reale:

- se la round senza safe reveal viene gia' rimborsata o chiusa con payout pari alla bet
- se la round con safe reveal viene gia' cashoutata al payout corrente
- se la chiusura per timeout e' idempotente
- se wallet, ledger, platform round e Mines round restano coerenti in caso di retry o timeout concorrenti

Se il comportamento attuale non copre questi casi, la Fase 5 deve includere esplicitamente l'estensione di `game_access_sessions` e i relativi test.

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

## Strategia migration e rollout dati

Prima di rendere obbligatori `game_launch_token` e `table_session_id` bisogna definire il comportamento dei dati esistenti. La strategia e' quella descritta in questa sezione.

Nel contesto attuale il progetto e' ancora locale, quindi non ci sono vincoli di produzione. Per staging o una futura beta, questa strategia va applicata prima del deploy enforcement, per evitare round/sessioni incompatibili.

### Stati esistenti da considerare

- round Mines terminali senza `table_session_id`
- round Mines active/in_progress senza `table_session_id`
- access session attive senza table session
- launch token emessi prima dell'obbligatorieta'
- history player/admin che mostra round vecchie

### Strategia raccomandata per ambiente locale/MVP

Per sviluppo locale:

- applicare migration additiva
- consentire history read-only delle round storiche senza table session
- bloccare solo i nuovi start round senza table session
- chiudere o invalidare eventuali access session attive create prima della migration
- non retro-contabilizzare budget table session sulle round gia' terminali

### Strategia raccomandata per staging/produzione futura

Prima del deploy che rende obbligatorio il contratto:

1. deploy additivo: creare `game_table_sessions`, campi FK opzionali e codice compatibile con vecchie round.
2. periodo compatibilita': nuove round usano table session, vecchie round restano leggibili.
3. drain sessioni attive: impedire nuovi start legacy e attendere chiusura/timeout delle round active.
4. backfill minimo: valorizzare `table_session_id` solo dove esiste una regola certa; altrimenti lasciare NULL per storico read-only.
5. enforcement: rendere obbligatorio `table_session_id` per nuovi start e `X-Game-Launch-Token` sugli endpoint round.
6. cleanup: rimuovere codice legacy solo dopo verifica di assenza sessioni active legacy.

Vincolo:

Non deve esserci una migration che inventa budget storici o altera movimenti ledger gia' chiusi.

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

### Fase 0 - Review CTO [FATTA]

Obiettivo:

- validare il modello table session
- scegliere perdita lorda vs perdita netta
- validare se creare nuova tabella `game_table_sessions`
- validare roadmap external game

Output:

- decisione architetturale
- eventuali correzioni a questo documento

### Fase 1 - Contratto e documentazione [FATTA]

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
- definire collocazione della configurazione:
  - `TABLE_SESSION_MAX_CHIPS = 100`
  - fonte autorevole lato platform, esposta al frontend via API/config response

### Fase 2 - Database [FATTA]

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
loss_reserved_amount
loss_consumed_amount
status
created_at
closed_at
closed_reason
```

Vincoli:

- user ownership
- amount > 0
- loss reserved >= 0
- loss consumed >= 0
- loss_reserved_amount + loss_consumed_amount <= loss_limit_amount
- status enum/logico
- FK a access session se presente
- FK a wallet account

### Fase 3 - Platform service [FATTA]

Creare modulo:

```text
backend/app/modules/platform/table_sessions/service.py
```

Responsabilita':

- create table session
- get table session
- validate and reserve table session exposure for round start
- consume reserved exposure on lost round
- release reserved exposure on win/cashout/refund
- close table session
- timeout table session

Regola transazionale:

- `validate and reserve` deve fare lock della riga `game_table_sessions` nella stessa transazione che apre la platform round e registra la bet.
- `consume` e `release` devono essere idempotenti e collegati allo stato terminale della platform round.
- retry della stessa richiesta non deve duplicare riserva, consumo, release, ledger transaction o wallet snapshot update.

### Fase 4 - API platform [FATTA]

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

### Fase 5 - Mines backend contract [FATTA]

Modificare start Mines:

- richiedere `table_session_id`
- validare table session via platform service/gateway
- bloccare bet se supera budget residuo
- riservare atomicamente l'esposizione della bet su `game_table_sessions`
- collegare platform_round a table_session

Modificare loss:

- quando round lost, convertire riserva in perdita consumata nella table session

Modificare cashout:

- nessun consumo perdita se round vinta, nel modello conservativo
- rilasciare la riserva della bet

Prerequisito Fase 5:

- verificare e, se necessario, estendere la logica attuale di timeout/auto-cashout in `game_access_sessions`
- coprire esplicitamente round active senza safe reveal e round active con safe reveal
- garantire idempotenza del timeout rispetto a cashout/reveal concorrenti

### Fase 6 - Launch token [FATTA]

Rendere obbligatorio `X-Game-Launch-Token` per:

- start
- reveal
- cashout
- session read
- fairness read

Valutare eccezioni:

- admin verify
- endpoint public config/fairness current

Prerequisito Fase 6:

- applicare la strategia migration/rollout dati descritta in questo documento
- non rendere obbligatorio `table_session_id` o launch token finche' esistono round active legacy non gestite

Implementato:

- `start`, `reveal`, `cashout`, `session/{id}`, `session/{id}/fairness` richiedono `X-Game-Launch-Token`
- `config` e `fairness/current` restano pubblici
- `launch-token` resta emesso con bearer player nel monolite
- bearer player e player del launch token devono coincidere
- token mancante -> `401 GAME_LAUNCH_TOKEN_REQUIRED`
- token invalido/scaduto -> `401 GAME_LAUNCH_TOKEN_INVALID`
- token valido ma di altro player o altro gioco -> `403 FORBIDDEN`
- il frontend tratta gli errori launch token come stato da riallineare senza logout automatico

### Fase 7 - Frontend Table Entry Screen [FATTA]

In `frontend/app/ui/mines/mines-standalone.tsx`:

- mostra schermata ingresso prima del gioco
- legge wallet snapshot
- default `min(balance, TABLE_SESSION_MAX_CHIPS)` usando il massimo restituito dalla platform
- input controllato
- conferma crea table session
- passare `table_session_id` a start
- mostra budget residuo/session limit in modo chiaro

### Fase 8 - Test [FATTA - backend critical path]

Test minimi:

- saldo 350 -> default 100
- saldo 63 -> default 63
- importo > `TABLE_SESSION_MAX_CHIPS` rifiutato
- importo > saldo rifiutato
- start round senza table session rifiutato
- bet oltre residuo rifiutata
- start concorrenti sulla stessa table session non superano `loss_limit_amount`
- retry idempotente dello start non duplica `loss_reserved_amount`
- perdita converte riserva in `loss_consumed_amount`
- cashout rilascia `loss_reserved_amount` e non rompe limite
- refund rilascia `loss_reserved_amount` e mantiene ledger/wallet coerenti
- timeout chiude sessione
- timeout con round active e cashout concorrente resta idempotente
- idempotenza start/cashout invariata
- wallet/ledger reconciliation invariata
- ownership table session: user A non usa sessione user B

Implementato nel checkpoint Fase 8:

- `tests/concurrency/test_mines_concurrency.py`
  - start concorrenti sulla stessa `table_session_id` non superano `loss_limit_amount`
  - retry concorrente con stessa idempotency key non duplica `loss_reserved_amount`
  - race timeout ping + cashout produce una sola `win` e rilascia la riserva table session
- `tests/integration/test_game_table_sessions.py`
  - ownership cross-user: un player non puo' leggere/usare la table session di un altro player
- `tests/integration/test_session_cascade_close.py`
  - refund su cascade close senza safe reveal rilascia `loss_reserved_amount`, ripristina `table_balance_amount` e mantiene wallet/ledger reconciliation a drift 0

### Fase 9 - External adapter [PARZIALE - 9a FATTA]

Solo dopo stabilizzazione:

- definire interface `PlatformGameClient`
- implementazione attuale interna
- implementazione futura HTTP
- test contract tra Mines e Platform

Implementato in Fase 9a:

- nuovo `backend/app/modules/games/mines/platform_client.py`
- `PlatformGameClient` come boundary esplicito game -> platform
- `InProcessPlatformGameClient` come implementazione monolite attuale
- `round_gateway.py` resta facciata compatibile per `service.py`, ma delega al client configurato
- nessun `validate_table_session` esposto: `open_round(...)` resta atomico
- contract test aggiornati per verificare che `round_gateway.py` non importi piu' direttamente `app.modules.platform.rounds.service`

Da fare in Fase 9b/c:

- `HttpPlatformGameClient`
- endpoint platform-side equivalenti al contratto
- retry/timeout/error mapping HTTP-side
- contract test che eseguono lo stesso scenario con client in-process e HTTP

Decisione 2026-05-04:

- Fase 9b/c e' rinviata finche' il progetto resta in lavoro locale.
- Riprendere solo su trigger esplicito di Michele: "voglio pubblicare in produzione".
- Nel frattempo non introdurre adapter HTTP parziali o doppio path applicativo non necessario.

## Decisioni aperte per CTO

| Tema | Opzione | Stato |
| --- | --- | --- |
| Limite sessione | perdita lorda | CONFERMATA, implementata |
| Atomicita' limite | lock `game_table_sessions` + riserva allo start | CONFERMATA, implementata via `FOR UPDATE` |
| Config limite 100 | costante centralizzata `TABLE_SESSION_MAX_CHIPS` | CONFERMATA, in `table_sessions/service.py` |
| Tabella | `game_table_sessions` separata | CONFERMATA, migrazione 0020 |
| Token launch | obbligatorio su endpoint round/session | CONFERMATA, implementata in Fase 6 |
| Migration dati legacy | rollout additivo + drain sessioni active | CONFERMATA, applicabile a futuro deploy staging/produzione |
| Timeout | auto-cashout e close table session | CONFERMATA, implementata con cascade close (commit `dd6d8ff`) |
| Produzione | HTTPS + token obbligatorio | DA DEFINIRE quando si arrivera' al deploy reale |
| Integrazione esterna | adapter HTTP dopo contratto interno | PARZIALE - Fase 9a in-process fatta, HTTP/contract rinviati fino a trigger produzione |
| Invariante 1 sessione attiva per user/gioco | rigid mode, cascade close su lifecycle | CONFERMATA, implementata (extra rispetto al piano originale) |
| Page load behavior | Option A - resume round se attiva | CONFERMATA, implementata via `create_access_session` idempotente |
| Admin force-close | semantica "void" con reversal ledger pulito | CONFERMATA, implementata |

## Rischi

### Rischio tecnico: ledger drift

Mitigazione:

- nessun update saldo fuori platform service
- test reconciliation
- transazioni DB
- idempotenza

### Rischio tecnico: superamento limite per concorrenza

Mitigazione:

- lock `game_table_sessions` con `SELECT FOR UPDATE` o equivalente
- validazione e riserva esposizione nella stessa transazione dello start round
- test concorrenti sullo stesso player/table session
- idempotenza su riserva, consumo e release

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
6. riserva atomica dell'esposizione round con lock sulla table session
7. migration strategy prima di rendere obbligatori token e table session
8. Mines authoritative solo su gioco, RNG e payout
9. percorso graduale verso adapter HTTP e integrazione esterna

Questo riduce rischio, aumenta chiarezza architetturale e prepara il progetto a ospitare altri giochi o partner futuri.
