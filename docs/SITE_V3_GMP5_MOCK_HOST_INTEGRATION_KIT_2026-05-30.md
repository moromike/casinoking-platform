Status: IMPLEMENTED - first slice plus GMP-5B backend launch authority slice
Last meaningful update: 2026-05-30

# Site V3 - GMP-5 Mock Host Integration Kit

## 0. Scope

GMP-5 first slice creates a concrete same-repo game module manifest boundary
and proves that a non-CasinoKing mock host can use the manifest together with
the existing demo launch contract.

GMP-5B adds a compatible backend action-authority slice for BOXE: the runtime
does not need to send a token yet, but when a real `X-Game-Launch-Token` is
present, BOXE start uses the token as the source of truth for `title_code` and
`site_code`.

This slice does not move runtime UI/CSS, does not create a frontend package,
does not create a backend service/RGS, and does not change wallet, ledger,
settlement, RNG, fairness, payout or gameplay behavior.

## 1. What Changed

- Added a BOXE module manifest in
  `backend/app/modules/platform/game_modules/manifest.py`.
- Added public read-only manifest endpoint:
  `GET /game-modules/{game_code}/manifest`.
- Registered the endpoint in `backend/app/api/router.py`.
- Added contract tests for manifest shape, descriptor parity, asset/i18n
  metadata, no arbitrary code and explicit blocker declarations.
- Added integration tests proving:
  - the BOXE manifest is readable by a host;
  - a non-CasinoKing mock site can request a BOXE demo launch;
  - launch/storage/embed/replay descriptors match the manifest;
  - unknown module manifest lookup has no fallback.
- Added BOXE real launch-token endpoint:
  `POST /games/boxe/launch-token`.
- Hardened `POST /games/boxe/start`:
  - no-token requests keep the legacy path;
  - invalid tokens return `GAME_LAUNCH_TOKEN_INVALID`;
  - non-BOXE or wrong-owner tokens are rejected;
  - demo launch tokens are not accepted by the authenticated start endpoint yet;
  - real launch tokens override payload title/site authority.
- Propagated `site_code` through BOXE `start_round`, platform round opening,
  `boxe_sessions`, `boxe_rounds` and `platform_rounds`.

## 2. What The Manifest Declares

The BOXE manifest declares:

- `manifest_version: 1`;
- `game_code: boxe`;
- runtime entry `/runtime/boxe`;
- embed protocol `ck-game-embed-v1`;
- supported modes `demo` and `real`;
- backend action API version `1`;
- current adapter mode `in_process_v1`;
- launch-token endpoint `/games/boxe/launch-token`;
- launch-token endpoint mode `real` only; demo launch remains `/demo/launch`;
- optional launch-token authority for `start`;
- token-authoritative fields `title_code`, `site_code`, `game_code`, `mode`;
- legacy no-token start supported during migration;
- service split status `service_ready: false`;
- title config, copy/i18n, assets, theme and sounds capability flags;
- replay/reporting descriptor fields;
- storage allowed and forbidden uses;
- asset kinds for lobby card, safe/mine symbols, title logo, background and
  BOXE sounds;
- i18n locales `it`, `en`, `de`, `es`;
- current host-integration blockers.

## 3. Explicit Current Blockers

GMP-5 first slice is honest about what is not portable yet:

- BOXE runtime/frontend still uses CasinoKing-oriented auth/demo storage keys.
- BOXE runtime still does not send `X-Game-Launch-Token` on actions, so strict
  token requirement is not enabled yet.
- BOXE demo action authority is still on the current bearer/demo-auth path; the
  authenticated start endpoint accepts only real launch tokens when a token is
  provided.
- The frontend embed bridge still keeps `casinoking:*` compatibility aliases.
- Replay viewers are still imported directly by account/finance UI.
- The in-process Platform Adapter still carries `psycopg.Cursor`, so it is not
  service-ready.

These blockers are now visible in the manifest instead of being hidden in code.

## 4. Mock Host Proof

The integration proof creates a temporary site code such as:

```text
gmp5host_<suffix>
```

Then it performs:

```text
GET /game-modules/boxe/manifest
POST /demo/token
POST /demo/launch
  game_code=boxe
  title_code=boxe001
  site_code=<mock site>
  host_code=mockhost
  brand_code=<mock site>
  embed_origin=https://mockhost.example
```

The test asserts that:

- the storage namespace is `host.<mock-site>.game.boxe`;
- no `casinoking` fallback appears in the storage namespace;
- embed protocol matches the manifest;
- replay endpoints match the manifest;
- unknown module lookup returns `RESOURCE_NOT_FOUND`.

## 5. Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE same-repo manifest | none | new manifest registry | new read-only endpoint | none | none | none | contract | this doc | Green first slice | Package-first boundary; no physical split. |
| Mock host demo launch contract | temporary test site row | existing demo launch + manifest endpoint | descriptors matched to manifest | none | none | none | integration | this doc | Green first slice | Proves non-CasinoKing launch descriptors, not runtime action portability. |
| Runtime consumption of host storage namespace | none | none | descriptors exist | none | future | future | future | this doc | Blocked | Runtime still uses CasinoKing-oriented local storage. |
| Runtime/action authority via launch token | none | BOXE start validates optional real launch token and persists token site/title | optional `X-Game-Launch-Token` on `/games/boxe/start` | none | future token consumption | none | integration | this doc | Green backend first slice | Strict requirement deferred until runtime launch context sends token; demo action token path still future. |
| Frontend package split | none | none | none | none | future | future | future | GMP-4 doc | Deferred | Requires visual/mobile/replay/audio/i18n gates. |
| Backend service/RGS split | none | future | future HTTP adapter | none | none | none | future | GMP-4 doc | Deferred | Requires adapter without cursor, idempotency, timeout and reconciliation gates. |

## 6. Verification

Completed verification:

- `python -m pytest tests/contract/test_gmp5_game_module_manifest.py -q`
  passed: 5 tests.
- `python -m pytest tests/integration/test_gmp5_mock_host_integration.py -q`
  passed: 2 tests.
- `python -m pytest tests/integration/test_boxe_api.py -q`
  passed: 59 tests, including launch-token issue/validation/title-authority
  coverage.
- Game runtime/UI diff gate for BOXE, Mines and HI-LO returned no files.

## 7. Next Step

GMP-5C should move from backend-compatible authority toward runtime
consumption, still without visual/runtime redesign. This requires explicit
approval because the smallest correct change is inside protected BOXE runtime
files:

- `frontend-v3/app/ui/boxe/use-boxe-runtime.ts`;
- `frontend-v3/app/ui/boxe/boxe-gameplay.tsx`;
- `frontend-v3/app/ui/boxe/boxe-standalone.tsx`.

The approved scope must be non-visual only: pass the existing real launch token
to BOXE start. No CSS, board layout, replay viewer, audio control, RNG,
fairness, math or payout changes.

```text
Implement GMP-5C runtime launch-context consumption for BOXE. Pass the
host-neutral launch descriptor/token from shell to runtime without changing
gameplay layout, make real BOXE starts send X-Game-Launch-Token, keep no-token
legacy fallback during migration, and design the demo-token action path
separately. Do not touch BOXE UI/CSS/gameplay visuals. Keep BOXE API, replay,
lobby, mobile smoke and game diff gates green.
```
