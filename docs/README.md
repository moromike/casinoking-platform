Status: ACTIVE
Last meaningful update: 2026-05-29

# CasinoKing Documentation Index

This is the documentation index for humans and AI working on CasinoKing.

The remembered project entry point is the root `README.md`. This file is the
entry point for the `docs/` tree.

AGENTS.md is not a primary source: shared rules live in this docs/ tree.

## Required First Reading

Read these files first, in this order:

1. docs/SOURCE_OF_TRUTH.md
2. docs/TASK_EXECUTION_GUARDRAILS.md
3. docs/DOCUMENTATION_MAINTENANCE.md
4. docs/AI_CRITICAL_JUDGMENT_RULES.md
5. docs/ACTIVE_OPEN_LOOPS.md

Then read only the domain documents needed for the current task. Do not claim a
file was read if it was only discovered in this index.

## Fresh AI / Desktop Bootstrap

For a new AI session, Codex Desktop handoff, Codex VS Code handoff, CLI handoff,
or CTO review of the repository bootstrap process, read:

- `docs/AI_BOOTSTRAP_RUNBOOK.md`
- `docs/SELF_BOOTSTRAP_AUDIT_2026-05-28.md`
- `docs/LOCAL_SMOKE_SUITE.md`

The runbook is the short operational entry point. The audit explains current
self-bootstrap maturity, gaps, and recommended work packages. The smoke suite
defines the canonical local smoke verification target.

## Da Fare Subito - In Attesa Di Michele

Pending product decisions che bloccano l'avanzamento di un workstream. Da chiudere prima
di entrare in fase implementativa.

| Data apertura | Tema | Cosa serve da Michele | Dove |
| --- | --- | --- | --- |
| 2026-05-25 | COINS - nuovo gioco proprietario, Fase 0+1 | 25 Q product + round 2 follow-up chiusi. Prerequisiti stretti Rule 18 registry ed embed parity committati. Parte A plan prodotto; prossimo step: approvare il plan e produrre i 6 documenti finali SPEC/Math/Architecture. | `docs/games/coins/COINS_PHASE_0_1_PLAN_2026-05-25.md` |
| 2026-05-25 | WP-FINANCE-REPLAY-REGISTRY-RETENTION (prerequisito COINS) | MVP committato (`e7cf96d`): registry guard unknown, settlement taxonomy metadata forward-only, BOXE wallet source, retention doc 30gg online/no deletion. Subset COINS-specific superseded. | `docs/PLATFORM_REPLAY_RETENTION_POLICY_2026-05-25.md` |
| 2026-05-25 | WP-ERROR-REQUEST-FOUNDATION-MVP | MVP committato (`1c07ced`): request/support id middleware, AppError/registry MVP, central handlers, frontend diagnostic line e test contrattuali. | `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_APPROACH_2026-05-25.md` |
| 2026-05-25 | WP-PLATFORM-REQUEST-ID-AND-STRUCTURED-LOGGING-MVP | MVP committato (`6d83be4`): stdout JSON structured logger, redaction/clamp, request_id/job_id correlation e timeout sweeper event. | `docs/PLATFORM_REQUEST_ID_STRUCTURED_LOGGING_MVP_APPROACH_2026-05-25.md` |
| 2026-05-25 | WP-PLATFORM-SETTINGS-READONLY-INVENTORY | MVP committato (`1857b00`) + closure security/settings: filtri UI, spiegazioni IT/EN, CSS leggibile su fondo chiaro, no client default access password, `/ready` DB/Redis, RBAC explicit profile, Site v2 senza token query, runtime descriptor uniforme per Mines/BOXE/HI-LO. | `docs/PLATFORM_SETTINGS_READONLY_INVENTORY_IMPLEMENTATION_2026-05-25.md` |
| 2026-05-25 | WP-EMBED-MODE-PARITY-BOXE-HILO (prerequisito COINS) | Committato: `useGameEmbedBridge(gameCode)` + Mines/BOXE/HI-LO consume. Audit: `docs/games/coins/EMBED_MODE_PARITY_AUDIT_2026-05-25.md`. | `docs/games/coins/PROMPT_CODEX_WP_EMBED_MODE_PARITY_2026-05-25.md` |
| 2026-05-25 | Site V3 - WP5/WP6/MIG player/game/admin shell | WP2 backend, WP3 admin builder e WP4 public renderer implementati. WP-A CMS IA cleanup, WP-B theme tokens, WP5 product QA guardrails e upload/picker banner Site media chiusi. WP6 cleanup ha rimosso il lab locale `frontend-v2/`, promosso `frontend-v3` a servizio Docker ufficiale e aggiunto l'edge locale: `:3000` e' il sito pubblico Site V3; login/register/account e shell pubbliche `/mines`, `/boxe`, `/hi-lo` sono Site V3-owned, Mines/BOXE/HI-LO vivono in `frontend-v3/app/runtime/*`; `:3001` resta direct renderer e `:3002` V1 diretto solo come host interno debug/admin. WP-MIG3 first slice aggiunge la pagina di sistema `register` e il modulo `system_registration_form` per configurare la registrazione dal CMS senza cambiare backend auth/wallet/ledger. WP-MIG4A/B avviano il retirement V1: le route dirette V1 login/register/account reindirizzano a Site V3 preservando query e il root diretto V1 reindirizza a `/admin`. WP-MIG4C ha fissato il contratto runtime extraction; WP-MIG4D/E/F hanno migrato BOXE, HI-LO e Mines rimuovendo le route `/legacy-games/*`. WP-MIG5A ha fissato il piano admin-only; WP-MIG5B/C/D first slice ha migrato `/admin/site-v3`, `site-v3-admin/**` e `/admin/games/**` con catalogo giochi, Title Editor e backoffice editor engine in `frontend-v3`, con edge specifici V3 prima del proxy `/admin` V1. Restano da migrare finance/player/settings/audit e asset statici prima di rimuovere il servizio V1. | `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md`, `docs/SITE_V3_V1_RETIREMENT_PLAN_2026-05-29.md`, `docs/SITE_V3_RUNTIME_EXTRACTION_CONTRACT_2026-05-29.md` |

Quando Michele dice "controlla il readme e facciamo l'elenco delle cose da fare",
questa sezione e' la prima da leggere insieme a `docs/ACTIVE_OPEN_LOOPS.md`.

## Resume / Open Loops Checkpoint

When resuming after a PC restart, context compaction, long pause, or handoff,
read `docs/ACTIVE_OPEN_LOOPS.md` immediately after the required rules above.
It is the short operational checkpoint for pending work that must not rely on
chat memory.

If the active work is HI-LO, also read
`docs/games/hi-lo/HI_LO_GAMEPLAY_UX_AND_RECOVERY_ROADMAP_2026-05-23.md`
before touching gameplay UX, replay/recovery, or player-facing refinements.

For the post-HI-LO open themes currently under CTO triage (finance/replay,
Site V3 rescue, HI-LO current multiplier), read
`docs/OPEN_TOPICS_CTO_REVIEW_2026-05-24.md`.

For any task that touches game financial reporting, player/admin replay,
account history, ledger explanations, or a new game's reporting adapter, read
`docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md`.

## Site V3

