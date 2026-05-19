Status: ACTIVE
Last meaningful update: 2026-05-19

# BOXE - Retrospective Analysis - 2026-05-19

## Scope And Sources Actually Reviewed Now

This retrospective was written after the merge of
`fix/boxe-shell-uniformity` into `main` at `410d42d`.

Sources actually reviewed for this analysis:

- `assets/Games/boxe/boxe1 splash.png`
- `assets/Games/boxe/boxe2 stato idle base .png`
- `assets/Games/boxe/boxe4.png`
- `assets/Games/boxe/boxe5.png`
- `assets/Games/boxe/boxe6.png`
- `assets/Games/boxe/boxe7.png`
- `assets/Games/boxe/BOXE - DOCUMENTO DI DESIGN FUNZIONALE.docx`
- `frontend/app/ui/boxe/boxe-gameplay.tsx`
- `frontend/app/ui/boxe/boxe.css`
- `frontend/app/ui/boxe/boxe-animations.css`
- `tests/visual/baselines/boxe_3c/*`
- `tests/visual/baselines/mines_classic/desktop_1440x900.png`
- `docs/games/boxe/SPEC.md`
- `docs/games/boxe/BOXE_BRIEF.md`
- `docs/games/boxe/SHELL_UNIFORMITY_AUDIT_2026-05-19.md`

Important correction to the current narrative: the repository evidence says
Phase 0 did reference the `.docx` and screenshot paths in `SPEC.md`. The real
failure is sharper: those references did not become binding visual gates during
implementation. The mockups were treated as background/source material, not as
acceptance artifacts that had to be opened, compared side-by-side, and signed
off before frontend phases closed.

## 1. Differenziazione Shell Mines-Replica Vs BOXE Gioco Proprio

| Area BOXE | Product expectation after 2026-05-19 | Should replicate Mines visually? | Should be BOXE-specific? | Current post-shell-extraction status | Honest verdict |
| --- | --- | --- | --- | --- | --- |
| Lobby card | Common lobby grid/card behavior; game artwork/name can differ. | Yes for card structure, modal trigger, cashier behavior. | Yes for image/title/description. | Shared `PlayerGameCard` and `LaunchCashierModal`; BOXE artwork is specific. | Aderente. This area is basically correct. |
| Launch Cashier | Protected equality zone. Same modal structure and launch choices. | Yes. | Minimal: game title/art/copy only if platform allows. | Same modal component; some copy source and route params differ by engine. | Mostly aderente. Copy unification remains a small platform concern, not a blocker. |
| Table Balance Gate | Protected equality zone. Same visual/form sequencing as Mines. | Yes. | Submit callback may remain game-specific until BOXE table sessions are real. | After Step 5, BOXE consumes shared visual and real-mode sequencing matches Mines. Backend lifecycle still placeholder/no `table_session_id`. | Visually aderente, behaviorally parziale. It is acceptable for shell extraction, not complete product parity. |
| Provider Intro | Protected equality zone. Same moromike lab intro. | Yes. | No meaningful BOXE-specific behavior in v1. | Shared `GameProviderBootstrap` consumed by both. | Aderente. |
| How-To-Play Gate | Same shell layout; content/visual cards game-specific. | Yes for overlay, grid, CTA, spacing. | Yes for steps, copy, mini visuals. | Shared `GameHowToPlayGate`; BOXE passes own cards/visuals. | Aderente for shell. BOXE content is serviceable, not mockup-faithful. |
| Boot sequencing | Same protected flow until gameplay. | Yes. | No. | Real cash/bonus: Table -> Provider -> How-To -> Gameplay. Demo: Provider -> How-To -> Gameplay. | Aderente after Step 5. This was wrong before Step 5. |
| Left gameplay panel | Product owner now states: left side gameplay should match Mines. | Yes for controls/balance/action ergonomics. | Only labels/settings appropriate to BOXE. | BOXE uses a separate left settings block and right bet panel, not Mines left rail. | Divergent. This is the biggest visible mismatch after shell extraction. |
| Gameplay layout | Central game surface must implement BOXE pyramid. | No, not visually identical to Mines grid. | Yes: pyramid, row progression, payout ladder, safe/mine reveal. | Pyramid exists, rows/difficulty exist, payout ladder exists, state machine works. | Functional but visually parziale. It is a clean prototype, not the mockup product. |
| Payout display | Must follow BOXE doc/mockup: top-center horizontal ladder, current pill, next mine risk. | Not Mines-identical; should be BOXE-specific. | Yes. | Has horizontal steps and current/next classes; mine risk text is weak and not icon/count faithful. | Parziale. Correct idea, incomplete execution. |
| Board symbols | Should use BOXE assets/visual language from mockups. | No. | Yes. | Current cells are CSS squares with simple diamond/mine shapes; source assets are not used in gameplay board. | Divergent from mockups. |
| Safe/mine animations | BOXE-specific. | No. | Yes: flip diamond, red mine/explosion, current row reveal only. | Implemented as CSS feedback; reduced motion covered. | Parziale. Technically present, visually undercooked vs mockups. |
| Loss reveal | BOXE-specific: reveal/opacify current row only. | No. | Yes. | Current row opaque reveal implemented; future rows remain hidden. | Aderente functionally, parziale visually. |
| Admin config | Should reuse Title Editor shell, with BOXE-specific plugin. | Yes for admin shell/workflow. | Yes for rows/difficulty/copy/assets. | Title Editor was generalized; BOXE editor exists. | Aderente. This is one of the stronger parts. |
| Backend/API/math/replay | Not visual Mines replica; game-specific BOXE implementation through platform adapter. | No. | Yes. | Math, RNG, state, API, settlement/replay are covered by tests. | Aderente/solid. |

