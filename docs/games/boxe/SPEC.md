Status: ACTIVE
Last meaningful update: 2026-05-18

# BOXE - SPEC

Contratto Fase 0 per il gioco proprietario BOXE.

Questo documento e' l'output di WP-BOXE-FASE-0 secondo
`docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` sezione 5. E' autosufficiente per
guidare Fase 1 e le fasi di implementazione successive.

## 0. Scope, Fonti E Stato

### 0.1 Stato

| Campo | Valore |
| --- | --- |
| WP | `WP-BOXE-FASE-0` |
| Branch | `feature/boxe-fase-0-spec` |
| Tipo | Documentation-only SPEC |
| Codice produzione | Non toccato |
| Architettura | Nessuna modifica |
| Stato consegna atteso | Branch pushato, non mergeato, in attesa gate CTO |

### 0.2 Fonti Lette

| Fonte | Uso nello SPEC |
| --- | --- |
| `docs/games/boxe/BOXE_BRIEF.md` | Brief compilato e decisioni product vincolanti. |
| `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` | Metodologia, 11 blocchi obbligatori, capability matrix. |
| `docs/NEW_GAME_BRIEF_TEMPLATE.md` | Template da cui deriva il brief. |
| `docs/TASK_EXECUTION_GUARDRAILS.md` | Guardrail, implementation log, capability matrix. |
| `docs/CAPABILITY_INVENTORY_2026-05-17.md` | Capability platform riusabili e loro stato. |
| `docs/ARCHITECTURE_ATLAS_MINES.md` | Gioco riferimento, pattern da riusare senza copiare. |
| `docs/SESSION_RECOVERY_ENGINE_DESIGN.md` | Policy recovery, in particolare scenario #2. |
| `docs/BOOT_2A_BRANCH_AUDIT_2026-05-17.md` | Stato stabile shell game-runtime. |
| `assets/Games/boxe/BOXE - DOCUMENTO DI DESIGN FUNZIONALE.docx` | Analisi funzionale originale, estratta da `word/document.xml`. |
| `assets/Games/boxe/boxe1 splash.png` | Splash/how-to-play reference. |
| `assets/Games/boxe/boxe2 stato idle base .png` | Idle layout reference. |
| `assets/Games/boxe/boxe4.png` | Compact/alternate configuration reference. |
| `assets/Games/boxe/boxe5.png` | Active pick positive reference. |
| `assets/Games/boxe/boxe6.png` | Mid/advanced progress reference. |
| `assets/Games/boxe/boxe7.png` | Negative pick / game-over reveal reference. |
| `docs/MINES_PENDING_TOPICS.md` | Previous-game residual lessons and max-win cap note. |

### 0.3 Non Fonti Primarie

| Fonte | Stato |
| --- | --- |
| `AGENTS.md` | Non usato come fonte primaria, come da guardrail. |
| `docs/BOXE_PROJECT_BRIEF.md` | Documento legacy/untracked individuato, non usato come source of truth. |
| Ricerca esterna Hacksaw | Non eseguita. La matematica non viene inventata da fonti esterne. |

### 0.4 Decisioni Product Gia' Prese

| Decisione | Valore SPEC |
| --- | --- |
| Game code | `boxe` |
| Game family | `boxe` |
| Prima variante | `boxe001` |
| Demo | Abilitata |
| Real | Abilitata |
| Bonus wallet | Supportato |
| Lingue lancio | `it`, `en`, `de`, `es` |
| Lingua default | `it` |
| Bet range | Pattern Mines: no min/max hardcoded in v1, solo balance check |
| Bet UX | Input libero v1; frecce +/- deferred |
| Max win cap | `null` v1; parametro previsto per WP futuro |
| Bonus rounds/free spins | No |
| Game-over reveal | Solo riga corrente |
| Recovery disconnect | Session Recovery scenario #2 auto-cashout se multiplier > 1 |
| Theme | Pattern Mines base; advanced skin deferred |
| Shell platform | Tutto default; nessun override |
| Nome display | `BOXE`, reversibile in futuro |

### 0.5 Open Questions Chiuse In Questa SPEC

| Open question | Decisione SPEC | Stato |
| --- | --- | --- |
| Provably fair UI visibile player? | No in v1; admin/dev verification e fairness data server-side. Player UI differita. | Chiuso |
| Top row auto-collect feedback? | Auto-collect immediato con stato `completed_top_row`, messaggio breve e animazione win dedicata. | Chiuso |
| Balance < bet behavior? | Errore esplicito/disabled BET; nessun auto-adjust silente. | Chiuso |
| Max win cap concreto? | `null` v1; campo/config previsto, non applicato finche' WP cap non esiste. | Deferred motivato |
| Bet UX input libero vs frecce? | Input libero v1, frecce +/- deferred. | Chiuso |
| Naming `BOXE` reversibile? | Reversibile a livello display/title; `game_code=boxe` stabile. | Chiuso |
| Skin advanced MSK V2? | Out of scope v1; theme tokens base. | Deferred motivato |

