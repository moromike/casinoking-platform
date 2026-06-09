Status: ACTIVE
Last meaningful update: 2026-05-21

# BOXE - Reset On Config Change Approach

## Scope

Wave 6 Parte A, doc-only. This WP covers the visual/state bug where a terminal
BOXE round remains on screen after the player changes `rows` or `difficulty`.
No production code is changed in this document.

## Files Actually Read

| File | Why |
| --- | --- |
| `docs/README.md` | Operational entry point and reading order. |
| `docs/SOURCE_OF_TRUTH.md` | Project precedence and architecture constraints. |
| `docs/TASK_EXECUTION_GUARDRAILS.md` | Scope, no-extra-UI and final-check rules. |
| `docs/DOCUMENTATION_MAINTENANCE.md` | Documentation update rules. |
| `docs/AI_CRITICAL_JUDGMENT_RULES.md` | Critical judgment rule for fragile inheritance. |
| `docs/games/boxe/SPEC.md` | Section 1.7 board model and 1.8 difficulty semantics. |
| `frontend/app/ui/boxe/boxe-gameplay.tsx` | BOXE state machine and board props. |
| `frontend/app/ui/boxe/boxe-settings-panel.tsx` | Rows/difficulty control wiring. |
| `frontend/app/ui/boxe/boxe-pyramid-board.tsx` | Board render inputs. |
| `frontend/app/ui/mines/mines-standalone.tsx` | Mines selected config, session reset and start flow. |
| `frontend/app/ui/mines/mines-gameplay.tsx` | Mines board presentation cleanup and controls. |
| `frontend/app/ui/mines/mines-board.tsx` | Mines board render contract. |
| `tests/integration/test_boxe_smoke.py` | Current BOXE smoke coverage and selectors. |
| `tests/integration/test_mines_embed_browser_smoke.py` | Mines browser behavior around config/start/reset. |

## Executive Verdict

The bug is a frontend state ownership bug in `BoxeGameplay`. BOXE keeps the
terminal `round`, `picks` and `pyramidFullReveal` after cashout/loss/top-row
completion. The board receives `rows={round?.rows ?? selectedRows}`, so changing
`selectedRows` after a terminal round does not affect the rendered board until a
new round starts.

Mines is a partial reference, not a perfect one: it clears the terminal board
when the grid size changes, but mine-count-only changes do not clear the
terminal session snapshot. For BOXE, both `rows` and `difficulty` define the
visible board/payout state, so the correct product-safe behavior is stricter:
after a terminal round, any `rows` or `difficulty` change clears the terminal
round presentation and returns the board to idle for the newly selected config.

## 1. BOXE State Machine Audit

| Area | Current state | File:lines | Finding |
| --- | --- | --- | --- |
| Selected config | `selectedRows` and `selectedDifficulty` are local state initialized from runtime defaults. | `frontend/app/ui/boxe/boxe-gameplay.tsx:149-152` | These are the idle config controls. |
| Round state | `round`, `picks` and `pyramidFullReveal` are independent local state. | `frontend/app/ui/boxe/boxe-gameplay.tsx:158-161` | Terminal board data can outlive config changes. |
| Terminal detection | `terminalStatus = readTerminalStatus(round?.status ?? null)` and `isRoundActive = round !== null && terminalStatus === null`. | `frontend/app/ui/boxe/boxe-gameplay.tsx:190-191` | Terminal rounds still keep `round !== null`. |
| Active row | Active row derives from safe picks only while active. | `frontend/app/ui/boxe/boxe-gameplay.tsx:193-196` | After terminal, `activeRow` becomes `null`, but old board/reveal remains. |
| Settings lock | Settings are disabled only when the round is active or an action is busy. | `frontend/app/ui/boxe/boxe-gameplay.tsx:216` | Terminal rounds allow config changes, as intended. |
| Runtime config fallback | Effects only correct invalid selected values against enabled rows/difficulties. | `frontend/app/ui/boxe/boxe-gameplay.tsx:265-280` | No cleanup is performed when selected config changes. |
| Start flow | Starting clears `picks`, `pyramidFullReveal` and replay state before API call. | `frontend/app/ui/boxe/boxe-gameplay.tsx:371-376` | Cleanup exists for start, not for config changes. |
| Start response | `round` stores the chosen `rows`, `difficulty`, multipliers and status. | `frontend/app/ui/boxe/boxe-gameplay.tsx:488-509` | Terminal board continues to point at this old round. |
| Reveal response | Mine/top-row terminal responses set `pyramidFullReveal`; safe picks append to `picks`. | `frontend/app/ui/boxe/boxe-gameplay.tsx:511-548` | Terminal reveal is intentionally sticky until a new state transition. |
| Cashout response | Cashout updates `round.status`, `collectAmount` and `pyramidFullReveal`. | `frontend/app/ui/boxe/boxe-gameplay.tsx:550-568` | Cashout creates the stale-terminal-board case. |
| Settings wiring | `BoxeSettingsPanel` receives direct `setSelectedRows` / `setSelectedDifficulty`. | `frontend/app/ui/boxe/boxe-gameplay.tsx:596-605` | There is no interception point to clear terminal presentation. |
| Settings controls | Rows/difficulty chips call `onRowsChange` and `onDifficultyChange`; disabled is respected. | `frontend/app/ui/boxe/boxe-settings-panel.tsx:31-43`, `frontend/app/ui/boxe/boxe-settings-panel.tsx:48-60` | The fix can be local handler wrappers, no component API change required. |
| Board render | Board receives `picks`, `pyramidFullReveal`, `terminalStatus` and `rows={round?.rows ?? selectedRows}`. | `frontend/app/ui/boxe/boxe-gameplay.tsx:769-779` | Root cause: terminal `round.rows` wins over changed `selectedRows`. |
| Mobile summary | Summary chips display `selectedRows` / `selectedDifficulty`. | `frontend/app/ui/boxe/boxe-gameplay.tsx:782-799` | UI can show new config while board still shows old terminal state. |
| Board component | Pyramid renders exactly the `rows` prop and terminal reveal map. | `frontend/app/ui/boxe/boxe-pyramid-board.tsx:21-44`, `frontend/app/ui/boxe/boxe-pyramid-board.tsx:50-115` | Board is not at fault; input state is stale. |

