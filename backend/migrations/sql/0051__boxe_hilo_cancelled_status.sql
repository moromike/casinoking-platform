-- CasinoKing - Add 'cancelled' status and 'admin_force_close' outcome to BOXE and HI-LO.
--
-- Scope:
-- - support admin force-close void semantics (DIV-06c)
-- - 'cancelled' is the VOID state, aligned with platform_rounds.status = 'cancelled'
-- - 'admin_force_close' is the void outcome, distinct from cashout/loss/expired/quarantined

BEGIN;

-- BOXE: extend status enum with 'cancelled'
ALTER TABLE boxe_rounds
    DROP CONSTRAINT IF EXISTS boxe_rounds_status_check;

ALTER TABLE boxe_rounds
    ADD CONSTRAINT boxe_rounds_status_check
        CHECK (status IN (
            'created',
            'active',
            'row_revealed',
            'cashout_pending',
            'completed_cashout',
            'completed_top_row',
            'failed_mine',
            'expired',
            'quarantined',
            'cancelled'
        ));

-- BOXE: extend closed_at consistency check to treat 'cancelled' as terminal
ALTER TABLE boxe_rounds
    DROP CONSTRAINT IF EXISTS boxe_rounds_closed_at_consistency_check;

ALTER TABLE boxe_rounds
    ADD CONSTRAINT boxe_rounds_closed_at_consistency_check
        CHECK (
            (status IN ('created', 'active', 'row_revealed', 'cashout_pending') AND closed_at IS NULL)
            OR (status IN ('completed_cashout', 'completed_top_row', 'failed_mine', 'expired', 'quarantined', 'cancelled') AND closed_at IS NOT NULL)
        );

-- BOXE: extend outcome enum with 'admin_force_close'
ALTER TABLE boxe_rounds
    DROP CONSTRAINT IF EXISTS boxe_rounds_outcome_check;

ALTER TABLE boxe_rounds
    ADD CONSTRAINT boxe_rounds_outcome_check
        CHECK (
            outcome IS NULL
            OR outcome IN ('cashout', 'top_row', 'loss', 'expired', 'quarantined', 'admin_force_close')
        );

-- HI-LO: extend status enum with 'cancelled'
ALTER TABLE hi_lo_rounds
    DROP CONSTRAINT IF EXISTS hi_lo_rounds_status_check;

ALTER TABLE hi_lo_rounds
    ADD CONSTRAINT hi_lo_rounds_status_check
        CHECK (status IN (
            'created',
            'active',
            'cashout_pending',
            'completed_cashout',
            'failed_prediction',
            'expired',
            'quarantined',
            'cancelled'
        ));

-- HI-LO: extend closed_at consistency check to treat 'cancelled' as terminal
ALTER TABLE hi_lo_rounds
    DROP CONSTRAINT IF EXISTS hi_lo_rounds_closed_at_consistency_check;

ALTER TABLE hi_lo_rounds
    ADD CONSTRAINT hi_lo_rounds_closed_at_consistency_check
        CHECK (
            (status IN ('created', 'active', 'cashout_pending') AND closed_at IS NULL)
            OR (status IN ('completed_cashout', 'failed_prediction', 'expired', 'quarantined', 'cancelled') AND closed_at IS NOT NULL)
        );

-- HI-LO: extend outcome enum with 'admin_force_close'
ALTER TABLE hi_lo_rounds
    DROP CONSTRAINT IF EXISTS hi_lo_rounds_outcome_check;

ALTER TABLE hi_lo_rounds
    ADD CONSTRAINT hi_lo_rounds_outcome_check
        CHECK (
            outcome IS NULL
            OR outcome IN ('cashout', 'loss', 'expired', 'quarantined', 'admin_force_close')
        );

COMMIT;
