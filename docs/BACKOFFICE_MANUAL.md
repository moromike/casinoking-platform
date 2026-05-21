Status: ACTIVE
Last meaningful update: 2026-05-17

# CasinoKing Backoffice Manual

Last updated: 2026-05-21, based on Title Editor shared tab frame B1, BOXE 4B/5/6 completion, and Wave 4 BO parity.

Audience: single CasinoKing operator. This manual explains what to do in the backoffice, where each workflow lives, and what player-facing effect to expect.

Out of scope: player help, game rules for players, financial architecture, RNG/fairness design, payout math, and implementation internals.

Use path references such as `Backoffice -> Games -> Mines -> Title detail -> Theme tab`. No screenshots are required to follow this document.

## 1. Overview

### What The Backoffice Is

The CasinoKing backoffice is the operator surface for:

- game catalog management;
- Mines and BOXE Title configuration;
- player lobby publication;
- homepage slots;
- finance reporting;
- player administration;
- admin management;
- operational audit review.

The backoffice is not the player site.

The player site is where players see:

- the lobby;
- published game cards;
- Launch Cashier;
- the Mines and BOXE runtimes;
- player account pages.

Backoffice changes affect the player site only after the correct save and publish step.

### Login

Use `Backoffice -> Login`.

The login form expects:

- admin email;
- admin password.

If credentials are invalid, the form must show an error message.

There is no player registration inside the backoffice.

Player login, player registration, and player account are separate player-facing flows.

### Main Navigation

After login, the visible menu depends on the admin account permissions.

The usual areas are:

- `Finance`;
- `Player admin`;
- `Games`;
- `Site`;
- `LOG`;
- `My Space`;
- `Administrators`.

If one area is missing, the signed-in admin probably does not have that permission.

Do not treat a missing menu item as deleted functionality until permissions are checked.

### Draft Versus Live

Several backoffice areas use a draft/live model.

Draft means:

- editable state;
- safe to prepare;
- not necessarily visible to players;
- can be saved without runtime effect.

Live means:

- published state;
- consumed by player runtime or player lobby;
- visible to users where the Title is also published and launchable.

The key distinction:

- `Save draft` stores the operator work.
- `Publish live` changes what players can see or use.

Never use `Publish live` as a normal save button.

### Where Things Live

Game configuration lives in:

`Backoffice -> Games -> Mines -> Title detail`

Lobby visibility lives in:

`Backoffice -> Site -> Lobby publication`

Homepage editorial slots live in:

`Backoffice -> Site -> Homepage slots`

Finance reporting lives in:

`Backoffice -> Finance`

Player operations live in:

`Backoffice -> Player admin`

Admin account management lives in:

`Backoffice -> Administrators`

Audit review lives in:

`Backoffice -> LOG`

### Engine, Master, Variant, Title

CasinoKing games use a catalog model.

An Engine is the technical game family.

Example:

- `mines`

A Master Title is the stable source Title for a game engine.

Example:

- `mines_classic`

A Variant is an editable Title created from the master.

A Title code is the stable technical identifier for one Title.

The Title code should be:

- lowercase;
- stable;
- short enough to recognize;
- not reused after production launch.

The display name is the operator/player label.

### What To Preview

Preview before publishing:

- game copy;
- rules;
- grid and mine configuration;
- assets;
- sounds;
- theme;
- lobby card;
- Launch Cashier behavior;
- player lobby visibility.

Preview is not publication.

## 2. Games

### Path

Use:

`Backoffice -> Games`

Then open:

`Backoffice -> Games -> Mines`

### What The Games Area Controls

The Games area controls the game catalog and Title detail entry points.

It does not directly edit homepage placement.

It does not directly edit lobby order.

It does not change wallet, ledger, RNG, payout, or settlement logic.

### Games List

The Games list shows the available game engines and Titles.

For Mines, the list includes:

- the master Title;
- editable variants;
- title code;
- display name;
- status badges;
- lobby status;
- preview action;
- detail action;
- save action for inline name edits;
- archive or restore action where available.

### Filters

Use the filters above the variant list.

`Active` shows active, non-archived variants.

`Inactive` shows inactive, non-archived variants.

`Archived` shows variants that were archived.

`All` shows every variant in the category.

`Test only` narrows the current list to Titles marked as test-only.

Use `Archived` when a Title seems to have disappeared from the editable list.

Use `All` when you need to confirm whether a Title is active, inactive, archived, or test-only.

Use `Test only` when working on temporary variants that should not be confused with release candidates.

### Master Title

The master Title is not the normal editing target.

Use the master Title to create variants.

Do not treat the master as a production variant.

Previewing the master is allowed, but operational edits should happen on variants.

