Status: ACTIVE
Last meaningful update: 2026-05-22

# HI-LO AI QuickStart

## Purpose

This is the short orientation guide for any AI agent starting the HI-LO project.
It points to the full method document and tells the agent what to do first.

The full methodology lives in:

`docs/games/hi-lo/HI_LO_PROJECT_METHOD_AND_EXECUTION_PLAN_2026-05-22.md`

Use this QuickStart when you need to begin work quickly without losing the
non-negotiable gates learned from BOXE.

## One-Minute Rule

Do not start by coding HI-LO.

Start by producing the HI-LO analysis documents that connect the product source
package to the reusable Playbook:

1. source inventory;
2. product decision map;
3. open questions / Stop-and-Ask register;
4. preliminary 12-surface status;
5. SPEC and MATH_SPEC only after open blockers are understood.

## Required Reading Order

Read in this order:

1. `docs/README.md`
2. `docs/SOURCE_OF_TRUTH.md`
3. `docs/TASK_EXECUTION_GUARDRAILS.md`
4. `docs/AI_CRITICAL_JUDGMENT_RULES.md`
5. `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`
6. `docs/NEW_GAME_BRIEF_TEMPLATE.md`
7. `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_BOXE_2026-05-22.md`
8. `docs/games/hi-lo/HI_LO_PROJECT_METHOD_AND_EXECUTION_PLAN_2026-05-22.md`
9. `docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md`
10. HI-LO source analysis files in `assets/Games/hi-lo/`, excluding video unless Michele asks.

## Document Map

| Need | Go to |
| --- | --- |
| Understand why this process exists | Method doc sections 1-5 |
| Know the high-level phases | Method doc section 6 |
| Know what evidence/gates are mandatory | Method doc section 10 |
| Track all 12 CasinoKing surfaces | Method doc section 9 |
| Avoid BOXE backoffice mistakes | BOXE replication brief + method sections 9-10 |
| Know when to stop and ask | Method doc section 11 |
| Know how to distill lessons for game 4 | Method doc section 12 |
| Get the first analysis prompt | Method doc section 13 |

## First Work Package

The first real HI-LO WP is doc-only.

Create:

- `docs/games/hi-lo/SOURCE_INVENTORY_2026-05-22.md`
- `docs/games/hi-lo/HI_LO_PRODUCT_DECISION_MAP_2026-05-22.md`
- `docs/games/hi-lo/HI_LO_OPEN_QUESTIONS_2026-05-22.md`
- `docs/games/hi-lo/HI_LO_12_SURFACE_STATUS_2026-05-22.md`

Do not create code in this WP.

## What The HI-LO Analysis Document Is

The HI-LO-specific analysis document is not the method document.

It should translate the source package into implementation-ready facts:

- game loop;
- states;
- math/RTP/fairness assumptions;
- visual layout and responsive behavior;
- admin/backoffice requirements;
- copy/rules/how-to-play/replay expectations;
- asset requirements;
- open decisions.

After that, SPEC and MATH_SPEC are created from the analysis.

Recommended chain:

```text
source package -> source inventory -> product decision map -> open questions
-> SPEC + MATH_SPEC -> architecture mapping -> Wave plan -> implementation
```

## Classification Rule

Before distilling a discovery into a reusable process, classify it:

| Category | Example | Destination |
| --- | --- | --- |
| Reusable method | Product owner `:3000` walkthrough gate | Playbook / method / future template |
| Platform pattern | Shared replay shell, shared title editor tab | Shared code + Mermaid map + Playbook |
| HI-LO-specific | Higher/lower card rules, deck math, card UI | HI-LO SPEC / MATH_SPEC / analysis docs |

Do not generalize HI-LO mechanics into the template. Generalize only the process
or platform lesson that future games should reuse.

## Non-Negotiable Gates

- Product owner walkthrough on `localhost:3000` is mandatory for critical Wave closure.
- Every Wave closure must include the eight-layer green table: container,
  content, visual, functional, persistence, runtime consume, tests and product
  owner. If the product-owner row is missing, critical player/admin surfaces
  are not green yet.
- Surface 10 Backoffice is decomposed into 10A-F; one red sub-layer means Surface 10 red.
- Shared component extraction is not parity unless container + content + visual + functional + persistence + runtime consume are all green.
- No gameplay board scrollbars. No clipped cells. All configurations need DOM measurement.
- Do not expect Michele to read long docs to find decisions. Every checkpoint
  must end with a short chat Product Decision Brief: completed work,
  recommended defaults, decisions needed now, Stop-before-code items and next
  action.
- Every Wave has evidence and an Implementation Log entry.
- Final HI-LO closure must produce a next-game replication brief.

## When 600 Lines Is Not Enough

The method document is intentionally not the final analysis. It is a control
system. It can be too short if it fails to force:

- complete source intake;
- 12-surface coverage;
- backoffice 10A-F coverage;
- real/bonus lifecycle coverage;
- product owner walkthrough;
- distillation forward to game 4.

If any of those are missing, extend the method before implementation.

## When 600 Lines Is Too Much

If an agent is lost, use this QuickStart first. Then jump into the full method
only for the section relevant to the current phase.

The rule is:

- QuickStart tells you where to go.
- Method tells you what must not be skipped.
- HI-LO analysis docs tell you what this specific game is.
