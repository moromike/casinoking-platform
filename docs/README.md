Status: ACTIVE
Last meaningful update: 2026-05-25

# CasinoKing Documentation Index

This is the operational entry point for humans and AI working on CasinoKing.
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

## Da Fare Subito - In Attesa Di Michele

Pending product decisions che bloccano l'avanzamento di un workstream. Da chiudere prima
di entrare in fase implementativa.

| Data apertura | Tema | Cosa serve da Michele | Dove |
| --- | --- | --- | --- |
| 2026-05-25 | COINS - nuovo gioco proprietario, Fase 0 | 25 Q product + round 2 follow-up chiusi 2026-05-25 sera. Prerequisiti stretti Rule 18 registry ed embed parity implementati in workspace; resta il gate/commit prima di Fase 1 COINS. | `docs/games/coins/COINS_OPEN_QUESTIONS_2026-05-25.md` |
| 2026-05-25 | WP-FINANCE-REPLAY-REGISTRY-RETENTION (prerequisito COINS) | CTO review completata 2026-05-25 sera. WP platform più ampio: registry + settlement taxonomy + forward metadata + Mines admin replay parity + BOXE wallet bug + retention doc. Subset COINS-specific superseded. | `docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md` |
| 2026-05-25 | WP-ERROR-REQUEST-FOUNDATION-MVP | Implementazione chiusa in workspace: request/support id middleware, AppError/registry MVP, central handlers, frontend diagnostic line e test contrattuali. | `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_APPROACH_2026-05-25.md` |
| 2026-05-25 | WP-PLATFORM-REQUEST-ID-AND-STRUCTURED-LOGGING-MVP | CTO review completata. Approve with mandatory corrections. Ora sbloccato da Error Foundation; prossimo WP sequenziale. | `docs/PLATFORM_APPLICATION_LOGGING_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md` |
| 2026-05-25 | WP-PLATFORM-SETTINGS-READONLY-INVENTORY | CTO review completata. Approve with mandatory corrections. Parallelo a WP2/WP3 (slice S1-S3 indipendenti). | `docs/PLATFORM_SETTINGS_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md` |
| 2026-05-25 | WP-EMBED-MODE-PARITY-BOXE-HILO (prerequisito COINS) | Implementato in workspace: `useGameEmbedBridge(gameCode)` + Mines/BOXE/HI-LO consume. Audit: `docs/games/coins/EMBED_MODE_PARITY_AUDIT_2026-05-25.md`. | `docs/games/coins/PROMPT_CODEX_WP_EMBED_MODE_PARITY_2026-05-25.md` |

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
CMS v2 rescue, HI-LO current multiplier), read
`docs/OPEN_TOPICS_CTO_REVIEW_2026-05-24.md`.

For any task that touches game financial reporting, player/admin replay,
account history, ledger explanations, or a new game's reporting adapter, read
`docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md`.

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
| `docs/ACTIVE_OPEN_LOOPS.md` | 2026-05-25 | CasinoKing Active Open Loops |
| `docs/AI_CRITICAL_JUDGMENT_RULES.md` | 2026-05-10 | AI Critical Judgment Rules |
| `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md` | 2026-05-21 | CasinoKing - Architecture Atlas Game Runtime |
| `docs/ARCHITECTURE_ATLAS_BOXE.md` | 2026-05-21 | BOXE - Architecture Atlas |
| `docs/ARCHITECTURE_ATLAS_MINES.md` | 2026-05-21 | CasinoKing - Architecture Atlas Mines |
| `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md` | 2026-05-17 | CasinoKing - Architecture Atlas Platform + Frontend |
| `docs/ASSET_REGISTRY_PLAN.md` | 2026-05-17 | CasinoKing - Asset registry plan - Fase 4 |
| `docs/BACKOFFICE_MANUAL.md` | 2026-05-18 | CasinoKing Backoffice Manual |
| `docs/BOOT_2A_BRANCH_AUDIT_2026-05-17.md` | 2026-05-17 | BOOT-2A Branch Audit - 2026-05-17 |
| `docs/BOXE_PROJECT_BRIEF.md` | 2026-05-19 | BOXE - Project Brief |
| `docs/CAPABILITY_INVENTORY_2026-05-17.md` | 2026-05-19 | CasinoKing Capability Inventory |
| `docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md` | 2026-05-23 | CasinoKing - Code Architecture Mermaid Map |
| `docs/CMS_0_ADMIN_CMS_INVENTORY.md` | 2026-05-09 | CMS-0 Admin CMS Inventory |
| `docs/CMS_ROADMAP_AND_EXTERNAL_GAMES_PLAN.md` | 2026-05-10 | CMS Roadmap And External Games Plan |
| `docs/CMS_V2_MODULE_COMPOSER_PLAN.md` | 2026-05-23 | CasinoKing - CMS v2 Module Composer Plan |
| `docs/DOCUMENTATION_MAINTENANCE.md` | 2026-05-17 | CasinoKing - Documentation Maintenance |
| `docs/E2E_MANUAL_SMOKE_PLAN.md` | 2026-05-07 | CasinoKing - E2E Manual Smoke Plan |
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
| `docs/games/coins/PLATFORM_REGISTRY_AUDIT_2026-05-25.md` | 2026-05-25 | COINS prerequisito - Platform Registry Audit for account/finance/replay |
| `docs/games/coins/EMBED_MODE_PARITY_AUDIT_2026-05-25.md` | 2026-05-25 | COINS prerequisito - Embed Mode Parity Audit for BOXE/HI-LO |
| `docs/games/coins/PROMPT_CODEX_WP_FINANCE_REPLAY_REGISTRY_2026-05-25.md` | 2026-05-25 | COINS prerequisito - Prompt Codex WP-FINANCE-REPLAY-ACCOUNT-REGISTRY |
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
| `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_CURRENT_STATE_CTO_REVIEW_2026-05-24.md` | 2026-05-24 | Platform Installation Settings Backoffice - Current-State CTO Review |
| `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_CTO_REVIEW_2026-05-24.md` | 2026-05-24 | Platform Installation Settings Backoffice - CTO Review |
| `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_PLAN_2026-05-24.md` | 2026-05-24 | Platform Installation Settings Backoffice Plan - CTO reviewed and corrected |
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
