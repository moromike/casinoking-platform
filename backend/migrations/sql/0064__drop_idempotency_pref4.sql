-- 0064 — PASSO 5 Riserve: rimuove le copie congelate pre-tabella-unica.
--
-- La retromarcia resta possibile: eseguire prima il rollback 0064, che
-- ricrea le tre tabelle vuote, e poi il rollback 0063, che le ripopola
-- dalla tabella unica.

BEGIN;

DROP TABLE IF EXISTS boxe_idempotency_keys_pref4;
DROP TABLE IF EXISTS hi_lo_idempotency_keys_pref4;
DROP TABLE IF EXISTS mines_idempotency_keys_pref4;

COMMIT;
