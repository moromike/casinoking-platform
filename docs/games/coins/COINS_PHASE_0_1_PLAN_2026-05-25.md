Status: ACTIVE
Last meaningful update: 2026-05-25

# COINS - Phase 0+1 Plan

## 0. Purpose

This document is Parte A for COINS Fase 0+1. It validates the CTO prompt in
`docs/games/coins/PROMPT_CODEX_COINS_FASE_0_1_SPEC_2026-05-25.md` and defines
the six final documents that must be produced before any COINS production code
starts.

Scope is documentation only:

- no backend code;
- no frontend code;
- no Mines/BOXE/HI-LO changes;
- no database migrations;
- no new product decisions beyond the closed decisions in
  `docs/games/coins/COINS_OPEN_QUESTIONS_2026-05-25.md`.

## 1. CTO Prompt Verdict

Verdict: **approved with small discipline corrections**.

The six-document plan is the right shape for COINS. It is intentionally stricter
than the early BOXE flow and matches the HI-LO lesson: do not start code until
product, math, 12 surfaces, architecture ownership, replay/finance and
backoffice expectations are written down.

Corrections to apply in Parte B:

| # | Correction | Reason |
| --- | --- | --- |
| 1 | Round 2 decisions in `COINS_OPEN_QUESTIONS` override earlier preferred defaults. | The early Q table says IT+EN in some places; final product decision is always IT+EN+DE+ES. |
| 2 | Treat the existing Rule 18 registry and embed bridge as platform capabilities to consume, not prereqs to reopen. | Both are already implemented and audited in `PLATFORM_REGISTRY_AUDIT_2026-05-25.md` and `EMBED_MODE_PARITY_AUDIT_2026-05-25.md`. |
| 3 | Stop-and-Ask list must distinguish true blockers from recommended defaults. | Route, title code and cap UI behavior can be proposed as defaults instead of blocking Fase 0+1. |
| 4 | Source inventory must record legal/lookalike risk as a product/legal check, not as engineering research. | COINS is inspired by Hacksaw Dare2Win; implementation must not copy brand/trade dress blindly. |
| 5 | The 12-surface status must start non-green and include the eight-layer closure rows. | Container-only green was the recurring BOXE/HI-LO failure mode. |

No counter-proposal to the six-document structure is needed.

## 2. Documents To Produce In Parte B

Produce the documents in this exact order. Each document must start with:

```text
Status: ACTIVE
Last meaningful update: 2026-05-25
```

### 2.1 `docs/games/coins/SOURCE_INVENTORY_2026-05-25.md`

Purpose: inventory every COINS input source and classify reliability.

Include:

- source files in `assets/Games/coins/`;
- `games/coins/COINS - analisi gemini funzionale_v01.md`;
- screenshot list and what each screenshot proves;
- video existence, explicitly noting that the transformed analysis is the main
  working source and the video is not re-analysed in this WP;
- comparison between Gemini analysis coverage and Playbook required coverage;
- missing/weak areas: state machine, idempotency, real/bonus lifecycle,
  reporting, replay, admin config, legal/lookalike review;
- file/source confidence labels: primary product decision, derived analysis,
  visual reference, future asset candidate.

Do not include:

- final product decisions in prose form; those belong in the decision map;
- implementation file ownership; that belongs in architecture mapping;
- payout proof; that belongs in `MATH_SPEC.md`;
- legal conclusion. Only record that legal/lookalike review is a non-engineering
  check.

### 2.2 `docs/games/coins/COINS_PRODUCT_DECISION_MAP_2026-05-25.md`

Purpose: convert `COINS_OPEN_QUESTIONS_2026-05-25.md` into a structured product
contract.

Include:

- Q1-Q25 final decision table;
- Round 2 decisions L1-L7;
- classification for every decision:
  `game-specific`, `platform-default`, `operator-configurable`, `wave-1`,
  `wave-2`, `future-annotation`;
- decisions that must become Playbook/template defaults for future games;
- values that must be visible in Title Editor:
  bet range, coin count range, max-win cap, autoplay limits, copy/rules,
  assets, sounds and theme tokens;
