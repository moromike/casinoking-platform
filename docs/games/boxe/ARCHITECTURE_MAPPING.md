Status: ACTIVE
Last meaningful update: 2026-05-18

# BOXE - Architecture Mapping

Output di `WP-BOXE-FASE-1`. Questo documento applica
`docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` sezione 6 a BOXE e prepara le Fasi 2-7.

## 0. Scope

| Campo | Valore |
| --- | --- |
| Branch | `feature/boxe-fase-1-architecture-mapping` |
| Tipo | Documentation-only architecture mapping |
| Codice produzione | Non toccato |
| Architettura runtime | Non modificata |
| Math gap | Chiuso dopo Fase 1 tramite Fase 2A Option C; contratto in `MATH_SPEC.md` |

## 1. Classification Legend

| Categoria | Significato | Regola |
| --- | --- | --- |
| common | Capability platform riusata senza modifiche architetturali. | Usare API/shell/servizi esistenti. |
| game-specific | Nuovo codice BOXE isolato. | `frontend/app/ui/boxe/`, `backend/app/modules/games/boxe/`, test/doc BOXE. |
| platform extension | Eccezionale. | Stop-and-Ask + WP platform dedicato prima di implementare. |
| deferred | Fuori v1 o bloccato da input futuro. | Non implementare nei WP v1. |

## 2. Common Vs Game-Specific Matrix

### 2.1 Runtime And Shell

| Capability | Classification | Implementation owner | Notes |
| --- | --- | --- | --- |
| `GameBootShell` | common | `game-runtime/` | BOXE wrapper lo monta senza modificarlo. |
| `GameBootDecisionFlow` | common | `game-runtime/` | BOXE passa nodi/contenuti specifici. |
| Provider intro gate | common | `game-runtime/` | Default `moromike lab`, nessun override. |
| How-to-play gate | common + game-specific content | Shell common, copy BOXE | Contenuto Bet/Pick/Collect in `boxe/`. |
| Table balance gate | common | `game-runtime/` + table sessions | Nessun limite custom v1. |
| Short viewport gate | common | `game-runtime/` | Usare comportamento stabile. |
| Launch context/storage | common | `game-runtime/` | Namespace `boxe`; nessun import Mines. |
| Audio preferences | common | `game-runtime/` | FX state comune; cue BOXE specifici se aggiunti. |
| Runtime overlay/fatal state | common | `game-runtime/` | BOXE fornisce error copy/handling. |

### 2.2 Platform Services

| Capability | Classification | Implementation owner | Notes |
| --- | --- | --- | --- |
| Engine/Title/Site catalog | common + seeding game-specific | Platform catalog + BOXE seed | Aggiungere engine/title, non cambiare catalog core. |
| Master/variant model | common | Platform catalog | `boxe001` variante pubblicabile; master non launch pubblico. |
| Lobby publication | common | Site/Lobby | BOXE usa publish esistente. |
| Game library | common | Platform library | Deve includere BOXE quando pubblicato. |
| Launch Cashier | common | Player lobby/platform | Demo/real/bonus separati. |
| Game launch token | common + route game-specific | Platform launch + BOXE API | Se endpoint oggi Mines-named, Fase 2D valuta adapter senza rompere Mines. |
| Access sessions | common | Platform access | Persistono `game_code/title_code/site_code`. |
| Table sessions | common | Platform table sessions | BOXE non muta wallet direttamente. |
| Wallet read | common | Platform wallet | Gameplay legge/stampa, non scrive. |
| Ledger | common protected | Platform accounting | Solo adapter/platform rounds. |
| Platform rounds | common protected | Platform rounds | BOXE usa adapter; no bypass. |
| Admin audit log | common | Platform audit | Publish config/theme/assets/lobby. |
| Finance report/drilldown | common + payload game-specific | Finance common + BOXE payload | BOXE deve apparire nei report. |
| Player statement/history | common + payload game-specific | Account/history + BOXE replay | Round chiusi e recovery label. |
| Demo wallet | common | Platform demo | BOXE demo isolato come pattern Mines. |
| Session recovery | common designed | Platform recovery | Scenario #2; non implementare recovery engine in BOXE. |

