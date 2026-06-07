-- CasinoKing - Drop user FK constraints for BOXE and HI-LO idempotency tables
-- to support anonymous demo mode (DIV-06c / 8b).
--
-- Scope:
-- - player_id may contain an anonymous UUID (not in users table) for demo rounds
-- - boxe_rounds and hi_lo_rounds already lack FK to users; only idempotency tables had them

BEGIN;

-- BOXE idempotency keys
ALTER TABLE boxe_idempotency_keys
    DROP CONSTRAINT IF EXISTS boxe_idempotency_keys_player_id_fkey;

-- HI-LO rounds
ALTER TABLE hi_lo_rounds
    DROP CONSTRAINT IF EXISTS hi_lo_rounds_player_id_fkey;

-- HI-LO idempotency keys
ALTER TABLE hi_lo_idempotency_keys
    DROP CONSTRAINT IF EXISTS hi_lo_idempotency_keys_player_id_fkey;

COMMIT;
