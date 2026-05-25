Status: ACTIVE
Last meaningful update: 2026-05-25

# Platform Replay Retention Policy - MVP

Scope: player/admin replay payloads and game audit payloads used to explain a
round visually. This policy does not change ledger/accounting retention.

## MVP Policy

| Area | MVP decision |
| --- | --- |
| Replay online window | 30 days rolling online availability target. |
| Cold storage | TBD by product/legal before production. |
| Ledger/accounting records | Persist forever in MVP; legal retention decision is future scope. |
| Deletion job | Not implemented in MVP. |
| Historical migration | None. Existing replay rows remain as-is. |

## Operational Notes

- The 30-day online window is a product visibility target, not permission to
  delete financial evidence.
- Backoffice pagination and "latest rows" limits are display limits only.
- Any physical deletion, archival job, anonymization, or cold-storage move needs
  a separate legal/product-approved WP.
- Unknown game replay behavior is unavailable-by-design: the platform must not
  route a game to another game's replay viewer as a fallback.

## Settings Dependency

Platform Settings may expose this as read-only inventory later. This WP only
documents the policy and keeps runtime behavior non-destructive.
