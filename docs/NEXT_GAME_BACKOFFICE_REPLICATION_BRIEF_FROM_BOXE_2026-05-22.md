Status: ACTIVE
Last meaningful update: 2026-05-22

# Next Game Backoffice Replication Brief - From BOXE Lessons (2026-05-22)

Handoff document for the CTO who opens the next proprietary game integration
(HI-LO or later) after BOXE. Produced as the "Replication Memory" closure
artifact of `docs/games/boxe/WAVE7_BACKOFFICE_FULL_CLOSURE_PLAN_2026-05-22.md`.

## Purpose

BOXE backoffice was declared green twice and was twice found broken by the
product owner. This document records exactly the path to avoid that, so the
next game does not pay BOXE's cost again.

## The Hard Rule

**Do not mark Surface 10 Backoffice green for shared container only.** A
surface is green only when ALL of the following are simultaneously true for
the new game vs the reference:

1. Admin engine page (`/admin/games/<engine>`): same master/variant grouping,
   same Editable Titles section, same Create variant button, same filters
   (Active/Inactive/Archived/All + Test only), same inline actions
   (Save/Preview/Archive) per row, same status badges (active, site active,
   variant tag), same lobby publication badges (Hidden/Visible/Demo
   on-off/Real on-off), same display_name editing inline.
2. Title detail page (`/admin/games/<engine>/titles/<title_code>`): same
   shell, same sub-tabs, same workflow surface (draft/save/publish).
3. Sub-editor tabs: same set (overview, copy, rules, config, assets, theme,
   sound, validation, with documented game-specific exceptions like Mines
   `grid&mines` vs game-X `rows&difficulty`).
4. Field depth per tab: every Mines field has a new-game equivalent (with
   game-specific values), including theme depth (advanced skin, skin
   assets, title presentation, background board), copy manifest depth (all
   sections including payout_display, payout_rules, fairness_explain, etc.),
   rules HTML depth (every section the reference has, with body content),
   validation breadth (all keys + maxLength + required).
5. Workflow per tab: draft save, draft publish to live, locale/rules
   persistence on draft → publish, uploaded assets actually consumed by the
   runtime (not only uploaded with success toast).
6. Admin access: canonical area access for the new game (not just engine
   alias), diagnostics panel if reference has one, RBAC parity.
7. Adjacent admin pages: asset library, copy manifest preview, finance
   drilldown — present for the new game if present for Mines.

## How To Replicate Correctly

### Step 1 — Start From The 12-Surface Audit With Decomposition

The Playbook's Surface 10 Backoffice is a multi-layer surface. Split it
locally for the audit:

- 10A — Admin engine page
- 10B — Title detail page shell
- 10C — Sub-editor tabs existence
- 10D — Field depth per tab (most failure-prone)
- 10E — Workflow (draft/save/publish)
- 10F — Adjacent admin pages

Audit each sub-layer separately. Treat any sub-layer red as Surface 10 red.

### Step 2 — Two-Step Audit Mandatory For Admin Layer

Apply Playbook Rule 13 strictly:
- Step 1 audit by Codex on the 6 sub-layers.
- Step 2 verifier mode by Codex with scope expansion required. Verifier must
  open route inventory (`frontend/app/admin/games/page.tsx`,
  `[engine]/page.tsx`, `[engine]/titles/[title_code]/page.tsx`) and walk
  each before checking sub-tabs.

### Step 3 — Side-By-Side Screenshots Per Admin Layer

Capture side-by-side screenshots Mines vs new-game on `localhost:3000/admin`
for every layer, not only for the title-detail sub-tabs:
- `/admin/games/mines` vs `/admin/games/<new-game>`
- `/admin/games/mines/titles/<some>` vs `/admin/games/<new-game>/titles/<some>`
- Each sub-tab Mines vs new-game
- Workflow screenshots: draft saved state, after publish, after locale
  switch.

If a screenshot pair shows divergence and no product document justifies it
as game-specific, treat as gap.

### Step 4 — Reject "Container Green Only"

Extracting `TitleEditorCommandBar` / `TitleEditorTabFrame` / etc. into shared
runtime is necessary but not sufficient. Each shared primitive must be
consumed AND populated with game-specific content/copy at parity with the
reference.

Verifier must walk content depth, not only container existence. If shared
container is mounted but content keys/fields/sections are fewer than the
reference, surface is partial.

### Step 5 — Use Mines As The Reference, Not As The Template

