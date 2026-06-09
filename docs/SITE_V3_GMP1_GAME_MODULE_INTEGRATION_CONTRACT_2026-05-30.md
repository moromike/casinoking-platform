Status: ACTIVE
Last meaningful update: 2026-05-30

# Site V3 - GMP-1 Game Module Integration Contract v1

## 0. Scope

GMP-1 defines the contract required before Mines, BOXE or HI-LO can become
portable proprietary game modules.

This is contract-first. It does not move code, split packages, create services
or change gameplay, wallet, ledger, settlement, RNG, fairness, payout, CSS or
runtime UI.

Input: `docs/SITE_V3_GMP0_COUPLING_INVENTORY_2026-05-30.md`.

## 1. Goals

The contract must allow a host platform to integrate a game module without
hardcoding CasinoKing site, storage, account, CMS or admin behavior.

Supported future targets:

- same-repo in-process game module;
- separate frontend package;
- separate backend package;
- separate game service/RGS;
- local mock host that is not CasinoKing-branded.

## 2. Roles

| Role | Owns | Must not own |
| --- | --- | --- |
| Host platform | player/admin identity, wallet, ledger, catalog, launch, sessions, audit, CMS, finance/account surfaces | game RNG, board, payout math, game state transitions |
| Game module | game engine, state machine, RNG/fairness, gameplay UI, replay payload/viewer, copy/assets/theme schema | host wallet, host ledger, host CMS, host account auth |
| Integration adapter | typed boundary between host and game | hidden financial shortcuts |

## 3. Module Manifest

Each portable game ships a manifest.

Required fields:

```json
{
  "manifest_version": 1,
  "game_code": "boxe",
  "display_name": "BOXE",
  "runtime": {
    "entry": "runtime/boxe",
    "embed_protocol": "ck-game-embed-v1",
    "supported_modes": ["demo", "real_cash", "real_bonus"]
  },
  "backend": {
    "action_api_version": 1,
    "requires_platform_adapter": true
  },
  "admin": {
    "title_config_schema_version": 1,
    "supports_copy_i18n": true,
    "supports_assets": true,
    "supports_theme": true,
    "supports_sounds": true
  },
  "reporting": {
    "descriptor_version": 1,
    "replay_viewer": "module-owned"
  },
  "assets": {
    "kinds": []
  },
  "i18n": {
    "locales": ["it", "en", "de", "es"],
    "default_locale": "it"
  }
}
```

The manifest is descriptive. It does not give operators a way to upload or run
arbitrary JavaScript.

## 4. Host Launch Contract

The host creates a launch intent before opening the runtime.

Required launch intent:

```json
{
  "launch_id": "uuid",
  "launch_token": "opaque-short-lived-token",
  "host_code": "casinoking",
  "site_code": "casinoking",
  "brand_code": "casinoking",
  "game_code": "boxe",
  "title_code": "boxe001",
  "player_ref": "host-player-id-or-demo-ref",
  "mode": "demo",
  "wallet_source": "demo",
  "locale": "it",
  "return_url": "https://host.example/",
  "embed_origin": "https://host.example",
  "correlation_id": "req-or-trace-id",
  "expires_at": "ISO-8601"
}
```

Rules:

- the game runtime reads launch/session authority from the launch token, not
  from host localStorage keys;
- `site_code`, `brand_code` and `host_code` are host-provided, not hardcoded in
  the game;
- `title_code` is explicit and must be validated by the host catalog;
- `return_url` must be sanitized by the host;
- launch tokens are short-lived and single-context;
- real-money launch requires authenticated player identity and table/session
  budget before round start.

## 5. Runtime Embed Contract

Protocol name: `ck-game-embed-v1`.

The current `casinoking:*` messages remain compatibility aliases only. Portable
modules must use versioned neutral messages.

Game -> host:

