Status: DECIDED - package-first, service-later
Last meaningful update: 2026-05-30

# Site V3 - GMP-4 Packaging And Service Decision

## 0. Scope

GMP-4 decides the next physical target for portable proprietary game modules
after the GMP-2 typed adapter and the GMP-3 host-neutral launch proof.

This decision package does not move files, split services, change runtime UI,
change CSS, change wallet/ledger semantics, change RNG/fairness, or change
gameplay behavior.

## 1. Decision

Choose a staged package-first path:

```text
same-repo game module package/manifest boundary first
-> mock host integration kit
-> frontend runtime package only after visual and embed gates
-> backend service/RGS mock only after HTTP adapter and settlement gates
```

Do not start with a separate backend game service.

Do not start by moving frontend runtime UI into a separate package.

The immediate implementation target after this decision is a same-repo module
manifest and host integration kit that keeps the current in-process deployment
but makes ownership, descriptors, versioning and test gates explicit.

## 2. Why This Is The Right Default

The current product is no longer V1/V2 based, but it is still a modular
monolith. That is acceptable for CasinoKing local product delivery and for
proving contracts. It is not yet a portable game product.

The strongest reason to avoid a backend service split now is financial
authority:

- wallet and ledger writes are host-platform responsibilities;
- table sessions and platform rounds are opened and settled inside the current
  backend transaction boundary;
- GMP-2 proves a typed adapter facade, but only in-process;
- GMP-3 proves host-neutral demo launch descriptors, not real-money remote
  settlement.

The strongest reason to avoid a frontend package split now is product risk:

- runtime UI, replay, audio, mobile layout and i18n are sensitive surfaces;
- the current shared game shell is still imported from `frontend-v3/app/ui/game-runtime`;
- portable storage and embed fields exist in launch descriptors, but the
  runtimes have not yet been fully converted to consume only host-neutral
  storage and protocol values.

Package-first keeps the system shippable while creating a real product boundary.

## 3. Option Comparison

| Option | Decision | Why |
| --- | --- | --- |
| Same-repo game module package/manifest first | Selected | Lowest risk. Preserves current deployment, lets us version manifests, descriptors, admin schema and test gates before moving runtime or backend code. |
| Separate frontend runtime package first | Defer | Useful later, but premature until storage/embed/i18n/replay/mobile gates are green against a mock host. Moving UI first risks recreating the recent game regressions. |
| Separate backend game service or RGS mock first | Reject for now | Too risky before HTTP Platform Adapter, idempotent settlement RPC, reconciliation, timeout policy and rollback are designed and tested. |
| Defer every split and keep only docs | Reject | Too passive. The next step should create a manifest-driven boundary and mock host proof, even if deployment remains in-process. |

## 4. Target Shape

The next product boundary is a same-repo game module definition, not a remote
service.

Conceptually:

```text
CasinoKing or Mock Host
  -> host launch API
  -> host-neutral launch/storage/embed/replay descriptors
  -> in-process game module runtime/action API
  -> typed Platform Adapter facade
  -> host wallet/ledger/session/audit
```

The same-repo module definition should expose:

- `manifest_version`;
- `game_code`;
- runtime entry and embed protocol;
- supported modes;
- backend action API version;
- platform adapter requirements;
- replay/reporting descriptor;
- title config schema version;
- asset kinds;
- i18n locales and fallback policy;
- theme/sound capability flags;
- test gate list.

It must not allow arbitrary admin-supplied executable code.

## 5. Ownership

| Surface | Owner After GMP-4 Decision | Notes |
| --- | --- | --- |
| Player/admin identity | Host platform | CasinoKing now; future host later. |
| Wallet, ledger, settlement, reconciliation | Host platform | Never game-owned. |
| Launch token and access/table sessions | Host platform | Game receives opaque refs and descriptors. |
| Game state machine, math, RNG/fairness | Game module | Must stay server-authoritative. |
| Gameplay UI and replay viewer | Game module | No host layout rewrite inside the game. |
| Public shell, close/return, account links | Host platform | Embed contract decides communication. |
| Module manifest/schema | Game module + host registry | Game declares; host validates and publishes. |
| Admin editor | Host platform | Driven by schema, no arbitrary code. |

## 6. Deployment And Versioning

For the next slice, deployment remains unchanged:

- backend game modules still run in the backend process;
- frontend runtimes still build with `frontend-v3`;
- public edge still serves Site V3 from `http://localhost:3000`;
- direct renderer stays `http://localhost:3001`.

Versioning rules to introduce before any physical split:

- every module manifest has a `manifest_version`;
- every backend action API has an explicit version;
- every replay payload schema has an explicit version;
- every embed protocol has an explicit version;
- title config snapshots record the module manifest version used at publish
  time;
