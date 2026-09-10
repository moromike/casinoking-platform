-- Punto E — le 14 partite mines che il gioco chiama 'won' e la piattaforma 'cancelled'.
--
-- COSA SONO, misurato e non supposto: 14 righe con bet_amount = payout_amount = 1.00,
-- cioe' rimborsi senza progresso. La piattaforma le ha gia' corrette a 'cancelled' con
-- CON-05 il 10/09; il lato gioco e' rimasto 'won'.
--
-- PERCHE' ESISTONO, e non e' un difetto vivo. Sono il fossile di una finestra di 19
-- minuti l'8/09 (commit 553a872 delle 22:59 -> 0ec8fcf delle 23:18) in cui il lato gioco
-- scriveva 'won' su un rimborso. Il codice di oggi scrive 'cancelled' su ENTRAMBE le
-- tabelle: autoliquidazione.py:167 e rounds/service.py:1062, chiamati in sequenza dallo
-- stesso flusso con lo stesso settlement_kind. Non possono divergere.
-- La correzione di CON-05 ha migrato 434 righe su platform_rounds ma non ha toccato
-- mines_game_rounds: queste 14 erano gia' 'won' e ci sono rimaste.
--
-- NOTA SULLA DATA, perche' RIPARTENZA.md dice il falso: non sono "pre-8/09". Sono nate
-- fra l'8/09 alle 20:52 e il 9/09 alle 16:07, cioe' DOPO la riparazione dell'8/09.
--
-- COSA NON FA: non tocca un centesimo. Cambia un'etichetta di stato, non un movimento.
-- La somma di ledger_entries prima e dopo e' identica, ed e' salvata in
-- artifacts/passo5/punto-e-prima.txt e punto-e-dopo.txt.
--
-- SI SCEGLIE PER JOIN, NON PER SOMIGLIANZA: solo le righe la cui partita di piattaforma
-- dice gia' 'cancelled'. Nessuna riga si tocca perche' "sembra" un rimborso.

BEGIN;
SET LOCAL lock_timeout = '2s';

CREATE TABLE audit_revert_mines_allineamento_0059 AS
SELECT mr.id, mr.status
FROM mines_game_rounds mr
JOIN platform_rounds pr ON mr.platform_round_id = pr.id
WHERE pr.status = 'cancelled' AND mr.status = 'won';

UPDATE mines_game_rounds mr
SET status = 'cancelled'
FROM platform_rounds pr
WHERE mr.platform_round_id = pr.id
  AND pr.status = 'cancelled'
  AND mr.status = 'won';

COMMIT;
