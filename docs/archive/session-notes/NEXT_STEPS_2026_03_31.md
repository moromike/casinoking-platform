# CasinoKing — Prossimi Step (2026-03-31)

## Stato: Tutte le 4 fasi del MINES_EXECUTION_PLAN completate

## Azioni immediate (pre-requisiti)

1. **Verifica post-fix Mines desktop**
   - Confermare che il rail sinistro desktop di [`/mines`](../frontend/app/mines/page.tsx) resti allineato con tutte le configurazioni supportate
   - Confermare che il banner errore non sposti più il layout

2. **Applicare migrazioni DB**
   - Le migrazioni 0012 e 0013 creano le nuove tabelle e migrano i dati
   - Richiede Docker up con il database PostgreSQL
   - `docker compose up -d` poi applicare migrazioni

3. **Test di integrazione**
   - Eseguire la suite completa: `cd backend && python -m pytest tests/ --timeout=30`
   - Verificare che tutti i test passino con il nuovo schema

## Verifica manuale

4. **Gioco Mines su `/mines`**
   - Desktop: verificare end-to-end dopo il fix del round start backend e del rail sinistro
   - Mobile: verificare layout responsive
   - Embedded: verificare iframe dalla lobby

5. **Backoffice admin**
   - Verificare che l'editor backoffice Mines funzioni
   - Testare draft/publish workflow

## Analisi per prossimi sviluppi

6. **Isolamento styling Mines** (opzionale ma consigliato)
   - [`globals.css`](../frontend/app/globals.css) è ancora il collo di bottiglia per i layout condivisi
   - Valutare estrazione dello styling Mines in file dedicato o namespace più stretti
   - Priorità: evitare futuri regressions del rail desktop da classi globali riusate

7. **Rimozione `game_sessions` table** (quando sicuri)
   - La tabella originale è ancora presente
   - La vista `game_sessions_compat` fornisce backward-compat
   - Droppare solo dopo aver verificato che nessun codice la usa direttamente

8. **Rinominare `helpers.ts`**
   - Ora è condiviso tra piattaforma e gioco
   - Rinominare in `frontend/app/lib/helpers.ts` per chiarezza

9. **Game launch token consumption tracking**
   - Attualmente il token è stateless (JWT only)
   - Per Document 35, serve consumption tracking (single-use o bounded-use)

10. **Valutare test E2E**
    - Playwright o Cypress per test browser automatizzati
    - Coprire: login → fund → play → win/lose → verify balance
