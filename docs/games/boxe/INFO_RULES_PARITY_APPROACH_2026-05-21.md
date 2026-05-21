# BOXE Info Rules Parity Approach

Status: ACTIVE - Wave 4 Parte B
Last meaningful update: 2026-05-21

Parte A is doc-only. Product decision is locked: the BOXE info button must follow the Mines rules modal pattern.

## 1. Problem

Mines uses the runtime info button to open a rules/replay modal. BOXE currently uses the same conceptual button to reopen the how-to-play gate. That is visually and functionally different, and Michele flagged it as wrong at a glance.

The how-to-play gate remains a first-run/onboarding surface. The runtime "i" button must become the rules modal surface.

## 2. Sources Audited

| Source | Finding |
| --- | --- |
| `frontend/app/ui/mines/mines-gameplay.tsx:395` | Mines resets rules tab state before opening rules modal. |
| `frontend/app/ui/mines/mines-gameplay.tsx:626` | Mines `i` trigger uses `button-ghost mines-rules-trigger` and copy-driven aria label. |
| `frontend/app/ui/mines/mines-rules-modal.tsx:57` | Overlay click closes modal. |
| `frontend/app/ui/mines/mines-rules-modal.tsx:59` | Modal article uses dialog semantics. |
| `frontend/app/ui/mines/mines-rules-modal.tsx:80` | Mines modal has tablist for rules/replay. |
| `frontend/app/ui/mines/mines-rules-modal.tsx:102` | Rules body rendering. |
| `frontend/app/ui/mines/mines-rules-modal.tsx:131` | Replay body rendering. |
| `frontend/app/ui/mines/mines.css:2355` | Overlay styling. |
| `frontend/app/ui/mines/mines.css:2441` | Modal container styling. |
| `frontend/app/ui/mines/mines.css:2478` | Tabs styling. |
| `frontend/app/ui/mines/mines.css:2737` | Info trigger styling. |
| `frontend/app/ui/mines/mines-copy-resolver.ts:26` | Runtime i18n/legacy/default copy chain. |
| `frontend/app/ui/mines/mines-copy-manifest.ts:188` | Rules copy keys. |
| `frontend/app/lib/helpers.ts:128` | Rules sections helper. |
| `frontend/app/ui/boxe/boxe-gameplay.tsx:599` | BOXE has an `i` button but hardcoded aria label. |
| `frontend/app/ui/boxe/boxe-gameplay.tsx:604` | BOXE `i` button calls `onOpenGameInfo`. |
| `frontend/app/ui/boxe/boxe-standalone.tsx:379` | BOXE implements game info by setting how-to-play incomplete. |
| `frontend/app/ui/boxe/boxe-standalone.tsx:248` | BOXE how-to-play gate overlay. |
| `frontend/app/ui/boxe/boxe-gameplay.tsx:194` | BOXE locale derives from browser language, not necessarily title copy locale. |
| `frontend/app/ui/boxe/boxe-copy-defaults.ts:6` | BOXE lacks rules modal labels/copy keys. |
| `backend/app/modules/games/boxe/service.py:119` | BOXE runtime presentation config includes rules data. |
| `backend/app/modules/games/boxe/admin_config.py:267` | BOXE default rules HTML exists. |
| `backend/app/modules/games/boxe/admin_config.py:400` | BOXE validates rules config. |

## 3. Mines Pattern To Inherit

| Pattern | Mines behavior | BOXE target |
| --- | --- | --- |
| Trigger | Runtime `i` button opens modal, not onboarding. | Same. |
| Modal shell | Overlay dialog with close semantics. | Shared shell or strict adapter. |
| Content tabs | Rules + replay tab where replay exists. | Rules now, replay tab coordinated with WP-REPLAY. |
| Copy chain | Manifest/runtime/defaults. | BOXE copy manifest/runtime/defaults. |
| Rules source | Title config and helper-rendered sections. | BOXE `presentation_config.rules_html` plus structured copy fallback. |
| Busy semantics | Trigger can be disabled while action interaction is locked. | Same principle. |

## 4. BOXE Divergences

| Divergence | Current BOXE | Verdict |
| --- | --- | --- |
| Runtime info opens HTP gate | `onOpenGameInfo` reopens how-to-play | Must change. |
| Rules modal absent | No BOXE runtime modal | Must add. |
| Copy hardcoded | Aria label is hardcoded | Must use copy adapter. |
| Replay tab absent | No BOXE runtime replay viewer | Coordinate with WP-REPLAY. |
| Layout not inherited | BOXE uses onboarding overlay instead of rules modal | Must inherit Mines pattern. |

## 5. Architecture Decision

Extract a shared rules modal pattern under `frontend/app/ui/game-runtime/`, then consume it through game-specific adapters.

Proposed primitives:

| Primitive | Responsibility |
| --- | --- |
| `GameInfoRulesModal` | Shared overlay, dialog semantics, title, close, tab shell, keyboard/overlay close. |
| `GameInfoRulesTrigger` or runtime tools slot | Shared `i` trigger semantics/styling if extraction can be zero-diff for Mines. |
| `GameRulesContentAdapter` | Game-specific content mapping from config/copy into modal sections. |
| `GameReplayTabAdapter` | Optional replay tab surface; BOXE can hide or disabled-state it until WP-REPLAY lands. |

Default implementation path:

1. Extract from Mines with a zero-diff visual gate.
2. Keep Mines consuming the same visual output.
3. Add BOXE adapter using BOXE rules copy/config.
4. Replace BOXE `onOpenGameInfo` behavior so it opens the rules modal instead of HTP.

If zero-diff extraction of Mines is too risky in the same wave, implement a BOXE modal that consumes the shared visual tokens/classes copied into `game-runtime`, then schedule Mines extraction immediately after. However, the target architecture remains shared.

## 6. BOXE Content Source

BOXE rules content should come from:

| Priority | Source |
| --- | --- |
| 1 | Runtime `presentation_config.rules_html` when present and sanitized/approved. |
| 2 | BOXE copy manifest structured rules sections. |
| 3 | Defaults derived from `SPEC.md`/`BOXE_BRIEF.md`. |

No backend raw error/copy strings should leak into the modal. Copy must be user-facing and localized through the same manifest path used elsewhere.

## 7. Replay Tab Coordination

Mines modal has Rules and Replay tabs. BOXE replay is WP-REPLAY and not yet player-visible.

Recommended Wave 4 sequencing:

1. Add BOXE rules modal now.
2. Include a tab API that can accept a replay tab.
3. Hide the BOXE replay tab until WP-REPLAY supplies a real viewer, unless CTO explicitly wants a disabled placeholder.
4. WP-REPLAY later turns on the tab using the same shared modal shell.

## 8. Parte B Granularity

| Sub-WP | Scope | Estimate |
| --- | --- | --- |
| INFO-B1 shared modal extraction | Extract modal shell/classes from Mines with zero-diff gate. | 3-5 prompts |
| INFO-B2 BOXE adapter | BOXE rules content, copy keys, trigger behavior. | 3-4 prompts |
| INFO-B3 replay tab seam | Optional/hidden replay tab API coordinated with WP-REPLAY. | 1-2 prompts |
| INFO-B4 visual and accessibility gates | Desktop/mobile screenshots, keyboard/overlay close, copy checks. | 2-3 prompts |

Total expected effort: 9-14 prompts.

## 9. Stop-and-Ask

| Trigger | Category | Ask |
| --- | --- | --- |
| Mines modal extraction causes any visual drift. | B/C | Stop and either fix extraction or defer Mines migration while preserving BOXE parity target. |
| Product wants BOXE replay tab visible before replay exists. | D | Ask whether to show disabled tab or hide until WP-REPLAY. |
| Rules HTML sanitization contract is unclear. | D/C | Stop before rendering arbitrary HTML. |
| Runtime HTP and rules modal conflict on first launch. | D | Ask whether first-run gate should block rules modal until accepted. |

## 10. Capability Matrix

| Capability | Mines | BOXE current | BOXE target |
| --- | --- | --- | --- |
| Runtime `i` trigger | Yes | Yes | Yes |
| Trigger opens rules modal | Yes | No, opens HTP | Yes |
| Shared modal shell | Mines-specific | No | Shared `game-runtime` shell |
| Rules content | Yes | Admin config exists, not runtime modal | Yes |
| Replay tab | Yes | No | Added by WP-REPLAY or hidden seam |
| Copy manifest | Yes | Partial | Yes |
| Mobile modal behavior | Yes | HTP only | Yes |

## 11. 12-Surface Impact

| Surface | Impact |
| --- | --- |
| 5 How-to-play / info | Direct. Separates onboarding HTP from runtime rules modal. |
| 7 Gameplay shell | Direct. Runtime top tools must match Mines behavior. |
| 8 Mobile rotation | Direct. Modal must behave on portrait/landscape. |
| 11 Replay | Indirect/direct. Modal becomes the future replay tab host. |
| 10 Backoffice editor | Indirect. Rules admin copy must feed the modal. |

## 12. Parte B Delivery Matrix

Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes
--- | --- | --- | --- | --- | --- | --- | --- | --- | --- | ---
Shared rules modal shell | n/a | n/a | n/a | n/a | `GameInfoRulesModal` extracted under `game-runtime`; Mines consumes through its adapter | Reuses existing Mines classes for zero visual drift | Contract boundary test | Runtime/Mines atlas | Complete | Shared shell has no Mines/BOXE imports.
Mines info modal parity | n/a | n/a | n/a | n/a | Mines `i` still opens the same rules/replay modal | Existing CSS/classes unchanged | Build + i18n lint + screenshots | Mines atlas | Complete | Visual output intentionally preserved.
BOXE info trigger | n/a | n/a | n/a | n/a | BOXE `i` opens `BoxeRulesModal`, not How To Play | Existing Mines modal styling reused | Browser smoke + screenshots | BOXE atlas | Complete | HTP remains first-run gate only.
BOXE rules content | n/a | Existing sanitized `rules_html` contract reused | Runtime `presentation_config.rules_html` and copy reused | n/a | Modal renders BOXE rules body with copy fallback | Existing rules body styles | Browser/static tests | Approach + BOXE atlas | Complete | Runtime rules HTML wins over defaults.
BOXE replay seam | n/a | n/a | n/a | n/a | Shared tab API can accept replay later; BOXE passes rules only | No disabled replay UI | Static test asserts no BOXE replay tab id | Approach doc | Intentionally skipped visible UI | WP-REPLAY owns viewer/tab activation.
How-to-play separation | n/a | n/a | n/a | n/a | `onOpenGameInfo` removed; no runtime path resets HTP incomplete | n/a | Static + browser smoke | BOXE brief log | Complete | First-run onboarding unchanged.
