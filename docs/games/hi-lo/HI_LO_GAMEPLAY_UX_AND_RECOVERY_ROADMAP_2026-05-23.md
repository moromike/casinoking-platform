# HI-LO Gameplay UX And Recovery Roadmap - 2026-05-23

Status: active planning after first product playtest on `localhost:3000`.

Scope: HI-LO gameplay area and HI-LO-specific recovery behavior only. Do not touch the shared game shell, shared control rail primitives, Mines, BOXE, or backend platform abstractions unless a bug proves the platform contract is wrong.

## 1. Product Feedback Summary

Observed during product playtest:

1. A blocking modal showed `Azione richiesta / Connessione instabile. Riprova` and the player could not escape.
2. Real-money HI-LO cashout could fail and leave the UI in an unrecoverable error state.
3. Replay exists technically, but it is not discoverable enough from gameplay.
4. Mobile gameplay hides functional elements that are visible on desktop: Skip, seed/history panel, and recent cards.
5. Mobile card/layout can look clipped or cramped.
6. Desktop gameplay area is functional but not polished enough: the card should be the protagonist, centered and visually clear.
7. The card should be more synthetic: rank + suit/color must be readable at a glance.
8. Backoffice `Games -> HI-LO` still needs a visual/content pass: spacing, theme field applicability, title management, and text alignment.

## 2. Root Cause And Recovery Policy

Root cause found for the blocking real-money crash:

- HI-LO real cashout closed `platform_rounds.status` as `cashed_out`.
- The platform round status contract accepts terminal statuses such as `won`, `lost`, and `cancelled`.
- The database rejected the write, backend returned 500, and the frontend mapped it to a generic unstable connection message.

Recovery policy for HI-LO and future games:

1. Never trap the player in a modal with only an infinite retry path.
2. A recoverable action error gets at most 3 explicit retry attempts.
3. After retry exhaustion, the player must get a clear escape: reload or return to the site.
4. Real-money sessions must not be silently closed by the frontend while money may be reserved in a table session.
5. Returning to the site is acceptable because active session/round recovery must be server-authoritative.
6. Reload is acceptable only when the runtime can resume active round/table state from backend.
7. Backend technical strings must not be shown directly to the player.

## 3. Immediate Fixes

P0 fixes implemented/required before UX redesign:

1. Real cashout platform close uses `status="won"` while game-specific HI-LO round remains `completed_cashout`.
2. `GameActionError` supports a custom dismiss label.
3. HI-LO action errors show retry count `Riprova 1/3`, `2/3`, `3/3`.
4. HI-LO action errors expose `Torna al sito` as secondary escape.
5. Runtime boot errors expose `Torna al sito` in addition to reload.
6. Integration test covers real cashout settlement and platform round closure.

## 4. Gameplay Redesign Principles

Hard constraints:

1. Only touch HI-LO gameplay area (`frontend/app/ui/hi-lo/*`) unless a shared primitive has a narrowly-scoped, backward-compatible improvement.
2. Do not touch shared shell/common interface for this redesign.
3. No scrollbars in the game surface.
4. No clipped cards, panels, or buttons at desktop/mobile breakpoints.
5. Desktop and mobile must expose the same functional concepts: predictions, skip, current card, history/recent cards, seed/fairness hint, bet/collect rail.
6. Card is the visual protagonist.
7. Prediction controls must remain fast to scan and tap/click.
8. Real and demo mode must have identical layout behavior.

Design target:

- Center stage is the current card.
- Four predictions are arranged around or below the card.
- Recent cards/history becomes a compact lane, not a hidden side-only panel.
- Skip is visible in mobile as a compact command, not hidden.
- Seed hash/fairness is available but visually secondary.

## 5. Desktop Layout Options

### Option A - Compass Card

Structure:

- Center: large current card.
- Left column: `BLACK` and `DOWN`.
- Right column: `RED` and `UP`.
- Bottom lane: recent cards/history chips.
- Top-right small controls: Skip and seed hash.

Pros:

- Card is central and dominant.
- Choices feel spatial and memorable.
- History gets a stable place without stealing the main focus.

Risks:

- Needs careful width math so prediction buttons do not crowd the card.

### Option B - Card Over Action Bar

Structure:

- Center/top: large current card.
- Bottom: 2x2 action grid under the card.
- Top/bottom thin lane: recent cards.
- Skip as right-aligned pill near history.

Pros:

- Strong mobile parity because the same shape stacks naturally.
- Very easy touch layout.

Risks:

- Desktop may feel less dynamic unless the card is visually rich.

### Option C - Arena Split

Structure:

- Center-left: card and card caption.
- Center-right: 2x2 predictions.
- Far-right: compact history/seed/skip rail, but rail collapses into bottom lane on tablet/mobile.

Pros:

- Closest to current implementation, lower risk.
- Good for quick iteration.

Risks:

- Product feedback says current side panel is too secondary; this may not move far enough.

Recommendation:

- Start with Option A as primary design target.
- Keep Option B as the mobile shape.
- Avoid Option C unless implementation time is the priority.

## 6. Mobile Layout Requirements

