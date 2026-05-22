Status: ACTIVE
Last meaningful update: 2026-05-23

# HI-LO Preliminary 12-Surface Status

## Purpose

This is the initial 12-surface tracker for HI-LO before implementation. It is
not a green report. Since no HI-LO code exists yet, the value is in defining the
expected inheritance, required evidence and likely work packages before any
surface gets a false green.

## Status Legend

| Status | Meaning |
| --- | --- |
| Not started | No HI-LO implementation yet. |
| Planned inherited | Expected to use existing platform/Mines/BOXE pattern. |
| Planned game-specific | Requires HI-LO-specific renderer/content/math. |
| Open | Product/CTO decision needed before implementation. |
| Blocker | Must be resolved before code. |

## Current Overall Verdict

HI-LO has H0/H1/H2 foundations in place: platform registration, pure
math/RNG/fairness and backend lifecycle/API. Overall surface status is still
**not green**, because player runtime, content, admin depth, replay UI and
product-owner walkthrough are not complete.

This is intentional. A surface cannot be green until it passes the eight-layer
gate:

1. container;
2. content;
3. visual;
4. functional;
5. persistence;
6. runtime consume;
7. tests;
8. product owner walkthrough on `localhost:3000`.

## 12-Surface Tracker

| # | Surface | Expected Inheritance | HI-LO Requirement | Current Status | Required Evidence | Likely Phase/WP |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Lobby card/catalog | Platform catalog + title/site publication | HI-LO visible only through CMS publication; owned icon/card asset. | Not started | CMS route screenshot, demo/real visibility toggle, asset consumed. | H0/H4/H5 |
| 2 | Launch Cashier modal | Platform launch cashier/table-balance gate | Real-money entry must force explicit stake selection and safe default/max guard. | Planned inherited + blocker | Demo/real/bonus launch smoke, no bypass to full balance. | H0/H2 |
| 3 | Admin preview launcher | Platform admin preview | Preview HI-LO title from admin detail. | Not started | `/admin` preview smoke and title_code propagation. | H5 |
| 4 | Provider intro gate | Shared `GameProviderBootstrap` | Use platform intro unless product overrides. | Planned inherited | Browser smoke and no local duplicate. | H3 |
| 5 | How-to-play/info rules | Shared containers + HI-LO content | HI-LO rich rules and 3-step tutorial with card/prediction visuals. | Planned inherited + game-specific content | Rules modal content, HTP screenshots, localized content. | H4 |
| 6 | Table balance gate | Shared `GameTableBalanceGate` | Demo, real cash and bonus separated; active round uses table session amount only. | Planned inherited + blocker | Ledger/table-session tests and real-money launch smoke. | H0/H2 |
| 7 | Gameplay shell | Shared shell + HI-LO card stage | Large card, four predictions, skip, collect, history. | Planned game-specific | Desktop/mobile visual evidence, no scroll/clipping DOM matrix. | H3 |
| 8 | Mobile/rotation | Shared rotation gate + game responsive card layout | Card/action/history fit without scrollbars. | Planned game-specific | 390x844, 844x390, small-height screenshots and DOM metrics. | H3 |
| 9 | Embed mode | Platform runtime contract | HI-LO works with embed parameters and title_code. | Not started | `?embed=1` smoke. | H3 |
| 10A | Admin engine page | Mines/BOXE canonical master/variant page | Full editable titles, filters, create variant, inline save/preview/archive, lobby toggles. | Planned inherited + blocker | Side-by-side Mines vs HI-LO engine page; e2e create/save/archive. | H5 |
| 10B | Admin title detail shell | Title Editor shell | Same command/status/tab frame and route mount. | Planned inherited | Side-by-side detail shell screenshots. | H5 |
| 10C | Admin tab existence | Shared tabs + game adapters | Overview, copy, rules, config, assets, theme, sound, validation, replay if present. | Planned inherited | Tab inventory screenshot. | H5 |
| 10D | Admin field depth | Reference parity + HI-LO game-specific fields | Theme advanced skin, card assets, background, title presentation, sound, copy/rules, config. | Planned inherited + game-specific | Field-by-field audit and screenshots. | H5 |
| 10E | Admin draft/save/publish | Platform workflow | Save draft activates on every change; publish persists and runtime consumes. | Planned inherited + blocker | Save/publish e2e, runtime consume, draft dirty-state tests. | H5 |
| 10F | Adjacent admin pages | Platform adjacent pages | Asset library, copy manifest preview, finance/replay links if reference has them. | Planned inherited | Route inventory and screenshots. | H5 |
| 11 | Replay viewer | Shared replay shell + HI-LO renderer | Show card sequence, skips, decisions, multipliers, fairness seeds. | Planned game-specific | Replay endpoint test, player replay smoke, admin replay management. | H6 |
| 12 | Disconnect/resume | Platform lifecycle/session recovery | Active round with collectible value must resume or follow approved auto-collect policy. | Open + blocker | Disconnect/resume tests and product-approved timeout policy. | H6 |

