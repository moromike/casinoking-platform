# SQL Migrations

SQL-first migration scaffold aligned with Documento 12 v3 and Documento 13 v3.

Current intent:
- keep migrations explicit and reviewable
- preserve a conservative path for financial tables
- avoid inventing schema details before the target model is implemented

Planned categories:
- base platform tables
- financial core tables
- game/session tables
- indexes, constraints, and reconciliation helpers

Status:
- bootstrap stage with first real financial-core migration started
- current implemented nucleus:
  - users
  - user_credentials
  - password_reset_tokens
  - ledger_accounts
  - wallet_accounts
  - ledger_transactions
  - ledger_entries
  - system ledger account seed
  - game_sessions base table
  - game_sessions seeded fairness nonce + server_seed_hash
  - fairness_seed_rotations for Mines internal seed rotation
  - admin_actions base audit table
- intentionally deferred:
  - reveal/cashout specific DB hardening
  - audit_event table details beyond admin_actions
  - JWT/session persistence
  - password reset delivery flow
  - gameplay and non-MVP admin runtime business flows
