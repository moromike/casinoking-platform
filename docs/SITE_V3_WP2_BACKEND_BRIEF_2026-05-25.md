Status: ACTIVE
Last meaningful update: 2026-05-25

# Site V3 - WP2 Backend MVP Brief Parte A

## 0. Executive Verdict

WP2 puo' essere implementato dopo review CTO, ma non prima. Questo brief fissa
DDL, API, validation, errori, audit, RBAC, test plan e ownership codice per il
Backend MVP Site V3.

Scope Parte A:

- documento only;
- nessuna migration creata;
- nessuna route Python creata;
- nessun service/repository/validator creato;
- `cms_v2_*` non toccato;
- V1 e runtime giochi non toccati.

Decisioni lockate usate:

- nuove tabelle `site_v3_pages`, `site_v3_page_versions`, `site_v3_modules`;
- `cms_v2_*` dormienti;
- app pubblica futura `frontend-v3/`;
- i18n model con `locale` da subito, content MVP solo `it`;
- snapshot published + history list in admin, revert UI Phase 2;
- audit tramite audit admin esistente, niente tabella dedicata.

## 1. DDL Completo Migration

Numero migration proposto: `backend/migrations/sql/0045__site_v3_persistence.sql`.

Nota naming audit: il prompt usa il nome concettuale `admin_audit_events`, ma
nel codice reale la tabella esistente si chiama `admin_audit_log`
(`backend/migrations/sql/0030__admin_audit_log.sql`). WP2 deve riusare
`admin_audit_log`, rappresentando la sorgente Site V3 con
`payload_json.source = "site_v3"` e action/resource kind dedicati, senza creare
una nuova tabella audit.

### 1.1 Forward SQL