### 0.6 Stop-And-Ask Register

| Tema | Esito |
| --- | --- |
| Platform shell extension | Non necessaria; tutto default. |
| Gap platform bloccante | Nessuno trovato per Fase 0. |
| Math completa | La tabella/formula completa non e' nel brief/docx; Fase 2A non puo' inventarla. |
| Contraddizioni brief vs docx | Nessuna contraddizione bloccante; il brief prevale dove ha gia' deciso. |

### 0.7 Capability Matrix Del WP

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE Phase 0 SPEC | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NEW | COMPLETE | Doc methodology and game-specific contract, no production code touched, no architecture changes. |
| BOXE brief implementation log | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | COMPLETE | First Implementation Log entry added to `BOXE_BRIEF.md`. |
| Docs index | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | COMPLETE | `docs/README.md` indexes this SPEC as ACTIVE. |

## 1. Game Rules

### 1.1 Closure Criterion

Every outcome and payout must be deterministic from server state.

### 1.2 Core Identity

| Campo | Valore |
| --- | --- |
| Display name v1 | `BOXE` |
| Game code | `boxe` |
| Game family | `boxe` |
| First title variant | `boxe001` |
| Route | `/boxe?title_code=<title_code>` |
| Core loop | Bet, pick row by row, collect or lose |
| Genre | Tower/Mines style pyramid push-your-luck |

### 1.3 Player Objective

The player places one bet before the round starts.

The player picks one box in the active row.

If the selected box contains a diamond:

| Result | Effect |
| --- | --- |
| Safe pick | Player advances to the next row. |
| Multiplier | Current multiplier advances to the row reached. |
| Collectability | Player may collect the current win. |
| Next action | Pick next row or collect. |

If the selected box contains a mine:

| Result | Effect |
| --- | --- |
| Mine pick | Round ends as loss. |
| Payout | Zero win for that round. |
| Reveal | Only current row is revealed. |
| Upper rows | Remain unrevealed. |

If the player successfully clears the top row:

| Result | Effect |
| --- | --- |
| Top row safe | Round auto-collects immediately. |
| State | `completed_top_row`. |
| Payout | Bet multiplied by top multiplier for config. |
| Further input | No further pick or manual collect. |

### 1.4 Configurable Round Parameters

| Parameter | Values | Owner | Timing |
| --- | --- | --- | --- |
| `rows` | `4`, `5`, `6`, `7`, `8` | Title Editor | Chosen pre-round |
| `difficulty` | `EASY`, `MEDIUM`, `HARD` | Title Editor / player selection if enabled by UI | Chosen pre-round |
| `bet_amount` | Positive chip/currency amount allowed by table/session balance | Player | Chosen pre-round |
| `wallet_source` | `cash`, `bonus`, demo wallet | Platform launch/table session | Chosen before gameplay |
| `max_win_cap` | `null` in v1 | Future config | Not enforced v1 |

### 1.5 Hardcoded Game Rules

| Rule | Value |
| --- | --- |
| Free picks after bet | Yes |
| Additional charge per pick | No |
| Bonus rounds | No |
| Free spins | No |
| Progressive jackpot | No |
| Frontend outcome authority | No |
| Backend outcome authority | Yes |

### 1.6 RNG Model

BOXE uses server-authoritative deterministic RNG.

| Artifact | Requirement |
| --- | --- |
| Server seed | Generated/stored server-side. |
| Client seed | Accepted or generated according to platform fairness pattern. |
| Nonce | Monotonic per round/session as needed. |
| Board generation | Deterministic from seed material and round config. |
| Hidden state | Never exposed while round is active. |
| Final state | Exposed only as needed for replay after closure. |

Implementation must follow the Mines fairness pattern conceptually, without
copying Mines game mechanics.

### 1.7 Board Model

The board is a pyramid of rows.

| Concept | Requirement |
| --- | --- |
| Row order | Bottom to top. |
| Active row | Only one row is interactable at a time. |
| Pick count per row | Exactly one pick. |
| Row contents | One or more diamonds and one or more mines depending on config. |
| Unpicked future rows | Hidden until reached; not revealed on loss. |
| Loss reveal | Current row only. |

### 1.8 Difficulty Semantics

Difficulty changes the risk/reward profile.

