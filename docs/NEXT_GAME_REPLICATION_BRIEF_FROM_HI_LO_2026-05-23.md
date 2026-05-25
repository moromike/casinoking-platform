Status: ACTIVE
Last meaningful update: 2026-05-24

# Next Game Replication Brief - From HI-LO Lessons (2026-05-23)

This is the handoff for the next proprietary CasinoKing game after HI-LO. It is
written for a future CTO/Codex/AI agent that must start fast without repeating
BOXE's false-green cycles or HI-LO's remaining hard-coded bridge debt.

HI-LO is game 3. The next game is the point where repeated explicit branches
must become platform registry/adapters instead of another copy-paste branch.

## 1. Required Reading Order

Read in this order before coding:

1. `docs/README.md`
2. `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`
3. `docs/NEW_GAME_BRIEF_TEMPLATE.md`
4. this document
5. `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_HI_LO_2026-05-23.md`
6. `docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md`
7. `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_BOXE_2026-05-22.md`
8. `docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md`
9. the new game's source package and product analysis

Do not start from memory. The point of HI-LO was to make game 4 less dependent
on oral history.

## 2. First Deliverables Before Code

Create these docs for the new game before implementation:

| Deliverable | Purpose |
| --- | --- |
| Source inventory | What product assets, references, videos, screenshots and analysis exist. |
| Product decision map | What is already approved, what is an assumption, what needs Michele. |
| Stop-and-Ask register | Short list of decisions that block implementation. |
| SPEC | Game contract: board/card model, actions, states, payouts, lifecycle. |
| MATH_SPEC | RTP, probability model, RNG, fairness, examples and simulator plan. |
| Architecture mapping | Exact files/owners/platform dependencies before code. |
| Finance/replay reporting map | How the game appears in ledger, player account, admin finance, replay and retention policy. |
| 12-surface tracker | Every surface starts non-green and moves only by evidence. |
| Wave plan | H0-H7 or equivalent, with effort estimates and gates. |

The product owner does not need to read all docs. Codex must restate any real
questions in chat.

## 3. Recommended Wave Sequence

| Wave | Goal | Gate |
| --- | --- | --- |
| H0 Platform enablement | Register game code, seed hidden master/title, route lobby/admin, add placeholders. | No player surface marked green. |
| H1 Math/RNG/fairness | Pure deterministic math and verifier. | Unit tests plus documented RTP examples. |
| H2 Backend state/API | Rounds, actions, idempotency, replay payload, demo/real table lifecycle. | Integration tests, finance/ledger guard and reporting descriptor draft. |
| H3 Player runtime | Shared gates, runtime shell, first playable UI, no-scroll responsive matrix. | Browser smoke plus eight-layer table. |
| H4 Content/assets | Rich rules/how-to/copy/assets in all locales. | Container + content + visual proof. |
| H5 Backoffice | Full Surface 10A-F from the start. | Admin save -> publish -> runtime consume. |
| H6 Replay/recovery/reporting | Player/account/admin replay, finance detail, retention class and active-round resume. | Replay viewer, account/admin finance drilldown, no hardcoded game branch, resume test. |
| H7 Closure/distillation | Closure report, next-game brief, Playbook/template/map updates. | Product owner `localhost:3000` walkthrough or explicit residual list. |

If a game is simpler than HI-LO, waves can be combined only after the affected
surfaces have their gates listed explicitly.

## 4. Hard Gates That Must Not Be Bypassed

| Gate | Why |
| --- | --- |
| Product owner walkthrough on `localhost:3000` | BOXE and HI-LO both proved internal green is not enough. |
| Lobby/CMS testability before walkthrough | A game that works only by direct URL is not ready for Michele; the local CMS must publish it and the lobby must launch it. |
| Eight-layer green table | A surface is green only when container, content, visual, functional, persistence, runtime consume, tests and product owner are green. |
| 12-surface status at every closure | The checklist is useful only if actively applied, not archived. |
| No-scroll/no-clipping matrix | Gameplay must adapt to space; scrollbars in the game board are forbidden unless explicitly approved for a non-game admin table. |
| Admin Surface 10A-F | Backoffice is not one surface. Engine page, detail shell, tabs, field depth, workflow and adjacent pages all matter. |
| Real-money table balance gate | The player must never enter a real-money game with the full wallet by accident. |
| Real-money auto-settlement on close/timeout | Closing the game or timing out must run a game-specific settlement policy: refund before meaningful progress, auto-cashout collectible exposure. |
| Provider intro before gameplay | The provider intro/video must own the screen before runtime gameplay mounts; no one-frame gameplay flash during boot checks. |
| Runtime consume proof | Admin upload/save is not green until the player runtime consumes it. |
| Finance/replay reporting proof | A real and demo round must appear in player account and admin finance with readable game-specific details and working replay. |

## 5. HI-LO Lessons To Carry Forward

