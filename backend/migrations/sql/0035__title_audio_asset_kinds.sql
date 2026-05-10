-- CasinoKing - Title audio asset kinds for Mines runtime sounds.
--
-- Scope:
-- - allow explicit V1 Mines sound kinds in title_assets
-- - keep legacy audio_lose/audio_click readable but not uploadable by service/UI
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
            'audio_safe_reveal',
            'audio_mine_hit',
            'audio_collect',
            'audio_win',
            'audio_lose',
            'audio_click',
            'font'
        ));

COMMIT;
