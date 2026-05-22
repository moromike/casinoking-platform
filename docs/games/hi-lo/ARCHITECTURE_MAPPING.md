Status: ACTIVE
Last meaningful update: 2026-05-23

# HI-LO - Architecture Mapping

Phase 3 output for HI-LO. This document maps the SPEC/MATH_SPEC contract into
platform, shared, and game-specific implementation ownership.

No production code is changed by this document.

## 1. Inputs Read

| Input | Use |
| --- | --- |
| `docs/games/hi-lo/SPEC.md` | Product and lifecycle contract. |
| `docs/games/hi-lo/MATH_SPEC.md` | Math/RNG/fairness contract. |
| `docs/games/hi-lo/HI_LO_12_SURFACE_STATUS_2026-05-22.md` | Surface tracker baseline. |
| `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` | Phase 1 architecture mapping rules, 12-surface audit, no-scroll and eight-layer gates. |
| `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_BOXE_2026-05-22.md` | Surface 10 backoffice anti-false-green brief. |
| `docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md` | Navigation and current module ownership. |
| Current filesystem scan | Verifies actual frontend/backend ownership and hardcoded `mines`/`boxe` branches. |

## 2. Architecture Verdict

HI-LO needs one platform-enablement wave before game-specific implementation.

Reason: current code has explicit two-game assumptions in several shared
surfaces:

| Surface | Current evidence | Architecture decision |
| --- | --- | --- |
| Backend game allowlist | `backend/app/modules/platform/game_codes.py` contains `("mines", "boxe")`. | Add `hi_lo` through platform registry before backend routes use it. |
| Title Editor registry | `frontend/app/ui/title-editor/engine-editor-registry.ts` registers `mines` and `boxe` only. | Register HI-LO editor/diagnostics through the same shared registry. |
| Player lobby launch | `frontend/app/ui/player-lobby-page.tsx` has route/mode branches for `mines` and `boxe`. | Generalize via launch registry or add explicit HI-LO adapter in a platform WP. |
| Launch cashier config | Lobby currently loads Mines runtime config only for cashier copy/config. | HI-LO must not bypass launch cashier; add a game-aware config adapter. |
| Account history/replay | `frontend/app/ui/player-account-page.tsx` fetches Mines and BOXE session endpoints explicitly. | Generalize or add HI-LO account/replay adapter before Surface 11 green. |
| Access-session recovery | `backend/app/modules/platform/access_sessions/service.py` auto-cashouts Mines only. | HI-LO real-money recovery needs platform adapter or dedicated HI-LO recovery hook. |

This is not bad news. It is exactly the point of Phase 3: find platform seams
before writing a local HI-LO workaround.

## 3. Common Vs Game-Specific Vs Platform Extension

| Area | Classification | HI-LO handling |
| --- | --- | --- |
| Runtime shell gates | Common platform | Consume `game-runtime` gates and shell. |
| Control rail/bet/balance/action | Common platform | Consume `GameControlRail` and existing primitives. |
| Info/rules modal | Common shell + HI-LO content | Use `GameInfoRulesModal`, populate HI-LO rules. |
| How-to-play gate | Common shell + HI-LO visual | Use shared gate; implement card-based HI-LO visual. |
| Table balance gate | Common platform | Mandatory for real/bonus. |
| Short viewport/rotation | Common platform | Use existing gate; no internal gameplay scrollbars. |
| Card stage | HI-LO-specific | New frontend renderer for card, options, skip, history. |
| Card math | HI-LO-specific | New backend math module per `MATH_SPEC.md`. |
| RNG/fairness draw helper | Platform pattern + HI-LO adapter | Prefer shared helper if available; otherwise HI-LO helper with extraction watchpoint. |
| Backend state machine | HI-LO-specific | New service/state machine under `games/hi_lo`. |
| Wallet/ledger/platform rounds | Common platform | HI-LO game code must use platform boundary, never direct ledger mutation. |
| Demo rounds | HI-LO-specific persistence + platform demo wallet | New demo table equivalent to current game patterns. |
| Replay shell | Common platform + HI-LO renderer | HI-LO supplies card playback renderer/payload. |
| Account history | Platform surface + HI-LO adapter | Must include HI-LO in merged game history. |
| Admin engine page | Common platform | Full master/variant page, no flat list. |
| Title detail shell | Common title-editor | HI-LO editor consumes shared shell/tabs. |
| Admin config fields | HI-LO-specific schema | Skip limit, card assets, theme, copy/rules, no max-win field. |
| Theme/assets/sound infra | Common platform | HI-LO defines asset kinds and defaults. |
| Asset ownership | Product/platform prerequisite | Runtime assets must be owned/licensed/generated. |

## 4. Proposed File Ownership

### 4.1 New Backend Files

