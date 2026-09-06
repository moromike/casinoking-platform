-- POR-02: Aggiunge provider_code a platform_rounds per legare la partita al fornitore
BEGIN;

ALTER TABLE platform_rounds
ADD COLUMN provider_code varchar(32) NULL;

-- Popoliamo i dati esistenti facendo join con game_engines
UPDATE platform_rounds pr
SET provider_code = ge.provider_code
FROM game_engines ge
WHERE pr.game_code = ge.engine_code;

-- Rendiamo la colonna NOT NULL
ALTER TABLE platform_rounds
ALTER COLUMN provider_code SET NOT NULL;

-- Aggiungiamo la foreign key
ALTER TABLE platform_rounds
ADD CONSTRAINT platform_rounds_provider_code_fkey
FOREIGN KEY (provider_code) REFERENCES game_providers(provider_code);

-- Drop old idempotency constraint (was UNIQUE (user_id, idempotency_key))
-- Fix existing duplicates by namespacing the idempotency_key with user_id for old records
UPDATE platform_rounds 
SET idempotency_key = user_id || ':' || idempotency_key 
WHERE idempotency_key IS NOT NULL;

ALTER TABLE platform_rounds
DROP CONSTRAINT platform_rounds_user_idempotency_key_key;

-- Add new idempotency constraint per provider (POR-02 richiede chiave anti-doppione per fornitore)
-- Note: it could be just (provider_code, idempotency_key), or (provider_code, user_id, idempotency_key).
-- We'll use (provider_code, idempotency_key) to ensure global uniqueness per provider.
ALTER TABLE platform_rounds
ADD CONSTRAINT platform_rounds_provider_idempotency_key_key
UNIQUE (provider_code, idempotency_key);

COMMIT;