### Create Variant

Path:

`Backoffice -> Games -> Mines`

Steps:

1. Choose a Title code.
2. Enter the display name.
3. Set `Test only` when the variant is experimental.
4. Use `Create variant`.
5. Open the new Title detail.
6. Configure it before making it visible in Site/Lobby.

Title code guidance:

- use lowercase;
- avoid spaces;
- avoid punctuation;
- use a stable name;
- do not encode temporary notes in the code.

The UI normalizes or rejects unsupported title-code characters.

### Inline Name Editing

The Games list can show editable display-name fields.

Use them for small label changes.

After changing a name, use the row `Save` action.

If the name affects player-facing presentation, also check Site/Lobby and player preview.

### Open Detail

Use `Open detail` to enter the Title editor.

Path:

`Backoffice -> Games -> Mines -> Open detail`

The detail page contains:

- header;
- fairness diagnostics;
- command bar;
- editor status;
- tabs;
- preview;
- archive/restore where applicable.

### Preview

Use `Preview` to inspect a Title as a game launch.

Preview can use an admin preview path.

Preview does not publish the Title.

Preview does not make a hidden Title visible to players.

### Archive

Archive is a mutating operation.

Use it when a variant should no longer be available through player launch surfaces.

Archive keeps historical data.

Archive does not delete finance history.

Archive does not change ledger records.

Archive does not change game math.

### Restore

Restore brings an archived Title back into the editable catalog.

Restore does not automatically publish it to the lobby.

After restore, check:

- Title status;
- live configuration;
- Site/Lobby visibility;
- demo and real availability;
- player preview.

## 3. Title Editor

### Path

Use:

`Backoffice -> Games -> Mines -> Title detail`

### Header

The header identifies the Title.

It shows:

- back to list;
- display name;
- title code;
- variant/master badge;
- engine;
- preview;
- archive/restore where available.

Use the header to confirm you are editing the intended Title before saving or publishing.

### Fairness Diagnostics

Path:

`Backoffice -> Games -> Mines -> Title detail -> Fairness diagnostics`

Fairness diagnostics are read-only.

They are for inspection.

They do not edit RNG.

They do not edit seed handling.

They do not edit payouts.

They do not edit settlement.

### Command Bar

Path:

`Backoffice -> Games -> Mines -> Title detail -> Command bar`

Actions:

- `Load saved draft`;
- `Load published live`;
- `Save draft`;
- `Publish live`.

Use `Load saved draft` when you want the last saved editable state.

Use `Load published live` when you want to compare against what players currently receive.

Use `Save draft` before leaving the editor.

Use `Publish live` only after review.

### Busy States

The command bar and editor status can show busy states.

Examples:

- loading draft;
- loading live;
- saving draft;
- publishing live.

Wait for the busy state to finish before taking the next action.

Do not click multiple publish actions while a previous request is still running.

### Editor Status

The editor status summarizes the current state.

Common meanings:

- published;
- draft ready;
- unsaved changes;
- loading;
- saving;
- blocked by validation;
- error.

Read the status before publishing.

If the status says there are unsaved changes, save the draft before publishing.

Mines and BOXE now use the same Title Editor status banner and tab navigation
frame. This is an operator workflow alignment only: the save and publish
endpoints remain engine-specific.

### 3.1 Overview Tab

Path:

`Backoffice -> Games -> Mines -> Title detail -> Overview tab`

Use Overview for a quick sanity check.

It summarizes the current Title state.

Check Overview before publishing if you changed several tabs.

Overview is useful after loading live because it gives quick confirmation that the editor has reloaded the intended state.

Mines keeps its runtime, draft, live and fairness summary. BOXE uses the same
Overview frame for rows and difficulty summary.

### 3.2 Copy & i18n Tab

Path:

`Backoffice -> Games -> Mines -> Title detail -> Copy i18n tab`

This tab edits player-facing Mines copy.

It does not translate the backoffice.

It affects text inside the game runtime.

Typical fields include:

- action labels;
- loading labels;
- balance labels;
- rules labels;
- runtime errors;
- Launch Cashier copy;
- board aria labels.

Keep copy short.

Respect max-length hints.

Do not paste legal terms, marketing paragraphs, or large help text into short runtime labels.

After editing:

1. Save draft.
2. Preview.
3. Publish live only after review.

### 3.3 Rules HTML Tab

Path:

`Backoffice -> Games -> Mines -> Title detail -> Rules HTML tab`

This tab edits the content shown in the game rules modal.

Use it for:

- how to win;
- payout explanation;
- settings menu explanation;
- bet and collect explanation;
- balance display explanation;
- general notes;
- history notes.

Keep HTML simple.