Site V3 e' il nuovo sito/CMS parallelo al V1. Il builder Site V3 vive ora in
`frontend-v3` su `/admin/site-v3`; anche il game admin e Title Editor vivono
in `frontend-v3` su `/admin/games/**`. Entrambi sono raggiunti dal public edge
`:3000` prima del proxy admin legacy; il renderer pubblico vive in `frontend-v3/` ed e' servito
come root pubblico da `edge` su `:3000`. Il direct renderer resta su `:3001`,
mentre V1 diretto resta su `:3002` per debug locale e admin legacy. Login,
registrazione, account player e shell pubbliche `/mines`, `/boxe`, `/hi-lo`
sono ora rotte Site V3; finance/player/settings/audit e il generic `/admin`
restano V1-owned dietro l'edge fino ai prossimi WP-MIG5.
Mines, BOXE e HI-LO sono runtime Site V3 sotto
`/runtime/mines`, `/runtime/boxe` e `/runtime/hi-lo`.
Il direct root V1 `:3002/` reindirizza a `/admin`, quindi
non e' piu' una homepage/lobby player. Il vecchio lab locale `frontend-v2/` e'
stato rimosso in WP6.

Baseline doc da leggere, in ordine:

1. `docs/SITE_V3_SCOPE_AND_ARCHITECTURE_PLAN_2026-05-25.md`
2. `docs/SITE_V3_AUDIT_RESCUE_2026-05-25.md`
3. `docs/SITE_V3_PRODUCT_CONTRACT_2026-05-25.md`
4. `docs/SITE_V3_MODULE_TAXONOMY_2026-05-25.md`
5. `docs/SITE_V3_LIFECYCLE_API_SECURITY_PLAN_2026-05-25.md`
6. `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md`
7. `docs/SITE_V3_V1_RETIREMENT_PLAN_2026-05-29.md`
8. `docs/SITE_V3_RUNTIME_EXTRACTION_CONTRACT_2026-05-29.md`

Prompt/checkpoint WP1 follow-up:

- `docs/SITE_V3_WP1_FOLLOWUP_PROMPT_2026-05-25.md`
- `docs/SITE_V3_WP2_BACKEND_BRIEF_2026-05-25.md`
- `docs/SITE_V3_WP3_ADMIN_BUILDER_BRIEF_2026-05-25.md`
- `docs/SITE_V3_WP4_PUBLIC_RENDERER_BRIEF_2026-05-25.md`
- `docs/SITE_V3_ADMIN_NAVIGATION_RESTRUCTURE_APPROACH_2026-05-26.md`
- `docs/SITE_V3_WP_PREVIEW_LIVE_BRIEF_2026-05-27.md`
- `docs/PROMPT_CODEX_WP_PREVIEW_LIVE_PARTE_B_2026-05-27.md`
- `docs/SITE_V3_CMS_INFORMATION_ARCHITECTURE_AUDIT_2026-05-28.md`
- `docs/SITE_V3_WP_CMS_IA_CLEANUP_BRIEF_2026-05-28.md`
- `docs/SITE_V3_WP_THEME_TOKENS_BRIEF_2026-05-28.md`
- `docs/SITE_V3_CUSTOM_MODULE_AUTHORING_PLAN_2026-05-29.md`
- `docs/SITE_V3_V1_RETIREMENT_PLAN_2026-05-29.md`
- `docs/SITE_V3_RUNTIME_EXTRACTION_CONTRACT_2026-05-29.md`

Memoria esterna/CTO collegata: `project_site_v3`.

WP2 Backend MVP, WP3 Admin Builder MVP, WP4 Public Renderer MVP, WP-A CMS IA
cleanup, WP-B theme tokens e Site V3 custom module first slice sono chiusi. Il builder vive in `frontend-v3` su
`/admin/site-v3`; il renderer pubblico vive in `frontend-v3/`, published-only,
senza token admin, ed e' il root del public edge `:3000`. WP5 Product QA ha chiuso guardrail su
modifiche non salvate, validation-before-publish, asset URL safe e upload/picker
banner nel builder usando il flusso Site media esistente. WP6 ha rimosso il lab
locale `frontend-v2/`, aggiunto `frontend-v3` allo stack Docker/doctor/smoke e
promosso il default locale via edge (`:3000` Site V3 root, `/admin/site-v3` in
V3, altre famiglie admin legacy V1 proxate). WP-MIG1 sposta login/register/account in `frontend-v3` consumando le
API auth/account/wallet esistenti senza cambiare wallet, ledger o runtime
giochi. WP-MIG2 sposta le shell pubbliche giochi in `frontend-v3`; WP-MIG4D/E/F
spostano i runtime gioco in iframe same-origin sotto `/runtime/*`. WP-MIG4A rende le
route dirette V1 `/login`, `/register` e `/account` semplici redirect verso
Site V3; WP-MIG4B fa reindirizzare il root diretto V1 `:3002/` a `/admin`,
cosi' V1 diretto non e' piu' un secondo prodotto player. WP-MIG4C fissa il
contratto di estrazione runtime giochi: un runtime per volta in
`frontend-v3/app/runtime/{game}`. WP-MIG4D/E/F hanno migrato BOXE, HI-LO e
Mines in `frontend-v3/app/runtime/*`, rimosso le route `/legacy-games/*`
dall'edge e reso le route dirette V1 gioco redirect verso Site V3. WP-MIG5B/C/D
sposta `/admin/site-v3`, il builder CMS e `/admin/games/**` con catalogo giochi
e Title Editor in `frontend-v3`; le route dirette V1 corrispondenti sono
redirect verso Site V3. Le custom module
definitions pubblicate sono montabili in Composition e renderizzate da snapshot
pubblici template-based. WP-MIG3 first slice aggiunge `Pages -> System pages`
per la pagina `register` e il modulo built-in `system_registration_form`: la
rotta pubblica `/register` legge copy, campi e step documenti dalla snapshot
pubblicata, con fallback default e senza cambiare backend auth/wallet/ledger. Il
prossimo step operativo e' WP-MIG5E/F: migrazione finance/player/settings/audit
e ownership degli asset statici; i giochi runtime non sono piu' il blocco
residuo principale.

## Platform Observability / Error / Settings Plans

The following platform plans are architecture proposals. Each plan has its own
CTO review; the unified review is only a cross-plan orchestration note and must
not replace the per-plan CTO verdict.

- `docs/PLATFORM_APPLICATION_LOGGING_PLAN_2026-05-24.md`
  - CTO review: `docs/PLATFORM_APPLICATION_LOGGING_CTO_REVIEW_2026-05-24.md`
  - Current-state CTO review:
    `docs/PLATFORM_APPLICATION_LOGGING_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`
- `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_PLAN_2026-05-24.md`
  - CTO review: `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_CTO_REVIEW_2026-05-24.md`
  - Current-state CTO review:
    `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`
- `docs/PLATFORM_ERROR_CODE_REGISTRY_PLAN_2026-05-24.md`
  - CTO review: `docs/PLATFORM_ERROR_CODE_REGISTRY_CTO_REVIEW_2026-05-24.md`
  - Current-state CTO review:
    `docs/PLATFORM_ERROR_CODE_REGISTRY_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`
  - First implementation brief:
    `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_BRIEF_2026-05-25.md`
  - Implemented foundation approach:
    `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_APPROACH_2026-05-25.md`
- `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_PLAN_2026-05-24.md`
  - CTO review: `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_CTO_REVIEW_2026-05-24.md`
  - Current-state CTO review:
    `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`
