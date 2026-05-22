Status: ACTIVE
Last meaningful update: 2026-05-22

# HI-LO Project Method And Execution Plan

## 0. How To Use This Document

This is the full method document. Start from the short guide first:

`docs/games/hi-lo/HI_LO_AI_QUICKSTART_2026-05-22.md`

Use this document as the control system behind the QuickStart.

| If you need to... | Read |
| --- | --- |
| Start a fresh AI session | QuickStart + section 13 prompt template |
| Understand why HI-LO is method-first | Sections 1-5 |
| Plan the project phases | Section 6 |
| Estimate prompt/work cost | Section 7 |
| Track adherence and false-green risk | Sections 8-10 |
| Decide when to stop and ask | Section 11 |
| Distill lessons for future games | Section 12 |
| Create the first HI-LO-specific docs | Sections 13 and 15 |

This document is intentionally broad. The HI-LO-specific analysis will live in
separate documents created during Phase 1. Do not confuse the method with the
game SPEC.

## 1. Purpose

This document defines how CasinoKing will approach HI-LO before implementation.
It is a methodology and execution-control plan, not the HI-LO game SPEC.

The goal is to make HI-LO the first new-game project that is executed with the
BOXE lessons built into the process from day one, so future games can be built
by multiple AI agents with less manual rescue work.

This plan must be approved before Codex starts the actual HI-LO source analysis
or writes any production code.

## 2. Non-Goals For This Document

This document does not:

- analyze HI-LO rules, math, visuals or assets;
- implement HI-LO;
- make product decisions about HI-LO mechanics;
- override `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`;
- replace the future `docs/games/hi-lo/SPEC.md`.

The HI-LO analysis folder exists at:

`assets/Games/hi-lo`

That folder is an input for the next phase. The video is explicitly out of
scope for this methodology pass because Michele already converted it into an
analysis document.

## 3. Mandatory Inputs

### 3.1 Process Inputs Already Read For This Plan

| Document | Why it matters |
| --- | --- |
| `docs/README.md` | Entry point and documentation index. |
| `docs/SOURCE_OF_TRUTH.md` | Project precedence and canonical domain boundaries. |
| `docs/TASK_EXECUTION_GUARDRAILS.md` | Required task behavior, capability matrix and implementation log rule. |
| `docs/DOCUMENTATION_MAINTENANCE.md` | Rules for updating docs as the project evolves. |
| `docs/AI_CRITICAL_JUDGMENT_RULES.md` | Anti-yes-man behavior and risk escalation. |
| `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` | Core reusable recipe for new games after BOXE. |
| `docs/NEW_GAME_BRIEF_TEMPLATE.md` | Product input structure and default decisions for new games. |
| `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_BOXE_2026-05-22.md` | Mandatory BOXE backoffice lessons for HI-LO. |
| `docs/games/boxe/CLOSURE_REPORT.md` | BOXE closure status, effort baseline and residual warnings. |
| `docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md` | Navigable code map for routing future agents to the right layers. |

### 3.2 Mandatory Inputs For The Next HI-LO Analysis Phase

These are not fully consumed in this methodology pass. They must be consumed
before HI-LO SPEC work starts.

| Input | Required handling |
| --- | --- |
| `assets/Games/hi-lo/` analysis document(s) | Read fully, excluding the video unless Michele explicitly asks. |
| `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` | Re-read relevant sections 3, 5, 6.2, 6.3, 13.1 and Rules 13-16. |
| `docs/NEW_GAME_BRIEF_TEMPLATE.md` | Fill/resolve every HI-LO input field or mark Stop-and-Ask. |
| `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_BOXE_2026-05-22.md` | Treat Surface 10 as decomposed 10A-F from the start. |
| `docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md` | Use as navigation; update when ownership/boundaries change. |
| Mines player/admin code | Reference behavior and shared platform source. |
| BOXE player/admin code | Second-game precedent and anti-pattern memory. |
| Existing artifacts under `artifacts/` | Use only as evidence/reference; do not treat screenshots as product source unless the relevant doc says so. |

## 4. Operating Model

### 4.1 HI-LO Execution Mode

For HI-LO, Michele wants to execute primarily with Codex. Codex therefore acts
as:

- analyst;
- CTO assistant;
- code writer;
- internal reviewer;
- verifier;
- merge/gate operator.

That does not remove the need for external challenge. It means challenge must
be explicit in the process instead of implied by a second human/AI.

### 4.2 Future Multi-AI Requirement

The output of HI-LO must be usable by future projects that may involve several
AI systems. Therefore every phase must leave durable artifacts:

- source inventory;
- product decision log;
- capability matrix;
- 12-surface tracker;
- evidence ledger;
- implementation log;
- closure brief for the next game.

Future AI agents should be able to continue after reading repository docs, not
private chat memory.

### 4.3 Internal Codex Roles

Every critical phase uses three explicit passes:

| Pass | Role | Required behavior |
| --- | --- | --- |
| 1 | Codex Analyst | Produce the analysis, plan or implementation approach. |
| 2 | Codex CTO Reviewer | Challenge scope, architecture, hidden coupling, missing gates and false-green risk. |
| 3 | Codex Verifier | Re-check from filesystem/evidence, not from memory. Mark weak/missed/wrong items. |

For critical surfaces, especially backoffice and content, this role separation
uses Playbook Rule 13 two-step audit mechanics.

### 4.4 External CTO / Claude Re-Engagement Points

Codex can run most of HI-LO, but this plan explicitly defines optional/strong
external CTO review points. These are not daily dependencies; they are brakes
for the places where BOXE proved self-validation can fail.

| Point | Trigger | Expected external review |
| --- | --- | --- |
| After Phase 1 source intake | HI-LO product decisions or source interpretation are ambiguous. | Validate whether the question list is complete. |
| Before first implementation Wave | Architecture mapping and WP split are ready. | Validate scope, dependencies, worktree plan and Stop-and-Ask list. |
| Before any platform extension | Codex proposes shared runtime/admin/backend changes. | Validate whether change belongs to platform or HI-LO-specific layer. |
| Backoffice closure | Surface 10 is being marked green. | Review decomposed 10A-F evidence or at least the verifier table. |
| Any product dispute | Product request conflicts with risk, legality, wallet/ledger, or visual acceptance. | Validate decision path before code. |
| Final closure | Codex says HI-LO is done. | Optional final check of `:3000` evidence, 12/12 status and distillation docs. |

If Claude is not available, Codex must still run the internal CTO Reviewer and
Verifier passes and explicitly state that external review was skipped.

## 5. Definition Of Green

For HI-LO, green is never "component exists" or "test passed" alone.

A surface is green only when all applicable layers are green:

| Layer | Required proof |
| --- | --- |
| Container | Shared shell/component is mounted where expected. |
| Content | Game-specific copy, rules, headings, sections, labels and admin fields are complete. |
| Visual | Side-by-side or reference-match screenshot confirms expected appearance. |
| Functional | The user/admin flow actually works end-to-end. |
| Persistence | Admin/backend state is saved, published and reloaded correctly where applicable. |
| Runtime consume | Player runtime consumes the saved/admin-uploaded data. |
| Tests | Focused automated tests cover the behavior. |
| Product owner | Michele validates critical player/admin flows on `localhost:3000`. |

The last row is a hard gate for Wave closure. Product owner walkthrough on
`:3000` is not optional, because BOXE repeatedly showed that AI/test evidence
can still miss product-visible gaps.

At every HI-LO Wave closure, Codex must output the eight-layer green table for
each affected surface. It is not enough to state "green" in prose. Missing
Product Owner validation means the Wave is not green yet for critical player or
admin surfaces.

## 5.1 Product Decision Brief In Chat

Repository documents are the durable memory for Codex and future AI agents.
They are not a substitute for asking Michele for decisions in the conversation.

At the end of every analysis/planning phase, Codex must include a short
Product Decision Brief directly in chat:

- what Codex completed;
- which defaults Codex recommends;
- which decisions Michele must approve now;
- which questions are Stop-before-code;
- what Codex will do next if Michele says OK.

Michele is not expected to read long documents to discover hidden questions.
If a document contains 30 open questions, Codex must group them into a small
number of decision clusters and ask only the choices that matter for the next
step. The full tables remain in docs for traceability.

## 5.2 Classification Rule: Reusable / Platform / HI-LO-Specific

Every HI-LO discovery, decision or implementation note must be classified before
it is distilled into broader methodology.

