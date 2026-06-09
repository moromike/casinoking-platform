Status: ACTIVE
Last meaningful update: 2026-05-30

# Site V3 - Game Module Externalization Plan

## 0. Purpose

This document answers a specific architectural point: when we say that Mines,
BOXE and HI-LO now live under Site V3 runtime routes, we are describing today's
local deployment, not a permanent product boundary.

The long-term goal is that proprietary games can become installable game
modules. A module may run inside CasinoKing, inside another platform we build,
or behind an integration owned by a third party. The host site can be
CasinoKing or not.

## 1. Current State

CasinoKing is currently a modular monolith:

| Layer | Current physical placement | Logical owner |
| --- | --- | --- |
| Public site, login, registration, account, game shell | `frontend-v3` | Platform/Site V3 |
| Game frontend runtimes | `frontend-v3/app/runtime/{game}` and `frontend-v3/app/ui/{game}` | Game module |
| Shared frontend game boot shell | `frontend-v3/app/ui/game-runtime` | Platform/game boundary |
| Backend APIs, wallet, ledger, catalog, admin | `backend` | Platform |
| Game engines/APIs | `backend` game modules | Game module |
| V1/V2 frontend services | removed from local stack/source | none |

This is acceptable for the current product because module boundaries are
logical and tested. It is not yet a portable product distribution because:

- there is no separate game package manifest;
- there is no HTTP Platform Adapter contract;
- there is no external host integration SDK;
- backend game modules still run in the same backend process as the platform;
- frontend game runtimes are deployed from `frontend-v3`, even though they are
  logically game-owned.

## 2. Boundary Rules

The platform owns:

- player and admin identity;
- wallet, ledger, settlement, financial audit and reconciliation;
- catalog, Engine/Title/Site publication and lobby visibility;
- launch tokens, access sessions, table sessions and platform rounds;
- player account, finance and operational audit surfaces;
- Site CMS pages, module composition and public shell URLs.

The game module owns:

- game engine and state machine;
- RNG/fairness model;
- board/card/pyramid mechanics;
- payout potential and current collectible exposure;
- game-specific API actions;
- game-specific replay payload and renderer;
- title config schema, player copy, runtime assets and theme consumption;
- gameplay UI and responsive board layout.

The integration boundary owns:

- launch/session contract;
- Game Adapter settlement contract;
- replay/reporting descriptor contract;
- asset/theme/i18n manifest contract;
- embed/close/fullscreen/return contract;
- security, correlation id and observability contract.

## 3. Target Integration Model

Future portable proprietary games should support this model:

```text
Host Site
  -> Launch API / SDK
  -> iframe or web runtime
  -> Game Module Runtime
     -> Game Service or in-process game package
        -> Platform Adapter
           -> host platform wallet/ledger/session/audit
```

CasinoKing can be one host. A different site can be another host if it
implements the same adapter contract.

## 4. Required Contracts

### Launch Contract

The host creates a launch intent and passes a short-lived launch token to the
game runtime.

Minimum payload:

- player reference or anonymous demo identity;
- site code;
- title code;
- game code;
- mode: demo, real cash, real bonus or future approved mode;
- wallet source hint;
- return URL;
- locale;
- correlation id.

### Runtime Embed Contract

The host embeds the runtime and receives lifecycle messages.

Minimum messages:

- game requests close/return;
- host reports fullscreen state;
- runtime reports fatal launch failure;
- runtime reports optional telemetry events without financial authority.

### Action API Contract

Each game exposes game-specific actions. The contract must still guarantee:

- server-authoritative outcome;
- idempotent mutating actions;
- no frontend-calculated payout authority;
- deterministic replay after closure;
- clear error codes mapped to player copy.

### Platform Adapter Contract

The game never writes wallet or ledger directly.

Required conceptual operations:

- `open_round`;
- `settle_win`;
- `settle_loss`;
- `void_round`;
- `get_table_session_state`;
- `close_or_timeout_session` with game-specific settlement policy.

### Replay And Reporting Contract

Every game must provide:

- player account descriptor;
- admin finance descriptor;
- replay endpoint;
- replay viewer adapter;
- replay retention policy;
- round summary fields for account and finance.

### Assets, Theme And I18n Contract

Every game module must declare:

- asset kinds, formats, size limits and render modes;
- theme tokens it consumes;
- copy manifest keys and supported locales;
- default copy fallback policy;
- admin editor schema for title config/copy/assets/theme.

## 5. Work Packages

### GMP-0 - Coupling Inventory

Status: completed read-only on 2026-05-30 in
`docs/SITE_V3_GMP0_COUPLING_INVENTORY_2026-05-30.md`.

Inventory current Mines, BOXE and HI-LO coupling to CasinoKing-specific platform
code. Classify every coupling as:

- intended platform adapter use;
- acceptable host shell use;
- game-owned implementation;
- portability blocker.

Gate: no production code changes.

### GMP-1 - Public Game Module Contract

Status: completed contract-first on 2026-05-30 in
`docs/SITE_V3_GMP1_GAME_MODULE_INTEGRATION_CONTRACT_2026-05-30.md`.

Write the versioned integration contract:

- launch/session payloads;
- adapter operations;
- replay/reporting descriptor;
- asset/theme/i18n manifest;
- embed messages;
- error taxonomy;
- security and correlation-id requirements.

Gate: CTO review/owner approval before implementation.

### GMP-2 - Adapter Interface Extraction

Implemented first slice: typed adapter interfaces plus BOXE in-process adapter
facade. The current implementation remains in-process.

Gate: no backend behavior change, no wallet/ledger semantic change.

### GMP-3 - Host-Neutral Launch/Storage/Replay Proof