- Cross-plan orchestration only:
  `docs/PLATFORM_OBSERVABILITY_ERROR_SETTINGS_CTO_REVIEW_2026-05-24.md`
- Final pre-implementation analysis packet:
  `docs/PLATFORM_PRE_IMPLEMENTATION_ANALYSIS_PACKET_2026-05-25.md`

Do not start code for logging, financial audit traceability, error-code
registry, global installation settings, or backoffice error matrix until the
relevant plan has been approved or explicitly narrowed by the CTO.

## Architecture Map Maintenance

The navigable Mermaid code map lives in
`docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md`.

When a commit changes module ownership, frontend/backend flow, admin routing,
game-runtime inheritance, API/domain boundaries, persistence responsibilities,
or the Mines/BOXE shared-vs-game-specific split, update the Mermaid map in the
same commit or add an explicit follow-up note explaining why no map update was
needed.

## Creazione Nuovi Giochi

Per ogni nuovo gioco proprietario dopo Mines e BOXE, non partire dal codice.
Partire dal metodo.

Ordine operativo:

1. leggere `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`;
2. leggere `docs/NEW_GAME_BRIEF_TEMPLATE.md`;
3. leggere l'ultimo replication brief del gioco precedente, se esiste;
4. leggere la mappa Mermaid `docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md`;
5. creare prima i documenti di analisi del nuovo gioco:
   - source inventory;
   - product decision map;
   - open questions / Stop-and-Ask register;
   - 12-surface status;
   - SPEC e MATH_SPEC solo dopo aver chiuso i blocker.

HI-LO è il progetto pilota per rendere questo processo più automatico. La guida
breve per iniziare è:

`docs/games/hi-lo/HI_LO_AI_QUICKSTART_2026-05-22.md`

Il manuale metodologico completo è:

`docs/games/hi-lo/HI_LO_PROJECT_METHOD_AND_EXECUTION_PLAN_2026-05-22.md`

Durante HI-LO, ogni scoperta va classificata come:

- **Reusable method**: regola di processo valida per i prossimi giochi;
- **Platform pattern**: capability/component condiviso da estrarre o riusare;
- **HI-LO-specific**: meccanica, math, visual o copy propri di HI-LO.

Le prime due categorie vanno nella distillation queue e possono aggiornare
Playbook, template o mappa architetturale. La terza resta nei documenti HI-LO
(`SPEC`, `MATH_SPEC`, `ARCHITECTURE_MAPPING`) salvo che riveli una lezione
riusabile.

Gate pratico prima del walkthrough Product Owner: il nuovo gioco deve essere
testabile dalla lobby/CMS locale, non solo tramite deep link. Prima di chiedere
validazione su `localhost:3000`, verificare che il title sia pubblicabile dal CMS,
visibile in `/games/library`, avviabile da card lobby in demo, e che il real mode
passi dal login/table-balance gate senza mai usare implicitamente tutto il wallet.

A chiusura HI-LO, produrre obbligatoriamente un replication brief per il gioco
successivo e, se il metodo regge, estrarre una versione generica del template
operativo da riusare per GAME 4+.

Brief correnti da usare per il prossimo gioco:

- `docs/NEXT_GAME_REPLICATION_BRIEF_FROM_HI_LO_2026-05-23.md`
- `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_HI_LO_2026-05-23.md`
- `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_BOXE_2026-05-22.md`

## Status Legend

| Status | Meaning |
| --- | --- |
| ACTIVE | Current product, process, architecture, operational, or pending-decision document. |
| COMPLETED | Closed plan, final reference, canonical mirror, or completed audit still useful for context. |
| SUPERSEDED | Replaced by a newer document; use the successor instead. |
| HISTORICAL | Past note, prompt, incident, snapshot, or decision history; not operational. |

Markdown files carry Status and Last meaningful update at the top. Binary
artifacts are classified in this index because writing metadata inside them
would corrupt or unnecessarily rewrite the artifact.

## Documenti attivi