| Path | Purpose |
| --- | --- |
| `backend/app/api/routes/hi_lo.py` | HI-LO public game API. |
| `backend/app/modules/games/hi_lo/__init__.py` | Game module marker. |
| `backend/app/modules/games/hi_lo/math.py` | Probability, multiplier and RTP helpers. |
| `backend/app/modules/games/hi_lo/randomness.py` | Deterministic card draw. |
| `backend/app/modules/games/hi_lo/fairness.py` | Seed/fairness artifacts. |
| `backend/app/modules/games/hi_lo/state_machine.py` | Legal transitions. |
| `backend/app/modules/games/hi_lo/repository.py` | SQL persistence. |
| `backend/app/modules/games/hi_lo/service.py` | Start/skip/predict/cashout/replay/session flows. |
| `backend/app/modules/games/hi_lo/admin_config.py` | Published config defaults/validation. |
| `backend/app/modules/games/hi_lo/i18n_manifest.py` | Backend copy/rules preservation if needed. |

### 4.2 Backend Platform Files Expected To Change

| Path | Reason |
| --- | --- |
| `backend/app/modules/platform/game_codes.py` | Add `hi_lo` to allowed game codes. |
| `backend/app/api/routes/__init__.py` or router wiring | Include HI-LO API route. |
| `backend/app/modules/platform/access_sessions/service.py` | Add game-aware recovery hook or explicitly defer HI-LO auto-cashout until recovery WP. |
| `backend/app/modules/account/service.py` | Include HI-LO in account/game history only if backend account service is not already generic. |
| `backend/app/modules/admin/service.py` | Finance/admin drilldown may need HI-LO joins unless generalized. |

### 4.3 New Frontend Files

| Path | Purpose |
| --- | --- |
| `frontend/app/hi-lo/page.tsx` | Public HI-LO route. |
| `frontend/app/ui/hi-lo/hi-lo-standalone.tsx` | Runtime shell composition. |
| `frontend/app/ui/hi-lo/hi-lo-gameplay.tsx` | Main gameplay controller. |
| `frontend/app/ui/hi-lo/hi-lo-card-stage.tsx` | Card/option/history layout. |
| `frontend/app/ui/hi-lo/hi-lo-card.tsx` | Card renderer. |
| `frontend/app/ui/hi-lo/hi-lo-action-options.tsx` | Four action choices. |
| `frontend/app/ui/hi-lo/hi-lo-history-bar.tsx` | FIFO history renderer. |
| `frontend/app/ui/hi-lo/hi-lo-rules-modal.tsx` | HI-LO tabs into shared `GameInfoRulesModal`. |
| `frontend/app/ui/hi-lo/hi-lo-replay-viewer.tsx` | Replay playback renderer. |
| `frontend/app/ui/hi-lo/hi-lo.css` | Game-specific stage/card CSS only. |
| `frontend/app/ui/hi-lo/hi-lo-i18n/*` | Copy defaults/manifest/resolver. |
| `frontend/app/ui/hi-lo/use-hi-lo-runtime.ts` | API/runtime hook. |
| `frontend/app/ui/hi-lo/use-hi-lo-audio.ts` | Optional sound mapping. |

### 4.4 New Backoffice Files

| Path | Purpose |
| --- | --- |
| `frontend/app/ui/hi-lo-backoffice/hi-lo-engine-editor.tsx` | Title Editor adapter. |
| `frontend/app/ui/hi-lo-backoffice/hi-lo-engine-diagnostics.tsx` | Fairness/config diagnostics. |
| `frontend/app/ui/hi-lo-backoffice/hi-lo-config-overview.tsx` | Overview summary. |
| `frontend/app/ui/hi-lo-backoffice/hi-lo-assets-editor.tsx` | Card/stage/lobby asset kinds. |
| `frontend/app/ui/hi-lo-backoffice/hi-lo-theme-editor.tsx` | Full theme/skin depth equivalent. |

### 4.5 Frontend Platform Files Expected To Change

| Path | Reason |
| --- | --- |
| `frontend/app/ui/title-editor/engine-editor-registry.ts` | Register HI-LO editor/diagnostics. |
| `frontend/app/ui/player-lobby-page.tsx` | Add/generalize HI-LO launch route, cashier copy/config and real/bonus mode mapping. |
| `frontend/app/ui/player-account-page.tsx` | Add/generalize HI-LO account history and replay viewer. |
| `frontend/app/ui/games/*` | Should remain generic; touch only if engine page rejects `hi_lo`. |

## 5. Persistence Plan

HI-LO should follow the platform-round split used by Mines/BOXE.