Do not paste:

- scripts;
- external widgets;
- tracking pixels;
- iframe embeds;
- heavy layout markup;
- unrelated promotional content.

Rules are player-facing.

Preview after editing.

### 3.4 Grid & Mines Config Tab

Path:

`Backoffice -> Games -> Mines -> Title detail -> Grid & Mines tab`

This tab controls which grid sizes and mine counts are available for the Title.

It can configure:

- published grid sizes;
- supported mine counts per grid;
- default mine count per grid;
- draft/live state.

Use this tab carefully.

Changing grid or mine options changes what players can select.

It does not change payout math directly.

The runtime uses configured options together with existing payout ladders.

Before publishing:

1. Confirm each enabled grid has at least one valid mine count.
2. Confirm the default mine count is enabled.
3. Preview the Title.
4. Start a demo hand if needed.

### 3.4A BOXE Configuration

Path:

`Backoffice -> Games -> BOXE -> Title detail`

BOXE uses the same Title Editor draft/live workflow as Mines, with
BOXE-specific engine tabs.

The BOXE editor contains:

- Overview;
- Copy i18n;
- Rules HTML;
- Rows & difficulty.
- Assets;
- Sounds;
- Theme.

The Rows & difficulty tab controls which player settings are available for the
Title:

- enabled rows, subset of `4, 5, 6, 7, 8`;
- default row, which must be one of the enabled rows;
- enabled difficulties, subset of `easy, medium, hard`;
- default difficulty, which must be one of the enabled difficulties.

The Copy i18n tab edits the required BOXE copy keys for `it`, `en`, `de`, and
`es`. It exposes the expanded BOXE frontend copy catalog, including runtime
actions, audio labels, how-to-play copy, rules/info headings, launch cashier
copy, runtime recovery copy, errors, board labels, and demo/real UI labels.
All required keys must be present before saving or publishing.

BOXE runtime action labels live in the copy manifest. This includes:

- Bet;
- Bet loading;
- Collect;
- Collect loading;
- Home / back to site aria label;
- Fullscreen;
- Game info.

Do not add a BOXE legacy-labels editor. BOXE uses the modern copy manifest path
from day one.

The Rules HTML tab edits the player-facing rules text for each locale. It
mirrors the multi-section Mines pattern with BOXE-specific content:

- Bet / Pick / Collect rules;
- Multiplier ladder display;
- Payout rules;
- Fairness / RTP explain;
- Board mechanics;
- Difficulty semantics;
- Max win cap.

Keep markup simple and player-focused. The backend sanitizes rules before
storing them.

Workflow:

1. Load the draft for the Title.
2. Edit rows, difficulty, copy, or rules.
3. Save draft.
4. Publish live after review.

Validation errors are shown inline and block save/publish.
For BOXE, validation errors appear in the shared validation panel and still
block save/publish until rows, difficulty, copy and rules are valid.

Publishing live affects future BOXE rounds only. Active rounds keep the config
snapshot stored when the round started.

### 3.4B BOXE Assets And Theme

Path:

`Backoffice -> Games -> BOXE -> Title detail`

BOXE uses the shared Title asset registry and shared Theme draft/live flow.

Asset kind decision:

- Lobby card uses `game_card`.
- Safe symbol uses `symbol_safe`.
- Mine symbol uses `symbol_mine`.
- Sounds use the same `audio_safe_reveal`, `audio_mine_hit`, `audio_collect`,
  and `audio_win` asset kinds as Mines.

Use the BOXE Assets tab for:

- uploading the lobby card;
- uploading the safe symbol;
- uploading the mine symbol;
- previewing active assets;
- deleting an active asset.

Upload guidance:

| Asset | Formats | Limit | Recommended dimensions | Render mode |
| --- | --- | --- | --- | --- |
| Lobby card | PNG, JPEG, WebP | 300 KB | 512 x 512 square | Cover, centered |
| Safe symbol | PNG, SVG | 150 KB operator limit | 256 x 256 transparent | Contain |
| Mine symbol | PNG, SVG | 150 KB operator limit | 256 x 256 transparent | Contain |

The shared backend registry has a wider technical cap for board symbols, but the
operator guidance for BOXE is 150 KB to keep runtime loading light.

The BOXE Theme tab controls the same shared token allowlist used by Mines:

- color tokens;
- radius and shadow tokens;
- font family;
- shared skin options where available.

Workflow:

1. Open the BOXE Title detail.
2. Upload assets in the Assets tab.
3. Use the Theme tab `Load theme`.
4. Edit tokens or apply a preset.
5. Save draft.
6. Publish live.
7. Open player lobby and `/boxe?title_code=boxe001&mode=demo` to verify.

