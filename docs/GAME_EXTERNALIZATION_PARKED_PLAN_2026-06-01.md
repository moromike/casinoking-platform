Status: PARKED
Last meaningful update: 2026-06-01

# Game Externalization Parked Plan

## 1. Decision

Michele decision, 2026-06-01: prepare the externalization path, but do not
execute it now.

Current focus stays on Site V3 stability and new-game integration inside
`frontend-v3`. This document is a parked plan for a future state where games can
live in a separate repo, package or service and communicate with the host only
through explicit API contracts.

No code, CSS, game logic, backend GMP slice, RNG, payout, board, reveal or replay
change is authorized by this document.

## 2. Vision

The long-term target is a host-neutral game module model:

```text
Host website / platform
  -> launch contract
  -> game runtime package/service
  -> table session contract
  -> action contract
  -> replay/reporting contract
```

CasinoKing is one possible host, not the only one. A future third-party site
should be able to integrate a game module by implementing the documented host
API or by using interfaces provided by this project.

The game owns gameplay, board behavior, rules, payout presentation, assets and
runtime copy. The platform owns identity, wallet, table-session authority,
ledger, reporting, launch tokens and legal money boundaries.

## 3. Current GMP Foundation

The parked plan builds on the Site V3 GMP work already documented. The existing
GMP work is preparation, not a physical split.

| Slice | Existing output | Externalization relevance |
| --- | --- | --- |
| GMP-0 | `docs/SITE_V3_GMP0_COUPLING_INVENTORY_2026-05-30.md` | Identifies current couplings between game runtime, Site V3 shell, backend, reports and host assumptions. |
| GMP-1 | `docs/SITE_V3_GMP1_GAME_MODULE_INTEGRATION_CONTRACT_2026-05-30.md` | Defines the first integration contract areas: launch, session, embed, storage, replay, admin, assets and i18n. |
| GMP-2 | `docs/SITE_V3_GMP2_BOXE_IN_PROCESS_ADAPTER_2026-05-30.md` | Proves a typed BOXE in-process adapter without changing game behavior. |
| GMP-3 | `docs/SITE_V3_GMP3_HOST_NEUTRAL_LAUNCH_PROOF_2026-05-30.md` | Adds host-neutral descriptors and a non-CasinoKing launch proof in-process. |
| GMP-4 | `docs/SITE_V3_GMP4_PACKAGING_SERVICE_DECISION_2026-05-30.md` | Records the packaging decision: package-first, service-later. |
| GMP-5 | `docs/SITE_V3_GMP5_MOCK_HOST_INTEGRATION_KIT_2026-05-30.md` | Adds same-repo manifest/mock-host kit and launch-token hardening as a first integration slice. |

## 4. Contract To Close Before Extraction

Externalization cannot start until these contracts are explicit, versioned and
covered by tests.

| Contract | Must define before extraction | Current stance |
| --- | --- | --- |
| Launch | Host-neutral launch descriptor, auth/session inputs, demo/real/bonus mode, title/site ownership and return/close behavior. | Partially prepared by GMP-1/GMP-3/GMP-5. |
| Table session | Who opens, owns, refreshes, closes and times out table sessions; how real and bonus balances are reserved or exposed. | Must be made game-agnostic and host-neutral before split. |
| Actions | Runtime action API, idempotency, validation, error copy mapping and authority boundaries. | No extraction until game actions avoid host-specific assumptions. |
| Replay | Replay payload versioning, viewer adapter, report drilldown, player history and deterministic reconstruction. | Must be registry-based for every game. |
| Assets/theme/i18n | Asset manifest, theme tokens, copy defaults, locale pack loading and fallback behavior. | Must not rely on CasinoKing-only global CSS or filesystem assumptions. |
| Reporting | Finance/account/admin reporting descriptors, game-code registry, status mapping and retention policy. | Must extend registries, not add fourth/fifth branches. |

## 5. Activation Conditions

This plan remains PARKED until at least one activation trigger is explicitly
approved by Michele and CTO.

Recommended triggers:

- after game 6 is stable and the repeated integration cost is proven;
- when a third-party host or non-CasinoKing website integration becomes a real
  business requirement;
- when a game must be versioned, deployed or licensed independently from the
  CasinoKing platform;
- when the mock-host kit proves that at least two games can run through the same
  host-neutral launch/table/replay contracts.

Minimum gates before activation:

- Site V3 public shell, admin, finance and all shipped games have green golden
  screenshot suites on desktop and mobile;
- no cross-game CSS class reuse remains in shipped games;
- game logic/RNG/math/payout/board/reveal files have protected zero-diff
  baselines;
- game reporting and embed launch are registry-based for game 4+;
- mock host can launch demo and real-mode gates without CasinoKing-only UI
  assumptions;
- CTO approves a dedicated extraction WP with rollback and parity artifacts.

## 6. Future Execution Shape

If activated, externalization should happen in small gates:

1. Freeze golden screenshots and contract fixtures for each shipped game.
2. Extract one game contract descriptor without moving runtime files.
3. Run the mock host against the descriptor.
4. Move assets/theme/i18n loading behind explicit manifest APIs.
5. Move one game to a package boundary inside the same repo.
6. Only after parity, decide whether a separate repo/service is justified.

Extraction must be one game at a time. Do not move all games together.

## 7. Out Of Scope Now

- No physical split.
- No service deployment.
- No repo move.
- No rewrite of game UI.
- No game logic changes.
- No CSS recovery work.
- No new host implementation beyond already documented GMP mock-host slices.

Status remains: PARKED.
