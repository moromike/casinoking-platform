BEGIN;
ALTER TABLE mines_game_rounds
  DROP CONSTRAINT chk_mines_status,
  DROP CONSTRAINT chk_mines_closed;
UPDATE mines_game_rounds m
SET status = b.status
FROM audit_revert_mines_rounds b
WHERE m.id = b.id;
COMMIT;
