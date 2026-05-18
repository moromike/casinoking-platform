# CasinoKing — Capability Inventory

**Status**: ACTIVE  
**Last updated**: 2026-05-19 (WP-BOXE-CLOSURE capability inventory update)
**Purpose**: Single source of truth for all product capabilities, their operational status, and pointers to detail docs. Required reading before BOXE design.

---

## How to read this document

| Status | Meaning |
|--------|---------|
| STABLE | In production (demo), fully integrated end-to-end (DB/Backend/API/Admin/Player/CSS/Test) |
| WIP | Partially implemented or on a feature branch not yet on main |
| DEFERRED | Recognized as needed, explicitly postponed to production hardening |
| PLACEHOLDER | Module scaffolded, no logic implemented |

---

## 1. Authentication & Access

| Capability | Status | Notes |
|-----------|--------|-------|
| Player registration (email, name, fiscal code, phone) | STABLE | POST /auth/register |
| Player login / logout | STABLE | JWT-based, POST /auth/login, /auth/logout |
| Password reset flow (email token, 30min TTL) | STABLE | POST /auth/password/forgot + /reset |
| Password change (authenticated) | STABLE | POST /auth/password/change |
| Current user profile | STABLE | GET /auth/me |
| Demo player provisioning (anonymous token) | STABLE | POST /auth/demo → demo wallet |
| Admin login (role-based) | STABLE | POST /admin/auth/login, area-based RBAC |
| Admin password change | STABLE | POST /admin/auth/change-password |
| Force-close all player game sessions | STABLE | POST /admin/users/{id}/force-close-sessions |
| Access log (IP, role, email, timestamp) | STABLE | GET /admin/access-logs |
| Admin audit trail | STABLE | GET /admin/audit-log |
| Admin audit log filters and detail view | STABLE | Backoffice LOG area filters by action/resource/admin/date and shows payload JSON detail |

**Detail docs**: docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md (launch auth), docs/BACKOFFICE_MANUAL.md § Admin Management

---

## 2. Wallet & Ledger

| Capability | Status | Notes |
|-----------|--------|-------|
| Multi-wallet per player (cash + bonus) | STABLE | wallet_accounts table; GET /wallets |
| Real-time wallet balance snapshot | STABLE | GET /wallets/{wallet_type} |
| Double-entry ledger (transactions + entries) | STABLE | ledger_accounts, ledger_transactions, ledger_entries |
| Player statement history (paginated, filterable) | STABLE | GET /account/statement-movements; category/wallet/period filters |
| Statement movement detail (line items) | STABLE | GET /account/statement-movements/{id} |
| Admin wallet adjustment (debit/credit) | STABLE | POST /admin/wallet-adjustments/{user_id} |
| Admin bonus grant | STABLE | POST /admin/bonus-grants/{user_id} |
| Wallet segregation (cash vs bonus) | STABLE | wallet_source routing in game launch |
| Crypto payment system | DEFERRED | Michele preference: blockchain direct (BTC/ETH/Ripple), no gateway; deferred to production |
| Top-up flow (player-side) | STABLE | LaunchCashierModal in player lobby; read-only /wallets |

**Detail docs**: docs/BACKOFFICE_MANUAL.md § Finance, docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md

---

## 3. Admin Backoffice

| Capability | Status | Notes |
|-----------|--------|-------|
| Player list with filtering | STABLE | GET /admin/users |
| Player detail + financial summary | STABLE | GET /admin/users/{id} |
| Player account suspension | STABLE | POST /admin/users/{id}/suspend |
| Admin player password reset | STABLE | POST /admin/users/{id}/password/reset |
| Financial session report (paginated) | STABLE | GET /admin/financial/sessions |
| Session detail with transaction events | STABLE | GET /admin/financial/sessions/{session_id} |
| Ledger balance report by account | STABLE | GET /admin/ledger/report |
| Admin RBAC (superadmin + area permissions) | STABLE | admin_areas: finance, mines |
| Operational audit log UI | STABLE | `AdminAuditLog` panel with filters, pagination, event table and JSON detail |
| Backoffice UI in English (hardcoded, no i18n infra) | STABLE | Merged 2026-05-17 (A1 branch) |
| Backoffice operational manual | STABLE | docs/BACKOFFICE_MANUAL.md (1438 lines, 10 sections) |
| Reporting dashboard (player behavior, retention) | DEFERRED | Awaiting real players in production |

