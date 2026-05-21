# BOXE Backoffice Parity Approach

Status: ACTIVE - refreshed for Wave 4 Parte A
Last meaningful update: 2026-05-21

This document refreshes the original 2026-05-20 Parte A approach with the CTO/Product decisions from 2026-05-21. Parte A remains doc-only: no implementation is included here.

## 1. Product Decisions Locked

| Area | Decision | Parte B consequence |
| --- | --- | --- |
| Sound assets | BOXE inherits the Mines sound-assets feature 1:1. No "skip v1". | Add BOXE sound tab/runtime consumption using the shared Title Editor pattern. |
| Legacy labels | Option B architectural cleanup. The seven UI labels are copy strings and move into the i18n copy manifest. | Do not create `BoxeLegacyLabelsEditor`. Deprecate `MinesLegacyLabelsEditor` behind a zero-diff visual/functionality gate. |
| Rule 2 inheritance symmetry | BOXE inherits platform features unless the source feature is known debt. | Sound assets are inherited; legacy-labels editor is treated as Mines debt and replaced by the modern copy manifest pattern. |

## 2. Sources Audited

| Source | Notes |
| --- | --- |
| `frontend/app/ui/title-editor/engine-editor-registry.ts:35` | Shared title-editor registry is already game-agnostic after Wave 1. |
| `frontend/app/ui/title-editor/title-editor-shell.tsx:116` | Shared shell and section rendering pattern. |
| `frontend/app/ui/mines/mines-backoffice-editor.tsx:78` | Mines exposes eight editor subsections. |
| `frontend/app/ui/mines/mines-backoffice-editor.tsx:1433` | Mines consumes shared title-editor frame/status primitives. |
| `frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx:32` | BOXE exposes six editor subsections. |
| `frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx:538` | BOXE already consumes shared title-editor frame/status primitives. |
| `frontend/app/ui/mines/mines-sound-assets-editor.tsx:14` | Mines sound-assets editor is a real feature, not debt. |
| `frontend/app/ui/mines/mines-legacy-labels-editor.tsx:5` | Mines legacy labels editor is the feature to deprecate. |
| `frontend/app/ui/boxe-backoffice/boxe-assets-editor.tsx:148` | BOXE currently documents audio as silent/missing instead of managing sound assets. |
| `frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx:87` | BOXE already has modern copy-oriented runtime labels. |
| `backend/app/modules/games/boxe/i18n_manifest.py:19` | BOXE backend manifest is the right target for UI label copy. |
| `backend/app/modules/platform/asset_registry/service.py:47` | Shared asset registry validation constraints for MIME/size. |

## 3. Current Sub-Editor Parity

| Mines sub-editor | Mines reference | BOXE status | Verdict |
| --- | --- | --- | --- |
| Overview | `mines-backoffice-editor.tsx:78` | Exists | Keep parameterized shared shell. |
| Copy / i18n admin | `mines-backoffice-editor.tsx:78` | Exists but thinner | Align manifest surface and validation. |
| Rules | `mines-backoffice-editor.tsx:78` | Exists | Align layout and copy validation. |
| Configuration / grid | `mines-backoffice-editor.tsx:78` | Exists as BOXE config | Keep game-specific schema, shared section contract. |
| Legacy labels | `mines-legacy-labels-editor.tsx:5` | Missing | Do not inherit editor. Migrate labels into manifest. |
| Assets | `mines-backoffice-editor.tsx:78` | Exists | Align field semantics and registry integration. |
| Sounds | `mines-sound-assets-editor.tsx:14` | Missing | Inherit 1:1. |
| Theme | `mines-backoffice-editor.tsx:78` | Exists | Align primitives; game-specific tokens allowed. |

## 4. Gap Plan