| Persistence | Decision |
| --- | --- |
| Platform economic round | `platform_rounds`, owned by platform. |
| Table/access session | Existing `game_access_sessions` and `game_table_sessions`. |
| Real/bonus HI-LO round state | New `hi_lo_game_rounds`. |
| Demo HI-LO round state | New `demo_hi_lo_game_rounds` if demo remains game-local like Mines/BOXE. |
| Admin config | Prefer title config/copy/theme/asset tables; add HI-LO config projection only if existing title config cannot validate shape. |
| Fairness nonce | Prefer generic per-game nonce; if not available, add `hi_lo_fairness_nonce_seq` with extraction watchpoint. |

Schema changes belong in a backend/state WP, not mixed into frontend work.

## 6. API Plan

| Endpoint | Purpose |
| --- | --- |
| `GET /games/hi-lo/config?title_code=...` | Runtime config, copy, theme, assets and table-balance config. |
| `POST /games/hi-lo/skip-idle` | Server-authoritative idle base card refresh. |
| `POST /games/hi-lo/start` | Start round. |
| `POST /games/hi-lo/round/{id}/skip` | Active skip. |
| `POST /games/hi-lo/round/{id}/predict` | Prediction action. |
| `POST /games/hi-lo/round/{id}/cashout` | Cashout. |
| `GET /games/hi-lo/sessions` | Account history list. |
| `GET /games/hi-lo/round/{id}/replay` | Replay payload. |
| Admin routes | Prefer existing platform catalog/title endpoints; game-specific API only if needed for diagnostics. |

All mutating endpoints require idempotency keys.

## 7. Protected Boundaries

| Boundary | Rule |
| --- | --- |
| `frontend/app/ui/mines/*` | Do not modify for HI-LO unless a shared extraction has a zero-diff Mines gate. |
| `frontend/app/ui/boxe/*` | Do not modify for HI-LO except shared regression tests or explicit platform extraction. |
| `frontend/app/ui/game-runtime/*` | May be extended only as platform WP with Mines/BOXE regression gates. |
| `frontend/app/ui/title-editor/*` | May be extended only as shared admin WP with Mines/BOXE regression gates. |
| Wallet/ledger modules | HI-LO must not mutate directly. |
| Existing migrations | Never rewrite; add new migration. |
| Existing game tables | Do not alter Mines/BOXE state tables for HI-LO. |

## 8. Platform Prerequisites

These are the blockers before heavy HI-LO code:

| ID | Prerequisite | Reason | Stop if not solved? |
| --- | --- | --- | --- |
| P1 | Add `hi_lo` to backend game-code registry. | Platform routes/table sessions reject unknown games. | Yes |
| P2 | Player lobby launch registry supports HI-LO. | Real-money launch guard must not be bypassed. | Yes |
| P3 | Account history/replay registry supports HI-LO. | Surface 11 and account entry point. | Before replay/closure |
| P4 | Title Editor registry supports HI-LO. | Surface 10 title detail. | Before admin WP |
| P5 | Access-session recovery has HI-LO strategy. | Silent loss is forbidden. | Before real-money release |
| P6 | Asset ownership plan for cards/background. | Runtime cannot ship screenshot pixels. | Before visual closure |

## 9. Testing Strategy

| Test family | Scope |
| --- | --- |
| Math unit | All 13 rank rows, sequence multipliers, skip EV, no cap. |
| RNG unit | Determinism, uniformity smoke, replacement. |
| Backend integration | Demo and real start/predict/win/loss/skip/cashout/idempotency. |
| Platform boundary | `game-runtime` no imports from game modules; platform game-code allowlist includes HI-LO. |
| Frontend smoke | Idle, active, win, loss, cashout, A edge, K edge. |
| No-scroll visual | Desktop/mobile/landscape DOM measurements. |
| Backoffice two-step | 10A-F audit and side-by-side evidence. |
| Real-money safety | Launch cashier appears and never opens with whole wallet. |
| Product owner | `localhost:3000` player/admin walkthrough. |

## 10. Mermaid Map Impact

H0-H3 added HI-LO backend, admin placeholder and player runtime modules. The
Mermaid code map was updated on 2026-05-23 to show:

- HI-LO player UI ownership under `frontend/app/ui/hi-lo`;
- HI-LO backend route/service/math/randomness/fairness ownership;
- HI-LO persistence group;
- `game-runtime` boundary extended to all game UI folders;
- HI-LO player runtime request flow.

Future implementation that changes module ownership, admin flow, replay flow or
shared-vs-game-specific boundaries must update
`docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md` in the same commit.

## 11. Decision Brief For Michele

Architecture proposal:

1. Do a small platform-enablement wave first.
2. Then implement backend math/RNG/state/API.
3. Then player visual/content.
4. Then admin/backoffice full depth.
5. Then replay/account/recovery/closure.

The main practical blocker is asset ownership for the full card deck and stage
visuals. The main platform blocker is game-code/account/lobby/admin registry
generalization for the third game.