## Surface 10 Decomposition Rule

Surface 10 is red until every sub-surface 10A-F is green. It is not enough for
the title detail tabs to exist.

The minimum admin closure proof for HI-LO is:

- engine page side-by-side vs Mines;
- title detail page side-by-side vs Mines;
- tab inventory;
- field-depth audit;
- draft/save/publish persistence;
- runtime consume of copy/assets/theme/sound;
- adjacent route audit;
- product owner walkthrough on `/admin`.

## Preliminary Eight-Layer Gate Template

Use this template for every Wave closure.

| Surface | Container | Content | Visual | Functional | Persistence | Runtime Consume | Tests | Product Owner `:3000` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD | TBD |

Any `TBD`, `partial`, or missing product-owner result means the surface is not
green.

## Phase 3 Architecture Update - 2026-05-23

Phase 3 mapped HI-LO from product/math contract to implementation ownership.
The result is that HI-LO should start with a platform-enablement wave before
game-specific gameplay code.

Current platform prerequisites found during architecture mapping:

| Prerequisite | Reason | Planned Wave |
| --- | --- | --- |
| Add `hi_lo` to backend game-code registry | The current allowlist is still two-game oriented. | H0 |
| Add HI-LO launch/lobby adapter | Player lobby route and cashier configuration have Mines/BOXE branches. | H0 |
| Add HI-LO account/history adapter | Account page currently fetches Mines and BOXE explicitly. | H0/H6 |
| Register HI-LO title editor | Title Editor registry currently registers Mines and BOXE only. | H0/H5 |
| Define access-session recovery hook | Real-money active-round recovery is game-specific today. | H6 |
| Confirm owned card/background assets | Screenshots are references, not runtime assets. | H4 |

Authoritative Phase 3 docs:

- `docs/games/hi-lo/ARCHITECTURE_MAPPING.md`
- `docs/games/hi-lo/HI_LO_WAVE_PLAN.md`

## H0 Platform Enablement Update - 2026-05-23

H0 closes the platform registration prerequisite, not any player/admin surface.
The tracker deliberately keeps the surfaces non-green until the eight-layer gate
is proven.

| Item | H0 Status |
| --- | --- |
| Backend allowlist | `hi_lo` accepted. |
| Catalog seed | Hidden master `hi_lo` and variant `hilo001` added. |
| Lobby route mapping | `hi_lo` launches toward `/hi-lo`. |
| Player route | `/hi-lo` placeholder exists, non-playable. |
| Account label | `hi_lo` labels as `HI-LO`; replay waits for H6. |
| Admin detail | Placeholder editor exists; full editor waits for H5. |

No surface is green from H0 alone because there is no gameplay, content,
persistence, replay, full admin editor, runtime consume proof, or product owner
walkthrough yet.

## H1 Math/RNG/Fairness Update - 2026-05-23

H1 closes the pure math/RNG prerequisite, not a player surface.

