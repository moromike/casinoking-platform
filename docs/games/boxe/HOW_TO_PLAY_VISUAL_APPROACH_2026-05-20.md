Status: ACTIVE
Last meaningful update: 2026-05-21

# BOXE - How-To-Play Visual Approach - 2026-05-20

WP: `WP-HTP-HOW-TO-PLAY-VISUAL` - Parte A approach validation, Parte B completed.

## 1. Scope Decision

Questo documento copre solo Parte A. Non autorizza modifiche runtime finche'
CTO/product owner non approvano Parte B.

Obiettivo: correggere la visualizzazione "Come si gioca" di BOXE. Il container
shared `GameHowToPlayGate` resta invariato; cambia solo il visual interno
BOXE, che oggi mostra una griglia 5x5 Mines-like mentre BOXE e' una piramide
bottom-to-top.

Out of scope:

- nessuna modifica a `GameHowToPlayGate`;
- nessuna modifica Mines;
- nessuna modifica copy how-to-play;
- nessuna modifica board runtime interattiva;
- nessuna modifica backend/math/payout;
- nessuna modifica asset pipeline.

## 2. Fonti Lette

- `docs/README.md`.
- `docs/SOURCE_OF_TRUTH.md`.
- `docs/TASK_EXECUTION_GUARDRAILS.md`.
- `docs/DOCUMENTATION_MAINTENANCE.md`.
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`.
- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`, sezioni 6.3 e 13.2.
- `docs/games/boxe/VISUAL_UNIFORMITY_APPROACH_2026-05-20.md`.
- `docs/games/boxe/GAMEPLAY_PYRAMID_APPROACH_2026-05-20.md`.
- `frontend/app/ui/game-runtime/game-how-to-play-gate.tsx`.
- `frontend/app/ui/game-runtime/game-runtime.css`.
- `frontend/app/ui/mines/mines-how-to-play-visual.tsx`.
- `frontend/app/ui/mines/mines-standalone.tsx`.
- `frontend/app/ui/boxe/boxe-standalone.tsx`.
- `frontend/app/ui/boxe/boxe-pyramid-board.tsx`.
- Mockup individuati: `assets/Games/boxe/boxe2 stato idle base .png`,
  `assets/Games/boxe/boxe4.png`, `assets/Games/boxe/boxe5.png`,
  `assets/Games/boxe/boxe6.png`, `assets/Games/boxe/boxe7.png`.

## 3. Audit Current BOXE How-To-Play

BOXE monta correttamente il container shared:

- `GameHowToPlayGate` in `frontend/app/ui/boxe/boxe-standalone.tsx:231-268`;
- titolo/copy BOXE-specific in `frontend/app/ui/boxe/boxe-standalone.tsx:233-236`;
- tre card `Bet`, `Pick`, `Collect` in
  `frontend/app/ui/boxe/boxe-standalone.tsx:237-265`;
- ogni card wrappa `BoxeHowToPlayVisual` dentro
  `.game-how-to-play-mobile-hidden` in
  `frontend/app/ui/boxe/boxe-standalone.tsx:242-262`.

Il problema e' il visual interno:

| Evidence | Stato attuale | Perche' e' un bug |
| --- | --- | --- |
| `BoxeHowToPlayVisual` inline in `frontend/app/ui/boxe/boxe-standalone.tsx:371`. | Implementazione locale, quindi correggibile senza toccare shared gate. | Good ownership. |
| `safeCells`, `mineCells`, `selectedCells` in `frontend/app/ui/boxe/boxe-standalone.tsx:373-376`. | Coordinate da griglia 5x5. | BOXE non e' griglia 5x5. |
| `Array.from({ length: 25 })` in `frontend/app/ui/boxe/boxe-standalone.tsx:377`. | Sempre 25 celle. | Copia visuale Mines, non piramide BOXE. |
| Stato `mine -> safe -> selected -> hidden` in `frontend/app/ui/boxe/boxe-standalone.tsx:381`. | `selected` perde precedenza se la cella e' anche safe. | Stato selected poco affidabile. |
| Celle senza icone in `frontend/app/ui/boxe/boxe-standalone.tsx:383`. | Solo colore CSS generico. | Non richiama diamond/mine BOXE. |
| Board class `game-how-to-play-visual-board` in `frontend/app/ui/boxe/boxe-standalone.tsx:388`. | Usa CSS shared hardcoded a 5 colonne. | Shared CSS e' giusto per Mines, sbagliato per BOXE. |
| Control dots in `frontend/app/ui/boxe/boxe-standalone.tsx:389-392`. | Sempre dot centrale active. | Non comunica card corrente; puo' restare decorativo o essere rimosso localmente. |

