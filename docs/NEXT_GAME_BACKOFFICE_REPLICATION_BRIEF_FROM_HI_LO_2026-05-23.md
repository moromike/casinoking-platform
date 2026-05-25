Status: ACTIVE
Last meaningful update: 2026-05-24

# Next Game Backoffice Replication Brief - From HI-LO Lessons (2026-05-23)

This document is the backoffice-specific handoff from HI-LO. It complements the
BOXE backoffice brief. BOXE taught what goes wrong; HI-LO proved the better
sequence: build Surface 10A-F upfront instead of rescuing it later.

## 1. Surface 10 Is Six Surfaces

Do not use "Backoffice green" as a single statement. Track these:

| Sub-surface | Required result |
| --- | --- |
| 10A Admin engine page | `/admin/games/<engine>` uses the shared master/variant page with editable titles, filters, create variant, inline save/preview/archive and lobby toggles. |
| 10B Title detail shell | `/admin/games/<engine>/titles/<title_code>` mounts shared command bar, status banner, tab frame and validation display. |
| 10C Tab existence | Overview, copy i18n, rules HTML, gameplay config, assets, sounds, theme and validation, unless a product doc justifies a game-specific exception. |
| 10D Field depth | Every reference field has a game-specific equivalent: copy/rules depth, config, assets, theme, advanced skin, sounds and validation. |
| 10E Workflow | Dirty state, save draft, publish live, locale/rules persistence and runtime consume are tested end-to-end. |
| 10F Adjacent pages | Asset library, copy preview, finance/replay links, readable finance detail and canonical admin access work for the game. |

A single red sub-surface keeps Surface 10 non-green.

## 2. HI-LO Pattern To Reuse

For the next game, start from the HI-LO H5 shape:

| Pattern | Reuse rule |
| --- | --- |
| Shared engine page | Do not create a local "Other engines" list. Register the game so `/admin/games/<engine>` uses the platform page. |
| Title editor shell | Consume `TitleEditorCommandBar`, `TitleEditorStatusBanner`, `TitleEditorTabFrame`, `TitleEditorValidationDisplay`. |
| Copy/rules | Define a full manifest and rich rules HTML in all supported locales before declaring content green. |
| Config | Use a game-specific config descriptor, not a Mines-shaped grid clone. |
| Assets | Include lobby card, title logo, runtime background, game symbols/cards and any game-specific textures. |
| Sounds | Use the shared sounds tab and the existing sound kind pattern. |
| Theme | Include title presentation, advanced skin, background and runtime-consumed tokens. |
| Validation | Validate required keys, lengths, formats and game-specific config consistency. |

## 3. Gate Sequence

Run this in order:

1. Engine page screenshot side-by-side vs Mines/HI-LO reference.
2. Title detail shell screenshot side-by-side.
3. Tab inventory screenshot.
4. Field-depth checklist per tab.
5. Save draft after each tab mutation; dirty state must activate.
6. Publish live.
7. Open player runtime and prove saved copy/assets/theme/sounds are consumed.
8. Open account/admin finance detail and replay. The round must be explained in
   finance terms, not only rendered as raw IDs.
9. Product owner walkthrough on `localhost:3000/admin`.

Do not replace step 9 with automated tests. Tests are necessary but not enough.

## 3.1 Visual Quality Minimum

Backoffice quality is not a cosmetic afterthought. Before a game admin surface
is called green, open the engine page and every title-detail tab and check:

- labels are not clipped;
- field text is centered/aligned inside its container;
- asset rows have stable preview, copy and action columns;
- theme/token/skin sections follow the reference hierarchy instead of ad hoc
  panels;
- `Save draft` activates after each supported edit.

If any of these fail, the surface is partial even when persistence and tests
pass.

## 4. What HI-LO Improved Over BOXE

| BOXE failure mode | HI-LO prevention |
| --- | --- |
| Admin engine page was missed by audits. | H5 started from 10A engine page, not only title-detail tabs. |
| Container green was mistaken for content green. | HI-LO shipped copy/rules/config/assets/theme/sound content with the container. |
| Runtime consume was discovered late. | HI-LO runtime config consumes published presentation config. |
| Backoffice got visually/functionally checked after product escalation. | HI-LO tracked PO walkthrough as pending instead of falsely marking final green. |
| Replay was placed on the live game table as a CTA. | Future games keep replay in the info/rules modal Replay tab unless product explicitly approves otherwise. |
| A game-specific close button inherited global hover movement and jumped visually. | Future games consume shared stage/header chrome or explicitly lock hover transforms when local positioning is absolute. |

## 5. Game-Specific Exceptions

Game-specific exceptions are allowed only when documented in SPEC/MATH_SPEC or a
product decision. Examples:

| Reference concept | New-game equivalent |
| --- | --- |
| Mines grid/mines matrix | New game's own gameplay configuration matrix. |
| Mines symbol_safe/symbol_mine | New game's card/symbol/stage assets. |
| Mines payout/rules copy | New game's payout/rules copy with equal richness, not equal words. |

If no document justifies the difference, classify it as a gap.

## 6. Platform Cleanup Before Game 4

HI-LO still required explicit additions in account history and admin finance
replay. For game 4, the backoffice/player reporting layer must expose a
registry. Read `docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md`
before implementation.

| Adapter | Responsibility |
| --- | --- |
| Account history adapter | Fetch sessions, label game, summarize round and open replay. |
| Admin finance replay adapter | Load admin replay payload and choose viewer. |
| Admin finance detail adapter | Explain the round/session in product language: config, actions, outcome, payout and fairness handle. |
| Title editor adapter | Provide tab descriptors, config schema and runtime config mapper. |

Do this before adding a fourth game's branches. A fourth `if game_code === ...`
in admin finance or account history is a platform regression.

## 7. Completion Definition

Surface 10 is green only when:

- all six sub-surfaces are green;
- the eight-layer table is green, including product owner;
- saved admin changes are visible in runtime;
- no game-specific exception is uncited;
- screenshots cover engine page, detail shell and every tab.

Anything less is green-major or partial, not final green.