```sql
-- Site V3 - Persistence for modular public site.
--
-- Scope:
-- - introduce Site V3 pages with locale-aware identity
-- - introduce immutable page versions for draft/published history
-- - introduce draft modules attached to pages
-- - keep cms_v2_* dormant and untouched

BEGIN;

CREATE TABLE site_v3_pages (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    site_code varchar(32) NOT NULL REFERENCES sites(site_code),
    page_code varchar(64) NOT NULL,
    locale varchar(8) NOT NULL DEFAULT 'it',
    title varchar(160) NOT NULL,
    status varchar(16) NOT NULL DEFAULT 'draft',
    draft_version integer NOT NULL DEFAULT 0,
    published_version integer NULL,
    created_by uuid NOT NULL REFERENCES users(id),
    updated_by uuid NOT NULL REFERENCES users(id),
    archived_by uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    archived_at timestamptz NULL,
    CONSTRAINT site_v3_pages_page_code_not_blank_check
        CHECK (length(btrim(page_code)) > 0),
    CONSTRAINT site_v3_pages_page_code_format_check
        CHECK (page_code ~ '^[a-z0-9][a-z0-9_-]{1,63}$'),
    CONSTRAINT site_v3_pages_locale_check
        CHECK (locale IN ('it', 'en', 'de', 'es')),
    CONSTRAINT site_v3_pages_title_not_blank_check
        CHECK (length(btrim(title)) > 0),
    CONSTRAINT site_v3_pages_status_check
        CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT site_v3_pages_draft_version_check
        CHECK (draft_version >= 0),
    CONSTRAINT site_v3_pages_published_version_check
        CHECK (published_version IS NULL OR published_version > 0),
    CONSTRAINT site_v3_pages_archive_consistency_check
        CHECK (
            (status = 'archived' AND archived_at IS NOT NULL)
            OR (status <> 'archived')
        )
);

CREATE UNIQUE INDEX idx_site_v3_pages_site_page_locale
    ON site_v3_pages (site_code, page_code, locale);

CREATE INDEX idx_site_v3_pages_site_status_updated
    ON site_v3_pages (site_code, status, updated_at DESC);

CREATE INDEX idx_site_v3_pages_site_locale_status
    ON site_v3_pages (site_code, locale, status);

CREATE TABLE site_v3_page_versions (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id uuid NOT NULL REFERENCES site_v3_pages(id) ON DELETE CASCADE,
    version integer NOT NULL,
    status varchar(16) NOT NULL,
    snapshot_json jsonb NOT NULL,
    validation_json jsonb NOT NULL DEFAULT '{"status":"unknown","issues":[]}'::jsonb,
    created_by uuid NOT NULL REFERENCES users(id),
    published_by uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    published_at timestamptz NULL,
    CONSTRAINT site_v3_page_versions_version_check
        CHECK (version > 0),
    CONSTRAINT site_v3_page_versions_status_check
        CHECK (status IN ('draft', 'published', 'archived')),
    CONSTRAINT site_v3_page_versions_snapshot_object_check
        CHECK (jsonb_typeof(snapshot_json) = 'object'),
    CONSTRAINT site_v3_page_versions_validation_object_check
        CHECK (jsonb_typeof(validation_json) = 'object'),
    CONSTRAINT site_v3_page_versions_publish_consistency_check
        CHECK (
            (status = 'published' AND published_at IS NOT NULL AND published_by IS NOT NULL)
            OR (status <> 'published')
        )
);

CREATE UNIQUE INDEX idx_site_v3_page_versions_page_version
    ON site_v3_page_versions (page_id, version);

CREATE INDEX idx_site_v3_page_versions_page_status_version
    ON site_v3_page_versions (page_id, status, version DESC);

CREATE INDEX idx_site_v3_page_versions_published_at
    ON site_v3_page_versions (published_at DESC)
    WHERE status = 'published';

CREATE TABLE site_v3_modules (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    page_id uuid NOT NULL REFERENCES site_v3_pages(id) ON DELETE CASCADE,
    module_code varchar(64) NOT NULL,
    schema_version integer NOT NULL DEFAULT 1,
    slot_key varchar(64) NOT NULL DEFAULT 'main',
    sort_order integer NOT NULL DEFAULT 0,
    config_json jsonb NOT NULL DEFAULT '{}'::jsonb,
    created_by uuid NOT NULL REFERENCES users(id),
    updated_by uuid NOT NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    updated_at timestamptz NOT NULL DEFAULT NOW(),
    CONSTRAINT site_v3_modules_module_code_not_blank_check
        CHECK (length(btrim(module_code)) > 0),
    CONSTRAINT site_v3_modules_module_code_format_check
        CHECK (module_code ~ '^[a-z0-9][a-z0-9_]{1,63}$'),
    CONSTRAINT site_v3_modules_schema_version_check
        CHECK (schema_version > 0),
    CONSTRAINT site_v3_modules_slot_key_not_blank_check
        CHECK (length(btrim(slot_key)) > 0),
    CONSTRAINT site_v3_modules_slot_key_format_check
        CHECK (slot_key ~ '^[a-z0-9][a-z0-9_-]{0,63}$'),
    CONSTRAINT site_v3_modules_sort_order_check
        CHECK (sort_order >= 0),
    CONSTRAINT site_v3_modules_config_object_check
        CHECK (jsonb_typeof(config_json) = 'object')
);

CREATE UNIQUE INDEX idx_site_v3_modules_page_slot_sort_order
    ON site_v3_modules (page_id, slot_key, sort_order);

CREATE INDEX idx_site_v3_modules_page_slot
    ON site_v3_modules (page_id, slot_key, sort_order ASC);

CREATE INDEX idx_site_v3_modules_module_code
    ON site_v3_modules (module_code, schema_version);

COMMIT;
```

### 1.2 Rollback Plan

Rollback SQL, in reverse dependency order:

```sql
BEGIN;

DROP TABLE IF EXISTS site_v3_modules;
DROP TABLE IF EXISTS site_v3_page_versions;
DROP TABLE IF EXISTS site_v3_pages;

COMMIT;
```

Rollback note:

- safe before WP3/WP4 consume the tables;
- after published content exists, rollback must first export snapshots or be
  treated as data-destructive and require CTO approval;
- `cms_v2_*` is never modified by this migration, so no CMS v2 rollback step is
  needed.

## 2. API Surface Admin

All admin endpoints use the platform envelope:

```json
{
  "success": true,
  "data": {}
}
```

All errors use the WP1 foundation envelope with `error.code`, `support_id`,
`request_id`, and `retryable` where applicable.

Admin dependency target: `require_admin_area("site")` if the admin profile area
exists in the environment. If not, the CTO must choose between adding the `site`
area in WP2 or temporarily using `require_admin_area("games")` as a documented
compatibility bridge. Recommendation: add/use explicit `site`; do not rely on
implicit superadmin fallback.

### 2.1 GET `/admin/site-v3/sites/{site_code}/pages`

Purpose: list Site V3 pages for a site.

Query:

```json
{
  "locale": "it",
  "status": "draft|published|archived|all",
  "page": 1,
  "limit": 50
}
```

Response:

```json
{
  "success": true,
  "data": {
    "site_code": "casinoking",
    "pages": [
      {
        "id": "uuid",
        "site_code": "casinoking",
        "page_code": "home",
        "locale": "it",
        "title": "Homepage",
        "status": "published",
        "draft_version": 3,
        "published_version": 2,
        "updated_at": "2026-05-25T10:00:00Z",
        "created_at": "2026-05-25T09:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total_items": 1,
      "total_pages": 1
    }
  }
}
```

### 2.2 GET `/admin/site-v3/sites/{site_code}/pages/{page_code}`

Purpose: return page draft, modules and published summary for admin editor.

Query:

```json
{
  "locale": "it"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "page": {
      "id": "uuid",
      "site_code": "casinoking",
      "page_code": "home",
      "locale": "it",
      "title": "Homepage",
      "status": "draft",
      "draft_version": 4,
      "published_version": 3,
      "updated_at": "2026-05-25T10:10:00Z"
    },
    "modules": [
      {
        "id": "uuid",
        "module_code": "hero_banner",
        "schema_version": 1,
        "slot_key": "main",
        "sort_order": 0,
        "config": {
          "headline": "CasinoKing",
          "cta": {"label": "Gioca ora", "target_type": "game_grid"}
        }
      }
    ],
    "published": {
      "version": 3,
      "published_at": "2026-05-25T10:00:00Z",
      "published_by": "uuid"
    },
    "validation": {
      "status": "valid",
      "issues": []
    }
  }
}
```

### 2.3 PUT `/admin/site-v3/sites/{site_code}/pages/{page_code}/draft`

Purpose: create or update the draft page and its draft modules. This must not
change the public response.

Payload:

```json
{
  "locale": "it",
  "title": "Homepage",
  "modules": [
    {
      "id": "optional-existing-uuid",
      "module_code": "hero_banner",
      "schema_version": 1,
      "slot_key": "main",
      "sort_order": 0,
      "config": {
        "headline": "CasinoKing"
      }
    }
  ]
}
```

Response:

```json
{
  "success": true,
  "data": {
    "page": {
      "id": "uuid",
      "site_code": "casinoking",
      "page_code": "home",
      "locale": "it",
      "title": "Homepage",
      "status": "draft",
      "draft_version": 5,
      "published_version": 3
    },
    "validation": {
      "status": "valid",
      "issues": []
    }
  }
}
```

Implementation note: full replacement of module rows is acceptable for MVP if
performed transactionally and recorded in audit. Module IDs should remain stable
when client sends existing IDs and ordering changes only.

### 2.4 POST `/admin/site-v3/sites/{site_code}/pages/{page_code}/validate`

Purpose: run validation without saving or publishing.

Payload:

```json
{
  "locale": "it",
  "title": "Homepage",
  "modules": [
    {
      "module_code": "game_grid",
      "schema_version": 1,
      "slot_key": "main",
      "sort_order": 1,
      "config": {"layout": "featured_first"}
    }
  ]
}
```