### 2.3 BOXE Backend Capabilities

| Capability | Classification | Implementation owner | Notes |
| --- | --- | --- | --- |
| BOXE math module | game-specific | `backend/app/modules/games/boxe/` | Fase 2A: formula derivata da anchor + RTP 98%, isolata nel modulo BOXE. |
| Multiplier table/formula | game-specific | Product + math module | Option C approvata; no ricerca esterna, no stima casuale. |
| RNG board generation | game-specific | BOXE module | Pattern fairness Mines, meccanica propria. |
| Fairness artifacts | game-specific + common concept | BOXE module | No player fairness UI v1. |
| State machine | game-specific | BOXE service/repository | Stati da SPEC §5. |
| Idempotency handling | game-specific using platform pattern | BOXE service/API | Start/reveal/cashout. |
| Schema BOXE | game-specific | `backend/migrations/sql` | Tabelle tecniche BOXE, FK platform se real. |
| Repository BOXE | game-specific | BOXE backend module | Persistenza round/sessioni. |
| API start/reveal/cashout | game-specific | BOXE routes | Contract analogo, non copia Mines. |
| Replay endpoint | game-specific | BOXE routes/service | Payload piramide. |
| Config public endpoint | game-specific + title config common | BOXE routes/config | Runtime config per `title_code`. |
| Adapter to platform rounds | game-specific adapter using common platform | BOXE platform client | No wallet/ledger direct. |

### 2.4 BOXE Frontend Capabilities

| Capability | Classification | Implementation owner | Notes |
| --- | --- | --- | --- |
| Route `/boxe` | game-specific | `frontend/app/boxe/page.tsx` | Wrapper pubblico. |
| `BoxeStandalone` | game-specific | `frontend/app/ui/boxe/` | Usa `useGameLaunchContext("boxe")`. |
| `BoxeGameplay` | game-specific | `frontend/app/ui/boxe/` | Non importa `game-runtime/` se diventa gameplay puro. |
| Pyramid board | game-specific | `frontend/app/ui/boxe/` | Layout bottom-to-top. |
| Row/difficulty controls | game-specific | BOXE gameplay/config | Pre-round only. |
| Payout display | game-specific | BOXE UI | Display backend multipliers. |
| Bet/collect controls | game-specific + common wallet display | BOXE UI | BET/COLLECT state from API. |
| Replay renderer | game-specific | BOXE UI | Pyramid final state. |
| Animations | game-specific | BOXE CSS/components | Reduced-motion required. |
| CSS | game-specific | `frontend/app/ui/boxe/boxe.css` or module | No editing Mines CSS. |
| i18n defaults | game-specific using common pattern | BOXE i18n files | `it/en/de/es`. |
| Sound event bridge | game-specific using common preferences | BOXE hook/components | Optional Fase 4B/3C. |

### 2.5 Admin, Assets, Theme

| Capability | Classification | Implementation owner | Notes |
| --- | --- | --- | --- |
| Title Editor shell | common | Existing title editor | No extension expected in Fase 1. |
| Engine editor registry entry | game-specific plug-in | Title editor registry | BOXE editor registration. |
| BOXE config editor | game-specific | `frontend/app/ui/boxe/` or title-editor/boxe | Rows/difficulty/defaults. |
| BOXE copy/rules editor | game-specific using common locale pattern | BOXE editor + backend config | Update manual in Fase 4A. |
| Theme tokens | common base + game-specific editor use | Theme service/editor | No advanced skin v1. |
| Lobby card | common asset kind | Asset registry | Use existing `game_card`. |
| Diamond/mine symbols | game-specific asset semantics | Asset registry | Prefer BOXE-specific kinds unless semantics truly match shared kind. |
| Audio FX | game-specific kinds using common asset infra | Asset registry | Optional but planned Fase 4B if product wants FX. |
| Upload guidance | game-specific UI text | Admin editor/manual | Must show format/size/dim/render. |