Bottom line: after the shell extraction, the protected pre-game zone is finally
aligned. The actual BOXE gameplay screen is not yet the visual product shown in
`boxe1-7`. It is a working second-game implementation with a generic dark
platform skin.

## 2. Analisi Errori Commessi

### Concrete Technical Mistakes

1. **The mockups were not converted into visual acceptance gates.**
   Phase 0 listed the assets, but later frontend WPs did not require opening
   `boxe1-7`, writing a frame-by-frame mapping, or comparing implemented
   screenshots against the references. That is the root product failure.

2. **The first BOXE gameplay UI optimized for architecture and testability, not
   visual fidelity.**
   `BoxeGameplay` is internally clean: state, backend calls, idempotency,
   retry, board, payout, settings and bet panel are separated. But the visual
   result is a generic dark dashboard-like game screen. It does not reproduce
   the mockup composition: left-bottom player panel, central pyramid scale,
   bottom system icons, compact Hacksaw-style shell, or board symbol treatment.

3. **The shell extraction was done too late.**
   BOXE 3A should not have been allowed to pass with local Provider Intro,
   local How-To and local Table Balance. The later extraction fixed it, but
   only after the product had already been told BOXE was closed. That was an
   avoidable loop.

4. **`GameBootShell` was mistaken for shared visual implementation.**
   The code had shared orchestration, not shared surfaces. I treated "uses
   GameBootShell" as stronger evidence than it was. The Step 5 Stop-and-Ask
   proved the correct distinction: wrappers can be shared while the actual
   rendered UX is forked.

5. **BOXE table lifecycle asymmetry should have stopped 3A earlier.**
   BOXE real mode had no real table-session lifecycle equivalent to Mines.
   The placeholder callback was a valid short-term decision after CTO approval,
   but this asymmetry should have been explicit at the first table-gate design
   point, not discovered during shell uniformity cleanup.

6. **The visual baseline protected the wrong thing.**
   BOXE visual regression snapshots now prove the implemented UI does not
   change accidentally. They do not prove it matches `boxe1-7`. A baseline of
   the wrong visual target can freeze a wrong product.

7. **The phrase "Pattern Mines" was overloaded.**
   Sometimes it meant backend safety, platform adapter reuse, launch mechanics,
   or shell visual identity. Sometimes it meant "do not copy Mines gameplay".
   Because those meanings were not separated hard enough, visual decisions
   drifted.

### Decisions I Would Make Differently

- I would make Phase 3A a shell-only WP with hard side-by-side Playwright
  evidence against Mines before any BOXE gameplay was implemented.