Uploading assets or changing theme does not alter wallet, ledger, payout, RNG,
fairness, or round settlement.

Use the BOXE Sounds tab for short runtime audio assets. It inherits the Mines
sound workflow 1:1:

- upload, preview, and remove safe reveal sound;
- upload, preview, and remove mine hit sound;
- upload, preview, and remove collect sound;
- upload, preview, and remove win sound.

Accepted formats are MP3, OGG, WAV, or WebM, max 1 MB each. Audio has no pixel
dimensions. Missing sounds degrade silently; they do not block gameplay.

### 3.5 Board Assets Tab

Path:

`Backoffice -> Games -> Mines -> Title detail -> Lobby card / Assets tab -> Board assets section`

Board assets manage runtime symbols.

Typical assets:

- safe reveal icon;
- mine hit icon.

Asset uploads go through the Title asset registry.

Upload limits: SVG or PNG only, max 150 KB each, 256 x 256 px square art recommended. Icons are rendered contained inside the cell, with no crop and no stretch.

Uploading a symbol does not alter RNG.

Uploading a symbol does not alter board generation.

Uploading a symbol does not alter payout.

After uploading:

1. Check the local draft state.
2. Save draft if the editor reports unsaved changes.
3. Preview the game.
4. Publish live when approved.

### 3.6 Sounds Tab

Path:

`Backoffice -> Games -> Mines -> Title detail -> Sounds tab`

Sounds manage short runtime audio assets.

Typical sound kinds:

- safe reveal;
- mine hit;
- collect;
- win.

Upload limits: MP3, OGG, WAV, or WebM audio, max 1 MB each. Audio has no pixel dimensions. Use very short sounds.

Missing sounds should degrade silently.

Do not use long music tracks here.

Do not use files that would delay runtime loading.

### 3.7 Theme Tab

Path:

`Backoffice -> Games -> Mines -> Title detail -> Theme tab`

The Theme tab controls runtime visual styling.

Theme state has its own flow:

- `Load theme`;
- `Save draft`;
- `Publish live`.

When the theme is not loaded, the tab shows only a compact empty state.

No editable fallback controls are available until the theme is loaded.

Theme fields include color tokens:

- `--ck-bg`;
- `--ck-surface`;
- `--ck-surface-strong`;
- `--ck-fg`;
- `--ck-muted`;
- `--ck-accent`;
- `--ck-accent-strong`;
- `--ck-good`;
- `--ck-danger`.

Theme fields include text tokens:

- `--ck-border`;
- `--ck-radius-panel`;
- `--ck-radius-cell`;
- `--ck-shadow-panel`;
- `--ck-font-family`.

Advanced skin fields include:

- title render mode;
- button density;
- button radius;
- button style;
- button emphasis;
- game area background fit;
- game area background position;
- game area overlay;
- closed cell background dominance.

Skin assets include:

- title logo;
- game area background;
- closed cell texture.

Upload limits: `title_logo` PNG/WebP max 150 KB, recommended 720 x 180 px, rendered contained with no crop or stretch; `game_area_background` PNG/WebP max 400 KB, recommended 1280 x 720 px, rendered with the selected Cover/Contain behavior; `cell_face_down_background` PNG/WebP max 256 KB, recommended 256 x 256 px, rendered cover inside each cell with possible edge crop.

Use `Title logo` when the title should render from an uploaded image.

Use `Game area background` for board-area background art.

Use `Closed cell texture` for covered cells.

#### Theme Example: Vivid Neon

Use this skin when the Title should feel colorful, high-energy, and arcade-like.

It works best for promotional variants and demo-heavy lobby tests.

Avoid it if the card art is already visually crowded.

Token JSON:

```json
{
  "tokens": {
    "--ck-bg": "#070014",
    "--ck-surface": "#151033",
    "--ck-surface-strong": "#2b1f78",
    "--ck-fg": "#f7fbff",
    "--ck-muted": "#c7b8ff",
    "--ck-accent": "#3df5ff",
    "--ck-accent-strong": "#ff4fd8",
    "--ck-good": "#6dff7a",
    "--ck-danger": "#ffb84d",
    "--ck-border": "rgba(61, 245, 255, 0.28)",
    "--ck-radius-panel": "22px",
    "--ck-radius-cell": "18px",
    "--ck-shadow-panel": "0 22px 44px rgba(61, 245, 255, 0.20)",
    "--ck-font-family": "inherit"
  },
  "skin": {
    "title_render_mode": "text",
    "button_density": "default",
    "button_radius": "rounded",
    "button_style": "raised",
    "button_emphasis": "primary",
    "game_area_background_fit": "cover",
    "game_area_background_position": "center",
    "game_area_overlay": "medium",
    "closed_cell_background_dominance": "balanced"
  }
}
```

