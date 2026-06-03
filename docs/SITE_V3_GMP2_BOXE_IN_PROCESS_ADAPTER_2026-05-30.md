Status: IMPLEMENTED - first in-process BOXE adapter slice
Last meaningful update: 2026-05-30

# Site V3 - GMP-2 BOXE In-Process Adapter

## 0. Scope

GMP-2 implements the first backend Platform Adapter extraction for BOXE.

This is not a service split and not a gameplay rewrite. It keeps all existing
BOXE endpoint paths, payloads, wallet/ledger behavior, settlement policy, RNG,
fairness, payout and replay behavior unchanged.

## 1. What Changed

- Added `backend/app/modules/platform/game_modules/adapter.py`.
- Added typed launch/session/storage/embed/replay descriptors.
- Added typed `PlatformGameAdapter` protocol and open/settle request/result
  dataclasses.
- Routed BOXE `open_round`, `settle_win` and `settle_loss` through
  `InProcessBoxePlatformAdapter` in
  `backend/app/modules/games/boxe/platform_client.py`.
- Preserved the existing BOXE function exports consumed by
  `round_gateway.py` and `service.py`.
- Added contract coverage in
  `tests/contract/test_gmp2_boxe_adapter_contract.py`.

## 2. What Did Not Change

- No DB schema change.
- No API route or payload change.
- No wallet or ledger semantic change.
- No settlement, RNG, fairness or payout change.
- No BOXE gameplay UI/CSS change.
- No package/service split.
- No Mines or HI-LO code change.

## 3. Current Boundary

BOXE still runs in-process. The new shape is:

```text
BOXE service/round_gateway
  -> BOXE platform_client compatibility functions
  -> InProcessBoxePlatformAdapter
  -> platform rounds/table-session services
```

The compatibility functions are intentionally kept so this slice does not force
API/service churn. The adapter request/result dataclasses are the new contract
surface for later extraction.

## 4. Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Typed adapter interfaces | none | `platform/game_modules/adapter.py` | none | none | none | none | contract | this doc/GMP docs | Green | Host-neutral dataclasses and protocol added. |
| BOXE open round facade | none | `boxe/platform_client.py` | unchanged | none | unchanged | none | contract + BOXE API | this doc | Green | Existing function export now builds a typed adapter request. |
| BOXE settlement facade | none | `boxe/platform_client.py` | unchanged | none | unchanged | none | contract + BOXE API | this doc | Green | Win/loss settlement still calls existing platform services in-process. |
| Runtime/game UI boundary | none | unchanged | unchanged | none | unchanged | no change | diff gate | this doc | Green | No edits under BOXE runtime UI or runtime route. |

## 5. Verification

Completed verification for this slice:

- `python -m pytest tests/contract/test_gmp2_boxe_adapter_contract.py tests/integration/test_boxe_api.py -q`
  passed: 60 tests.
- `python -m pytest tests/integration/test_player_account_statement_browser_smoke.py tests/integration/test_site_v3_player_handoff_browser.py -q`
  passed: 7 tests.
- `.\scripts\ck-test-smoke.ps1` passed: 19 tests.
- `.\scripts\ck-doctor.ps1` passed: all local services healthy and Site V3
  served from `http://localhost:3000`.
- `git diff --check` passed with line-ending warnings only.
- `git diff --name-only -- frontend-v3/app/ui/boxe frontend-v3/app/runtime/boxe frontend-v3/app/ui/mines frontend-v3/app/runtime/mines frontend-v3/app/ui/hi-lo frontend-v3/app/runtime/hi-lo`
  returned no files.

During verification,
`tests/integration/test_player_account_statement_browser_smoke.py` was made
configuration-aware for Mines published grid/mine combinations. This is a test
stability fix only; no Mines runtime, UI, math, payout, replay, wallet or
ledger code was changed.

## 6. Next Step

GMP-3 should extend the same adapter shape toward host-neutral launch/storage
and replay descriptor consumption without moving services yet.

Do not start a physical package/service split until BOXE proves parity through
the adapter and a mock non-CasinoKing host can launch demo mode.
