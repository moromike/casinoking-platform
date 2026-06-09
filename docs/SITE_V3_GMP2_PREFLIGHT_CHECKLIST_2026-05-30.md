Status: IMPLEMENTED - first BOXE in-process adapter slice
Last meaningful update: 2026-05-30

# Site V3 - GMP-2 Preflight Checklist

## 0. Purpose

This checklist prepared GMP-2. The first BOXE in-process adapter slice is now
implemented in `docs/SITE_V3_GMP2_BOXE_IN_PROCESS_ADAPTER_2026-05-30.md`.

GMP-2 is the in-process adapter interface extraction required before any game
module can become portable. It must start with BOXE and must not move services,
split packages or touch game runtime UI/CSS.

Required gate before code was:

- CTO approval of `docs/SITE_V3_GMP1_GAME_MODULE_INTEGRATION_CONTRACT_2026-05-30.md`.

Michele gave operational approval in chat on 2026-05-30 to execute the bounded
in-process slice. The implementation stayed inside the allowed scope below.

## 1. Allowed Scope After CTO Approval

Allowed:

- add typed backend adapter interfaces;
- add typed launch/session/storage/embed/replay descriptor interfaces;
- route BOXE backend economic calls through an in-process facade;
- keep every existing endpoint path and payload compatible;
- add contract and integration tests proving behavior parity;
- add docs for the new adapter boundary.

Forbidden:

- no wallet or ledger semantic change;
- no payout, RNG, fairness or settlement policy change;
- no gameplay UI/CSS change;
- no package or service split;
- no Mines-first extraction;
- no direct host-specific shortcuts inside the game module;
- no fallback from one game's replay/reporting to another game.

## 2. Candidate

Candidate: BOXE.

Reason:

- smaller than Mines;
- already exercises platform round open/settle;
- has replay/account history;
- has real/table gate behavior;
- has clear backend `platform_client.py` boundary.

## 3. Expected Code Areas

Likely backend areas:

- `backend/app/modules/games/boxe/platform_client.py`;
- `backend/app/modules/games/boxe/service.py`;
- new platform/game adapter interface module;
- tests under `tests/contract` and `tests/integration`.

Likely frontend areas only if needed for typed descriptors:

- shared registry/descriptors outside game runtime UI;
- no edits under `frontend-v3/app/ui/boxe`;
- no edits under `frontend-v3/app/runtime/boxe`.

## 4. Required Tests

Before and after GMP-2 implementation:

- BOXE API start/reveal/cashout;
- BOXE real/table gate behavior;
- BOXE replay/account history;
- finance/replay registry contracts;
- game runtime frontend boundary contracts;
- Site V3 player handoff browser smoke;
- canonical local smoke suite;
- `git diff -- frontend-v3/app/ui/boxe frontend-v3/app/runtime/boxe` must be empty.

## 5. Stop Conditions

Stop immediately if a proposed GMP-2 implementation:

- changes wallet/ledger amounts or transaction semantics;
- changes BOXE math/payout/RNG/fairness;
- changes BOXE runtime visual layout;
- changes public endpoint compatibility;
- introduces CasinoKing-only assumptions into the adapter interface;
- makes Mines, HI-LO or frontend runtime files part of the same slice.

## 6. Execution Prompt

```text
Implement GMP-2 only after CTO approval of GMP-1.

Start with BOXE. Extract an in-process Platform Adapter interface around the
existing BOXE platform_client/service economic boundary. Preserve all existing
endpoint paths, payloads, wallet/ledger semantics, settlement, RNG, fairness,
payout and replay behavior. Do not edit BOXE runtime UI/CSS or move packages or
services. Prove parity with BOXE API, replay/account, finance registry, runtime
boundary, Site V3 handoff and canonical smoke tests. End by proving there is no
diff under frontend-v3/app/ui/boxe and frontend-v3/app/runtime/boxe.
```

## 7. Implementation Result

Implemented:

- `backend/app/modules/platform/game_modules/adapter.py`;
- `backend/app/modules/games/boxe/platform_client.py` now routes open/win/loss
  calls through `InProcessBoxePlatformAdapter`;
- `tests/contract/test_gmp2_boxe_adapter_contract.py`.

No runtime UI/CSS or game math files were changed.

Final verification on 2026-05-30:

- GMP-2 BOXE adapter/API batch: 60 passed.
- Site V3 account/player handoff browser batch: 7 passed.
- Canonical local smoke: 19 passed.
- `ck-doctor`: all local services healthy, `http://localhost:3000` serving Site
  V3.
- Game runtime/UI diff gate for BOXE, Mines and HI-LO: empty.
