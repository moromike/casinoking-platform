Status: ACTIVE
Last meaningful update: 2026-05-23

# HI-LO Closure Report

Technical closure record for HI-LO as CasinoKing game 3 and for the methodology
distilled toward game 4.

Important: this is a technical closure package, not a product-owner final
approval. The hard `localhost:3000` walkthrough remains the last gate before
calling HI-LO fully green.

## 1. Executive Summary

HI-LO is implemented end-to-end as a playable CasinoKing proprietary game:

- platform registration, lobby routing and launch context;
- math/RNG/fairness and deterministic replay payload;
- demo and real-money table-session guarded lifecycle;
- player runtime with provider intro, how-to, rules, table-balance gate,
  card gameplay, predictions, skip, cashout and error UX;
- full title-editor backoffice with copy, rules, config, assets, sounds, theme
  and validation;
- player account history and admin finance replay;
- active-round resume to prevent silent loss on reload.

The implementation succeeded in the main methodological goal: HI-LO did not
repeat the BOXE Surface 10 rescue cycle. The admin layer was built from the
full 10A-F decomposition and shared platform primitives instead of a local
partial editor.

## 2. Final State

| Area | State | Evidence |
| --- | --- | --- |
| Main branch | `c147eca` before this docs closure commit | H6 merged to `main`. |
| Services | Green | Frontend `:3000`, backend `:8000`, Postgres and Redis healthy after rebuild. |
| Build | Green | `npm run build` PASS. |
| I18n lint | Green | `npm run lint:i18n` PASS. |
| Backend/game tests | Green | HI-LO service, math/randomness, platform game adapter tests PASS. |
| Admin/account regression | Green | Admin finance and account wallet movement integration tests PASS. |
| Product owner walkthrough | Pending | Must be run by Michele on `localhost:3000`. |

## 3. 12-Surface Status

| # | Surface | Technical status | Product-owner status | Notes |
| --- | --- | --- | --- | --- |
| 1 | Lobby card/catalog | Green | Pending | HI-LO uses CMS publication and player registry. |
| 2 | Launch cashier/table gate | Green | Pending | Real/bonus entry uses explicit `GameTableBalanceGate`, default/max 100. |
| 3 | Admin preview launcher | Green | Pending | Shared admin engine page can preview title variants. |
| 4 | Provider intro gate | Green | Pending | Shared `GameProviderBootstrap`. |
| 5 | How-to/info rules | Green | Pending | Shared rules modal + rich HI-LO content. |
| 6 | Table balance gate | Green | Pending | Cash/bonus start requires table session. |
| 7 | Gameplay shell | Green-major | Pending | Player shell implemented; PO visual pass still required. |
| 8 | Mobile/rotation | Green-major | Pending | CSS no-scroll intent implemented; final visual matrix should be walked. |
| 9 | Embed mode | Green-major | Pending | Shared launch context supports embed; explicit smoke still useful. |
| 10 | Backoffice | Green-major | Pending | Full 10A-F implemented; PO admin walkthrough required. |
| 11 | Replay viewer | Green-major | Pending | Player/account/admin replay implemented in H6. |
| 12 | Disconnect/resume | Green-major | Pending | Active-round resume implemented; timeout/force-close policy remains a tracked platform hardening item. |

Verdict: HI-LO is **technical green-major**. It becomes full green only after
Michele's `localhost:3000` walkthrough approves the player, admin, account and
replay flows or explicitly accepts residuals.

## 4. Eight-Layer Closure Table

| Surface group | Container | Content | Visual | Functional | Persistence | Runtime consume | Tests | Product owner |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Player launch/gameplay | Green | Green | Green-major | Green | Green | Green | Green | Pending |
| Info/how-to | Green | Green | Green-major | Green | n/a/defaults | Green | Green | Pending |
| Real-money guard | Green | Green | Green-major | Green | Green | Green | Green | Pending |
| Backoffice 10A-F | Green | Green | Green-major | Green | Green | Green | Green | Pending |
| Replay/account/finance | Green | Green | Green-major | Green | Green | Green | Green | Pending |
| Resume/recovery | n/a | n/a | n/a | Green-major | Green | Green | Green | Pending |

The product-owner column is intentionally not marked green.

## 5. Work Completed By Wave