- all four locales: `it`, `en`, `de`, `es`;
- M-section future annotations: crypto/multicurrency, replay retention
  operations, provably fair client seed, animation polish, advanced theme.

Do not include:

- endpoint design;
- DB schema;
- math derivation beyond a pointer to `MATH_SPEC.md`;
- open questions that were already closed unless they are explicitly marked as
  history.

### 2.3 `docs/games/coins/COINS_12_SURFACE_STATUS_2026-05-25.md`

Purpose: initial non-green 12-surface tracker for COINS.

Include:

- the 12 Playbook surfaces;
- expected inheritance from Mines/BOXE/HI-LO/GameRuntimeShell;
- game-specific COINS requirement for each surface;
- current status before code, usually `not-started` or `precondition-green`;
- required evidence for final green;
- eight-layer gate per surface:
  container, content, visual, functional, persistence, runtime consume, tests,
  Product Owner on `localhost:3000`;
- Surface 10 decomposition into 10A-F from the HI-LO backoffice brief;
- Rule 19 lobby/CMS local testability as a hard gate;
- Rule 14 no-scroll/no-clipping matrix for coin grid N=1..10 Wave 1 and N=12
  deferred/optional.

Do not include:

- implementation order detail; use architecture mapping for that;
- final green claims; no COINS surface can be green before implementation and
  product owner walkthrough.

### 2.4 `docs/games/coins/SPEC.md`

Purpose: canonical Phase 0 product and runtime contract.

Include these sections:

1. Scope, sources and decision status.
2. Game identity: `coins`, route `/coins`, proposed first title `coins001`.
3. Core rules: choose N coins, all heads win, any X loses.
4. State machine: `IDLE -> BET_PLACED -> SPINNING -> RESOLVED`.
5. Idempotency: client UUID, TTL 5 minutes, duplicate response replay.
6. Real/demo/bonus lifecycle, close/timeout and auto-settlement mapping.
7. Replay/history contract and info modal Replay tab.
8. Visual layout: shell inheritance, game-specific coin board, autoplay.
9. Operator settings and Title Editor fields.
10. Asset/sound/theme contract.
11. Failure UX and i18n copy keys.
12. Test gates and Stop-Before-Code items.

Do not include:

- payout proof tables beyond short references; use `MATH_SPEC.md`;
- detailed file ownership; use `ARCHITECTURE_MAPPING.md`;
- full copy text for all locales; define the contract, not the final manifest.

### 2.5 `docs/games/coins/MATH_SPEC.md`

Purpose: math, RNG and fairness contract.

Include:

- formula `P_win(N) = 1 / 2^N`;
- formula `M(N) = 0.98 * 2^N`;
- Wave 1 payout matrix N=1..10;
- deferred N=11..12 matrix entries as Wave 2/operator-enabled candidates;
- RTP proof: `P_win(N) * M(N) = 0.98`;
- max-win cap interaction with payout;
- bet range effects;
- rounding/precision rules to be implemented in backend;
- server-side RNG model;
- coin matrix generation;
- deterministic replay data;
- simulator/test harness expectations;
- failure cases: malformed N, out-of-range bet, cap reached, idempotent replay.

Do not include:

- backend route names;
- UI copy;
- admin editor layout;
- legal/certification claims beyond the engineering fairness contract.

### 2.6 `docs/games/coins/ARCHITECTURE_MAPPING.md`

Purpose: Phase 1 implementation contract and WP split for Fases 2-7.

Include:

- common vs game-specific vs platform-extension matrix;
- exact protected areas: Mines/BOXE/HI-LO untouched unless a platform WP is
  explicitly approved;
- backend file ownership candidates;
- frontend player file ownership candidates;
- backoffice/title editor ownership candidates;
- registry/adapter points COINS must consume:
  game reporting registry, embed bridge, game runtime shell, title editor
  registry, game runtime descriptor;
- WP list for Fases 2-7;
- dependencies and merge order;
- contract tests and smoke tests;
- visual baseline and Product Owner gate plan;
- admin manual update plan;
- capability matrix skeleton per WP.

