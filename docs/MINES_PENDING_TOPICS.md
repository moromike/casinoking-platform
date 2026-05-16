# Mines Pending Topics

Registro dei debiti Mines che non devono restare affidati alla memoria di una
chat o di una singola AI.

## Stato BOOT-2A

| Topic | Stato | Nota |
| --- | --- | --- |
| BOOT-2A Game Boot Shell | Chiuso in BOOT-2A.6 | Game boot runtime documentato in `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`; `GameBootDecisionFlow` gestisce il flow visuale comune e `MinesStandalone` resta wrapper Mines-specific. Il secondo gioco e' sbloccato per piano/design, non per implementazione automatica. |
| BOOT-2A decision flow extraction | Chiuso in BOOT-2A.6 | Estratto con boundary conservativo: `game-runtime/` riceve booleans e `ReactNode`; Mines conserva stato, copy, contenuti, table session API e callback specifiche. |
| Target line count `MinesStandalone` | Chiuso con target rivisto | Target `N` aggiornato da 700 a 2000 righe. Razionale: il wrapper minimo contiene orchestration API/session/token/config specifica Mines. Line count reale con `wc -l`: 1939. |
| bootLog/baseline compare | Chiuso | Helper temporaneo e baseline BOOT-2A sono stati rimossi prima del merge BOOT-2A.4b. |

## Chiusure Post-Recovery

| Topic | Stato | Nota |
| --- | --- | --- |
| Mines skin estesa / MSK V2 | Chiuso il 2026-05-16 | Mergeato in `main` con asset kind `title_logo`, `game_area_background`, `cell_face_down_background`, editor Tema avanzato, runtime wiring e WCAG publish gate. |
| Finance drilldown | Chiuso il 2026-05-16 | Mergeato in `main` come drilldown read-only; non apre modifiche a wallet/ledger/RNG/payout/settlement. |

## Pending Residui

| Topic | Stato | Razionale | Quando riprenderlo |
| --- | --- | --- | --- |
| Full browser smoke legacy cleanup | Da pulire prima del rilascio o quando bloccante per altro WP | Il full smoke legacy ha ancora 11 failure note fuori dal perimetro BOOT-2A.5. Non devono bloccare la chiusura docs/atlas, ma non vanno dimenticate. | Prima di un rilascio, oppure appena un work package dipende dal full browser smoke legacy verde. |

## Regola Operativa

Non riaprire BOOT-2A per questi debiti residui. Aprire un piano dedicato solo
quando un rilascio richiede di chiuderli.