## 4. Shared Pattern Da Non Toccare

`GameHowToPlayGate` e' il container corretto:

- contratto `GameHowToPlayCard { title, text, visual? }` in
  `frontend/app/ui/game-runtime/game-how-to-play-gate.tsx:5-9`;
- overlay/dialog/panel/grid/card/copy/button in
  `frontend/app/ui/game-runtime/game-how-to-play-gate.tsx:20-57`;
- CSS overlay/panel/card shared in
  `frontend/app/ui/game-runtime/game-runtime.css:81-146`.

Mines e' corretto a usare una griglia:

- `MinesHowToPlayVisual` in `frontend/app/ui/mines/mines-how-to-play-visual.tsx:5`;
- 25 celle Mines in `frontend/app/ui/mines/mines-how-to-play-visual.tsx:11`;
- icone diamond/mine Mines in
  `frontend/app/ui/mines/mines-how-to-play-visual.tsx:18-21`;
- Mines monta `GameHowToPlayGate` in
  `frontend/app/ui/mines/mines-standalone.tsx:1517`.

Decisione: Mines mantiene griglia. BOXE non deve cambiare classi shared che
servono a Mines.

## 5. Mockup Target BOXE

I mockup BOXE `boxe2`, `boxe4`, `boxe5`, `boxe6`, `boxe7` mostrano:

- board piramidale;
- righe bottom-to-top;
- larghezza variabile per riga;
- avanzamento safe con diamond;
- rischio mine come reveal distinto;
- payout/ladder visivamente associata alla progressione.

Il visual HTP non deve replicare il board interattivo completo. Deve richiamare
la stessa grammatica visiva in scala ridotta.

## 6. Geometria Mini-Piramidi

Usare la formula gia' approvata per Wave 2 board:

```text
cells_for_row(row, rows) = rows - row + 1
```

Indici:

- `row = 0` e' la bottom row logica;
- `row = rows - 1` e' la top row;
- render visuale puo' essere top-down per CSS, ma data model resta
  bottom-to-top.

Decisione: usare `rows = 4` per le card HTP.

Tabella bottom-to-top:

| Row logica | Cells |
| ---: | ---: |
| 0 | 5 |
| 1 | 4 |
| 2 | 3 |
| 3 | 2 |

Motivo: `rows = 4` entra meglio nello slot card shared (`min-height: 132px` in
`frontend/app/ui/game-runtime/game-runtime.css:151`) e richiama la piramide
senza densita' eccessiva. `rows = 5` rischia miniature troppo piccole.

Non importare direttamente helper da `boxe-pyramid-board.tsx` se questo crea
dipendenza dal board runtime interattivo. Parte B puo' estrarre un helper puro
locale/shared BOXE (`boxe-board-geometry.ts`) o duplicare una funzione minima
con test, mantenendo identica formula.

## 7. Stati Per Card

| Card | Visual target | Stato celle |
| --- | --- | --- |
| Bet | Piramide chiusa idle, bottom row evidenziata. | `covered` per tutte, `active` su bottom row, una cella bottom `selected` per anticipare la scelta. |
| Pick | Piramide con prime 2-3 righe safe-revealed e active row evidenziata. | Path bottom-to-top con `safe`; riga successiva `active`; righe future `opaque` o `covered`. |
| Collect | Piramide con safe path e 1 mine reveal nella riga corrente. | Safe path gia' visibile, una cella `mine` nella current row, altre celle current `covered/opaque`. |