- I would make Phase 3B start with a visual contract document:
  mockup frame -> DOM region -> implemented component -> baseline screenshot.
- I would put the left gameplay control rail decision in writing before coding:
  either "reuse Mines rail ergonomics" or "BOXE custom panel"; not infer it.
- I would not accept BOXE 3C polish until board symbols, payout ladder, and
  action panel were compared against `boxe5-7`.
- I would keep the first visual baseline in a `reference_match` suite, separate
  from normal regression baselines.

### Wrong Assumptions Made During Coding

- That "functional BOXE pyramid + platform dark theme" was enough for v1 visual
  acceptability.
- That the `.docx` and screenshots were inspirational sources, not strict
  visual acceptance criteria.
- That shell equality ended at boot gates and did not constrain gameplay left
  side once the BOXE board mounted.
- That a placeholder table balance callback was harmless if visually hidden
  behind an otherwise good flow. It was not harmless; it changed sequencing.
- That reaching 100+ green tests meant product risk was low. It only meant
  technical behavior risk was low.

### CTO Brief Ambiguities Or Weak Spots

This is not blame shifting; these are process facts.

- The briefs pushed very hard on architecture, game-agnosticity, adapters,
  idempotency, math, settlement, replay and docs. They did not force an explicit
  visual review of `boxe1-7` before Phase 3B/3C implementation.
- "Use Mines as reference" was clear for platform patterns but not sharp enough
  about the exact gameplay boundary: shell identical until gameplay, then left
  side still Mines-like and right side game-specific.
- The phase plan allowed BOXE to be called closed before the shell uniformity
  audit. That was premature.
- The review gates accepted visual regression tests as proof of visual quality.
  They should have asked: "Regression against what target?"
- The title "BOXE closure" was granted while a product-visible protected-zone
  mismatch still existed. The later Step 5 fixed part of it, but the closure
  timing was wrong.

### Stop-And-Ask That Should Have Happened Earlier

- **Before 3A:** "Do I create local BOXE pre-game gates, or must Provider
  Intro/How-To/Table Balance be extracted shared first?"
- **Before 3B:** "Are `boxe1-7` pixel/composition references or only broad
  inspiration?"
- **Before 3B:** "Should BOXE keep the Mines left control rail, with only the
  central/right gameplay area changing?"
- **Before 3C:** "Are CSS shapes acceptable for diamond/mine, or must gameplay
  use prepared symbol assets?"
- **Before 4B/5/6 closure:** "Does launch into BOXE need real table sessions
  before the product can be called E2E complete?"
- **Before closure report:** "Do we have side-by-side evidence for the protected
  equality zone?"

### Code Review Gaps

- Reviews were strong on contracts, DB, idempotency, backend settlement and
  test breadth.
- Reviews were not rigorous enough on visual source fidelity.
- Reviews did not challenge the local BOXE gate forks early enough.
- Reviews did not require a "mockup delta table" before accepting gameplay
  polish.
- Reviews did not flag that the current BOXE board cells do not use the
  prepared diamond/mine assets and do not resemble the source references.

## 3. Come Avrei Affrontato BOXE Se Gestito Diversamente

Given these upfront constraints:

- explicit mockups from day 1;
- "shell identical to Mines until gameplay, gameplay left side same as Mines,
  right side/board game-specific";
- pre-3A consume audit;
- pre-4A backend lifecycle symmetry audit;
- Parte A/Parte B validation before execution;

I would restructure BOXE like this.

### Revised Phase Plan

