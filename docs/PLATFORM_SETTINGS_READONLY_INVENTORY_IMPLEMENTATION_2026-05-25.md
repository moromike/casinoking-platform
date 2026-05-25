Status: ACTIVE
Last meaningful update: 2026-05-25

# Platform Settings Read-Only Inventory - Implementation Note

WP: `WP-PLATFORM-SETTINGS-READONLY-INVENTORY`

Scope delivered:

- backend descriptor contract and masked read model;
- explicit-superadmin-only endpoint at `GET /api/v1/admin/platform-settings`;
- backoffice read-only Platform Settings panel with working status/risk/visibility filters;
- bilingual IT/EN row explanations for every setting descriptor;
- bilingual IT/EN category descriptions and gap-risk explanations;
- game registry health from backend `game_codes.py` as MVP source of truth;
- CK.* error matrix read-only view from the WP1 error registry;
- four CTO-mandated gap risk write-ups, now closed at MVP level.

No setting is editable in this WP.

## Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Descriptor contract | n/a | NEW | NEW | read | n/a | n/a | NEW | UPDATE | Complete | Code-backed descriptors with mandatory metadata and evidence. |
| Backend read model superadmin-only | read `admin_profiles` | NEW | NEW | consume | n/a | n/a | NEW | UPDATE | Complete | Requires explicit `admin_profiles.is_superadmin = true`; does not use missing-profile fallback. |
| Frontend Platform Settings UI | n/a | consume | parse | NEW | n/a | NEW | NEW | UPDATE | Complete | Read-only tables, working filters and expandable explanations; no inputs, save, publish or edit controls. |
| Game registry health | n/a | NEW | NEW | NEW | n/a | NEW | NEW | UPDATE | Complete | Backend `game_codes.py` is source of truth; adapter checks can be pending if not detected. |
| Error Matrix placeholder | n/a | NEW | NEW | NEW | n/a | NEW | NEW | UPDATE | Complete | WP1 is present, so CK.* codes are shown read-only. |
| Bilingual descriptor/category explanations | n/a | NEW | NEW | NEW | n/a | NEW | NEW | UPDATE | Complete | Every descriptor, category and gap-risk row has operator-readable Italian and English explanation text. |
| Gap risk closure | n/a | UPDATE | UPDATE | consume | n/a | n/a | NEW | UPDATE | Complete | Four CTO gaps now show closed MVP mitigation and long-term follow-up direction. |

## Gap Risk Write-Up

| Gap | Severity | Impact | MVP mitigation | Long-term mitigation | Follow-up WP |
| --- | --- | --- | --- | --- | --- |
| `site_access.client_default` | Critical | Client-side default access password can leak a credential-like control. | Closed: registration requires an entered access code and no longer embeds a default value. | Replace shared access code with temporary token or server-mediated registration. | `WP-FRONTEND-SECRET-AUDIT` |
| `health.ready_db_redis` | High | `/ready` can be green while DB/Redis are unavailable. | Closed: `/ready` checks app, database and Redis and returns 503 when a dependency is down. | Add deeper dependency telemetry and environment-specific readiness thresholds. | `WP-HEALTH-READINESS-DB-REDIS` |
| `auth.rbac_fallback` | Critical | Missing admin profile is treated as superadmin by legacy dependency. | Closed: admin dependencies require explicit `admin_profiles` rows; missing profile is forbidden. | Add operations repair/report tooling without implicit privilege grants. | `WP-AUTH-RBAC-EXPLICIT-PROFILE` |
| `cms_v2_lab.admin_token_in_query` | High | Admin token can appear in URL history, logs or referrers. | Closed: Site v2 lab opens without putting the admin token in the URL. | Replace with postMessage, one-time server token, or httpOnly cookie flow when CMS v2 is rescued. | `WP-CMS-V2-LAB-TOKEN-HANDOFF` |

## Security Notes

- Hidden values return only `configured: true/false`.
- Masked values return count-only or partial safe display.
- Raw DB URL, Redis URL, JWT secret, site password, Mines server seed and bearer/admin tokens are not returned.
- The endpoint depends on `get_current_user` plus a direct `admin_profiles` lookup, not on `get_current_admin` or `require_admin_area("superadmin")`.
- Global admin dependencies now also reject missing admin profiles instead of promoting them to superadmin.
- The Site v2 lab menu item no longer appends the admin token to the query string.

## Residual Scope

- No settings edit flow.
- No audit log for future settings changes.
- CMS v2 still needs a real secure auth handoff when the lab/rescue scope reopens.
- No manual smoke status feed for per-game health.
- Payout runtime sources are not yet conceptually uniform: Mines points to the
  historical payout-runtime JSON annex, while BOXE and HI-LO point to their
  `math.py` runtime code. This is acceptable as read-only evidence today, but
  finance/replay should get a per-game runtime descriptor contract before
  COINS goes live.
