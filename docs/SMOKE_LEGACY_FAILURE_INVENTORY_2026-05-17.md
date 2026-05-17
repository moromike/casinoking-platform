Status: ACTIVE
Last meaningful update: 2026-05-17

# Smoke Legacy Failure Inventory - 2026-05-17

Status: active tracking report. Original audit baseline retained.

Baseline:

- Branch: `audit/smoke-legacy-11-failure-inventory`
- Main reference: `79310d7 merge: clarify upload dimensions and rendering`
- Command:

```powershell
python -m pytest tests/integration/test_mines_embed_browser_smoke.py -q
```

Result:

```text
11 failed, 26 passed in 238.95s
```

The 17 `test_boot_*` cases are inside the same file and passed. The original
11 failures are in the legacy non-boot browser smoke area.

Closure updates:

- WP-SMOKE-1 closed failures #1, #2, #7, and #11 in commit `cd7670e`
  (`test: modernize mines smoke launch selectors`), reducing the open legacy
  smoke failures from 11 to 7.
- WP-SMOKE-2 closed failures #3, #4, #5, and #6 by splitting the mobile
  contract into playable portrait and landscape-short rotation gate behavior,
  reducing the open legacy smoke failures from 7 to 3.

## Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Full Mines browser smoke legacy inventory | n/a | observed only | observed only | n/a | observed only | observed only | audited failing smoke file | this report | INVENTORIED | No production logic changed. Wallet, ledger, RNG, payout, fairness and math untouched. |

## Failure Inventory

| # | Test | What Fails | Likely Cause | Effort | Priority | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `test_mines_desktop_launcher_keeps_only_outer_close_action` | Closed by WP-SMOKE-1. | Launch Cashier recovery changed lobby cards from direct links to buttons that open a launch modal. The test still assumed the old direct launcher entry. | S | Medium | RESOLVED in `cd7670e`: test now opens a player lobby card, asserts the Launch Cashier close action, and launches the enabled demo option. |
| 2 | `test_mines_embed_desktop_controls_do_not_overlap_actions` | Closed by WP-SMOKE-1. | The selector was text-bound to legacy `.field` + `Mines` copy/markup. Current UI/copy is title-driven. | S | Medium | RESOLVED in `cd7670e`: test uses structural config selectors and a published non-master demo variant before asserting layout metrics. |
| 3 | `test_mines_mobile_surface_stays_inside_viewport_on_short_screens[/mines?title_code=mines_classic-375-667]` | Closed by WP-SMOKE-2. | The old 220 px portrait board assertion was stricter than the accepted playable rendering. | M | High | RESOLVED in WP-SMOKE-2: portrait contract is >=200 px, with current 216 px rendering accepted. |
| 4 | `test_mines_mobile_surface_stays_inside_viewport_on_short_screens[/mines?title_code=mines_classic-882-344]` | Closed by WP-SMOKE-2. | Landscape-short is not a supported playable surface. | M | High | RESOLVED in WP-SMOKE-2: landscape-short below 400 px height shows the rotation gate instead of requiring Collect visibility. |
| 5 | `test_mines_mobile_surface_stays_inside_viewport_on_short_screens[/mines?title_code=mines_classic&embed=1-375-667]` | Closed by WP-SMOKE-2. | Same portrait contract revision as #3, now in embedded mode. | M | High | RESOLVED in WP-SMOKE-2: embedded portrait uses the same >=200 px contract. |
| 6 | `test_mines_mobile_surface_stays_inside_viewport_on_short_screens[/mines?title_code=mines_classic&embed=1-882-344]` | Closed by WP-SMOKE-2. | Same landscape-short product decision as #4. | M | High | RESOLVED in WP-SMOKE-2: embedded landscape-short shows the rotation gate. |
| 7 | `test_mines_demo_loss_reveals_all_mines_before_session_refresh` | Closed by WP-SMOKE-1. | Test uses variant `mines001b`, whose runtime copy can be localized/customized. The action text is no longer guaranteed to be English `Bet`. | S | Medium | RESOLVED in `cd7670e`: test uses the structural submit action instead of English action copy. |
| 8 | `test_mines_resume_prefers_active_game_session_over_stored_access_session_id` | Helper `_browser_create_access_session` gets `422 Master titles cannot be launched publicly`. | Test creates an access session without a mutable/public variant title. Current backend correctly blocks public launch of the master title. | S | High | Rewrite helper setup to use a published non-master variant or explicit preview context. |
| 9 | `test_mines_launch_token_auth_error_blocks_runtime_without_logout` | Cannot click button named `Bet`. | Test enters `/mines` directly with only an access token, but the current real-mode flow needs a valid launch/access context before betting. | M | High | Rebuild the test around the current launch-token boundary, then assert the safety overlay. |
| 10 | `test_mines_access_session_conflict_shows_expired_overlay_and_locks_surface` | Expected expired-session overlay is not visible. | Test mocks access-session ping conflict without first establishing the current access-session runtime context. The ping may not fire or may target a different state. | M | High | Seed/access the runtime through the current launch flow, then force ping conflict. |
| 11 | `test_mines_embed_shows_only_published_mine_choices_for_selected_grid` | Closed by WP-SMOKE-1. | Selector was text-bound to legacy `.field` + `Mines` label. Current UI/copy structure is title/localization driven. | S | Medium | RESOLVED in `cd7670e`: test reads mine choices from the structural Mines config section. |