Nota critica: la card "Collect" e' positiva nel copy, ma il brief chiede
esplicitamente safe + mine reveal. Parte B deve rappresentarlo come "rischio
prima di incassare", senza cambiare la copy del container.

Stati CSS candidati:

- `is-covered`;
- `is-active`;
- `is-selected`;
- `is-safe`;
- `is-mine`;
- `is-opaque`.

## 8. CSS Decision

Decisione: CSS locale BOXE, non estensione shared.

Motivo:

- `.game-how-to-play-visual-board` shared e' hardcoded a 5 colonne in
  `frontend/app/ui/game-runtime/game-runtime.css:165-168`, corretto per Mines;
- modificare quel selector rischia regressione Mines;
- la geometria piramidale e' game-specific BOXE;
- Rule 2: Mines reference untouched.

Pattern Parte B:

```tsx
<div className="game-how-to-play-visual boxe-how-to-play-pyramid is-card-1">
  <div className="boxe-how-to-play-pyramid-board">
    <div className="boxe-how-to-play-pyramid-row" style={{ "--boxe-htp-row-cells": cells }}>
      <span className="boxe-how-to-play-pyramid-cell is-covered" />
    </div>
  </div>
</div>
```

Classi candidate:

- `.boxe-how-to-play-pyramid`;
- `.boxe-how-to-play-pyramid-board`;
- `.boxe-how-to-play-pyramid-row`;
- `.boxe-how-to-play-pyramid-cell`;
- `.boxe-how-to-play-pyramid-controls` se si mantengono dots locali.

Parte B puo' riusare il wrapper `.game-how-to-play-visual` per mantenere
cornice/padding shared, ma non deve usare `.game-how-to-play-visual-board`
per la griglia interna BOXE.

## 9. Asset / Symbol Decision

Non introdurre asset pipeline in WP-HTP.

Opzioni ammesse Parte B:

1. Preferita: usare gli stessi public URL gia' introdotti da Wave 2 se
   disponibili a runtime per BOXE symbols.
2. Fallback: usare micro-shapes CSS locali per HTP, perche' sono illustrazione
   didattica e non asset gameplay.

Non importare da `assets/Games/boxe/`. Quella cartella e' sorgente/mockup, non
pipeline runtime.

## 10. Parte B Granularity

Raccomandazione: 2 commit.

1. `refactor(boxe): replace how-to-play grid visual with mini pyramid`
   - riscrive solo `BoxeHowToPlayVisual`;
   - aggiunge helper geometria mini;
   - mantiene `GameHowToPlayGate` invariato;
   - non tocca Mines.
2. `style(boxe): add local how-to-play pyramid states`
   - aggiunge solo classi `boxe-how-to-play-pyramid-*` in `boxe.css`;
   - no `.boxe-pyramid-*` runtime board;
   - no `game-runtime.css` se non strettamente necessario.

Se Parte B deve toccare `game-runtime.css`, STOP: serve motivazione perche'
non bastano classi locali.

## 11. Gates Parte B

| Gate | Check |
| --- | --- |
| Container shared untouched | `frontend/app/ui/game-runtime/game-how-to-play-gate.tsx` zero diff. |
| Mines untouched | `frontend/app/ui/mines/` zero diff. |
| BOXE visual HTP | Screenshot desktop/mobile del gate con tre card piramidali. |
| Responsive | Mobile mantiene visual hidden se la classe shared lo nasconde; nessun overflow desktop. |
| Board runtime untouched | Nessun diff a `.boxe-pyramid-*` o `boxe-pyramid-board.tsx` salvo decisione separata. |
| Build | Frontend build/lint verde. |

## 12. Stop-and-Ask Attesi

STOP se:

- per ottenere la piramide bisogna modificare `GameHowToPlayGate`;
- serve cambiare Mines HTP o CSS shared della griglia Mines;
- product chiede nuova copy o nuovo flusso del gate;
- si vuole riusare classi `.boxe-pyramid-*` del board interattivo dentro HTP,
  creando coupling tra tutorial e gameplay runtime;