Response:

```json
{
  "success": true,
  "data": {
    "validation": {
      "status": "invalid",
      "issues": [
        {
          "severity": "error",
          "module_id": null,
          "field": "headline",
          "code": "SITEV3.VALIDATION.REQUIRED",
          "message": "Headline is required"
        }
      ]
    }
  }
}
```

### 2.5 POST `/admin/site-v3/sites/{site_code}/pages/{page_code}/publish`

Purpose: validate current draft, create a published snapshot/version, update
`published_version`, and make the public API serve the new snapshot.

Payload:

```json
{
  "locale": "it",
  "expected_draft_version": 5
}
```

Response:

```json
{
  "success": true,
  "data": {
    "page": {
      "site_code": "casinoking",
      "page_code": "home",
      "locale": "it",
      "status": "published",
      "draft_version": 5,
      "published_version": 6
    },
    "version": {
      "id": "uuid",
      "version": 6,
      "status": "published",
      "published_at": "2026-05-25T10:30:00Z",
      "published_by": "uuid"
    }
  }
}
```

If validation fails, return HTTP 422 with
`SITEV3.PUBLISH.VALIDATION_FAILED` and validation issues in `details`.

### 2.6 POST `/admin/site-v3/sites/{site_code}/pages/{page_code}/archive`

Purpose: archive page so public API no longer serves it. This is the MVP
alternative to destructive delete.

Payload:

```json
{
  "locale": "it",
  "reason": "retired by operator"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "page": {
      "site_code": "casinoking",
      "page_code": "home",
      "locale": "it",
      "status": "archived",
      "archived_at": "2026-05-25T10:40:00Z",
      "archived_by": "uuid"
    }
  }
}
```

### 2.7 GET `/admin/site-v3/sites/{site_code}/pages/{page_code}/versions`

Purpose: list page history. Revert UI is Phase 2; MVP only lists.

Query:

```json
{
  "locale": "it",
  "page": 1,
  "limit": 50
}
```

Response:

```json
{
  "success": true,
  "data": {
    "versions": [
      {
        "id": "uuid",
        "version": 6,
        "status": "published",
        "validation": {"status": "valid", "issues": []},
        "created_at": "2026-05-25T10:30:00Z",
        "published_at": "2026-05-25T10:30:00Z",
        "published_by": "uuid"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 50,
      "total_items": 1,
      "total_pages": 1
    }
  }
}
```

### 2.8 Asset Endpoint Decision

Decision: do not add a dedicated Site V3 asset endpoint in WP2.

Rationale:

- WP1 locked no Site V3 dedicated asset table;
- existing platform already has site assets and title assets patterns;
- modules should store asset references in config, not binary payloads;
- upload/list/picker UX belongs to WP3 admin builder or a focused asset WP.

Recommended MVP contract:

- module config can contain `asset_ref`:

```json
{
  "asset_ref": {
    "asset_id": "uuid",
    "asset_kind": "site_v3_hero_media"
  }
}
```

- WP2 validation supports asset checks via adapter interface, but if the
  concrete Site V3 asset kinds are not yet wired, validation returns a warning,
  not a blocking error, unless the module manifest marks the asset as required.

Open risk for CTO: existing site asset API currently targets `homepage_banner`.
Before WP3 upload UI, either extend existing site asset kinds or introduce a
platform-wide site asset registry adapter. Do not create a Site V3-specific
asset table in WP2.

## 3. API Surface Public

Public APIs:

- must never accept or require admin token;
- must be served from service methods that enforce published-only;
- must not rely on route-only filtering;
- must not expose draft modules, draft versions, validation internals, admin
  user IDs or unpublished pages.

### 3.1 GET `/site-v3/sites/{site_code}/pages/{page_code}`

Query:

```json
{
  "locale": "it"
}
```

Response:

```json
{
  "success": true,
  "data": {
    "site_code": "casinoking",
    "page_code": "home",
    "locale": "it",
    "title": "Homepage",
    "published_version": 6,
    "published_at": "2026-05-25T10:30:00Z",
    "modules": [
      {
        "module_code": "hero_banner",
        "schema_version": 1,
        "slot_key": "main",
        "sort_order": 0,
        "config": {
          "headline": "CasinoKing"
        }
      }
    ]
  }
}
```

If no published snapshot exists, return HTTP 404
`SITEV3.PAGE.NOT_PUBLISHED`.

### 3.2 GET `/site-v3/sites/{site_code}/navigation`

Purpose: return published navigation/header/footer data for the renderer.

MVP behavior:

- load from published `global_header` and `global_footer` modules on `home`;
- if missing, return safe empty navigation with status `partial`;
- never read draft rows.

Response:

```json
{
  "success": true,
  "data": {
    "site_code": "casinoking",
    "locale": "it",
    "status": "partial",
    "header": null,
    "footer": null
  }
}
```

### 3.3 GET `/site-v3/sites/{site_code}/manifest`

Purpose: expose public renderer metadata.

Response:

```json
{
  "success": true,
  "data": {
    "site_code": "casinoking",
    "locales": ["it"],
    "default_locale": "it",
    "pages": [
      {
        "page_code": "home",
        "locale": "it",
        "title": "Homepage",
        "published_version": 6,
        "updated_at": "2026-05-25T10:30:00Z"
      }
    ]
  }
}
```

## 4. Error Code Registry `SITEV3.*`

WP2 must add Site V3 definitions to the existing AppError/registry foundation
documented in `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_APPROACH_2026-05-25.md`.

Required codes:

| Code | HTTP | Retryable | Meaning |
| --- | --- | --- | --- |
| `SITEV3.VALIDATION.REQUIRED` | 422 | false | Required module/page field missing. |
| `SITEV3.VALIDATION.UNKNOWN_MODULE` | 422 | false | Module code is not in registry. |
| `SITEV3.VALIDATION.UNKNOWN_TITLE` | 422 | false | Referenced `title_code` is unknown or unavailable for site. |
| `SITEV3.VALIDATION.UNSAFE_HTML` | 422 | false | Rich text contains unsafe HTML or attributes. |
| `SITEV3.PAGE.NOT_FOUND` | 404 | false | Admin/public page identity does not exist. |
| `SITEV3.PAGE.NOT_PUBLISHED` | 404 | false | Page exists but has no published snapshot. |
| `SITEV3.PAGE.DUPLICATE_CODE` | 409 | false | `(site_code, page_code, locale)` conflicts. |
| `SITEV3.RBAC.FORBIDDEN` | 403 | false | Admin has no explicit Site V3 area access. |
| `SITEV3.PUBLISH.VALIDATION_FAILED` | 422 | false | Publish blocked by validation errors. |

Envelope shape:

```json
{
  "success": false,
  "error": {
    "code": "SITEV3.PUBLISH.VALIDATION_FAILED",
    "message": "Page validation failed",
    "details": {
      "validation": {
        "status": "invalid",
        "issues": []
      }
    },
    "support_id": "request-id",
    "request_id": "request-id",
    "retryable": false
  }
}
```

Do not collapse Site V3 validation failures back to legacy
`VALIDATION_ERROR`.

## 5. Validation Engine

Ownership target:

```text
backend/app/modules/platform/site_v3/validation/
backend/app/modules/platform/site_v3/manifests/
```

Validation output:

```json
{
  "status": "valid|invalid",
  "issues": [
    {
      "severity": "error|warning",
      "module_id": "uuid-or-client-temp-id-or-null",
      "field": "headline",
      "code": "SITEV3.VALIDATION.REQUIRED",
      "message": "Headline is required"
    }
  ]
}
```

Blocking errors:

- unknown module code;
- unsupported schema version;
- required field empty;
- required asset missing;
- referenced title unknown/not available for site;
- unsafe rich text;
- duplicate route/page code;
- invalid or unsupported locale.