Do not include:

- full product prose already in `SPEC.md`;
- full math proof already in `MATH_SPEC.md`;
- final implementation code snippets;
- speculative platform rewrites not needed for COINS Wave 1.

## 3. Recommended Defaults, Not Blocking Questions

These are not Stop-and-Ask blockers unless CTO/Michele disagrees. Use them in
Parte B.

| Topic | Recommended default | Why |
| --- | --- | --- |
| Public route | `/coins` | Matches game code and prompt. |
| Engine code | `coins` | Product decision closed. |
| First title code | `coins001` | Matches BOXE `boxe001` and HI-LO `hilo001` style. |
| First display name | `COINS 001` | Human-readable admin/lobby name. |
| Wave 1 coin range | `1..10` | Product decision; N=11/12 deferred. |
| Locales | `it`, `en`, `de`, `es` | Round 2 final decision. |
| Settlement taxonomy subset | Use existing platform metadata where it fits: `loss`, `refund_no_progress`, `admin_void` or `quarantined` for malfunctioning/admin cases. Natural instant win needs explicit semantic mapping in `SPEC.md`: either existing platform win settlement kind if acceptable, or Stop-and-Ask for a new `instant_win`/`resolved_win` taxonomy value. | COINS has no mid-round collect, so blindly calling a natural win `manual_cashout` would be misleading. |
| Max-win cap UI | Pre-bet display warning + backend hard cap. If theoretical payout exceeds cap, UI must explain capped payout before bet. | Avoid silent money surprises. |
| Replay entry | Info modal Replay tab + account/admin history. No gameplay replay CTA. | Playbook Rule 20. |

## 4. True Stop-And-Ask List

Parte B should stop only if one of these becomes true:

| Stop | Trigger |
| --- | --- |
| Product decision conflict | `COINS_OPEN_QUESTIONS` conflicts with a newer Michele/CTO instruction. |
| Route/title naming rejected | CTO/product rejects `/coins` or `coins001`. |
| Max-win cap behavior legally sensitive | CTO wants silent cap, capped odds, disabled N/bet combos, or another policy. |
| Settlement taxonomy mismatch | Platform finance metadata cannot represent COINS natural win/loss/refund/malfunctioning without a new value. |
| Replay payload insufficient | Stored `{coin_matrix, N, bet, multiplier, payout, mode, timestamp, idempotency_key_hash}` cannot reconstruct player/admin replay. |
| Title Editor cannot host required COINS fields | Existing registry/editor shell cannot represent N range, cap, autoplay, coin asset mode and theme tokens. |
| Visual sources conflict | Screenshots, Gemini analysis and product decisions describe incompatible board/control layout. |
| Legal/lookalike issue is raised | Product/legal says Hacksaw reference is too close and visual direction must change. |

## 5. Missing Or Weak Source Areas

| Area | Current state | Parte B handling |
| --- | --- | --- |
| Final visual mockup | We have screenshots/video-derived analysis, not a CasinoKing-final design. | Record as visual baseline input; Phase 3B must produce mockup/component mapping before UI code. |
| Final production assets | Source folder contains video/screens/rules images, not final runtime coin PNG/sounds. | SPEC defines upload/default-text fallback; Phase 4B can launch without required coin images. |
| Legal/lookalike review | Not present. | Source inventory records as product/legal check. Not an engineering blocker for docs. |
| Replay retention operations | Policy MVP says 30 days online/no deletion, cold storage later. | SPEC cites MVP; ARCH maps future retention/cold-storage WP outside Wave 1 if needed. |
| Advanced animation polish | Product wants base now, possible polish mini-project later. | MATH/SPEC do not block; ARCH maps Phase 3C base and future polish. |
| Provably fair client seed | Future probable, not Wave 1. | MATH_SPEC includes server-side deterministic seed now; future client-seed section only. |

## 6. Preliminary Capability Matrix For Fases 2-7

Legend: `NEW`, `UPDATE`, `CONSUME`, `n/a`.

