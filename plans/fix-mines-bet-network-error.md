# Fix Plan: Mines Bet Button NetworkError + Layout Shift

## Final Outcome (2026-03-31)

This plan started from an incomplete diagnosis and is now superseded by the implemented result.

- The Bet failure was **not** a frontend-only network issue.
- The actual blocking bug was a backend round-start failure in [`start_session()`](../backend/app/modules/games/mines/service.py), where the split-schema flow was inserting the Mines round without first creating the matching `platform_rounds` row.
- The frontend error handling issue was still real and was fixed in [`MinesStandalone()`](../frontend/app/ui/mines/mines-standalone.tsx).
- The remaining visual issue on the left desktop rail was resolved only after replacing the generic wrapping option rows with a deterministic grid-based layout in [`MinesStandalone()`](../frontend/app/ui/mines/mines-standalone.tsx) and [`globals.css`](../frontend/app/globals.css).

### Implemented changes

- Backend: restored `platform_rounds` creation in the Mines round start flow.
- Frontend: improved error banner behavior and message clarity.
- Frontend: rewrote the Mines desktop left rail layout to avoid fragile `flex-wrap` behavior for option chips.

### Verified result

- `POST /games/mines/start` returns success again.
- The desktop left rail no longer misaligns the `Bet amount` block.
- The error banner no longer pushes the full game layout.

## Bug Report Summary

1. **UI shifts** when the error banner appears/disappears
2. **Bet button does nothing** — clicking it triggers a network call that fails silently (grid remains changeable)
3. **Error message**: `"Round launch failed. NetworkError when attempting to fetch resource."`
4. **Same on mobile**
5. **Error messages appear in random places** (secondary concern, noted for future)

---

## Root Cause Analysis

> Note: the sections below capture the initial investigation path. The final root cause is documented in [`Final Outcome`](plans/fix-mines-bet-network-error.md).

### Bug 1: NetworkError on Bet click

**FACT**: The error `"NetworkError when attempting to fetch resource."` is a **browser-level fetch failure**. This means the HTTP request never reaches the backend at all. It is NOT a CORS error (those produce `"CORS request did not succeed"` or similar).

**FACT**: The frontend calls `fetch("http://localhost:8000/api/v1/games/mines/start", ...)` from `apiRequest()` in `api.ts:42`.

**FACT**: The `handleStartSession()` flow in `mines-standalone.tsx:393-435` does:
1. If no `accessToken`, calls `prepareDemoAccessToken()` first (POST `/auth/demo`)
2. Then calls `ensureGameLaunchToken()` (POST `/games/mines/launch-token` + POST `/games/mines/launch/validate`)
3. Then calls `apiRequest("/games/mines/start", ...)` with POST

**HYPOTHESIS**: The `/auth/demo` and/or `/games/mines/launch-token` calls succeed (since the user sees "DEMO MODE" badge and has 1000 CHIP balance), but the `/games/mines/start` call fails with a NetworkError. This could be caused by:

- **Backend is down or unreachable** at the moment of the `/start` call — unlikely if other calls work
- **CORS preflight fails for the `/start` endpoint specifically** — the `Idempotency-Key` and `X-Game-Launch-Token` custom headers trigger a CORS preflight (OPTIONS request). If the backend doesn't handle the preflight correctly for these headers, the browser blocks the actual request with a NetworkError.

**KEY INSIGHT**: Looking at `main.py:15-21`, CORS is configured with `allow_headers=["*"]` which should handle custom headers. However, the `CORS_ALLOWED_ORIGINS` env var defaults to `http://localhost:3000`. If the user is accessing the frontend from a different origin (e.g., `http://127.0.0.1:3000`, or a mobile device on the LAN like `http://192.168.x.x:3000`), the CORS preflight will fail, causing a NetworkError.

**MOST LIKELY ROOT CAUSE**: The user is accessing the app from an origin that doesn't match `CORS_ALLOWED_ORIGINS`. On mobile, this is almost certainly the case — the phone accesses `http://<LAN-IP>:3000` but CORS only allows `http://localhost:3000`.

**SECONDARY POSSIBILITY**: The backend container is not running or crashed. The initial config/fairness/wallet calls may have been cached or succeeded earlier, but `/start` fails because the backend is now down.