### 2.6 Platform Extension Register

| Candidate | Decision | Reason |
| --- | --- | --- |
| Runtime shell extension | Not needed | SPEC says all shell defaults. |
| Title Editor framework extension | Not planned; watchpoint | Existing registry/editor shell should host BOXE-specific editor. |
| Wallet/ledger extension | Not allowed | Use platform adapter only. |
| New player fairness common UI | Deferred | BOXE v1 excludes visible fairness UI. |
| Max win cap platform policy | Deferred platform WP | `max_win_cap=null` v1. |
| Session recovery engine implementation | Deferred platform WP | BOXE consumes scenario #2 policy only. |

## 3. Protected File / Area List

| Area | Protection | Allowed BOXE interaction |
| --- | --- | --- |
| `backend/app/modules/wallet/` | Do not modify for BOXE. | Read via existing APIs/services only. |
| `backend/app/modules/ledger/` | Do not modify for BOXE. | Settlement through platform rounds. |
| `backend/app/modules/platform/rounds/` | Protected common core. | Adapter calls only; changes require CTO gate. |
| `backend/app/modules/games/mines/` | Do not modify. | Reference only. |
| `frontend/app/ui/mines/` | Do not modify/import. | Reference only. |
| `frontend/app/ui/game-runtime/` | Do not modify for BOXE v1. | Import/use public common APIs. |
| `frontend/app/lib/theme/` | Protected common theme. | Use provider/tokens. |
| Existing Mines smoke/visual baselines | Do not rewrite. | Run as regression protection. |
| Financial migrations/tables | Protected. | Add BOXE tables only if needed. |
| Payout/runtime Mines files | Do not touch. | None. |

## 4. Required Contract Tests

| Test | Purpose | Phase |
| --- | --- | --- |
| `game-runtime/*` does not import `boxe/*` | Keep shell game-agnostic. | 3A |
| `boxe/*` does not import `mines/*` | Prevent copy-coupling. | 3A/3B |
| `boxe-gameplay` does not import `game-runtime/*` if gameplay extracted | Keep wrapper/gameplay boundary clean. | 3B |
| BOXE backend does not import Mines backend modules | Preserve game isolation. | 2A/2B |
| BOXE game code does not import wallet/ledger services directly | Economic mutations through adapter. | 2D |
| BOXE API mutating endpoints require idempotency key | Retry safety. | 2C |
| BOXE replay never exposes hidden active state | Fairness/security. | 2C/2D |
| Demo/real/bonus flows tested separately | Wallet-mode correctness. | 2D/5/7 |

## 5. Smoke And Visual Baseline Plan

### 5.1 Browser Smoke

| Smoke | Minimum assertion | Phase |
| --- | --- | --- |
| Missing title | BOXE returns lobby/fatal safe state. | 3A |
| Unpublished title | Public launch blocked. | 5 |
| Demo launch | Opens BOXE with demo wallet. | 3A/5 |
| Real launch | Cashier -> table gate -> BOXE. | 5/7 |
| Bonus launch | Bonus wallet route separate. | 5/7 |
| Preview launch | Admin preview works for hidden/master as allowed. | 4/5 |
| Config loading slow/fail | No gameplay before runtime ready. | 3A |
| Start/reveal/cashout happy path | Round playable. | 3B/7 |
| Mine loss | Current row reveal only. | 3B/7 |
| Top row auto-collect | No extra click, terminal win. | 3B/7 |
| Resume/recovery-safe state | No duplicate settlement. | 7 |
| Mines regression smoke | Existing Mines smoke remains green. | 7 |

### 5.2 Visual Baselines

