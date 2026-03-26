-- CasinoKing Mines game_sessions runtime hardening
-- Source references:
-- - docs/md/CasinoKing_Documento_06_Mines_Prodotto_Stati_Matematica_API.md
-- - docs/md/CasinoKing_Documento_09_v2_Game_Engine_Testing.md
-- - docs/md/CasinoKing_Documento_11_v2_API_Contract_Allineato_v3.md
-- - docs/md/CasinoKing_Documento_13_v3_SQL_Migrations_Definitivo.md
--
-- Scope of this migration:
-- - tighten runtime invariants for Mines session state persistence
-- - guard closed_at semantics for active vs closed sessions
-- - ensure safe reveal counters cannot exceed available safe cells

BEGIN;

ALTER TABLE game_sessions
    ADD CONSTRAINT game_sessions_closed_at_consistency_check
        CHECK (
            (
                status IN ('created', 'active')
                AND closed_at IS NULL
            )
            OR (
                status IN ('won', 'lost', 'cancelled')
                AND closed_at IS NOT NULL
            )
        ),
    ADD CONSTRAINT game_sessions_safe_reveals_upper_bound_check
        CHECK (safe_reveals_count <= (grid_size - mine_count));

COMMIT;