Step-by-step:

1. Open `Backoffice -> Games -> Mines -> Title detail -> Theme tab`.
2. Use `Load theme`.
3. Copy each value from `tokens` into the matching theme field.
4. Set the advanced skin fields from the `skin` block.
5. Upload skin assets only if the variant already has approved art.
6. Use `Save draft`.
7. Preview the Title.
8. Use `Publish live` only after the preview is accepted.

#### Theme Example: Minimal Dark

Use this skin when the Title should feel restrained, readable, and workmanlike.

It works well for production review, finance-sensitive testing, and variants where clarity matters more than spectacle.

It is also a good fallback when custom assets are not ready.

Token JSON:

```json
{
  "tokens": {
    "--ck-bg": "#07090f",
    "--ck-surface": "#111722",
    "--ck-surface-strong": "#1b2433",
    "--ck-fg": "#f5f7fb",
    "--ck-muted": "#aeb8c7",
    "--ck-accent": "#8fd0ff",
    "--ck-accent-strong": "#c4e6ff",
    "--ck-good": "#73d99f",
    "--ck-danger": "#f28b82",
    "--ck-border": "rgba(174, 184, 199, 0.18)",
    "--ck-radius-panel": "14px",
    "--ck-radius-cell": "10px",
    "--ck-shadow-panel": "0 18px 34px rgba(0, 0, 0, 0.38)",
    "--ck-font-family": "inherit"
  },
  "skin": {
    "title_render_mode": "text",
    "button_density": "compact",
    "button_radius": "soft",
    "button_style": "outlined",
    "button_emphasis": "neutral",
    "game_area_background_fit": "cover",
    "game_area_background_position": "center",
    "game_area_overlay": "light",
    "closed_cell_background_dominance": "solid"
  }
}
```

Step-by-step:

1. Open `Backoffice -> Games -> Mines -> Title detail -> Theme tab`.
2. Use `Load theme`.
3. Copy each value from `tokens` into the matching theme field.
4. Set the advanced skin fields from the `skin` block.
5. Leave skin assets empty unless the variant needs branded art.
6. Use `Save draft`.
7. Preview desktop and mobile.
8. Publish live only when readability is confirmed.

### 3.8 Lobby Card / Assets Tab

Path:

`Backoffice -> Games -> Mines -> Title detail -> Lobby card / Assets tab`

This tab manages the Title assets that are not Site/Homepage media.

The main lobby-specific asset is:

- lobby game card image.

The lobby game card appears in the player lobby.

Upload limits: PNG, JPEG, or WebP, max 300 KB, square required, 512 x 512 px recommended. The card renders as centered cover in a square area; it is not stretched.

If no game card is uploaded, the player lobby uses fallback game art.

Use this tab for:

- uploading the lobby card;
- removing the lobby card;
- previewing the uploaded card;
- opening board assets from the same detail surface.

Do not upload lobby card images in Site/Lobby.

Site/Lobby controls visibility and order.

Title detail controls the game card asset.

After uploading the card:

1. Confirm the preview is correct.
2. Check `Backoffice -> Site -> Lobby publication`.
3. Make sure the Title is visible if it should appear.
4. Open the player lobby.
5. Confirm the card image renders.

## 4. Site / Lobby

### Path

Use:

`Backoffice -> Site`

The Site area is split into:

- Homepage slots;
- Lobby publication.

### What Site / Lobby Controls

Site/Lobby controls player-site presentation.

It does not edit game mechanics.

It does not edit Mines grid configuration or BOXE rows/difficulty.

It does not upload game card assets.

It does not change payouts.

### Homepage Slots

Path:

`Backoffice -> Site -> Homepage slots`

Homepage slots are editorial surfaces on the player homepage.

Operators can:

- upload homepage banner media;
- create a slot;
- edit title;
- edit subtitle;
- edit CTA label;
- choose CTA target;
- set status;
- set schedule;
- set sort order;
- save the slot.

The homepage media asset kind is separate from Title assets.

Use homepage media only for homepage slots.

Upload limits: PNG, JPEG, or WebP, max 2 MB, 1280 x 720 px / 16:9 recommended. The player homepage renders it as centered cover, so edges can be cropped on some viewport sizes; it is not stretched.

To publish a new homepage banner:

1. Upload the image in `Backoffice -> Site -> Homepage slots -> Banner media`.
2. Confirm it appears in the media list.
3. In `New slot`, set a unique `Slot key`, for example `homepage-hero`.
4. Enter `Title` and optional `Subtitle`.
5. Choose the CTA behavior: `None`, `Title demo`, or `Title real`.
6. If the CTA targets a Title, select the `Target ref`.
7. Select the uploaded image in `Banner image`.
8. Set `Sort order`; lower numbers appear first.
9. Set `Status` to `Published` if it should be visible now, or `Draft` if it is only being prepared.
10. Use `Starts at` and `Ends at` only when the banner needs a visibility window.
11. Use `Create slot`.
12. Check the player homepage. A published slot appears only when it is published, inside its optional schedule window, and has a valid target if a CTA is configured.

### Homepage Slot CTA

CTA target types include:

- no target;
- demo Title target;
- real Title target.

On the player site, a valid game CTA opens the Launch Cashier for that Title.

The player then chooses:

- Real money;
- Bonus;
- Demo.

The CTA does not directly mutate a wallet.

### Lobby Publication

Path:

`Backoffice -> Site -> Lobby publication`

Lobby publication controls which Titles appear in the player game library.

For each Title, operators can set:

- visible or hidden;
- order;
- demo enabled;
- real enabled;
- featured;
- lobby title;
- lobby description.

Visible lobby and configured game state are separate.

A Title can have a good live game configuration and still be hidden from the lobby.

A Title can be visible in the lobby but still fail player expectations if launch modes are disabled.

Check both Games and Site/Lobby before release.

### Lobby Preview

The Site/Lobby preview shows compact player lobby cards.

Use it to check:

- order;
- visibility;
- labels;
- demo/real flags;
- featured state.

It is not a replacement for opening the actual player lobby.

After major changes, also check the player site.

## 5. Finance

### Path

Use:

`Backoffice -> Finance`

### What Finance Controls

Finance is primarily for reporting and inspection.

Some player operations may be available if the admin has finance permission.

Round drilldown is read-only.

Do not expect Finance reports to be correction tools.

### Dashboard

The Finance dashboard can show:

- financial sessions;
- player;
- wallet;
- transaction type;
- date filters;
- min and max bank delta;
- rows per page;
- page totals;
- global totals when available.

Use filters to reduce the report before opening details.

### Round Drilldown

Path:

`Backoffice -> Finance -> Round detail`

Use `Round detail` to inspect wallet and ledger movement detail for a round/session.

Round drilldown is read-only.

It must not:

- mutate ledger events;
- mutate round data;
- change payout;
- change settlement;
- change reconciliation;
- create adjustments.

Use the drilldown to collect IDs and context.

If a correction is needed, it requires a dedicated approved finance workflow.

### Player Drill-In

Some finance rows allow opening the related player profile.

Use this when the finance report needs context from:

- player identity;
- wallet balances;
- player status;
- access logs;
- active sessions.

## 6. Admin Management

### Player Admin

Path:

`Backoffice -> Player admin`

Player admin can include:

- player search;
- player profile;
- password reset;
- wallet balance inspection;
- finance sessions for the player;
- player access logs;
- suspend account;
- bonus operations when permitted;
- wallet adjustments when permitted;
- force-close active sessions when permitted.

Treat player operations as sensitive.

Financial actions require a reason.

Write reasons as operational audit text.

Do not put private notes into reason fields.

### Access Log

Path:

`Backoffice -> LOG` or access log panels inside admin/player areas.

Access logs are read-only.

Use them to review:

- login events;
- role;
- email;
- date/time;
- operational context.

Access logs are not rollback tools.

### LOG

Path:

`Backoffice -> LOG`

LOG is the operational audit surface.

It can include events such as:

- Title changes;
- config publishing;
- theme publishing;
- asset operations;
- lobby publication;
- admin operations.

LOG is not the financial ledger.

Financial accounting remains in ledger and finance reports.

### My Space

Path:

`Backoffice -> My Space`

Use My Space for the currently signed-in admin.

Typical actions:

- inspect current admin account;
- change current admin password.

Do not use My Space to manage other admins.

### Administrators

Path:

`Backoffice -> Administrators`

This area is for superadmin-level admin management.

Tabs:

- Registered admins;
- Create admin;
- Admin accesses.

Registered admins is for searching and inspecting existing admin accounts.

Create admin is for creating another admin and assigning access areas.

Admin accesses is for admin access logs.

Keep permissions narrow.

Give only the areas the admin needs.

### Local Admin Bootstrap

Local admin bootstrap is a local development support flow.

It is not player registration.

It is not a production onboarding workflow.

Use it only to recover or prepare a local admin account according to the local environment rules.

If a known local admin stops working:

1. Confirm the environment is local.
2. Confirm the backend is running.
3. Check login error messages.
4. Check bootstrap output or backend logs.
5. Do not assume the password was changed by the UI.