| Difficulty | Meaning |
| --- | --- |
| `EASY` | Fewer mines per row, lower multipliers. |
| `MEDIUM` | Intermediate mines/multipliers. |
| `HARD` | More mines per row, higher multipliers. |

The exact mine-count-per-row and multiplier table must be defined in Fase 2A
from a product-approved math source.

### 1.9 Payout Contract

| Item | Contract |
| --- | --- |
| Payout basis | Initial bet multiplied by current row multiplier. |
| Payout owner | Backend math module. |
| Frontend role | Display only. |
| Collect timing | Any safe state with multiplier > 1, except top row auto-collect. |
| Loss payout | Zero. |
| Top row payout | Top multiplier for selected `rows x difficulty`. |
| RTP target | 98%, to be validated by math tests/simulation. |

### 1.10 Observed Math Anchors

These anchors are requirements to reconcile, not a complete payout table.

| Configuration | Observed value |
| --- | --- |
| 4 rows / EASY first multiplier | `1.37x` |
| 4 rows / HARD first multiplier | `2.94x` |
| 4 rows / HARD max multiplier | `36.58x` |
| 8 rows / EASY first multiplier | `1.76x` |
| 8 rows / EASY max multiplier | `9.87x` |
| 8 rows / HARD max multiplier | `548.80x` |
| RTP target | `98%` |

### 1.11 Math Gap Guardrail

The complete multiplier table/formula is not present in the brief or extracted
`.docx`.

Fase 2A must not approximate or scrape external rules ad hoc. It must receive
one of:

| Accepted input | Requirement |
| --- | --- |
| Product-approved multiplier table | Complete for all rows/difficulty/steps. |
| Product-approved formula | Generates all multipliers and matches observed anchors. |
| Product-approved deviation | Explicitly states BOXE differs from Hacksaw anchors. |

Without one accepted input, Fase 2A is blocked.

### 1.12 Max Win Cap

| Field | Value |
| --- | --- |
| v1 behavior | No enforced cap. |
| Config value | `null`. |
| Future field | `max_win_cap`. |
| Future source | Dedicated WP after platform cap design. |
| Hacksaw reference | EUR 1,000,000 cap mentioned in docx, not adopted in v1. |

## 2. Visual Layout

### 2.1 Closure Criterion

Every visible state has a named layout.

### 2.2 Visual Principles

| Principle | Requirement |
| --- | --- |
| Focus | Central pyramid is primary. |
| Density | Compact casino-game runtime, not landing page. |
| Responsiveness | Desktop, portrait mobile, short-landscape gate through platform shell. |
| State clarity | Active row, safe picks, mine hit, collectable amount must be clear. |
| Theme | Use platform theme tokens v1; no advanced skin. |

### 2.3 Required Layout Regions

| Region | Position | Contents |
| --- | --- | --- |
| Payout display | Top center | Step multipliers, current step highlight, next mines indicator. |
| Settings | Top/side compact area | Rows and difficulty selectors before round. |
| Pyramid | Center | Boxes arranged bottom-to-top. |
| Player panel | Lower/side area | Balance, bet, primary action. |
| Runtime tools | Existing shell/runtime area | Info, history/replay, sound/FX controls. |
| Overlay gates | Platform shell | Provider intro, how-to-play, table balance gate. |

### 2.4 State: Provider Intro

| Item | Requirement |
| --- | --- |
| Owner | Platform game-runtime. |
| Content | Default `moromike lab` intro. |
| BOXE override | None. |
| Close behavior | Existing shell behavior. |

### 2.5 State: How-To-Play Gate

BOXE uses game-specific content inside the default gate.

| Step | Copy concept |
| --- | --- |
| Bet | Choose rows, difficulty and bet amount. |
| Pick | Pick one box per active row and look for diamonds. |
| Collect | Collect a safe multiplier before a mine ends the round. |

The splash reference is `boxe1 splash.png`.

### 2.6 State: Idle

| Element | Requirement |
| --- | --- |
| Pyramid | Covered boxes, no revealed content. |
| Active row | None. |
| Settings | Editable. |
| Bet input | Editable. |
| Primary button | `BET`. |
| Collect amount | Hidden or zero state. |
| Payout display | Shows configured multiplier path. |

### 2.7 State: Round Starting

| Element | Requirement |
| --- | --- |
| Primary button | Busy/disabled. |
| Settings | Locked. |
| Bet input | Locked. |
| Pyramid | Waiting for backend active state. |
| Failure | If start fails, return to idle with explicit error. |

### 2.8 State: Active Row

| Element | Requirement |
| --- | --- |
| Active row | Only active row clickable. |
| Previous safe rows | Show selected diamonds. |
| Future rows | Covered and disabled. |
| Primary button | `COLLECT <amount>` when multiplier > 1. |
| Payout display | Highlights current multiplier and next step. |