| Document | Last meaningful update | Notes |
| --- | --- | --- |
| `docs/ACCOUNT_ACC_1_ENDPOINT_AUDIT.md` | 2026-05-10 | Account ACC-1 Endpoint Audit |
| `docs/ACCOUNT_CASHIER_MOVEMENTS_REDESIGN_ANALYSIS.md` | 2026-05-10 | Account Cashier Movements Redesign Analysis |
| `docs/ACCOUNT_WALLET_GAME_HISTORY_REDESIGN_PLAN.md` | 2026-05-10 | Account Wallet And Game History Redesign Plan |
| `docs/ACTIVE_OPEN_LOOPS.md` | 2026-05-29 | CasinoKing Active Open Loops |
| `docs/AI_BOOTSTRAP_RUNBOOK.md` | 2026-05-28 | CasinoKing AI Bootstrap Runbook |
| `docs/AI_CRITICAL_JUDGMENT_RULES.md` | 2026-05-10 | AI Critical Judgment Rules |
| `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md` | 2026-05-29 | CasinoKing - Architecture Atlas Game Runtime |
| `docs/ARCHITECTURE_ATLAS_BOXE.md` | 2026-05-21 | BOXE - Architecture Atlas |
| `docs/ARCHITECTURE_ATLAS_MINES.md` | 2026-05-21 | CasinoKing - Architecture Atlas Mines |
| `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md` | 2026-05-29 | CasinoKing - Architecture Atlas Platform + Frontend |
| `docs/ASSET_REGISTRY_PLAN.md` | 2026-05-17 | CasinoKing - Asset registry plan - Fase 4 |
| `docs/BACKOFFICE_MANUAL.md` | 2026-05-29 | CasinoKing Backoffice Manual |
| `docs/BOOT_2A_BRANCH_AUDIT_2026-05-17.md` | 2026-05-17 | BOOT-2A Branch Audit - 2026-05-17 |
| `docs/BOXE_PROJECT_BRIEF.md` | 2026-05-19 | BOXE - Project Brief |
| `docs/CAPABILITY_INVENTORY_2026-05-17.md` | 2026-05-19 | CasinoKing Capability Inventory |
| `docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md` | 2026-05-29 | CasinoKing - Code Architecture Mermaid Map |
| `docs/CMS_0_ADMIN_CMS_INVENTORY.md` | 2026-05-09 | CMS-0 Admin CMS Inventory |
| `docs/CMS_ROADMAP_AND_EXTERNAL_GAMES_PLAN.md` | 2026-05-10 | CMS Roadmap And External Games Plan |
| `docs/CMS_V2_MODULE_COMPOSER_PLAN.md` | 2026-05-25 | SUPERSEDED - old CMS v2 lab handoff, replaced by Site V3 plan |
| `docs/SITE_V3_SCOPE_AND_ARCHITECTURE_PLAN_2026-05-25.md` | 2026-05-25 | Site V3 - Scope And Architecture Plan |
| `docs/SITE_V3_AUDIT_RESCUE_2026-05-25.md` | 2026-05-25 | Site V3 - Audit Rescue del Lab Gemini |
| `docs/SITE_V3_PRODUCT_CONTRACT_2026-05-25.md` | 2026-05-29 | Site V3 - Product And Boundary Contract |
| `docs/SITE_V3_MODULE_TAXONOMY_2026-05-25.md` | 2026-05-29 | Site V3 - Module Taxonomy And Content Model |
| `docs/SITE_V3_LIFECYCLE_API_SECURITY_PLAN_2026-05-25.md` | 2026-05-25 | Site V3 - Lifecycle, API And Security Plan |
| `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md` | 2026-05-29 | Site V3 - Implementation WP Roadmap |
| `docs/SITE_V3_V1_RETIREMENT_PLAN_2026-05-29.md` | 2026-05-29 | Site V3 - V1 Retirement Plan |
| `docs/SITE_V3_RUNTIME_EXTRACTION_CONTRACT_2026-05-29.md` | 2026-05-29 | Site V3 - Runtime Extraction Contract |
| `docs/SITE_V3_WP1_FOLLOWUP_PROMPT_2026-05-25.md` | 2026-05-25 | Site V3 - WP1 Follow-up Prompt per Codex |
| `docs/SITE_V3_WP2_BACKEND_BRIEF_2026-05-25.md` | 2026-05-25 | Site V3 - WP2 Backend MVP Brief Parte A |
| `docs/SITE_V3_WP3_ADMIN_BUILDER_BRIEF_2026-05-25.md` | 2026-05-25 | Site V3 - WP3 Admin Builder MVP Brief Parte A |
| `docs/SITE_V3_WP4_PUBLIC_RENDERER_BRIEF_2026-05-25.md` | 2026-05-25 | Site V3 - WP4 Public Renderer MVP Brief Parte A |
| `docs/SITE_V3_ADMIN_NAVIGATION_RESTRUCTURE_APPROACH_2026-05-26.md` | 2026-05-26 | Site V3 - Admin Navigation Restructure Approach |
| `docs/SITE_V3_WP_PREVIEW_LIVE_BRIEF_2026-05-27.md` | 2026-05-27 | Site V3 - WP Preview Live Brief |
| `docs/SITE_V3_CMS_INFORMATION_ARCHITECTURE_AUDIT_2026-05-28.md` | 2026-05-28 | Site V3 - CMS Information Architecture Audit |
| `docs/SITE_V3_WP_CMS_IA_CLEANUP_BRIEF_2026-05-28.md` | 2026-05-28 | Site V3 - CMS IA Cleanup Brief |
| `docs/SITE_V3_WP_THEME_TOKENS_BRIEF_2026-05-28.md` | 2026-05-28 | Site V3 - WP-B Theme Tokens Brief |
| `docs/SELF_BOOTSTRAP_AUDIT_2026-05-28.md` | 2026-05-28 | CasinoKing Self-Bootstrap Audit |
| `docs/DOCUMENTATION_MAINTENANCE.md` | 2026-05-17 | CasinoKing - Documentation Maintenance |
| `docs/E2E_MANUAL_SMOKE_PLAN.md` | 2026-05-07 | CasinoKing - E2E Manual Smoke Plan |
| `docs/LOCAL_SMOKE_SUITE.md` | 2026-05-29 | CasinoKing Local Smoke Suite |
| `docs/FINANCIAL_AREA_DESIGN.md` | 2026-04-12 | Analisi e Design: Area Finanziaria e Vista Banco (EPIC 4) |
| `docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md` | 2026-05-24 | Game Finance / Replay / Reporting Contract |
| `docs/GAME_ADMIN_CHANGE_LOG_PLAN.md` | 2026-05-07 | CasinoKing - Game Admin Change Log Plan |
| `docs/GAME_ARCHITECTURE_OVERVIEW.md` | 2026-05-16 | Game Architecture Overview |
| `docs/games/boxe/ARCHITECTURE_MAPPING.md` | 2026-05-18 | BOXE - Architecture Mapping |
| `docs/games/boxe/BOXE_BRIEF.md` | 2026-05-21 | BOXE - Game Brief |
| `docs/games/boxe/CLOSURE_REPORT.md` | 2026-05-19 | BOXE - Closure Report |
| `docs/games/boxe/MATH_SPEC.md` | 2026-05-18 | BOXE - Math, RNG And Fairness Spec |
| `docs/games/boxe/MANUAL_PLAYTHROUGH_CHECKLIST.md` | 2026-05-18 | BOXE - Manual Playthrough Checklist |
| `docs/games/boxe/BOXE_FULL_PARITY_AUDIT_2026-05-19.md` | 2026-05-19 | BOXE - Full Parity Audit |
| `docs/games/boxe/CONTROL_RAIL_EXTRACTION_APPROACH_2026-05-19.md` | 2026-05-19 | BOXE - Control Rail Shared Extraction Approach |
| `docs/games/boxe/INFO_RULES_PARITY_APPROACH_2026-05-21.md` | 2026-05-21 | BOXE - Info Rules Parity Approach |
| `docs/games/boxe/BOXE_RETROSPECTIVE_ANALYSIS_2026-05-19.md` | 2026-05-19 | BOXE - Retrospective Analysis |
| `docs/games/boxe/SPEC.md` | 2026-05-18 | BOXE - SPEC |
| `docs/games/boxe/SHELL_UNIFORMITY_AUDIT_2026-05-19.md` | 2026-05-19 | BOXE - Shell Uniformity Audit |
| `docs/games/boxe/TABLE_SESSION_LIFECYCLE_APPROACH_2026-05-19.md` | 2026-05-19 | BOXE - Table Session Lifecycle Approach |
| `docs/games/boxe/TITLE_EDITOR_TABS_EXTRACTION_APPROACH_2026-05-19.md` | 2026-05-19 | BOXE - Title Editor Tabs Shared Extraction Approach |
| `docs/games/boxe/WAVE7_BACKOFFICE_FULL_CLOSURE_PLAN_2026-05-22.md` | 2026-05-22 | BOXE Wave 7 - Backoffice Full Closure Plan |
| `docs/games/coins/COINS_OPEN_QUESTIONS_2026-05-25.md` | 2026-05-25 | COINS - Open Questions And Product Decision Checklist (Fase 0) |
| `docs/games/coins/PROMPT_CODEX_COINS_FASE_0_1_SPEC_2026-05-25.md` | 2026-05-25 | COINS - Prompt Codex Fase 0+1 SPEC and Architecture Mapping |
| `docs/games/coins/COINS_PHASE_0_1_PLAN_2026-05-25.md` | 2026-05-25 | COINS - Phase 0+1 Plan (Parte A) |
| `docs/games/coins/PLATFORM_REGISTRY_AUDIT_2026-05-25.md` | 2026-05-25 | COINS prerequisito - Platform Registry Audit for account/finance/replay |
| `docs/games/coins/EMBED_MODE_PARITY_AUDIT_2026-05-25.md` | 2026-05-25 | COINS prerequisito - Embed Mode Parity Audit for BOXE/HI-LO |
| `docs/games/coins/PROMPT_CODEX_WP_FINANCE_REPLAY_REGISTRY_2026-05-25.md` | 2026-05-25 | SUPERSEDED - COINS subset replaced by WP-FINANCE-REPLAY-REGISTRY-RETENTION |
| `docs/games/coins/PROMPT_CODEX_WP_EMBED_MODE_PARITY_2026-05-25.md` | 2026-05-25 | COINS prerequisito - Prompt Codex WP-EMBED-MODE-PARITY-BOXE-HILO |
| `docs/games/hi-lo/ARCHITECTURE_MAPPING.md` | 2026-05-23 | HI-LO - Architecture Mapping |
| `docs/games/hi-lo/CLOSURE_REPORT.md` | 2026-05-23 | HI-LO - Closure Report |
| `docs/games/hi-lo/HI_LO_AI_QUICKSTART_2026-05-22.md` | 2026-05-22 | HI-LO - AI QuickStart |
| `docs/games/hi-lo/HI_LO_12_SURFACE_STATUS_2026-05-22.md` | 2026-05-23 | HI-LO - Preliminary 12-Surface Status |
| `docs/games/hi-lo/HI_LO_OPEN_QUESTIONS_2026-05-22.md` | 2026-05-22 | HI-LO - Open Questions And Stop-And-Ask Register |
| `docs/games/hi-lo/HI_LO_PRODUCT_DECISION_MAP_2026-05-22.md` | 2026-05-22 | HI-LO - Product Decision Map |
| `docs/games/hi-lo/HI_LO_PROJECT_METHOD_AND_EXECUTION_PLAN_2026-05-22.md` | 2026-05-22 | HI-LO - Project Method And Execution Plan |
| `docs/games/hi-lo/HI_LO_WAVE_PLAN.md` | 2026-05-23 | HI-LO - Wave Plan |
| `docs/games/hi-lo/MATH_SPEC.md` | 2026-05-23 | HI-LO - Math, RNG And Fairness Spec |
| `docs/games/hi-lo/SPEC.md` | 2026-05-22 | HI-LO - SPEC |
| `docs/games/hi-lo/SOURCE_INVENTORY_2026-05-22.md` | 2026-05-22 | HI-LO - Source Inventory |
| `docs/games/mines/MATH_SPEC.md` | 2026-05-18 | Mines - Math, RNG And Fairness Spec |
| `docs/LOCAL_ENV_RESTART_PROCEDURE.md` | 2026-05-10 | CasinoKing Local Environment Restart Procedure |
| `docs/md/INDEX.md` | 2026-05-04 | Markdown Mirrors Index |
| `docs/MINES_PENDING_TOPICS.md` | 2026-05-17 | Mines Pending Topics |
| `docs/MINES_PROVIDER_BOOTSTRAP_UX_PLAN.md` | 2026-05-15 | Mines Provider Bootstrap UX Plan |
| `docs/MINES_REPLAY_VIEWER_PLAN.md` | 2026-05-10 | Mines Replay Viewer Plan |
| `docs/MINES_SKIN_EXTENDED_CUSTOMIZATION_PLAN.md` | 2026-05-17 | CasinoKing - Mines skin extended customization plan |
| `docs/MINES_SKIN_X0_AUDIT.md` | 2026-05-17 | CasinoKing - Mines skin SKIN-X0 audit |
| `docs/MINES_SOUND_ASSETS_PLAN.md` | 2026-05-17 | Mines Sound Assets Plan |
| `docs/MINES_VISUAL_EFFECTS_PLAN.md` | 2026-05-10 | Mines Visual Effects Plan |
| `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_BOXE_2026-05-22.md` | 2026-05-22 | Next Game Backoffice Replication Brief - From BOXE Lessons |
| `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_HI_LO_2026-05-23.md` | 2026-05-23 | Next Game Backoffice Replication Brief - From HI-LO Lessons |
| `docs/NEXT_GAME_REPLICATION_BRIEF_FROM_HI_LO_2026-05-23.md` | 2026-05-23 | Next Game Replication Brief - From HI-LO Lessons |
| `docs/NEW_GAME_BRIEF_TEMPLATE.md` | 2026-05-19 | New Game Brief Template (v2) |
| `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` | 2026-05-23 | New Game Integration Playbook (v2) |
| `docs/OPEN_TOPICS_CTO_REVIEW_2026-05-24.md` | 2026-05-24 | Open Topics - CTO Review |
| `docs/PLATFORM_APPLICATION_LOGGING_CURRENT_STATE_CTO_REVIEW_2026-05-24.md` | 2026-05-24 | Platform Application Logging - Current-State CTO Review |
| `docs/PLATFORM_APPLICATION_LOGGING_CTO_REVIEW_2026-05-24.md` | 2026-05-24 | Platform Application Logging - CTO Review |
| `docs/PLATFORM_APPLICATION_LOGGING_PLAN_2026-05-24.md` | 2026-05-24 | Platform Application Logging Plan - CTO reviewed and corrected |
| `docs/PLATFORM_APPLICATION_LOGGING_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md` | 2026-05-25 | Platform Application Logging - Pre-Implementation Analysis |
| `docs/PLATFORM_REQUEST_ID_STRUCTURED_LOGGING_MVP_APPROACH_2026-05-25.md` | 2026-05-25 | Platform Request-ID And Structured Logging MVP - Implemented Approach |
| `docs/PLATFORM_ERROR_CODE_REGISTRY_CURRENT_STATE_CTO_REVIEW_2026-05-24.md` | 2026-05-24 | Platform Error Code Registry - Current-State CTO Review |
| `docs/PLATFORM_ERROR_CODE_REGISTRY_CTO_REVIEW_2026-05-24.md` | 2026-05-24 | Platform Error Code Registry - CTO Review |
| `docs/PLATFORM_ERROR_CODE_REGISTRY_PLAN_2026-05-24.md` | 2026-05-24 | Platform Error Code Registry Plan - CTO reviewed and corrected |
| `docs/PLATFORM_ERROR_REGISTRY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md` | 2026-05-25 | Platform Error Registry - Pre-Implementation Analysis |
| `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_BRIEF_2026-05-25.md` | 2026-05-25 | Platform Error / Request Foundation MVP Brief |
| `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_APPROACH_2026-05-25.md` | 2026-05-25 | Platform Error / Request Foundation MVP - Implemented Approach |
| `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_CURRENT_STATE_CTO_REVIEW_2026-05-24.md` | 2026-05-24 | Platform Financial Audit Traceability - Current-State CTO Review |
| `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_CTO_REVIEW_2026-05-24.md` | 2026-05-24 | Platform Financial Audit Traceability - CTO Review |
| `docs/PLATFORM_FINANCIAL_AUDIT_TRACEABILITY_PLAN_2026-05-24.md` | 2026-05-24 | Platform Financial Audit Traceability Plan - CTO reviewed and corrected |
| `docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md` | 2026-05-25 | Platform Financial Traceability - Pre-Implementation Analysis |
| `docs/PLATFORM_REPLAY_RETENTION_POLICY_2026-05-25.md` | 2026-05-25 | Platform Replay Retention Policy - MVP |
| `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_CURRENT_STATE_CTO_REVIEW_2026-05-24.md` | 2026-05-24 | Platform Installation Settings Backoffice - Current-State CTO Review |
| `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_CTO_REVIEW_2026-05-24.md` | 2026-05-24 | Platform Installation Settings Backoffice - CTO Review |
| `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_PLAN_2026-05-24.md` | 2026-05-24 | Platform Installation Settings Backoffice Plan - CTO reviewed and corrected |
| `docs/PLATFORM_SETTINGS_READONLY_INVENTORY_IMPLEMENTATION_2026-05-25.md` | 2026-05-25 | Platform Settings Read-Only Inventory - Implementation Note |
| `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_BRIEF_2026-05-25_CTOREVIEW.md` | 2026-05-25 | CTO Review - WP-ERROR-REQUEST-FOUNDATION-MVP |
| `docs/PLATFORM_APPLICATION_LOGGING_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md` | 2026-05-25 | CTO Review - WP-PLATFORM-REQUEST-ID-AND-STRUCTURED-LOGGING-MVP |
| `docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md` | 2026-05-25 | CTO Review - WP-FINANCE-REPLAY-REGISTRY-RETENTION |
| `docs/PLATFORM_SETTINGS_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md` | 2026-05-25 | CTO Review - WP-PLATFORM-SETTINGS-READONLY-INVENTORY |
| `docs/SKILL_GEMINI_NEW_GAME_ANALYSIS_PROMPT_2026-05-25.md` | 2026-05-25 | Skill Gemini v2 - Prompt per analisi nuovo gioco con checklist 25 Q + 12-surface |
| `docs/PLATFORM_OBSERVABILITY_ERROR_SETTINGS_CTO_REVIEW_2026-05-24.md` | 2026-05-24 | Platform Observability / Errors / Settings - Cross-plan CTO Orchestration |
| `docs/PLATFORM_PRE_IMPLEMENTATION_ANALYSIS_PACKET_2026-05-25.md` | 2026-05-25 | Platform Pre-Implementation Analysis Packet |
| `docs/PLATFORM_SETTINGS_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md` | 2026-05-25 | Platform Settings - Pre-Implementation Analysis |
| `docs/PLAYER_ACCOUNT_UX_REDESIGN_PLAN.md` | 2026-05-17 | Player Account UX Redesign Plan |
| `docs/PLAYER_LOBBY_UX_PLAN.md` | 2026-05-09 | CasinoKing - Player Lobby UX Plan |
| `docs/PRE_PRODUCTION_EXTERNAL_AUDIT_2026-05-21.md` | 2026-05-21 | CasinoKing - Pre-Production External Audit (4 scaling bottlenecks) |
| `docs/PRODUCT_CLOSURE_BACKLOG.md` | 2026-05-10 | CasinoKing Product Closure Backlog |
| `docs/PRODUCT_COPY_ENGLISH_CLEANUP_PLAN.md` | 2026-05-08 | CasinoKing - Product Copy English Cleanup Plan |
| `docs/PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md` | 2026-05-07 | CasinoKing - Product UX Execution Sequence Plan |
| `docs/PRODUCTION_READINESS_BRIEF.md` | 2026-05-07 | CasinoKing - Production Readiness Brief |
| `docs/PRODUCTION_READINESS_ROADMAP.md` | 2026-05-19 | CasinoKing — Production Readiness Roadmap |
| `docs/README.md` | 2026-05-23 | CasinoKing Documentation Map |
| `docs/ROUND_REPORTING_DISPLAY_ID_PLAN.md` | 2026-05-16 | CasinoKing - Round Reporting Display ID Plan |
| `docs/SECURITY_REVIEW_PRE_PRODUCTION_PLAN.md` | 2026-05-06 | CasinoKing - Security Review Pre-Production Plan |
| `docs/SESSION_RECOVERY_ENGINE_DESIGN.md` | 2026-05-17 | Session Recovery Engine Design |
| `docs/SITE_BANNER_AND_MOCKUP_PLAN.md` | 2026-05-17 | Site Banner And Mockup Plan |
| `docs/SITE_CMS_EDITORIAL_UX_PLAN.md` | 2026-05-09 | CasinoKing - Site CMS Editorial UX Plan |
| `docs/SITE_LOBBY_PUBLICATION_PLAN.md` | 2026-05-07 | CasinoKing - Site Lobby Publication Plan |
| `docs/SMOKE_LEGACY_FAILURE_INVENTORY_2026-05-17.md` | 2026-05-17 | Smoke Legacy Failure Inventory - 2026-05-17 |
| `docs/SOURCE_OF_TRUTH.md` | 2026-05-05 | CasinoKing – Source of Truth |
| `docs/TASK_EXECUTION_GUARDRAILS.md` | 2026-05-17 | CasinoKing - Task Execution Guardrails |