| Category | Meaning | Where it lives | Distill forward? |
| --- | --- | --- | --- |
| Reusable method | Process rule valid for any future game. | Playbook, method docs, future template. | Yes. |
| Platform pattern | Shared capability or component reusable by multiple games. | `game-runtime/`, `title-editor/`, backend platform modules, Mermaid map, Playbook. | Yes, as platform guidance. |
| HI-LO-specific | Mechanics, visuals, math, copy or assets specific to HI-LO. | HI-LO SPEC, MATH_SPEC, source inventory, decision map, architecture mapping. | No, unless it reveals a reusable process/platform lesson. |

Examples:

| Item | Classification | Handling |
| --- | --- | --- |
| Product owner `:3000` walkthrough gate | Reusable method | Keep in Playbook/method. |
| Replay modal shell | Platform pattern | Reuse/extract shared shell, HI-LO supplies renderer. |
| Higher/lower card comparison rules | HI-LO-specific | Keep in HI-LO SPEC/MATH_SPEC. |
| Deck RNG proof format | HI-LO-specific + possible platform fairness pattern | Put concrete rules in HI-LO MATH_SPEC; distill only any reusable fairness lesson. |
| Card face/skin asset kind | Platform pattern + HI-LO-specific asset kind | Shared asset pipeline, HI-LO-specific kind/defaults. |

Rule: a HI-LO-specific decision is not a reusable rule unless it reveals a
repeatable platform or process pattern. Keep game mechanics in HI-LO docs;
distill only what future games should copy.

## 6. Project Phases

### 6.0 Planning Granularity

HI-LO planning uses three levels. Future games should reuse the same shape.

| Level | Meaning | Artifact |
| --- | --- | --- |
| High level | Project phase: source intake, SPEC, architecture, implementation, closure. | This document + Wave plan. |
| Medium level | Work package: backend math, player shell, board UI, backoffice, replay, content. | Parte A approach doc + capability matrix. |
| Detail level | Concrete task/gate: files, tests, screenshots, `:3000` walkthrough, docs update. | Parte B delivery report + evidence ledger. |

AI agents may work in parallel only at medium level, after the high-level
phase and file ownership are approved. Detail-level tasks must be explicit
enough that a fresh agent can execute without private chat context.

### Phase 0 - Method Approval And Source Pack

Objective: freeze the execution method before touching HI-LO content.

Tasks:

1. Approve this document.
2. Create a HI-LO source inventory without interpreting content yet.
3. Confirm which HI-LO source files are binding and which are inspirational.
4. Confirm video exclusion unless Michele reopens it.
5. Create initial tracking sections in the future HI-LO brief/SPEC.

Outputs:

- this document approved;
- `docs/games/hi-lo/SOURCE_INVENTORY_2026-05-22.md` or equivalent;
- initial Stop-and-Ask register;
- initial product decision log.

Gate:

- Michele confirms the methodology is acceptable.

Estimate: 2-4 prompts.

### Phase 1 - Source Intake And Product Decision Map

Objective: understand HI-LO enough to know what must be specified before code.

Tasks:

1. Read the HI-LO analysis document(s) in `assets/Games/hi-lo/`.
2. Map source claims into product decisions, open questions and implementation constraints.
3. Fill the New Game Brief Template fields for HI-LO.
4. Identify missing inputs that block SPEC.
5. Separate binding product requirements from reference/inspiration.
6. Produce first draft of 12-surface expectations.

Outputs:

- `docs/games/hi-lo/HI_LO_PRODUCT_DECISION_MAP_2026-05-22.md`;
- open questions table;
- source-to-requirement matrix;
- preliminary 12-surface status.

Gate:

- no open blocker is silently converted into a code assumption;
- optional external CTO review if the source interpretation is ambiguous.

Estimate: 3-5 prompts.

### Phase 2 - SPEC, Math And Experience Contract

Objective: turn product input into a contract that implementation can follow.

Tasks:

1. Draft `docs/games/hi-lo/SPEC.md`.
2. Draft `docs/games/hi-lo/MATH_SPEC.md`.
3. Define backend state machine, idempotency and fairness contract.
4. Define visual states, board/card geometry, payout display and action flow.
5. Define demo, real cash and bonus lifecycle expectations.
6. Define rules modal, how-to-play, replay and history requirements.
7. Define backoffice config, copy, assets, theme, sound and validation.

