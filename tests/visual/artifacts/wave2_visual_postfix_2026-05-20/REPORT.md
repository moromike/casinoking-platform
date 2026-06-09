# Wave 2 Visual Postfix Evidence - 2026-05-20

Reference: Mines on `http://localhost:3000`.
Target: BOXE on `http://localhost:3100`.

## Screenshots

Pre-fix side-by-side:

- `pre_side_by_side_idle_desktop.png`
- `pre_side_by_side_active_desktop.png`
- `pre_side_by_side_win_desktop.png`
- `pre_side_by_side_idle_mobile_portrait.png`
- `pre_side_by_side_active_mobile_portrait.png`
- `pre_side_by_side_landscape_rotation.png`

Post-fix side-by-side:

- `post_side_by_side_idle_desktop.png`
- `post_side_by_side_active_desktop.png`
- `post_side_by_side_win_desktop.png`
- `post_side_by_side_idle_mobile_portrait.png`
- `post_side_by_side_active_mobile_portrait.png`
- `post_side_by_side_landscape_rotation.png`

Raw captures are under `pre_raw/` and `post_raw/`.

## Divergence Table

| # | Surface | Pre-fix observation | Post-fix observation | Verdict |
| ---: | --- | --- | --- | --- |
| 1 | Product shell width/position | BOXE card was centered with large outer margins; Mines embed shell fills the viewport. | BOXE uses Mines shell/embed classes and fills the viewport like Mines. | Match |
| 2 | Desktop macro layout | BOXE rendered a full-width topbar and then a nested play surface; Mines uses left rail + right stage/board. | BOXE uses left rail + right stage/board. | Match |
| 3 | Desktop close button | BOXE showed `X` in embed mode; Mines hides close in embed. | BOXE close is hidden in embed. | Match |
| 4 | Stage title placement | BOXE title lived in a topbar spanning rail and board. | BOXE title lives in the stage header over the board. | Match |
| 5 | Payout placement | BOXE multipliers sat between topbar and play surface. | BOXE multipliers sit under the stage title like Mines. | Match |
| 6 | Payout content count | BOXE shows row-count-driven multipliers; Mines shows a five-step preview. | BOXE styling/placement matches; count/value remain game-specific. | Game-specific justified |
| 7 | Rail header tools | BOXE used shared game icon styling but rail was lower in a nested panel. | Info, Rome clock, audio and DEMO badge align with Mines rail. | Match |
| 8 | Rows/difficulty chips | BOXE difficulty chips compressed/overlapped after first shared pass. | BOXE uses flex choice chips; no overlap. | Match |
| 9 | Quick bet chips | BOXE quick chips used a separate game-chip look and sizing. | BOXE uses Mines `quick-chip` sizing and active state. | Match |
| 10 | Bet input | BOXE input was in a BOXE-only rail block. | BOXE input uses Mines field style and spacing. | Match |
| 11 | Bet/Collect labels | BOXE used uppercase `BET`/`COLLECT amount`. | BOXE uses Mines-style `Bet`/`Collect`; amount moved out of button. | Match |
| 12 | Active demo balance | BOXE demo balance stayed at `100` after start. | BOXE applies local demo debit; active state shows `95` with a 5 chip bet. | Match |
| 13 | Balance footer typography | BOXE labels were uppercase and cards were flattened by local overrides. | BOXE uses Mines compact balance cards and non-uppercase labels. | Match |
| 14 | Mobile layout order | BOXE showed controls above the board. | BOXE uses Mines order: stage, board, balance, bet/actions, settings summary. | Match |
| 15 | Mobile stage tools | BOXE mobile clock label and audio overlapped the short BOXE title. | BOXE hides the mobile clock label and uses compact tools; title remains readable. | Match |
| 16 | Landscape short viewport gate | BOXE had custom Italian rotate copy. | BOXE uses the default Mines gate copy and placement. | Match |
| 17 | Win state overlay | BOXE rendered a central Win overlay and dimmed the board; Mines uses stage subtitle. | BOXE overlay removed; win is shown in stage subtitle. | Match |
| 18 | Board geometry | BOXE is a pyramid; Mines is a 5x5 grid. | Difference remains by game design. | Game-specific justified |
| 19 | Board reveal assets | BOXE uses diamond/mine asset pipeline; Mines uses Mines symbols. | Difference remains by game design. | Game-specific justified |
| 20 | Settings summary copy | BOXE mobile summary says rows/difficulty; Mines says grid/mines. | Control placement/style matches; labels are game-specific. | Game-specific justified |

Final verdict: BOXE matches Mines at the player shell/control/stage level; remaining visual differences are the BOXE pyramid board, multiplier count/value, and game-specific settings labels.