| Type | Required payload |
| --- | --- |
| `ck-game:v1:ready` | `{ gameCode, launchId, correlationId }` |
| `ck-game:v1:close-requested` | `{ gameCode, launchId, reason }` |
| `ck-game:v1:fatal-error` | `{ gameCode, launchId, code, messageKey, retryable }` |
| `ck-game:v1:round-state` | `{ gameCode, launchId, roundRef, state }` |

Host -> game:

| Type | Required payload |
| --- | --- |
| `ck-host:v1:fullscreen-state` | `{ gameCode, launchId, active }` |
| `ck-host:v1:visibility-state` | `{ gameCode, launchId, visible }` |
| `ck-host:v1:close-accepted` | `{ gameCode, launchId }` |

Rules:

- every message includes `gameCode` and `launchId`;
- host and game verify `origin`;
- no wallet, ledger, payout or settlement authority travels through
  postMessage;
- postMessage telemetry is informational only.

## 6. Storage Contract

Portable games must not assume `casinoking.*` localStorage keys.

Host provides a storage namespace in launch context:

```json
{
  "storage_namespace": "host.casinoking.game.boxe"
}
```

Allowed storage uses:

- non-authoritative UI preferences;
- audio mute/volume;
- safe resume hints tied to launch/session;
- demo-only anonymous convenience tokens when host allows them.

Forbidden storage uses:

- authoritative player identity;
- wallet balance;
- payout state;
- hidden board/outcome;
- permanent cross-host access tokens.

## 7. Platform Adapter Contract

Every real-money economic action passes through the host platform adapter.

Required operations:

```text
open_round(request) -> OpenRoundResult
settle_win(request) -> SettlementResult
settle_loss(request) -> SettlementResult
void_round(request) -> VoidResult
get_table_session_state(request) -> TableSessionState
close_or_timeout_session(request) -> CloseSessionResult
```

`open_round` request:

- idempotency key;
- player ref;
- game code;
- title code;
- site code;
- mode/wallet source;
- bet amount;
- table session ref;
- access session ref;
- game config snapshot hash;
- correlation id.

`settle_win` and `settle_loss` request:

- idempotency key;
- platform round ref;
- game round ref;
- outcome state;
- payout amount for win;
- replay ref/hash;
- correlation id.

Rules:

- game modules never mutate wallet or ledger directly;
- adapter operations are idempotent;
- open round is atomic: validate, reserve/debit and ledger bet cannot be split;
- close/timeout uses the game-specific settlement policy declared by the
  module;
- adapter responses include host-owned round refs and ledger refs, but games
  treat those as opaque.

## 8. Action API Contract

Each game may define game-specific actions, but all mutating actions share
rules:

- require launch/session authority;
- require idempotency key;
- return stable error codes;
- never expose hidden outcome state early;
- return enough state for the runtime to render;
- write replay/audit payload incrementally or at terminal state.

Examples:

| Game | Actions |
| --- | --- |
| Mines | start, reveal, cashout |
| BOXE | start, reveal/pick, cashout |
| HI-LO | start, predict, skip, cashout |

## 9. Replay And Reporting Descriptor

Every game ships a reporting descriptor.

Required fields:

```json
{
  "descriptor_version": 1,
  "game_code": "boxe",
  "player_replay_endpoint": "/games/boxe/round/{roundRef}/replay",
  "admin_replay_endpoint": "/games/boxe/admin/round/{roundRef}/replay",
  "account_summary_fields": [],
  "finance_summary_fields": [],
  "replay_payload_schema": "boxe.replay.v1",
  "viewer": {
    "mode": "module-component-or-iframe",
    "entry": "replay/boxe"
  },
  "retention": {
    "ledger": "host-policy",
    "replay_payload": "host-policy"
  }
}
```

Rules:

- unknown games must not fall back to another game's replay endpoint;
- account and finance may use different layouts, but must reconstruct the same
  deterministic round;
- replay payloads must not depend on live mutable config;
- admin replay may expose server/fairness fields unavailable to players.

## 10. Asset, Theme And I18n Contract

Each game declares asset kinds:

```json
{
  "kind": "game_area_background",
  "mime": ["image/png", "image/webp"],
  "max_bytes": 400000,
  "recommended_dimensions": "1280x720",
  "render_mode": "cover"
}
```

