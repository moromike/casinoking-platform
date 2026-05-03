BEGIN;

ALTER TABLE game_table_sessions
    ADD COLUMN IF NOT EXISTS table_balance_amount numeric(18, 6);

UPDATE game_table_sessions
SET table_balance_amount = GREATEST(
    loss_limit_amount - loss_reserved_amount - loss_consumed_amount,
    0
)
WHERE table_balance_amount IS NULL;

ALTER TABLE game_table_sessions
    ALTER COLUMN table_balance_amount SET DEFAULT 0,
    ALTER COLUMN table_balance_amount SET NOT NULL;

ALTER TABLE game_table_sessions
    ADD CONSTRAINT game_table_sessions_table_balance_amount_check
        CHECK (table_balance_amount >= 0);

COMMIT;
