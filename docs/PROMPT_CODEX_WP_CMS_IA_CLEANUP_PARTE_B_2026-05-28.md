Status: ACTIVE
Last meaningful update: 2026-05-28

# Prompt Codex - WP-SITE-V3-CMS-IA-CLEANUP (Parte B)

## Context delta

Site V3 admin CMS (`/admin/site-v3`) IA cleanup. The menu-driven restructure is
already in place but two later quick fixes re-introduced confusion: a "Mounted
modules" instance list in the left nav, and a standalone "Add module" wizard with
"template" wording that duplicates the in-Composition add picker.

Full contract: read `docs/SITE_V3_WP_CMS_IA_CLEANUP_BRIEF_2026-05-28.md`. It is
the source of truth for this WP. Locked decisions: single vocabulary `module`
(no "block"/"template"); light contextual split of the builder file; theme
tokens are a separate later WP (do NOT touch `frontend-v3` CSS here).

## Parte A — confirm before coding (short)

Reply with a one-paragraph confirmation or a counter-proposal on:
- the per-screen split boundaries in brief section A5;
- removing the standalone wizard (A2) vs only renaming it.
Do not start coding until this is acknowledged. If you fully agree, say so and proceed.

## Parte B — execute

Implement brief sections A1–A7 exactly. Keep git history in clean commits:

1. `refactor(site-v3): split admin builder into per-screen files` — A5 only,
   pure mechanical move, no behavior change, `npm run build` green.
2. `fix(site-v3): remove mounted-module nav list and fake hierarchy note` — A1, A3.
3. `refactor(site-v3): drop redundant add-module wizard, single add path` — A2.
4. `style(site-v3): align cms copy to single module vocabulary` — A4.
5. `test(site-v3): lock cms ia contract` — A6.
6. `docs(site-v3): update manual, roadmap, loops after ia cleanup` — A7.

## Hard constraints

- No backend / API / public renderer (`frontend-v3`) change. Admin-only.
- No new module types; the 7 MVP descriptors are unchanged.
- No vocabulary "block"/"section"; delete "template".
- `npm run build` in `frontend/` passes after each commit.
- `:3000/admin/site-v3` loads; `:3001` unchanged.

## Delivery report (mandatory, explicit)

State for each: branch name, commits, whether merged to main or still on branch,
and whether the change is visible on `localhost:3000`. No ambiguous "done".
End with the WP-A gate checklist from brief section 4, each item pass/fail.
Michele runs the final walkthrough on `:3000`; do not declare green yourself.