| Item | H1 Status |
| --- | --- |
| Probability table | Implemented and unit-tested for all 13 ranks. |
| RTP formula | Implemented as 98% single-edge cumulative multiplier. |
| A/K edge behavior | Implemented and tested: no guaranteed 100% option. |
| Active skip math | Proved EV-neutral before rounding drift. |
| RNG | Deterministic 52-card draw with replacement and bias-safe mapping. |
| Fairness artifacts | Pure draw-sequence artifact and verifier implemented. |

No surface is green from H1 alone because there is still no HI-LO API,
persistence, player runtime consume, replay endpoint, admin consume or product
owner walkthrough.

## H2 Backend State/API Update - 2026-05-23

H2 closes the backend persistence/API prerequisite. It does not mark player or
admin surfaces green because there is no player runtime consume, visual evidence
or product owner walkthrough yet.

| Item | H2 Status |
| --- | --- |
| Round persistence | `hi_lo_rounds` stores server-authoritative current card, cumulative probability, multiplier, payout, seeds and terminal outcome. |
| Action persistence | `hi_lo_actions` stores start, active skip, prediction and cashout events with draw metadata. |
| Idempotency | `hi_lo_idempotency_keys` stores replayable API responses and rejects same-key/different-payload conflicts. |
| Demo lifecycle | Start debit, loss record and cashout credit are integrated with demo wallet. |
| Real-money guard | Cash/bonus start requires `table_session_id` and opens platform/table-session reserved exposure. |
| Replay payload | Player replay hides server seed; admin replay exposes server seed for verification. |
| API route | `/games/hi-lo/*` routes are registered. |
| Focused tests | Demo start/predict/cashout/replay, route start, real-money table guard, idempotency, loss and skip limit pass. |

Surface impact:

- Surface 2 Launch Cashier modal: backend table-session guard is ready, visual
  launch cashier remains H3/H7 evidence.
- Surface 6 Table balance gate: backend real-money start refuses cash/bonus
  without a table session; product-owner real-money walkthrough remains open.
- Surface 11 Replay viewer: backend replay payload exists; player/admin replay
  viewer remains H6.

## Required Product Owner Walkthrough Scenarios

These are preliminary. They will be refined in SPEC and Wave plans.

| Scenario | Route | Goal |
| --- | --- | --- |
| Demo launch | `/hi-lo?title_code=<first-title>&mode=demo` | Player sees idle card state and can play without wallet risk. |
| Real launch guard | Lobby click into real mode | Player cannot enter with full wallet accidentally; launch cashier gate appears. |
| Active gameplay | `/hi-lo` demo | BET, choose prediction, win/loss/cashout path visible. |
| Skip limit | `/hi-lo` demo | Idle skip and active skip limit behave as approved. |
| Edge rank | `/hi-lo` demo/replay harness | A/K display SAME behavior correctly. |
| Info/rules | `/hi-lo` demo | Modal has complete HI-LO rules, not placeholder content. |
| Mobile | 390x844 and 844x390 | No scrollbars, no clipping, no overlapping controls. |
| Admin engine page | `/admin/games/hi-lo` | Full master/variant management, not flat list. |
| Admin title detail | `/admin/games/hi-lo/titles/<title_code>` | All tabs and fields at reference depth. |
| Runtime consume | Admin + player route | Saved copy/assets/theme/sound appear in player runtime. |
| Replay | Account/admin replay route | Card sequence and fairness verification visible. |
| Disconnect/resume | Player route | Pending round behavior matches approved lifecycle. |

## Codex CTO Reviewer Notes

1. Surface 2 and 6 are financial/legal risk surfaces. They should be planned
   before any playable real mode.
2. Surface 10 must not be compressed. HI-LO starts with 10A-F from day one.
3. Surface 7/8 must include no-scroll/no-clipping measurement because the
   card/action layout can fail on small screens.
4. Surface 11 should be designed with replay payload during backend math work,
   not added after gameplay is visually done.

## Verifier Notes

Verifier checked that no HI-LO code exists and therefore no surface can be
marked green. This tracker is a planning baseline, not a completion report.