## 2. Mines Comparative Pattern

| Pattern | Mines behavior | File:lines | BOXE implication |
| --- | --- | --- | --- |
| Selected config state | `selectedGridSize` and `selectedMineCount` live in `MinesStandalone`. | `frontend/app/ui/mines/mines-standalone.tsx:211-212` | BOXE keeps equivalent state inside `BoxeGameplay`. |
| Active lock | `isActiveRound = currentSession?.status === "active"`. | `frontend/app/ui/mines/mines-standalone.tsx:275-287` | Active rounds are not configurable. |
| Control config while active | Mines buttons are disabled when `busyAction !== null || isActiveRound || isInteractionLocked`. | `frontend/app/ui/mines/mines-gameplay.tsx:680-708` | BOXE already has the same active-lock intent. |
| Visible board source | Mines board uses `visibleGridSize = currentSession ? currentSession.grid_size : selectedGridSize`. | `frontend/app/ui/mines/mines-gameplay.tsx:192-202` | Same stale-session risk exists unless the terminal session is cleared. |
| Presentation cleanup | When `currentSession` becomes `null`, `MinesGameplay` clears round presentation and replay state. | `frontend/app/ui/mines/mines-gameplay.tsx:253-259`, `frontend/app/ui/mines/mines-gameplay.tsx:300-320` | BOXE needs an equivalent local cleanup because it owns `round` directly. |
| Start cleanup | Mines clears the current session snapshot before starting. | `frontend/app/ui/mines/mines-standalone.tsx:1108-1111` | BOXE already clears on start; the missing case is post-terminal config change. |
| Grid change cleanup | `handleGridSizeChange` ignores active/busy/no-op, updates grid, updates default mine count, then clears the current session snapshot. | `frontend/app/ui/mines/mines-standalone.tsx:1411-1419` | This is the closest reference for BOXE rows change. |
| Session clear helper | `clearCurrentSessionSnapshot` sets `currentSession(null)` and clears stored session id. | `frontend/app/ui/mines/mines-standalone.tsx:1406-1409` | BOXE has no equivalent helper for local terminal round state. |
| Mine count caveat | Mines passes `onMineCountChange={updateSelectedMineCount}` and the update helper only mutates selected state. | `frontend/app/ui/mines/mines-standalone.tsx:596-606`, `frontend/app/ui/mines/mines-standalone.tsx:1623-1628` | Do not inherit this part blindly; for BOXE difficulty changes the payout ladder and visible state must reset. |
| Browser smoke reference | Mines test asserts the old board is cleared while a new start is pending. | `tests/integration/test_mines_embed_browser_smoke.py:1631-1683` | BOXE Parte B should add a smaller targeted smoke for config-change cleanup. |

## 3. Proposed Fix