- account/finance replay must keep working for rounds created under older
  manifest versions.

## 7. Required Gates Before Further Extraction

### Gate A - Manifest Boundary

Required before GMP-5:

- manifest schema exists for BOXE first;
- manifest includes launch, runtime, backend, reporting, admin, assets, theme,
  sounds and i18n metadata;
- contract test rejects missing required manifest fields;
- descriptors are generated from the manifest or checked against it;
- no game runtime/UI diff.

### Gate B - Mock Host Integration

Required before frontend package extraction:

- a non-CasinoKing mock host can request a demo launch;
- returned descriptors contain no hidden CasinoKing fallback;
- runtime storage namespace is host-scoped;
- close/return uses the embed contract;
- mock host does not import account, CMS, CasinoKing lobby or backoffice UI;
- desktop and mobile smoke pass.

### Gate C - Frontend Runtime Package

Required before moving runtime UI:

- visual baseline for desktop/mobile on BOXE, HI-LO and Mines;
- replay viewer baseline for account and finance surfaces;
- audio controls verified;
- i18n/copy fallback verified;
- no host storage key dependency inside portable runtime code;
- rollback can restore same-origin `frontend-v3` runtime without data loss.

### Gate D - Backend Service Or RGS Mock

Required before backend service split:

- HTTP Platform Adapter v1 is designed and contract-tested;
- adapter DTOs no longer require an in-process `psycopg.Cursor`;
- `void_round`, `get_table_session_state` and
  `close_or_timeout_session` are typed and implemented;
- BOXE and HI-LO action authority consumes launch/session descriptors instead
  of hardcoded CasinoKing defaults;
- idempotency and conflict semantics match the in-process adapter;
- settlement and replay refs are reconciliable;
- timeout policy is explicit per game;
- structured logs carry correlation id across host, game and adapter;
- rollback does not duplicate bets, payouts or ledger transactions.

## 8. Rollback

Rollback for the package-first path is simple:

- disable module manifest consumption and use the current static descriptors;
- keep launch token payload fields because they are additive;
- keep in-process adapter as the only production adapter;
- keep runtime routes under `frontend-v3/app/runtime/{game}`;
- keep account/finance replay using the current registry.

Rollback for a future backend service split is not simple and must not be
started until Gate D is green.

## 9. Migration Risk Register

| Risk | Severity | Mitigation |
| --- | --- | --- |
| Remote service duplicates or loses settlement | Critical | Do not build remote service before HTTP adapter, idempotency and reconciliation gates. |
| Frontend package move breaks gameplay layout | High | Do not move UI before visual/mobile/replay/audio/i18n baselines. |
| Mock host accidentally imports CasinoKing account/CMS/admin | High | GMP-5 test must assert no host import shortcuts. |
| Manifest drifts from backend descriptors | Medium | Add static contract tests for manifest/descriptor parity. |
| Old replay rounds become unreadable | High | Version replay schema and viewer entry; keep old viewers available. |
| Admin module registration becomes arbitrary code execution | Critical | Schema-only registration; no uploaded executable code. |

## 10. Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| GMP-4 packaging decision | none | none | none | none | none | none | doc review | this doc | Decided | Package-first, service-later. |
| Same-repo module manifest target | future | future manifest registry | future descriptor parity | future schema-driven admin | unchanged | unchanged | future contract | this doc | Selected next implementation target | No physical split yet. |
| Frontend runtime package | none | none | none | none | future | future | future visual/mobile/replay/audio/i18n | this doc | Deferred | Start only after GMP-5 mock host gates. |
| Backend service/RGS mock | none | future HTTP adapter | future adapter RPC | none | unchanged | unchanged | future settlement/idempotency/reconciliation | this doc | Rejected for now | Too risky before Gate D. |
| Full defer | none | none | none | none | none | none | none | this doc | Rejected | Would not advance portability. |

## 11. Stop Conditions

Stop before code if the next slice would:

- move gameplay UI/CSS while manifest and mock host are still missing;
- introduce a remote backend service without HTTP adapter contract tests;
- bypass platform wallet/ledger/table-session authority;
- let admin upload or execute arbitrary module code;
- make another host responsible for CasinoKing ledger data;
- break replay compatibility for old rounds.

## 12. Next Implementation Prompt

```text
GMP-4 is decided: package-first, service-later.

Implement GMP-5 as a mock non-CasinoKing host integration kit without moving
game runtime UI/CSS and without creating a backend service. Start with BOXE.
Add a manifest/schema boundary if needed for the mock host, prove demo launch,
storage namespace, embed close/return and replay descriptor consumption, and
keep all real-money wallet/ledger settlement in the host platform. No physical
frontend package split and no backend service split in this slice.
```
