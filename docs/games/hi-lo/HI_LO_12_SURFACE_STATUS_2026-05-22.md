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

HI-LO has H0/H1/H2/H3/H4/H5/H6 foundations in place: platform registration,
pure math/RNG/fairness, backend lifecycle/API, the first player runtime shell,
rich rules/how-to content, a full-depth admin editor, replay/account wiring and
active-round resume. Overall surface status is still **not final green**,
because browser smoke evidence and product-owner walkthrough remain open.

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
| 4 | Provider intro gate | Shared `GameProviderBootstrap` | Use platform intro unless product overrides. | Partial - shell implemented, PO/browser evidence pending | Browser smoke and no local duplicate. | H3 |
| 5 | How-to-play/info rules | Shared containers + HI-LO content | HI-LO rich rules and 3-step tutorial with card/prediction visuals. | Partial - H4 content/runtime implemented, PO walkthrough pending | Rules modal content, HTP screenshots, localized content. | H4 |
| 6 | Table balance gate | Shared `GameTableBalanceGate` | Demo, real cash and bonus separated; active round uses table session amount only. | Partial - shell consumes gate, real-money browser walkthrough pending | Ledger/table-session tests and real-money launch smoke. | H0/H2/H3 |
| 7 | Gameplay shell | Shared shell + HI-LO card stage | Large card, four predictions, skip, collect, history. | Partial - H3 implemented, PO visual gate pending | Desktop/mobile visual evidence, no scroll/clipping DOM matrix. | H3 |
| 8 | Mobile/rotation | Shared rotation gate + game responsive card layout | Card/action/history fit without scrollbars. | Partial - responsive CSS implemented, screenshot matrix pending | 390x844, 844x390, small-height screenshots and DOM metrics. | H3 |
| 9 | Embed mode | Platform runtime contract | HI-LO works with embed parameters and title_code. | Partial - shared launch context supports it, browser smoke pending | `?embed=1` smoke. | H3 |
| 10A | Admin engine page | Mines/BOXE canonical master/variant page | Full editable titles, filters, create variant, inline save/preview/archive, lobby toggles. | Implemented via shared platform, PO pending | Side-by-side Mines vs HI-LO engine page; e2e create/save/archive. | H5 |
| 10B | Admin title detail shell | Title Editor shell | Same command/status/tab frame and route mount. | Implemented, PO pending | Side-by-side detail shell screenshots. | H5 |
| 10C | Admin tab existence | Shared tabs + game adapters | Overview, copy, rules, config, assets, theme, sound, validation, replay if present. | Implemented | Tab inventory screenshot. | H5 |
| 10D | Admin field depth | Reference parity + HI-LO game-specific fields | Theme advanced skin, card assets, background, title presentation, sound, copy/rules, config. | Implemented, PO pending | Field-by-field audit and screenshots. | H5 |
| 10E | Admin draft/save/publish | Platform workflow | Save draft activates on every change; publish persists and runtime consumes. | Implemented, integration-tested | Save/publish e2e, runtime consume, draft dirty-state tests. | H5 |
| 10F | Adjacent admin pages | Platform adjacent pages | Asset library, copy manifest preview, finance/replay links if reference has them. | Implemented, PO pending | Route inventory and screenshots. | H5/H6 |
| 11 | Replay viewer | Shared replay shell + HI-LO renderer | Show card sequence, skips, decisions, multipliers, fairness seeds. | Implemented, browser/PO pending | Replay endpoint test, player replay smoke, admin replay management. | H6 |
| 12 | Disconnect/resume | Platform lifecycle/session recovery | Active round with collectible value must resume or follow approved auto-collect policy. | Implemented resume path, timeout policy pending | Disconnect/resume tests and product-approved timeout policy. | H6 |

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

## H3 Player Runtime Shell Update - 2026-05-23

H3 closes the first playable player-shell implementation, but it does not mark
any surface green without the product-owner `localhost:3000` walkthrough.

| Item | H3 Status |
| --- | --- |
| Route | `/hi-lo` renders `HiLoStandalone`. |
| Runtime storage | `hi_lo` namespace added to shared game storage keys. |
| Boot flow | Provider intro, how-to and table-balance gates consume shared runtime primitives. |
| Gameplay actions | Start, predict, skip and cashout call H2 backend endpoints through `use-hi-lo-runtime.ts`. |
| Visual shell | Card stage, four prediction buttons, skip, collect, balance and history render in `hi-lo-gameplay.tsx`. |
| No-scroll CSS | `hi-lo.css` compresses desktop, mobile portrait and short landscape without internal gameplay scrollbars. |
| Tests | Build, frontend boundary contracts and H1/H2 HI-LO backend tests pass. |

Surface impact:

- Surface 4 Provider intro: partial until browser evidence and PO walkthrough.
- Surface 5 HTP/info: partial until product-owner walkthrough on `localhost:3000`.
- Surface 6 Table balance: partial until real-money browser walkthrough.
- Surface 7 Gameplay shell: partial until visual/product-owner gate.
- Surface 8 Mobile/rotation: partial until screenshot/DOM matrix.
- Surface 9 Embed mode: partial until explicit embed smoke.

## H4 Content And Asset Update - 2026-05-23

H4 adds HI-LO-owned runtime content without changing Mines or BOXE.

| Item | H4 Status |
| --- | --- |
| Shared rules container | `HiLoRulesModal` consumes `GameInfoRulesModal`; shared shell remains game-agnostic. |
| Rule content | 7 HI-LO sections in it/en/de/es: bet/predict/collect, probability, payout, fairness, deck mechanics, skip, A/K edge ranks. |
| How-to content | 3 cards use HI-LO-specific bet/predict/collect copy and card visuals. |
| Runtime asset | HI-LO owns runtime card visuals directly in CSS plus optional title logo/table background assets from backoffice. |
| Tests | Build PASS; frontend boundary contract PASS; HI-LO backend/math PASS. |

