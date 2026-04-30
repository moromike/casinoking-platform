# CasinoKing - Blueprint Tecnico di Implementazione

Contratto Platform/Game, Mappa Stato Attuale -> Target e Piano di Esecuzione a Rischio Minimo

## Stato del documento

- Documento operativo tecnico.
- Estende il masterplan:
  - [PLATFORM_GAME_SEPARATION_AND_ENVIRONMENTS_MASTERPLAN_2026_04.md](C:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/PLATFORM_GAME_SEPARATION_AND_ENVIRONMENTS_MASTERPLAN_2026_04.md)
- Scopo:
  - trasformare la visione in piano implementativo concreto
  - mappare l'architettura reale del repo contro l'architettura target
  - definire il primo intervento di codice con rischio minimo
- Non autorizza da solo lo sviluppo: serve come base di decisione prima di toccare il codice.

## 1. Obiettivo del blueprint

Questo documento esiste per rispondere a quattro domande tecniche precise:

1. Oggi, in quali punti il confine `platform <-> game` e' gia' presente davvero nel codice?
2. Oggi, in quali punti quel confine e' ancora incompleto o ambiguo?
3. Qual e' il contratto target minimo che ci permette di evolvere verso giochi separabili senza rompere il core?
4. Qual e' il primo step implementativo che produce valore architetturale senza aprire una cascata di regressioni?

L'obiettivo non e' massimizzare il cambiamento.

L'obiettivo e' minimizzare il rischio architetturale e il costo futuro di sviluppo.

## 2. Fonti usate

### 2.1 Fonti canoniche

- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/md/CasinoKing_Documento_02_Fondazioni_Architettura.md`
- `docs/md/CasinoKing_Documento_03_Architettura_DB_API.md`
- `docs/md/CasinoKing_Documento_05_v3_Wallet_Ledger_Fondamenta_Definitive.md`
- `docs/md/CasinoKing_Documento_06_Mines_Prodotto_Stati_Matematica_API.md`
- `docs/md/CasinoKing_Documento_11_v2_API_Contract_Allineato_v3.md`
- `docs/md/CasinoKing_Documento_14_v2_Ambiente_Locale_Realtime_Policy.md`
- `docs/md/CasinoKing_Documento_15_Piano_Implementazione.md`

### 2.2 Fonti operative gia' presenti nel repo

- `docs/md/CasinoKing_Documento_31_Contratto_Tra_Platform_Backend_E_Mines_Backend.md`
- `docs/md/CasinoKing_Documento_34_Contratto_API_Operativo_Platform_Mines_v1.md`
- `docs/md/CasinoKing_Documento_35_Contratto_API_Operativo_Platform_Game_v1.md`
- `docs/CTO_MINES_ANALYSIS_2026_03_30.md`

### 2.3 Codice analizzato

- `backend/app/api/routes/mines.py`
- `backend/app/api/routes/platform_access.py`
- `backend/app/modules/platform/game_launch/service.py`
- `backend/app/modules/platform/access_sessions/service.py`
- `backend/app/modules/platform/rounds/service.py`
- `backend/app/modules/games/mines/round_gateway.py`
- `backend/app/modules/games/mines/service.py`
- `frontend/app/ui/mines/mines-standalone.tsx`

## 3. Decisione tecnica di partenza

Il blueprint assume come decisione ufficiale il seguente modello:

- `platform` resta authority per identity, wallet, ledger, settlement, reporting e admin
- `game` resta authority per gameplay, fairness, runtime, board e stato tecnico
- il contratto tra i due domini deve diventare sempre piu' stretto, esplicito e versionabile
- il deployment puo' restare monorepo-based in questa fase, ma l'architettura deve diventare deploy-separable

## 4. Fotografia dello stato attuale

## 4.1 Cose gia' corrette

Oggi nel progetto esistono gia' i semi giusti del modello target.

### A. Esiste il concetto di `game_code`

Questo e' molto importante, perche' evita di costruire un sistema hardcoded su Mines senza chiavi di generalizzazione.

### B. Esiste il concetto di `game_access_session`

Questo significa che il progetto ha gia' introdotto una distinzione tra:

- accesso esteso al gioco
- round economica

Anche se la distinzione non e' ancora perfetta, la direzione e' corretta.

### C. Esiste il `game_launch_token`

Questo significa che l'handoff platform -> game non e' solo "entri con il bearer normale".

Esiste gia' un token pensato per il lancio del gioco.

### D. Esiste un primo boundary adapter

Il file `backend/app/modules/games/mines/round_gateway.py` e' gia' una forma di confine applicativo:

- il gioco parla con un gateway
- il gateway traduce verso il dominio platform

Questo e' esattamente il pattern da preservare.

### E. Il core finanziario e' gia' fuori dal frontend gioco

Il frontend gioco non decide outcome economici.
La parte finanziaria vive sul backend.

### F. Le API di access session platform esistono gia'

`backend/app/api/routes/platform_access.py` mostra che il progetto ha gia' iniziato a portare alcuni concetti sotto namespace platform.

## 4.2 Cose ancora transitorie

Oggi il progetto non e' ancora arrivato al target finale.

### A. Il launch token e' ancora esposto sotto route Mines

In `backend/app/api/routes/mines.py` oggi esistono:

- `POST /games/mines/launch-token`
- `POST /games/mines/launch/validate`

Concettualmente questo e' gia' un segnale di transizione:

- il token e' una preoccupazione platform
- ma al momento la sua surface pubblica vive ancora nel namespace gioco

### B. `start_session()` Mines conosce ancora dettagli finanziari

Nel servizio Mines, il flusso di start:

- apre la round
- legge ritorni finanziari
- inserisce record platform round
- inserisce record game round

Questo e' molto meglio del vecchio modello monolitico, ma significa ancora che il servizio gioco e' troppo consapevole del lifecycle economico.

### C. Identificatore round tecnica e round finanziaria coincidono troppo

Oggi il `session_id` generato in `start_session()` viene usato come:

- id di sessione/round visibile dal gioco
- id della round platform

Questo riduce complessita' immediata, ma nel medio periodo rende meno chiara la separazione dei domini.

### D. Il token e' stateless senza consumption tracking

`backend/app/modules/platform/game_launch/service.py` oggi:

- emette JWT
- verifica firma, issuer, audience e claims

Ma non traccia:

- consumo
- revoca
- bounded-use

Per MVP puo' essere accettabile.
Per una separazione seria platform/provider esterno, no.

### E. La route pubblica del gioco continua a portarsi dietro pezzi del modello transitorio

`/games/mines/start` oggi e' ancora endpoint ibrido dal punto di vista concettuale:

- dal lato client sembra gioco puro
- sotto il cofano apre anche il lifecycle economico

Questo e' normale per una fase di migrazione, ma non e' il target.

## 5. Mappa stato attuale -> target

Questa sezione e' il cuore operativo del documento.

## 5.1 Handoff di lancio

### Stato attuale

- route: `POST /games/mines/launch-token`
- route: `POST /games/mines/launch/validate`
- service: `platform/game_launch/service.py`

### Valutazione

- bene: il token esiste gia'
- bene: il contenuto del token e' sensato
- limite: ownership concettuale ancora sotto namespace Mines
- limite: no token consumption tracking

### Target

Concettualmente il launch token dovrebbe vivere sotto area platform, con un contratto generico game-aware:

- `POST /internal/v1/platform/game-launch/issue`
- `POST /internal/v1/games/{game_code}/launch/validate`

oppure, se si vuole tenere il validate lato game:

- issue lato platform
- validate lato game

### Decisione raccomandata

Non spostare subito le route pubbliche.

Prima:

- stabilizzare il contratto logico
- introdurre naming e ownership nei documenti
- poi spostare o duplicare le route con compatibilita' transitoria

Questo evita regressioni frontend inutili.

## 5.2 Access session

### Stato attuale

- route: `POST /access-sessions`
- route: `POST /access-sessions/{access_session_id}/ping`
- service: `platform/access_sessions/service.py`

### Valutazione

Questa e' una delle parti gia' piu' corrette dell'architettura.

Perche':

- e' sotto namespace platform
- e' game-aware via `game_code`
- e' distinta dalla round economica

### Target

Mantenere il concetto e rafforzarlo.

Possibili estensioni future:

- `close access session`
- `resume access session`
- policy timeout configurabile per game code

### Decisione raccomandata

Non toccare pesantemente questa parte nella prima iterazione.

Va considerata base architetturale gia' buona.

## 5.3 Apertura round economica

### Stato attuale

Oggi il frontend chiama:

- `POST /games/mines/start`

Il backend gioco:

- valida config
- apre round via `round_gateway.open_round()`
- scrive record platform round
- scrive record game round

### Valutazione

Qui il boundary e' iniziato ma non completato.

Punti positivi:

- il movimento economico vero passa da `platform/rounds/service.py`
- esiste un gateway dedicato

Punti ancora transitori:

- Mines orchestration conosce troppo del sequencing economico
- l'API pubblica continua a presentarsi come "game start", ma in realta' ingloba apertura round economica

### Target

Target concettuale:

1. game riceve richiesta di start
2. game valida config
3. game chiama platform `rounds/open`
4. platform risponde con `platform_round_id`
5. game crea il proprio `game_round_id`

### Decisione raccomandata

Non introdurre subito nuove API esterne pubbliche verso il frontend.

Il primo passaggio pulito e' interno:

- isolare meglio il contratto `game service -> round gateway`
- rendere piu' esplicita la risposta `platform_round_id`
- ridurre la conoscenza finanziaria diretta nel servizio Mines

## 5.4 Reveal

### Stato attuale

- route: `POST /games/mines/reveal`
- ownership: gioco

### Valutazione

Questa parte e' gia' allineata al target.

Il reveal:

- e' server-authoritative
- vive nel dominio gioco
- non genera posting intermedi

### Target

Resta invariato concettualmente.

### Decisione raccomandata

Non usare il reveal come area di refactor boundary nella prima fase.

E' una delle parti piu' sane del sistema.

## 5.5 Settlement round

### Stato attuale

- route pubblica: `POST /games/mines/cashout`
- sotto il cofano passa da gateway e platform rounds
- la loss avviene nel lifecycle game con settle lato platform

### Valutazione

Anche qui il pattern di fondo e' corretto, ma la surface pubblica resta ibrida.

### Target

Target concettuale:

- il gioco determina esito finale
- la piattaforma registra settlement finale

API target interne:

- `POST /internal/v1/seamless-wallet/rounds/{platform_round_id}/settle-lost`
- `POST /internal/v1/seamless-wallet/rounds/{platform_round_id}/settle-won`

oppure un endpoint unico:

- `POST /internal/v1/seamless-wallet/rounds/settle`

### Decisione raccomandata

Per la prima implementazione seria non serve ancora spaccare `won` e `lost` in API distinte se questo complica troppo.

Serve prima chiarire:

- payload
- ownership
- idempotency
- identifiers

## 5.6 Identificatori

### Stato attuale

Nel progetto oggi si vedono:

- `platform_session_id`
- `play_session_id`
- `game_play_session_id`
- `access_session_id`
- `game_session_id`

### Problema

Il sistema e' ricco di identificatori, ma non ancora abbastanza didascalico su cosa appartiene a quale layer.

### Target

Set di identificatori chiaro:

- `platform_session_id` = sessione piattaforma
- `access_session_id` = permanenza estesa nel gioco lato platform
- `platform_round_id` = round economica platform
- `game_round_id` = round tecnica lato gioco
- `game_play_session_id` = eventuale sessione tecnica di presenza lato gioco, se davvero serve distinta

### Decisione raccomandata

Prima di cambiare il codice, va scritto un piccolo glossario ufficiale degli ID e del loro ownership.

Questa e' una di quelle cose che costano poco e riducono tantissima confusione futura.

## 6. Contratto target endpoint-by-endpoint

Questa sezione definisce la forma target raccomandata, senza pretendere di implementarla tutta subito.

## 6.1 Group A - Platform public/player-facing APIs

Queste sono le API che il frontend platform puo' usare direttamente.

### `POST /access-sessions`

Scopo:

- creare o riaprire una sessione di accesso al gioco

Ownership:

- platform

Stato:

- gia' esiste

### `POST /access-sessions/{access_session_id}/ping`

Scopo:

- tenere viva la sessione di accesso

Ownership:

- platform

Stato:

- gia' esiste

### `POST /platform/game-launch`

Scopo:

- emettere `game_launch_token`

Ownership:

- platform

Stato:

- non esiste ancora come route platform esplicita
- concetto gia' esiste sotto route Mines

Decisione:

- candidata naturale a un primo spostamento futuro
- ma non nel primissimo intervento

## 6.2 Group B - Game public/player-facing APIs

Queste sono le API che il frontend gioco usa per il gameplay.

### `POST /games/mines/start`

Scopo:

- oggi apre anche la round economica
- in target deve diventare orchestration di dominio gioco che usa un boundary interno pulito

Stato:

- esiste

Decisione:

- mantenerla come endpoint pubblico stabile nel breve periodo
- non cambiare il contratto client-facing finche' il boundary interno non e' maturo

### `POST /games/mines/reveal`

Stato:

- corretto e stabile

Decisione:

- da mantenere come API gioco

### `POST /games/mines/cashout`

Stato:

- corretto come API pubblica gioco
- internamente ancora transitorio lato settlement orchestration

Decisione:

- mantenere pubblico
- ripulire internamente il boundary

### `GET /games/mines/session/{id}`

Stato:

- corretto come API gioco

### `GET /games/mines/session/{id}/fairness`

Stato:

- corretto come API gioco

## 6.3 Group C - Internal platform seamless-wallet APIs

Queste sono le API che il game provider dovrebbe poter chiamare verso la piattaforma.

Non devono per forza diventare HTTP reali subito, ma il loro shape deve essere pensato come se un giorno lo fossero.

### `POST /internal/v1/seamless-wallet/rounds/open`

Request minima raccomandata:

```json
{
  "player_id": "uuid",
  "access_session_id": "uuid",
  "game_code": "mines",
  "idempotency_key": "uuid-or-stable-key",
  "wallet_type": "cash",
  "bet_amount": "5.000000",
  "currency_code": "CHIP",
  "game_config": {
    "grid_size": 25,
    "mine_count": 3
  }
}
```

Response minima raccomandata:

```json
{
  "platform_round_id": "uuid",
  "wallet_balance_after_start": "995.000000",
  "ledger_transaction_id": "uuid",
  "opened_at": "2026-04-12T18:00:00Z"
}
```

### `POST /internal/v1/seamless-wallet/rounds/settle`

Request minima raccomandata:

```json
{
  "platform_round_id": "uuid",
  "game_round_id": "uuid",
  "game_code": "mines",
  "player_id": "uuid",
  "idempotency_key": "uuid-or-stable-key",
  "outcome": "won",
  "payout_amount": "12.700000",
  "currency_code": "CHIP",
  "game_result": {
    "safe_reveals_count": 4,
    "reason": "cashout",
    "final_multiplier": "2.5400"
  }
}
```

Response minima raccomandata:

```json
{
  "platform_round_id": "uuid",
  "status": "settled",
  "wallet_balance_after_settlement": "1007.700000",
  "ledger_transaction_id": "uuid",
  "settled_at": "2026-04-12T18:03:00Z"
}
```

### `POST /internal/v1/seamless-wallet/play-sessions/close`

Scopo:

- opzionale nella prima fase
- utile per analytics, audit, cleanup stato

Decisione:

- non entra nella prima implementazione

## 6.4 Group D - Internal game launch validation API

### `POST /internal/v1/games/mines/launch/validate`

Scopo:

- validare il `game_launch_token`
- aprire o confermare la sessione tecnica lato gioco

Request minima:

```json
{
  "game_launch_token": "jwt"
}
```

Response minima:

```json
{
  "player_id": "uuid",
  "game_code": "mines",
  "platform_session_id": "uuid",
  "access_session_id": "uuid",
  "game_play_session_id": "uuid",
  "expires_at": "2026-04-12T18:15:00Z"
}
```

Nota:

Qui bisogna decidere in una fase successiva se `access_session_id` debba entrare gia' nel token o restare coordinato dalla platform separatamente.

## 7. Policy di compatibilita' e migrazione

Qui c'e' la parte piu' importante per evitare regressioni.

## 7.1 Regola di migrazione

Ogni refactor boundary deve rispettare questa sequenza:

1. definire contratto target
2. introdurre adapter o naming transitorio
3. mantenere surface pubblica stabile
4. spostare wiring interno
5. solo alla fine cambiare route/client se davvero serve

Questa regola evita di rompere frontend, admin e smoke flow mentre si lavora sul cuore architetturale.

## 7.2 Regola sugli endpoint pubblici

Gli endpoint pubblici del gioco non devono essere rivoluzionati nella prima fase.

Perche':

- il rischio di regressione e' alto
- il vero problema non e' il path URL, ma il boundary interno
- cambiare l'URL senza cambiare l'ownership reale non migliora l'architettura

## 7.3 Regola sugli identificatori

Prima si chiarisce il naming.
Poi si cambia lo schema o il codice.

Altrimenti si rischia di creare un falso refactor, dove cambiano i nomi ma non la chiarezza.

## 8. Primo intervento di codice raccomandato

Questa e' la sezione decisiva.

Se dovessimo iniziare davvero, il primo intervento NON dovrebbe essere:

- deploy beta
- estrarre Mines fuori repo
- introdurre provider esterno
- cambiare tutte le route

Il primo intervento corretto dovrebbe essere molto piu' controllato.

### 8.1 Obiettivo del primo intervento

Rendere il boundary interno piu' esplicito senza cambiare il comportamento pubblico.

### 8.2 Contenuto del primo intervento

#### Step 1. Glossario ufficiale degli ID e ownership

Produrre un piccolo documento operativo con:

- elenco ID
- significato
- ownership
- dove nascono
- dove vengono usati

Perche':

- costa poco
- riduce ambiguita'
- prepara il codice senza toccarlo ancora

#### Step 2. Formalizzare il contratto interno del gateway

Oggi `round_gateway.py` esiste gia'.

Bisogna renderlo ancora piu' chiaro:

- input di dominio gioco
- output di dominio platform
- nessuna perdita di chiarezza sugli ownership

Esempio:

- esplicitare `platform_round_id`
- rendere piu' leggibile la distinzione tra `game_round_id` e `platform_round_id`

#### Step 3. Ridurre la conoscenza finanziaria esplicita in `mines/service.py`

Il servizio Mines non dovrebbe "ragionare" in termini di dettagli contabili piu' del necessario.

Non significa togliere tutto subito.

Significa:

- confinare sempre di piu' le responsabilita' tramite gateway
- evitare che nuove logiche finanziarie rientrino nel servizio gioco

### 8.3 Cosa NON fare nel primo intervento

- non cambiare il frontend gioco
- non cambiare il contratto client-facing
- non introdurre Beta
- non fare migrazione schema grossa
- non spostare repository

Questo e' il modo con cui si protegge il progetto.

## 9. Secondo intervento raccomandato

Dopo il primo step boundary, il secondo intervento sensato e':

### 9.1 Sul piano backend

- introdurre route platform piu' esplicite per launch token issuance
- mantenendo compatibilita' temporanea con le route esistenti

### 9.2 Sul piano environments

- progettare il Beta deployment
- senza ancora pretendere di portare online tutto

Output atteso:

- checklist infrastrutturale
- env vars
- composizione servizi
- database beta dedicato
- strategia secrets minima

## 10. Strategia ambienti: dettaglio operativo

## 10.1 Local

### Scopo

- coding
- debug
- refactor
- test rapidi

### Requisiti minimi

- Docker Compose locale
- seed o utenti test
- credenziali fake
- log piu' verbosi
- strumenti di inspection

### Cosa e' ammesso

- feature in corso
- wiring transitorio
- branch non ancora pronti per demo

### Cosa non va preso come prova finale

- performance reale
- cookie/same-site reali
- reverse proxy reali
- deploy problems

## 10.2 Beta

### Scopo

- validazione prodotto
- QA end-to-end
- demo condivisibili
- test cross-device e fuori dalla macchina locale

### Requisiti minimi

- dominio o sottodominio beta
- backend deployato
- frontend deployato
- DB dedicato beta
- migrazioni vere
- HTTPS
- login reale beta

### Regole

- niente esperimenti casuali
- dati non di production
- resettable
- smoke test pre-release beta

### Cosa ci si testa

- launch token reale via HTTPS
- access session reale
- login/logout
- route protette
- Mines standalone
- admin base
- round start/reveal/cashout

## 10.3 Production

### Scopo

- rilascio reale

### Requisiti minimi

- backup
- rollback
- segreti separati
- demo mode governato da env/policy
- log appropriati
- monitoring minimo

### Regola

Production non e' il posto dove si scopre se l'architettura regge.

Quella verifica va fatta prima in Beta.

## 11. Piano roadmap raccomandato

## Milestone 1 - Chiarezza del boundary

Output:

- questo blueprint approvato
- glossario ID
- contratto target concordato

No codice pesante.

## Milestone 2 - Boundary hardening minimo

Output:

- gateway piu' esplicito
- service Mines meno accoppiato ai dettagli finanziari
- nessun cambiamento pubblico rompente

Questo e' il primo milestone di codice consigliato.

## Milestone 3 - Launch ownership cleanup

Output:

- route platform piu' esplicite per issue launch token
- compatibilita' transitoria mantenuta

## Milestone 4 - Beta design package

Output:

- documento infrastrutturale beta
- definizione servizi
- env vars richieste
- segreti e database
- procedura di deploy

## Milestone 5 - Beta rollout

Output:

- primo ambiente beta online

## Milestone 6 - Production readiness

Output:

- checklist pre-prod
- hardening token
- smoke test formali

## 12. Rischi principali e mitigazioni

## 12.1 Rischio: refactor simbolico ma non reale

Esempio:

- spostiamo una route
- rinominiamo un file
- ma il servizio gioco resta accoppiato allo stesso modo

Mitigazione:

- ogni step deve dichiarare quale ownership migliora davvero

## 12.2 Rischio: troppo cambiamento pubblico troppo presto

Mitigazione:

- mantenere stabili gli endpoint player-facing nella prima fase

## 12.3 Rischio: fare Beta senza disciplina

Mitigazione:

- Beta solo dopo boundary e smoke flow minimi stabilizzati

## 12.4 Rischio: inseguire test invece di ridurre il coupling

Mitigazione:

- usare i test per proteggere i confini
- non per compensare design ambiguo

## 13. Decisione finale raccomandata

Se l'obiettivo e' fare un lavoro maturo e pulito, la decisione consigliata e' questa:

1. approvare il modello `platform authority / game authority`
2. approvare il contratto target qui descritto
3. iniziare da un primo milestone di hardening interno, non da cambi pubblici o deploy
4. progettare Beta in parallelo, ma deployarla solo dopo aver reso il boundary piu' chiaro

## 14. Checklist per autorizzare il primo sviluppo

Prima di iniziare a scrivere codice sul tema `H/I`, dovremmo poter dire di si' a queste domande:

1. sappiamo quali identificatori appartengono a platform e quali a game?
2. sappiamo quali endpoint restano pubblici e quali sono internal contract?
3. sappiamo quale e' il primo punto del codice che toccheremo?
4. sappiamo quale comportamento pubblico non deve cambiare?
5. sappiamo come verificare che il boundary sia migliorato senza aprire regressioni?

Se la risposta e' si', allora il primo sviluppo puo' partire bene.

## 15. Sintesi brevissima finale

### Oggi

Il progetto ha gia' il seme giusto:

- launch token
- access session
- round gateway
- platform rounds

### Domani

Serve completare il boundary, non rifare tutto.

### Primo step corretto

- chiarire ID e ownership
- rafforzare il gateway
- ridurre l'accoppiamento di `mines/service.py`

### Beta

- va progettata presto
- ma va deployata solo dopo il primo hardening boundary

## 16. Schema finale

```text
LOCAL
  -> build, debug, refactor
  -> nessuna pretesa di realta' esterna completa

BETA
  -> validazione end-to-end reale
  -> HTTPS, dominio, deploy, DB dedicato
  -> test dei boundary veri

PRODUCTION
  -> pubblicazione
  -> policy e hardening maggiori

------------------------------

PLATFORM
  owns:
  - auth
  - wallet
  - ledger
  - settlement
  - admin
  - reporting
  - launch issue
  - access session
  - platform round

GAME
  owns:
  - config
  - board
  - fairness
  - reveal
  - technical round
  - payout result

BOUNDARY
  via:
  - launch token
  - access session
  - rounds/open
  - rounds/settle
```
