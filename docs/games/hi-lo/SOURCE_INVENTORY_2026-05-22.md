Status: ACTIVE
Last meaningful update: 2026-05-22

# HI-LO Source Inventory

## Purpose

This document inventories the HI-LO source package before implementation. It
does not define the final SPEC. It classifies every known source as binding,
inspirational, ignored, or unresolved, so the next phase can turn the sources
into `SPEC.md` and `MATH_SPEC.md` without hidden assumptions.

## Scope

Read and inventoried:

- `assets/Games/hi-lo/analisi funzionale hi-lo.md`
- all PNG screenshots under `assets/Games/hi-lo/`
- HI-LO method documents in `docs/games/hi-lo/`
- `docs/NEW_GAME_BRIEF_TEMPLATE.md`
- `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_BOXE_2026-05-22.md`

Explicitly not read:

- `assets/Games/hi-lo/HI-LO video.mp4`

Reason: Michele already converted the video into the analysis document and
asked to avoid the video for this pass.

## Source Catalog

| # | Source | Type | Status | Binding Use | Notes |
| --- | --- | --- | --- | --- | --- |
| 1 | `assets/Games/hi-lo/analisi funzionale hi-lo.md` | Product analysis | Primary source | Binding for observed gameplay, provisional for math details marked as hypothesis | Contains game loop, UI, controls, math observations, edge cases and open questions. |
| 2 | `assets/Games/hi-lo/Stato Idle (Schermata Iniziale).png` | Screenshot | Visual reference | Binding for idle composition and main visual regions | 1274x789. Shows left rail, card stage, BET state, skip button. |
| 3 | `assets/Games/hi-lo/Stato Attivo (Opzioni visibili).png` | Screenshot | Visual reference | Binding for active-state action layout | 1274x789. Shows four action choices and displayed multipliers/probabilities. |
| 4 | `assets/Games/hi-lo/Azione Errata (Perdita).png` | Screenshot | Visual reference | Binding for loss transition directionally | 1274x789. Used for silent-loss behavior and card reveal timing. |
| 5 | `assets/Games/hi-lo/Vincita Parziale (Primo step).png` | Screenshot | Visual reference | Binding for first win state directionally | 1274x789. Shows active card transition and collect progression. |
| 6 | `assets/Games/hi-lo/Aggiornamento Quote In-Game.png` | Screenshot | Visual reference | Binding for quote refresh after successful pick | 1274x789. Used for cumulative multiplier/probability display. |
| 7 | `assets/Games/hi-lo/Animazione History Bar.png` | Screenshot | Visual reference | Binding for history bar composition | 1274x789. Shows five-card history row and result indicators. |
| 8 | `assets/Games/hi-lo/Edge Case-Carta Re (K).png` | Screenshot | Visual reference | Binding for K/high-edge UI behavior | 1274x789. Shows higher option becoming SAME at top rank. |
| 9 | `assets/Games/hi-lo/Cashout (Collect) ad alto valore.png` | Screenshot | Visual reference | Binding for collect state directionally | 1274x789. Used for collect CTA and high-value run state. |
| 10 | `assets/Games/hi-lo/HI-LO video.mp4` | Video | Ignored for now | None | Reopen only if Michele asks. |

## Source Coverage Matrix

| Topic | Covered By Source | Quality | Phase 2 Handling |
| --- | --- | --- | --- |
| Game identity | Analysis doc | Partial | Confirm display name, slug, first title code. |
| Core loop | Analysis doc + state screenshots | Strong | Convert into backend/frontend state machine. |
| Idle state | Analysis doc + idle screenshot | Strong | Define legal actions and persisted starting card. |
| Active state | Analysis doc + active screenshot | Strong | Define action options, quote display, skip rules. |
| Win step | Analysis doc + partial-win/quote screenshots | Medium | Specify transition, history update and multiplier accumulation. |
| Loss step | Analysis doc + loss screenshot | Medium | Specify terminal timing, history behavior and next starting card. |
| Cashout | Analysis doc + cashout screenshot | Medium | Specify settlement, balance update and next starting card. |
| Skip feature | Analysis doc | Medium | Confirm exact active-round counter semantics. |
| History bar | Analysis doc + history screenshot | Medium | Confirm max visible cards and FIFO behavior. |
| Edge rank behavior | Analysis doc + K screenshot | Strong for K, missing A screenshot | Specify A and K UI labels. |
| Deck model | Analysis doc | Strong directionally | MATH_SPEC must define deterministic RNG and replacement model. |
| RTP and multipliers | Analysis doc + screenshots | Incomplete | Requires MATH_SPEC derivation and product approval. |
| Max win | Analysis doc | Medium | Confirm 5000x and disabled/auto-collect behavior. |
| Visual fidelity | Screenshots | Directional | Decide composition reference vs pixel-perfect. |
| Card assets | Screenshots only | Weak | Need owned/generated/licensed card asset plan. |
| Rules/copy/locales | Analysis doc | Weak | Need full rules manifest in it/en/de/es or approved locale set. |
| Backoffice | BOXE replication brief + template | Platform-driven, not source-driven | Treat Mines/BOXE parity as mandatory, game-specific fields TBD. |
| Replay/fairness | Template + source | Partial | Need payload and verification model. |
| Real/bonus lifecycle | Template/platform | Not covered by HI-LO source | Must inherit platform gate and wallet protections. |