## 7. Player Preview

### Purpose

Player Preview means checking what the player sees after backoffice changes.

Use it after changes in:

- Title config;
- copy;
- rules;
- assets;
- sounds;
- theme;
- lobby publication;
- homepage slots.

### Player Lobby Game Cards

Path:

`Player site -> Lobby`

Game cards come from the published game library.

The card can show:

- uploaded lobby card image;
- fallback game art;
- Title display name;
- engine label;
- featured state.

For Mines, the uploaded lobby card comes from:

`Backoffice -> Games -> Mines -> Title detail -> Lobby card / Assets tab`

For BOXE, the uploaded lobby card comes from:

`Backoffice -> Games -> BOXE -> Title detail -> Assets tab`

Lobby visibility comes from:

`Backoffice -> Site -> Lobby publication`

Both must be correct.

### Launch Cashier Flow

Launch Cashier is opened from:

- player lobby game card;
- homepage slot CTA when it targets a game.

The modal offers:

- Real money;
- Bonus;
- Demo.

Real money requires:

- player login;
- Title real mode enabled;
- wallet state available.

Bonus requires:

- player login;
- Title real mode enabled;
- bonus wallet available;
- bonus balance greater than zero.

Demo requires:

- Title demo mode enabled.

Launch Cashier reads wallet balances.

Launch Cashier does not mutate wallet or ledger.

For Mines, the actual game launch path passes:

- `title_code`;
- `mode=demo` for demo;
- `wallet_source=real` for real;
- `wallet_source=bonus` for bonus.

For BOXE, Launch Cashier routes are:

- demo: `/boxe?title_code=boxe001&mode=demo`;
- real cash: `/boxe?title_code=boxe001&mode=real_cash&wallet_source=real`;
- bonus: `/boxe?title_code=boxe001&mode=real_bonus&wallet_source=bonus`.

The selected game runtime handles table entry after launch.

### BOXE Site/Lobby Publication Workflow

Path:

`Backoffice -> Site -> Lobby publication`

BOXE catalog seed creates:

- master Title `boxe`, hidden and blocked from public launch;
- variant Title `boxe001`, hidden by default.

To publish BOXE:

1. Configure BOXE rows/difficulty/copy/rules in `Backoffice -> Games -> BOXE`.
2. Upload the BOXE lobby card and symbols.
3. Publish BOXE config and theme live if changed.
4. Open `Backoffice -> Site -> Lobby publication`.
5. Set `boxe001` to visible.
6. Enable demo and real if desired.
7. Set display name, description, featured flag and position.
8. Open the player lobby and verify the BOXE card.
9. Open Launch Cashier and verify demo, real cash and bonus routes.

Do not publish the master Title `boxe`. Master launch is rejected with
`LAUNCH_REJECTED_MASTER`.

### Mobile Viewport Behavior

Mines remains playable in normal portrait phone viewports, including iPhone SE
class 375 x 667 screens.

Very short landscape viewports are intentionally blocked by a rotation gate.
When the screen is too short for gameplay, the player sees `Rotate device to
play`. Rotating back to portrait, or to a taller landscape viewport, clears the
gate and restores the normal game surface.

This behavior protects gameplay readability. It does not change wallet,
ledger, RNG, payout, fairness, or math behavior.

### Theme Runtime

Theme changes affect the selected runtime after theme publish.

Player runtime can reflect:

- colors;
- panel radius;
- cell radius;
- shadow;
- font family;
- button style;
- title logo;
- game area background;
- closed cell texture.

If a theme change does not appear:

1. Confirm the theme was loaded before editing.
2. Confirm the theme draft was saved.
3. Confirm the theme was published live.
4. Refresh the player runtime.
5. Confirm you are launching the intended Title code.

### Config Runtime

Game config changes affect:

- grid choices;
- mine choices;
- default values;
- copy;
- rules.

If a config change does not appear:

1. Confirm the game config draft was saved.
2. Confirm the game config was published live.
3. Confirm Site/Lobby points to the same Title.
4. Refresh the player runtime.

### Public Versus Preview Launch

Admin Preview can launch a Title for inspection.

Public player launch follows:

- Title status;
- archive status;
- live config;
- Site/Lobby visibility;
- demo/real flags;
- player login state;
- Launch Cashier option chosen.

Do not assume Preview success means public launch is ready.

## 8. Operator Cheat Sheet

### Publish A Title Live

Path: `Backoffice -> Games -> Mines -> Title detail`.

Load or edit the draft, use `Save draft`, preview the game, then use `Publish live`.

After publishing, check player launch with the intended Title code.

### Archive A Title

Path: `Backoffice -> Games -> Mines`.

