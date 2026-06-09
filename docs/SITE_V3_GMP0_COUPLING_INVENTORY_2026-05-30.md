Status: ACTIVE
Last meaningful update: 2026-05-30

# Site V3 - GMP-0 Game Module Coupling Inventory

## 0. Scope

GMP-0 is a read-only inventory for future game-module portability.

It answers one question: what currently ties Mines, BOXE and HI-LO to the
CasinoKing platform/site, and which ties must become explicit contracts before
the games can be installed in another site or runtime host?

No gameplay, wallet, ledger, RNG, payout, fairness, settlement, CSS or runtime
file changes are part of this inventory.

## 1. Current Verdict

CasinoKing is still a modular monolith, but the current modular monolith is
acceptable for the Site V3/V1 retirement goal.

It is not yet a portable game-module product.

The most important distinction:

- `frontend-v3/app/runtime/{game}` is a local deployment target;
- the game module boundary is logical, not physical;
- portability requires a new Platform Adapter and host integration contract
  before any package/service split.

## 2. Coupling Matrix

| Coupling | Evidence | Classification | Portability impact | Next WP |
| --- | --- | --- | --- | --- |
| Site V3 public shell hosts games in iframes | `frontend-v3/app/{mines,boxe,hi-lo}/page.tsx` and `GameFramePage` point to `/runtime/{game}` | Host shell coupling | Acceptable locally; another host needs the same launch/embed contract without Site V3 imports | GMP-1 Launch/embed contract |
| Runtime placement in `frontend-v3` | `frontend-v3/app/runtime/mines`, `runtime/boxe`, `runtime/hi-lo` | Deployment coupling | Acceptable for V1 removal; blocker for installable package/service | GMP-4 Packaging/service decision after GMP-1/2/3 |
| Hardcoded local site code in public route loading | `loadGameLibraryTitles("casinoking")` in game shell routes | Host/catalog coupling | Blocks multi-site host without passing site context from host config | GMP-1 Host context payload |
| Hardcoded local site code in BOXE and HI-LO services | `DEFAULT_SITE_CODE = "casinoking"` in `backend/app/modules/games/boxe/service.py` and `backend/app/modules/games/hi_lo/service.py` | Portability blocker | A non-CasinoKing host cannot validate titles or rounds without code change | GMP-2 Adapter interface extraction |
| Mines accepts site code but defaults to CasinoKing | `backend/app/modules/games/mines/service.py` normalizes `site_code or SITE_CODE_CASINOKING` | Partial host context coupling | Better than BOXE/HI-LO; still needs host-provided contract | GMP-2 Adapter interface extraction |
| Game storage keys use `casinoking.*` | `frontend-v3/app/ui/game-runtime/game-storage.ts` and direct runtime writes in BOXE/HI-LO gameplay | Storage namespace coupling | Blocks embedding same game in a different brand/site without key collisions or brand leak | GMP-1 Storage namespace contract |
| Embed messages use `casinoking:*` | `frontend-v3/app/ui/game-runtime/use-game-embed-bridge.ts` | Embed protocol coupling | Fine as legacy local protocol; portable module needs versioned neutral message names or declared namespace | GMP-1 Embed protocol v1 |
| Player auth token lives in host localStorage | `casinoking.access_token`, `casinoking.email` read/written by shared game storage | Host auth coupling | Portable module should not assume host token key; launch token/session should be the runtime authority | GMP-1 Launch/session contract |
| Backend game modules call platform services in-process | `platform_client.py`, `round_gateway.py`, `open_game_round`, `settle_game_round_win/loss` | Intended platform adapter use | Correct logical boundary; not portable until typed/HTTP adapter is explicit | GMP-2 Adapter interface extraction |
| Backend game routes depend on platform auth/admin dependencies | `get_current_player`, `require_admin_area("finance")`, `get_current_admin` in game route files | Platform identity coupling | Correct for CasinoKing; portable host needs auth adapter or signed launch/session token boundary | GMP-1 Security/auth contract |
| Replay endpoints are game-specific but consumed by account/finance | `/games/{game}/.../replay`, player account registry/renderers | Intended reporting coupling | Correct locally; portable module needs replay descriptor and either viewer package or iframe viewer | GMP-1 Replay/reporting descriptor |
| Admin game config is in same backend/admin | `admin_config.py`, `backoffice_config.py`, title editor folders | Admin/catalog coupling | Correct for CasinoKing; portable module needs admin schema manifest and host-side editor integration | GMP-6 Admin module registration |
| Public assets and theme live under CasinoKing asset registry | title assets, theme assets, `resolveBackendAssetUrl`, `/static/games/...` | Asset registry coupling | Correct locally; portable host needs asset-kind manifest and storage URL contract | GMP-1 Asset/theme manifest |
| Runtime copy/i18n lives in game manifests | game copy defaults and title locale config | Game-owned capability | Good separation; must become part of installable manifest | GMP-1 i18n manifest contract |
| Game math/state/replay payloads are game-owned | game service modules, replay payload builders | Game-owned capability | Good separation; keep inside module | GMP-3 one-game facade |

