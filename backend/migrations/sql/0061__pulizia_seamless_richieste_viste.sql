-- POR-03 — pulizia del registro anti-rigioco del confine esterno.
--
-- PERCHE': la revisione indipendente ha riprodotto che il registro non aveva
-- alcuna pulizia e quindi cresceva senza fine. Un controllo che conserva ogni
-- richiesta puo' finire per consumare lo spazio del database che protegge.
-- Un'ora supera la finestra temporale del protocollo: rimuovere prima
-- trasformerebbe una richiesta ancora valida in una richiesta mai vista.

BEGIN;
SET LOCAL lock_timeout = '2s';

CREATE OR REPLACE FUNCTION pulisci_seamless_richieste_viste()
RETURNS integer
LANGUAGE plpgsql
AS $$
DECLARE
    righe_eliminate integer;
BEGIN
    DELETE FROM seamless_richieste_viste
    WHERE creato_il < now() - interval '1 hour';

    GET DIAGNOSTICS righe_eliminate = ROW_COUNT;
    RETURN righe_eliminate;
END;
$$;

COMMIT;