Eight-layer snapshot for Surface 5:

| Surface | Container | Content | Visual | Functional | Persistence | Runtime Consume | Tests | Product Owner `:3000` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 5 HTP/info | green | green | evidence collected, PO pending | green | n/a for defaults | green | green | pending |

Surface 5 remains partial until Michele validates the modal/how-to on
`localhost:3000`.

## H5 Backoffice Full-Depth Update - 2026-05-23

H5 replaces the placeholder HI-LO backoffice with a full title editor:

| Item | H5 Status |
| --- | --- |
| Engine page | Shared `/admin/games/{engine}` category page handles master/variant grouping, editable titles, filters, inline save/preview/archive and lobby toggles. |
| Detail shell | `HiLoEngineEditor` consumes shared command bar, status banner, tab frame and validation display. |
| Tabs | Overview, Copy i18n, Rules HTML, Gameplay config, Assets, Sounds, Theme and Validation. |
| Persistence | `/admin/games/hi-lo/config`, `/draft`, `/publish` store draft/live presentation config in `title_configs`. |
| Runtime consume | `/games/hi-lo/config` exposes published `presentation_config`; player copy/rules/title logo/table background consume it. |
| Assets/theme | HI-LO manages lobby card, title logo, game-area background, audio assets and advanced skin. Card-back texture is intentionally not exposed because HI-LO has no closed-cell/card-back gameplay surface. |
| Tests | Build PASS; title-editor/runtime boundary contracts PASS; HI-LO admin config integration PASS; HI-LO backend/math PASS. |

Eight-layer snapshot for Surface 10:

| Surface | Container | Content | Visual | Functional | Persistence | Runtime Consume | Tests | Product Owner `:3000` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 10 Backoffice | green | green | implemented, PO pending | green | green | green | green | pending |

Surface 10 is no longer red from missing implementation. It remains not-final
green until product-owner walkthrough confirms the engine page and title detail
visually on `localhost:3000`.

## H6 Replay, Account And Resume Update - 2026-05-23

H6 closes the first implementation pass for Surface 11 and the no-silent-loss
resume branch of Surface 12.

| Item | H6 Status |
| --- | --- |
| Player replay | `HiLoReplayViewer` renders card sequence playback with Start/Play/Step/Skip controls, timeline, payout and fairness hashes. |
| Account history | `/account` loads HI-LO sessions from `/games/hi-lo/sessions` alongside Mines and BOXE. |
| Admin finance drilldown | Finance session detail opens HI-LO admin replay through `/games/hi-lo/admin/round/{round_id}/replay`. |
| Active-round resume | Runtime calls `/games/hi-lo/active-round` and restores the open round before letting the player enter a new table flow. |
| Statement/finance enrichment | Account and admin summaries label HI-LO and include correct predictions / active skips. |
| Tests | Build PASS; i18n lint PASS; title-editor/runtime contracts PASS; HI-LO service integration PASS; admin finance/account statement integration PASS. |

Eight-layer snapshot for Surface 11:

| Surface | Container | Content | Visual | Functional | Persistence | Runtime Consume | Tests | Product Owner `:3000` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 11 Replay | green | green | implemented, smoke/PO pending | green | green | green | green | pending |

Eight-layer snapshot for Surface 12:

| Surface | Container | Content | Visual | Functional | Persistence | Runtime Consume | Tests | Product Owner `:3000` |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 12 Disconnect/resume | n/a | n/a | n/a | resume branch green | green | green | green for active-round resume | pending |

Surface 12 remains closure-pending until timeout/force-close policy is verified
or explicitly deferred. The dangerous silent-reload path is covered by active
round resume.

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

## H7 Technical Closure Update - 2026-05-23

H7 documents the technical closure package after H0-H6. It does not override
the hard product-owner gate.

Current verdict: **technical green-major, final product green pending**.

| Surface group | Technical status | Remaining closure gate |
| --- | --- | --- |
| 1-6 Launch/content/table flow | Implemented and test-backed | Michele walkthrough on `localhost:3000`, especially real-money table amount guard. |
| 7-9 Gameplay/mobile/embed | Implemented | Browser visual pass for desktop/mobile/short landscape and embed smoke. |
| 10 Backoffice 10A-F | Implemented | Product owner admin walkthrough and runtime consume spot check. |
| 11 Replay | Implemented | Player/account/admin replay browser walkthrough. |
| 12 Disconnect/resume | Active-round resume implemented | Timeout/force-close policy remains a platform hardening decision or explicit deferral. |

H7 produced:

- `docs/games/hi-lo/CLOSURE_REPORT.md`
- `docs/NEXT_GAME_REPLICATION_BRIEF_FROM_HI_LO_2026-05-23.md`
- `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_HI_LO_2026-05-23.md`

Do not mark this tracker `12/12 final green` until the product owner column is
green or each residual is explicitly accepted.

### H7 Technical Pre-Walkthrough Fix - 2026-05-23

Codex browser pre-check found and fixed a wallet-source isolation bug: if a
demo HI-LO hand was active, entering a real route could resume that demo hand in
`REAL MODE` and bypass the table-balance gate. Active-round resume is now
filtered by requested wallet source (`demo`, `cash`, `bonus`).

Evidence:

- `tests/visual/artifacts/hilo_h7_technical_walkthrough_2026-05-23/REPORT.md`
- `tests/visual/artifacts/hilo_h7_technical_walkthrough_2026-05-23/04_real_table_gate_desktop.png`

Surface 2/6 technical status remains green-major and product-owner walkthrough
remains pending.
