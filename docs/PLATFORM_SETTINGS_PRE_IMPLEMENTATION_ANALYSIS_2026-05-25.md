Status: ACTIVE
Last meaningful update: 2026-05-25

# Platform Settings - Pre-Implementation Analysis

## Verdict

Status: not green.

The direction is correct only as read-only inventory. No editable Platform
Settings backoffice is approved. Building an editor before classifying
source-of-truth, owner, visibility, masking, restart requirements and risk
would be dangerous.

Recommended implementation WP:

`WP-PLATFORM-SETTINGS-READONLY-INVENTORY`

This WP should come after `WP-ERROR-REQUEST-FOUNDATION-MVP`, or be limited to
documentation/descriptors until the error/request foundation lands.

## Scope Of This Analysis

This analysis closes pre-development discovery for Platform Settings. It does
not authorize editable settings, changing environment config, changing financial
limits or exposing secrets.

Read before implementation:

- `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_PLAN_2026-05-24.md`
- `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_CTO_REVIEW_2026-05-24.md`
- `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`
- this document

## Current Code Evidence

| Area | Current state | Evidence | Visibility |
| --- | --- | --- | --- |
| App identity | `APP_NAME`, `APP_VERSION`, `APP_ENV`, API prefix from env defaults. | `backend/app/core/config.py:12`, `backend/app/core/config.py:15` | Read-only |
| DB/Redis | URLs loaded from env with local defaults. | `backend/app/core/config.py:16`, `backend/app/core/config.py:20`, `infra/docker/docker-compose.yml:15`, `infra/docker/docker-compose.yml:16` | Hidden/masked |
| JWT | Secret and TTL from env. | `backend/app/core/config.py:21`, `backend/app/core/config.py:25`, `infra/docker/docker-compose.yml:17`, `infra/docker/docker-compose.yml:18` | Secret hidden; TTL read-only |
| Game launch token TTL | Env-backed TTL. | `backend/app/core/config.py:28` | Read-only high-risk |
| Site password | Env-backed password. | `backend/app/core/config.py:31` | Hidden |
| Mines server seed | Env-backed server seed. | `backend/app/core/config.py:35` | Hidden |
| CORS origins | Env-backed tuple used by FastAPI CORS. | `backend/app/core/config.py:39`, `backend/app/main.py:39`, `infra/docker/docker-compose.yml:21` | Masked/read-only |
| Asset storage | Env-backed storage root/base URL plus static mounts. | `backend/app/core/config.py:45`, `backend/app/core/config.py:48`, `backend/app/main.py:47`, `backend/app/main.py:50` | Masked/read-only |
| Access timeout | Code constant. | `backend/app/modules/platform/access_sessions/service.py:23` | Read-only high-risk |
| Sweep interval | Code constant in app main. | `backend/app/main.py:17` | Read-only high-risk |
| Sweep limit | Code constant in access session service. | `backend/app/modules/platform/access_sessions/service.py:24` | Read-only high-risk |
| Table session limits | Code constants. | `backend/app/modules/platform/table_sessions/service.py:13`, `backend/app/modules/platform/table_sessions/service.py:14` | Read-only high-risk |
| Demo token rate limit | Code constant. | `backend/app/api/routes/demo.py:27`, `backend/app/api/routes/demo.py:194` | Read-only future-editable |
| Game registry | Backend allowed tuple and frontend registries are separate. | `backend/app/modules/platform/game_codes.py:1`, `frontend/app/ui/player-game-registry.ts:1`, `frontend/app/ui/title-editor/engine-editor-registry.ts:35` | Read-only health |
| Error matrix | No registry yet. | `backend/app/api/responses.py:11`, `frontend/app/lib/api.ts:14` | Blocked by error foundation |
| Admin RBAC | `require_admin_area("superadmin")` exists conceptually; missing settings shell. | `backend/app/api/dependencies.py:126`, `backend/app/api/dependencies.py:160` | Superadmin-only |
| Admin token query | CMS v2 lab can receive admin token in URL query. | `frontend/app/ui/admin-shell-panel.tsx:81` | Sensitive surface for masking/logging |
| Site access password frontend | Frontend has a default access password value. | `frontend/app/ui/player-register-page.tsx:13`, `frontend/app/ui/player-register-page.tsx:95` | Secret-like access control leaks into client behavior. |
| Health readiness | `/ready` does not verify DB/Redis readiness. | `backend/app/api/routes/health.py:17`, `backend/app/api/routes/health.py:27`, `infra/docker/docker-compose.yml:30` | Platform Settings could show false health. |
| RBAC fallback | Admin without profile is treated as superadmin for compatibility. | `backend/app/api/dependencies.py:89`, `backend/app/api/dependencies.py:99` | Platform Settings must not inherit this fallback blindly. |
| Audit payload display | Admin audit UI can render `payload_json` raw. | `frontend/app/ui/audit/admin-audit-log.tsx:311` | Sensitive settings payloads need redaction before any settings audit view. |
| Site asset paths | Site CMS asset path/base assumptions are partly hardcoded. | `backend/app/modules/platform/site_cms/service.py:986`, `backend/app/modules/platform/site_cms/service.py:993` | Asset storage health must distinguish game assets and site assets. |

