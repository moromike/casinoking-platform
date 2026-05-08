-- CasinoKing Title locale map cascade
--
-- Keep Title-level i18n content owned by game_titles. This protects local/test
-- cleanup paths and prevents orphaned locale maps when a Title variant is
-- deleted.

ALTER TABLE title_locale_maps
    DROP CONSTRAINT IF EXISTS title_locale_maps_title_code_fkey;

ALTER TABLE title_locale_maps
    ADD CONSTRAINT title_locale_maps_title_code_fkey
    FOREIGN KEY (title_code)
    REFERENCES game_titles(title_code)
    ON DELETE CASCADE;

ALTER TABLE title_locale_maps
    DROP CONSTRAINT IF EXISTS title_locale_maps_default_locale_payload_check;

ALTER TABLE title_locale_maps
    ADD CONSTRAINT title_locale_maps_default_locale_payload_check
    CHECK (locales_json ? default_locale_code);