### 2.9 State: Safe Pick

| Element | Requirement |
| --- | --- |
| Picked box | Reveal diamond. |
| Animation | Box flip/3D rotation if feasible in Fase 3C. |
| Payout pill | Slides to reached multiplier. |
| Next row | Becomes active after backend response. |
| Collect amount | Updates from backend payout. |

### 2.10 State: Mine Hit

| Element | Requirement |
| --- | --- |
| Picked box | Reveal mine. |
| Animation | Red explosion/pulse. |
| Current row unpicked boxes | Reveal partially/opaque to show row contents. |
| Upper rows | Remain hidden. |
| Primary button | Return to `BET` after resolution/reset. |
| Outcome label | Loss/game-over state. |

### 2.11 State: Manual Collect

| Element | Requirement |
| --- | --- |
| Trigger | Player clicks `COLLECT`. |
| Primary button | Busy/disabled while request is pending. |
| Outcome | Win/cashout celebration. |
| Pyramid | Final safe picks remain visible for round summary. |
| Ledger | Settlement through platform only. |

### 2.12 State: Top Row Auto-Collect

This closes open question #2.

| Element | Requirement |
| --- | --- |
| Trigger | Safe pick on the final/top row. |
| Backend state | `completed_top_row`. |
| User action | No extra click. |
| Message | Short win/completion copy, locale-backed. |
| Animation | Final diamond reveal plus win celebration. |
| Button | Disabled during settlement, then returns to `BET`. |

### 2.13 State: Replay

| Element | Requirement |
| --- | --- |
| Mode | Read-only. |
| Board | Reconstruct pyramid at final state. |
| Safe picks | Show selected safe path. |
| Loss row | If loss, show current row reveal only. |
| Future rows | Remain hidden if never reached. |
| Outcome | Show cashout/top-row/loss/expired/recovery. |

### 2.14 Animations V1/VDeferred

| Animation | v1 requirement | Deferred |
| --- | --- | --- |
| Row count change | Smooth resize/fade if feasible. | Advanced choreography. |
| Diamond reveal | Required feedback. | Rich 3D polish. |
| Mine explosion | Required feedback. | Advanced particle system. |
| Payout pill slide | Required or simple highlight fallback. | Complex timeline. |
| Top row win | Required message + celebration. | Custom cinematic. |

### 2.15 Visual Reference Mapping

| Screenshot | Meaning |
| --- | --- |
| `boxe1 splash.png` | How-to-play splash / three-step tutorial. |
| `boxe2 stato idle base .png` | Base idle layout. |
| `boxe4.png` | Alternate compact configuration. |
| `boxe5.png` | Positive pick and collectable state. |
| `boxe6.png` | Progression with multiple safe rows. |
| `boxe7.png` | Mine hit and current row reveal. |

## 3. Operator Settings

### 3.1 Closure Criterion

Every setting has owner, default, validation, and publish behavior.

### 3.2 Settings Table

| Setting | Owner | Default | Validation | Draft/live |
| --- | --- | --- | --- | --- |
| `rows_enabled` | Operator | `[4,5,6,7,8]` | Subset of allowed rows, non-empty | Draft -> publish |
| `default_rows` | Operator | `8` | Must be enabled row | Draft -> publish |
| `difficulty_enabled` | Operator | `[EASY,MEDIUM,HARD]` | Subset non-empty | Draft -> publish |
| `default_difficulty` | Operator | `EASY` | Must be enabled difficulty | Draft -> publish |
| `rtp_label` | Hardcoded/math | `98%` | Must match math contract | Code/math release |
| `multiplier_table` | Math module | TBD Fase 2A | Complete and tested | Code/math release |
| `max_win_cap` | Future operator/platform | `null` | Deferred | Future WP |
| Copy/rules | Operator/content | Locale defaults | Required locale coverage | Draft -> publish |
| Theme tokens | Operator | Platform/Mines pattern base | Token allowlist | Draft -> publish |
| Assets | Operator | Default/lobby assets | Asset contract section 10 | Draft/live asset registry |

### 3.3 Player-Selectable Pre-Round Values

The player may select only values exposed by live config.

| Player value | Source |
| --- | --- |
| Rows | Live `rows_enabled`. |
| Difficulty | Live `difficulty_enabled`. |
| Bet | Table session/balance constraints. |
| Wallet source | Launch Cashier / Table Balance Gate. |

### 3.4 Hardcoded / Not Operator-Owned