## Source-Of-Truth Inventory Contract

Every Platform Settings row must have these fields before it appears in UI:

| Field | Required meaning |
| --- | --- |
| `key` | Stable setting key. |
| `label` | Human-readable name. |
| `source_of_truth` | env, code, db, registry, title_config, document, derived. |
| `owner` | platform, security, finance, game, product, infra. |
| `visibility` | hidden, masked, read_only, editable_future. |
| `risk_class` | low, medium, high, critical. |
| `environment_scope` | local, staging, production, all. |
| `restart_required` | yes/no/unknown. |
| `audit_required` | yes/no/future. |
| `editable_now` | always false for MVP. |
| `masking_rule` | none, full, partial, count_only, hash_only. |
| `evidence` | file:line or document reference. |

No row without this metadata.

## Initial Inventory Matrix

| Key | Source | Owner | Visibility | Risk | Restart | Notes |
| --- | --- | --- | --- | --- | --- | --- |
| `app.name` | env | platform | read_only | low | yes | `APP_NAME`. |
| `app.version` | env/build | platform | read_only | low | yes | Current default is static `0.1.0`. |
| `app.env` | env | infra | read_only | medium | yes | Drives masking posture. |
| `api.v1_prefix` | env | platform | read_only | medium | yes | API routing contract. |
| `database.url` | env | infra/security | hidden | critical | yes | Never display raw. |
| `redis.url` | env | infra/security | hidden | critical | yes | Never display raw. |
| `jwt.secret` | env | security | hidden | critical | yes | Never display hash unless approved. |
| `jwt.access_ttl_minutes` | env | security | read_only | high | yes | Editable only after auth plan. |
| `game_launch.token_ttl_minutes` | env | security/platform | read_only | high | yes | Affects protected game launch. |
| `site_access.password` | env | security | hidden | critical | yes | Never display. |
| `site_access.client_default` | frontend code | security | gap | critical | deploy | Current hardcoded default must be reviewed before settings UI claims security posture. |
| `mines.server_seed` | env | security/fairness | hidden | critical | yes | Unrevealed seed must never be logged/displayed. |
| `cors.allowed_origins` | env | security/infra | masked | high | yes | Local origins can be shown; prod must be stricter. |
| `assets.storage_root` | env | platform/infra | masked | medium | yes | Path can leak host structure. |
| `assets.public_base_url` | env | platform | read_only | medium | yes | Must match static mounts. |
| `access_session.timeout` | code | finance/platform | read_only | critical | deploy | Affects real-money closure. |
| `access_session.sweep_interval` | code | finance/platform | read_only | high | deploy | Background job cadence. |
| `access_session.sweep_limit` | code | finance/platform | read_only | high | deploy | Timeout throughput. |
| `table_session.max_chips` | code | finance/platform | read_only | critical | deploy | Real-money risk. |
| `table_session.default_chips` | code | finance/platform | read_only | critical | deploy | Product asked default/max 100. |
| `demo.token_rate_limit` | code | platform/security | read_only | medium | deploy | Could be editable later. |
| `game_registry.backends` | code/db | platform | read_only | high | deploy/db | Must show registry health. |
| `catalog.publication_flags` | DB/catalog | platform/product | read_only | high | db | Lobby/site visibility flags need health reporting, not global editing. |
| `health.ready_db_redis` | derived | infra | read_only | high | deploy | `/ready` currently does not prove DB/Redis. |
| `error_registry.status` | code | platform/support | read_only | high | deploy | Blocked until CK registry exists. |
| `finance.replay_retention` | document | finance/legal | read_only | high | policy | No deletion job yet. |