| Baseline | Viewports | Phase |
| --- | --- | --- |
| Idle 8 rows EASY | Desktop + mobile portrait | 3B |
| 4 rows HARD compact | Desktop + mobile portrait | 3B |
| Active safe pick | Desktop | 3B |
| Mine hit/current row reveal | Desktop + mobile | 3B/3C |
| Top row win | Desktop | 3B/3C |
| How-to-play gate | Desktop + mobile | 3A |
| Short landscape gate | Mobile landscape-short | 3A |
| Admin BOXE config editor | Desktop admin | 4A |
| Admin BOXE asset editor | Desktop admin | 4B |
| Lobby card | Desktop + mobile lobby | 5 |

## 6. Admin Manual Update Plan

| WP | Manual section to update | Content |
| --- | --- | --- |
| Fase 4A | Games / BOXE configuration | Rows, difficulty, copy/rules, draft/publish, validation. |
| Fase 4B | Games / BOXE assets and sounds | Asset kinds, upload constraints, render modes, preview/delete. |
| Fase 5 | Site / Lobby | Publishing BOXE, demo/real/bonus launch from lobby. |
| Fase 7 | Operating playthrough | Backoffice -> publish -> player -> finance -> replay checklist if manual has validation section. |

No Backoffice Manual update is required in Fase 1 because this WP is docs-only
and adds no admin UI behavior.

## 7. Planned WP List

| WP | Branch suggestion | Scope | Dependencies |
| --- | --- | --- | --- |
| `WP-BOXE-2A-MATH-RNG-FAIRNESS` | `feature/boxe-2a-math-rng-fairness` | Pure math, RNG, fairness artifacts, fixed-seed tests. | Product-approved math input. |
| `WP-BOXE-2B-SCHEMA-STATE` | `feature/boxe-2b-schema-state` | Migrations, repository, state machine, locks. | 2A interfaces, SPEC. |
| `WP-BOXE-2C-API` | `feature/boxe-2c-api` | Start/reveal/cashout/session/replay endpoints and error mapping. | 2B. |
| `WP-BOXE-2D-ADAPTER-FINANCE-REPLAY` | `feature/boxe-2d-platform-adapter` | Platform adapter, finance, player history, replay wiring. | 2C + platform services. |
| `WP-BOXE-3A-STANDALONE-BOOT` | `feature/boxe-3a-standalone-boot` | Route, standalone wrapper, shell gates, demo smoke placeholder. | 2C config/launch minimum or mocked contract. |
| `WP-BOXE-3B-GAMEPLAY` | `feature/boxe-3b-gameplay` | Pyramid board, controls, API actions, replay renderer basic. | 3A + 2C. |
| `WP-BOXE-3C-ANIMATIONS-POLISH` | `feature/boxe-3c-animations-polish` | Reveal/mine/top-row animations, audio event hooks, reduced motion. | 3B. |
| `WP-BOXE-4A-ADMIN-CONFIG-COPY` | `feature/boxe-4a-admin-config-copy` | Title Editor config/copy/rules integration. | 2B/2C config service decisions. |
| `WP-BOXE-4B-ASSETS-SOUNDS-THEME` | `feature/boxe-4b-assets-sounds-theme` | Asset kinds/editor, sounds if enabled, theme usage, lobby card. | 4A or shared asset decisions. |
| `WP-BOXE-5-LOBBY-LAUNCH` | `feature/boxe-5-lobby-launch` | Engine/title seed, site publication, library card, launch cashier. | 2D, 3A, 4B for card asset. |
| `WP-BOXE-6-DOCS-ATLAS` | `feature/boxe-6-docs-atlas` | `ARCHITECTURE_ATLAS_BOXE.md`, docs sync. | 2-5 enough behavior stabilized. |
| `WP-BOXE-7-E2E-VALIDATION` | `feature/boxe-7-e2e-validation` | Full smoke, visual baseline, manual playthrough, Mines regression. | 2-6 complete. |

## 8. Capability Matrix Skeletons

### 8.0 WP Exit Criteria Summary