Mobile portrait target:

1. Top: HI-LO title small enough to leave room for the card.
2. Center: card, never clipped.
3. Under card: 2x2 prediction buttons.
4. Under predictions: compact row with Skip and seed/fairness short label.
5. History/recent cards: horizontal chip strip of the last 5 cards.
6. Shared control rail remains below or in existing mobile stack, but gameplay content must not rely on hidden desktop side panel.

Mobile acceptance checks:

- 390x844 portrait: no clipping, no internal scrollbar.
- 360x740 portrait: no clipping, controls remain tappable.
- 844x390 landscape: no clipping, compact mode still playable or short-viewport gate triggers intentionally.
- Active round: skip and history visible.
- Terminal round: replay CTA visible when replay payload is available.

## 7. Replay Discoverability

Current state:

- HI-LO replay exists in account/history/admin paths and in the rules modal integration path.
- Product did not see it during gameplay, so discoverability is insufficient.

Fix proposal:

1. On terminal cashout/loss, show a `Replay mano` CTA in the HI-LO game area.
2. The CTA opens the replay viewer for the just-finished round.
3. Keep account/history replay as the long-term audit path.
4. Keep admin replay as the backoffice path.
5. Do not block active gameplay with replay UI.

## 8. Backoffice Follow-Up

Backoffice is not part of the immediate gameplay redesign, but it needs a dedicated pass:

1. Audit `Games -> HI-LO` visually against the current strongest reference.
2. Verify theme fields one by one:
   - keep fields that HI-LO genuinely consumes at runtime;
   - remove fields that do not apply;
   - document any game-specific difference.
3. Fix spacing, alignment, label centering, and section hierarchy.
4. Verify title management and variant flow are conceptually unified with the other games.
5. Gate must include product walkthrough on `localhost:3000/admin`.

## 9. Prompt Pack For Design AI

Use this prompt for a design assistant only. The output must be mockups, not code.

```text
Design only the HI-LO gameplay area inside an existing CasinoKing game shell. Do not redesign the shared shell, page background, top bar, betting rail, wallet/balance footer, or common controls.

Context:
- Game: HI-LO card prediction.
- Player sees a current playing card and chooses one of four predictions: BLACK, RED, DOWN, UP.
- Skip is available during an active round.
- History/recent cards must show the last 5 cards/actions.
- Seed/fairness hash is useful but secondary.
- Desktop reference viewport: 1365x768.
- Mobile reference viewport: 390x844.

Hard constraints:
- No internal scrollbars.
- No clipped card, buttons, panels, or text.
- The card is the protagonist and should be centered.
- Prediction controls must be clear, tappable, and visually tied to the card.
- Mobile must include skip and recent-card history; do not hide them.
- The card should be synthetic and highly readable: rank, suit, and suit color visible at a glance.
- Keep the common game interface untouched.

Create 3 layout directions:
1. Compass Card: card centered, BLACK/DOWN left, RED/UP right, recent cards as bottom lane.
2. Card Over Action Bar: card centered, 2x2 prediction grid below, recent cards below or above.
3. Arena Split: card center-left, predictions center-right, history as a compact lane.

For each direction provide:
- Desktop mockup.
- Mobile portrait mockup.
- Active-round state.
- Terminal cashout state with Replay mano CTA.
- Notes on spacing, touch targets, and responsive behavior.
```

## 10. Prompt Pack For Codex Implementation

Use after product picks the preferred layout.

```text
Implement HI-LO gameplay area redesign only. Do not touch shared shell/common interface, Mines, BOXE, backend, or admin.

Files expected:
- frontend/app/ui/hi-lo/hi-lo-gameplay.tsx
- frontend/app/ui/hi-lo/hi-lo.css
- optional HI-LO-only small components under frontend/app/ui/hi-lo/

Requirements:
- Card is centered and visually dominant on desktop.
- Desktop uses the approved layout direction.
- Mobile portrait shows card, 2x2 predictions, Skip, seed/fairness short label, and recent-card history without clipping or scrollbars.
- History shows last 5 actions/cards.
- Terminal state exposes Replay mano CTA if replay can be loaded for the current round.
- Existing betting/control rail remains unchanged.
- Existing backend payloads remain unchanged unless replay CTA needs an already available endpoint call.

Gate:
- Build PASS.
- lint:i18n PASS.
- HI-LO demo smoke PASS.
- HI-LO real smoke PASS with table amount gate.
- Screenshots: desktop idle/active/terminal, mobile idle/active/terminal, landscape.
- Product owner walkthrough on localhost:3000.
```

## 11. Closure Gates

The redesign is not green unless all are true:

1. Container green: HI-LO layout renders in the existing shared shell.
2. Content green: card, actions, skip, history, seed, balances all present.
3. Visual green: no clipping, no scrollbars, card centered, buttons readable.
4. Functional green: start, predict, skip, cashout, replay CTA.
5. Persistence green: reload resumes active round/table state.
6. Runtime consume green: admin theme/assets still apply where expected.
7. Tests green: build, lint, smoke, targeted integration.
8. Product owner green: Michele validates on `localhost:3000`.

