# PROMPT KIMI — WP-PC1 Doc-state reconciliation (pre-COINS)

> Incollare in KIMI. Esecuzione, dominio `docs/` SOLO. Gate finale = CTO.

## Contesto (delta)
La bonifica cross-game è COMPLETA e già mergeata in `main` (`d6eb114 Merge feature/site-v3-cms-ia-cleanup`; B6/B7 gate 2026-06-08). Due dashboard hanno celle di stato vecchie che dicono ancora "da fare/IN CORSO" per item chiusi. Tuo compito: riallinearle. NIENTE codice, NIENTE file fuori da `docs/`.

## Setup
1. `git checkout main && git pull`
2. `git checkout -b chore/pre-coins-doc-reconciliation`

## Task 1 — `docs/CROSS_GAME_BONIFICA_PROGRAM_2026-06-04.md`
Sostituzioni esatte (find → replace della sola cella di stato):

- Master schedule, riga item 9:
  - FIND: `| 9 | DIV-07..10 validator/idempotency/adapter/layering | Backend | da fare | 7 |`
  - REPLACE: `| 9 | DIV-07..10 validator/idempotency/adapter/layering | Backend | ✅ DONE (DIV-07/08 gate CTO; DIV-09 \`1ed469c\`, DIV-10 \`19bbb71\` — merged to main via \`d6eb114\`) | 7 |`

- Tabella "Ordine e stato (tronco backend dettaglio)":
  - `| 3 | DIV-03 | ... | **IN CORSO** |` → stato `✅ **DONE** (gate CTO 2026-06-05)`
  - `| 4 | DIV-05/06 | ... | da decidere PRIMA di migrare |` → stato `✅ **DONE** (DIV-06 host-owned + DIV-05 boxe_sessions rimossa, gate CTO 2026-06-07)`
  - `| 5 | DIV-02 | ... | dopo step 4 |` → stato `✅ **DONE** (gate CTO 2026-06-06)`
  - `| 6 | DIV-07..10 | ... | pacchetto finale |` → stato `✅ **DONE** (merged to main \`d6eb114\`)`

## Task 2 — `docs/ACTIVE_OPEN_LOOPS.md`
1. Header: `Last meaningful update: 2026-06-03` → `Last meaningful update: 2026-06-09`.
2. Nelle righe P0, porta a stato **CHIUSO** con motivazione 1-riga + evidenza (cita `d6eb114` / B6-B7 gate 2026-06-08) le seguenti, e in "Prossima azione" scrivi "Nessuna azione residua":
   - `Consistenza launch-token tra giochi (BOXE↔Mines)`
   - `Cross-game parity audit (Mines/BOXE/HI-LO)`
   - `Test stale error-shape`
   - `Test-infra: suite integration timeout + isolamento cross-file`
3. Riga `Cross-game FRONTEND/UX parity`: NON chiuderla. Aggiorna stato: "F1/F2 DONE; residui **F07 (mobile layout HI-LO) + F08 (bet input decimale)** pianificati pre-COINS in `docs/PRE_COINS_ACTIVITY_PLAN_2026-06-09.md` (WP-PC2/PC3); F06 audio PARCHEGGIATO." Prossima azione = "Eseguire WP-PC2/PC3 poi CTO-MOBILE".
4. Non toccare le righe già CHIUSE né le P1 non pertinenti.

## Vincoli
- Solo `docs/`. Nessun cambio di codice/test.
- Non inventare evidenze: usa solo `d6eb114` (merge), gate B6/B7 2026-06-08, e i commit citati sopra.

## Commit
`git add -A && git commit -m "WP-PC1: reconcile stale status in bonifica tracker + ACTIVE_OPEN_LOOPS"`

## Evidence richiesta nella risposta finale (auto-attestazione)
1. `git diff --stat` (solo file in `docs/`).
2. Output di: `grep -nE "da fare|IN CORSO|da decidere PRIMA di migrare|dopo step 4|pacchetto finale" docs/CROSS_GAME_BONIFICA_PROGRAM_2026-06-04.md` → deve NON elencare più le 5 celle bonificate (mostra l'output, anche se vuoto).
3. Le 4 righe ACTIVE_OPEN_LOOPS portate a CHIUSO (cita riga).
4. La riga FRONTEND parity aggiornata col rimando al piano pre-COINS.
5. SHA del commit + conferma "nessun file fuori da `docs/` toccato".

**Clausola forzante:** esplicita CIASCUNA evidenza sopra nella risposta finale + auto-attestazione. Se manca anche una sola evidenza = task FAILED a priori; non dichiarare done.
