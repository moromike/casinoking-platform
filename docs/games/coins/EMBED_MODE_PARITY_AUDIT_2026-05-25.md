Status: ACTIVE
Last meaningful update: 2026-05-25

# Embed Mode Parity Audit - BOXE / HI-LO

Scope: prerequisite before COINS. Mines already had iframe postMessage behavior;
BOXE and HI-LO had embed CSS/flags but no close/fullscreen handshake.

## 1. Audit

| Game | CSS embed | `isEmbeddedView` | Close postMessage before | Fullscreen receive before | Resolution |
| --- | --- | --- | --- | --- | --- |
| Mines | `mines-page-shell-embedded`, `mines-product-shell-embedded` | yes | legacy `casinoking:mines-close` | legacy `casinoking:mines-fullscreen-state` | Migrated to shared bridge while keeping legacy messages. |
| BOXE | reuses Mines embed shell classes plus BOXE classes | yes | missing | missing | Consumes shared bridge with `gameCode: "boxe"`. |
| HI-LO | `hi-lo-page-shell-embedded`, `hi-lo-product-shell-embedded` | yes | missing | missing | Consumes shared bridge with `gameCode: "hi_lo"`. |

## 2. Contract

Shared bridge file:

- `frontend/app/ui/game-runtime/use-game-embed-bridge.ts`

Outbound:

- generic: `{ type: "casinoking:game-close", gameCode }`;
- legacy compatibility: `{ type: "casinoking:<game-code>-close" }`.

Inbound:

- generic fullscreen: `{ type: "casinoking:game-fullscreen-state", gameCode, active }`;
- legacy compatibility: `{ type: "casinoking:<game-code>-fullscreen-state", active }`.

Origin policy:

- default accepted/target origin: `window.location.origin`;
- optional third-party host origin: `?embed_origin=<absolute-origin-url>`;
- direct parent DOM access is not used.

## 3. Implementation Notes

- Mines keeps visible behavior and admin launcher compatibility.
- `casinoking-console.tsx` now sends both legacy and generic fullscreen-state
  messages to the embedded Mines iframe and accepts both close messages.
- BOXE and HI-LO call `requestEmbedClose()` after their normal access/table
  cleanup; if no parent iframe is available they still navigate to `/`.
- The shared hook is game-agnostic: no `if gameCode === "mines" / "boxe" /
  "hi_lo"` branch lives inside the bridge.

## 4. Contract Tests

Updated `tests/contract/test_game_runtime_frontend_boundary.py` to assert:

- the bridge lives in `game-runtime/`;
- it declares generic close/fullscreen message types;
- the bridge has no game-specific branches;
- Mines, BOXE and HI-LO standalone wrappers consume the same hook;
- the admin console still supports Mines legacy embed launcher behavior.

## 5. Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Game embed bridge - hook platform | n/a | n/a | n/a | n/a | NEW | n/a | NEW | UPDATE | green | Generic + legacy compatibility. |
| BOXE embed handshake | n/a | n/a | n/a | n/a | REFACTOR | unchanged | NEW | UPDATE | green | Close/fullscreen-state supported. |
| HI-LO embed handshake | n/a | n/a | n/a | n/a | REFACTOR | unchanged | NEW | UPDATE | green | Close/fullscreen-state supported. |
| Mines embed migration to bridge | n/a | n/a | n/a | compatible | REFACTOR | unchanged | UPDATE | UPDATE | green | Legacy messages retained. |
| Third-party iframe readiness | n/a | n/a | n/a | n/a | REFACTOR | unchanged | NEW | UPDATE | partial-green | Requires host to pass `embed_origin` when cross-origin. |

