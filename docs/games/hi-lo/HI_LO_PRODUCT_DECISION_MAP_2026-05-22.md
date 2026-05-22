Status: ACTIVE
Last meaningful update: 2026-05-22

# HI-LO Product Decision Map

## Purpose

This map converts the HI-LO source package into decisions, constraints and
open items for SPEC work. It is not the final SPEC and it does not authorize
implementation.

## Decision Status Legend

| Status | Meaning |
| --- | --- |
| Binding | Source is strong enough to carry into SPEC unless Michele changes it. |
| Platform default | Use CasinoKing/Mines/BOXE shared behavior unless a product exception is approved. |
| Proposed | Recommended direction; needs approval in SPEC phase. |
| Open | Needs product/CTO decision before implementation. |
| Stop-before-code | Cannot safely code this behavior until resolved. |

## 1. Identity And Routing

| Topic | Current Decision | Status | Notes |
| --- | --- | --- | --- |
| Display name | HI-LO | Proposed | Source uses HI-LO. Final capitalization can be product copy. |
| Public route | `/hi-lo` | Proposed | Human-readable route. Backend Python module should likely use `hi_lo`. |
| Engine code | `hi_lo` or `hilo` | Open | Decide once and keep DB/API/admin consistent. |
| First title code | `hilo001` or `hi_lo001` | Open | Needs platform naming convention decision. |
| Demo enabled | Yes | Platform default | Matches new-game template. |
| Real cash enabled | Yes, with table-balance launch modal | Platform default | Must inherit safe real-money launch guard. |
| Bonus wallet | Supported if platform default supports it | Platform default | Must be tested separately from real cash. |

## 2. Product Concept

| Topic | Decision | Status | Source |
| --- | --- | --- | --- |
| Game type | Single-player arcade card prediction game. | Binding | Analysis section 1. |
| Player objective | Predict next card by color or rank direction, then collect before losing. | Binding | Analysis sections 3-4. |
| No bonus rounds | No free spins, wheel, jackpot or progressive bonus in v1. | Binding | Analysis section 7. |
| Core tension | Risk rising cumulative multiplier vs cashout. | Binding | Analysis sections 4-5. |

## 3. Player Layout And Visual Direction

| Area | Decision | Status | Notes |
| --- | --- | --- | --- |
| Control rail/sidebar | Inherit CasinoKing shared runtime rail, not a local copy. | Platform default | The screenshot provider sidebar is directional; CasinoKing shell remains the platform reference unless Michele asks for pixel-perfect external layout. |
| Stage/canvas | HI-LO-specific card stage inside shared game shell. | Proposed | Card, choices, skip and history are game-specific. |
| Main card | Large centered current card. | Binding | All screenshots. |
| Skip button | Small button near card top-right. | Binding directionally | Exact icon/position can be adapted to CasinoKing shell. |
| Four action choices | Around the active card: black, red, lower/same, higher/same. | Binding | Active screenshot. |
| History bar | Bottom centered row of recent cards. | Binding | History screenshot. |
| No scrollbars/clipping | All HI-LO layouts must fit their game area responsively. | Platform hard rule | Learned from BOXE. |
| Visual fidelity | Composition reference unless product asks pixel-perfect. | Proposed | External screenshots cannot be treated as final owned assets. |

## 4. Game States And Legal Actions

| State | Visible UI | Legal Actions | Terminal? | Status |
| --- | --- | --- | --- | --- |
| Idle | Current card, BET CTA, skip available, no active win. | Change bet, skip current card, open tools, start round. | No | Binding, details TBD. |
| Active decision | Current card, four choices, COLLECT CTA, skip counter. | Choose one prediction, collect, skip if skip limit allows. | No | Binding. |
| Win step | New card becomes current, history updates, cumulative multiplier increases. | Continue, collect, maybe skip. | No | Binding directionally. |
| Loss transition | Losing card revealed briefly, no blocking loss modal. | None during transition. | Yes | Binding directionally; exact response state TBD. |
| Cashout | Collect amount credited, round ends, active buttons disappear. | Return to idle. | Yes | Binding directionally. |
| Max-win reached | Options that would exceed cap disabled; possible auto-collect if all disabled. | TBD. | Maybe | Stop-before-code. |
| Resume after disconnect | Pending active round restored or auto-collected by policy. | TBD. | TBD | Stop-before-code. |

