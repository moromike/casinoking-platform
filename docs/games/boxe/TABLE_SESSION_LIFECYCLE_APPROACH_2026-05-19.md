Status: ACTIVE
Last meaningful update: 2026-05-19

# BOXE - Table Session Lifecycle Approach

WP: `WP-BOXE-TABLE-SESSION-LIFECYCLE-PARITY` - Parte A, approach validation.

2026-05-23 update: BOXE now participates in platform access-session
close/timeout auto-settlement. If a real-money BOXE round is started and closed
before any safe pick, the reserved bet is refunded. If at least one safe pick
exists, close/timeout performs an automatic cashout using `payout_current`.
The backend timeout sweeper applies the same policy if the browser disappears.
This mirrors the Mines lifecycle invariant and is covered by integration tests.

## 1. Scope Decision

Obiettivo: allineare BOXE real cash e real bonus al lifecycle Mines per table
balance gate, table session, wallet lock/limits e round start.

Parte A non applica modifiche runtime. Questo documento valida l'approccio per
Parte B.

Out of scope confermati:

- nessuna modifica gameplay BOXE;
- nessuna modifica admin BOXE;
- nessuna modifica funzionale Mines;
- nessuna modifica alla platform table session API;
- nessuna modifica al flow demo BOXE.

## 2. Sources Letti

Letti integralmente o nelle sezioni rilevanti:

- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`
- `docs/games/boxe/BOXE_FULL_PARITY_AUDIT_2026-05-19.md`, sezione Table Balance gate e WP raccomandato
- `docs/games/boxe/SPEC.md`, sezione Backend State Machine
- `backend/app/api/routes/boxe.py`
- `backend/app/api/routes/mines.py`
- `backend/app/api/routes/platform_table_sessions.py`
- `backend/app/modules/games/mines/service.py`
- `backend/app/modules/games/mines/round_gateway.py`
- `backend/app/modules/games/mines/platform_client.py`
- `backend/app/modules/games/boxe/service.py`
- `backend/app/modules/games/boxe/repository.py`
- `backend/app/modules/games/boxe/round_gateway.py`
- `backend/app/modules/games/boxe/platform_client.py`
- `backend/app/modules/platform/table_sessions/service.py`
- `backend/app/modules/platform/rounds/service.py`
- `backend/migrations/sql/0039__boxe_session_tables.sql`
- `frontend/app/ui/mines/mines-standalone.tsx`
- `frontend/app/ui/boxe/boxe-standalone.tsx`
- `frontend/app/ui/boxe/boxe-gameplay.tsx`
- `frontend/app/ui/boxe/use-boxe-runtime.ts`

## 3. Current State

### BOXE backend

`/games/boxe/start` oggi accetta:

```json
{
  "title_code": "boxe001",
  "rows": 6,
  "difficulty": "medium",
  "bet_amount": "5",
  "wallet_source": "cash",
  "client_seed": "optional"
}
```

Il service BOXE apre gia' un platform round per wallet non demo tramite
`open_platform_round`, ma non passa `table_session_id` o `access_session_id`.
Di conseguenza la platform layer puo' auto-creare una table session quando
`table_session_id` e' `None`, ma il frontend BOXE non sta usando il table gate
come lifecycle reale.

### BOXE schema

`boxe_sessions` ha gia':

- `access_session_id uuid NULL REFERENCES game_access_sessions(id)`
- `table_session_id uuid NULL REFERENCES game_table_sessions(id)`

`platform_rounds` ha gia' `access_session_id` e `table_session_id`.

`boxe_rounds` non ha un FK diretto a `game_table_sessions`; il legame e'
indiretto e coerente col modello attuale:

```text
boxe_rounds.platform_round_id -> platform_rounds.id -> platform_rounds.table_session_id
boxe_rounds.session_id -> boxe_sessions.id -> boxe_sessions.table_session_id
```

Conclusione: non serve migration per il requisito attuale. Una migration avrebbe
senso solo se il CTO chiedesse denormalizzazione esplicita
`boxe_rounds.table_session_id`, ma non e' necessaria per lifecycle parity.

### BOXE adapter

`backend/app/modules/games/boxe/platform_client.py` supporta gia' parametri
opzionali:

- `table_session_id`
- `access_session_id`

e li inoltra a `open_game_round`. La platform layer applica gia':

- validazione owner/user;
- game/title/site/wallet match;
- stato active;
- table balance sufficiente;
- `loss_reserved_amount`;
- `loss_consumed_amount`;
- release/consume sul settle.

La lacuna principale e' nel service/endpoint BOXE, non nel platform client.

### BOXE frontend

`BoxeStandalone` usa `GameTableBalanceGate`, ma `onConfirm` oggi salva solo
wallet/amount e chiama `setIsTableBalanceComplete(true)`.

Mines invece:

- carica `/table-sessions/limits`;
- crea/riusa `access_session`;
- POST `/table-sessions`;
- salva `tableSession`;
- passa `table_session_id` e `access_session_id` a `/games/mines/start`.

## 4. Payload Shape Proposto

Estensione additiva di `/games/boxe/start`:

```json
{
  "title_code": "boxe001",
  "rows": 6,
  "difficulty": "medium",
  "bet_amount": "5",
  "wallet_source": "cash",
  "client_seed": "boxe-ui:<idempotency-key>",
  "table_session_id": "uuid-optional",
  "access_session_id": "uuid-optional"
}
```

Pydantic:

```python
class StartRoundRequest(BaseModel):
    title_code: str
    rows: int
    difficulty: str
    bet_amount: str
    wallet_source: str
    client_seed: str | None = None
    table_session_id: str | None = None
    access_session_id: str | None = None