| Gap | Architecture decision | Files likely affected in Parte B |
| --- | --- | --- |
| Sound assets | Extract/parameterize the Mines sound-assets editor as a shared title-editor primitive, then configure BOXE sound fields. | `frontend/app/ui/title-editor/*`, `frontend/app/ui/mines/*`, `frontend/app/ui/boxe-backoffice/*`, asset registry adapters. |
| Runtime sound consumption | BOXE should resolve sound asset URLs the same way Mines does; no silent placeholder. | BOXE runtime audio hook/helper, title config loader. |
| Legacy labels | Move Bet/Collect/Home/Fullscreen/Game info demo/Game info real and related UI labels into copy manifest keys. | Mines manifest, BOXE manifest, copy resolvers, deprecation wrapper for Mines editor. |
| I18n copy parity | BOXE uses manifest-first copy admin; Mines gets zero-diff projection during migration. | `backend/app/modules/games/*/i18n_manifest.py`, frontend copy manifest/resolver files. |
| Rows/difficulty config | Do not reuse Mines grid-config directly. Introduce a BOXE rows/difficulty config section using the same editor contract. | BOXE backoffice config editor and validation copy. |
| Asset/theme parity | Keep game-specific fields but align field component semantics, validation messaging, and dirty-state behavior. | BOXE backoffice assets/theme editors. |

## 5. Legacy Labels Cleanup Detail

The legacy-labels editor is not a feature to inherit. It is a Mines debt surface. Parte B should:

1. Add canonical i18n manifest keys for the seven legacy UI labels.
2. Make Mines read those keys through its existing copy resolver.
3. Keep a temporary projection layer so existing Mines config produces the same UI output.
4. Deprecate `MinesLegacyLabelsEditor` after proving zero visual and functional drift.
5. Start BOXE directly on the manifest pattern and never add `BoxeLegacyLabelsEditor`.

Gate: Mines player UI and backoffice must remain visually/functionally zero-diff after migration.

## 6. Sound Assets Detail

BOXE should inherit the Mines sound-assets behavior, including:

| Capability | Expected BOXE behavior |
| --- | --- |
| Upload/select/clear sound assets | Same control flow and validation as Mines. |
| Registry constraints | Use shared MIME/size validation from the platform asset registry. |
| Runtime resolution | Runtime config exposes sound URLs to BOXE gameplay. |
| Missing asset behavior | Graceful silence only when no asset is configured, not because BOXE lacks the feature. |
| Backoffice status | Dirty/saved/error states match Mines title-editor behavior. |

Initial BOXE sound slots should mirror gameplay events: safe reveal, mine hit, collect/cashout, win/round success, button/action if supported by the shared primitive.

## 7. Parte B Granularity

| Sub-WP | Scope | Estimate |
| --- | --- | --- |
| BO-B1 copy manifest and legacy-label migration | Add canonical label keys, Mines projection, BOXE manifest usage, deprecation plan. | 4-6 prompts |
| BO-B2 sound-assets inheritance | Shared sound editor primitive and BOXE integration. | 3-4 prompts |
| BO-B3 BOXE config/assets/theme alignment | Rows/difficulty config plus field-level parity cleanup. | 3-4 prompts |
| BO-B4 gates and docs | Zero-diff Mines checks, BOXE backoffice screenshots, capability matrix update. | 2-3 prompts |

Total expected effort: 12-17 prompts, best done after Wave 4 visual/runtime decisions are locked because replay and info rules also touch backoffice metadata.

## 8. Capability Matrix

| Capability | Mines | BOXE current | BOXE target |
| --- | --- | --- | --- |
| Shared title-editor shell | Yes | Yes | Yes |
| Copy/i18n admin | Yes | Partial | Yes, manifest-first |
| Rules admin | Yes | Partial | Yes |
| Gameplay config | Grid config | Rows/difficulty config | Game-specific schema under shared editor contract |
| Legacy labels editor | Yes, debt | No | No; labels are manifest copy |
| Sound assets | Yes | No | Yes, inherited 1:1 |
| Asset registry | Yes | Partial | Yes |
| Theme editor | Yes | Yes | Yes, aligned |
| Zero-diff Mines migration gate | Required | N/A | Required |

## 9. Stop-and-Ask