## Read-Only Backoffice Shape

MVP navigation:

```text
Admin -> Platform -> Installation Settings
```

Sections:

1. Overview
2. Environment
3. Security-sensitive values
4. Observability status
5. Error Matrix status
6. Finance/replay/retention status
7. Session/table/recovery policy
8. Game registry health
9. Change history

UI rule: read-only values are not disabled inputs. Use definition lists, status
rows, badges and masked text.

## Masking Rules

| Visibility | UI behavior |
| --- | --- |
| `hidden` | Show only "Configured / Missing"; no value, no hash unless approved. |
| `masked` | Show partial safe value, e.g. host only or count of entries. |
| `read_only` | Show value if non-sensitive. |
| `editable_future` | Show value read-only and explain "not editable in MVP". |

Never display:

- JWT secret;
- DB URL credentials;
- Redis credentials;
- site access password;
- unrevealed server seed;
- raw bearer/admin token;
- token query strings.

## Implementation Slices

### Slice S1 - Descriptor Contract Only

- typed descriptor list;
- no UI yet;
- tests for every row requiring owner/source/visibility/risk.
- explicitly classify current conflicts as `gap`, not silently green:
  site access client default, readiness without DB/Redis, RBAC fallback,
  CMS v2 lab token query.

### Slice S2 - Backend Read Model

- superadmin-only endpoint;
- aggregate descriptor statuses;
- no editable payload;
- mask at backend before returning.
- do not rely on "missing admin profile means superadmin" for this endpoint;
  require an explicit superadmin profile or add a CTO-approved compatibility
  exception.

### Slice S3 - Frontend Read-Only UI

- Platform Settings shell;
- no form inputs for critical values;
- no save/publish buttons.

### Slice S4 - Game Registry Health

Show each game:

- backend game code registered;
- frontend player registry present;
- title-editor registry present;
- finance/replay descriptor present;
- error namespace present;
- smoke status if available.

### Slice S5 - Error Matrix Placeholder

Only after Error Registry foundation:

- read-only code table;
- no semantic editing.

## Stop-and-Ask

Stop before code if:

- any setting is requested editable in MVP;
- any secret must be displayed;
- CORS/JWT/session/table limits are requested editable live;
- platform settings route is not superadmin-only;
- UI uses disabled inputs for critical values;
- Error Matrix is requested before the CK registry exists.

## Test Gates

Automated:

- descriptor contract rejects rows missing owner/source/visibility/risk;
- backend masks hidden/masked fields;
- superadmin can read settings;
- non-superadmin cannot read settings;
- no raw secrets in JSON response;
- no raw sensitive values in audit payload rendering;
- no editable controls in MVP page;
- readiness status distinguishes app process from DB/Redis health;
- Error Matrix section hidden/blocked until registry exists.

Manual:

- open `/admin` as superadmin and see read-only settings;
- verify secrets show only configured/missing;
- verify game registry health identifies Mines/BOXE/HI-LO;
- verify no admin can change values from this page.

## CTO Development Recommendation

Start with descriptor contract and backend read model. Do not build a pretty
settings UI first. The dangerous part is classification/masking, not layout.

## Analysis Completeness

Closed for pre-development:

- env/code/registry setting categories;
- source-of-truth row contract;
- hidden/masked/read-only classification;
- high-risk finance/session/table settings;
- superadmin-only requirement;
- Error Matrix dependency;
- implementation sequence;
- gates and Stop-and-Ask.

No further analysis is required before writing the implementation prompt,
unless the CTO asks to make a specific setting editable in MVP.