## 5. Card And Prediction Rules

| Topic | Decision | Status | Notes |
| --- | --- | --- | --- |
| Deck model | Infinite 52-card deck with replacement. | Binding | No card counting. |
| Rank order | A lowest, K highest. | Binding | Source explicit. |
| Color choice | Black means spades/clubs; Red means hearts/diamonds. | Binding directionally | Icons show suit pairs. |
| Lower/Same | Winning if next rank is lower or equal to current rank. | Binding | Source explicit. |
| Higher/Same | Winning if next rank is higher or equal to current rank. | Binding | Source explicit. |
| Edge rank A | Lower-or-same likely becomes SAME or equivalent. | Open | Source gives K only; A must be specified. |
| Edge rank K | Higher-or-same becomes SAME. | Binding directionally | K screenshot. |

## 6. Math, RTP And Payout

| Topic | Decision | Status | Notes |
| --- | --- | --- | --- |
| RTP target | 98% | Binding directionally | Source says declared rules. Confirm demo vs production. |
| Max win | 5000x base bet | Binding directionally | Source says declared rules. |
| Multiplier display | Buttons show total cumulative multiplier if the prediction wins. | Binding | Source section 5. |
| Probability display | Buttons show win probability for the prediction. | Binding directionally | Exact value semantics open. |
| Formula candidate | `next_total_multiplier = current_total_multiplier * RTP / p(win)` | Proposed | Fits color x1.96 at 50% and K same after cumulative progression, but must be proven. |
| House edge application | Apply in multiplier, not necessarily in displayed probability. | Proposed | Avoid misleading probability display unless product/legal approves otherwise. |
| Max-win behavior | Disable options exceeding cap; auto-collect if no legal options. | Open | Source asks for UI behavior. |
| Bet range | EUR/chip 0.20 to 200.00 in source game. | Open | CasinoKing chip economy must approve actual min/max. |

## 7. Skip Feature

| Topic | Decision | Status | Notes |
| --- | --- | --- | --- |
| Idle skip | Unlimited starting-card refresh before bet. | Binding directionally | Analysis says player can change starting card freely. |
| Active skip | Up to 5 skips per round, then a prediction is required. | Binding directionally | Exact counter reset behavior open. |
| Skip economics | Skip appears free in source. | Open | Needs backend fairness and anti-abuse decision. |
| Skip RNG | Server-authoritative draw from same deck model. | Platform default | Must be deterministic/replayable. |

## 8. History, Replay And Fairness

| Topic | Decision | Status | Notes |
| --- | --- | --- | --- |
| History row | Shows recent current-round cards. | Binding directionally | Source says last 5. |
| More than 5 cards | FIFO display likely. | Open | Source explicitly asks. |
| Replay payload | Include starting card, action sequence, skipped cards, drawn cards, multipliers, terminal result. | Proposed | Needed for deterministic replay. |
| Fairness visibility | Show server seed hash, client seed and outcome verification like platform pattern. | Platform default | From BOXE/Mines replay parity. |

## 9. Content, Rules And How-To-Play

| Content Area | Decision | Status | Notes |
| --- | --- | --- | --- |
| Info/rules modal | Shared `GameInfoRulesModal` pattern with HI-LO-specific sections. | Platform default | Must include content, not only container. |
| How-to-play | 3-step visual tutorial: bet, predict, collect/avoid loss. | Proposed | Needs visual plan. |
| Rules sections | Bet/collect, prediction rules, multiplier/payout, RTP/fairness, skip, max win, history/replay. | Proposed | Phase 2 should draft full copy manifest. |
| Locales | it/en/de/es if following BOXE/Mines current pattern. | Proposed | Needs product confirmation. |

