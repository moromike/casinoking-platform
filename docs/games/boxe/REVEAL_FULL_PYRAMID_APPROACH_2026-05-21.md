# BOXE Full Pyramid Reveal Approach

Status: ACTIVE - Wave 4 Parte B
Last meaningful update: 2026-05-21

Parte A is doc-only. The product decision is locked: on loss and cashout, BOXE reveals the full pyramid, matching the Mines terminal reveal pattern conceptually.

## 1. Change Summary

Current SPEC behavior says future rows remain hidden and loss reveals only the current row. Wave 4 changes that:

```text
During active round: future rows remain hidden.
Terminal loss: reveal the full pyramid.
Terminal cashout: reveal the full pyramid.
Replay/history: consume the same server-authoritative terminal reveal payload.
```

## 2. Sources Audited

| Source | Finding |
| --- | --- |
| `docs/games/boxe/SPEC.md:194` | Board model defines bottom-to-top pyramid. |
| `docs/games/boxe/SPEC.md:204` | Current spec keeps unpicked future rows hidden until reached. |
| `docs/games/boxe/SPEC.md:205` | Current spec says loss reveal is current row only. |
| `docs/games/boxe/SPEC.md:400` | Replay currently describes current-row reveal behavior. |
| `docs/games/boxe/ARCHITECTURE_ATLAS_BOXE.md:273` | Frontend opacity is used because backend does not expose full board contents. |
| `backend/app/modules/games/mines/service.py:937` | Mines loss returns server-stored mine positions. |
| `backend/app/modules/games/mines/service.py:992` | Mines final safe auto-win returns full mine positions. |
| `backend/app/modules/games/mines/service.py:1129` | Mines cashout returns full mine positions. |
| `backend/app/modules/games/mines/service.py:740` | Mines replay exposes full terminal positions only when round is closed. |
| `frontend/app/ui/mines/mines-standalone.tsx:1189` | Mines reveal maps terminal mine positions into UI state. |
| `frontend/app/ui/mines/mines-board.tsx:127` | Mines board renders server-provided mine positions. |
| `backend/app/modules/games/boxe/randomness.py:32` | BOXE currently evaluates only the selected box. |
| `backend/app/modules/games/boxe/service.py:357` | BOXE reveal response does not include full pyramid reveal. |
| `backend/app/modules/games/boxe/service.py:513` | BOXE cashout response does not include full pyramid reveal. |
| `backend/app/modules/games/boxe/service.py:721` | BOXE replay payload has picks/safe path/current row, not full pyramid. |
| `backend/migrations/sql/0039__boxe_session_tables.sql:136` | BOXE persists picks, not a full board snapshot. |
| `frontend/app/ui/boxe/use-boxe-runtime.ts:40` | Reveal response type lacks full reveal field. |
| `frontend/app/ui/boxe/use-boxe-runtime.ts:49` | Cashout response type lacks full reveal field. |
| `frontend/app/ui/boxe/boxe-gameplay.tsx:438` | UI appends selected pick only. |
| `frontend/app/ui/boxe/boxe-pyramid-board.tsx:46` | Board infers terminal row visuals client-side. |
| `tests/integration/test_boxe_smoke.py:220` | Existing smoke expects current loss row opacity behavior. |

## 3. Mines Pattern

Mines terminal reveal is server-authoritative:

1. The backend stores board mine positions.
2. Active gameplay hides unrevealed positions.
3. Loss/cashout/complete responses return terminal mine positions.
4. Replay exposes those positions only after the round is closed.
5. The frontend renders payload truth; it does not invent board contents.

BOXE should follow this pattern with a pyramid payload instead of a flat mine list.

## 4. BOXE Current Gap

BOXE currently does not have server-side full pyramid contents. The service evaluates whether the selected cell is safe/mine for the current action and the frontend visually infers unrevealed cells.

This is sufficient for active gameplay but not for:

| Need | Current status |
| --- | --- |
| Full terminal reveal | Missing |
| Deterministic replay of all row contents | Missing |
| Player trust/fairness inspection | Partial |
| Cashout reveal parity with Mines | Missing |
| Replay Surface 11 | Blocked/partial |

