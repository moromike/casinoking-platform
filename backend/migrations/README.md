# Migrations

This directory is reserved for database migrations.

Current status:
- schema design follows Documento 05 v3, Documento 12 v3 and Documento 13 v3
- the current migrations introduce the minimum users/auth and financial-core tables
- the initial chart of accounts is seeded for system accounts
- the base Mines game_sessions table is present
- Mines fairness seed metadata is now persisted with nonce + server_seed_hash
- Mines fairness seed rotations are now persisted for internal/admin rotate flows
- the admin_actions audit nucleus is present for manual financial operations
- no database business logic is being implemented in this pass

Still intentionally deferred:
- reveal/cashout specific game-session hardening
- audit_event table details beyond admin_actions
- JWT/session persistence
- password reset delivery flow
- gameplay and non-MVP admin posting flows
