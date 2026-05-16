-- CasinoKing - Title game card asset kind for player lobby cards.
--
-- Scope:
-- - allow a square game_card asset on title_assets
-- - keep ownership at Title level; no site media library changes

BEGIN;

ALTER TABLE title_assets
    DROP CONSTRAINT IF EXISTS title_assets_kind_check;

ALTER TABLE title_assets
    ADD CONSTRAINT title_assets_kind_check
        CHECK (asset_kind IN (
            'logo',
            'background',
            'symbol_safe',
            'symbol_mine',
            'game_card',
            'audio_safe_reveal',
            'audio_mine_hit',
            'audio_collect',
            'audio_win',
            'audio_lose',
            'audio_click',
            'font'
        ));

COMMIT;