| Item | Reason |
| --- | --- |
| Outcome generation | Core RNG/fairness. |
| Payout calculation | Core math, testable. |
| Settlement | Platform adapter/wallet-ledger. |
| Game code | Stable route/db integration. |
| Shell gates | Platform common runtime. |

### 3.5 Deferred Operator Features

| Feature | Decision |
| --- | --- |
| Bet arrows +/- | Deferred; input libero v1. |
| Advanced skin MSK V2 controls | Deferred for BOXE v1. |
| Music/BGM upload | Deferred unless Fase 1 classifies sounds as required. |
| Max win cap value | Deferred until platform cap WP. |

## 4. Product Constraints

### 4.1 Closure Criterion

No launch mode or language ambiguity remains.

### 4.2 Launch Modes

| Mode | Required | Notes |
| --- | --- | --- |
| Demo | Yes | Anonymous demo wallet, no real ledger/platform rounds if platform pattern requires isolation. |
| Real cash | Yes | Uses platform table session and wallet/ledger adapter. |
| Bonus | Yes | Separate wallet source, must be tested separately. |
| Preview admin | Yes | Same concept as Mines preview, if platform supports title preview. |

### 4.3 Languages

| Field | Value |
| --- | --- |
| Supported locales | `it`, `en`, `de`, `es` |
| Default | `it` |
| Fallback | `it` |
| Runtime selector | None in v1 |
| Backoffice editor | Reuse title locale pattern |

### 4.4 Asset Source Policy

| Asset type | v1 source |
| --- | --- |
| Lobby card | Asset registry upload, initial prepared source exists. |
| Board diamond | Asset registry or default source from prepared asset. |
| Board mine | Asset registry or default source from prepared asset. |
| Theme | Tokens, not raw CSS. |
| Sounds | Reuse platform/title sound asset pattern if enabled in Fase 4B. |

Raw files under `assets/Games/boxe/` are working/source material, not runtime
product assets until imported through the asset registry or a declared pipeline.

### 4.5 Naming Reversibility

This closes open question #6.

| Layer | Decision |
| --- | --- |
| `game_code` | Stable `boxe`; not renamed casually. |
| Display name | `BOXE` v1, can be changed by title metadata later. |
| Title variant | `boxe001` v1, stable once seeded. |
| Marketing name | Reversible through title/site metadata. |

## 5. Backend State Machine

### 5.1 Closure Criterion

All mutations map to a state transition or explicit rejection.

### 5.2 States

| State | Meaning | Terminal |
| --- | --- | --- |
| `created` | Round row exists or is being initialized, no pick accepted yet. | No |
| `active` | Round has debited/started and awaits pick or collect. | No |
| `row_revealed` | Last action safe; current multiplier advanced. | No |
| `cashout_pending` | Cashout settlement in progress. | No |
| `completed_cashout` | Player manually collected. | Yes |
| `completed_top_row` | Final row safe, auto-collect settled. | Yes |
| `failed_mine` | Player selected a mine. | Yes |
| `expired` | Round ended by timeout/recovery policy. | Yes |
| `quarantined` | Future recovery/admin review state for unresolved inconsistency. | Yes until manual action |

### 5.3 Legal Transitions

| From | Event | To |
| --- | --- | --- |
| none | `start_round` | `created` |
| `created` | platform open success | `active` |
| `active` | safe pick non-top row | `row_revealed` |
| `row_revealed` | safe pick non-top row | `row_revealed` |
| `active` | mine pick | `failed_mine` |
| `row_revealed` | mine pick | `failed_mine` |
| `row_revealed` | manual collect | `cashout_pending` |
| `cashout_pending` | settlement success | `completed_cashout` |
| `active` or `row_revealed` | safe pick top row | `completed_top_row` |
| `active` or `row_revealed` | recovery auto-cashout | `completed_cashout` |
| `active` with zero safe picks | recovery refund future policy | `expired` or future refund terminal |
| any non-terminal | irrecoverable inconsistency | `quarantined` |

### 5.4 Illegal Transitions

| Attempt | Required result |
| --- | --- |
| Pick before start | Reject. |
| Pick future row before current row | Reject. |
| Pick previous completed row again with different key | Reject or return idempotent result if same key. |
| Manual collect before any safe pick | Reject. |
| Manual collect after mine | Return terminal loss state, no payout. |
| Manual collect after top row | Return terminal top-row state, no duplicate credit. |
| Start second active round for same table/session if one active exists | Reject or resume existing according to platform policy. |
| Change rows/difficulty mid-round | Reject. |
| Reveal after terminal state | Return terminal state for idempotent retry, otherwise explicit closed-round error. |

### 5.5 Concurrency