Implement in `frontend/app/ui/boxe/boxe-gameplay.tsx` only.

1. Add a local cleanup helper:

```ts
function clearTerminalRoundForConfigChange() {
  setRound(null);
  setPicks([]);
  setPyramidFullReveal(null);
  setReplayState({ roundId: null, replay: null, loading: false, error: null });
  setCelebration(null);
  setErrorText("");
  setRetryAction(null);
  setInfoTab("rules");
}
```

The exact helper name can be adjusted, but it should remain local to BOXE
because this is game-specific board state.

2. Replace direct setters with guarded handlers:

```ts
function handleRowsChange(rows: number) {
  if (isInteractionLocked || isRoundActive || rows === selectedRows) return;
  setSelectedRows(rows);
  if (terminalStatus !== null) clearTerminalRoundForConfigChange();
}

function handleDifficultyChange(difficulty: string) {
  if (isInteractionLocked || isRoundActive || difficulty === selectedDifficulty) return;
  setSelectedDifficulty(difficulty);
  if (terminalStatus !== null) clearTerminalRoundForConfigChange();
}
```

3. Wire `BoxeSettingsPanel` to these handlers instead of direct state setters.

4. Extend the existing runtime-config fallback effects so that an automatic
fallback from an invalid selected row/difficulty also clears terminal state when
`terminalStatus !== null`. This covers a backoffice publish/config refresh edge
case without adding backend behavior.

5. Keep `BoxePyramidBoard` unchanged. It will naturally render idle rows from
`selectedRows` after `round` is cleared.

6. Keep backend unchanged. This is a player UI state reset, not a round lifecycle
or payout change.

### State That Must Be Cleared

| State | Clear? | Reason |
| --- | --- | --- |
| `round` | Yes | Removes old `round.rows`, `round.difficulty`, `roundId`, terminal status and multipliers. |
| `picks` | Yes | Removes old safe/mine picks from board. |
| `pyramidFullReveal` | Yes | Removes old terminal reveal. |
| `replayState` | Yes | It is keyed to the old `roundId`. |
| `celebration` | Yes | Prevents old win/cashout subtitle after config change. |
| `errorText` / `retryAction` | Yes | Retry actions may reference old round or old config. |
| `betAmount` | No | Mines does not reset bet when changing config. |
| `demoBalance` / wallets | No | Balance is not part of visual board state. |
| `showRules` | No, but reset `infoTab` to `rules` | Avoid closing a modal unexpectedly; avoid replay tab pointing to a cleared round. |

### Replay Note

Current BOXE replay availability is `Boolean(round?.roundId)` in
`boxe-gameplay.tsx:874-893`. Clearing `round` means the replay tab will no longer
target the just-finished round after a config change. This matches the requested
"reset board state (picks, activeRow, round/live round id, terminal reveal)".

If Product wants "last completed replay remains accessible even after config
change", Parte B should add a separate `lastReplayRoundId` like Mines'
`lastReplaySessionId` pattern (`frontend/app/ui/mines/mines-gameplay.tsx:164`,
`frontend/app/ui/mines/mines-gameplay.tsx:267`, `frontend/app/ui/mines/mines-gameplay.tsx:434`).
Do not add that without CTO confirmation because it expands the task from board
reset to replay retention.

## 4. Active-Round Edge Case

Product decision proposed:

| State | Rows/difficulty click behavior | Rationale |
| --- | --- | --- |
| Idle, no round | Change selected config, render idle board immediately. | Normal setup flow. |
| Active round | Ignore/disable config change until terminal. | Mines reference disables config chips during active rounds. |
| Busy action | Ignore/disable config change until request settles. | Prevents race between API state and visual state. |
| Terminal round | Change selected config and clear terminal board/reveal immediately. | Fixes the reported bug and aligns with "new config means new board preview". |

BOXE already disables settings during active/busy via `settingsDisabled`
(`frontend/app/ui/boxe/boxe-gameplay.tsx:216`) and `GameChipGroup disabled`
(`frontend/app/ui/boxe/boxe-settings-panel.tsx:31-60`). Parte B should still
put the same guard in handlers to cover race conditions or synthetic events.

## 5. Parte B Tests And Gates

### Targeted tests

Add/extend `tests/integration/test_boxe_smoke.py`.

