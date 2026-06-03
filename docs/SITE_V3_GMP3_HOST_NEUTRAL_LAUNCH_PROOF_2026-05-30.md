Status: IMPLEMENTED - in-process host-neutral BOXE launch proof
Last meaningful update: 2026-05-30

# Site V3 - GMP-3 Host-Neutral Launch Proof

## 0. Scope

GMP-3 proves the next portability slice for BOXE without moving packages,
services or runtime UI.

This slice adds host-neutral launch/storage/embed/replay descriptor consumption
to platform launch responses and proves that a non-CasinoKing site publication
can issue a BOXE demo launch token.

## 1. What Changed

- Extended descriptor dataclasses in
  `backend/app/modules/platform/game_modules/adapter.py`.
- Added descriptor builders in
  `backend/app/modules/platform/game_modules/descriptors.py`.
- Added launch/storage/embed/replay descriptor payloads to real and demo launch
  responses in `backend/app/modules/platform/game_launch/service.py`.
- Added optional host fields to `/demo/launch`:
  `host_code`, `brand_code`, `return_url`, `locale`, `embed_origin`,
  `correlation_id`.
- Allowed `/games/boxe/config` to validate a supplied `site_code`, so a mock
  host publication can read BOXE config without falling back to CasinoKing.
- Updated the BOXE lobby browser test to use a temporary Site V3 page instead
  of client-side route mocks that no longer apply after Site V3 server-side
  rendering.

## 2. What Did Not Change

- No gameplay UI/CSS changes.
- No game math, RNG, fairness, payout or replay renderer changes.
- No wallet, ledger or settlement semantic changes.
- No physical package or service split.
- No Mines or HI-LO runtime/UI changes.
- No CMS/admin registration surface for portable modules yet.

## 3. Proof

The proof uses BOXE and a temporary non-CasinoKing site code:

```text
mock host site publication
  -> /demo/token
  -> /demo/launch game_code=boxe title_code=boxe001 site_code=<mock>
  -> host-neutral descriptors returned with storage namespace
     host.<mock>.game.boxe
```

The negative proof verifies that BOXE launch on an unpublished mock site returns
`VALIDATION_ERROR` instead of falling back to CasinoKing publication.

## 4. Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Host-neutral launch descriptor | none | launch service + descriptor builder | added descriptor object | none | unchanged | none | contract + integration | this doc | Green | Includes host/brand/site/locale/return/correlation/storage namespace. |
| Host-neutral storage descriptor | none | descriptor builder | added descriptor object | none | unchanged | none | contract + integration | this doc | Green | Namespace is host/site scoped, not `casinoking.*`. |
| Replay descriptor payload | none | descriptor builder | added descriptor object | none | unchanged | none | contract | this doc | Green | BOXE replay endpoints are explicit and no unknown-game fallback is introduced. |
| Mock non-CasinoKing demo launch | temporary test site row | demo launch validates site publication | existing `/demo/launch` plus optional host fields | none | unchanged | none | integration | this doc | Green | Proves demo launch token and descriptors for a non-CasinoKing site. |
| BOXE config site validation | none | BOXE config accepts optional `site_code` | query param only | none | unchanged | none | integration | this doc | Green | Avoids CasinoKing fallback when a host-specific config read is requested. |

## 5. Verification

Completed verification:

- `python -m pytest tests/contract/test_gmp3_host_neutral_descriptors.py tests/integration/test_gmp3_host_neutral_demo_launch.py -q`
  passed: 4 tests.
- `python -m pytest tests/unit/test_platform_game_agnostic_adapter.py tests/integration/test_boxe_lobby_launch.py -q`
  passed: 9 tests.
- `python -m pytest tests/contract/test_gmp2_boxe_adapter_contract.py tests/integration/test_boxe_api.py -q`
  passed: 60 tests.
- `python -m pytest tests/integration/test_player_account_statement_browser_smoke.py tests/integration/test_site_v3_player_handoff_browser.py -q`
  passed: 7 tests.
- `python -m pytest tests/contract/test_game_runtime_storage.py tests/contract/test_game_reporting_registry.py tests/contract/test_finance_replay_metadata_contract.py tests/contract/test_game_runtime_frontend_boundary.py tests/contract/test_site_v3_runtime_extraction_contract.py -q`
  passed: 31 tests.
- `.\scripts\ck-test-smoke.ps1` passed: 19 tests.
- `.\scripts\ck-doctor.ps1` passed: all local services healthy and Site V3
  served from `http://localhost:3000`.
- `npm run lint` in `frontend-v3` passed.
- `npm run build` in `frontend-v3` passed.
- `git diff --check` passed with line-ending warnings only.
- Game runtime/UI diff gate for BOXE, Mines and HI-LO returned no files.

## 6. Next Step

GMP-4 is decided in
`docs/SITE_V3_GMP4_PACKAGING_SERVICE_DECISION_2026-05-30.md`:
package-first, service-later.

The selected next step is GMP-5: a mock non-CasinoKing host integration kit,
starting with BOXE and keeping deployment in-process. Do not create a backend
service or move frontend runtime UI/CSS in GMP-5.

Deferred targets:

- separate frontend runtime package after mock host, mobile, replay, audio and
  i18n gates;
- separate backend game service/RGS mock after HTTP Platform Adapter,
  idempotency, timeout and reconciliation gates.

The decision must include ownership, deployment, versioning, test gates and
rollback expectations before implementation.