### Bug 2: Bet button appears to "do nothing"

**FACT**: After the NetworkError, `handleStartSession` catches the error at line 428 and sets `setStatus({ kind: "error", text: ... })`. Then `setBusyAction(null)` runs in `finally`.

**FACT**: The `isBetDisabled` prop at line 714 is `busyAction !== null || currentSession?.status === "active"`. After the error, `busyAction` is reset to `null` and `currentSession` is still `null`, so the Bet button becomes enabled again. The grid also remains changeable because `isActiveRound` is `false`.

**CONCLUSION**: The Bet button IS working — it fires the request, gets a NetworkError, shows the error banner, and resets. The user can then change the grid because no session was created. The "nothing happens" perception is because the error banner appears at the top and may not be noticed, especially on mobile.

### Bug 3: Layout shift when error banner appears

**FACT**: The error banner is rendered at line 769:
```tsx
{visibleStatus ? <div className={`status-banner ${visibleStatus.kind}`}>{visibleStatus.text}</div> : null}
```

**FACT**: There is NO CSS definition for `.status-banner` in `globals.css` (search returned 0 results). This means the banner is an unstyled `<div>` that gets inserted into the document flow, pushing everything below it down.

**CONCLUSION**: The layout shift is caused by the error banner being conditionally rendered without any CSS to position it outside the normal flow (e.g., `position: absolute/fixed`). When it appears, it pushes the entire game UI down.

---

## Fix Plan

### Fix A: Resolve the NetworkError (PRIMARY)

This is likely an environment/configuration issue, not a code bug. However, we should make the app more resilient:

**A1. Verify backend is running and reachable**
- Check if docker containers are up
- Check if `http://localhost:8000/api/v1/health/ready` responds

**A2. Fix CORS for non-localhost access**
- Update `CORS_ALLOWED_ORIGINS` in `.env` to include the actual origin being used
- For development, consider adding `http://127.0.0.1:3000` and LAN IPs
- Document this in the README

### Fix B: Fix the layout shift (CSS)

**File**: `frontend/app/globals.css`

Add CSS for `.status-banner` inside the mines product shell to use absolute/fixed positioning so it doesn't push content:

```css
.mines-product-shell > .status-banner {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  padding: 8px 16px;
  font-size: 0.85rem;
  /* auto-dismiss or at least don't shift layout */
}
```

The `mines-product-shell` already has `overflow: hidden` and needs `position: relative` to contain the absolute banner.

### Fix C: Improve error visibility

**File**: `frontend/app/ui/mines/mines-standalone.tsx`

- Add auto-dismiss for error messages (e.g., `setTimeout` to clear status after 5-6 seconds)
- This prevents the error banner from permanently occupying space

### Fix D: Better error feedback on Bet failure

**File**: `frontend/app/ui/mines/mines-standalone.tsx`

- When the Bet fails, the user should clearly see what happened
- The current `readErrorMessage(error, "Round launch failed.")` produces `"Round launch failed. NetworkError when attempting to fetch resource."` which is technical
- Consider a more user-friendly message for network errors specifically

---

## Files to Touch

| File | Change | Risk |
|------|--------|------|
| `frontend/app/globals.css` | Add `.status-banner` positioning rules for mines shell | Low — CSS only |
| `frontend/app/ui/mines/mines-standalone.tsx` | Add auto-dismiss timer for error status | Low — UX improvement |
| `infra/docker/.env.example` | Document CORS origins for mobile/LAN access | None — docs |

## Files NOT to Touch

- Backend routes — no code bug there
- `api.ts` — working correctly
- `mines-action-buttons.tsx` — wiring is correct

## Acceptance Criteria

1. Error banner does NOT cause layout shift — it overlays the content
2. Error banner auto-dismisses after ~5 seconds
3. If backend is reachable and CORS is correct, Bet creates a session successfully
4. Grid becomes locked after successful Bet (already works when session starts)

## Risks

- The NetworkError may be purely environmental (backend not running). Code fixes won't help if the backend is down.
- If the user is testing on mobile via LAN, CORS must be configured for the LAN IP.

## Open Questions

- Is the backend actually running when the Bet is clicked? Need to verify.
- What origin is the browser using? (localhost vs LAN IP vs 127.0.0.1)