| Phase | What I would change | Compress/expand | Stop-and-Ask gates |
| --- | --- | --- | --- |
| Phase 0 SPEC | Add visual acceptance matrix from `boxe1-7`; define which mockup regions are binding. | Expand by 1 prompt. | Is the mockup a strict composition target? Which parts may inherit Mines? |
| Phase 1 Architecture Mapping | Add consume-vs-fork audit for `game-runtime`, Title Editor, Launch Cashier, table sessions and gameplay rail. | Expand slightly. | If a Mines component is the visual reference, do we extract shared or clone? |
| Phase 2 Backend | Keep mostly as done. Backend was the healthiest part. | No major change. | Before 2D: does BOXE need table-session parity now or later? |
| Phase 3A Shell | Extract shared pre-game surfaces before BOXE standalone passes. No BOXE local gates. | Expand; this should have been a platform WP upfront. | Approve shared visual shell API before implementation. |
| Phase 3B Gameplay Functional | Build with Mines left rail/controls as structural reference; central pyramid only is BOXE-specific. | Similar effort, less later rework. | Approve left rail reuse and board composition before coding. |
| Phase 3C Visual Fidelity | Compare `boxe2`, `boxe4`, `boxe5`, `boxe6`, `boxe7` to Playwright screenshots. Use assets for symbols or explicitly defer. | Expand significantly. | Is "acceptable" CSS-symbol UI enough, or must it match mockup art? |
| Phase 4 Admin | Mostly as done, but add table lifecycle warning if admin exposes real mode before table parity. | Same. | Does admin config change visual/gameplay acceptance? |
| Phase 5/6 Lobby/E2E | Do not call closed unless protected shell side-by-side is green. | Same tests, stronger gate. | Product signoff before closure. |
| Phase 7 Validation | Include product visual review, not only automated tests. | Expand by 1 prompt. | Are visual baselines protecting target fidelity or only current state? |

### Expected Stop-And-Ask List Upfront

1. Is BOXE gameplay left panel a Mines clone, a shared component, or a custom
   implementation?
2. Are `boxe1-7` required visual targets for v1, or just inspiration for a
   future polish WP?
3. Should table sessions be fully integrated before BOXE real mode is called
   product-complete?
4. Must board cells use uploaded diamond/mine assets in v1?
5. Should payout ladder show mine icon/count exactly like the `.docx`?
6. Is the bottom system menu required for BOXE v1, or does platform shell cover
   it differently?
7. Is mobile allowed to be a responsive reinterpretation, or must it preserve
   the desktop mockup hierarchy?

### Effort Estimate: Revised Vs Actual

Actual effort was high because we paid for architecture discovery late:

- backend platform adapter hardcoding;
- frontend runtime namespace hardcoding;
- title editor hardcoding;
- shell surface extraction;
- sequencing fix.

If the revised process had been used from day 1:

| Area | Actual pattern | Revised estimate |
| --- | --- | --- |
| Backend/math/API/settlement | Mostly efficient, with real platform discoveries. | Similar effort. |
| Shell extraction | Done late after BOXE fork existed. | 1-2 prompts earlier, less rework. |
| Gameplay functional | Built once, but with wrong visual target. | Similar code effort, better layout target. |
| Visual polish | Current polish is not mockup-faithful. | +2-4 prompts upfront, but avoids a larger post-hoc redesign. |
| Admin/lobby | Mostly efficient. | Similar effort. |

Honest total: the project would not necessarily be much shorter in raw prompts.
It would be less emotionally expensive and less misleading. I estimate a
proper mockup-gated BOXE would add 2-4 focused prompts early, but save 3-6
cleanup/argument prompts later. Net effort roughly equal or slightly lower;
product confidence much higher.

## 4. Consigli Operativi Per Arrivare A BOXE Accettabile/Eccellente

### Current Status

BOXE backend is solid: math, RNG/fairness, state machine, API, idempotency,
platform settlement, real/bonus/demo, replay/history and admin config are in
good shape.

Frontend shell is now acceptable for the protected pre-game zone after
`WP-PLATFORM-PREGAME-SHELL-EXTRACTION`.

Gameplay frontend is the weak product area. It is functional and testable, but
not visually faithful to the mockups.

### Level 1: BOXE Accettabile

Goal: playable, coherent with Mines shell, no embarrassing product mismatch.

Required WPs:

1. **WP-BOXE-GAMEPLAY-LEFT-RAIL-ALIGNMENT**
   - Align gameplay controls with the Mines left-side ergonomics where product
     now expects parity.
   - Keep BOXE-specific settings: rows, difficulty, bet/collect.
   - Remove the current split left-settings/right-bet layout unless explicitly
     re-approved.

