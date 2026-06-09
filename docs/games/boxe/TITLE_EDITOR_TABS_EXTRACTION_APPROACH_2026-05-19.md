Status: ACTIVE
Last meaningful update: 2026-05-19

# BOXE - Title Editor Tabs Shared Extraction Approach - 2026-05-19

## 1. Scope

Parte A valida l'approccio per `WP-TITLE-EDITOR-TABS-SHARED-EXTRACTION`.
Non autorizza Parte B e non modifica runtime, backend, schema, migration o
gameplay Mines/BOXE.

Obiettivo: estrarre da Mines i pattern admin tab in componenti shared sotto
`frontend/app/ui/title-editor/`, mantenendo Mines admin visual e functional
baseline invariati e facendo crescere BOXE fino alla stessa ergonomia
operativa dove il prodotto lo richiede.

Fonti effettivamente lette o ispezionate:

- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` v2, sezioni
  `GameRuntimeShell As Platform Pattern` e `Pre-Phase Audits`
- `docs/games/boxe/BOXE_FULL_PARITY_AUDIT_2026-05-19.md`, sezioni 2 e 6
- `frontend/app/ui/title-editor/title-editor-shell.tsx`
- `frontend/app/ui/title-editor/title-editor-command-bar.tsx`
- `frontend/app/ui/title-editor/engine-editor-registry.ts`
- `frontend/app/ui/mines/mines-backoffice-editor.tsx`
- `frontend/app/ui/mines/mines-config-overview.tsx`
- `frontend/app/ui/mines/mines-i18n-admin-editor.tsx`
- `frontend/app/ui/mines/mines-grid-config-editor.tsx`
- `frontend/app/ui/mines/mines-board-assets-editor.tsx`
- `frontend/app/ui/mines/mines-sound-assets-editor.tsx`
- `frontend/app/ui/mines/mines-theme-editor.tsx`
- `frontend/app/ui/mines/mines-legacy-labels-editor.tsx`
- `frontend/app/ui/mines/i18n/mines-copy-manifest.ts`
- `frontend/app/ui/mines/i18n/mines-copy-defaults.ts`
- `frontend/app/ui/mines/mines-engine-editor.tsx`
- `frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx`
- `frontend/app/ui/boxe-backoffice/boxe-assets-editor.tsx`
- `frontend/app/ui/boxe-backoffice/boxe-theme-editor.tsx`
- `docs/BACKOFFICE_MANUAL.md` sections covering Title Editor, Mines and BOXE

## 2. Coupling Audit

| Mines tab / surface | Current files | Coupling classification | Evidence | Extraction recommendation |
| --- | --- | --- | --- | --- |
| Editor command/status/subnav | `mines-backoffice-editor.tsx`, `title-editor-command-bar.tsx` | Generalizable via schema/props | Command bar is already shared. Status banner and subnav are duplicated conceptually in Mines and BOXE, but Mines uses specific busy action labels and local unsaved state. | Extract `TitleEditorTabFrame` and `TitleEditorStatusBanner`; keep command bar shared. Engines pass tab registry, active tab, status model and handlers. |
| Overview | `mines-config-overview.tsx`, `mines-backoffice-editor.tsx` | Mixed: frame generalizable via schema/props; metrics via adapter; fairness strictly Mines-specific | Runtime/draft/live cards follow a reusable pattern. Fields are Mines-specific: grid sizes, mine counts, payout runtime, fairness version. Fairness live panel uses `FairnessCurrentConfig` and Mines-specific wording. | Extract `TitleEditorOverviewTab` with sections/metrics descriptors. Mines contributes runtime/config/fairness adapters. BOXE contributes rows/difficulty metrics. Fairness is an optional capability slot, not default shared content. |
| Published language panel | `mines-i18n-admin-editor.tsx`, `mines-backoffice-editor.tsx` | Generalizable via schema/props | Locale selector, live/draft locale, in-game title, coverage, missing/too-long counters and draft/live diff are game-agnostic. Data source is manifest + rule section registry. | Fold into `TitleEditorCopyI18nTab` overview panel. Engines pass locale manifest, defaults, title key, active/live values and update callbacks. |
| Copy / i18n fields | `mines-i18n-admin-editor.tsx`, `i18n/mines-copy-manifest.ts` | Generalizable via schema/props | Mines copy fields are already declarative: key, required, maxLength, placeholders. The editor chooses input vs textarea from max length/value length. | Extract generic manifest-driven copy editor. Mines manifest remains source for Mines keys; BOXE converts current `BOXE_COPY_DEFINITIONS` to the same manifest type. |
| Rules HTML | `mines-i18n-admin-editor.tsx`, `i18n/mines-copy-manifest.ts`, `i18n/mines-copy-defaults.ts` | Generalizable via adapter | Mines has multiple rule sections with labels/helpers; BOXE currently has only `bet_collect`. Shape differs (`i18n.rules_sections[section].body_html` vs `rules_html[locale][section]`). | Extract `TitleEditorRulesHtmlTab` rendering section descriptors. Engines provide read/write adapters for their payload shape and section list. |
| Config: Grid & mines | `mines-grid-config-editor.tsx`, `mines-backoffice-editor.tsx` | Generalizable via adapter, not pure schema | UI pattern is reusable: option group, enabled values, default value, constraints. Mines has a nested matrix: grid -> mine counts -> default per grid, with max 5 published mine choices and "at least one grid/count" validation. | Extract a config framework with field kinds and custom nested field adapters. Mines uses `matrixChoiceWithDefault` adapter; BOXE uses two `choiceSetWithDefault` adapters for rows and difficulty. |
| Demo / Real labels | `mines-legacy-labels-editor.tsx` | Mostly Mines-specific / legacy | This tab edits `ui_labels.demo/real` for legacy button labels. BOXE does not expose an equivalent tab and copy/i18n is the preferred future model. | Do not promote as a first-class shared tab. Either leave Mines-local for backward compatibility or model it later as a legacy capability flag. Do not add to BOXE v1. |
| Lobby card / board assets | `GameCardAssetEditor` inside `mines-backoffice-editor.tsx`, `mines-board-assets-editor.tsx` | Generalizable via schema/props plus asset adapters | Lobby card limits are shared. Board asset rendering uses field descriptors; kind mapping is Mines-local (`safe_icon_data_url` -> `symbol_safe`, `mine_icon_data_url` -> `symbol_mine`). BOXE already has declarative asset fields. | Extract `TitleEditorAssetsTab` with asset field descriptors, validation, preview and delete/upload handlers. Engines provide config write-back mapping only when an uploaded asset must also update presentation config. |
| Sounds | `mines-sound-assets-editor.tsx`, `use-mines-sounds.ts` | Generalizable via schema/props, capability-gated | Sound fields are declarative: kind, label, description, mime limits. Runtime missing-asset behavior is silent. BOXE v1 product decision is silent/defer. | Extract shared design/types and optional `TitleEditorSoundsTab`, but mount only when `capabilities.sounds === true`. Mines mounts; BOXE does not mount in v1. |
| Theme tokens | `mines-theme-editor.tsx`, `boxe-theme-editor.tsx`, `mines-backoffice-editor.tsx` | Generalizable via schema/props | Token lists, presets, load/save/publish flow and status are duplicated. BOXE has a smaller preset set and no advanced skin. | Extract `TitleEditorThemeTab` token editor and theme workflow facade. Engines pass token fields, presets and default tokens. |
| Advanced skin / skin assets | `mines-theme-editor.tsx` | Generalizable via capability flags plus schema/props, but Mines currently richer than BOXE | Mines supports advanced skin fields and skin asset specs. BOXE explicitly says advanced skin is out of scope v1. | Include in shared Theme tab as optional `advancedSkin` and `skinAssets` capabilities. Mines enables both; BOXE v1 disables both while still using shared token/preset UI. |
| Validation error display | `boxe-engine-editor.tsx`, Mines inline status paths in `mines-backoffice-editor.tsx`, `mines-i18n-admin-editor.tsx` | Generalizable via adapter | BOXE has a simple summary list. Mines has inline prevention and i18n coverage summaries but no unified field-targeting abstraction. | Extract `TitleEditorValidationDisplay` with `ValidationIssue[]` and optional field path mapping. Mines can initially use it for summary/coverage without changing existing guards; BOXE maps existing validation errors to issue codes/paths. |

Verdict: extraction is feasible, but not as one flat "8 tab" component
move. The real boundary is:

1. shared tab frame/workflow,
2. shared generic renderers,
3. engine adapters for payload shape,
4. capability flags for surfaces Mines has and BOXE intentionally does not.

## 3. Declarative Schema Shape

Use TypeScript descriptors, not JSON Schema as the primary authoring format.
Reason: fields need renderer components, get/set adapters, validation hooks and
runtime-derived choices. JSON Schema is useful as a future export/check layer,
but would be too weak as the source of truth for nested game config behavior.

Proposed shared types:

```ts
type TitleEditorGameDefinition<TDraft, TRuntime, TLocale extends string> = {
  engineCode: string;
  displayName: string;
  tabs: TitleEditorTabDefinition<TDraft, TRuntime, TLocale>[];
  capabilities: TitleEditorCapabilities;
  copy?: CopyI18nSchema<TDraft, TLocale>;
  rules?: RulesHtmlSchema<TDraft, TLocale>;
  config?: ConfigSchema<TDraft, TRuntime>;
  assets?: AssetsSchema<TDraft>;
  theme?: ThemeSchema;
  validation?: ValidationSchema<TDraft, TRuntime>;
};

