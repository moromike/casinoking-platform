# BOXE Cell Size Consistency Approach

Status: ACTIVE - Wave 6 Parte A
Last meaningful update: 2026-05-21

Parte A is doc-only. Scope is limited to the BOXE pyramid visual sizing plan; Mines is the visual reference and must remain untouched in Parte B.

## 1. Problem

Michele observed that BOXE pyramid cells scale with the selected row count and with row width, especially on mobile. This breaks the Mines inheritance rule: a board can resize as a container, but individual cells should keep a stable visual rhythm instead of stretching because a row has fewer cells.

BOXE remains game-specific in geometry: the board is a bottom-to-top pyramid, not a Mines grid. The parity target is the cell sizing behavior, not the shape.

## 2. Sources Audited

| Source | Finding |
| --- | --- |
| `docs/games/boxe/SPEC.md:194` | BOXE board model starts at section 1.7. |
| `docs/games/boxe/SPEC.md:196` | The board is explicitly a pyramid of rows. |
| `docs/games/boxe/SPEC.md:200` | Row order is bottom to top. |
| `docs/games/boxe/SPEC.md:201` | Only one row is active at a time. |
| `frontend/app/ui/mines/mines-board.tsx:131` | Mines renders one `.mines-board` grid container. |
| `frontend/app/ui/mines/mines-board.tsx:133` | Mines columns are fixed from `boardSide`, not from per-row content. |
| `frontend/app/ui/mines/mines-board.tsx:135` | Mines renders `cellCount` cells in the stable grid. |
| `frontend/app/ui/mines/mines-gameplay.tsx:194` | Mines visible grid size comes from session/config. |
| `frontend/app/ui/mines/mines-gameplay.tsx:195` | Mines computes `boardSide` as the square root of the visible grid size. |
| `frontend/app/ui/mines/mines.css:830` | `.mines-board` is a grid with a bounded max width. |
| `frontend/app/ui/mines/mines.css:837` | `.board-cell` defines the common Mines cell surface. |
| `frontend/app/ui/mines/mines.css:843` | Mines cells keep square geometry through `aspect-ratio: 1`. |
| `frontend/app/ui/mines/mines.css:2229` | Runtime Mines board width is bounded by viewport/height constraints. |
| `frontend/app/ui/mines/mines.css:2239` | Desktop non-embedded Mines board uses a clamp-based board width, not per-row stretch. |
| `frontend/app/ui/mines/mines.css:2249` | Current visual skin overrides Mines cell styling while keeping the same board rhythm. |
| `frontend/app/ui/mines/mines.css:1536` | Mobile embedded Mines board constrains the board width. |
| `frontend/app/ui/mines/mines.css:1635` | Mobile Mines layout constrains the board to viewport and height. |
| `frontend/app/ui/mines/mines.css:3188` | Narrow mobile shell reduces board container/gap, not individual rows independently. |
| `frontend/app/ui/boxe/boxe-pyramid-board.tsx:17` | BOXE exposes `getBoxeCellsForRow(row, rows) = rows - row + 1`. |
| `frontend/app/ui/boxe/boxe-pyramid-board.tsx:38` | Visual rows render top-down while data row order remains bottom-to-top. |
| `frontend/app/ui/boxe/boxe-pyramid-board.tsx:54` | Each BOXE row derives its own `cellCount`. |
| `frontend/app/ui/boxe/boxe-pyramid-board.tsx:78` | BOXE passes `--boxe-row-cells` to CSS per row. |
| `frontend/app/ui/boxe/boxe.css:136` | `.boxe-pyramid-board` is the board container. |
| `frontend/app/ui/boxe/boxe.css:144` | `.boxe-pyramid-row` owns row-level grid sizing. |
| `frontend/app/ui/boxe/boxe.css:147` | Desktop BOXE cells use `clamp(38px, 5.2vw, 62px)`. |
| `frontend/app/ui/boxe/boxe.css:163` | `.boxe-pyramid-cell` keeps square geometry with `aspect-ratio: 1`. |
| `frontend/app/ui/boxe/boxe.css:655` | Mobile BOXE overrides rows to `repeat(..., minmax(28px, 1fr))`. |
| `frontend/app/ui/boxe/boxe.css:657` | Mobile BOXE rows are forced to `width: 100%`, causing fewer-cell rows to stretch. |
| `frontend/app/ui/boxe/boxe.css:693` | `.boxe-stage-board` hides overflow, which constrains the responsive strategy. |

