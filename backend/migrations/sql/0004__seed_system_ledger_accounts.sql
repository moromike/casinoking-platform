-- CasinoKing initial system ledger accounts
-- Source references:
-- - docs/md/CasinoKing_Documento_05_v3_Wallet_Ledger_Fondamenta_Definitive.md
-- - docs/md/CasinoKing_Documento_13_v3_SQL_Migrations_Definitivo.md
--
-- Scope of this migration:
-- - seed the minimum chart-of-accounts rows required by the initial flows
-- - keep player accounts dynamic and per-user at runtime

BEGIN;

INSERT INTO ledger_accounts (
    id,
    account_code,
    account_type,
    owner_user_id,
    currency_code,
    status
)
VALUES
    (
        '00000000-0000-0000-0000-000000000101',
        'HOUSE_CASH',
        'house_cash',
        NULL,
        'CHIP',
        'active'
    ),
    (
        '00000000-0000-0000-0000-000000000102',
        'HOUSE_BONUS',
        'house_bonus',
        NULL,
        'CHIP',
        'active'
    ),
    (
        '00000000-0000-0000-0000-000000000103',
        'PROMO_RESERVE',
        'promo_reserve',
        NULL,
        'CHIP',
        'active'
    ),
    (
        '00000000-0000-0000-0000-000000000104',
        'GAME_PNL_MINES',
        'game_pnl_mines',
        NULL,
        'CHIP',
        'active'
    );

COMMIT;