## Documenti completati di riferimento

| Document | Last meaningful update | Notes |
| --- | --- | --- |
| `docs/AUTH_CLEANUP_P0.md` | 2026-04-03 | Auth Cleanup (P0) - Login & Registrazione |
| `docs/AUTH_SEPARATION_PLAN.md` | 2026-04-09 | Piano di Refactoring: Separazione Logica Autenticazione Player e Admin |
| `docs/BACKOFFICE_GAMES_UX_REORGANIZATION_PLAN.md` | 2026-05-06 | CasinoKing - Backoffice Games UX Reorganization Plan |
| `docs/BETA_HOSTING_DECISION_MEMO_2026_04.md` | 2026-04-30 | CasinoKing - Beta Hosting Decision Memo |
| `docs/CATALOG_ENGINE_TITLE_SITE_PLAN.md` | 2026-05-04 | Catalogo Engine / Title / Site - Piano operativo Fase 1 |
| `docs/DEMO_MODE_PLAN.md` | 2026-05-05 | CasinoKing - Demo Mode Plan - Fase 6 |
| `docs/F7_C_GAMES_DETAIL_ROUTE_REFACTOR_PLAN.md` | 2026-05-08 | CasinoKing - F7-C Games Detail Route Refactor Plan |
| `docs/FINANCIAL_AREA_EXECUTION_PLAN.md` | 2026-04-12 | Piano Esecutivo: Area Finanziaria "Vista Banco" (EPIC 4) |
| `docs/FINANCIAL_UI_REFACTOR_PLAN.md` | 2026-04-12 | Piano di Refactoring: UI Area Finanziaria ("Vista Banco") |
| `docs/MASTER_LAUNCH_LEGACY_REMOVAL_PLAN.md` | 2026-05-07 | CasinoKing - Master Launch Legacy Removal Plan |
| `docs/md/CasinoKing_Documento_00_FINALE.md` | 2026-03-24 | CasinoKing – Documento 00 (Versione Finale) |
| `docs/md/CasinoKing_Documento_02_Fondazioni_Architettura.md` | 2026-03-24 | CasinoKing |
| `docs/md/CasinoKing_Documento_03_Architettura_DB_API.md` | 2026-03-24 | CasinoKing |
| `docs/md/CasinoKing_Documento_05_v3_Wallet_Ledger_Fondamenta_Definitive.md` | 2026-03-24 | CasinoKing – Documento 05 v3 |
| `docs/md/CasinoKing_Documento_06_Mines_Prodotto_Stati_Matematica_API.md` | 2026-03-24 | CasinoKing – Documento 06 |
| `docs/md/CasinoKing_Documento_07_v2_Mines_Matematica_Congelata.md` | 2026-03-24 | CasinoKing – Documento 07 v2 |
| `docs/md/CasinoKing_Documento_08_v2_Game_Tuning_Numerico.md` | 2026-03-24 | CasinoKing – Documento 08 v2 |
| `docs/md/CasinoKing_Documento_09_v2_Game_Engine_Testing.md` | 2026-03-24 | CasinoKing – Documento 09 v2 |
| `docs/md/CasinoKing_Documento_10_Fairness_Randomness_Seed_Audit.md` | 2026-03-24 | CasinoKing – Documento 10 |
| `docs/md/CasinoKing_Documento_11_v2_API_Contract_Allineato_v3.md` | 2026-03-24 | CasinoKing – Documento 11 v2 |
| `docs/md/CasinoKing_Documento_12_v3_Schema_Database_Definitivo.md` | 2026-03-24 | CasinoKing - Documento 12 v3 |
| `docs/md/CasinoKing_Documento_13_v3_SQL_Migrations_Definitivo.md` | 2026-03-24 | CasinoKing - Documento 13 v3 |
| `docs/md/CasinoKing_Documento_14_v2_Ambiente_Locale_Realtime_Policy.md` | 2026-03-24 | CasinoKing – Documento 14 v2 |
| `docs/md/CasinoKing_Documento_15_Piano_Implementazione.md` | 2026-03-24 | CasinoKing – Documento 15 |
| `docs/md/CasinoKing_Documento_20_Refiniture_Prodotto_Web_Player_Backoffice.md` | 2026-03-27 | CasinoKing - Documento 20 |
| `docs/md/CasinoKing_Documento_21_Vincoli_Priorita_Gioco_Mines.md` | 2026-03-27 | CasinoKing - Documento 21 |
| `docs/md/CasinoKing_Documento_22_Vincoli_Priorita_Sito_Web_Player.md` | 2026-03-27 | CasinoKing - Documento 22 |
| `docs/md/CasinoKing_Documento_23_Vincoli_Priorita_Backend_Piattaforma.md` | 2026-03-27 | CasinoKing - Documento 23 |
| `docs/md/CasinoKing_Documento_30_Separazione_Prodotti_Piattaforma_Gioco_Aggregatore.md` | 2026-03-27 | CasinoKing - Documento 30 |
| `docs/md/CasinoKing_Documento_31_Contratto_Tra_Platform_Backend_E_Mines_Backend.md` | 2026-03-27 | CasinoKing - Documento 31 |
| `docs/md/CasinoKing_Documento_32_Piano_Migrazione_Da_Monolite_Frontend_A_Prodotti_Separati.md` | 2026-03-27 | CasinoKing - Documento 32 |
| `docs/md/CasinoKing_Documento_33_Stato_Progetto_Analisi_CTO_Guida_Migrazione.md` | 2026-03-30 | CasinoKing - Documento 33 |
| `docs/md/CasinoKing_Documento_34_Contratto_API_Operativo_Platform_Mines_v1.md` | 2026-03-27 | CasinoKing - Documento 34 |
| `docs/md/CasinoKing_Documento_34_Mappatura_Codebase_Attuale_Vs_Target_Platform_Game.md` | 2026-04-02 | CasinoKing - Documento 34 |
| `docs/md/CasinoKing_Documento_35_Contratto_API_Operativo_Platform_Game_v1.md` | 2026-04-02 | CasinoKing - Documento 35 |
| `docs/md/CasinoKing_Documento_35_Mappatura_Codebase_Attuale_E_Split_Target.md` | 2026-03-30 | CasinoKing - Documento 35 |
| `docs/md/CasinoKing_Documento_36_CTO_Reading_Order_Esecutivo.md` | 2026-04-30 | CasinoKing - Documento 36 |
| `docs/md/CasinoKing_Documento_37_Catalogo_Engine_Title_Site.md` | 2026-05-04 | CasinoKing - Documento 37 |
| `docs/md/CasinoKing_Documento_38_Configurazione_Per_Title.md` | 2026-05-04 | CasinoKing - Documento 38 |
| `docs/md/FIDELITY_AUDIT.md` | 2026-03-24 | Fidelity Audit |
| `docs/MINES_COPY_LABELS_AND_I18N_READINESS_PLAN.md` | 2026-05-08 | CasinoKing - Mines Copy, Labels and i18n Readiness Plan |
| `docs/MINES_EXECUTION_PLAN.md` | 2026-04-02 | CasinoKing — Mines Execution Plan |
| `docs/MINES_EXTERNAL_GAME_AND_TABLE_SESSION_PLAN.md` | 2026-05-04 | Mines External Game + Table Session Plan |
| `docs/MINES_I18N_CTO_REVIEW_BRIEF.md` | 2026-05-08 | CasinoKing - Mines i18n CTO Review Brief |
| `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md` | 2026-05-08 | CasinoKing - Mines i18n Foundation Implementation Plan |
| `docs/MINES_I18N_STRING_INVENTORY.md` | 2026-05-19 | CasinoKing - Mines i18n String Inventory |
| `docs/MINES_IN_GAME_TITLE_PLAN.md` | 2026-05-08 | CasinoKing - Mines In-Game Title Plan |
| `docs/MINES_RUNTIME_STABILISATION_PLAN.md` | 2026-04-12 | Piano di Stabilizzazione Runtime Mines (EPIC 5) |
| `docs/RECOVERY_CAPABILITY_RECONCILIATION_2026-05-16.md` | 2026-05-17 | Recovery Capability Reconciliation - 2026-05-16 |
| `docs/THEME_SYSTEM_PLAN.md` | 2026-05-16 | CasinoKing - Theme system plan - Fase 5 |
| `docs/TITLE_CODE_PROPAGATION_PLAN.md` | 2026-05-04 | Title / Site code propagation - Piano operativo Fase 2 |
| `docs/TITLE_CONFIG_PLAN.md` | 2026-05-04 | Title configuration split - Piano operativo Fase 3 |
| `docs/TITLE_EDITOR_SHELL_PLAN.md` | 2026-05-06 | CasinoKing - Title Editor Shell Plan - Fase 7 |