Outputs:

- SPEC;
- MATH_SPEC;
- visual state matrix;
- lifecycle matrix;
- replay payload proposal;
- admin capability matrix.

Gate:

- every visible/gameplay/economic behavior has a named owner and expected state;
- no real-money, payout or ledger behavior is implicit;
- product owner approves the experience contract before code.

Estimate: 5-8 prompts.

### Phase 3 - Architecture Mapping And WP Plan

Objective: decide what is shared, what is HI-LO-specific and what must be fixed
in platform before HI-LO work starts.

Tasks:

1. Run Playbook 6.2 mandatory pre-phase audits.
2. Run 12-surface audit upfront.
3. Decompose Surface 10 Backoffice into 10A-F.
4. Produce common vs game-specific vs platform-extension matrix.
5. Produce file ownership map and protected file list.
6. Produce worktree/branch plan for parallel execution.
7. Update Mermaid map plan if architecture will change.

Outputs:

- `docs/games/hi-lo/ARCHITECTURE_MAPPING.md`;
- `docs/games/hi-lo/HI_LO_12_SURFACE_STATUS.md`;
- `docs/games/hi-lo/HI_LO_WAVE_PLAN.md`;
- capability matrix skeleton for every WP.

Gate:

- no implementation WP starts without Parte A approved;
- external CTO review strongly recommended before implementation begins.

Estimate: 4-6 prompts.

### Phase 4 - Platform Prerequisite And Shared Extraction WPs

Objective: remove platform blockers before HI-LO-specific implementation pays
for them locally.

Potential areas:

- `GameControlRail`;
- `GameRuntimeTools`;
- `GameStageHeader`;
- title-editor schema adapters;
- replay shell;
- admin engine canonicalization;
- lifecycle/table-session boundary;
- asset/theme/sound capability flags;
- architecture map update.

Rule:

If a platform gap is found, open a platform WP. Do not hide it inside HI-LO.

Outputs:

- platform WP approach docs;
- platform code changes when approved;
- boundary tests;
- updated Mermaid map where ownership changes.

Gate:

- Mines and BOXE zero-regression where shared code is touched;
- HI-LO implementation is not allowed to copy Mines/BOXE local code to avoid the platform fix.

Estimate: 4-8 prompts if gaps are small; 10+ if a major shell/admin extraction
is still missing.

### Phase 5 - HI-LO Implementation Waves

Objective: implement HI-LO in controlled WPs after SPEC and architecture gates
are green.

Recommended Wave groups:

| Wave | Scope | Notes |
| --- | --- | --- |
| 5A | Backend math/RNG/fairness/state/API | Server-authoritative, deterministic, idempotent. |
| 5B | Player runtime shell consume | Boot, gates, table balance, runtime tools, control rail. |
| 5C | Gameplay board/card UI | Visual-first, no-scroll matrix, all configurations. |
| 5D | Admin/backoffice | Decomposed 10A-F from the start. |
| 5E | Replay/history/finance | Player replay, account history, admin/finance visibility. |
| 5F | Content/rules/how-to-play/audio/theme | Container + content + runtime consume. |

Every Wave uses:

1. Parte A doc-only approach;
2. Codex CTO Reviewer pass;
3. optional external CTO checkpoint if scope is critical;
4. Parte B execution;
5. automated gates;
6. visual evidence;
7. product owner `:3000` walkthrough for critical player/admin surfaces;
8. Implementation Log entry.

Estimate: 12-18 prompts if platform prerequisites are ready.

### Phase 6 - Closure, Distillation And Next-Game Handoff

Objective: prove HI-LO is closed and make game 4 easier.

Tasks:

1. Re-run 12-surface tracker.
2. Re-run critical two-step audits where required.
3. Run product owner `:3000` walkthrough.
4. Produce closure report.
5. Distill implementation log into Playbook, Template and architecture docs.
6. Produce next-game replication brief.

Mandatory outputs:

- `docs/games/hi-lo/CLOSURE_REPORT.md`;
- `docs/NEXT_GAME_REPLICATION_BRIEF_FROM_HI_LO_<DATE>.md`;
- `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_HI_LO_<DATE>.md` if Surface 10 produced any new lesson;
- Playbook update with Rule 17+ when a reusable lesson appears;
- New Game Brief Template update if a repeated product question appears;
- Mermaid map update if architecture changed.

Gate:

- 12/12 surfaces green or explicitly documented residuals approved by Michele;
- no hidden blocker;
- final services visible on `localhost:3000`;
- final closure approved by product owner.

Estimate: 5-8 prompts.

## 7. Effort Baseline

The Playbook estimates HI-LO at 24-38 prompts after BOXE if the platform shell
and admin lessons are truly reusable.

This plan adds explicit methodology and verification overhead. Current planning
baseline:

| Area | Estimate | Notes |
| --- | ---: | --- |
| Phase 0 method/source pack | 2-4 | Includes this document and source inventory. |
| Phase 1 source intake | 3-5 | Depends on quality of existing HI-LO analysis. |
| Phase 2 SPEC/math/experience | 5-8 | May grow if math/RTP is unclear. |
| Phase 3 architecture/WP plan | 4-6 | Includes 12-surface and Surface 10 decomposition. |
| Phase 4 platform prerequisites | 4-8 | Can be near-zero only if all shared shells are truly ready. |
| Phase 5 implementation | 12-18 | Backend + player + admin + replay + content. |
| Phase 6 closure/distillation | 5-8 | Includes product walkthrough and next-game handoff. |
| Total from current state | 35-57 | Wider than Playbook baseline because this includes methodology hardening. |

Target after HI-LO for game 4: reduce the total back toward 24-38 by converting
HI-LO lessons into reusable process, shared components and stronger templates.

Any deviation greater than 30% must be explained in the Implementation Log and
distilled into the Playbook or Template.

## 8. Monitoring Instruments

HI-LO must maintain the following tracking artifacts.

| Instrument | Purpose | When updated |
| --- | --- | --- |
| Source inventory | Lists every input and its binding status. | Phase 0/1 and whenever new input appears. |
| Product decision log | Records product choices and open questions. | Every Stop-and-Ask/product decision. |
| Stop-and-Ask register | Prevents unresolved blockers from becoming code assumptions. | Every phase. |
| Capability matrix | Tracks DB/backend/API/admin/player/CSS/test/docs end-to-end. | Every WP. |
| 12-surface tracker | Prevents entry-point misses. | Phase 3, every Wave closure, final closure. |
| Surface 10 10A-F tracker | Prevents backoffice false green. | Any admin Wave. |
| Evidence ledger | Lists screenshots, DOM metrics, build/test outputs and walkthrough results. | Every gate. |
| Product owner walkthrough log | Records `:3000` validation results and residuals. | Every critical Wave closure. |
| Implementation Log | Explains why decisions changed or surprises appeared. | Every WP. |
| Distillation queue | Collects Playbook/Template/brief updates before closure. | Continuous, not only final day. |

## 9. 12-Surface Tracker Template

Use this table from Phase 3 onward.

| # | Surface | Expected inheritance | HI-LO status | Evidence | Owner | Gate |
| --- | --- | --- | --- | --- | --- | --- |
| 1 | Lobby card/catalog | Platform/Mines/BOXE pattern | TBD | TBD | TBD | Screenshot + CMS publication check |
| 2 | Launch Cashier modal | Platform pattern | TBD | TBD | TBD | Demo/real/bonus launch |
| 3 | Admin preview launcher | Platform admin | TBD | TBD | TBD | Admin preview smoke |
| 4 | Provider intro gate | Shared `GameProviderBootstrap` | TBD | TBD | TBD | Browser smoke |
| 5 | How-to-play/info rules | Shared container + HI-LO content | TBD | TBD | TBD | Content + visual + test |
| 6 | Table balance gate | Shared `GameTableBalanceGate` | TBD | TBD | TBD | Real/bonus gate + safe default |
| 7 | Gameplay shell | Shared shell + game board adapter | TBD | TBD | TBD | Side-by-side + PO walkthrough |
| 8 | Mobile/rotation | Shared gate + game responsive board | TBD | TBD | TBD | Mobile + landscape |
| 9 | Embed mode | Platform runtime contract | TBD | TBD | TBD | `?embed=1` smoke |
| 10A | Admin engine page | Mines/BOXE pattern | TBD | TBD | TBD | Side-by-side |
| 10B | Admin title detail shell | Title Editor shell | TBD | TBD | TBD | Side-by-side |
| 10C | Admin tab existence | Shared tabs + game adapters | TBD | TBD | TBD | Tab inventory |
| 10D | Admin field depth | Reference parity + game-specific docs | TBD | TBD | TBD | Field audit |
| 10E | Admin draft/save/publish | Platform pattern | TBD | TBD | TBD | End-to-end persistence |
| 10F | Adjacent admin pages | Platform pattern | TBD | TBD | TBD | Route audit |
| 11 | Replay viewer | Shared shell + HI-LO renderer | TBD | TBD | TBD | Replay smoke |
| 12 | Disconnect/resume | Platform lifecycle | TBD | TBD | TBD | Resume smoke |

