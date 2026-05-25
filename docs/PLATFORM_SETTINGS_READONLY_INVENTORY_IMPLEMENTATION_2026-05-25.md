Status: ACTIVE
Last meaningful update: 2026-05-25

# Platform Settings Read-Only Inventory - Implementation Note

WP: `WP-PLATFORM-SETTINGS-READONLY-INVENTORY`

Scope delivered:

- backend descriptor contract and masked read model;
- explicit-superadmin-only endpoint at `GET /api/v1/admin/platform-settings`;
- backoffice read-only Platform Settings panel;
- game registry health from backend `game_codes.py` as MVP source of truth;
- CK.* error matrix read-only view from the WP1 error registry;
- four CTO-mandated gap risk write-ups.

No setting is editable in this WP.

## Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Descriptor contract | n/a | NEW | NEW | read | n/a | n/a | NEW | UPDATE | Complete | Code-backed descriptors with mandatory metadata and evidence. |
| Backend read model superadmin-only | read `admin_profiles` | NEW | NEW | consume | n/a | n/a | NEW | UPDATE | Complete | Requires explicit `admin_profiles.is_superadmin = true`; does not use missing-profile fallback. |
| Frontend Platform Settings UI | n/a | consume | parse | NEW | n/a | NEW | NEW | UPDATE | Complete | Read-only tables and status rows; no inputs, save, publish or edit controls. |
| Game registry health | n/a | NEW | NEW | NEW | n/a | NEW | NEW | UPDATE | Complete | Backend `game_codes.py` is source of truth; adapter checks can be pending if not detected. |
| Error Matrix placeholder | n/a | NEW | NEW | NEW | n/a | NEW | NEW | UPDATE | Complete | WP1 is present, so CK.* codes are shown read-only. |
| Gap risk write-up | n/a | NEW | NEW | NEW | n/a | n/a | NEW | UPDATE | Complete | Four CTO gaps include severity, impact, MVP mitigation and follow-up WP. |

## Gap Risk Write-Up

| Gap | Severity | Impact | MVP mitigation | Long-term mitigation | Follow-up WP |
| --- | --- | --- | --- | --- | --- |
| `site_access.client_default` | Critical | Client-side default access password can leak a credential-like control. | Show as critical gap only; no registration flow fix in this WP. | Remove client-side default and use temporary token or server-mediated registration. | `WP-FRONTEND-SECRET-AUDIT` |
| `health.ready_db_redis` | High | `/ready` can be green while DB/Redis are unavailable. | Show as high gap only; do not change health behavior here. | Add DB/Redis dependency checks to readiness. | `WP-HEALTH-READINESS-DB-REDIS` |
| `auth.rbac_fallback` | Critical | Missing admin profile is treated as superadmin by legacy dependency. | Settings endpoint requires explicit superadmin profile. | Remove fallback and require explicit profiles globally. | `WP-AUTH-RBAC-EXPLICIT-PROFILE` |
| `cms_v2_lab.admin_token_in_query` | High | Admin token can appear in URL history, logs or referrers. | Show as high gap only; no CMS lab handoff fix in this WP. | Replace query token with postMessage, one-time handoff token, or httpOnly cookie flow. | `WP-CMS-V2-LAB-TOKEN-HANDOFF` |

## Security Notes

- Hidden values return only `configured: true/false`.
- Masked values return count-only or partial safe display.
- Raw DB URL, Redis URL, JWT secret, site password, Mines server seed and bearer/admin tokens are not returned.
- The endpoint depends on `get_current_user` plus a direct `admin_profiles` lookup, not on `get_current_admin` or `require_admin_area("superadmin")`.

## Residual Scope

- No settings edit flow.
- No audit log for future settings changes.
- No DB/Redis readiness fix.
- No global RBAC fallback fix.
- No CMS v2 lab token handoff fix.
- No manual smoke status feed for per-game health.