2. **WP-BOXE-MOCKUP-DELTA-AUDIT**
   - Write a table for `boxe2`, `boxe4`, `boxe5`, `boxe6`, `boxe7`:
     reference region -> current implementation -> keep/fix/defer.
   - This should be read-only first. No code until product accepts the target.

3. **WP-BOXE-TABLE-SESSION-INTEGRATION**
   - Replace placeholder Table Balance callback with real BOXE table-session
     lifecycle or explicitly mark real mode as not final.
   - This is not just polish; it is product/accounting lifecycle parity.

4. **WP-BOXE-GAMEPLAY-SYMBOL-ASSET-WIRING**
   - Use prepared diamond/mine assets or publish a deliberate visual fallback.
   - The current CSS diamond/mine is too generic.

5. **WP-BOXE-PAYOUT-LADDER-POLISH-L1**
   - Ensure ladder communicates current multiplier, next multiplier and next
     mine risk clearly.
   - Minimal icon/count support if full mockup fidelity is deferred.

Effort estimate: **3-5 prompts** if product accepts "acceptable" as structured
Mines-like UI with improved BOXE board. Add 1-2 prompts if table-session
integration exposes backend/API gaps.

Priority order:

1. Mockup delta audit.
2. Left rail alignment decision and implementation.
3. Table-session integration.
4. Symbol asset wiring.
5. Payout ladder L1 polish.
6. Refresh BOXE visual baselines after product approval.

### Level 2: BOXE Eccellente

Goal: visually close to `boxe1-7`, polished, production-ready, and not just
"working".

Required WPs:

1. **WP-BOXE-VISUAL-TARGET-SPEC-V2**
   - Convert mockups into a binding visual spec.
   - Include desktop composition, mobile reinterpretation, palette, spacing,
     typography, board scale, payout strip, bottom/system controls and state
     overlays.

2. **WP-BOXE-GAMEPLAY-COMPOSITION-REDESIGN**
   - Rebuild layout around mockup composition:
     compact top payout, central pyramid, left/bottom player controls, system
     icon strip, correct safe zones.
   - Keep existing backend hooks/state code where possible.

3. **WP-BOXE-BOARD-ART-AND-ANIMATION-PASS**
   - Asset-backed boxes/diamonds/mines.
   - More faithful flip/reveal, red explosion, opaque current-row reveal.
   - Explicit reduced-motion equivalents.

4. **WP-BOXE-PAYOUT-LADDER-POLISH-L2**
   - Sliding pill, mine icon/count, active/current/next states matching the
     `.docx` and frames.

5. **WP-BOXE-HOW-TO-SPLASH-CONTENT-PASS**
   - The shell layout stays shared, but BOXE content should echo `boxe1` more
     closely: Bet/Pick/Collect with visual miniatures.

6. **WP-BOXE-AUDIO-POLISH**
   - Real click, safe reveal, mine, cashout/top-row sounds.
   - BGM only if product decides it is required.

7. **WP-BOXE-PRODUCTION-VISUAL-QA**
   - Side-by-side reference review.
   - Playwright screenshots for reference states.
   - Product owner signoff before baseline freeze.

Effort estimate: **7-12 prompts** for a serious excellent pass. Less would be
cosmetic patching. The current code is not throwaway, but the layout/CSS layer
needs a real redesign against the source frames.

Priority order:

1. Visual Target Spec V2.
2. Composition redesign.
3. Board art and animation.
4. Payout ladder L2.
5. How-to splash content pass.
6. Audio polish.
7. Production visual QA and baseline freeze.

### Final Brutal Verdict

BOXE is technically much healthier than it looks. The backend and platform
integration are real work and should not be dismissed.

But the product concern is valid. The current frontend gameplay is not the game
shown in the BOXE mockups. It is a functional BOXE engine wearing a generic
CasinoKing/Mines-derived interface. Calling that "closed" was premature.

The shell extraction WP fixed an important architectural and pre-game UX
problem. It did not make BOXE visually excellent. The next product decision
should be explicit: either accept BOXE as a functional v1 with limited visual
ambition, or open a real BOXE gameplay visual redesign WP and stop pretending
the existing baselines prove mockup fidelity.
