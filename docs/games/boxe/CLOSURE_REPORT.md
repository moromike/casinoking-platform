Status: ACTIVE
Last meaningful update: 2026-05-19

# BOXE Closure Report

Final closure for the BOXE project. This report distills the BOXE
Implementation Log into reusable methodology for game 3 and later.

## 1. Summary

BOXE is functionally complete and E2E-validated on the local CasinoKing
platform:

| Area | Closure state |
| --- | --- |
| Player gameplay | Demo, real cash, real bonus, loss, top-row and retry flows validated. |
| Backend | Math/RNG/fairness, schema, state machine, API, adapter, finance, replay and i18n complete. |
| Frontend | `/boxe`, boot shell, gameplay, animations, audio hooks and visual baseline complete. |
| Admin | Config/copy/rules, assets/theme and Site/Lobby publication complete. |
| Docs | SPEC, MATH_SPEC, Architecture Mapping, Atlas, manual checklist and Closure Report active. |
| Method | Playbook v1 and Template v1 produced from BOXE learnings. |

BOXE also delivered the promised second output: a battle-tested new-game
Playbook and richer Brief Template for HI-LO and later games.

Closure WP declaration: Docs-only distillation, no production code touched, no
architecture changes.

| Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Playbook v1 distillation | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | NEW |
| Template v1 distillation | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | NEW |
| BOXE Closure Report | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NEW | NEW |
| Capability Inventory BOXE | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | UPDATED |
| BOXE_PROJECT_BRIEF tracked | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NEW | TRACKED |
| README index closure | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | UPDATED |
| Implementation Log closure | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | UPDATED |

## 2. Effort Actual Vs Estimated

Prompt counts are handoff-level counts reconstructed from brief/gate/update
messages, not hidden tool-call counts.

| Work package | Original estimate | Actual handoff prompts | Notes |
| --- | --- | --- | --- |
| Phase 0 SPEC | 5-7 | 3 | SPEC closed without extra product Stop-and-Ask. |
| Phase 1 Architecture Mapping | 3-5 | 3 | Title Editor risk correctly marked as watchpoint. |
| Phase 2A Math/RNG/Fairness | 8-12 | 3 | Product Option C unlocked formula derivation. |
| Phase 2B Schema/State | 6-9 | 3 | BOXE-owned schema, no platform schema change. |
| Phase 2C API | 6-9 | 3 | API/idempotency/error mapping stayed game-specific. |
| Backend platform adapter WP | 9-13 | 3 | Unplanned but reusable platform prerequisite. |
| Phase 2D Adapter/Finance/Replay | 8-12 | 4 | Paused and resumed after backend platform adapter. |
| Frontend runtime agnostic WP | 4-6 | 3 | Unplanned platform prerequisite before 3A. |
| Phase 3A Standalone Boot | 5-7 | 4 | Paused and resumed after runtime namespace refactor. |
| Phase 3B Gameplay | 8-12 | 3 | Largest frontend gameplay WP, no shell extension. |
| Phase 3C Animations/Polish | 5-8 | 3 | Visual baseline and reduced-motion added. |
| Title Editor agnostic WP | 5-9 | 3 | Unplanned platform prerequisite before 4A. |
| Phase 4A Admin Config/Copy | 5-8 | 4 | Title Editor refactor paid off immediately. |
| Phase 4B+5+6 Combined | 12-19 | 3 | Combined safely after platform patterns stabilized. |
| Phase 7 E2E Validation | 5-8 | 3 | Atlas drift and Mines baseline refresh handled. |
| Closure Distillation | 5-8 | 3 | Docs-only methodology closure. |

The largest cost variance came from the three game-agnosticity platform WPs.
Those are now part of Playbook v1 audits instead of surprises.

## 3. Discoveries

| Discovery | Where found | Closure action |
| --- | --- | --- |
| Backend adapter was Mines-shaped | BOXE 2D Stop-and-Ask | Playbook v1 pre-Phase 2D backend adapter audit. |
| Frontend game-runtime storage was Mines-shaped | BOXE 3A Stop-and-Ask | Playbook v1 pre-Phase 3A frontend runtime audit. |
| Title Editor shell was Mines-shaped | BOXE 4A Stop-and-Ask | Playbook v1 pre-Phase 4A Title Editor audit. |
| Mines runtime RTP diverged from doc target | Mines retroactive math pass | Template v1 adds `rtp_demo` / `rtp_production`; Playbook anti-pattern added. |
| Atlas drift persisted after implementation | BOXE Phase 7 | Phase 7 atlas verification now mandatory. |
| Mines visual baseline drifted after RTP fix | BOXE Phase 7 | Baseline refresh tied to math/UI-changing WP. |

