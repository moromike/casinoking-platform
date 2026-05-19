Status: ACTIVE
Last meaningful update: 2026-05-19

# BOXE Closure Report

Final closure record for BOXE as game 2 and for the methodology distilled into
Playbook v2. This report is intentionally stricter than the original closure:
the backend and pre-game shell are usable platform wins, but the post-audit
truth is that BOXE gameplay and admin still need structural parity WPs before
the product should be called visually accepted.

## 1. Summary

BOXE is backend-complete and E2E-validated as a functional CasinoKing game
prototype. It is not yet visually excellent and it is not the model to copy
locally for HI-LO. BOXE's real value is that it exposed which pieces of Mines
must become shared platform before games 3-20 can be cheaper.

| Area | Closure state |
| --- | --- |
| Player gameplay | Demo, real cash, real bonus, loss, top-row and retry flows validated. Gameplay UX is functional but still visually partial vs BOXE mockups and Mines shell expectations. |
| Backend | Math/RNG/fairness, schema, state machine, API, adapter, finance, replay and i18n complete. |
| Frontend | Pre-game shell extracted/aligned with Mines. Gameplay surface still needs GameControlRail, RuntimeTools, StageHeader and BOXE board visual WPs. |
| Admin | Base Title Editor support works. Tab-level parity and shared schema/adapters still need extraction. |
| Docs | SPEC, MATH_SPEC, Architecture Mapping, Atlas, Retrospective, Full Parity Audit, Playbook v2, Template v2 and Closure Report active. |
| Method | Playbook v2 and Template v2 produced from BOXE failures, fixes and audit evidence. |

Closure WP declaration: docs-only distillation, no production code touched in
this WP, no architecture changes.

| Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Playbook v2 distillation | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | ACTIVE |
| Template v2 distillation | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | ACTIVE |
| BOXE Closure Report extended | n/a | n/a | n/a | n/a | n/a | n/a | n/a | UPDATED | ACTIVE |
| BOXE Retrospective consumed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | READ | ACTIVE |
| BOXE Full Parity Audit consumed | n/a | n/a | n/a | n/a | n/a | n/a | n/a | READ | ACTIVE |

## 2. Effort Actual Vs Estimated

Prompt counts below are handoff-level counts reconstructed from
brief/gate/update messages, not hidden tool-call counts. They undercount the
real cognitive/project burden because BOXE later required shell extraction,
retrospective, full parity audit and v2 distillation.

| Work package | Original estimate | Actual handoff prompts | Notes |
| --- | --- | --- | --- |
| Phase 0 SPEC | 5-7 | 3 | SPEC closed without extra product Stop-and-Ask. |
| Phase 1 Architecture Mapping | 3-5 | 3 | Title Editor risk marked, but visual gates were not enforced. |
| Phase 2A Math/RNG/Fairness | 8-12 | 3 | Product Option C unlocked formula derivation. |
| Phase 2B Schema/State | 6-9 | 3 | BOXE-owned schema, no platform schema change. |
| Phase 2C API | 6-9 | 3 | API/idempotency/error mapping stayed game-specific. |
| Backend platform adapter WP | 9-13 | 3 | Unplanned but reusable platform prerequisite. |
| Phase 2D Adapter/Finance/Replay | 8-12 | 4 | Paused and resumed after backend platform adapter. |
| Frontend runtime agnostic WP | 4-6 | 3 | Unplanned platform prerequisite before 3A. |
| Phase 3A Standalone Boot | 5-7 | 4 | Paused and resumed after runtime namespace refactor. |
| Phase 3B Gameplay | 8-12 | 3 | Functional gameplay shipped, but visual parity was not gated. |
| Phase 3C Animations/Polish | 5-8 | 3 | Visual baseline captured current state, not target mockups. |
| Title Editor agnostic WP | 5-9 | 3 | Shell refactor helped, but inner admin tabs stayed too Mines-local. |
| Phase 4A Admin Config/Copy | 5-8 | 4 | Worked functionally; shared admin parity still pending. |
| Phase 4B+5+6 Combined | 12-19 | 3 | Combined safely after platform patterns stabilized. |
| Phase 7 E2E Validation | 5-8 | 3 | Atlas drift and Mines baseline refresh handled. |
| Platform pre-game shell extraction | 8-12 | 5 | Required after product owner visual bugs; correctly extracted shared gates. |
| Retrospective + full parity audit | 5-8 | 4 | Exposed 34 surfaces and structural correction mix. |
| Playbook v2 distillation | 2-3 | 1 | This WP records the system-level learnings. |

Calibration for future planning: the full BOXE journey cost is best treated as
about 150+ prompts of product/engineering attention once refactors, fixes,
audit and distillation are included. HI-LO should be 24-38 prompts only if the
next WPs extract shared shell/admin primitives instead of patching BOXE locally.