type TitleEditorCapabilities = {
  fairnessOverview?: boolean;
  copyI18n?: boolean;
  rulesHtml?: boolean;
  config?: boolean;
  legacyModeLabels?: boolean;
  assets?: boolean;
  sounds?: boolean;
  themeTokens?: boolean;
  advancedSkin?: boolean;
  skinAssets?: boolean;
};

type CopyI18nSchema<TDraft, TLocale extends string> = {
  locales: readonly { code: TLocale; label: string }[];
  titleKey: string;
  fields: readonly CopyFieldDefinition[];
  getActiveLocale: (draft: TDraft) => TLocale;
  setActiveLocale: (draft: TDraft, locale: TLocale) => TDraft;
  getCopy: (draft: TDraft, locale: TLocale) => Record<string, string>;
  setCopyValue: (draft: TDraft, locale: TLocale, key: string, value: string) => TDraft;
};

type RulesHtmlSchema<TDraft, TLocale extends string> = {
  sections: readonly RulesSectionDefinition[];
  getSections: (draft: TDraft, locale: TLocale) => Record<string, { body_html: string }>;
  setSectionBody: (draft: TDraft, locale: TLocale, key: string, value: string) => TDraft;
};

type ConfigSchema<TDraft, TRuntime> = {
  fields: readonly ConfigFieldDefinition<TDraft, TRuntime>[];
  validate?: (draft: TDraft, runtime: TRuntime | null) => ValidationIssue[];
};