## 4. Generalization Candidates Distilled

| Candidate | Distilled into |
| --- | --- |
| Pre-Fase 2 architecture mapping must verify platform adapter game-agnosticity. | Playbook v1 section 6.1 and Known Structural Risks. |
| Pre-Fase 3A must audit `game-runtime/` hardcoding: storage, context, audio, theme, gates. | Playbook v1 section 6.1 and Game Runtime Atlas. |
| Pre-Fase 4A must audit Title Editor registry/types/command bar/config loading/diagnostics. | Playbook v1 section 6.1 and Game Runtime Atlas audit pattern. |
| RTP target must be explicit per environment. | Template v1 Math & RNG fields `RTP demo` and `RTP production`; pending production memo below. |
| Asset kind semantics must be decided upfront. | Template v1 Visuals & Assets fields for lobby card and board symbol kinds. |
| Game-over reveal logic needs game-specific detail. | Template v1 Special behaviors field. |
| BOXE state machine pattern is reusable for ladder/pick games. | Template v1 State machine default pattern. |
| Atlas drift is a real closure risk. | Playbook v1 Phase 7 atlas verification. |
| Visual baseline refresh belongs with the changing WP. | Playbook v1 anti-pattern catalog. |

## 5. Lessons Learned

What went well:

- Stop-and-Ask worked: platform gaps were extracted as platform WPs instead of
  becoming BOXE scope creep.
- Math derivation stayed explicit: anchor reconciliation, formula, simulator
  and stress framework are audit-ready for future certification work.
- Contract boundaries paid off: BOXE did not import Mines, and shared runtime
  did not import BOXE.
- Combining 4B+5+6 was safe only after backend, frontend runtime and Title
  Editor shared patterns were already generalized.

What can improve:

- The three game-agnosticity audits should happen in Fase 1/early planning, not
  at the consumption point.
- Atlas verification should not wait for a human noticing stale wording.
- Visual baseline refresh should be scheduled in the same WP as math/UI drift.
- Prompt estimates should separate game-specific work from platform extraction
  work more explicitly.

## 6. Memo For HI-LO

Expected HI-LO cost with Playbook v1:

| Area | Expected effect |
| --- | --- |
| Backend adapter | Already game-agnostic after BOXE; audit should be quick unless HI-LO needs new finance metadata. |
| Frontend runtime | Namespace whitelist exists; add `hilo` namespace after audit instead of refactoring shell from scratch. |
| Title Editor | Registry/generic props exist; add HI-LO editor plugin instead of shell refactor. |
| Template input | v1 asks for RTP, asset kind, reveal logic and state machine upfront. |
| Math framework | BOXE/Mines simulator and stress patterns can be reused. |
| Session recovery | Scenario-based design exists; HI-LO should map to it in SPEC. |

Estimated reduction: 40-50% fewer methodology and Stop-and-Ask prompts than
BOXE if HI-LO fits the same shell/platform model. The reduction comes from not
repeating the three platform agnostic refactors and from richer upfront product
questions.

## 7. Pending Production Items

| Item | Status | Owner / timing |
| --- | --- | --- |
| Mines production RTP target around 92% | Deferred | Future pre-launch production WP. |
| RTP configurable per environment (`demo` / `production`) | Deferred | Same math production WP; affects Mines and BOXE. |
| External actuarial / fairness certification | Deferred | Production readiness roadmap, after product stabilizes. |
| Session Recovery Engine implementation | Designed, not fully implemented | Reuse existing design for future production hardening. |
| Player visible provably fair UI | Deferred product/platform decision | Do not implement game-by-game. |

## References

- BOXE SPEC: `docs/games/boxe/SPEC.md`
- BOXE Math Spec: `docs/games/boxe/MATH_SPEC.md`
- BOXE Architecture Atlas: `docs/ARCHITECTURE_ATLAS_BOXE.md`
- BOXE Implementation Log: `docs/games/boxe/BOXE_BRIEF.md`
- New Game Playbook v1: `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`
- New Game Brief Template v1: `docs/NEW_GAME_BRIEF_TEMPLATE.md`
- Production readiness RTP memo: `docs/PRODUCTION_READINESS_ROADMAP.md`
