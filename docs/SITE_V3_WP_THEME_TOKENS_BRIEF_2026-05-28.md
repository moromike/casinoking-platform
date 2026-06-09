Status: ACTIVE
Last meaningful update: 2026-05-28

# Site V3 - WP-B Theme Tokens Brief

This brief records the closed scope for `WP-SITE-V3-THEME-TOKENS`.

## Goal

Give the public Site V3 renderer one obvious restyle surface. Future visual
changes to background, colours, borders, radii, shadows and font family should
start from the token block in `frontend-v3/app/globals.css`, not from scattered
hardcoded CSS values.

## Scope

- Add a single public theme token block at the top of
  `frontend-v3/app/globals.css`.
- Keep the existing layout tokens:
  `--site-v3-content-width`, `--site-v3-module-gap`,
  `--site-v3-page-gutter`.
- Add visual tokens for:
  `--font-sans`, `--bg`, `--bg-gradient`, `--surface`,
  `--surface-raised`, text colours, accent/primary colours, borders, radii,
  shadows and module-specific overlays.
- Replace the matching hardcoded values in the rest of `globals.css` with
  `var(...)`.

## Non-goals

- No public renderer component changes.
- No backend/API/admin/V1 changes.
- No visual redesign.
- No new CMS capability.
- No asset workflow change.

## Gate

- `npm run lint` in `frontend-v3/` passes.
- `npm run build` in `frontend-v3/` passes.
- `frontend-v3/app/globals.css` has no hardcoded colours or gradients outside
  the `:root` token block.
- Public renderer still loads on `:3001`.

## Operator Note

The token block is not an admin UI yet. It is the developer/operator handoff for
a later visual restyle WP: edit the variables first, then verify the renderer.
