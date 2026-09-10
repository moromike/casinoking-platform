-- Retromarcia di 0059. Rimette lo stato esatto che ogni riga aveva prima,
-- riga per riga, dalla tabella di salvataggio. Non indovina: rilegge.
BEGIN;
UPDATE mines_game_rounds m
SET status = b.status
FROM audit_revert_mines_allineamento_0059 b
WHERE m.id = b.id;
DROP TABLE audit_revert_mines_allineamento_0059;
COMMIT;