## 3. Mines Board Sizing Pattern

Mines does not make each cell independently responsive by row. Its board pattern is:

| Layer | Mines behavior | Why it matters for BOXE |
| --- | --- | --- |
| Grid geometry | `MinesBoard` sets `gridTemplateColumns: repeat(boardSide, minmax(0, 1fr))` (`mines-board.tsx:133`). | The number of columns is stable for the board, so every cell in that board has the same size. |
| Cell geometry | `.board-cell` uses `aspect-ratio: 1` and `width: 100%` (`mines.css:843-845`). | The cell fills an equal grid track; the grid track is stable. |
| Desktop container | Runtime board width is bounded by `min(100%, clamp(...))` (`mines.css:2235-2240`). | The container scales, but the whole board scales together. |
| Mobile container | Mobile rules constrain board width/height and gap (`mines.css:1536-1538`, `1635-1638`, `3188-3191`). | Mobile adapts the board as one unit, not by stretching short rows. |
| Visual skin | The current skin changes border/background at `.board-cell` (`mines.css:2249-2257`). | BOXE can match the sizing discipline without copying Mines square-grid geometry. |

Conclusion: the inheritable rule is **stable per-cell size inside the visible board unit**. For BOXE, each pyramid row can have a different number of cells, but each cell in the pyramid should use the same size for a given breakpoint/state.

## 4. BOXE Current Sizing Problem

| Surface | Current BOXE behavior | Verdict |
| --- | --- | --- |
| Desktop row tracks | `.boxe-pyramid-row` uses `repeat(var(--boxe-row-cells), clamp(38px, 5.2vw, 62px))` (`boxe.css:147`). | Mostly stable per viewport, but still viewport-scaling rather than fixed token sizing. |
| Desktop row width | Row width is natural content width because tracks are fixed-ish clamp values. | Acceptable baseline, but should become explicit `max-content` with named variables. |
| Mobile row tracks | `@media (max-width: 460px)` changes to `repeat(var(--boxe-row-cells), minmax(28px, 1fr))` (`boxe.css:655-656`). | Gap: cell size depends on how many cells are in that row. |
| Mobile row width | Same mobile block sets `width: 100%` (`boxe.css:657`). | Gap: top rows stretch dramatically; bottom rows shrink, so pyramid cells are inconsistent. |
| Max cells | With `getBoxeCellsForRow(row, rows) = rows - row + 1`, 8 rows produce a 9-cell bottom row (`boxe-pyramid-board.tsx:17-18`). | The CSS strategy must handle 9 cells at max selected rows. |
| Overflow policy | `.boxe-stage-board` has `overflow: hidden` (`boxe.css:693-697`). | Risk: a fixed 9-cell pyramid can be clipped unless the board container owns scroll/scale deliberately. |

The critical bug is the mobile override. It intentionally stretches rows to full width, so row count and cell count change cell size. That is the opposite of the Mines board rhythm.

## 5. Proposed Parte B Fix

Implement this as a CSS-first change in `frontend/app/ui/boxe/boxe.css`. Do not touch Mines. Do not change board mechanics.

### 5.1 CSS Variables

Introduce explicit board sizing tokens on `.boxe-pyramid-board`:

```css
.boxe-pyramid-board {
  --boxe-pyramid-cell-size: 62px;
  --boxe-pyramid-cell-gap: 8px;
  --boxe-pyramid-max-cells: 9;
}
```

Rationale:

- `62px` matches the current desktop upper bound in `boxe.css:147`, so the first pass should not visually shrink the current preferred desktop board.
- `9` matches current maximum geometry for 8 rows via `rows - row + 1`.
- Named variables make the rule auditable and prevent future `1fr` row stretch from creeping back in.

### 5.2 Row Grid

Replace row track sizing with a fixed token per breakpoint:

```css
.boxe-pyramid-row {
  grid-template-columns: repeat(var(--boxe-row-cells), var(--boxe-pyramid-cell-size));
  gap: var(--boxe-pyramid-cell-gap);
  width: max-content;
  max-width: 100%;
}
```

Remove the mobile `minmax(28px, 1fr)` and `width: 100%` override. This is the direct fix for the observed stretch.

### 5.3 Board Container

Give the board a predictable maximum width based on the largest row:

```css
.boxe-pyramid-board {
  width: 100%;
  max-width: calc(
    var(--boxe-pyramid-max-cells) * var(--boxe-pyramid-cell-size)
    + (var(--boxe-pyramid-max-cells) - 1) * var(--boxe-pyramid-cell-gap)
  );
  justify-items: center;
}
```

If CSS `calc()` multiplication with custom properties is not supported consistently enough in the target browser matrix, use a precomputed value per breakpoint:

| Breakpoint | Cell | Gap | 9-cell row width |
| --- | ---: | ---: | ---: |
| Desktop/tablet | 62px | 8px | 622px |
| Portrait mobile | 36px | 5px | 364px |
| Short landscape | 32px | 4px | 320px |

Use precomputed widths only as CSS constants; do not add JavaScript unless max rows become dynamic beyond the current 4/6/8 range.

### 5.4 Component Change Policy

Default Parte B path: no change to `boxe-pyramid-board.tsx`.

Allowed fallback only if needed:

- Add a board-level CSS variable such as `--boxe-pyramid-max-cells` from `rows + 1`.
- Keep `getBoxeCellsForRow` unchanged.
- Do not change `picks`, `terminalStatus`, `pyramidFullReveal`, or reveal rendering.

This fallback is only justified if product later allows row counts above 8 or if CSS constants cannot cover the runtime range safely.

## 6. Mobile Strategy

BOXE must fit the worst supported geometry: 8 rows -> 9 cells in the bottom row.

Recommended mobile sizing:

| Context | Proposed tokens | Expected behavior |
| --- | --- | --- |
| Portrait mobile around 390px wide | `--boxe-pyramid-cell-size: 36px; --boxe-pyramid-cell-gap: 5px;` | 9-cell bottom row is 364px, fitting inside a 390px viewport with tight stage padding. |
| Very narrow portrait | `--boxe-pyramid-cell-size: 34px; --boxe-pyramid-cell-gap: 4px;` | Keeps board visible without row-specific stretching. |
| Landscape rotation / short height | `--boxe-pyramid-cell-size: 32px; --boxe-pyramid-cell-gap: 4px;` | Keeps 8 rows vertically readable and avoids clipping by controls. |
| If viewport is still too narrow | Prefer board-level horizontal overflow/scroll or stage-level scale, not `1fr` per row. | Every row keeps equal cell size; the board adapts as one unit. |

Important: do not restore `width: 100%` on `.boxe-pyramid-row`. If a scroll container is needed, the scroll belongs to `.boxe-pyramid-board` or a board viewport wrapper, not to each row.

Touch-target trade-off:

- A 36px mobile visual cell is smaller than the common 44px touch target.
- A strict 44px cell makes the 9-cell row about 428px wide with 4px gaps, requiring horizontal scroll on 390px portrait.
- Recommendation: start with 36px no-scroll for parity/readability, then ask CTO/product only if accessibility policy requires 44px minimum touch targets for game cells.

## 7. Gate Visual Plan

Parte B must ship screenshot evidence, not just CSS inspection.