type ConfigFieldDefinition<TDraft, TRuntime> =
  | ChoiceSetWithDefaultField<TDraft, TRuntime>
  | MatrixChoiceWithDefaultField<TDraft, TRuntime>
  | CustomConfigField<TDraft, TRuntime>;
```

Mines config can then be expressed without pretending it has the same shape as
BOXE:

```ts
const minesConfigSchema: ConfigSchema<MinesPresentationConfig, MinesRuntimeConfig> = {
  fields: [
    {
      kind: "matrixChoiceWithDefault",
      id: "grid_mines",
      label: "Grid & mines",
      rowLabel: formatGridChoiceLabel,
      getRows: (runtime) => runtime?.supported_grid_sizes ?? [],
      isRowEnabled: (draft, grid) => draft.published_grid_sizes.includes(grid),
      setRowEnabled: toggleMinesGrid,
      getChoices: (runtime, grid) => runtime?.supported_mine_counts[String(grid)] ?? [],
      getSelectedChoices: (draft, grid) => draft.published_mine_counts[String(grid)] ?? [],
      setChoiceEnabled: toggleMinesMineCount,
      getDefaultChoice: (draft, grid) => draft.default_mine_counts[String(grid)],
      setDefaultChoice: setMinesDefaultMineCount,
      constraints: { minRows: 1, minChoicesPerRow: 1, maxChoicesPerRow: 5 },
    },
  ],
};
```

BOXE uses simpler descriptors:

```ts
const boxeConfigSchema: ConfigSchema<BoxeAdminPayload, BoxeRuntimeConfig> = {
  fields: [
    {
      kind: "choiceSetWithDefault",
      id: "rows",
      label: "Rows enabled",
      choices: [4, 5, 6, 7, 8],
      getSelected: (draft) => draft.rows_enabled,
      setSelected: (draft, values) => ({ ...draft, rows_enabled: values }),
      getDefault: (draft) => draft.default_rows,
      setDefault: (draft, value) => ({ ...draft, default_rows: value }),
      constraints: { minSelected: 1 },
    },
    {
      kind: "choiceSetWithDefault",
      id: "difficulty",
      label: "Difficulty enabled",
      choices: ["easy", "medium", "hard"],
      getSelected: (draft) => draft.difficulty_enabled,
      setSelected: (draft, values) => ({ ...draft, difficulty_enabled: values }),
      getDefault: (draft) => draft.default_difficulty,
      setDefault: (draft, value) => ({ ...draft, default_difficulty: value }),
      constraints: { minSelected: 1 },
    },
  ],
};
```

Key decision: shared schema describes admin behavior, not backend payload
shape. Each engine keeps its current endpoint contract and adapters translate
between renderer actions and the game payload.

## 4. Recommended Granularity

Recommendation: split Parte B into 3 sequential sub-WP, not all tabs together
and not cherry-pick only v1 critical tabs.

| Option | Verdict | Reason |
| --- | --- | --- |
| All tabs together with sub-commit atomici | Reject | Too much coupled state in `mines-backoffice-editor.tsx`: config, i18n, assets, theme and validation all mutate different payload shapes. Risk of hidden Mines regression is high even with sub-commits. |
| 2-3 sub-WP sequenziali | Recommended | Preserves Mines baseline gates while extracting stable layers first. Lets BOXE gain value early and exposes schema gaps before touching high-risk Theme/Sounds. |
| Cherry-pick v1 only: Overview, Config, Rules, Assets; defer Theme/Sounds/Copy | Too narrow | Copy/i18n is one of the most mature Mines patterns and BOXE already has copy. Deferring it leaves a major duplicated admin surface. Sounds can be capability-gated, but Copy should be in scope. |

Sub-WP plan:

| Sub-WP | Scope | Mines gate | BOXE outcome | Stop-and-Ask triggers |
| --- | --- | --- | --- | --- |
| B1 - Tab frame, validation, overview, config | `TitleEditorStatusBanner`, `TitleEditorTabFrame`, `TitleEditorValidationDisplay`, `TitleEditorOverviewTab`, `TitleEditorConfigTab` descriptors. | Mines overview/config screenshot and behavior unchanged; grid/mine validation unchanged. | BOXE overview and rows/difficulty move to shared frame; validation gains summary/field paths. | If Mines matrix config cannot be represented without changing current toggle/default behavior. |
| B2 - Copy/i18n and Rules HTML | `TitleEditorCopyI18nTab`, locale panel, manifest editor, `TitleEditorRulesHtmlTab`. | Mines copy/rules exact field list, locale behavior and publish payload unchanged. | BOXE copy/rules get Mines-grade manifest/editor ergonomics, still using BOXE endpoint shape. | If BOXE multi-locale payload and Mines single published-locale model require incompatible UX. |
| B3 - Assets, Theme and Sounds capability gate | `TitleEditorAssetsTab`, `TitleEditorThemeTab`, optional `TitleEditorSoundsTab` design. | Mines lobby/board assets, sounds, tokens, advanced skin and skin assets unchanged. | BOXE assets/theme consume shared UI; BOXE sounds remain unmounted by capability flag. | If theme skin payload in shared endpoint is actually Mines-shaped or BOXE cannot safely ignore `skin`. |

This is still the same WP strategically, but it should be executed as three
reviewable slices with separate visual/admin smoke gates.

## 5. Capability Flags Pattern

Mines has capabilities BOXE should not receive immediately:

| Capability | Mines | BOXE v1 | Pattern |
| --- | --- | --- | --- |
| Fairness diagnostics in overview | Yes | Not in editor diagnostics registry today | `capabilities.fairnessOverview`; optional overview slot. |
| Legacy Demo / Real labels tab | Yes | No | Keep Mines-local or `capabilities.legacyModeLabels`; do not add to BOXE. |
| Advanced skin controls | Yes | No | `capabilities.advancedSkin`; shared Theme tab hides the section when false. |
| Skin asset uploads | Yes | No in current BOXE editor | `capabilities.skinAssets`; asset specs passed only by games that consume them. |
| Sounds tab | Yes | Product owner says BOXE v1 silent/defer | `capabilities.sounds`; shared tab exists but BOXE registry omits it. |
| Board symbols written into presentation config | Yes | BOXE assets currently registry-only | Asset field descriptor has optional `writeBackToDraft`; Mines enables, BOXE disables unless a later runtime-consume WP requires it. |
| Multi-section rules | Yes | Currently only `bet_collect` | Rules sections are schema-driven; BOXE can start with one section and grow without changing shared renderer. |

Capability flags must live in the engine editor definition, not scattered
`if (engineCode === "boxe")` branches in shared components.

## 6. Registry Architecture Decision

Decision: shared tabs live under `frontend/app/ui/title-editor/`, while engine
plugins own schemas/adapters and API orchestration.

Recommended folder shape:

```text
frontend/app/ui/title-editor/
  title-editor-shell.tsx
  title-editor-command-bar.tsx
  engine-editor-registry.ts
  tabs/
    title-editor-tab-frame.tsx
    title-editor-status-banner.tsx
    title-editor-overview-tab.tsx
    title-editor-copy-i18n-tab.tsx
    title-editor-rules-html-tab.tsx
    title-editor-config-tab.tsx
    title-editor-assets-tab.tsx
    title-editor-theme-tab.tsx
    title-editor-sounds-tab.tsx
    title-editor-validation-display.tsx
    types.ts