**Detail docs**: docs/BACKOFFICE_MANUAL.md

---

## 4. Game Catalog & Platform Infrastructure

| Capability | Status | Notes |
|-----------|--------|-------|
| Game title management (create, archive, restore) | STABLE | game_titles table; admin UI Games tab |
| Title publication to site lobby (draft/live) | STABLE | site_title_publications; demo/real enablement per title |
| Title duplication | STABLE | Admin UI: duplicate Mines title |
| Game library (player-facing, with game_card asset) | STABLE | GET /games/library; LEFT JOIN title_assets WHERE kind='game_card' |
| Game card lobby asset (upload/delete/preview, 300KB PNG/JPEG/WebP) | STABLE | GameCardAssetEditor in admin; restored WP-1 2026-05-17 |
| Title theme management (tokens, save draft, publish) | STABLE | title_themes; isThemeLoaded gate added WP-2 |
| Title i18n / locale bundle management | STABLE | title_locales; admin i18n editor |
| Access sessions (game context per player session) | STABLE | POST /access-sessions; ping, close |
| Table sessions (budgeted play) | STABLE | table_sessions; wallet type integration |
| Table session API endpoints | STABLE | POST/GET/close/limits via `/table-sessions`; integration tests cover reserve/consume/release |
| Game launch token (demo/preview/real modes) | STABLE | POST /games/mines/launch-token + /launch/validate |
| Platform rounds tracking | STABLE | platform_rounds table |
| Asset registry (upload, delete, version, metadata) | STABLE | title_assets, site_assets tables |
| Title asset registry endpoints | STABLE | `/admin/titles/{title_code}/assets` list/upload/delete; contract + integration coverage |

**Detail docs**: docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md

---

## 5. Mines Game

| Capability | Status | Notes |
|-----------|--------|-------|
| Game session lifecycle (start/reveal/cashout/resume) | STABLE | Idempotent start/cashout with Idempotency-Key header; real-mode resume uses the persisted session `title_code`, including published variants |
| Configurable grid sizes (e.g., 3×3, 5×5) | STABLE | mines_config; admin Grid & Mines config tab |
| Configurable mine counts per grid | STABLE | Managed per title in admin |
| Server-authoritative randomness | STABLE | mines_seeds table; server seed + client seed |
| Provable fairness (seed rotation, public proof) | STABLE | GET /games/mines/fairness; POST /fairness/rotate (superadmin) |
| Session replay | STABLE | GET /games/mines/session/{id}/replay |
| Fairness verification (admin) | STABLE | GET /games/mines/verify |
| Session history (player, paginated) | STABLE | GET /games/mines/sessions |
| Demo mode | STABLE | Demo launch token, isolated wallet |
| Multi-wallet support (cash / bonus routing) | STABLE | wallet_source param on /games/mines/start |
| Visual theme (color tokens, board icons, sounds) | STABLE | mines-theme-editor, board-assets-editor, sound-assets-editor |
| Runtime sound assets per Title | STABLE | `audio_safe_reveal`, `audio_mine_hit`, `audio_collect`, `audio_win`; backoffice Sounds tab + `useMinesSounds` runtime hook |
| Mines runtime tools | STABLE | Info/replay modal, clock, FX mute/volume controls in `mines-runtime-tools.tsx`; no core outcome logic |
| Mines i18n admin editor | STABLE | Copy/rules editor backed by `MINES_COPY_MANIFEST`, locale defaults and publish validation |
| Provider bootstrap and How To Play gates | STABLE | Provider intro preload/skip and How To Play gate mounted by `GameBootDecisionFlow`; covered by boot/visual smoke |
| Theme empty state / load gate | STABLE | isThemeLoaded gate added WP-2 2026-05-17 |
| i18n string bundle (19 launch_cashier.* keys) | STABLE | mines-copy-manifest.ts + mines-copy-defaults.ts |
| Mines backoffice config editor | STABLE | mines-backoffice-editor.tsx; 7 sub-tabs |
| Launch Cashier modal (wallet picker, lobby → game) | STABLE | LaunchCashierModal, restored WP-3 2026-05-17 |
| Player lobby game card (button → cashier) | STABLE | PlayerGameCard as <button>, restored WP-3 |
| Lobby hero slot CTA → cashier | STABLE | LobbyHomeSlotHero CTA opens cashier |
| Mobile portrait viewport contract | STABLE | Portrait 375x667 remains playable with a >=200 px board contract; 216 px measured rendering accepted by product decision 2026-05-17 |
| Mobile landscape-short rotation gate | STABLE | `GameShortViewportGate` blocks landscape-short gameplay below 400 px height and clears when the player rotates back to portrait/playable height |
| Legacy browser smoke tests | STABLE | WP-SMOKE-1/2/3 closed all 11 legacy failures; full Mines browser smoke is green again |