## Archivio

Archived documents are not primary sources. Use them only to reconstruct history
or understand why a newer plan exists.

| Document | Status | Last meaningful update | Notes |
| --- | --- | --- | --- |
| `docs/archive/README.md` | ACTIVE | 2026-05-15 | CasinoKing Documentation Archive |
| `docs/archive/bug-notes/BUG_ANALYSIS_01.md` | HISTORICAL | 2026-04-30 | Analisi del Bug (Architect Mode) |
| `docs/archive/bug-notes/BUG_REGISTRATION_FAILED.md` | HISTORICAL | 2026-04-30 | Bug Report: Registration Failed (Failed to fetch) |
| `docs/archive/prompts/AI_ALIGNMENT_PROMPT.md` | HISTORICAL | 2026-04-30 | CasinoKing — AI Alignment Prompt |
| `docs/archive/prompts/CTO_REVIEW_PROMPT.md` | HISTORICAL | 2026-04-30 | CTO Review Prompt |
| `docs/games/boxe/ARCHITECTURE_ATLAS_BOXE_DRAFT.md` | HISTORICAL | 2026-05-18 | Redirect to active BOXE architecture atlas |
| `docs/archive/session-notes/ANALYSIS_NEXT_STEPS_P0.md` | HISTORICAL | 2026-04-30 | Architectural Analysis - Next Steps P0 (Apr 2026) |
| `docs/archive/session-notes/ANALYSIS_SESSIONS_AND_UI_P1.md` | HISTORICAL | 2026-04-30 | Analisi e Pianificazione: UI/UX & Paradigma Sessioni (P1) |
| `docs/archive/session-notes/CTO_MINES_ANALYSIS_2026_03_30.md` | HISTORICAL | 2026-04-02 | CasinoKing — CTO / Principal Engineer Analysis: MINES |
| `docs/archive/session-notes/EXECUTION_PLAN_APRIL_2026.md` | HISTORICAL | 2026-04-09 | Piano Esecutivo: Attività Aprile 2026 |
| `docs/archive/session-notes/mines_backoffice_i18n_notes.md` | HISTORICAL | 2026-03-29 | Mines Backoffice And I18n Notes |
| `docs/archive/session-notes/mines_future_ux_notes.md` | HISTORICAL | 2026-03-31 | Mines Future UX Notes |
| `docs/archive/session-notes/NEXT_STEPS_2026_03_31.md` | HISTORICAL | 2026-04-30 | CasinoKing — Prossimi Step (2026-03-31) |
| `docs/archive/session-notes/NEXT_STEPS_2026_04_02.md` | HISTORICAL | 2026-04-30 | Next Steps - CasinoKing Platform |
| `docs/archive/session-notes/NEXT_STEPS_2026_04_08.md` | HISTORICAL | 2026-04-09 | Next Steps: 8 Aprile 2026 |
| `docs/archive/session-notes/PROJECT_STATUS_2026_03_30.md` | HISTORICAL | 2026-04-30 | CasinoKing — Project Status (2026-03-30) |
| `docs/archive/superseded-plans/ARCH_CMS_VS_PLATFORM.md` | SUPERSEDED | 2026-04-02 | Superseded by docs/CMS_ROADMAP_AND_EXTERNAL_GAMES_PLAN.md |
| `docs/archive/superseded-plans/ARCHIVED_FINANCIAL_REPORT_REFACTOR_PLAN.md` | SUPERSEDED | 2026-04-30 | Superseded by docs/FINANCIAL_AREA_DESIGN.md and docs/ROUND_REPORTING_DISPLAY_ID_PLAN.md |
| `docs/archive/superseded-plans/CODE_REVIEW_CLEANUP_01.md` | SUPERSEDED | 2026-04-30 | Superseded by docs/README.md |
| `docs/archive/superseded-plans/EPIC_6_UI_REFACTOR_PLAN.md` | SUPERSEDED | 2026-04-12 | Superseded by docs/PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md |
| `docs/archive/superseded-plans/FINANCIAL_REPORT_REFACTOR_PLAN.md` | SUPERSEDED | 2026-04-30 | Superseded by docs/FINANCIAL_AREA_DESIGN.md and docs/ROUND_REPORTING_DISPLAY_ID_PLAN.md |
| `docs/archive/superseded-plans/I18N_FOUNDATION_DEFERRED_DECISION.md` | SUPERSEDED | 2026-05-08 | Superseded by docs/PRODUCT_COPY_ENGLISH_CLEANUP_PLAN.md and docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md |
| `docs/archive/superseded-plans/MINES_BOOT_2A_CTO_READY_PLAN.md` | SUPERSEDED | 2026-05-15 | Superseded by docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md and docs/MINES_PENDING_TOPICS.md |
| `docs/archive/superseded-plans/NEXT_EXECUTION_DETAILED_CTO_REVIEW_PLAN.md` | SUPERSEDED | 2026-05-16 | Superseded by docs/README.md and docs/ACTIVE_OPEN_LOOPS.md |
| `docs/archive/superseded-plans/NEXT_UX_SLICES_CTO_REVIEW_PLAN.md` | SUPERSEDED | 2026-05-07 | Superseded by docs/PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md |
| `docs/archive/superseded-plans/PLATFORM_GAME_CONTRACT_AND_ENVIRONMENTS_IMPLEMENTATION_BLUEPRINT_2026_04.md` | SUPERSEDED | 2026-04-30 | Superseded by docs/GAME_ARCHITECTURE_OVERVIEW.md and docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md |
| `docs/archive/superseded-plans/PLATFORM_GAME_M1_EXECUTION_PACKAGE_2026_04.md` | SUPERSEDED | 2026-04-30 | Superseded by docs/GAME_ARCHITECTURE_OVERVIEW.md and docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md |
| `docs/archive/superseded-plans/PLATFORM_GAME_M1_FILE_BY_FILE_EXECUTION_PLAN_2026_04.md` | SUPERSEDED | 2026-04-30 | Superseded by docs/GAME_ARCHITECTURE_OVERVIEW.md and docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md |
| `docs/archive/superseded-plans/PLATFORM_GAME_SEPARATION_AND_ENVIRONMENTS_MASTERPLAN_2026_04.md` | SUPERSEDED | 2026-04-30 | Superseded by docs/GAME_ARCHITECTURE_OVERVIEW.md and docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md |
| `docs/archive/superseded-plans/PRODUCT_COPY_AND_I18N_FOUNDATION_PLAN.md` | SUPERSEDED | 2026-05-06 | Superseded by docs/PRODUCT_COPY_ENGLISH_CLEANUP_PLAN.md and docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md |
| `docs/archive/superseded-plans/TECHNICAL_CLEANUP_PLAN_01.md` | SUPERSEDED | 2026-04-30 | Superseded by docs/README.md |
| `docs/archive/superseded-plans/TECHNICAL_CLEANUP_ROADMAP_FINAL.md` | SUPERSEDED | 2026-04-30 | Superseded by docs/README.md |
| `docs/archive/superseded-plans/UI_UX_ACTION_PLAN_P0.md` | SUPERSEDED | 2026-04-02 | Superseded by docs/PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md |
| `docs/archive/superseded-plans/UI_UX_BLUEPRINT_P0.md` | SUPERSEDED | 2026-04-02 | Superseded by docs/PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md |