Warnings:

- image below recommended dimensions;
- copy very short;
- CTA missing where optional;
- module suboptimal on mobile;
- asset adapter not yet wired for optional visual asset.

Registry pattern:

```text
ModuleManifest
  module_code
  schema_version
  fields[]
  validate(config, context) -> issues[]
```

Each MVP module gets one manifest and one validation function. The Site V3
service calls the module registry; route handlers do not validate module
internals directly.

## 6. Audit Integration

Decision: no dedicated Site V3 audit table.

Existing implementation target: `admin_audit_log` via
`record_audit_entry(...)`.

Conceptual mapping requested by product:

| Site V3 event | `action_kind` | `resource_kind` | `resource_id` |
| --- | --- | --- | --- |
| page_create | `site_v3.page_create` | `site_v3_page` | `{site_code}:{page_code}:{locale}` |
| save_draft | `site_v3.save_draft` | `site_v3_page` | `{site_code}:{page_code}:{locale}` |
| validate | `site_v3.validate` | `site_v3_page` | `{site_code}:{page_code}:{locale}` |
| publish | `site_v3.publish` | `site_v3_page` | `{site_code}:{page_code}:{locale}` |
| archive | `site_v3.archive` | `site_v3_page` | `{site_code}:{page_code}:{locale}` |

Payload minimum:

```json
{
  "source": "site_v3",
  "actor": {
    "admin_user_id": "uuid"
  },
  "request_id": "request-id",
  "support_id": "request-id",
  "site_code": "casinoking",
  "page_code": "home",
  "locale": "it",
  "draft_version": 5,
  "published_version": 6,
  "version_id": "uuid",
  "validation_status": "valid"
}
```

`request_fingerprint` should use existing `build_audit_request_fingerprint`.
If CTO requires a physical `source` column on audit, that is a separate
platform audit enhancement, not WP2 MVP.

## 7. RBAC

Required:

- explicit admin profile required;
- no fallback "missing profile = superadmin";
- admin routes use admin dependency;
- public routes use no admin dependency and reject no-user assumptions;
- public service methods enforce published-only.

Recommended area:

- target area: `site`;
- if current admin profiles do not seed/support `site`, WP2 brief review must
  decide whether to add area support in WP2 or temporarily map Site V3 to the
  existing `games` area.

Preferred CTO answer: add/use explicit `site` area. Temporary `games` reuse is
acceptable only as a documented compatibility bridge with a follow-up.

Rate limit / abuse:

- admin mutation endpoints rely on authenticated admin access in MVP;
- public endpoints should be cache-friendly and read-only;
- if generic rate limiting exists before implementation, include public Site V3
  reads in it; do not invent custom rate limiting in WP2.

## 8. Test Plan

### 8.1 Backend Gate Tests

| Gate | Test |
| --- | --- |
| Draft save does not modify public | Save draft, call public page before publish, verify previous published version or `SITEV3.PAGE.NOT_PUBLISHED`. |
| Public returns only published | Create page/draft only, public returns 404 `SITEV3.PAGE.NOT_PUBLISHED`. |
| Publish creates snapshot | Save valid draft, publish, verify `site_v3_page_versions` row and public payload uses snapshot. |
| Validation blocks publish | Save invalid draft, publish returns 422 `SITEV3.PUBLISH.VALIDATION_FAILED`; no published version change. |
| Unknown module blocked | Validate module `not_real`, expect `SITEV3.VALIDATION.UNKNOWN_MODULE`. |
| Unknown title blocked | Validate game module referencing hidden/unknown title, expect `SITEV3.VALIDATION.UNKNOWN_TITLE`. |
| Unsafe HTML blocked | Validate rich text with script/event handler, expect `SITEV3.VALIDATION.UNSAFE_HTML`. |
| Audit every mutation | page_create/save_draft/publish/archive insert `admin_audit_log` event. |
| RBAC enforced | Missing admin profile or no `site` area returns 403 `SITEV3.RBAC.FORBIDDEN` or `CK.AUTH.FORBIDDEN` with Site V3 mapping. |
| `cms_v2` unchanged | Existing cms_v2 tests still pass; no rows/tables mutated by Site V3 tests. |

