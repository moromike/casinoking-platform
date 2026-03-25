-- CasinoKing users and auth foundations
-- Source references:
-- - docs/md/CasinoKing_Documento_00_FINALE.md
-- - docs/md/CasinoKing_Documento_03_Architettura_DB_API.md
-- - docs/md/CasinoKing_Documento_11_v2_API_Contract_Allineato_v3.md
-- - docs/md/CasinoKing_Documento_15_Piano_Implementazione.md
--
-- Scope of this migration:
-- - create the minimum users/auth tables required by the MVP backbone
-- - add the user foreign keys that were intentionally deferred in the
--   financial-core migration
--
-- Explicitly deferred:
-- - JWT/session persistence
-- - email verification
-- - rate limiting tables
-- - admin audit tables

BEGIN;

CREATE TABLE users (
    id uuid PRIMARY KEY,
    email varchar(320) NOT NULL UNIQUE,
    role varchar(32) NOT NULL,
    status varchar(32) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT users_role_check
        CHECK (role IN ('player', 'admin')),
    CONSTRAINT users_status_check
        CHECK (status IN ('active', 'suspended'))
);

CREATE TABLE user_credentials (
    user_id uuid PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    password_hash varchar(255) NOT NULL,
    password_updated_at timestamptz NOT NULL DEFAULT now(),
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE password_reset_tokens (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    token_hash varchar(255) NOT NULL UNIQUE,
    expires_at timestamptz NOT NULL,
    consumed_at timestamptz NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

ALTER TABLE ledger_accounts
    ADD CONSTRAINT ledger_accounts_owner_user_id_fkey
    FOREIGN KEY (owner_user_id) REFERENCES users(id);

ALTER TABLE wallet_accounts
    ADD CONSTRAINT wallet_accounts_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id);

ALTER TABLE ledger_transactions
    ADD CONSTRAINT ledger_transactions_user_id_fkey
    FOREIGN KEY (user_id) REFERENCES users(id);

CREATE INDEX idx_password_reset_tokens_user_id
    ON password_reset_tokens (user_id);

CREATE INDEX idx_password_reset_tokens_expires_at
    ON password_reset_tokens (expires_at);

COMMIT;
