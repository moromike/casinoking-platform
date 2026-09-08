BEGIN;
SET LOCAL lock_timeout = '2s';

CREATE TABLE audit_revert_mines_rounds AS
SELECT id, status
FROM mines_game_rounds
WHERE status = 'active' AND closed_at IS NOT NULL;

ALTER TABLE mines_game_rounds ADD CONSTRAINT chk_mines_status
  CHECK (status IS NOT NULL AND status IN ('active','won','lost','cancelled')) NOT VALID;
ALTER TABLE mines_game_rounds ADD CONSTRAINT chk_mines_closed
  CHECK ((status = 'active' AND closed_at IS NULL)
      OR (status <> 'active' AND closed_at IS NOT NULL)) NOT VALID;

UPDATE mines_game_rounds
SET status = 'cancelled'
WHERE status = 'active' AND closed_at IS NOT NULL;
COMMIT;

ALTER TABLE mines_game_rounds VALIDATE CONSTRAINT chk_mines_status;
ALTER TABLE mines_game_rounds VALIDATE CONSTRAINT chk_mines_closed;