```

Service signature:

```python
def start_round(
    *,
    player_id: str,
    title_code: str,
    rows: int,
    difficulty: str,
    bet_amount: str,
    wallet_source: str,
    client_seed: str | None,
    idempotency_key: str,
    table_session_id: str | None = None,
    access_session_id: str | None = None,
) -> IdempotentResult:
```

Response consigliata, additiva:

```json
{
  "session_id": "uuid",
  "round_id": "uuid",
  "multipliers": ["1.08", "1.24"],
  "status": "active",
  "server_seed_hash": "...",
  "table_session_id": "uuid-or-null",
  "table_session": {}
}
```

`table_session` serve al frontend come Mines per aggiornare saldo tavolo dopo
la riserva della puntata. Per demo puo' restare assente/null.

## 5. Validation Decision

Raccomandazione CTO:

- `wallet_source == "demo"`: `table_session_id` e `access_session_id` non richiesti.
- `wallet_source in {"cash", "bonus"}`: `table_session_id` richiesto per BOXE.
- `access_session_id`: opzionale a livello schema/payload, ma il frontend BOXE
  deve passarlo quando crea la table session, come Mines.
- Se `access_session_id` e' presente, validarlo con
  `ensure_access_session_active_for_round_start`, come Mines.

Nota critica: Mines backend oggi accetta `table_session_id=None` e la platform
layer crea una sessione tavolo implicita. La UX Mines rende comunque il gate
hard prima dello start. Se per BOXE aggiungiamo il reject backend in real mode,
otteniamo un invariant piu' esplicito di Mines senza cambiare Mines. Questo e'
coerente con i test richiesti dal WP, ma va considerato una scelta deliberata
di hardening BOXE.

Error mapping consigliato:

- real start senza `table_session_id`: `422 VALIDATION_ERROR`
- table session non trovata o non owner: mapping esistente da
  `BoxePlatformValidationError`, idealmente `422` oppure `404` solo se si
  espone errore typed dedicato;
- saldo tavolo insufficiente: `409 TABLE_LIMIT_EXCEEDED` se si introduce mapping
  specifico, altrimenti `422 VALIDATION_ERROR` come oggi via adapter.

Per Parte B minima, non serve creare nuovi codici errore se il frontend tratta
il messaggio come failure start. Per parita' prodotto piu' pulita, conviene
mappare `TableSessionLimitExceededError` a codice dedicato nel boundary BOXE.

## 6. State Machine Integration

Flow real cash/bonus proposto:

```text
Player enters BOXE real launch
        |
        v