- si vuole rappresentare probabilita'/mine count non presenti nel contratto
  math/backend;
- asset runtime symbols non sono esposti e il fix viene bloccato dalla pipeline
  asset: usare fallback CSS locale e aprire backlog.

## 13. Capability Matrix End-To-End

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Stato | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| HTP container parity | N/A | N/A | N/A | N/A | `GameHowToPlayGate` resta shared | `game-runtime.css` unchanged | Existing HTP smoke | Questo doc | Existing | Do not touch. |
| BOXE mini pyramid visual | N/A | N/A | N/A | N/A | Three HTP cards show pyramid grammar | `boxe-how-to-play-pyramid-*` local | `npm run build`; screenshot evidence under `tests/visual/artifacts/wave3_htp_pyramid_2026-05-21/` | Questo doc | Completed Parte B | Replaced 25-cell grid with `rows = 4`, bottom-to-top data model, top-down render. |
| Mines grid visual | N/A | N/A | N/A | N/A | Mines stays 5x5 grid | Existing shared classes | Mines zero diff gate | Questo doc | Protected / verified | Rule 2. |
| Board runtime geometry | N/A | N/A | N/A | N/A | Already Wave 2, no change | `.boxe-pyramid-*` untouched | Existing board tests | Wave 2 docs | Out of scope | HTP only. |

## 13.1 Parte B Gate Evidence - 2026-05-21

Code paths:

- `frontend/app/ui/boxe/boxe-standalone.tsx` - only `BoxeHowToPlayVisual`.
- `frontend/app/ui/boxe/boxe.css` - local `boxe-how-to-play-pyramid-*` classes.

Screenshot evidence:

- `tests/visual/artifacts/wave3_htp_pyramid_2026-05-21/boxe_htp_gate_overview_desktop.png`.
- `tests/visual/artifacts/wave3_htp_pyramid_2026-05-21/boxe_htp_card_1_bet_idle.png`.
- `tests/visual/artifacts/wave3_htp_pyramid_2026-05-21/boxe_htp_card_2_pick_mid_progress.png`.
- `tests/visual/artifacts/wave3_htp_pyramid_2026-05-21/boxe_htp_card_3_collect_mine_reveal.png`.
- `tests/visual/artifacts/wave3_htp_pyramid_2026-05-21/boxe_htp_cards_collage_desktop.png`.
- `tests/visual/artifacts/wave3_htp_pyramid_2026-05-21/REPORT.md`.

Gate notes:

- Frontend build: `npm run build` passed on 2026-05-21.
- BOXE smoke: `python -m pytest tests/integration/test_boxe_smoke.py::test_boxe_demo_safe_sequence_cashout_resets_to_bet -q` passed on 2026-05-21 with `CASINOKING_FRONTEND_BASE_URL=http://localhost:3100`.
- Screenshot capture used `tests/visual/capture_wave3_htp_pyramid.py`.
- Port note: final evidence was regenerated on the assigned WP-HTP port
  `http://localhost:3100` with browser-level API mocks.
- Directional mockup comparison is recorded in the artifact `REPORT.md`:
  `boxe2` idle pyramid grammar, `boxe4`/`boxe5` safe path, `boxe6`/`boxe7`
  mine reveal risk.

## 14. Effort Estimate Prompt

Effort stimato: 0.5 giornata / 2-3 prompt per visual statico con screenshot;
1 giornata / 4 prompt se si aggiungono rifiniture responsive e test visual
dedicati.

Prompt Parte B suggerito:

"Implementa WP-HTP Parte B: solo `BoxeHowToPlayVisual` e CSS locale
`boxe-how-to-play-pyramid-*`; `GameHowToPlayGate`, Mines, board runtime e
backend zero diff. Le tre card devono mostrare mini-piramidi bottom-to-top con
stati Bet/Pick/Collect definiti nell'approach."