| WP | Exit criteria |
| --- | --- |
| 2A | Math/RNG/fairness deterministic, fixed-seed tests green, multiplier input reconciled. |
| 2B | Schema migrated, repository persists states, illegal transitions and races tested. |
| 2C | Mutating APIs idempotent, replay/session read endpoints return safe payloads. |
| 2D | Platform adapter settles through platform rounds, finance/history/replay visible. |
| 3A | `/boxe` boots through common shell, demo smoke reaches runtime placeholder. |
| 3B | Pyramid gameplay playable demo end-to-end without polish animations. |
| 3C | Animations/audio feedback added without changing state/outcome. |
| 4A | Operator saves/publishes config/copy/rules; manual updated. |
| 4B | Assets/sounds/theme/lobby card upload/preview/delete; manual updated. |
| 5 | Lobby publishes BOXE and launches demo/real/bonus through cashier. |
| 6 | BOXE atlas and docs reflect actual delivered behavior. |
| 7 | Full E2E, visual baselines, finance/replay and Mines regression complete. |

### 8.0.1 Cross-WP Dependencies

| Dependency | Producer | Consumer | Blocking? |
| --- | --- | --- | --- |
| Product-approved multiplier table/formula | Product/CTO | 2A | Yes |
| BOXE config schema | 2B/4A design | 2C, 3A, 4A | Yes |
| Runtime config endpoint | 2C | 3A, 3B | Yes |
| Replay payload contract | 2C/2D | 3B, 7 | Yes |
| Platform adapter settlement | 2D | 5, 7 | Yes for real/bonus |
| Engine/title seed | 5 or earlier seed WP | 3A, 4A, 5 | Yes for public launch |
| Asset kind decision | 4B | 3B/3C/5 | Partial |
| Admin manual sections | 4A/4B/5 | 7 | Yes for closure |
| BOXE atlas | 6 | 7 | Yes |

### 8.0.2 Stop-And-Ask Triggers By WP

| WP | Trigger |
| --- | --- |
| 2A | Math input incomplete, conflicting, or not reproducible. |
| 2B | BOXE schema requires changing platform financial schema. |
| 2C | API needs payload changes in shared launch/table/session endpoints. |
| 2D | Adapter cannot settle without wallet/ledger direct mutation. |
| 3A | `game-runtime/` must be modified to boot BOXE. |
| 3B | Gameplay needs imports from Mines components. |
| 3C | Animation changes gameplay timing/outcome semantics. |
| 4A | Title Editor cannot host BOXE editor via existing registry/shell. |
| 4B | Asset registry cannot represent BOXE kinds without platform constraint change. |
| 5 | Lobby/cashier cannot launch non-Mines game through existing model. |
| 6 | Atlas reveals delivered behavior diverges from SPEC. |
| 7 | Mines regression appears or BOXE real/bonus differ from expected settlement. |

### 8.0.3 Protected Regression Suites

| Suite | Why |
| --- | --- |
| Game runtime frontend boundary contract | Ensures common shell remains game-agnostic. |
| Mines browser smoke | BOXE must not regress the shipped game. |
| Mines visual baseline | BOXE CSS/assets must not leak into Mines. |
| Financial reconciliation tests | BOXE settlement must preserve wallet/ledger invariants. |
| Platform access/table session tests | BOXE launch/session flow reuses these services. |
| Asset registry tests | BOXE asset kinds must preserve upload/delete/version behavior. |
| Admin audit log tests | BOXE publish/upload events must remain auditable. |

### 8.1 Fase 2A

| Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE math/RNG/fairness | n/a | NEW | n/a | n/a | n/a | n/a | NEW | SPEC/map | PLANNED |
| Math input reconciliation | n/a | NEW | n/a | n/a | n/a | n/a | NEW | SPEC | BLOCKED_UNTIL_INPUT |

### 8.2 Fase 2B

| Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE schema/repository | NEW | NEW | n/a | n/a | n/a | n/a | NEW | atlas draft | PLANNED |
| BOXE state machine/concurrency | NEW | NEW | n/a | n/a | n/a | n/a | NEW | SPEC | PLANNED |

### 8.3 Fase 2C

| Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE mutating APIs | TOUCHED | NEW | NEW | n/a | n/a | n/a | NEW | SPEC | PLANNED |
| BOXE replay/session read | TOUCHED | NEW | NEW | n/a | n/a | n/a | NEW | SPEC | PLANNED |

### 8.4 Fase 2D

| Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE platform adapter | TOUCHED | NEW | TOUCHED | n/a | n/a | n/a | NEW | atlas draft | PLANNED |
| Finance/history/replay wiring | TOUCHED | NEW | TOUCHED | TOUCHED | TOUCHED | n/a | NEW | atlas draft | PLANNED |

### 8.5 Fase 3A-3C

| Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE standalone boot | n/a | n/a | TOUCHED | n/a | NEW | TOUCHED | NEW | atlas draft | PLANNED |
| BOXE gameplay/replay UI | n/a | n/a | TOUCHED | n/a | NEW | NEW | NEW | atlas draft | PLANNED |
| BOXE animations/audio hooks | n/a | n/a | n/a | n/a | TOUCHED | TOUCHED | NEW | atlas draft | PLANNED |

### 8.6 Fase 4A-4B

| Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE admin config/copy/rules | TOUCHED | NEW | NEW | NEW | n/a | TOUCHED | NEW | manual/atlas | PLANNED |
| BOXE assets/sounds/theme | TOUCHED | NEW | NEW | NEW | TOUCHED | TOUCHED | NEW | manual/atlas | PLANNED |

### 8.7 Fase 5-7

| Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE lobby/launch | TOUCHED | TOUCHED | TOUCHED | TOUCHED | TOUCHED | TOUCHED | NEW | manual/atlas | PLANNED |
| BOXE atlas/docs | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NEW | PLANNED |
| BOXE E2E validation | n/a | n/a | n/a | TOUCHED | TOUCHED | TOUCHED | NEW | delivery | PLANNED |

## 9. Detailed WP Notes

### 9.1 `WP-BOXE-2A-MATH-RNG-FAIRNESS`

| Item | Note |
| --- | --- |
| Scope guard | Pure backend math/RNG/fairness only. |
| Must not touch | Wallet, ledger, platform rounds, frontend preview math. |
| Required input | Product Option C: derive formula from observed anchors + RTP 98%; documented in `MATH_SPEC.md`. |
| Tests | Fixed seed board generation, multiplier anchors, RTP/cap/rounding edges. |
| Docs | Update SPEC only if product math decision changes the contract. |

### 9.2 `WP-BOXE-2B-SCHEMA-STATE`

| Item | Note |
| --- | --- |
| Scope guard | Technical BOXE persistence and state machine. |
| Must not touch | Shared financial schema except FK/reference usage. |
| Tests | Migration, illegal transitions, concurrent reveal/cashout, active round lock. |
| Docs | Start draft notes for future `ARCHITECTURE_ATLAS_BOXE.md`. |

### 9.3 `WP-BOXE-2C-API`

| Item | Note |
| --- | --- |
| Scope guard | BOXE game endpoints and error mapping. |
| Must not touch | Existing Mines routes except shared router registration if unavoidable. |
| Tests | Idempotency, failure UX status codes, replay closed-only payload. |
| Docs | API payload decisions recorded if they refine SPEC. |

### 9.4 `WP-BOXE-2D-ADAPTER-FINANCE-REPLAY`

| Item | Note |
| --- | --- |
| Scope guard | Bridge BOXE to platform money/reporting. |
| Must not touch | Ledger internals for game-specific shortcuts. |
| Tests | Demo isolation, real cash settlement, bonus settlement, finance drilldown. |
| Docs | Capability matrix must prove no direct wallet/ledger mutation. |

### 9.5 `WP-BOXE-3A-STANDALONE-BOOT`

