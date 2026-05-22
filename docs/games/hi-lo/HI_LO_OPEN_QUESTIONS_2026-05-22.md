Status: ACTIVE
Last meaningful update: 2026-05-22

# HI-LO Open Questions And Stop-And-Ask Register

## Purpose

This document lists the questions that must be resolved, defaulted, or carried
as explicit risks before HI-LO implementation. It separates Phase 2 SPEC
questions from true Stop-before-code blockers.

## Status Legend

| Status | Meaning |
| --- | --- |
| SPEC-needed | Must be answered in SPEC/MATH_SPEC before implementation. |
| Product-needed | Michele decision required. |
| CTO-needed | Architecture/risk decision required. |
| Can-default | Use platform default unless Michele overrides. |
| Stop-before-code | Implementation must not start until resolved. |

## Questions

| # | Area | Question | Current Recommendation | Status | Blocks |
| --- | --- | --- | --- | --- | --- |
| 1 | Identity | What is the canonical engine code: `hi_lo`, `hilo`, or `hi-lo`? | Use route `/hi-lo`, backend module `hi_lo`, title prefix `hilo`. | Product-needed | SPEC |
| 2 | Title | What is the first title code? | `hilo001` for clean DB/code identifiers. | Product-needed | SPEC |
| 3 | Visual | Is the Hacksaw/Dare2Win screenshot pixel-perfect or composition reference? | Composition reference inside CasinoKing shared shell. | Product-needed | Player UI |
| 4 | Assets | Are screenshots only references, or can any visual asset be reused? | Treat screenshots as references only; create owned assets. | Stop-before-code | Player UI |
| 5 | Math | Is displayed probability true hit probability or RTP-adjusted probability? | Display true probability; apply RTP in multiplier. | Stop-before-code | MATH_SPEC |
| 6 | Math | Is multiplier formula `current_multiplier * RTP / p(win)`? | Use as candidate and validate against all screenshot anchors. | Stop-before-code | MATH_SPEC |
| 7 | RTP | Is 98% RTP target for demo only, production, or both? | Demo 98%; production requires explicit product/legal decision. | Stop-before-code | Backend math |
| 8 | Max win | Confirm max win cap: 5000x base bet? | Use 5000x if product confirms. | Product-needed | MATH_SPEC |
| 9 | Max win UX | If an option would exceed max win, is it disabled, hidden, or converted to auto-collect? | Disable illegal options; auto-collect if no legal option remains. | Product-needed | Player UI/backend |
| 10 | Bet range | Should CasinoKing use source range 0.20-200.00, chip defaults, or title-configurable values? | Use platform/table-session defaults and expose admin config if needed. | Product-needed | Real-money launch |
| 11 | Skip | Is active skip limit exactly 5 per round? | Yes, based on source. | SPEC-needed | Backend/frontend |
| 12 | Skip | After 5 skips, when does skip become available again? | Reset after one prediction attempt, if the round continues. | Product-needed | Backend/frontend |
| 13 | Skip | Does idle skip have any cost or limit? | No cost, unlimited before BET. | Product-needed | Backend fairness |
| 14 | Edge A | When current card is Ace, does Lower-or-Same become SAME? | Yes by symmetry with K. | SPEC-needed | UI/math |
| 15 | Edge K | When current card is King, Higher-or-Same becomes SAME. | Use screenshot behavior. | SPEC-needed | UI/math |
| 16 | Color | Do Black/Red choices count only color, not suit? | Yes: black = spades/clubs, red = hearts/diamonds. | SPEC-needed | MATH_SPEC |
| 17 | Loss | After loss, which card becomes the next idle base card? | Use the losing revealed card as next base only if source confirms; otherwise draw fresh idle card. | Product-needed | State machine |
| 18 | Cashout | After cashout, does the last active card remain as next idle base card? | Source says yes; confirm. | SPEC-needed | State machine |
| 19 | History | When history exceeds 5 visible cards, is it FIFO? | Yes. | SPEC-needed | Player UI/replay |
| 20 | History | Does a losing card remain in history before reset? | Show briefly and record in replay; visible idle history TBD. | Product-needed | Player UI/replay |
| 21 | Disconnect | What happens to an active round with collectible value on disconnect? | Use Session Recovery policy; likely resume pending round, not silent loss. | CTO-needed | Lifecycle |
| 22 | Auto-cashout | Is there timeout auto-collect for pending collectible rounds? | Use platform Session Recovery if already approved; otherwise Stop. | CTO-needed | Lifecycle |
| 23 | Replay | What must player replay show? | Starting card, choices, skips, drawn cards, multipliers, seed verification. | SPEC-needed | Replay |
| 24 | Fairness | What seed model should HI-LO use? | Platform server seed hash + client seed deterministic model. | CTO-needed | MATH_SPEC |
| 25 | Admin config | Which fields are operator-configurable vs locked? | Start with bet limits, skip limit, max win, theme/assets/sound/copy. Math/RTP likely locked. | Product-needed | Backoffice |
| 26 | Theme | Does HI-LO need advanced skin/card skin/background controls at v1? | Yes if Mines has equivalent theme depth; use game-specific asset kinds. | Platform default | Backoffice |
| 27 | Sounds | Use platform sounds or HI-LO-specific pack? | Platform sounds for v1 unless product provides pack. | Can-default | Backoffice/player |
| 28 | Locales | Which locales launch? | Match current platform pattern: it/en/de/es. | Product-needed | Content/admin |
| 29 | Keyboard | Are all source keybinds required? | Implement only platform-approved shortcuts; document unsupported source shortcuts. | Product-needed | Player UI |
| 30 | Mobile | What is the mobile/portrait arrangement of card, choices and rail? | Derive from shared shell; no scrollbars/clipping. | SPEC-needed | Visual |
| 31 | How-to-play | What are the 3 tutorial cards? | Bet, predict, collect/avoid loss. | Product-needed | Content |
| 32 | Rules modal | Which rules sections are required? | At least: bet/collect, predictions, payout, RTP/fairness, skip, max win, history/replay. | SPEC-needed | Content |
| 33 | Launch cashier | Confirm real-money launch modal cannot bypass stake selection and uses safe default/max. | Inherit platform launch cashier hard guard. | Stop-before-code | Real money |
| 34 | Admin engine page | Will HI-LO admin inherit full master/variant page on day one? | Yes. No flat "Other engines" list. | Stop-before-code | Backoffice |
| 35 | Draft save | Must save-draft activation be tested after every admin change type? | Yes, because production previously missed changes. | Stop-before-code | Backoffice |