Hard risk: BOXE local patches would make HI-LO cost close to BOXE again.

## 3. Discoveries

| Discovery | Where found | Closure action |
| --- | --- | --- |
| Backend adapter was Mines-shaped | BOXE 2D Stop-and-Ask | Playbook v2 pre-phase backend adapter audit. |
| Frontend game-runtime storage was Mines-shaped | BOXE 3A Stop-and-Ask | Playbook v2 pre-phase frontend storage/context audit. |
| Title Editor shell was Mines-shaped | BOXE 4A Stop-and-Ask | Playbook v2 Title Editor engine-agnosticity audit. |
| Table/session lifecycle symmetry was incomplete | Shell extraction Step 3 | Playbook v2 backend lifecycle symmetry audit. |
| Shared components existed without true consumption | Shell extraction Step 4 | GameRuntimeShell consume audit added. |
| Gate sequencing diverged between Mines and BOXE | Shell extraction Step 5 | Reference sequencing gate added. |
| Mockups were listed but not enforced as gates | Retrospective + audit | Visual reference contract added to Playbook/Template v2. |
| Visual baselines captured current state, not target | Full parity audit | Separate `reference_match` suite required. |
| Gameplay rail/tools/header are platform, not game-local | Full parity audit | GameControlRail, RuntimeTools and StageHeader added as platform target. |
| Admin inner tabs remain a platform extraction area | Full parity audit | Title Editor shared tabs with schema adapters added to Playbook v2. |

## 4. Generalization Candidates Distilled

| # | Candidate | Distilled into |
| --- | --- | --- |
| 1 | Pre-Phase backend platform adapter game-agnosticity audit. | Playbook v2 Pre-Phase Mandatory Audits. |
| 2 | Pre-Phase frontend storage/context namespace audit. | Playbook v2 Pre-Phase Mandatory Audits. |
| 3 | Pre-Phase Title Editor engine-agnosticity audit. | Playbook v2 Pre-Phase Mandatory Audits. |
| 4 | Scaffolding is not shared implementation. | Playbook v2 Anti-pattern Catalog. |
| 5 | Shared shell plus game-specific visual/copy adapter. | GameRuntimeShell as Platform Pattern. |
| 6 | Shared visual plus game-specific submit callback. | GameTableBalanceGate / shell adapter guidance. |
| 7 | Gate sequencing must replicate the reference game. | Phase 3B/3C visual gates. |
| 8 | CSS cleanup must check both extracted and source sides. | Anti-pattern Catalog and shell extraction checklist. |
| 9 | Mockups are binding visual acceptance gates. | Template v2 Visuals & Assets and Playbook visual contract. |
| 10 | Pre-3B visual contract maps mockup frame to DOM region, component and baseline. | Playbook v2 Phase 3B/3C Visual Gates. |
| 11 | Left rail decision must be explicit before coding. | Template v2 Pre-Phase Checklist. |
| 12 | Visual reference baselines must be separate from regression baselines. | Playbook v2 `reference_match` rule. |
| 13 | Side-by-side Playwright evidence is mandatory in Phase 7. | Playbook v2 Phase 7 closure. |
| 14 | Backend lifecycle symmetry is a pre-frontend architecture gate. | Playbook v2 Pre-Phase Mandatory Audits and Template v2 Backend lifecycle parity. |
| 15 | GameRuntimeShell with slots/adapters is the actual architecture. | Playbook v2 GameRuntimeShell as Platform Pattern. |
| 16 | Critical WPs use Parte A/B: approach validation, then execution. | Playbook v2 Pattern Operativo CTO. |
| 17 | Codex must be briefed as partner of thought, not executor only. | Playbook v2 Pattern Operativo CTO. |
| 18 | RTP target must be configurable/explicit per environment. | Template v2 Math & RNG. |
| 19 | Implementation Log discoveries must flow into product decisions. | Playbook Update Protocol and Closure Report. |

## 5. Post-Audit Parity Findings

The full parity audit reviewed 34 surfaces across player-facing UI, admin
backoffice and cross-cutting visual systems.

| Verdict | Count | Meaning |
| --- | --- | --- |
| Aderente | 9 | Mostly backend/pre-game shared shell and launch surfaces. |
| Parziale | 15 | Functional, but not yet structurally or visually aligned enough. |
| Divergente | 7 | BOXE current behavior/layout differs materially from product expectation. |
| Mancante | 3 | Required surfaces absent or not product-acceptable. |

Correction type distribution from the 25 non-aderent surfaces:

| Correction type | Count | Share | Meaning |
| --- | --- | --- | --- |
| Shared extraction | 18 | 72% | Mines-local implementation should become game-runtime/title-editor shared and be consumed by Mines + BOXE. |
| BOXE consume existing shared | 3 | 12% | Shared exists, BOXE consumes it incompletely or incorrectly. |
| BOXE game-specific | 3 | 12% | Real game-specific board/payout/mockup work. |
| Mines local future extraction | 1 | 4% | Platform debt to track for HI-LO even if not required for BOXE. |

This distribution confirms the product owner thesis: BOXE should be a forcing
function for platform extraction. The wrong response would be to paint BOXE
until it looks acceptable while leaving Mines logic local.

Product owner decisions now captured in Playbook/Template v2:

| Decision | Closure encoding |
| --- | --- |
| Left rail should be ergonomically similar to Mines, not pixel-perfect. | Template v2 left rail decision and GameControlRail default. |
| BOXE mockups are composition reference, not Hacksaw pixel-gate. | Visual fidelity level field. |
| Bottom system icon strip is mandatory v1. | GameRuntimeTools default. |
| BOXE palette stays close to Mines. | Color palette default and anti-pattern. |
| Sounds admin tab is silent v1/deferred. | Admin shared tabs use capability flags. |
| Replay viewer is mandatory acceptable parity. | GameRuntimeTools and replay fields. |
| Table session placeholder is demo-only. | Backend lifecycle parity section. |
| Admin extraction can run in parallel to gameplay. | Pattern operativo CTO and WP ordering. |
| Mobile portrait is an acceptance gate. | Phase 3B/3C visual gates. |
| Existing diamond/mine assets are binding immediately. | Template visual asset gates. |

## 6. Lessons Learned

What went well:

- Stop-and-Ask worked when used: platform gaps became platform WPs instead of
  silent BOXE hacks.
- Math derivation stayed explicit: formula, simulator and stress framework are
  reusable for future certification work.
- Contract boundaries paid off: BOXE did not import Mines, and shared runtime
  did not import BOXE.
- The pre-game shell extraction proved that shared visual parity is achievable
  when both games consume the same component.

What failed:

- Mockups were not treated as binding inputs. That is the root product failure
  of BOXE frontend.
- "Visual baseline green" was confused with "visual target met". Baselines
  protected the wrong current state.
- CTO/Codex review accepted namespace and shell scaffolding evidence too often
  without proving rendered shared consumption.
- Phase 3B should have stopped before coding gameplay and asked for the visual
  contract: mockup frame, DOM region, shared component, adapter, baseline.
- Admin was considered "done" because config worked; for games 3-20, tab-level
  extraction matters as much as player shell extraction.

## 7. Memo For HI-LO

Expected HI-LO cost with Playbook v2, assuming the next BOXE WPs extract shared
runtime/admin surfaces instead of local patches:

| Area | Expected effort | Notes |
| --- | --- | --- |
| Backend math/RNG/fairness/state/API/adapter | 10-15 prompts | BOXE patterns reusable; still audit lifecycle and finance symmetry. |
| Frontend | 8-12 prompts | Only realistic if GameControlRail, RuntimeTools, StageHeader and mobile shell are shared first. |
| Admin | 2-4 prompts | Requires shared Title Editor tabs with schema adapters. |
| Visual fidelity | 2-4 prompts | Mockup-gated composition reference, not retroactive polish. |
| Validation | 2-3 prompts | Contract, side-by-side, reference_match and regression suites. |
| Total | 24-38 prompts | Target is plausible but conditional. |

If BOXE is fixed through local CSS/components, HI-LO will not be 40-50% cheaper.
It will inherit the same hidden platform work and the Playbook will be mostly
ceremony.

## 8. Pending Production Items

| Item | Status | Owner / timing |
| --- | --- | --- |
| BOXE GameControlRail / RuntimeTools / StageHeader shared extraction | Required | Next player-facing parity WPs. |
| BOXE board and payout visual composition against mockups | Required | After/shared with shell slot extraction. |
| Title Editor tab extraction with schema adapters | Required | Parallel admin WP before HI-LO. |
| Table session lifecycle closed for production | Deferred for demo only | Must close before production real-money launch. |
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
- BOXE Retrospective: `docs/games/boxe/BOXE_RETROSPECTIVE_ANALYSIS_2026-05-19.md`
- BOXE Full Parity Audit: `docs/games/boxe/BOXE_FULL_PARITY_AUDIT_2026-05-19.md`
- New Game Playbook v2: `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`
- New Game Brief Template v2: `docs/NEW_GAME_BRIEF_TEMPLATE.md`
- Production readiness RTP memo: `docs/PRODUCTION_READINESS_ROADMAP.md`