| Item | Note |
| --- | --- |
| Scope guard | Route and boot wrapper only. |
| Must not touch | `game-runtime/` unless CTO approves platform WP. |
| Tests | Missing title, demo boot, preview boot, runtime config slow/fail. |
| Docs | Runtime atlas update only if common responsibility changes. |

### 9.6 `WP-BOXE-3B-GAMEPLAY`

| Item | Note |
| --- | --- |
| Scope guard | BOXE-specific board, controls, replay renderer. |
| Must not touch | Mines UI/CSS/components. |
| Tests | Safe pick, mine hit, manual collect, top-row auto-collect. |
| Docs | Future BOXE atlas gameplay section. |

### 9.7 `WP-BOXE-3C-ANIMATIONS-POLISH`

| Item | Note |
| --- | --- |
| Scope guard | Visual/audio feedback only. |
| Must not touch | Outcome logic, timing semantics, payout. |
| Tests | Reduced motion, visual baselines, no layout overlap mobile/desktop. |
| Docs | Atlas only if animation ownership becomes architectural. |

### 9.8 `WP-BOXE-4A-ADMIN-CONFIG-COPY`

| Item | Note |
| --- | --- |
| Scope guard | BOXE editor plugin for config/copy/rules. |
| Must not touch | Title Editor shell architecture unless Stop-and-Ask passes. |
| Tests | Draft save, publish, validation errors, locale coverage. |
| Docs | `BACKOFFICE_MANUAL.md` update mandatory. |

### 9.9 `WP-BOXE-4B-ASSETS-SOUNDS-THEME`

| Item | Note |
| --- | --- |
| Scope guard | Asset/sound/theme controls for BOXE. |
| Must not touch | Asset registry invariants without dedicated platform WP. |
| Tests | Upload/delete/preview, format/size/dimension validation, runtime render. |
| Docs | `BACKOFFICE_MANUAL.md` upload constraints mandatory. |

### 9.10 `WP-BOXE-5-LOBBY-LAUNCH`

| Item | Note |
| --- | --- |
| Scope guard | Publication and player launch integration. |
| Must not touch | Lobby shell for game-specific hacks. |
| Tests | Hidden/unpublished/master blocked, demo/real/bonus launch, card render. |
| Docs | Manual Site/Lobby update. |

### 9.11 `WP-BOXE-6-DOCS-ATLAS`

| Item | Note |
| --- | --- |
| Scope guard | Documentation of delivered architecture. |
| Must not do | Document planned behavior as delivered. |
| Tests | n/a |
| Docs | `docs/ARCHITECTURE_ATLAS_BOXE.md` active and indexed. |

### 9.12 `WP-BOXE-7-E2E-VALIDATION`

| Item | Note |
| --- | --- |
| Scope guard | Validation and bug filing/fixes only if scoped. |
| Must not do | Hide regressions in delivery prose. |
| Tests | Browser smoke, visual regression, manual playthrough, Mines regression. |
| Docs | Delivery report with capability matrix final state. |

## 10. Fase 1 Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE architecture mapping | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NEW | COMPLETE | Architecture mapping, no production code touched, no architecture changes. |
| BOXE WP plan | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NEW | COMPLETE | Fasi 2-7 planned with branch suggestions and dependencies. |
| BOXE brief implementation log | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | COMPLETE | Fase 1 log entry added. |
| Docs index | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | COMPLETE | Mapping indexed as ACTIVE. |

## 11. Stop-And-Ask Register

| Topic | Decision |
| --- | --- |
| Platform extension found | None required in Fase 1. |
| Title Editor Mines-shaped risk | Watchpoint for Fase 4A; current plan is game-specific editor plugin, not platform extension. |
| Math gap | Closed after Fase 1 by product-approved Option C in Fase 2A; see `MATH_SPEC.md`. |
| Asset kind semantics | Fase 4B must decide final kind names; avoid reusing Mines kind if semantics diverge. |