## 5. Proposed SPEC Update

Replace the current SPEC 1.7 reveal language with:

```text
Active round:
- Rows above the active row remain hidden.
- Reached rows show selected safe picks and row state allowed by the current interaction.

Terminal round:
- Loss reveal: full pyramid reveal.
- Cashout reveal: full pyramid reveal.
- Completed top-row win reveal: full pyramid reveal.
- The reveal payload is server-authoritative and must be replay-safe.

Replay/history:
- Replay uses the same terminal full-pyramid payload. Client-side generated filler cells are not authoritative.
```

## 6. Payload Proposal

Add a terminal-only field to reveal/cashout/replay responses:

```json
{
  "pyramid_full_reveal": [
    {
      "row": 0,
      "cells": [
        {
          "position": 0,
          "state": "safe",
          "picked": true,
          "reveal_scope": "picked_path"
        },
        {
          "position": 1,
          "state": "mine",
          "picked": false,
          "reveal_scope": "terminal_full_reveal"
        }
      ]
    }
  ]
}
```

Rules:

| Rule | Decision |
| --- | --- |
| Active responses | Omit `pyramid_full_reveal` or return `null`. |
| Terminal responses | Include every row and every cell. |
| Cell geometry | Use `cells_for_row(row, rows) = rows - row + 1`. |
| Row mine counts | Must match the BOXE math/difficulty contract once row-content generation is defined. |
| Frontend authority | Render payload exactly on terminal; no client-side synthetic mines/safes. |

## 7. Server-Authoritative Design Options

| Option | Description | Pros | Cons | Recommendation |
| --- | --- | --- | --- | --- |
| A. Precompute and persist full board at session start | Store all row cell states before first pick. | Best replay/fairness story, simple terminal reveal. | Requires schema/storage change. | Preferred if fairness policy allows exposing commitment later. |
| B. Derive terminal full reveal from session seed on close | Generate full board deterministically from server seed/action context when terminal. | Smaller storage change. | Must prove idempotency and replay stability. | Acceptable if persisted snapshot is considered too large. |
| C. Client-derived reveal | Frontend invents non-picked cells. | Easy. | Not authoritative, fails replay/fairness. | Reject. |

## 8. Frontend Rendering Impact

| File | Expected Parte B change |
| --- | --- |
| `frontend/app/ui/boxe/use-boxe-runtime.ts` | Add response types for `pyramid_full_reveal`. |
| `frontend/app/ui/boxe/boxe-gameplay.tsx` | Store terminal full reveal in gameplay state and clear it on new round. |
| `frontend/app/ui/boxe/boxe-pyramid-board.tsx` | Render full payload when terminal status is loss/cashout/win. Active state stays current pyramid behavior. |
| `frontend/app/ui/boxe/boxe.css` | Only terminal reveal styling if existing `.boxe-pyramid-*` classes cannot express it. Avoid unrelated board redesign. |

Important: Wave 4 Parte B must not rework board geometry again. It should only add a terminal payload render path.

## 9. Backend Impact

| Area | Expected Parte B change |
| --- | --- |
| Randomness/fairness | Add deterministic full-board/pyramid generation contract. |
| Session persistence | Persist full board or enough seed material to regenerate the exact board. |
| Reveal action | On loss/top-row terminal, include `pyramid_full_reveal`. |
| Cashout action | Include `pyramid_full_reveal`. |
| Replay endpoint | Include terminal full reveal for closed sessions. |
| Idempotency | Replayed response for the same idempotency key must return the same full reveal. |
| Tests | Update smoke that expects current-row-only reveal. |

`backend/app/modules/games/boxe/math.py` should remain unchanged unless the full-board generation exposes a mismatch between row mine counts and current probability model.

## 10. Parte B Granularity