| Trigger | Category | Ask |
| --- | --- | --- |
| Mines cannot keep zero-diff after label manifest migration. | B/C | Stop and present the exact label/config mismatch before changing UI behavior. |
| Existing asset registry cannot support BOXE sound MIME/size parity. | C | Stop with registry limitation and proposed shared contract. |
| Sound slots need product names beyond Mines event vocabulary. | D | Ask Michele for BOXE-specific sound event naming. |
| Backoffice replay management requires new navigation ownership. | D | Coordinate with WP-REPLAY before implementing admin tabs. |

## 10. 12-Surface Impact

| Surface | Impact |
| --- | --- |
| 10 Backoffice editor | Direct. Current status is red/partial until sound assets and label cleanup land. |
| 11 Replay | Indirect. Backoffice replay management belongs to WP-REPLAY but must reuse the same editor shell. |
| 7 Gameplay shell | Indirect. Label copy and sound assets affect runtime behavior. |
| 12 Resume/disconnect | Indirect. Copy manifest and sound resolution must tolerate stale or missing config. |

## 11. Parte B Delivery - 2026-05-21

Status: PASS with CTO-approved smoke-debt exception.

CTO decision after Stop-and-Ask: full BOXE smoke failures were classified as
category A test/harness drift and do not block WP-BO. The BO gate is focused on
admin parity, build, contract coverage, and Mines zero-diff for the legacy-label
migration.

### Implemented Capabilities

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| BOXE sound assets inherit Mines | Existing title asset registry | Existing asset registry validation | `audio_safe_reveal`, `audio_mine_hit`, `audio_collect`, `audio_win` | BOXE Sounds tab added with shared `TitleSoundAssetsEditor` | BOXE audio hook resolves title theme assets | Shared title-editor classes | Admin focused tests + build | Manual + approach updated | Complete | Naming mirrors Mines 1:1. |
| Shared sound editor primitive | Existing | Existing | Existing | Mines and BOXE consume shared title-editor sound editor | N/A | Existing board-assets/sound classes | Build | Manual updated | Complete | Mines visual path preserved via wrapper. |
| Mines legacy labels manifest migration | Existing title locale maps | `ui_labels.*` added to Mines manifest and projection | Published/draft runtime still exposes legacy `ui_labels` projection | Mines labels tab reads/writes manifest-backed labels | Runtime resolver reads manifest labels then legacy fallback | No intentional visual change | Mines backoffice config tests | Approach updated | Complete | `MinesLegacyLabelsEditor` remains as compatibility UI, backed by manifest copy. |
| BOXE copy manifest labels | Existing title locale maps | BOXE manifest includes action/loading/info labels | Runtime copy payload can override defaults | BOXE Copy i18n tab exposes labels | BOXE buttons/audio/info consume resolver | No intentional layout change | BOXE admin config tests + build | Manual updated | Complete | No `BoxeLegacyLabelsEditor`. |
| BOXE sound runtime consumption | Existing title theme assets | Existing theme asset payload | `titleThemeAssets` passed to gameplay | Sounds configurable in backoffice | `useBoxeAudio` plays configured assets or stays silent | No visual change | Build | Manual updated | Complete | Browser autoplay failures are swallowed and never block gameplay. |

### Gate Result

| Gate | Result |
| --- | --- |
| Frontend build + i18n lint | PASS |
| `tests/contract/test_title_editor_agnostic.py` | PASS |
| `tests/integration/test_title_editor_agnostic_frontend.py` | PASS |
| `tests/integration/test_boxe_admin_config.py` | PASS |
| `tests/integration/test_mines_backoffice_config.py` | PASS |
| `tests/contract/test_game_runtime_frontend_boundary.py` | PASS |
| Mines label visual evidence | Captured under `artifacts/wave4_bo_parity_2026-05-21/` |
| BOXE sound/copy evidence | Captured under `artifacts/wave4_bo_parity_2026-05-21/` |
| Full `test_boxe_smoke.py` | Deferred by CTO as category A smoke debt, not BO blocker |

### Stop-and-Ask Outcome

No product Stop-and-Ask remains for WP-BO. The only encountered blocker was
smoke harness drift outside BO's accepted gate. It is deferred to
`WP-SMOKE-DEBT-CLEANUP`.