| WP | Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| WP-COINS-2A-MATH-RNG | Coin probability, multiplier, RTP, RNG verifier | n/a | NEW | n/a | n/a | n/a | n/a | NEW | UPDATE |
| WP-COINS-2B-SCHEMA-STATE | Round/session schema, state machine, repository | NEW | NEW | n/a | n/a | n/a | n/a | NEW | UPDATE |
| WP-COINS-2C-API | Start/bet/resolve/replay/idempotency endpoints | UPDATE | NEW | NEW | n/a | n/a | n/a | NEW | UPDATE |
| WP-COINS-2D-ADAPTER-FINANCE-REPLAY | Reporting descriptor, account/admin finance/replay, settlement metadata | UPDATE | UPDATE | UPDATE | CONSUME | CONSUME | n/a | NEW | UPDATE |
| WP-COINS-3A-STANDALONE-BOOT | Route, launch context, shell gates, embed bridge consume | n/a | n/a | CONSUME | n/a | NEW | UPDATE | NEW | UPDATE |
| WP-COINS-3B-GAMEPLAY | Coin board, manual/autoplay controls, payout display, no-scroll matrix | n/a | n/a | CONSUME | n/a | NEW | NEW | NEW | UPDATE |
| WP-COINS-3C-ANIMATIONS | Base spin/fade animation and reduced motion | n/a | n/a | n/a | n/a | UPDATE | NEW | NEW | UPDATE |
| WP-COINS-4A-CONFIG-COPY-RULES | Title Editor config, i18n manifest, rich rules HTML | UPDATE | UPDATE | UPDATE | NEW | CONSUME | UPDATE | NEW | UPDATE |
| WP-COINS-4B-ASSETS-SOUNDS-THEME | Asset kinds, coin mode image/text, sounds, theme tokens, lobby card | UPDATE | UPDATE | UPDATE | NEW | CONSUME | UPDATE | NEW | UPDATE |
| WP-COINS-5-SITE-LOBBY | Engine/title seeding, CMS publish path, lobby launch | UPDATE | UPDATE | UPDATE | UPDATE | UPDATE | UPDATE | NEW | UPDATE |
| WP-COINS-6-DOCS-ATLAS | Atlas, Mermaid map, admin manual, implementation log | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATE |
| WP-COINS-7-E2E-VALIDATION | End-to-end demo/real/bonus, replay, finance, Product Owner walkthrough | n/a | CONSUME | CONSUME | CONSUME | CONSUME | CONSUME | NEW | UPDATE |

## 7. Proposed Merge / Approval Discipline

Recommended workflow:

1. Approve this plan.
2. Produce the six docs one by one in the order above.
3. After `SPEC.md` and `MATH_SPEC.md`, do a CTO mini-review before writing the
   final `ARCHITECTURE_MAPPING.md`.
4. Commit all six final docs plus README/open-loop updates as one docs-only
   checkpoint.
5. Only then open implementation Fase 2A.

If time is tight, `SOURCE_INVENTORY`, `PRODUCT_DECISION_MAP` and
`12_SURFACE_STATUS` can be produced in parallel by separate agents, but
`SPEC`, `MATH_SPEC` and `ARCHITECTURE_MAPPING` should be reviewed serially
because they become implementation contracts.

## 8. Parte A Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| COINS Phase 0+1 planning | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NEW | green | This doc defines the six-document output and stop gates. |
| Product decision digestion | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATE | green | Final Round 2 decisions override earlier preferred defaults. |
| Future implementation WP split | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NEW | green | Preliminary capability matrix prepared for Fases 2-7. |

## 9. Decision Brief For Michele / CTO

No code should start yet.

Recommended approval:

- approve the six-document structure;
- accept `/coins` and `coins001` as defaults unless product wants another
  title code;
- accept pre-bet visible cap warning plus backend hard cap as the max-win UX;
- accept that final COINS surfaces remain non-green until Product Owner
  walkthrough on `localhost:3000`.

After approval, the next action is Parte B: produce the six COINS contract
documents.