Theme contract:

- game declares consumed token names;
- host stores draft/live title theme;
- runtime reads published theme snapshot only;
- missing optional assets degrade with packaged defaults.

I18n contract:

- game ships default copy manifest for all supported locales;
- host may override title copy per locale;
- visible runtime errors map from stable error codes to copy keys;
- backend/internal error strings are never rendered directly.

## 11. Admin Module Registration Contract

A host admin can register a game module only through a schema manifest.

Required admin surfaces:

- title config schema;
- copy/i18n schema;
- rules HTML schema;
- asset kinds;
- theme token/skin schema;
- sounds schema when supported;
- preview launch config;
- publish lifecycle.

Rules:

- no arbitrary executable code from admin;
- draft edits never mutate active rounds;
- publish creates immutable snapshots where required;
- operational audit records config/copy/assets/theme changes;
- admin permissions are host-owned.

## 12. Security And Observability

Required:

- launch token TTL;
- origin validation for embed;
- idempotency keys on mutating calls;
- correlation id across host/game/adapter;
- host-owned auth and admin permissions;
- stable error code taxonomy;
- structured logs without leaking secrets;
- no wallet/ledger payloads in browser-only telemetry.

## 13. Migration Gates

Before GMP-2 implementation:

- this contract reviewed by CTO;
- one candidate game selected, default BOXE;
- tests planned for launch, embed, storage, adapter, replay and admin manifest;
- no runtime visual changes in the same slice.

Before physical split:

- adapter interface proven in-process;
- BOXE facade green;
- account/finance reporting descriptor green;
- mock non-CasinoKing host can launch demo;
- real-money path remains host-owned and audited.

As of 2026-05-30, the first BOXE in-process adapter and host-neutral demo
launch proof are implemented in the GMP-2 and GMP-3 docs. GMP-4 is also
decided: package-first, service-later. The next gate is GMP-5 mock host
integration, not a backend service split.

## 14. Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Launch contract | none | descriptor proof implemented | descriptors added to launch responses | none | future | none | GMP-3 tests | GMP-3 doc | Green proof | Host-neutral fields proven for BOXE demo launch. |
| Embed protocol | none | none | defined here | none | future | none | future | this doc | Designed | Keep `casinoking:*` aliases locally. |
| Storage namespace | none | descriptor proof implemented | storage descriptor added | none | future | none | GMP-3 tests | GMP-3 doc | Green proof | Host-scoped namespace proven without `casinoking.*`. |
| Platform Adapter | none | first BOXE interface implemented | unchanged | none | none | none | contract + BOXE API | GMP-2 doc | Green first slice | In-process first, no service split yet. |
| Replay/reporting descriptor | future if needed | descriptor proof implemented | replay descriptor added | future | future | none | GMP-3 tests | GMP-3 doc | Green proof | BOXE endpoints explicit; no fallback to wrong game. |
| Asset/theme/i18n manifest | future if needed | future | defined here | future | future | none | future | this doc | Designed | Host-neutral module metadata. |
| Admin schema registration | future if needed | future | defined here | future | none | none | future | this doc | Designed | No arbitrary code. |
| Packaging/service decision | none | none | none | none | none | none | doc review | GMP-4 doc | Decided | Package-first, service-later. |

## 15. Next Execution Prompt

```text
GMP-2 first slice is implemented in
docs/SITE_V3_GMP2_BOXE_IN_PROCESS_ADAPTER_2026-05-30.md.

GMP-3 is implemented in
docs/SITE_V3_GMP3_HOST_NEUTRAL_LAUNCH_PROOF_2026-05-30.md.

GMP-4 is decided in
docs/SITE_V3_GMP4_PACKAGING_SERVICE_DECISION_2026-05-30.md:
package-first, service-later.

Implement GMP-5 as a mock non-CasinoKing host integration kit without moving
game runtime UI/CSS and without creating a backend service. Start with BOXE.
```