| Race | Required behavior |
| --- | --- |
| Two reveals same row | Per-round lock; first mutation wins. |
| Same reveal retry same idempotency key | Same response. |
| Reveal vs cashout | Lock decides order; second returns resulting state. |
| Cashout retry | Same response, no duplicate credit. |
| Timeout/recovery vs player action | Deterministic lock; no double settlement. |

### 5.6 Expiry / Recovery

| Scenario | Policy |
| --- | --- |
| Active safe multiplier > 1 and disconnect | Auto-cashout scenario #2. |
| Active zero safe picks | Future platform policy may refund; not custom BOXE logic. |
| Loss already committed | Confirm loss. |
| Wallet refusal during recovery | Retry/quarantine per recovery design. |

## 6. Idempotency Contract

### 6.1 Closure Criterion

Every mutating endpoint has replay behavior.

### 6.2 Required Mutating Operations

| Operation | Idempotency key | Owner |
| --- | --- | --- |
| Start round | Required | Frontend/client generated or platform helper. |
| Reveal/pick | Required | Frontend/client generated per row action. |
| Cashout | Required | Frontend/client generated. |
| Recovery auto-cashout | Required deterministic key | Backend recovery engine. |
| Admin force close/future quarantine action | Required if mutating money/session | Backend/admin service. |

### 6.3 Key Scope

| Field | Requirement |
| --- | --- |
| Scope | User/session/title/game/action. |
| Collision | Same key with different payload must reject. |
| Replay same payload | Return original result. |
| TTL | Must be long enough to cover client retry and recovery windows; exact value in Fase 2C. |
| Storage | Backend persistence, not browser-only. |

### 6.4 Duplicate Semantics

| Case | Response |
| --- | --- |
| Start key repeated after success | Return same active/started round. |
| Reveal key repeated after safe pick | Return same safe result. |
| Reveal key repeated after mine | Return same loss result. |
| Cashout key repeated after settlement | Return same cashout result. |
| Same key different row/box | Reject as idempotency conflict. |
| Same key different bet/config | Reject as idempotency conflict. |

### 6.5 Retry UX

Frontend may retry network failures.

Frontend must not fabricate an outcome while waiting.

After repeated failure, frontend shows connection error and offers retry/resume,
without starting a fresh round silently.

## 7. Rounding, Precision And Cap

### 7.1 Closure Criterion

No payout value depends on frontend rounding.

### 7.2 Precision Ownership

| Item | Owner |
| --- | --- |
| Multiplier precision | Backend math module. |
| Chip/currency payout rounding | Backend/platform accounting. |
| Display formatting | Frontend, from backend values. |
| Ledger amount | Platform wallet/ledger only. |

### 7.3 Required Numeric Contract

| Field | Requirement |
| --- | --- |
| Bet amount | Decimal money/chip amount accepted by platform. |
| Multiplier | Decimal, exact stored representation chosen in Fase 2A/2B. |
| Potential win | Backend computed. |
| Cashout win | Backend/platform settled. |
| Display amount | Derived from backend response. |

### 7.4 Rounding Rule

Fase 2A must define one explicit rounding rule for payout to ledger amount.

Accepted outcomes:

| Rule | Requirement |
| --- | --- |
| Existing platform decimal rule | Preferred if already canonical. |
| New game-specific helper | Allowed only if documented and tested. |
| Frontend rounding | Forbidden. |

### 7.5 Max Win Cap Interaction

This closes open question #4.

| Item | v1 decision |
| --- | --- |
| Cap value | `null`. |
| Auto stop on cap | Not active. |
| Cap UI | Not shown. |
| Config field | Reserved/future. |
| Future behavior | Requires platform cap WP and statement/finance contract. |

If a future cap is introduced, the cap must be enforced server-side before
settlement and represented in replay/history.

## 8. Replay And History Contract

### 8.1 Closure Criterion

Replay can be rendered after round close without hidden state.

### 8.2 Persisted Round Data

| Data | Required |
| --- | --- |
| `game_code` | `boxe` |
| `title_code` | Yes |
| `site_code` | Yes |
| `mode` | demo/real/bonus context |
| `rows` | Yes |
| `difficulty` | Yes |
| `bet_amount` | Yes |
| `wallet_source` | If real/bonus |
| `multiplier_path` | Yes, from backend math. |
| `safe_picks` | Ordered row/position list. |
| `final_pick` | If loss or top-row completion. |
| `outcome` | cashout/top_row/loss/expired/quarantined. |
| `payout_amount` | Yes for wins, zero for loss. |
| Fairness artifacts | Yes, enough for audit. |

### 8.3 Replay Payload Shape

The exact JSON can evolve in Fase 2C, but must include:

| Field | Meaning |
| --- | --- |
| `session_id` | BOXE technical session/round id. |
| `platform_round_id` | Real/bonus economic round id if applicable. |
| `title_code` | Title variant. |
| `rows` | Board height. |
| `difficulty` | Difficulty used. |
| `picks` | Ordered list of selected boxes. |
| `revealed_current_row` | Final row reveal for loss. |
| `safe_path` | Safe selected cells. |
| `outcome` | Terminal outcome. |
| `multiplier_final` | Final reached multiplier. |
| `payout_amount` | Settled amount. |

### 8.4 Player History

| Surface | Requirement |
| --- | --- |
| Account history | BOXE rounds appear alongside game history. |
| Replay access | Closed rounds only. |
| Active rounds | Not displayed as history. |
| Loss | Shows loss outcome and replay current row reveal only. |
| Recovery | Shows explicit recovery label if auto-cashout occurred. |

### 8.5 Finance/Admin History

| Surface | Requirement |
| --- | --- |
| Finance sessions report | Shows BOXE game/title/site dimensions. |
| Drilldown | Shows platform round and ledger transaction events. |
| Replay/admin view | Read-only, no hidden active state exposure. |
| Display id | Do not invent a new display id in BOXE; use platform decision. |

### 8.6 Fairness UI Decision

This closes open question #1.

| Layer | v1 decision |
| --- | --- |
| Player visible fairness UI | Not included in v1. |
| Player replay fairness data | Not shown unless platform adds common UI. |
| Admin/dev verification | Required by backend tests/tools. |
| Public endpoint | Only if common platform/game pattern requires it. |
| Rationale | Mines has no visible player fairness UI; adding one only for BOXE would be product/platform scope creep. |

## 9. Admin Config Lifecycle

### 9.1 Closure Criterion

Publishing cannot silently alter active rounds.

### 9.2 Master / Variant Defaults

| Item | Value |
| --- | --- |
| Engine/family | `boxe` |
| Master title | `boxe` or platform master code decided in Fase 1 seeding. |
| First variant | `boxe001` |
| Variant public launch | Only non-master published variants. |
| Master public launch | Rejected, same principle as Mines. |

### 9.3 Draft And Live Config

| Config | Draft behavior | Live behavior |
| --- | --- | --- |
| Rows/difficulty settings | Editable in admin | Used by new rounds only |
| Copy/rules | Editable per locale | Used by runtime/how-to/info |
| Theme tokens | Editable | Used by runtime title theme |
| Assets | Upload/delete/select | Used by runtime after publish/activation |
| Multiplier table | Not admin-editable | Code/math release only |

### 9.4 Active Round Publish Rule

Active rounds are pinned to the config snapshot used at start.

Publishing new config affects only future rounds.

| Scenario | Required behavior |
| --- | --- |
| Admin changes rows options during active round | Active round unaffected. |
| Admin publishes copy during active round | Gameplay logic unaffected. |
| Admin publishes theme during active round | Fase 1/implementation decides whether visual refresh is immediate; no logic change. |
| Admin archives title during active round | Existing round resolves/recovery; new launch blocked. |

### 9.5 Audit

| Event | Audit requirement |
| --- | --- |
| Publish BOXE config | Admin audit log. |
| Publish copy/rules | Admin audit log. |
| Publish theme | Admin audit log. |
| Upload/delete assets | Admin audit log. |
| Lobby publication | Existing site/title audit. |

## 10. Asset Contract

### 10.1 Closure Criterion

Every upload UI can state format, max size, dimensions, and render mode.

### 10.2 Asset Inventory

| Asset | Kind | v1 status |
| --- | --- | --- |
| Lobby card | `game_card` or existing platform lobby kind | Required. |
| Diamond symbol | BOXE board safe/diamond kind, final naming in Fase 1 | Required if not using fallback. |
| Mine symbol | BOXE board mine kind, final naming in Fase 1 | Required if not using fallback. |
| Sounds | Game-specific audio kinds if enabled | Optional/Fase 4B. |
| Theme | Tokens, not uploaded file | Required through platform default. |

### 10.3 Prepared Source Assets

| Source file | Use |
| --- | --- |
| `assets/Games/boxe/boxe_icon001_512px.webp` | Candidate lobby card. |
| `assets/Games/boxe/boxe_icon001.png` | Source backup, not runtime. |
| `assets/Games/boxe/diamond_green_v001.png` | Candidate safe/diamond symbol. |
| `assets/Games/boxe/mine_fucsia_002.png` | Candidate mine symbol. |

### 10.4 Upload Constraints