**Detail docs**: docs/ARCHITECTURE_ATLAS_MINES.md, docs/MINES_PENDING_TOPICS.md

---

## 6. BOXE Game

| Capability | Status | Notes |
|-----------|--------|-------|
| Game rules SPEC | STABLE | `docs/games/boxe/SPEC.md` with 11 closure blocks. |
| Math/RNG/fairness | STABLE | Log-lerp multiplier formula, deterministic server seed/client seed/nonce. |
| Math certification material | STABLE | `docs/games/boxe/MATH_SPEC.md`, simulator and stress framework. |
| BOXE schema | STABLE | `boxe_sessions`, `boxe_rounds`, `boxe_picks`, `boxe_idempotency_keys`. |
| BOXE repository | STABLE | Round/session/pick CRUD, per-round locking and idempotency storage. |
| BOXE state machine | STABLE | 9 states including cashout, top-row, failed mine, expired and quarantined. |
| BOXE API endpoints | STABLE | Config/start/reveal/cashout/session/replay/sessions. |
| POST idempotency | STABLE | Required Idempotency-Key with replay/conflict semantics. |
| Game adapter integration | STABLE | Consumes game-agnostic platform adapter with `game_code="boxe"`. |
| Demo isolation | STABLE | Demo creates BOXE-owned state only; no wallet/ledger/platform round mutation. |
| Real cash and bonus settlement | STABLE | Platform round debit/settlement through wallet/ledger adapter. |
| Finance drilldown | STABLE | BOXE rounds visible in admin financial sessions with game-specific extras. |
| Player statement/history | STABLE | BOXE labels and details exposed through account statement. |
| Replay payload | STABLE | Terminal-only replay with fairness artifacts and no active hidden-state leak. |
| Backend i18n manifest | STABLE | Required copy keys validated for `it`, `en`, `de`, `es`. |
| Standalone route `/boxe` | STABLE | Uses shared Game Runtime shell and BOXE namespace. |
| Frontend gameplay | STABLE | Pyramid board, settings, payout ladder, bet/collect panel, retry UX. |
| Frontend animations/audio hooks | STABLE | Reveal/loss/win polish, reduced motion and silent/default audio hooks. |
| BOXE admin config/copy/rules | STABLE | Title Editor plugin with draft/publish, validation and audit. |
| BOXE assets/theme admin | STABLE | Assets and Theme tabs; reuses `game_card`, `symbol_safe`, `symbol_mine`. |
| Catalog seed | STABLE | Engine `boxe`, master `boxe`, variant `boxe001`. |
| Site/lobby launch | STABLE | Lobby publication and Launch Cashier demo/real/bonus routing. |
| Visual regression baseline | STABLE | BOXE 3C visual baseline plus E2E validation. |
| Manual playthrough checklist | STABLE | `docs/games/boxe/MANUAL_PLAYTHROUGH_CHECKLIST.md`. |

**Detail docs**: docs/ARCHITECTURE_ATLAS_BOXE.md, docs/games/boxe/SPEC.md, docs/games/boxe/MATH_SPEC.md, docs/games/boxe/CLOSURE_REPORT.md

---

## 7. Game Runtime Shell (platform-level)

