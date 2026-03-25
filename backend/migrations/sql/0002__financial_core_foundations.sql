-- CasinoKing financial core foundations
-- Source references:
-- - docs/md/CasinoKing_Documento_05_v3_Wallet_Ledger_Fondamenta_Definitive.md
-- - docs/md/CasinoKing_Documento_11_v2_API_Contract_Allineato_v3.md
-- - docs/md/CasinoKing_Documento_12_v3_Schema_Database_Definitivo.md
-- - docs/md/CasinoKing_Documento_13_v3_SQL_Migrations_Definitivo.md
--
-- Scope of this migration:
-- - create the minimum financial tables already stable in the documents
-- - preserve double-entry foundations and wallet snapshot linkage
-- - defer cross-module foreign keys to the future users/auth schema migration
--
-- Explicitly deferred:
-- - users/auth tables
-- - game/session tables
-- - admin_actions table details
-- - seed data for chart of accounts

BEGIN;

CREATE TABLE ledger_accounts (
    id uuid PRIMARY KEY,
    account_code varchar(128) NOT NULL UNIQUE,
    account_type varchar(64) NOT NULL,
    owner_user_id uuid NULL,
    currency_code varchar(16) NOT NULL,
    status varchar(32) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE wallet_accounts (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    ledger_account_id uuid NOT NULL UNIQUE REFERENCES ledger_accounts(id),
    wallet_type varchar(32) NOT NULL,
    currency_code varchar(16) NOT NULL,
    balance_snapshot numeric(18, 6) NOT NULL DEFAULT 0,
    status varchar(32) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT wallet_accounts_user_wallet_currency_key
        UNIQUE (user_id, wallet_type, currency_code)
);

CREATE TABLE ledger_transactions (
    id uuid PRIMARY KEY,
    user_id uuid NOT NULL,
    transaction_type varchar(64) NOT NULL,
    reference_type varchar(64) NULL,
    reference_id uuid NULL,
    idempotency_key varchar(128) UNIQUE NULL,
    metadata_json jsonb NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE TABLE ledger_entries (
    id uuid PRIMARY KEY,
    transaction_id uuid NOT NULL REFERENCES ledger_transactions(id),
    ledger_account_id uuid NOT NULL REFERENCES ledger_accounts(id),
    entry_side varchar(16) NOT NULL,
    amount numeric(18, 6) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT ledger_entries_entry_side_check
        CHECK (entry_side IN ('debit', 'credit')),
    CONSTRAINT ledger_entries_amount_check
        CHECK (amount > 0)
);

CREATE INDEX idx_wallet_accounts_user_id
    ON wallet_accounts (user_id);

CREATE INDEX idx_ledger_transactions_user_id
    ON ledger_transactions (user_id);

CREATE INDEX idx_ledger_entries_transaction_id
    ON ledger_entries (transaction_id);

CREATE INDEX idx_ledger_entries_ledger_account_id
    ON ledger_entries (ledger_account_id);

COMMIT;