## 10. Backoffice And Admin

Surface 10 must start decomposed as 10A-F. HI-LO cannot repeat BOXE's
"sub-tab green but engine page red" failure.

| Layer | Decision | Status | Notes |
| --- | --- | --- | --- |
| 10A Admin engine page | Inherit Mines/BOXE full master/variant page. | Platform default | Master/variant grouping, editable titles, filters, create variant, inline save/preview/archive, lobby toggles. |
| 10B Title detail shell | Inherit Title Editor shell. | Platform default | Route and mount must match current canonical admin pattern. |
| 10C Tabs | Overview, copy, rules, config, assets, theme, sound, validation, replay if platform exposes. | Proposed | Exact tab names can follow platform. |
| 10D Field depth | Every reference field has HI-LO equivalent or documented game-specific exception. | Platform default | Theme advanced skin, title presentation, card assets, background, sounds. |
| 10E Workflow | Draft save, publish, locale persistence, runtime consume. | Platform default | Must be end-to-end tested. |
| 10F Adjacent pages | Asset library, manifest preview, finance/replay links as applicable. | Platform default | Must be route-audited. |

## 11. Admin Config Candidates

These are not final. They are candidate fields for Phase 2/3 architecture
mapping.

| Field | Why It Exists | Status |
| --- | --- | --- |
| RTP target | Rules/math display and operator diagnostics. | Proposed, likely locked. |
| Max win multiplier | Source says 5000x. | Proposed, maybe configurable with guard. |
| Bet min/max/default | Platform economy/admin. | Open. |
| Active skip limit | Source says 5. | Proposed. |
| Card skin asset set | HI-LO needs card faces/back/suit icons. | Proposed. |
| Stage background | Screenshots show branded blue pattern. | Proposed. |
| Sound pack | BET, prediction, win, loss, collect, skip. | Proposed. |
| Title presentation | Text/logo/image parity with Mines theme. | Platform default. |

## 12. Asset Decisions Needed

| Asset | Source Coverage | Decision Needed |
| --- | --- | --- |
| Card face deck | Only visible inside reference screenshots. | Create/own/import licensed full deck asset pack. |
| Card back | Not fully specified. | Define default and theme overrides. |
| Logo/title graphic | Reference screenshot only. | Use text title or create owned logo. |
| Background pattern | Reference screenshot only. | Create owned background or theme token equivalent. |
| Suit/action icons | Visible in screenshots. | Use owned icon set, likely local SVG/CSS or asset registry. |
| Sound/music | Mentioned in controls, no files. | Use platform default or provide HI-LO pack. |

## 13. Stop-Before-Code Items

Do not implement HI-LO before Phase 2 resolves or explicitly defers:

1. engine code/title code naming;
2. exact RTP/multiplier/probability display contract;
3. real-money bet range and table-balance launch policy;
4. max-win disabled/auto-collect behavior;
5. disconnect/resume/auto-cashout behavior;
6. asset ownership plan for card deck and background;
7. visual fidelity level;
8. admin config field list;
9. replay/fairness payload;
10. active skip counter semantics.

## Codex CTO Reviewer Verdict

Phase 1 is sufficient to proceed to Phase 2 SPEC/MATH_SPEC drafting, with a
clear caveat: math, real-money lifecycle and assets are not implementation-ready.

Recommended next step: draft SPEC and MATH_SPEC in one Phase 2 package, but
mark any unresolved economics/legal behavior as Stop-and-Ask before code.

## Verifier Pass

Verifier checked this map against:

- source inventory;
- HI-LO analysis document;
- visual screenshots inspected directly;
- new-game template;
- BOXE backoffice replication brief.

No code implementation exists yet, so all implementation-facing entries are
contracts to be created, not audits of current HI-LO code.
