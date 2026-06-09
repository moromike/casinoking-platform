Status: ACTIVE
Last meaningful update: 2026-05-24

# Platform Installation Settings Backoffice - Current-State CTO Review

Reviewed plan: `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_PLAN_2026-05-24.md`

This review is per-plan only. It is not a cross-plan review and it does not
authorize implementation.

## CTO Verdict

Status: not green, read-only direction confirmed.

The read-only Platform Settings MVP is valid, but CasinoKing does not yet have
a source-of-truth inventory for platform settings. Building UI before
classification would be dangerous. Every row must declare owner, source,
visibility, masking, restart requirement and risk class before it appears in
backoffice.

No editable setting is approved.

## Settings Inventory

| Setting / Area | Source of truth | Visibility | Risk | Current gap | Evidence |
| --- | --- | --- | --- | --- | --- |
| App identity, env, API prefix, version | Process env read by `Settings` | Read-only | Low | No source tracking and no real build metadata beyond `APP_VERSION`. | `backend/app/core/config.py:12`, `infra/docker/docker-compose.yml:11` |
| Database URL, Redis URL | Effective env | Hidden/masked | Critical | `/ready` does not verify DB/Redis; Redis exists in config but diagnostics are not modeled. | `backend/app/core/config.py:16`, `backend/app/db/config.py:6`, `backend/app/db/connection.py:10` |
| JWT secret, site access password, Mines server seed | Env with local defaults | Hidden only | Critical | Local defaults exist; production guard against weak/default secrets is not modeled here. | `backend/app/core/config.py:21`, `backend/app/api/dependencies.py:30`, `backend/app/modules/auth/security.py:52`, `backend/app/modules/games/mines/fairness.py:257` |
| JWT and game launch token TTL | Env | Read-only | High | Operationally sensitive; not safe as editable without rollout/test. | `backend/app/core/config.py:25`, `backend/app/modules/platform/game_launch/service.py:71` |
| CORS origins | Effective env | Masked/read-only | High | Local envs diverge; wildcard methods/headers; no production policy row. | `backend/app/core/config.py:39`, `backend/app/main.py:39`, `backend/.env:3`, `infra/docker/.env:9` |
| Asset storage root/base URL/static mounts | Env + FastAPI mounts | Masked/read-only | Medium | Title assets and site assets use different URL assumptions; no storage health row. | `backend/app/core/config.py:45`, `backend/app/main.py:47`, `backend/app/modules/platform/asset_registry/service.py:538` |
| Asset upload limits and MIME | Code constants | Read-only | Medium | Limits are not central descriptors; not safe as global editable settings. | `backend/app/modules/platform/asset_registry/service.py:25`, `backend/app/modules/platform/site_cms/service.py:37` |
| Access session timeout, sweep interval, sweep limit | Code constants | Read-only | High | Backend 3 minutes and frontend Mines 180s duplicate semantics; no shared contract. | `backend/app/modules/platform/access_sessions/service.py:23`, `backend/app/main.py:17`, `frontend/app/ui/mines/mines-standalone.tsx:68` |
| Table session max/default chips and quick amounts | Backend constants + frontend per game | Read-only | High | Endpoint limits do not pass game code to service; quick chips are scattered. | `backend/app/modules/platform/table_sessions/service.py:13`, `backend/app/api/routes/platform_table_sessions.py:29`, `frontend/app/ui/boxe/boxe-table-balance-config.ts:1`, `frontend/app/ui/hi-lo/hi-lo-standalone.tsx:50` |
| Auto-settlement policy | Platform service with game branches | Read-only | Critical | Refund/cashout semantics are game-specific but live in platform service; no health descriptor. | `backend/app/modules/platform/access_sessions/service.py:577` |
| Admin audit change history | `admin_audit_log` | Read-only | Medium-high | Route uses games area, not superadmin; no `platform_settings` resource kind; retention absent. | `backend/migrations/sql/0030__admin_audit_log.sql:10`, `backend/app/modules/platform/admin_audit/service.py:34`, `backend/app/api/routes/admin.py:676` |
| Game registry health | Catalog DB + hardcoded frontend registries | Read-only | High | No unified descriptor for lobby/runtime/finance/replay/error namespace/smoke. | `backend/app/modules/platform/game_codes.py:1`, `backend/migrations/sql/0023__platform_catalog_bootstrap.sql:17`, `frontend/app/ui/player-game-registry.ts:1`, `frontend/app/ui/title-editor/engine-editor-registry.ts:35` |
| Error Matrix | No registry yet | Read-only later | High | Cannot render correctly before error registry/request id foundation. | `backend/app/api/responses.py:11`, `backend/app/api/routes/boxe.py:266`, `backend/app/api/routes/hi_lo.py:294`, `backend/app/api/routes/mines.py:113` |
| Platform settings RBAC | Admin profile + `require_admin_area` | Read-only | Critical | Admin without profile falls back to superadmin; no Platform Settings shell or superadmin-only route yet. | `backend/migrations/sql/0017__admin_roles_and_permissions.sql:4`, `backend/app/api/dependencies.py:75`, `backend/app/api/dependencies.py:126`, `frontend/app/ui/admin-shell-panel.tsx:107` |

## CTO Corrections To Carry Forward

- Platform Settings must be a read model first, not an editor.
- Values that are hidden/masked must never be placed in disabled inputs.
- Error Matrix depends on the Error Code Registry and request/support id.
- Session/table/settlement settings touch money and are read-only only.
- RBAC must be superadmin-only for MVP.
- Every row needs `source_of_truth`, `owner`, `visibility`, `restart_required`,
  `environment_scope`, `audit_required` and `risk_class`.

## Approved Next WP

`WP-PLATFORM-SETTINGS-READONLY-INVENTORY`

Scope:

- produce descriptor contract for settings rows;
- classify hidden/masked/read-only/editable-future;
- define masking rules;
- define source-of-truth inventory;
- define superadmin-only route/nav;
- render no editable UI yet;
- exclude Error Matrix rendering until error registry exists.

## Stop Before Code

Stop if implementation proposes:

- editable settings in the MVP;
- exposing secrets or unrevealed seeds;
- rendering read-only critical values as form inputs;
- changing timeout/table balance/settlement behavior from this WP;
- adding Error Matrix before the error registry foundation.