```

Engine plugin responsibility:

- load/save/publish against current endpoints
- own draft/live state shape and clone/update helpers
- provide descriptors/adapters to shared tabs
- decide capabilities and mounted tabs
- map validation issues to `ValidationIssue[]`

Shared tab responsibility:

- render common layout
- render manifest/schema-driven fields
- perform generic client-side file validation from descriptors
- show status/validation consistently
- avoid engine-specific branches

Do not move API endpoints into the shared tab layer in Parte B. Current backend
contracts differ (`/admin/games/titles/{title}/config` for Mines vs
`/admin/games/boxe/config?...` for BOXE), and backend changes are explicitly
out of scope.

## 7. Backward Compatibility Gates

Hard gates for every Parte B slice:

- zero changes to `frontend/app/ui/mines/` gameplay behavior
- zero backend endpoint/schema/migration changes
- Mines admin visual baseline unchanged for touched tabs
- Mines save/publish payload unchanged
- Mines copy manifest keys and default locale behavior unchanged
- Mines asset upload limits and guidance unchanged
- Mines theme advanced skin and skin assets unchanged
- BOXE sounds tab remains unmounted unless CTO/product reverses the v1 silent decision
- `docs/BACKOFFICE_MANUAL.md` updated in the same PR for any admin capability or behavior change

Suggested verification for Parte B:

- TypeScript/lint for frontend
- focused unit or component tests if existing harness supports these surfaces
- Playwright/admin smoke for Mines Title detail tabs touched by the slice
- screenshot comparison for Mines admin baseline before and after
- BOXE admin smoke for the same tabs

## 8. Stop-and-Ask Expected

Expected Stop-and-Ask points:

| Trigger | Recommendation |
| --- | --- |
| Mines tab proves too coupled to extract without changing markup/order | Stop. Use wrapper extraction first, leaving inner Mines component mounted unchanged, then extract internals in the next slice. |
| Config schema cannot cover Mines matrix and BOXE independent fields cleanly | Stop. Add a `custom` field adapter rather than forcing both into one generic abstraction. |
| Mines validation remains mostly inline and cannot be represented as field paths | Do not block extraction. Shared `ValidationIssue[]` can start as summary-only for Mines and field-level for BOXE, then improve later. |
| Backoffice manual update becomes massive because every tab text changes | Stop. This means implementation changed operator behavior too broadly. Split the PR or keep visual text stable for Mines. |
| BOXE asset runtime consumption is still incomplete | Do not solve inside tab extraction unless already in scope for that sub-WP. Record as dependency on `WP-BOXE-ASSETS-RUNTIME-CONSUME`. |
| Theme advanced skin shared payload risks changing BOXE draft save body | Stop. BOXE v1 should save tokens only until backend/product approves skin support. |

## 9. Backoffice Manual Effort

Manual update is mandatory in the same PR as Parte B because admin capabilities
and tab behavior will change for BOXE and possibly wording/path semantics will
become shared.

Estimated doc-only effort:

- B1: 0.5 prompt, focused on shared overview/config/validation wording and BOXE
  rows/difficulty parity.
- B2: 0.5 prompt, copy/rules section updates for BOXE and shared locale model.
- B3: 0.5-1 prompt, assets/theme/sounds capability flags and BOXE silent v1
  note.

Total doc effort: 1.5-2 prompts across Parte B. It should be co-located with
each sub-WP, not batched at the end.

## 10. Effort Estimate

Audit estimate `7-11 prompt` remains directionally right, but I would adjust
the working estimate to `9-13 prompt` if Mines admin baseline screenshot gates
are enforced properly.

Breakdown:

- Parte A: 1-2 prompt, this document.
- B1: 3-4 prompt.
- B2: 2-3 prompt.
- B3: 3-4 prompt.
- Final integration/manual/playbook distillation if requested: 1-2 prompt.

Why higher than audit: the code shows `mines-backoffice-editor.tsx` owns API
orchestration, draft cloning, local unsaved state, config mutation, i18n
normalization, asset upload/delete and theme workflow in one component. Safe
extraction needs adapter seams before component moves, otherwise Mines parity
is too easy to break.

## 11. Final Recommendation

Proceed to Parte B only after CTO OK, with the 3-slice plan above.

Architecture call:

- shared tabs in `title-editor/tabs/`
- engine schemas/adapters in the Mines and BOXE editor plugins
- capability flags in engine definitions
- no backend/schema/migration changes
- no BOXE Sounds tab in v1
- Mines admin baseline is the release gate, not a nice-to-have