## 3. Per-Game Notes

### Mines

Strengths:

- accepts and normalizes `site_code` through service calls;
- has launch token flow and replay/fairness endpoints;
- has mature asset/theme/i18n runtime.

Portability blockers:

- defaults to `SITE_CODE_CASINOKING`;
- frontend storage and embed protocol still use CasinoKing names;
- large standalone runtime means extraction should not start with Mines.

Recommendation: keep Mines as final proof game, not first externalization
candidate.

### BOXE

Strengths:

- smaller runtime than Mines;
- exercises real/table gate, platform round open/settle and replay;
- uses `platform_client.py` as a clear adapter boundary.

Portability blockers:

- backend service has `DEFAULT_SITE_CODE = "casinoking"`;
- frontend demo auth writes CasinoKing localStorage keys;
- title/config validation assumes CasinoKing catalog.

Recommendation: first candidate for GMP-3 one-game facade.

### HI-LO

Strengths:

- similar adapter structure to BOXE;
- exercises active round, skip/predict/cashout and replay.

Portability blockers:

- backend service has `DEFAULT_SITE_CODE = "casinoking"`;
- frontend demo auth writes CasinoKing localStorage keys;
- active-round query defaults include a CasinoKing title route assumption.

Recommendation: second candidate after BOXE, once adapter contract is proven.

## 4. What Is Not A Bug

These couplings are acceptable inside the current local product:

- Site V3 same-origin iframe runtime;
- CasinoKing storage keys for the CasinoKing player shell;
- `casinoking:*` postMessage names kept for legacy compatibility;
- in-process `PlatformGameClient`;
- admin-only replay endpoints guarded by platform admin auth;
- account/finance consuming registered replay descriptors.

They become blockers only if the goal is installable game modules or another
host site.

## 5. Required GMP-1 Contract Topics

GMP-1 must define:

- host context: `site_code`, `host_code`, `brand_code`, `locale`, return URL;
- launch token payload and validation;
- runtime auth/session authority, without assuming host localStorage keys;
- postMessage namespace and event schema;
- neutral storage namespace policy;
- Platform Adapter operations and idempotency;
- replay/reporting descriptor;
- admin config schema manifest;
- asset/theme/i18n manifest;
- host security, correlation id and observability.

## 6. Recommended Work Order

1. GMP-1: write versioned contracts, no production code.
2. GMP-2: introduce typed adapter interfaces in-process, no behavior change.
3. GMP-3: route BOXE through the new facade, still in-process.
4. GMP-4: decide package vs service vs remote RGS mock.
5. GMP-5: build a non-CasinoKing mock host.
6. GMP-6: register a game module in host admin through manifest/schema.

## 7. Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Coupling inventory | none | read-only | none | read-only | read-only | none | rg/manual | this doc | Complete for GMP-0 | No production code changed. |
| Site code portability | none | future | future | future | future | none | future | this doc | Blocker | BOXE/HI-LO hardcode CasinoKing. |
| Storage namespace portability | none | none | future | none | future | none | future | this doc | Blocker | Runtime reads/writes CasinoKing localStorage keys. |
| Embed protocol portability | none | none | future | none | future | none | future | this doc | Blocker | Current protocol uses `casinoking:*`. |
| Adapter portability | none | future | future | none | none | none | future | this doc | Not started | Current in-process adapter is correct local boundary. |
| Replay/reporting portability | future | future | future | future | future | none | future | this doc | Partial | Local registry exists; external descriptor not versioned. |

## 8. Stop Conditions

Stop before code if a proposed portability slice would:

- touch wallet or ledger semantics;
- change payout, RNG, fairness or settlement behavior;
- redesign runtime UI/CSS;
- bypass platform round/table session idempotency;
- make another host responsible for CasinoKing financial data;
- move Mines first without proving the facade on a smaller game.