| Capability | Status | Notes |
|-----------|--------|-------|
| GameBootShell (launch orchestration) | STABLE | game-runtime/game-boot-shell.tsx; on main |
| GameBootDecisionFlow (state machine composer) | STABLE | On main after BOOT-2A.6; composer receives booleans and ReactNode children |
| GameProviderIntroGate (video brand reveal) | STABLE | On main after BOOT-2A.6; MP4 8s moromike lab common to all games |
| GameHowToPlayGate (how-to overlay, contents as prop) | STABLE | On main after BOOT-2A.6; game-specific content injected as children |
| GameTableBalanceGate (wallet picker, limits as prop) | STABLE | On main after BOOT-2A.6; game-specific limits injected as props/children |
| Audio preferences (useGameAudioPreferences) | STABLE | On main (BOOT-2A.3) |
| Game storage (useGameLaunchContext) | STABLE | On main |
| Theme provider | STABLE | On main |
| History/replay infra | STABLE | On main via mines session replay |
| Contract test: game-runtime/* never imports mines/* | STABLE | tests/contract/test_game_runtime_frontend_boundary.py |

**Detail docs**: docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md

---

## 8. Site CMS

| Capability | Status | Notes |
|-----------|--------|-------|
| Homepage slot management (content blocks) | STABLE | home_slots table; site-home-slots-panel.tsx |
| Site asset management (banners, images) | STABLE | site_assets; upload/delete |
| Site homepage banner asset endpoints | STABLE | `/admin/sites/{site_code}/assets` list/upload/delete; `homepage_banner` only, 2 MB cap, 1280 x 720 recommended |
| Draft/publish workflow for homepage slots | STABLE | Draft → Publish live |
| Lobby title publication (demo/real toggle) | STABLE | site-lobby-publication-panel.tsx |
| Lobby title ordering | STABLE | site-lobby-summary.tsx |
| CMS advanced (multi-page, structured content) | DEFERRED | Post-BOXE; Michele acknowledged need 2026-05-17 |

**Detail docs**: docs/BACKOFFICE_MANUAL.md § Site / Lobby

---

## 9. Reporting & Analytics

| Capability | Status | Notes |
|-----------|--------|-------|
| Financial session report (admin) | STABLE | GET /admin/financial/sessions |
| Ledger balance report by account | STABLE | GET /admin/ledger/report |
| Player behavior dashboard (retention, conversion) | DEFERRED | Awaiting real players in production |

---

## 10. Promotions

| Capability | Status | Notes |
|-----------|--------|-------|
| Bonus grant (manual, admin-only) | STABLE | POST /admin/bonus-grants/{id}; credited to bonus wallet |
| Promotion workflow (automated rules engine) | PLACEHOLDER | promotions/ module scaffolded; no logic |

---

## 11. Infrastructure & Quality

| Capability | Status | Notes |
|-----------|--------|-------|
| Docker Compose stack (FastAPI + Next.js + PostgreSQL + Redis) | STABLE | Local dev only; not production-deployed |
| Database migrations (SQL, 39 total) | STABLE | Alembic-managed; auto-applied on startup |
| Health checks (live + ready) | STABLE | /api/v1/health/live, /api/v1/health/ready |
| Test suite (60+ files: unit/contract/integration/concurrency) | STABLE | Core suites exist; legacy Mines browser smoke is green; two pre-existing contract failures remain tracked separately |
| Visual regression baseline (mines_classic) | STABLE | Read-only, stabile; used in CI |
| Linting/formatting enforcement | WIP | WP-CLEAN-2 removed unused code; no general formatter/linter enforcement was introduced |

---

## Capability count summary

| Domain | STABLE | WIP | DEFERRED | PLACEHOLDER |
|--------|--------|-----|----------|-------------|
| Auth & Access | 12 | 0 | 0 | 0 |
| Wallet & Ledger | 9 | 0 | 1 | 0 |
| Admin Backoffice | 11 | 0 | 1 | 0 |
| Game Catalog & Platform | 14 | 0 | 0 | 0 |
| Mines Game | 24 | 0 | 0 | 0 |
| BOXE Game | 24 | 0 | 0 | 0 |
| Game Runtime Shell | 10 | 0 | 0 | 0 |
| Site CMS | 6 | 0 | 1 | 0 |
| Reporting | 2 | 0 | 1 | 0 |
| Promotions | 1 | 0 | 0 | 1 |
| Infrastructure | 6 | 1 | 0 | 0 |
| **TOTAL** | **119** | **1** | **4** | **1** |

---

## WIP resolution plan

| WIP Capability | Blocking? | Resolution |
|----------------|-----------|------------|
| Linting/formatting | Non-blocking | Decide whether to add dedicated lint/formatter tooling in a future cleanup WP |

## DEFERRED resolution plan

| Deferred Capability | Unlock condition |
|--------------------|-----------------|
| Crypto payment system | Pre-launch production; architecture decision on chain |
| Player behavior dashboard | After real players in production |
| CMS advanced | Post-BOXE |
| Registration wizard extended (KYC, country) | Pre-launch production |

---
