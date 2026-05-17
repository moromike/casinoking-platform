# Smoke Legacy Failure Inventory - 2026-05-17

Status: audit-only report. No code fixes applied.

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

The 17 `test_boot_*` cases are inside the same file and passed. The 11 failures
are in the legacy non-boot browser smoke area.

## Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Full Mines browser smoke legacy inventory | n/a | observed only | observed only | n/a | observed only | observed only | audited failing smoke file | this report | INVENTORIED | No production logic changed. Wallet, ledger, RNG, payout, fairness and math untouched. |

## Failure Inventory

| # | Test | What Fails | Likely Cause | Effort | Priority | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | `test_mines_desktop_launcher_keeps_only_outer_close_action` | Cannot find homepage link role `link` named `Mines`. | Launch Cashier recovery changed lobby cards from direct links to buttons that open a launch modal. The test still assumes the old direct launcher entry. | S | Medium | Rewrite around current lobby card/cashier flow, or retire if covered by Launch Cashier tests. |
| 2 | `test_mines_embed_desktop_controls_do_not_overlap_actions` | `mine_labels` is empty, causing `IndexError`. | The selector is text-bound to legacy `.field` + `Mines` copy/markup. Current UI no longer exposes that exact text path after shell/copy changes. | S | Medium | Update selector to a stable data/semantic target before using it as layout coverage. |
| 3 | `test_mines_mobile_surface_stays_inside_viewport_on_short_screens[/mines?title_code=mines_classic-375-667]` | Board height is 216 px, below expected 220 px. | Mobile viewport contract is stricter than current rendering after shell/skin/layout changes. This may be a small real UX regression or an over-specific threshold. | M | High | Needs CTO/product decision: preserve 220 px minimum or revise the contract. |
| 4 | `test_mines_mobile_surface_stays_inside_viewport_on_short_screens[/mines?title_code=mines_classic-882-344]` | Collect button is not fully visible. | Landscape-short mobile layout no longer satisfies the old "board and Collect visible without scroll" contract. | M | High | Same WP as #3. This is the strongest candidate for a real layout fix. |
| 5 | `test_mines_mobile_surface_stays_inside_viewport_on_short_screens[/mines?title_code=mines_classic&embed=1-375-667]` | Board height is 216 px, below expected 220 px. | Same mobile viewport contract mismatch as #3, now in embedded mode. | M | High | Same WP as #3. |
| 6 | `test_mines_mobile_surface_stays_inside_viewport_on_short_screens[/mines?title_code=mines_classic&embed=1-882-344]` | Collect button is not fully visible. | Same landscape-short embedded contract mismatch as #4. | M | High | Same WP as #3. |
| 7 | `test_mines_demo_loss_reveals_all_mines_before_session_refresh` | Cannot click button named `Bet`. | Test uses variant `mines001b`, whose runtime copy can be localized/customized. The action text is no longer guaranteed to be English `Bet`. | S | Medium | Use a stable control selector or resolve the published action copy before clicking. |
| 8 | `test_mines_resume_prefers_active_game_session_over_stored_access_session_id` | Helper `_browser_create_access_session` gets `422 Master titles cannot be launched publicly`. | Test creates an access session without a mutable/public variant title. Current backend correctly blocks public launch of the master title. | S | High | Rewrite helper setup to use a published non-master variant or explicit preview context. |
| 9 | `test_mines_launch_token_auth_error_blocks_runtime_without_logout` | Cannot click button named `Bet`. | Test enters `/mines` directly with only an access token, but the current real-mode flow needs a valid launch/access context before betting. | M | High | Rebuild the test around the current launch-token boundary, then assert the safety overlay. |
| 10 | `test_mines_access_session_conflict_shows_expired_overlay_and_locks_surface` | Expected expired-session overlay is not visible. | Test mocks access-session ping conflict without first establishing the current access-session runtime context. The ping may not fire or may target a different state. | M | High | Seed/access the runtime through the current launch flow, then force ping conflict. |
| 11 | `test_mines_embed_shows_only_published_mine_choices_for_selected_grid` | Mine choice list is empty instead of published values. | Selector is text-bound to legacy `.field` + `Mines` label. Current UI/copy structure no longer matches, even though config may be valid. | S | Medium | Same selector modernization as #2. |

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

4. **Mobile viewport assertions may represent real UX debt.**
   The short-screen mobile failures are not just selector failures: the measured
   board size and Collect visibility miss the old contract. This deserves a
   product/UX decision before changing CSS or weakening the test.

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

Expected failures covered: #1, #2, #7, #11.

Effort: M.

Priority: Medium.

### WP-SMOKE-2 - Decide And Fix Mobile Short-Viewport Contract

Scope:

- Reproduce the four mobile viewport failures visually.
- Decide whether the old contract is still required:
  - board minimum 220 px portrait / 160 px landscape;
  - Collect visible without scroll on short screens;
  - settings summary visible.
- If required, apply focused CSS/layout fixes.
- If no longer required, update the test contract with CTO approval.

Expected failures covered: #3, #4, #5, #6.

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

Do not fix these inside BOXE prep. Close them as dedicated smoke debt WPs before
using the full browser smoke as a release gate. The mobile viewport group should
be triaged first because it is the only group that clearly may indicate a real
player-facing layout regression instead of only stale test assumptions.