| Asset | Formats | Max size | Dimensions | Render mode |
| --- | --- | --- | --- | --- |
| Lobby card | PNG/JPEG/WebP | 300 KB | Square recommended, 512x512 target | Cover/center, possible crop |
| Diamond symbol | PNG/WebP | 300 KB v1 unless platform kind says otherwise | Transparent cutout recommended | Contain, no stretch |
| Mine symbol | PNG/WebP | 300 KB v1 unless platform kind says otherwise | Transparent cutout recommended | Contain, no stretch |
| Audio FX | MP3/WAV/OGG if enabled | 1 MB per current Mines audio pattern | n/a | Playback only |

Fase 1 must decide whether board symbols reuse existing semantic kinds or use
BOXE-specific kinds. Reusing a kind is allowed only if the meaning matches.

### 10.5 Validation Messages

| Error | Message contract |
| --- | --- |
| Unsupported format | State accepted formats. |
| Too large | State max file size. |
| Bad dimensions | State recommended dimensions and whether blocking. |
| Upload failed | Keep existing asset; show retry. |
| Delete active asset | Require clear operator confirmation if destructive. |

## 11. Failure UX

### 11.1 Closure Criterion

Every visible failure has player/admin copy and expected action.

### 11.2 Player Failure Matrix

| Scenario | Player behavior | Expected action |
| --- | --- | --- |
| Config missing | Error overlay: game configuration not loaded. | Retry or return lobby. |
| Title not published | Platform not-found/unavailable flow. | Return lobby. |
| Master title launch | Launch rejected with platform error. | Return lobby/admin preview only. |
| Table session expired | Session expired overlay. | Return to cashier/lobby. |
| Balance < bet | BET disabled or explicit insufficient balance error. | Lower bet manually or add/switch wallet. |
| Bonus wallet empty | Bonus empty warning. | Switch to cash or leave. |
| Network intermittent | Spinner/retry. | Retry same idempotent action. |
| Backend unreachable | Game temporarily unavailable. | Retry later/return lobby. |
| Round already closed, cashout retry | Return terminal state. | No duplicate action. |
| Disconnect safe multiplier | Auto-cashout/recovery label. | Show resolved result when available. |
| Loss response missed | Resume shows confirmed loss. | No new round until state is clear. |

### 11.3 Balance < Bet Decision

This closes open question #3.

The UI must not silently auto-adjust the player's bet.

| Reason | Requirement |
| --- | --- |
| Transparency | Player sees why BET is unavailable. |
| Accounting safety | No hidden mutation to stake amount. |
| Consistency | Matches conservative table-session/balance flow. |

If the player changes wallet or balance changes, the bet remains the player
input until the player edits it or a future explicit UX changes this behavior.

### 11.4 Admin Failure Matrix

| Scenario | Admin behavior |
| --- | --- |
| Invalid rows/default row | Block publish with field error. |
| Invalid difficulty/default | Block publish with field error. |
| Missing required locale copy | Block publish or show coverage failure. |
| Asset upload invalid | Show format/size/dimension guidance. |
| Title hidden/unpublished | Preview allowed only via admin preview flow. |
| Recovery quarantine future | Visible queue when platform implements it. |

## 12. Phase 1 Handoff Requirements

Fase 1 must produce:

| Output | Requirement |
| --- | --- |
| Common vs game-specific matrix | Include every capability from Playbook section 6. |
| Protected areas | Wallet, ledger, platform rounds, game-runtime, Mines. |
| Math input decision | Obtain multiplier table/formula before Fase 2A. |
| Asset kind decision | Reuse vs BOXE-specific kinds. |
| Admin editor shape | Confirm Title Editor can host BOXE settings. |
| Test skeleton | Contract, integration, visual, smoke. |
| Capability matrix skeleton | One per planned WP. |

## 13. Out Of Scope V1

| Item | Reason |
| --- | --- |
| Player visible provably fair UI | Platform/product decision, not BOXE-only v1. |
| Bet arrows +/- | Deferred UX polish. |
| Concrete max win cap | Requires platform cap WP. |
| Advanced skin MSK V2 controls | Deferred for BOXE v1. |
| Bonus rounds/free spins | Explicitly no. |
| External provider integration | BOXE is proprietary in-process game. |
| New platform shell behavior | Not needed; Stop-and-Ask if discovered. |

## 14. Acceptance Checklist

| Requirement | Status |
| --- | --- |
| 11 Playbook blocks present | Complete |
| Closure criterion per block | Complete |
| 7 open questions closed/deferred | Complete |
| BOXE_BRIEF decisions consolidated | Complete |
| `.docx` analysis referenced | Complete |
| Screenshot references included | Complete |
| Capability matrix declared | Complete |
| Wallet/ledger/RNG/payout/fairness/math untouched | Complete |
| Stop-and-Ask gaps documented | Complete |