| Sub-WP | Scope | Estimate |
| --- | --- | --- |
| REVEAL-B1 spec/API contract | Update SPEC, DTO types, response examples. | 2-3 prompts |
| REVEAL-B2 backend board generation | Implement server-authoritative full pyramid reveal and idempotency. | 5-8 prompts |
| REVEAL-B3 replay/history integration | Persist/expose terminal reveal in replay and history. | 3-5 prompts |
| REVEAL-B4 frontend render path | Render terminal payload in board/gameplay state. | 3-5 prompts |
| REVEAL-B5 tests/evidence | Backend integration, smoke, replay, terminal visual screenshots. | 3-4 prompts |

Total expected effort: 16-25 prompts. This should coordinate with WP-REPLAY because replay payload shape is shared.

## 11. Stop-and-Ask

| Trigger | Category | Ask |
| --- | --- | --- |
| Need to choose precompute/persist vs derive-on-close. | D | Ask CTO which server-authoritative storage model is preferred. |
| Full-board row mine counts conflict with current probability ladder. | C/D | Stop and decide whether BOXE uses explicit mine counts or probability-derived outcomes. |
| Idempotency cannot return the same full reveal after retry. | C | Stop before shipping. |
| Replay WP proposes a different payload shape. | D | Serialize with WP-REPLAY and choose one payload contract. |

## 12. 12-Surface Impact

| Surface | Impact |
| --- | --- |
| 7 Gameplay shell | Direct. Terminal board reveal changes visible gameplay. |
| 11 Replay | Direct. Replay needs full pyramid to be deterministic and useful. |
| 12 Resume/disconnect | Direct. Resumed terminal sessions must restore the same reveal. |
| 10 Backoffice editor | Indirect. Rules/copy must describe full terminal reveal. |
| 5 Info/how-to-play | Indirect. Rules modal should describe terminal reveal behavior. |

## 13. Parte B Final Decision

Chosen design: **derive-deterministic-from-seed at terminal close**.

Rationale:

- BOXE's delivered math contract is probability-based per step/position, not a
  fixed mine-count board contract.
- Precomputing and persisting a board at start would require schema expansion
  without improving replay determinism, because the existing server seed,
  client seed and nonce already reproduce every cell outcome.
- Terminal reveal uses the same backend RNG material as normal reveal actions.
  The frontend only renders `pyramid_full_reveal`; it does not invent hidden
  future cells.

Payload contract:

- Active reveal responses omit `pyramid_full_reveal`.
- Terminal loss, cashout and top-row win responses include
  `pyramid_full_reveal`.
- Replay includes the same `pyramid_full_reveal` for terminal rounds.
- Payload rows are bottom-to-top, with cell geometry
  `cells_for_row(row, rows) = rows - row + 1`.

## 14. Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Terminal loss full pyramid reveal | No schema change | Deterministic seed-derived reveal | `pyramid_full_reveal` on `failed_mine` | N/A | Board renders all cells on terminal | Existing safe/mine classes | API + browser smoke | SPEC + approach | Complete | Future rows remain hidden until terminal. |
| Terminal cashout full pyramid reveal | No schema change | Deterministic seed-derived reveal | `pyramid_full_reveal` on `completed_cashout` | N/A | Board renders all cells on terminal | Existing safe/mine classes | API + browser smoke | SPEC + approach | Complete | Idempotency stores the terminal response payload. |
| Terminal top-row win full pyramid reveal | No schema change | Deterministic seed-derived reveal | `pyramid_full_reveal` on `completed_top_row` | N/A | Board renders all cells on terminal | Existing safe/mine classes | API + browser smoke | SPEC + approach | Complete | Auto-collect path uses same reveal contract. |
| Replay deterministic full pyramid | No schema change | Replay regenerates from persisted seed material | Replay includes `pyramid_full_reveal` | N/A | WP-REPLAY can consume explicit payload | N/A | Replay determinism test | SPEC + approach | Complete | Repeated replay responses match terminal cashout reveal. |
| Active-round secrecy | No schema change | Active responses omit full reveal | No `pyramid_full_reveal` before terminal | N/A | Future rows stay hidden while active | Existing future styling | API assertion | SPEC + approach | Complete | Preserves Mines-style terminal-only reveal boundary. |