## Binding Product Facts Extracted

These facts are safe to carry into SPEC draft unless Michele changes direction.

| Area | Fact | Source |
| --- | --- | --- |
| Game type | Arcade casino high/low card game. | Analysis doc section 1. |
| Deck | Infinite virtual 52-card deck with replacement; previous cards do not affect future probabilities. | Analysis doc section 5. |
| Rank order | Ace is lowest, King is highest. | Analysis doc section 5. |
| Player choices | Black, Red, Lower-or-Same, Higher-or-Same, with edge-rank adaptation. | Analysis doc sections 2, 3, 6. |
| Primary CTA | BET in idle, COLLECT with amount during active round. | Analysis doc sections 2, 4. |
| Skip | Skip changes current card; active-round skip limit observed as 5 before a required guess. | Analysis doc sections 2, 4, 7. |
| History | Bottom history shows recent cards from the current round. | Analysis doc sections 2, 6, 8. |
| Loss UX | Loss is quiet; no large blocking "you lost" popup. | Analysis doc section 6. |
| Win UX | Positive feedback is mostly collect amount/multiplier progression, not a large celebration. | Analysis doc section 6. |
| Max win | Rules mention max win 5000x base bet. | Analysis doc sections 5, 8. |
| RTP | Rules mention 98% RTP. | Analysis doc section 5. |
| No bonus feature | No free spins, wheel, jackpot, or progressive bonus. | Analysis doc section 7. |

## Hypotheses And Non-Binding Observations

These must not be implemented as final rules without Phase 2 validation.

| Hypothesis | Why Not Final Yet | Phase 2 Work |
| --- | --- | --- |
| Multiplier formula is approximately `next_total_multiplier = current_multiplier * 0.98 / probability`. | Screenshots support this pattern, but the analysis text and screenshot values are not fully reconciled. | Derive exact MATH_SPEC and compare every screenshot anchor. |
| Displayed probability may include house edge adjustment. | Analysis text mentions 49.46% for a color, while inspected active screenshot shows 50.00%. | Decide whether UI probability is true probability or RTP-adjusted display. |
| Cashout returns to idle using the last card as next base card. | Mentioned in analysis, but exact backend persistence and resume behavior are not defined. | Define terminal state and next-round seed/card policy. |
| Loss reveals card briefly and then instantly returns to idle. | Directional from source, but exact timing/history persistence is not specified. | Define animation state and terminal response. |
| History shows last five cards only. | Source says last 5 and asks what happens beyond 5. | Confirm FIFO and replay payload. |

## Current Implementation Presence

No HI-LO production code exists yet in the current tree:

- `frontend/app/ui/hi-lo/`: not present
- `backend/app/modules/games/hi_lo/`: not present
- `backend/app/modules/games/hilo/`: not present
- `backend/app/modules/games/hi-lo/`: not present

This is useful: Phase 2 can define the contract before code creates inertia.

## Required Phase 2 Inputs From This Inventory

Phase 2 must create:

- `docs/games/hi-lo/SPEC.md`
- `docs/games/hi-lo/MATH_SPEC.md`
- visual state matrix for idle, active, win-step, loss, cashout, edge-rank,
  skip-limited and mobile states
- backend state machine and idempotency contract
- rules/how-to-play content outline
- admin config/copy/assets/theme/sound/replay capability matrix
- asset ownership plan for cards, logo, background and sounds

## Codex CTO Reviewer Notes

1. The source package is good enough to begin SPEC drafting, but not enough to
   implement math or real-money behavior.
2. The visual screenshots are reference material, not owned assets. HI-LO needs
   an asset decision before implementation.
3. The analysis doc contains at least one probability-display ambiguity. That
   must be resolved in `MATH_SPEC.md`.
4. Backoffice cannot be inferred from the HI-LO source package. It must be
   inherited from Mines/BOXE platform parity using the BOXE replication brief.

## Verifier Notes

Verifier pass checked the filesystem from scratch:

- all source files under `assets/Games/hi-lo/` were listed;
- PNG dimensions were collected from the filesystem;
- video was not opened;
- current tree search found no HI-LO production implementation.

No Phase 1 blocker found. Several Phase 2 Stop-and-Ask items are listed in
`docs/games/hi-lo/HI_LO_OPEN_QUESTIONS_2026-05-22.md`.