Surface 10 is expanded intentionally. A red 10A-F row makes Surface 10 red.

## 10. Gate Catalogue

### Product Owner Walkthrough Gate

Required for:

- first playable HI-LO runtime on `localhost:3000`;
- any visual shell closure;
- backoffice closure;
- final closure.

Minimum record:

```text
Date:
Build/commit:
Route(s):
Scenario(s):
Michele verdict: approved / approved with residuals / rejected
Residuals:
Follow-up WP:
```

### Visual Gate

Required proof:

- screenshots in `artifacts/` or `tests/visual/artifacts/`;
- side-by-side with reference when inheritance is expected;
- reference-match screenshots against HI-LO mockups when game-specific;
- no-scroll DOM measurement matrix for every user-selectable configuration.

### Backoffice Gate

Required proof:

- 10A-F tracker green;
- admin save -> backend persist -> runtime consume;
- copy/rules/theme/assets/sound/validation coverage;
- Mines and BOXE regression checks if shared editor code is touched;
- product owner walkthrough on `/admin`.

### Financial/Lifecycle Gate

Required proof:

- demo, real cash, real bonus separate;
- table session amount cannot consume full wallet balance;
- ledger/platform rounds reconcile;
- idempotency tested;
- expired/closed/session conflict errors mapped to user-facing copy.

### Closure Gate

Required proof:

- build green;
- focused smoke green;
- 12-surface tracker green or approved residual;
- evidence ledger complete;
- product owner walkthrough approved;
- Playbook/Template/replication brief updates done.

## 11. Stop-And-Ask Rules

Codex must stop before code if any of these occur:

- HI-LO source contradicts Playbook/platform constraints;
- math/RTP/fairness cannot be derived from source material;
- product decision is missing for a visible or economic behavior;
- implementation would require wallet/ledger/table-session changes;
- shared platform component is not truly ready and would be copied locally;
- Surface 10 parity requires interpreting a Mines behavior as game-specific without product citation;
- visual implementation would require scrollbars or clipped board/card areas;
- product owner rejects a `:3000` walkthrough;
- external AI/CTO advice conflicts with repository rules.

## 12. Continuous Distillation Rule

Do not wait until final closure to update methodology.

During HI-LO, if a reusable lesson appears:

1. add it to the HI-LO Implementation Log immediately;
2. add a pending item to the distillation queue;
3. update Playbook Rule 17+ or the New Game Brief Template in the same Wave
   closure if the rule will affect the next Wave;
4. otherwise update during final closure with explicit reason.

Final mandatory deliverable:

`docs/NEXT_GAME_REPLICATION_BRIEF_FROM_HI_LO_<DATE>.md`

This brief must explain how game 4 should start, what HI-LO taught, and which
steps can now be automated safely.

## 12.1 Automation Target For Future Games

HI-LO is considered methodologically successful only if the next game can start
with a much shorter human prompt. The target future flow is:

1. Product owner provides game source package and fills the brief template.
2. AI reads `docs/README.md`, Playbook, Template, previous game replication
   brief, current Mermaid map and game source package.
3. AI produces source inventory, decision map, SPEC draft and architecture
   mapping.
4. Human/CTO approves only open decisions and scope trade-offs.
5. AI executes WPs from approved plans with standard gates and evidence.

