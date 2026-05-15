# Mines Pending Topics

Registro dei debiti Mines che non devono restare affidati alla memoria di una
chat o di una singola AI.

## Stato BOOT-2A

| Topic | Stato | Nota |
| --- | --- | --- |
| BOOT-2A Game Boot Shell | Chiuso in BOOT-2A.5 | Game boot runtime documentato in `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`; `MinesStandalone` e' wrapper Mines-specific e `MinesGameplay` contiene gameplay. Il secondo gioco e' sbloccato per piano/design, non per implementazione automatica. |
| Target line count `MinesStandalone` | Chiuso con target rivisto | Target `N` aggiornato da 700 a 2000 righe. Razionale: il wrapper minimo contiene orchestration API/session/token/config specifica Mines. Line count reale con `wc -l`: 1939. |
| bootLog/baseline compare | Chiuso | Helper temporaneo e baseline BOOT-2A sono stati rimossi prima del merge BOOT-2A.4b. |

## Pending Residui

| Topic | Stato | Razionale | Quando riprenderlo |
| --- | --- | --- | --- |
| BOOT-2A decision flow extraction | Rimandato a design secondo gioco | L'orchestration Balance Gate / Intro / How To Play e' specifica Mines: real-mode bet flow, intro provider 8s e How To Play. Spostarla nella shell prima di avere un secondo gioco reale rischia astrazione prematura. | Durante il piano del secondo gioco, quando sara' chiaro quale parte del flow e' davvero comune. |
| Full browser smoke legacy cleanup | Da pulire prima del rilascio o quando bloccante per altro WP | Il full smoke legacy ha ancora 11 failure note fuori dal perimetro BOOT-2A.5. Non devono bloccare la chiusura docs/atlas, ma non vanno dimenticate. | Prima di un rilascio, oppure appena un work package dipende dal full browser smoke legacy verde. |

## Regola Operativa

Non riaprire BOOT-2A per questi debiti residui. Aprire un piano dedicato solo
quando il secondo gioco o un rilascio richiede di chiuderli.