## Patterns

1. **Launch flow changed but legacy smoke still assumes direct entry.**
   Lobby card launch is now mediated by Launch Cashier. Tests that click a
   homepage `Mines` link or enter real mode with only a token are no longer
   aligned with the product flow.

2. **Master title public launch is now correctly blocked.**
   A failing helper still creates access sessions without a variant
   `title_code`, so it hits the backend guard against public master launch.

3. **Text-bound selectors are brittle.**
   Several tests locate controls by visible English strings such as `Bet` or by
   a `.field` containing `Mines`. Runtime copy is title/localization driven, so
   these tests should use stable semantic selectors or resolve the configured
   copy.

4. **Mobile viewport assertions were split by product contract.**
   Portrait 375x667 remains playable with a >=200 px board contract. Very short
   landscape viewports are intentionally gated with a rotate-device message.

5. **Safety overlay tests need current access-session setup.**
   Auth error/conflict tests still target the old access path. They remain
   important, but their setup must go through the current launch/access-session
   boundary.

## Proposed Closure WPs

### WP-SMOKE-1 - Modernize Legacy Smoke Selectors And Launch Entry

Scope:

- Update homepage/lobby smoke to use the current Launch Cashier entry.
- Replace text-bound control selectors with stable semantic selectors where
  possible.
- Fix published mine choice and demo loss tests without changing gameplay code.

Closed failures: #1, #2, #7, #11 in commit `cd7670e`.

Effort: M.

Priority: Medium.

### WP-SMOKE-2 - Decide And Fix Mobile Short-Viewport Contract

Scope:

- Portrait 375x667: revise the old 220 px assertion to the accepted >=200 px
  playable contract.
- Landscape-short: add a rotation gate below 400 px height and update the smoke
  assertion to expect the gate.

Closed failures: #3, #4, #5, #6 in WP-SMOKE-2.

Effort: M.

Priority: High.

### WP-SMOKE-3 - Rewrite Real-Mode Access Session Safety Smokes

Scope:

- Use a published non-master variant or preview launch context.
- Seed a valid current access session through the current runtime flow.
- Reassert:
  - active game session wins over stale stored access session;
  - launch-token auth error blocks runtime without logging out;
  - access-session conflict shows the expired overlay and locks betting.

Expected failures covered: #8, #9, #10.

Effort: M.

Priority: High.

## Recommendation

Do not fix these inside BOXE prep. Close the remaining access-session safety
tests as a dedicated smoke debt WP before using the full browser smoke as a
release gate.