If HI-LO still requires ad-hoc rescue prompts for known BOXE failure modes
(false green, backoffice scope miss, content partial, no-scroll failure,
runtime/admin copy-paste), the method has failed and the Playbook must be
updated immediately.

## 13. First Execution Prompt Template

When Michele approves this method, the next Codex prompt should be:

```text
You are Codex for CasinoKing HI-LO. Phase 1 is source intake only, no code.

Read:
1. docs/README.md
2. docs/SOURCE_OF_TRUTH.md
3. docs/TASK_EXECUTION_GUARDRAILS.md
4. docs/AI_CRITICAL_JUDGMENT_RULES.md
5. docs/NEW_GAME_INTEGRATION_PLAYBOOK.md
6. docs/NEW_GAME_BRIEF_TEMPLATE.md
7. docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_BOXE_2026-05-22.md
8. docs/games/hi-lo/HI_LO_PROJECT_METHOD_AND_EXECUTION_PLAN_2026-05-22.md
9. docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md
10. assets/Games/hi-lo analysis documents, excluding video unless requested.

Output:
- HI-LO source inventory
- product decision map
- open questions / Stop-and-Ask register
- preliminary 12-surface status
- Codex CTO Reviewer pass
- Codex Verifier pass

No implementation.
```

## 14. Current Approval State

Status: draft created by Codex.

Next action: Michele reviews and approves/edits this methodology before Codex
starts Phase 1 source intake.

## 15. How This Method Produces The HI-LO Analysis Documents

The method document answers: "how do we run a new-game project without losing
pieces?"

The HI-LO analysis documents answer: "what exactly is HI-LO on CasinoKing?"

They must be separate because a reusable process must not be polluted with
game-specific mechanics, and a game-specific analysis must not hide behind
generic process language.

### 15.1 Required HI-LO Analysis Outputs

Phase 1 should produce at least these documents:

| Document | Purpose |
| --- | --- |
| `docs/games/hi-lo/SOURCE_INVENTORY_2026-05-22.md` | Lists every source file in `assets/Games/hi-lo`, classifies binding vs inspirational vs ignored. |
| `docs/games/hi-lo/HI_LO_PRODUCT_DECISION_MAP_2026-05-22.md` | Converts source observations into product decisions, assumptions, open questions and implementation constraints. |
| `docs/games/hi-lo/HI_LO_OPEN_QUESTIONS_2026-05-22.md` | Stop-and-Ask register before SPEC. |
| `docs/games/hi-lo/HI_LO_12_SURFACE_STATUS_2026-05-22.md` | Initial surface tracker, including Surface 10A-F. |
| `docs/games/hi-lo/SPEC.md` | Game behavior contract, created only after the decision map is reviewed. |
| `docs/games/hi-lo/MATH_SPEC.md` | Math, RNG, RTP and fairness contract. |
| `docs/games/hi-lo/ARCHITECTURE_MAPPING.md` | Shared vs HI-LO-specific vs platform-extension map. |
| `docs/games/hi-lo/HI_LO_WAVE_PLAN.md` | Approved implementation WPs and merge/gate plan. |

### 15.2 Minimum Content For The HI-LO Product Decision Map

The decision map must cover:

- game loop;
- player actions and legal state transitions;
- payout/RTP/max-win model;
- randomness/fairness model;
- visual layout, card/board area and responsive behavior;
- all selectable configurations;
- how-to-play and rules modal content depth;
- replay/history payload;
- admin engine page, title detail, config, copy, rules, assets, theme, sound,
  validation;
- demo, real cash and bonus lifecycle;
- error UX and recovery states;
- product-owner walkthrough scenarios.

### 15.3 Enough Detail Test

The method is detailed enough only if a fresh AI can answer:

1. What should I read first?
2. What must I produce before code?
3. Which surfaces can fail even if the gameplay works?
4. Which evidence proves a Wave is green?
5. When must I stop and ask Michele or a CTO reviewer?
6. What must be distilled for the next game?

The HI-LO analysis is detailed enough only if a fresh AI can answer:

1. What are HI-LO's states and legal actions?
2. What is server-authoritative?
3. What is game-specific vs inherited from the platform?
4. What must the player see in every state?
5. What must admin be able to configure and publish?
6. What tests/screenshots prove the behavior?

If either set cannot be answered, add detail before implementation.