1. `test_boxe_config_change_after_cashout_resets_terminal_board`
   - Start 4-row EASY round.
   - Reach safe state and cash out.
   - Assert full pyramid reveal is visible.
   - Click `boxe-rows-6`.
   - Assert:
     - `.boxe-pyramid-row` count is 6.
     - `.boxe-pyramid-cell.safe`, `.boxe-pyramid-cell.mine` and `.boxe-pyramid-cell.opaque` counts are 0.
     - `boxe-primary-action` is the Bet action and enabled.
     - Next `POST /games/boxe/start` payload uses `rows: 6`.

2. `test_boxe_difficulty_change_after_loss_resets_terminal_board`
   - Start 4-row EASY round.
   - Hit a mine.
   - Assert full pyramid reveal is visible.
   - Click `boxe-difficulty-hard`.
   - Assert terminal reveal is gone and idle board remains for selected rows.
   - Next start payload uses `difficulty: "hard"`.

3. Active-round lock smoke
   - Start round.
   - Assert rows and difficulty chips are disabled.
   - Confirm no selected config mutation during active round.

4. Mobile portrait smoke
   - Complete terminal round in 390x844 viewport.
   - Open mobile settings sheet, change rows or difficulty.
   - Assert board resets and summary chips match the idle board.

### Existing gates

| Gate | Expected |
| --- | --- |
| `test_boxe_demo_safe_sequence_cashout_resets_to_bet` | PASS, still validates baseline cashout lifecycle. |
| New BOXE config-change smokes | PASS. |
| Mines smoke subset | PASS, no code touched under `frontend/app/ui/mines/`. |
| `npm run build` | PASS. |
| `npm run lint:i18n` | PASS if run as standard frontend gate. |
| Screenshot evidence | Before/after terminal cashout plus rows change, terminal loss plus difficulty change, mobile settings change. |

## 6. Capability Matrix For Parte B

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Reset terminal board on rows change | n/a | n/a | n/a | n/a | `BoxeGameplay` clears local terminal state | n/a | New smoke | SPEC unchanged | Planned | Fixes stale `round.rows`. |
| Reset terminal board on difficulty change | n/a | n/a | n/a | n/a | `BoxeGameplay` clears local terminal state | n/a | New smoke | SPEC unchanged | Planned | Fixes stale payout/reveal state. |
| Active-round config lock | n/a | n/a | n/a | n/a | Preserve disabled controls and add handler guard | n/a | New/updated smoke | SPEC unchanged | Planned | Mirrors Mines behavior. |
| Runtime fallback cleanup | n/a | n/a | n/a | n/a | Existing fallback effects clear terminal state when auto-changing selection | n/a | Unit/static or browser smoke if feasible | SPEC unchanged | Planned | Covers published config changes. |

## 7. Commit Granularity For Parte B

1. `fix(boxe): reset terminal board when config changes`
   - Local helper and rows/difficulty handlers in `boxe-gameplay.tsx`.
   - No backend, no Mines, no CSS.

2. `test(boxe): cover terminal board reset on config changes`
   - Playwright integration smoke for cashout/loss + rows/difficulty changes.
   - Mobile case can be in same commit if compact; split if it grows.

3. `docs(boxe): record config reset closure`
   - Only if Parte B changes docs/brief/current closure notes.

## 8. Effort Estimate

| Step | Estimate |
| --- | --- |
| Implement local BOXE state helper/handlers | 1 prompt |
| Add browser smoke tests and stabilize selectors | 1-2 prompts |
| Run build/smoke and capture evidence | 1 prompt |
| Closure docs/report | 0.5 prompt |

Total: 3-5 prompts, assuming no hidden Playwright flake.

## 9. Stop-And-Ask

| Trigger | Why |
| --- | --- |
| Product wants replay of the previous terminal round to remain available after config change. | Requires a `lastReplayRoundId` pattern, expanding beyond reset. |
| Mines mine-count-only behavior is declared canonical and must be fixed too. | Current task says Mines invariant; fixing Mines would be a separate WP. |
| Backend/session lifecycle must be changed to close or forget rounds on config change. | Not needed for this bug and risks round/audit semantics. |
| Runtime config fallback needs to mutate selected values while a round is active. | Active config mutation would violate Mines-like lock behavior. |
| Tests reveal BOXE settings are clickable during active/busy despite disabled UI. | That becomes a behavior bug in `GameChipGroup` or event wiring and should be scoped explicitly. |

## 10. Parte A Conclusion

Proceed to Parte B with a BOXE-only frontend fix. The safest behavior is:

- active/busy: rows and difficulty remain locked;
- terminal: changing either rows or difficulty clears `round`, picks, full reveal,
  stale replay state and celebration;
- idle: changing config updates the idle pyramid immediately.

No backend or Mines changes are required for this WP.
