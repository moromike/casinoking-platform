-- CasinoKing - Quadratura garantita (CON-02, CON-03).
--
-- Perche' esiste questa migrazione:
-- Fino a qui la partita doppia era garantita solo dal codice applicativo e
-- verificata a posteriori con rapporti di riconciliazione: una transazione
-- sbilanciata poteva essere registrata e scoperta dopo. Il database e' appena
-- stato azzerato, quindi e' il momento giusto per rendere lo sbilancio
-- IMPOSSIBILE a livello di database.
--
-- CON-02: un constraint trigger DEFERRABLE INITIALLY DEFERRED su ledger_entries
-- verifica AL COMMIT che per ogni transaction_id toccato dalla transazione
-- somma(dare) = somma(avere). Una CHECK non puo' guardare piu' righe, quindi
-- serve un trigger differito: controlla a fine transazione, quando tutte le
-- scritture sono presenti.
--
-- CON-03: ledger_transactions.idempotency_key diventa NOT NULL. Se esistono
-- righe con valore nullo la migrazione FALLISCE con un messaggio chiaro:
-- non ci si inventa valori per dati contabili.
--
-- Ambito: solo vincoli di database. Nessuna modifica al codice applicativo,
-- nessun dato cancellato o riscritto.

BEGIN;

-- CON-03: rifiuta la migrazione se ci sono transazioni senza idempotency_key.
DO $$
DECLARE
    righe_senza_chiave integer;
BEGIN
    SELECT count(*) INTO righe_senza_chiave
    FROM ledger_transactions
    WHERE idempotency_key IS NULL;

    IF righe_senza_chiave > 0 THEN
        RAISE EXCEPTION 'CON-03 fallita: % transazioni contabili hanno idempotency_key NULL. Correggere i dati a mano prima di riapplicare la migrazione: nessun valore verra'' inventato.', righe_senza_chiave;
    END IF;
END $$;

ALTER TABLE ledger_transactions
    ALTER COLUMN idempotency_key SET NOT NULL;

-- CON-02: funzione di verifica della quadratura, eseguita al COMMIT.
CREATE OR REPLACE FUNCTION verifica_quadratura_transazione()
RETURNS trigger
LANGUAGE plpgsql
AS $$
DECLARE
    v_transaction_id uuid;
    v_totale_dare numeric(18, 6);
    v_totale_avere numeric(18, 6);
BEGIN
    -- Con UPDATE che sposta una scrittura fra transazioni, sia la transazione
    -- di origine (OLD) sia quella di destinazione (NEW) vanno riverificate.
    FOR v_transaction_id IN
        SELECT DISTINCT tid
        FROM (VALUES (NEW.transaction_id), (OLD.transaction_id)) AS sorgenti(tid)
        WHERE tid IS NOT NULL
    LOOP
        SELECT
            COALESCE(SUM(amount) FILTER (WHERE entry_side = 'debit'), 0),
            COALESCE(SUM(amount) FILTER (WHERE entry_side = 'credit'), 0)
        INTO v_totale_dare, v_totale_avere
        FROM ledger_entries
        WHERE transaction_id = v_transaction_id;

        IF v_totale_dare <> v_totale_avere THEN
            RAISE EXCEPTION 'Quadratura contabile violata: la transazione % e'' sbilanciata (dare %, avere %, differenza %)',
                v_transaction_id, v_totale_dare, v_totale_avere, v_totale_dare - v_totale_avere;
        END IF;
    END LOOP;

    RETURN NULL;
END;
$$;

DROP TRIGGER IF EXISTS ledger_entries_quadratura_trigger ON ledger_entries;

CREATE CONSTRAINT TRIGGER ledger_entries_quadratura_trigger
AFTER INSERT OR UPDATE OR DELETE ON ledger_entries
DEFERRABLE INITIALLY DEFERRED
FOR EACH ROW
EXECUTE FUNCTION verifica_quadratura_transazione();

COMMIT;
