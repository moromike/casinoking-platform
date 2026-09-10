-- Retromarcia di 0062. Le tracce non vincolanti possono condividere il nonce:
-- vanno tolte prima di ripristinare il vecchio vincolo totale.
BEGIN;
DELETE FROM seamless_richieste_viste WHERE NOT vincola_nonce;
DROP INDEX seamless_richieste_viste_provider_nonce_key;
CREATE UNIQUE INDEX seamless_richieste_viste_provider_nonce_key
    ON seamless_richieste_viste (provider_code, nonce);
ALTER TABLE seamless_richieste_viste
    DROP CONSTRAINT seamless_richieste_viste_proprietario_check,
    DROP COLUMN proprietario,
    DROP COLUMN vincola_nonce;
COMMIT;