GameTableBalanceGate
        |
        | POST /access-sessions
        |   game_code=boxe
        |   title_code=boxe001
        |   site_code=casinoking
        |
        | POST /table-sessions
        |   game_code=boxe
        |   title_code=boxe001
        |   site_code=casinoking
        |   wallet_type=cash|bonus
        |   table_budget_amount=<amount>
        |   access_session_id=<id>
        v
BOXE gameplay unlocked
        |
        | POST /games/boxe/start
        |   wallet_source=cash|bonus
        |   access_session_id=<id>
        |   table_session_id=<id>
        v
boxe.service.start_round
        |
        | validate launch/title/config/wallet
        | validate required table_session_id for real
        | validate access_session_id if present
        v
boxe.platform_client.open_round
        |
        | platform.rounds.open_game_round
        |   validate_and_reserve_round_exposure
        |   debit wallet
        |   insert ledger bet
        v
repository.create_session
        | access_session_id=<id>
        | table_session_id=<id>
        v
repository.create_platform_round
        | access_session_id=<id>
        | table_session_id=<id>
        v
repository.create_round
        | platform_round_id=<round_id>
        v
BOXE round active
```

Flow demo invariato:

```text
BOXE demo start -> wallet_source=demo -> no /table-sessions -> no platform round
```

## 7. Game Adapter Modifiche Scope

### `backend/app/modules/games/boxe/platform_client.py`

Modifiche minime:

- nessuna firma nuova obbligatoria: `open_round` accetta gia'
  `table_session_id` e `access_session_id`;
- valutare solo mapping errori piu' specifico per table limits, se il frontend
  deve distinguere limite tavolo da validazione generica.

### `backend/app/modules/games/boxe/round_gateway.py`

Modifiche minime:

- nessuna modifica strutturale richiesta: re-exporta gia' `open_round`.

### `backend/app/modules/games/boxe/service.py`

Modifiche richieste:

- accettare `table_session_id` e `access_session_id`;
- includerli nel fingerprint idempotente di start;
- richiedere `table_session_id` per `cash`/`bonus`;
- passare entrambi a `open_platform_round`;
- passare `access_session_id` a `repository.create_session`;
- passare `access_session_id` a `repository.create_platform_round`;
- includere `table_session_id/table_session` nella response start quando
  disponibile.

### `backend/app/api/routes/boxe.py`

Modifiche richieste:

- estendere `StartRoundRequest`;
- validare `access_session_id` se presente, usando lo stesso service platform
  usato da Mines;
- inoltrare entrambi i campi al service.

## 8. Frontend Approach

BOXE puo' replicare il pattern Mines quasi 1:1, ma non basta sostituire solo
`/games/mines/start` con `/games/boxe/start`: BOXE deve anche conservare e
passare `tableSession` e `accessSessionId` dentro `BoxeGameplay`/runtime API.

Modifiche attese:

- `BoxeStandalone` carica `/table-sessions/limits?wallet_type=<cash|bonus>`
  invece dei valori hardcoded `100 CHIP`;
- `handleConfirmTableBalance` crea/riusa access session BOXE;
- `handleConfirmTableBalance` crea table session con:
  - `game_code: "boxe"`
  - `title_code: bootStatus.request.titleCode`
  - `site_code: "casinoking"`
  - `wallet_type: walletSource`
  - `table_budget_amount`
  - `access_session_id`
- `BoxeStandalone` passa `tableSession` e `accessSessionId` a `BoxeGameplay`;
- `startBoxeRound` invia `table_session_id` e `access_session_id` nel body;
- dopo start, se response contiene `table_session`, aggiornare lo stato locale.

Vincolo: nessuna modifica a layout/board/gameplay visuale. Sono solo props,
runtime state e API payload.

## 9. Lifecycle Limits

BOXE usa gli stessi tipi di limits di Mines perche' la platform table session e'
game-agnostic:

- `TABLE_SESSION_MAX_CHIPS = 100.000000`
- `table_budget_amount`
- `table_balance_amount`
- `loss_limit_amount`
- `loss_reserved_amount`
- `loss_consumed_amount`
- `loss_remaining_amount`
- wallet type `cash|bonus`

Non servono campi nuovi per BOXE. Il mapping BOXE verso `open_game_round` usa:

- `grid_size = rows`
- `mine_count = DIFFICULTY_RISK_INDEX[difficulty]`

Questo mapping esiste gia' ed e' sufficiente per metadata/ledger; non cambia la
matematica BOXE.

## 10. Test Coverage Plan

Test backend integration consigliati:

1. Real cash BOXE start con `table_session_id`
   - crea `game_table_sessions`;
   - chiama `/games/boxe/start`;
   - verifica `boxe_sessions.table_session_id`;
   - verifica `boxe_sessions.access_session_id` se passato;
   - verifica `platform_rounds.table_session_id`;
   - verifica `boxe_rounds.platform_round_id`;
   - verifica decremento `table_balance_amount` e incremento
     `loss_reserved_amount`.

2. Real bonus BOXE start con `table_session_id`
   - stesso controllo con wallet `bonus`;
   - verifica wallet type match.

3. Real BOXE start senza `table_session_id`
   - atteso `422 VALIDATION_ERROR`;
   - nessun `boxe_sessions`, `boxe_rounds`, `platform_rounds`, ledger bet creato.

4. Demo BOXE start senza `table_session_id`
   - atteso successo;
   - nessun `platform_rounds`;
   - `boxe_sessions.table_session_id IS NULL`.

5. Table session mismatch
   - table session `mines` usata su BOXE: reject;
   - table session `cash` usata con `wallet_source=bonus`: reject.

Regression gate Mines:

- test esistenti/manual smoke Mines invariati;
- nessuna modifica a `backend/app/modules/games/mines/*`;
- nessuna modifica a platform table session API.

Nota: oggi `backend/tests` contiene solo `unit/test_boxe_math.py`; Parte B dovra'
aggiungere struttura integration se non esiste harness gia' pronto in CI.

## 11. Stop-and-Ask Attesi

Stop-and-Ask obbligatori:

- Se si scopre che CI/test harness non supporta integration DB per table
  sessions senza nuovo setup.
- Se il CTO vuole FK diretto `boxe_rounds.table_session_id` invece del legame
  via `boxe_sessions`/`platform_rounds`.
- Se il product owner vuole backend BOXE permissivo come Mines service attuale
  invece di reject real senza `table_session_id`.
- Se la platform table session API dovesse richiedere estensione: out of scope,
  fermarsi.
- Se BOXE richiede `X-Game-Launch-Token` parity completa con Mines nello stesso
  WP: e' correlato ma piu' ampio del table session lifecycle.
- Se `access_session_id` deve diventare obbligatorio backend per real mode:
  oggi si propone opzionale ma passato dal frontend.

## 12. Effort Stimato Finale

Parte A: completabile in 1-2 prompt.

Parte B stimata: 4-6 prompt confermati, con questa distribuzione:

- backend payload/service propagation: 1 prompt;
- frontend table session lifecycle BOXE: 1-2 prompt;
- integration tests: 1-2 prompt;
- regression/doc finalization: 1 prompt.

Il rischio principale non e' il platform adapter: e' il wiring frontend BOXE,
perche' oggi `BoxeStandalone` non conserva una table session reale e
`BoxeGameplay` non riceve il contesto tavolo.

## 13. Recommendation

Approccio approvabile per Parte B:

1. non migrare schema;
2. non toccare platform table session API;
3. usare `boxe_sessions.table_session_id` e `platform_rounds.table_session_id`
   come fonte relazionale;
4. rendere `table_session_id` obbligatorio per BOXE `cash|bonus`;
5. mantenere `access_session_id` opzionale nel contratto ma sempre passato dal
   frontend reale;
6. mantenere demo invariato.

Parte B non va iniziata prima di OK CTO.

## Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Stato | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| `table_session_id` propagation | Usa FK esistenti su `boxe_sessions.table_session_id` e `platform_rounds.table_session_id`; nessuna migration | `start_round` passa `table_session_id` al platform adapter e salva il legame BOXE | `/games/boxe/start` accetta `table_session_id` additivo | N/A | `BoxeGameplay` invia il table session reale per cash/bonus | N/A | Integration cash start verifica session, platform round e saldo tavolo | Questa sezione | Completa | Nessuna FK diretta aggiunta a `boxe_rounds`; la relazione resta via session/platform round |
| `access_session_id` validation | Usa FK esistente su `boxe_sessions.access_session_id` e `platform_rounds.access_session_id` | Route valida access session attiva prima dello start; service persiste l'id | `/games/boxe/start` accetta `access_session_id` additivo e opzionale | N/A | `BoxeStandalone` crea access session prima della table session reale | N/A | Integration cash/bonus verifica propagation; mismatch copre reject table/wallet | Questa sezione | Completa | Demo non richiede access session |
| `table_session` response field | Nessun cambio schema | Response start include snapshot table session da platform adapter | Response additiva: `table_session_id`, `table_session` | N/A | Runtime aggiorna lo stato tavolo dalla response dopo BET | N/A | Integration cash start verifica importi riservati e rimanenti | Questa sezione | Completa | Campo nullable in demo per compatibilita' |
| Real cash lifecycle parity | Table session decrementa `table_balance_amount` e incrementa `loss_reserved_amount` | BOXE real cash usa adapter platform con table session | Cash start senza `table_session_id` viene rigettato | N/A | Gate tavolo crea sessione e start usa wallet cash bloccato | N/A | Test cash start e reject missing table | Questa sezione | Completa | Strict mode BOXE: real play deve passare dal gate |
| Real bonus lifecycle parity | Table session bonus usa wallet type bonus e riserva separata | Service normalizza e propaga `wallet_source=bonus` | Bonus start richiede table session bonus coerente | N/A | Gate tavolo supporta wallet bonus quando selezionato | N/A | Test bonus start e wallet mismatch | Questa sezione | Completa | Mismatch cash table + bonus wallet resta `VALIDATION_ERROR` |
| Demo flow unchanged | Nessun `platform_rounds`; `boxe_sessions.table_session_id` resta NULL | Demo bypassa adapter platform come prima | Demo start non richiede table/access session e restituisce null | N/A | Demo continua senza gate table session reale | N/A | Test demo start senza platform round | Questa sezione | Completa | Mantiene backward compatibility e idempotenza demo |
| Mines lifecycle unchanged | Nessun file/schema Mines toccato | Nessuna modifica a service/route Mines o platform table session API | Nessun contratto Mines modificato | N/A | Nessun wiring Mines toccato | N/A | Gate diff fuori scope atteso empty su path mines/title-editor | Questa sezione | Completa | WP-C e' BOXE-only piu' docs |
| Table session limit error mapping | Nessun cambio DB | Errori platform table-session restano gestiti dal layer platform chiamato dal service | Eventuali errori di limite arrivano come errore API coerente del platform adapter | N/A | `BoxeStandalone` mostra errore runtime se limits/create table fallisce | N/A | Coperto indirettamente da mismatch/reject; test dedicato non aggiunto | Questa sezione | Completa | `TableSessionLimitExceededError` non richiede mapping custom in route BOXE per questo WP |
