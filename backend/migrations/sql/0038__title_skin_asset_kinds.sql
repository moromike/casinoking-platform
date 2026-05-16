-- CasinoKing - Title skin asset kinds for Mines Advanced Skin V1.
--
-- Scope:
-- - allow explicit skin asset kinds in title_assets
-- - keep legacy logo/background kinds readable
-- - no gameplay, payout, RNG, wallet or ledger changes

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
            'title_logo',
            'game_area_background',
            'cell_face_down_background',
            'audio_safe_reveal',
            'audio_mine_hit',
            'audio_collect',
            'audio_win',
            'audio_lose',
            'audio_click',
            'font'
        ));

COMMIT;