| Gate | Viewport | Configs | Evidence |
| --- | --- | --- | --- |
| Desktop pyramid | 1365x768 | rows 4, 6, 8 | BOXE screenshots prove same cell size across top/middle/bottom rows. |
| Mobile portrait | 390x844 | rows 4, 6, 8 | BOXE screenshots prove no full-width stretched top rows. |
| Landscape rotation | 844x390 | rows 8 | BOXE screenshot proves no clipping by `.boxe-stage-board`. |
| Mines reference | Same desktop/mobile viewports | Current Mines grid | Side-by-side reference for stable board/cell rhythm. |
| Runtime state | idle + active + terminal reveal | rows 8 preferred | Safe/mine assets still render centered after sizing changes. |
| Regression boundary | CSS scan | `.boxe-pyramid-*` only | No changes under `frontend/app/ui/mines/`; no backend changes. |

Verdict table for Parte B should separate:

- `match`: cell rhythm and fixed sizing behavior inherits Mines.
- `game-specific`: pyramid row count/shape differs by SPEC section 1.7.
- `gap`: any row-specific cell stretch remains.

## 8. Parte B Granularity

| Commit | Scope | Files |
| --- | --- | --- |
| `fix(boxe): use fixed pyramid cell sizing tokens` | Add CSS variables, fixed row tracks, remove mobile `1fr` row stretch. | `frontend/app/ui/boxe/boxe.css` |
| `fix(boxe): tune pyramid responsive board viewport` | Mobile/landscape tokens and overflow policy if needed. | `frontend/app/ui/boxe/boxe.css` |
| `test(visual): add boxe fixed cell sizing evidence` | Screenshot artifacts and verdict table. | `tests/visual/artifacts/...` and/or approach doc update |

Expected effort: 3-5 prompts for implementation plus screenshot gate. If Playwright setup is already warm from prior waves, this should stay near the low end.

## 9. Stop-and-Ask

Stop and ask CTO if any of these happen in Parte B:

| Trigger | Reason |
| --- | --- |
| Product requires 44px minimum touch target and no horizontal scroll on 390px portrait. | 9 cells cannot fit at 44px without either scroll, scale, or layout trade-off. |
| Supported BOXE row counts expand beyond 8. | CSS max-cells constant `9` would become invalid; component-level max-cells var may be needed. |
| CSS-only fix clips the board because `.boxe-stage-board` hides overflow. | May require a small board viewport wrapper or stage overflow policy, touching more than `.boxe-pyramid-*`. |
| Matching exact Mines pixel cell size is requested. | Mines is a 5-column square grid; BOXE is a 9-cell max pyramid, so exact cell pixels would force different overall board footprint. |
| Any fix needs changes under `frontend/app/ui/mines/` or backend. | Violates the hard constraints for this WP. |

## 10. Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE fixed pyramid cell sizing | N/A | N/A | N/A | N/A | Planned | Planned | Planned visual gate | This doc | Proposed | CSS-only preferred; removes row-specific mobile stretch. |
| Mines zero-diff | N/A | N/A | N/A | N/A | Required | Required | Required screenshot/reference gate | This doc | Guardrail | Mines files must remain untouched. |
| Board runtime behavior | N/A | Unchanged | Unchanged | N/A | Unchanged | Sizing-only | Smoke/visual | This doc | Guardrail | No change to picks/reveal/payout/state machine. |

## 11. Files Read

Actually read for this approach:

- `docs/README.md`
- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`
- `docs/games/boxe/SPEC.md` section 1.7 excerpt
- `frontend/app/ui/mines/mines.css`
- `frontend/app/ui/mines/mines-board.tsx`
- `frontend/app/ui/mines/mines-gameplay.tsx`
- `frontend/app/ui/boxe/boxe.css`
- `frontend/app/ui/boxe/boxe-pyramid-board.tsx`
- `frontend/app/ui/boxe/boxe-gameplay.tsx`

Not read because outside this doc-only WP:

- Backend BOXE math/service files.
- Backoffice files.
- Runtime smoke tests.
