-- POR-03 — una prenotazione ha un proprietario; una traccia non prenota.
--
-- PERCHE': il recupero della riga morta faceva proseguire una nuova esecuzione,
-- ma quella vecchia poteva ancora chiuderla. Inoltre i rifiuti prima dello
-- schema devono essere osservabili senza consumare il nonce della rotta giusta.
-- I due difetti hanno la stessa radice: la riga non dichiarava chi possedeva lo
-- stato esclusivo. `proprietario` cambia a ogni acquisizione; `vincola_nonce`
-- separa una prenotazione da una semplice traccia.

BEGIN;
SET LOCAL lock_timeout = '2s';

ALTER TABLE seamless_richieste_viste
    ADD COLUMN proprietario uuid,
    ADD COLUMN vincola_nonce boolean NOT NULL DEFAULT TRUE;

-- Le sole righe vive preesistenti ricevono una generazione. Le righe terminali
-- non appartengono piu' a un esecutore.
UPDATE seamless_richieste_viste
SET proprietario = gen_random_uuid()
WHERE esito = 'in_corso';

ALTER TABLE seamless_richieste_viste
    ADD CONSTRAINT seamless_richieste_viste_proprietario_check
    CHECK (
        (vincola_nonce AND esito = 'in_corso')
        = (proprietario IS NOT NULL)
    );

DROP INDEX seamless_richieste_viste_provider_nonce_key;
CREATE UNIQUE INDEX seamless_richieste_viste_provider_nonce_key
    ON seamless_richieste_viste (provider_code, nonce)
    WHERE vincola_nonce;

COMMIT;