## Binary And Data Artifacts

| Artifact | Status | Last meaningful update | Notes |
| --- | --- | --- | --- |
| `docs/casinoking_movimenti.xlsx` | HISTORICAL | 2026-05-10 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/md/assets/CasinoKing_Documento_02_Fondazioni_Architettura/image1.png` | COMPLETED | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/md/assets/CasinoKing_Documento_02_Fondazioni_Architettura/image2.png` | COMPLETED | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/md/assets/CasinoKing_Documento_02_Fondazioni_Architettura/image3.png` | COMPLETED | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/md/assets/CasinoKing_Documento_02_Fondazioni_Architettura/image4.png` | COMPLETED | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/md/assets/CasinoKing_Documento_03_Architettura_DB_API/image1.png` | COMPLETED | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/md/assets/CasinoKing_Documento_03_Architettura_DB_API/image2.png` | COMPLETED | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/md/assets/CasinoKing_Documento_03_Architettura_DB_API/image3.png` | COMPLETED | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/PROJECT_ROOT_TREE_EXPLAINED.csv` | ACTIVE | 2026-05-10 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/runtime/CasinoKing_Documento_07_Allegato_A_Payout_Table_Mines_v3.xlsx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/runtime/CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.csv` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/runtime/CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_00_FINALE.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_02_Fondazioni_Architettura.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_03_Architettura_DB_API.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_05_v3_Wallet_Ledger_Fondamenta_Definitive.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_06_Mines_Prodotto_Stati_Matematica_API.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_07_v2_Mines_Matematica_Congelata.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_08_v2_Game_Tuning_Numerico.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_09_v2_Game_Engine_Testing.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_10_Fairness_Randomness_Seed_Audit.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_11_v2_API_Contract_Allineato_v3.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_12_v3_Schema_Database_Definitivo.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_13_v3_SQL_Migrations_Definitivo.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_14_v2_Ambiente_Locale_Realtime_Policy.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
| `docs/word/CasinoKing_Documento_15_Piano_Implementazione.docx` | ACTIVE | 2026-03-24 | Binary/data artifact; status is indexed here because metadata cannot be written inside safely. |