| Wave | Result |
| --- | --- |
| H0 Platform enablement | `hi_lo` accepted by registries, lobby/admin routes and title editor placeholders. |
| H1 Math/RNG/fairness | Rank/action probability table, 98% multiplier model, deterministic seeded draw and verifier. |
| H2 Backend state/API | Rounds, actions, idempotency, demo/real lifecycle, sessions and replay payload. |
| H3 Player runtime | `/hi-lo` standalone, shared gates, gameplay shell and card stage. |
| H4 Content/assets | Rules modal, how-to cards, four locales and owned card-back asset. |
| H5 Backoffice | Full shared Title Editor implementation, draft/live config, assets/theme/sounds/validation. |
| H6 Replay/recovery | Player/account/admin replay and active-round resume. |
| H7 Closure | This report, next-game replication brief and Playbook distillation. |

## 6. Reusable Lessons From HI-LO

| Lesson | Classification | Action |
| --- | --- | --- |
| Platform enablement before game-specific code works. | Reusable method | Keep H0 pattern for game 4. |
| Surface 10 10A-F upfront prevents BOXE-style false green. | Reusable method | Keep mandatory for every admin wave. |
| Full admin editor is now cheap when shared primitives are consumed correctly. | Platform pattern | Reuse Title Editor shape for game 4. |
| Replay/account/finance still use explicit per-game branches. | Platform debt | Game 4 should introduce a registry adapter instead of a fourth branch. |
| Active-round resume can be game-specific while platform timeout recovery remains separate. | Platform pattern + debt | Keep game resume endpoint; plan generic recovery adapter later. |
| Product-owner walkthrough remains non-automatable. | Reusable method | Do not mark final green without it. |

## 7. Residuals

| Residual | Severity | Recommendation |
| --- | --- | --- |
| Product owner `localhost:3000` walkthrough pending. | Hard closure gate | Michele tests the checklist in section 8. |
| Timeout/force-close recovery is not a generic HI-LO auto-cashout adapter. | Platform hardening | Track as production readiness, not hidden HI-LO blocker if reload resume is accepted. |
| Account/admin replay adapters are explicit branches for Mines/BOXE/HI-LO. | Platform cleanup before game 4 | Extract player/admin replay registry before adding another game. |
| Visual screenshot matrix is not attached to this docs-only H7 commit. | Evidence gap | Run browser smoke if Michele wants formal screenshot archive. |

## 8. Product Owner Walkthrough Checklist

Run on `localhost:3000` after services are healthy.

| Scenario | Route | Expected |
| --- | --- | --- |
| Lobby publication | `/` | HI-LO appears only if CMS title/site publication enables it. |
| Demo play | `/hi-lo?title_code=hilo001&mode=demo` | Provider/how-to, start, predict, skip, cashout/loss work. |
| Real play guard | Lobby real launch or real route | Table-balance modal appears before gameplay; default amount is 100 and max is 100. |
| Reload active round | Start real/demo round, reload | Existing active hand resumes; no new silent round and no silent loss. |
| Info modal | In game, click info | Rich HI-LO rules, not placeholder content. |
| Account replay | `/account` -> Storico gioco | HI-LO sessions appear; replay opens with card sequence/fairness. |
| Admin engine | `/admin/games/hi-lo` | Master/variant page matches shared Mines/BOXE engine-page pattern. |
| Admin detail | `/admin/games/hi-lo/titles/<title_code>` | Overview/copy/rules/config/assets/sounds/theme/validation visible. |
| Admin save/publish | Edit copy/theme, save draft, publish | Runtime consumes published changes. |
| Admin finance replay | `/admin` finance report | HI-LO session detail can open admin replay. |

## 9. Handoff Documents

Use these for game 4:

- `docs/NEXT_GAME_REPLICATION_BRIEF_FROM_HI_LO_2026-05-23.md`
- `docs/NEXT_GAME_BACKOFFICE_REPLICATION_BRIEF_FROM_HI_LO_2026-05-23.md`
- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`
- `docs/NEW_GAME_BRIEF_TEMPLATE.md`
- `docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md`

## 10. CTO Verdict

HI-LO can be treated as temporarily closed for engineering purposes and ready
for Michele's final walkthrough. Do not start game 4 implementation from memory:
start from the replication brief, the Playbook and the current Mermaid map.
