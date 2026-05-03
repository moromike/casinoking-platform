-- Admin force-close: schema additions for void/audit semantics.
--
-- Source references:
-- - docs/MINES_EXTERNAL_GAME_AND_TABLE_SESSION_PLAN.md (sezione "Admin
--   force-close - semantica e scope", CTO note 1: void as tracked
--   reversal, not deletion; CTO note 3: neutral overlay text)
--
-- Scope:
-- - allow recording an admin-driven void of an in-flight Mines round
--   in admin_actions via the new 'session_void' action_type
-- - track the close reason on game_access_sessions so the API can
--   distinguish admin-driven voids from inactivity timeouts and
--   surface a specific error code (SESSION_VOIDED_BY_OPERATOR) to
--   the player, used by the frontend to display a neutral overlay
-- - keeps the ledger immutable: every void is a new admin_actions
--   row linked to a 'void' ledger_transactions entry that reverses
--   the original 'bet' transaction in double-entry

BEGIN;

ALTER TABLE admin_actions
    DROP CONSTRAINT admin_actions_action_type_check;

ALTER TABLE admin_actions
    ADD CONSTRAINT admin_actions_action_type_check
        CHECK (action_type IN ('admin_adjustment', 'bonus_grant', 'session_void'));

ALTER TABLE game_access_sessions
    ADD COLUMN IF NOT EXISTS closed_reason varchar(64) NULL;

COMMIT;