Mines is the reference implementation but not a template to copy literally.
Document explicit game-specific exceptions (e.g. Mines grid/mines matrix vs
new-game rows/difficulty choice). Anything not documented as game-specific
defaults to "must match Mines".

### Step 6 — Backend Persistence And Runtime Consume Are Part Of The Closure

Wave 7 found that BOXE admin theme saved skin in the wrong payload shape
(commit `5bb5002`), that BOXE backend did not preserve all copy keys sent by
admin (commit `2d5c912`), that uploaded BOXE board symbols were not consumed
at runtime (commit `df98da2`), and that BOXE create-variant failed in the
backend before Wave 7. The lesson: admin UI green is meaningless if backend
persistence or runtime consume is broken. Closure gate must include
end-to-end: admin save → backend persist → runtime consume → player sees.

### Step 7 — Admin Access Canonicalization When Scaling Multi-Engine

When the platform moves from a single proprietary game (Mines) to multi
(Mines + BOXE + HI-LO + …), admin RBAC area names should be canonicalized
to a multi-engine label like `games` and legacy single-engine names should
become aliases for backward compatibility (commit `d73ba60` precedent).
Plan this BEFORE adding the third game.

### Step 8 — Architecture Map Update Per Commit

Every commit that changes module ownership, admin routing, runtime
inheritance, API/domain boundaries, persistence responsibilities or the
shared-vs-game-specific split must update the Mermaid code map
(`docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md`) in the same commit, or
add an explicit follow-up note. This is recorded in `docs/README.md`
section "Architecture Map Maintenance" (2026-05-22).

## Failure Modes Specifically Recorded From BOXE

| Failure mode | Cost paid | Prevention |
| --- | --- | --- |
| Wave 4 WP-BO declared Surface 10 green based on container extraction. | One product-owner-driven audit (Wave 5 ondata 2) + multiple sub-WP. | Apply Rule 13 two-step at Wave closure, not after the fact. |
| Wave 5 ondata 1+2+3 declared Surface 10 green based on sub-editor sub-tabs. | Wave 6 full-layer audit + Wave 7 closure. | Decompose Surface 10 into 10A-F at the start. |
| Wave 6 full-layer audit was triggered only after product owner found gaps a vista. | Slow loop. | Schedule scope-broad audit on admin layer at every Wave touching admin, do not wait for product to find. |
| BOXE create variant failed in backend silently before Wave 7. | Wave 7 detected during parallel audit and fixed. | End-to-end gate at closure (admin → backend persist → runtime consume). |
| BOXE uploaded board symbols were not consumed at runtime. | Wave 7 closure fix. | Closure gate must include "uploaded asset visible in game". |
| BOXE admin theme saved skin in wrong payload shape. | Wave 7 closure fix. | Backend persistence schema must be validated in admin closure gate. |
| Admin RBAC used engine-name alias instead of canonical area. | Wave 7 canonicalization. | Canonicalize at third-engine point. |

## What HI-LO Should Skip Entirely

These BOXE-specific costs do not apply to HI-LO if this brief is followed:

- Multiple "Surface 10 green declared then reverted" cycles.
- One-shot audits that miss admin engine page.
- Test-drift fixes that don't notice broken backend payload.
- Asset upload that doesn't bind to runtime.

## Cross-Reference

- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` — generic Playbook v2, includes
  Wave Lessons in section 13.2.
- `docs/games/boxe/WAVE7_BACKOFFICE_FULL_CLOSURE_PLAN_2026-05-22.md` — the
  Wave 7 plan and live log that produced this brief.
- `docs/games/boxe/BACKOFFICE_FULL_LAYER_AUDIT_STEP1_2026-05-22.md` +
  `BACKOFFICE_FULL_LAYER_AUDIT_STEP2_VERIFIER_2026-05-22.md` +
  `BACKOFFICE_AUDIT_ROOT_CAUSE_2026-05-22.md` — the Wave 6 audit that
  required Wave 7.
- `docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md` — navigable code map
  required to stay current.
- Memory feedback files (CTO Claude): `feedback_audit_scope_breadth_critical`,
  `feedback_two_step_audit_verifier`, `feedback_content_vs_container_parity`,
  `feedback_capability_check_at_every_wave`.

## Closure

The next game should not produce a Wave 7 of its own. If it does, this brief
or the Playbook is missing a rule. Add the rule at that point.
