-- POR-03 — il registro delle richieste gia' viste sul confine esterno.
--
-- PERCHE' UNA TABELLA E NON LA MEMORIA. Un anti-rigioco tenuto in RAM si svuota
-- al riavvio e non esiste per il secondo processo: sarebbe un controllo che si
-- spegne da solo proprio quando il sistema e' sotto carico. Il contratto chiede
-- esplicitamente persistenza, comportamento al riavvio e comportamento in
-- concorrenza (CONTRATTO_PASSO3.md, P3-01).
--
-- PERCHE' NON BASTAVA L'IDEMPOTENZA CHE C'E' GIA'. Le chiavi esistenti derivano
-- da tx_id e sono volutamente NON a uso singolo: la stessa richiesta ripetuta
-- deve rispondere 200 con already_exists, ed e' un comportamento collaudato
-- (test_seamless_ordine_operazioni.py:122-153). Difendono dal duplicato, non
-- dalla ripetizione a comando: chi cambia il tx_id passa. Il nonce e' l'altra
-- meta', e vive qui.
--
-- L'IMPRONTA DEL CORPO, E PERCHE' NON BASTAVA NEMMENO LEI. La prima stesura
-- diceva: stesso nonce + stesso corpo = retry, si riesegue. La sfida al piano
-- ha trovato il buco, e non era teorico: si intercetta una reserve, la si manda
-- quando il saldo non basta (rifiutata), la si rimanda dopo una ricarica. Byte
-- identici, quindi "retry", quindi eseguita. Il denaro si muove per una
-- richiesta intercettata.
--   Percio' qui non si registra solo che il nonce e' stato visto: si registra
--   COME E' FINITA. Alla ripetizione l'esito si RIPRODUCE, non si riesegue.
--   Un rifiuto resta un rifiuto anche se il mondo intorno e' cambiato.
--
-- ESITI: 'in_corso' (prenotato, la richiesta e' in volo), 'accettato',
-- 'rifiutato'. Una riga che resta 'in_corso' e' una richiesta morta a meta':
-- la ripetizione riceve 409, perche' non sappiamo se il denaro si e' mosso e
-- indovinare sarebbe la cosa peggiore.

BEGIN;
SET LOCAL lock_timeout = '2s';

CREATE TABLE seamless_richieste_viste (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    provider_code varchar(32) NOT NULL,
    nonce varchar(128) NOT NULL,
    -- sha256 esadecimale del corpo esatto che e' stato firmato
    impronta_corpo varchar(64) NOT NULL,
    rotta varchar(128) NOT NULL,
    esito varchar(16) NOT NULL,
    codice_http integer,
    corpo_risposta jsonb,
    creato_il timestamptz NOT NULL DEFAULT now(),
    chiuso_il timestamptz,
    CONSTRAINT seamless_richieste_viste_esito_check
        CHECK (esito IN ('in_corso', 'accettato', 'rifiutato')),
    CONSTRAINT seamless_richieste_viste_impronta_check
        CHECK (length(impronta_corpo) = 64)
);

-- IL VINCOLO CHE FA IL LAVORO. Lo scope e' (provider_code, nonce) e non il solo
-- nonce: due fornitori diversi non devono potersi bloccare a vicenda scegliendo
-- lo stesso numero. E' un vincolo di database, non un controllo applicativo,
-- perche' in concorrenza due richieste gemelle arrivano insieme e solo il
-- database puo' dire quale delle due e' arrivata prima.
CREATE UNIQUE INDEX seamless_richieste_viste_provider_nonce_key
    ON seamless_richieste_viste (provider_code, nonce);

-- Per la pulizia: si cancella per eta', e senza indice diventerebbe una
-- scansione dell'intera tabella su un percorso che muove denaro.
CREATE INDEX idx_seamless_richieste_viste_creato_il
    ON seamless_richieste_viste (creato_il);

COMMIT;