Find the variant, use `Archive`, confirm, then check `Archived` filter.

After archive, verify Site/Lobby no longer exposes the Title.

### Recover A Saved Draft

Path: `Backoffice -> Games -> Mines -> Title detail`.

Use `Load saved draft`.

Check editor status and fields before saving or publishing again.

### Hide A Title From Lobby

Path: `Backoffice -> Site -> Lobby publication`.

Set the Title to hidden and save the lobby publication row.

Check the player lobby after saving.

### Check A Finance Round

Path: `Backoffice -> Finance`.

Filter the report, find the row, open `Round detail`, collect IDs and movements.

Do not edit financial data from the drilldown.

### Change A Lobby Card

Path: `Backoffice -> Games -> Mines -> Title detail -> Lobby card / Assets tab`.

Upload or remove the lobby card, then check `Backoffice -> Site -> Lobby publication` and the player lobby.

The Site/Lobby area controls visibility, not the card upload.

## 9. Warnings / Guardrails

### Production Caution

Do not publish live during an active player-facing test unless the change is intended.

Do not publish live just to preserve work.

Use `Save draft` to preserve work.

Use `Publish live` to affect players.

### Draft And Live

Draft and live can differ.

Always check which state is loaded.

Do not edit a draft while assuming it is the current live state.

Use `Load published live` when you need to inspect what players currently receive.

### Player Impact

These actions can affect players:

- publish game config live;
- publish theme live;
- make a Title visible in Site/Lobby;
- enable or disable demo;
- enable or disable real;
- archive or restore a Title;
- change homepage slot CTA;
- change lobby card asset;
- upload runtime assets;
- remove runtime assets.

### Financial Guardrails

Do not change wallet, ledger, payout, RNG, fairness, settlement, or reconciliation without a dedicated approved work package.

Finance drilldown is read-only.

Player wallet actions require correct permission and a clear reason.

Never treat a UI display issue as a reason to directly edit ledger data.

### Asset Guardrails

Use the correct asset surface.

Homepage media:

`Backoffice -> Site -> Homepage slots`

Lobby card:

`Backoffice -> Games -> Mines -> Title detail -> Lobby card / Assets tab`

or

`Backoffice -> Games -> BOXE -> Title detail -> Assets tab`

Board symbols:

`Backoffice -> Games -> Mines -> Title detail -> Lobby card / Assets tab -> Board assets`

or

`Backoffice -> Games -> BOXE -> Title detail -> Assets tab`

Skin assets:

`Backoffice -> Games -> Mines -> Title detail -> Theme tab`

or

`Backoffice -> Games -> BOXE -> Title detail -> Theme tab`

Sounds:

`Backoffice -> Games -> Mines -> Title detail -> Sounds tab`

or

`Backoffice -> Games -> BOXE -> Title detail -> Sounds tab`

### Copy Guardrails

Backoffice is hardcoded in English.

Mines and BOXE runtime copy is configurable per Title and locale.

Do not use Copy & i18n to translate the backoffice.

Do not use backoffice copy changes to alter player legal or financial behavior.

### Site/Lobby Guardrails

Do not publish a lobby entry before the Title has a valid live game config.

Do not assume a visible lobby card means real play is enabled.

Demo and real are independent flags in Site/Lobby.

Launch Cashier still applies login and wallet availability rules.

## 10. Maintenance

### Manual Ownership

This manual is an operational document.

It should describe what the operator can see and do.

It should not explain internal implementation unless that implementation changes the operator workflow.

### Update Rule

Update this manual when:

- a backoffice area is added;
- a menu label changes;
- a Title Editor tab changes;
- a backoffice action is added or removed;
- a draft/live behavior changes;
- a player-preview consequence changes;
- a finance reporting workflow changes;
- a Site/Lobby workflow changes;
- Launch Cashier behavior changes;
- theme, asset, sound, or lobby card controls change.

### Same-PR Rule

When a work package changes admin UI behavior or adds/removes admin capabilities, update the corresponding section of this manual in the same PR.

Do not postpone the manual update to a later cleanup unless the CTO explicitly approves that split.

Documentation-only PRs should be reserved for typo, wording, or structure fixes.

Capability changes belong with their documentation.

### What Not To Add

Do not add screenshots.

Do not add FAQ sections.

Do not add player-facing help.

Do not add design history.

Do not copy internal plans into this manual.

### Review Checklist

Before merging a manual update, verify:

- paths match the current UI;
- labels match the current UI;
- player impact is stated where relevant;
- mutating actions are clearly marked;
- read-only reports are clearly marked;
- wallet/ledger/RNG/payout/fairness/math boundaries are not blurred;
- examples are copyable and do not require missing assets.