## Recommended Defaults If Michele Says "Use Platform"

| Area | Default |
| --- | --- |
| Shell | CasinoKing shared runtime shell inherited from Mines/BOXE. |
| Info/rules modal | Shared modal container, HI-LO-specific rich content. |
| Launch cashier | Platform table-balance gate with safe default and max guard. |
| Admin engine page | Full Mines/BOXE canonical master/variant page. |
| Backoffice tabs | Full platform title editor depth with HI-LO-specific config/assets. |
| Replay/fairness | Platform fairness visibility with HI-LO card replay renderer. |
| Locales | it/en/de/es. |

## Phase 2 Stop-And-Ask Threshold

Codex can draft Phase 2 documents with recommended answers, but must stop
before implementation if any of these remain unresolved:

- math/RTP formula;
- real-money launch and bet range;
- asset ownership;
- max-win behavior;
- disconnect/resume lifecycle;
- admin engine page parity;
- visual fidelity level.

## Codex CTO Reviewer Notes

The current questions are normal for a pre-SPEC phase. They are not a reason to
stop Phase 1. They are a reason not to code yet.

The only immediate external review recommended before Phase 2 is if Michele
wants pixel-perfect external visual fidelity or a non-platform real-money flow.
Those would change cost/risk materially.

## Verifier Notes

Verifier rechecked the question list against:

- analysis doc section 8 open questions;
- new-game brief template sections 1-12;
- BOXE backoffice replication brief;
- current CasinoKing safety lessons on no-scroll and product-owner walkthrough.

No missing Phase 1 blocker found.