| Lesson | Next-game action |
| --- | --- |
| Platform enablement first saved time. | Open H0 before game-specific UI/backend. |
| Rich content must be built with the container. | Do not mark rules/info green with placeholder sections. |
| Backoffice 10A-F upfront avoided BOXE rescue waves. | Use the HI-LO H5 shape as the default. |
| Active-round resume must be designed early. | Define resume/timeout/force-close policy in H2, not at the end. |
| Active-round resume must be wallet-source isolated. | A demo active round must never resume inside real/bonus mode and bypass the table-balance gate. |
| Close/timeout settlement is a platform invariant with game-specific mapping. | Every new game must wire the X button to access-session close, define its own progress/cashout semantics, and add tests for refund-before-progress plus auto-cashout-after-progress, including the timeout sweeper path. |
| Provider intro owns the screen before gameplay. | Do not mount runtime gameplay while `showProviderIntroGate` is true. Active-round resume and other boot checks must run behind the provider intro, never by briefly exposing the game surface. |
| Account/admin replay is now hard-coded across three games. | Game 4 must extract registry/adapters instead of adding a fourth branch. Finance text, replay endpoint and viewer are part of the game contract. |
| Product owner walkthrough is non-automatable. | Final closure remains pending until Michele walks the site. |
| Direct deep links are not enough for testability. | Before PO validation, publish the game through CMS, verify `/games/library`, launch demo from the lobby card through the engine's approved demo bootstrap, and verify real mode reaches the table-balance gate. |

## 6. Platform Debt Before Game 4

These were acceptable as a bridge for game 3, but should not be repeated:

| Debt | Current shape | Required next action |
| --- | --- | --- |
| Player account history game fan-out | Account UI explicitly merges Mines, BOXE and HI-LO. | Introduce game replay/history registry. |
| Admin finance replay fan-out | Admin finance panel has per-game replay branches. | Introduce admin replay adapter registry. |
| Finance detail copy | Game-specific detail strings are ad hoc. | Each game owns finance/account summary copy through the reporting descriptor. |
| Runtime config adapters | Each game still owns config shape mapping. | Keep game-specific mapping, but expose through a typed registry. |
| Active-round resume | HI-LO added game endpoint directly. | Decide if generic recovery adapter is needed before game 4 or after. |
| Access-session auto-settle dispatcher | Platform now handles Mines, BOXE and HI-LO explicitly, each with game-specific progress semantics. | Before game 4, replace the next explicit branch with a registered per-game settlement adapter. |

Rule of thumb: a third explicit branch can be a bridge; a fourth explicit branch
is usually platform debt becoming architecture.

## 7. Stop-And-Ask Defaults

Ask Michele/CTO only when the answer changes product, money, fairness, legal
risk, or scope. Do not ask about local implementation preferences when the
codebase already has a pattern.

Mandatory Stop-and-Ask topics:

| Topic | Stop condition |
| --- | --- |
| RTP / payout / max-win | Product target or legal/economic risk is unclear. |
| Real-money launch | Any path can bypass explicit table amount selection. |
| Timeout recovery | Game has collectible exposure and no approved resume/auto-close policy. |
| Visual reference | Screenshots/mockups conflict or do not cover target states. |
| Game-specific exception vs Mines | No product doc justifies the divergence. |
| Admin field parity | A Mines capability has no equivalent and is not game-specific. |
| Finance/replay reporting | New game cannot explain a round in player account/admin finance or replay cannot be reconstructed deterministically. |

## 8. Expected Effort

Post-HI-LO baseline for a game with similar complexity:

| Area | Expected prompts | Assumption |
| --- | ---: | --- |
| Method/spec/math planning | 8-12 | Source package is clear and product decisions are available. |
| Platform enablement | 3-5 | Registry cleanup is done instead of one more hard-coded branch. |
| Backend/math/API | 8-14 | Economy is not more complex than HI-LO. |
| Player runtime/content/assets | 8-14 | Shared gates and runtime shell are reused. |
| Backoffice full-depth | 5-9 | 10A-F descriptors are reused from HI-LO pattern. |
| Replay/recovery/account/admin finance | 6-10 | Registry/adapters and finance explanation contract exist before implementation. |
| Closure/distillation | 2-4 | Product owner walkthrough happens promptly. |
| Total | 39-67 | Drops if the next game is mechanically simpler; rises if registry cleanup is skipped. |

The old 24-38 prompt target is still possible only if the platform cleanup
after HI-LO is done before adding a fourth game.

## 9. Closure Deliverables For The Next Game

At final closure, produce:

- `docs/games/<game>/CLOSURE_REPORT.md`
- `docs/NEXT_GAME_REPLICATION_BRIEF_FROM_<GAME>_<DATE>.md`
- `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_<GAME>_<DATE>.md` if
  Surface 10 produced any reusable lesson
- Playbook updates for reusable lessons only
- Template updates if the same product question appears again
- Mermaid map update if architecture, ownership or flow changed

Final green requires the product owner row to be green, not just tests.