Status: implemented on 2026-05-30 in
`docs/SITE_V3_GMP3_HOST_NEUTRAL_LAUNCH_PROOF_2026-05-30.md`.

BOXE launch now emits host-neutral launch/storage/embed/replay descriptors and
a mock non-CasinoKing site can issue a BOXE demo launch token without moving
the service.

Gate: all existing product and replay tests still pass.

### GMP-4 - Packaging Or Service Decision

Status: decided on 2026-05-30 in
`docs/SITE_V3_GMP4_PACKAGING_SERVICE_DECISION_2026-05-30.md`.

Decision: package-first, service-later.

The selected path is a same-repo game module manifest/package boundary first,
then a mock non-CasinoKing host integration kit. Separate frontend runtime
package and separate backend game service/RGS mock are deferred until their
specific gates are green.

### GMP-5 - Host Integration Kit

Status: first slice plus GMP-5B backend launch authority slice implemented on 2026-05-30 in
`docs/SITE_V3_GMP5_MOCK_HOST_INTEGRATION_KIT_2026-05-30.md`.

Build a local mock host path that is not CasinoKing-branded and launches the
chosen game through the contract.

Gate: the game can run from the mock host without importing account, CMS,
CasinoKing lobby or backoffice UI.

First slice result: a public read-only BOXE manifest endpoint and integration
test prove that a mock non-CasinoKing site can read the manifest and issue a
BOXE demo launch whose storage/embed/replay descriptors match the manifest.

GMP-5B result: `POST /games/boxe/launch-token` issues BOXE real launch tokens,
and `POST /games/boxe/start` now validates an optional real
`X-Game-Launch-Token`. When present, the token owns `title_code` and
`site_code`; legacy no-token BOXE starts remain compatible until the runtime
sends the token.

### GMP-6 - Admin Module Registration

Define how a host registers a game module in its own admin:

- Engine/Title config schema;
- asset kinds;
- copy manifest;
- publish lifecycle;
- test/preview launch;
- finance/replay descriptor.

Gate: no arbitrary code injection from admin.

## 6. Non-Negotiables

- No game module directly mutates wallet, ledger, settlement or financial audit.
- No host site gets hidden game-specific financial shortcuts.
- No CasinoKing brand, account URL, CMS route or backoffice route may be
  hardcoded inside portable game runtime code.
- Demo and real money remain separate.
- Replay must remain deterministic and available through account/finance.
- Every visible runtime string stays in the game copy manifest.
- Every portable game has explicit mobile, replay, audio and multilingual QA.
- The first portable slice is contract-first, not a rewrite.

## 7. Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Current V3 runtime placement | none | unchanged | existing game APIs | none | `/runtime/{game}` iframe | existing | contract/browser | runtime extraction contract | Green | Deployment placement only, not permanent ownership. |
| Portable game module contract | none | none yet | defined in GMP-1 | none yet | none yet | none | future implementation tests | GMP-1 contract | Designed | Completed contract-first; requires CTO review before code. |
| BOXE in-process Platform Adapter | none | typed adapter + BOXE facade | unchanged | none | unchanged | unchanged | contract + BOXE API | GMP-2 implementation doc | Green first slice | No package/service split; preserves wallet/ledger/settlement/RNG/fairness/payout. |
| Host-neutral launch/storage/replay proof | none | descriptor builder + launch service | launch descriptors added | none | unchanged | unchanged | contract + integration | GMP-3 implementation doc | Green | Mock non-CasinoKing BOXE demo launch proof passed. |
| GMP-4 packaging/service decision | none | none | none | none | none | none | doc review | GMP-4 decision | Decided | Package-first, service-later. No physical split in GMP-4. |
| Platform Adapter HTTP/service split | none yet | future | future | none | none | none | future | future WP | Deferred | Do not implement before HTTP adapter, idempotency, timeout and reconciliation gates. |
| Mock non-CasinoKing host | temporary test site row | manifest endpoint + demo launch proof | `/game-modules/boxe/manifest` + `/demo/launch` | none | none | none | contract + integration | GMP-5 doc | Green first slice | Proves manifest/descriptor launch contract. |
| BOXE launch authority hardening | none | optional token validation in BOXE start; `site_code` propagated to session/round/platform round | `POST /games/boxe/launch-token`, optional `X-Game-Launch-Token` on `/games/boxe/start` | none | future runtime token send | none | integration | GMP-5 doc | Green backend first slice | Strict token requirement and demo action-token path deferred. |

## 8. Immediate Next Step

GMP-2, GMP-3, GMP-4, GMP-5 first slice and GMP-5B backend slice are complete for the current
decision path:

- `docs/SITE_V3_GMP2_BOXE_IN_PROCESS_ADAPTER_2026-05-30.md`;
- `docs/SITE_V3_GMP3_HOST_NEUTRAL_LAUNCH_PROOF_2026-05-30.md`;
- `docs/SITE_V3_GMP4_PACKAGING_SERVICE_DECISION_2026-05-30.md`;
- `docs/SITE_V3_GMP5_MOCK_HOST_INTEGRATION_KIT_2026-05-30.md`.

Next, run GMP-5C as runtime launch-context consumption for BOXE:

```text
Implement GMP-5C runtime launch-context consumption for BOXE. Pass the
host-neutral launch descriptor/token from shell to runtime without changing
gameplay layout, make real BOXE starts send X-Game-Launch-Token, keep no-token
legacy fallback during migration, and design the demo-token action path
separately. Do not touch BOXE UI/CSS/gameplay visuals. Keep BOXE API, replay,
lobby, mobile smoke and game diff gates green.
```