### 8.2 Fixtures / Factories

Needed:

- active `sites.site_code = casinoking`;
- admin user with explicit admin profile and Site V3 area;
- non-admin player user;
- visible game title for `game_grid` / `featured_game` validation;
- hidden/archived title for negative validation;
- Site V3 page factory;
- module payload factory for all 7 MVP modules.

### 8.3 Smoke Tests

Minimum smoke:

1. admin creates/saves home draft;
2. admin validates draft;
3. admin publishes home;
4. public reads home;
5. admin archives home;
6. public no longer reads home.

### 8.4 Contract Tests

Contract tests must assert:

- exact endpoint URLs;
- envelope shape;
- error code preservation;
- `request_id` / `support_id` presence on errors;
- public payload excludes admin-only fields;
- public service does not expose draft when called directly, not only via route.

## 9. Strategia Ownership Codice

Recommended code ownership for Parte B:

```text
backend/app/api/routes/site_v3_admin.py
backend/app/api/routes/site_v3_public.py
backend/app/modules/platform/site_v3/__init__.py
backend/app/modules/platform/site_v3/service.py
backend/app/modules/platform/site_v3/repository.py
backend/app/modules/platform/site_v3/validation/__init__.py
backend/app/modules/platform/site_v3/validation/engine.py
backend/app/modules/platform/site_v3/manifests/__init__.py
backend/app/modules/platform/site_v3/manifests/modules.py
backend/migrations/sql/0045__site_v3_persistence.sql
tests/integration/test_site_v3_backend.py
tests/contract/test_site_v3_public_published_only.py
```

Router registration:

- add admin router to API router only in Parte B;
- add public router to API router only in Parte B;
- do not modify `backend/app/api/routes/cms_v2.py`.

## 10. Effort Stimato Parte B E Sequenza Commit

Effort Parte B stimato: 10-16 prompt.

Recommended commit sequence:

1. `feat(site-v3): add backend persistence schema`
2. `feat(site-v3): add module manifests and validation engine`
3. `feat(site-v3): add admin repository and service`
4. `feat(site-v3): expose admin backend endpoints`
5. `feat(site-v3): expose published-only public endpoints`
6. `test(site-v3): cover draft publish validation and rbac gates`
7. `docs(site-v3): update backend capability matrix after wp2`

Merge gate:

- backend tests green;
- cms_v2 tests green;
- public published-only contract green;
- AppError envelope green;
- no frontend/runtime changes.

## 11. Rischi E Open Questions

| Rischio / domanda | Gravita' | Recommendation |
| --- | --- | --- |
| Audit table naming mismatch: prompt says `admin_audit_events`, repo has `admin_audit_log`. | Medium | Treat `admin_audit_events` as conceptual name; use `admin_audit_log` with `payload_json.source='site_v3'`. |
| RBAC area `site` may not exist in seeded admin profiles. | Medium | Prefer adding/supporting explicit `site`; temporary `games` bridge only with CTO approval. |
| Asset endpoint not in WP2 may defer full hero/promo validation. | Low/Medium | WP2 validates references via adapter; upload/picker belongs WP3 or focused asset WP. |
| Unique `(page_id, slot_key, sort_order)` can make reorder updates require transaction discipline. | Low | Repository should replace/reorder modules transactionally. |
| `status` on page and versions can drift if publish/archive is not transactional. | Medium | Service layer must wrap save/publish/archive in DB transactions. |
| Rich text sanitization location must be server-side or validation-enforced. | High | Do not rely on frontend-only sanitization. |

No Stop-and-Ask blocks Parte A. Parte B must wait for CTO review/approval.

