-- CasinoKing - BOXE demo wallet session linkage.
--
-- Scope:
-- - persist the server-side demo wallet session used by BOXE demo rounds
-- - keep real-money platform round linkage unchanged

BEGIN;

ALTER TABLE boxe_rounds
    ADD COLUMN IF NOT EXISTS demo_session_id uuid NULL REFERENCES demo_play_sessions(id);

CREATE INDEX IF NOT EXISTS idx_boxe_rounds_demo_session_id
    ON boxe_rounds(demo_session_id)
    WHERE demo_session_id IS NOT NULL;

COMMIT;
