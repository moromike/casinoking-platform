-- CasinoKing admin actions and manual adjustment foundations
-- Source references:
-- - docs/md/CasinoKing_Documento_03_Architettura_DB_API.md
-- - docs/md/CasinoKing_Documento_05_v3_Wallet_Ledger_Fondamenta_Definitive.md
-- - docs/md/CasinoKing_Documento_11_v2_API_Contract_Allineato_v3.md
-- - docs/md/CasinoKing_Documento_15_Piano_Implementazione.md
--
-- Scope of this migration:
-- - create the minimum admin_actions audit table required by M6
-- - support idempotent admin adjustments and bonus grants
--
-- Document ambiguity handled conservatively:
-- - Documento 05 mentions admin_action + audit_event, but the current
--   canonical mirrors do not define a concrete audit_events table yet.
--   This migration introduces admin_actions as the persisted audit nucleus
--   without inventing a second audit table.

BEGIN;

CREATE TABLE admin_actions (
    id uuid PRIMARY KEY,
    admin_user_id uuid NOT NULL REFERENCES users(id),
    target_user_id uuid NOT NULL REFERENCES users(id),
    action_type varchar(64) NOT NULL,
    wallet_type varchar(32) NOT NULL,
    direction varchar(16) NOT NULL,
    amount numeric(18, 6) NOT NULL,
    reason varchar(255) NOT NULL,
    wallet_balance_after numeric(18, 6) NOT NULL,
    ledger_transaction_id uuid NOT NULL REFERENCES ledger_transactions(id),
    idempotency_key varchar(128) NOT NULL UNIQUE,
    request_fingerprint varchar(64) NOT NULL,
    metadata_json jsonb NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    CONSTRAINT admin_actions_action_type_check
        CHECK (action_type IN ('admin_adjustment', 'bonus_grant')),
    CONSTRAINT admin_actions_wallet_type_check
        CHECK (wallet_type IN ('cash', 'bonus')),
    CONSTRAINT admin_actions_direction_check
        CHECK (direction IN ('credit', 'debit')),
    CONSTRAINT admin_actions_amount_check
        CHECK (amount > 0)
);

CREATE INDEX idx_admin_actions_admin_user_id
    ON admin_actions (admin_user_id);

CREATE INDEX idx_admin_actions_target_user_id
    ON admin_actions (target_user_id);

CREATE INDEX idx_admin_actions_ledger_transaction_id
    ON admin_actions (ledger_transaction_id);

CREATE INDEX idx_admin_actions_created_at
    ON admin_actions (created_at DESC);

COMMIT;
