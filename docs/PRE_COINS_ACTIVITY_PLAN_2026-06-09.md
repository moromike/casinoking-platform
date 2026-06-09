Status: ACTIVE
Created: 2026-06-09
Owner: CTO (Claude) plans/gates · Executor: KIMI · Mobile validation: CTO

# Pre-COINS Activity Plan (2026-06-09)

Piano delle attività da chiudere PRIMA di aprire COINS (gioco 4). Bonifica
cross-game completa; questo piano porta a un baseline pulito per il gioco 4.
Tutte le attività di esecuzione = **KIMI**. Gate = CTO sull'evidenza. Mobile = CTO.

## Baseline verificato (2026-06-09)

- **Bonifica cross-game COMPLETA e mergeata in `main`** (`d6eb114 Merge feature/site-v3-cms-ia-cleanup`). DIV-01..10, DIV-06c, 8b, B6 (663 passed / 9 marker), B7 tutti in `main` (verificato: B7 `8e0c9c5` e DIV-10 `19bbb71` sono ancestor di `main`).
- **B6 regression = verde** (gate CTO 2026-06-08). `main` aggiunge SOLO commit di documentazione sopra il lavoro (`3ce0e10`, `ca38526`): nessuna modifica di codice → **niente re-regression necessaria** prima di COINS.
- **Playbook = v3.4, OK** (`docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`), tutte le lezioni 16.2bis→quinquies presenti. Header allineato a v3.4/2026-06-08.
- **Prerequisiti playbook §2 = STABLE**; Rule 18 registry + embed-mode parity già committati.

## Setup (decisione CTO, 0 prompt)

Tutte le WP partono da **`main`**. Il branch `feature/site-v3-cms-ia-cleanup` è 3 commit
*dietro* main ed è da ritirare (lavoro già integrato). COINS nascerà da un branch nuovo su main.

## Ordine vincolante (NO LIFO)

| # | WP | Esecutore | Dominio | Tipo | Dipende da |
|---|----|-----------|---------|------|-----------|
| 1 | WP-PC1 Doc-state reconciliation | KIMI | `docs/` | Igiene | — |
| 2 | WP-PC2 F08 bet input decimale | KIMI | frontend giochi | Parità FE | — |
| 3 | WP-PC3 F07 HI-LO mobile layout | KIMI | frontend HI-LO | Parità FE (rischio ALTO) | — |
| 4 | CTO-MOBILE parity check M/B/H | **CTO (io)** | screenshot Playwright | Gate | WP-PC2/PC3 |

WP-PC1 può girare in parallelo a WP-PC2 (domini disgiunti: docs vs frontend).
WP-PC3 dopo WP-PC2 (toccano entrambe il control rail HI-LO → no conflitto in parallelo).

---

## WP-PC1 — Doc-state reconciliation (igiene)

**Perché:** due dashboard sono stale e ingannano chi subentra.
**Scope (KIMI, solo `docs/`):**
- `CROSS_GAME_BONIFICA_PROGRAM_2026-06-04.md`: aggiornare le celle di stato vecchie — master schedule riga #9 "DIV-07..10 = da fare" → DONE; tabella "Ordine e stato (tronco backend dettaglio)" (DIV-03 "IN CORSO", DIV-05/06 "da decidere", DIV-02 "dopo step 4", DIV-07..10 "pacchetto finale") → tutte DONE, coerenti col footer "COMPLETO".
- `ACTIVE_OPEN_LOOPS.md`: bumpare "Last meaningful update" a 2026-06-09; chiudere le righe ora superate (Cross-game parity audit, launch-token uniform, DIV-06c, test stale-error-shape, test-infra timeout, cross-game FRONTEND parity con stato F07/F08 residui); P0 "prossima azione" = gate documentale COINS.

**Gate CTO (evidence):** diff per file; grep che nessuna cella dica più "da fare/IN CORSO/da decidere" per item chiusi; nessun file fuori da `docs/` toccato.
**Stima prompt:** Brief 0 (gli edit esatti li do io nel prompt) · Esec 1 · Gate CTO 1 · Review Michele 0. **~2.**
**Stop-and-ask:** nessuno.

## WP-PC2 — F08 bet input decimale (CONSISTENZA, non add)

**Nota scoperta 2026-06-09 (CTO, read-only):** l'audit DIV-F08 è PARZIALMENTE STALE. Tutti e 3 i giochi usano GIÀ `inputMode="decimal"` (Mines incluso: `mines-gameplay.tsx:740,756`) e parsano con `parseFloat`. Quindi F08 NON è "aggiungere il decimale" ma **uniformare a 2dp + normalizzatore**. Gap candidati: (a) normalizzatore Mines `normalizeWholeChipInput` (arrotonda a intero → scarta i decimali); (b) display inconsistente (`hi-lo-replay-viewer.tsx:297 toFixed(4)` vs BOXE 2dp); (c) verificare che il backend Mines accetti bet decimali.

**Target deciso:** input decimale ovunque; display cliente 2dp; backend 6dp (già).
**Split (incognite stato reale ≠ audit):**
- **Parte A (KIMI, read-only):** mappa stato attuale (inputMode/normalizzatore/parse-invio/schema backend/display) per i 3 giochi → STOP CTO. Prompt: `docs/PROMPT_KIMI_WP_PC2A_BET_DECIMAL_MAP_2026-06-09.md`.
- **Gate CTO Parte A** → confermo i punti di modifica (e se serve un cambio backend).
- **Gate Parte A: ✅ PASS 2026-06-09** (CTO verificato a mano: backend Mines `_parse_bet_amount` accetta decimali `mines/service.py:799`; bet usa `normalizeBetInput`, whole-chip solo table-entry; formatter `helpers.ts:175/220`). Esito: **nessun cambio backend, normalizzatori OK; gap = solo display**. Decisione visiva Michele 2026-06-09: **importi CHIP sempre 2 decimali** ("5.00"), separatori attuali invariati (punto decimale, no grouping).
- **Parte B (KIMI):** unificare display amount su **sempre 2dp** (rimuovere lo strip `.00` in BOXE/HI-LO gameplay; Mines+replay già 2dp; allineare moltiplicatore replay HI-LO `toFixed(4)→` formato gameplay). Solo display, zero money-flow/backend. Prompt: `docs/PROMPT_KIMI_WP_PC2B_BET_DISPLAY_2DP_2026-06-09.md`.

**Gate CTO Parte B (evidence):** `tsc --noEmit` + build Next.js verdi; test bet-input/smoke verdi sui 3 giochi; prova che il valore inviato al backend resta consistente (no perdita precisione, no doppio arrotondamento); diff per file.
**Stima prompt:** Parte A: Brief 1 · Esec 1 · Gate 1 — Parte B: Esec 1-2 · Gate 1 · Review Michele (desktop) 1. **~5-7.**
**Stop-and-ask:** se il backend Mines rifiuta bet decimali (vincolo int-only) → è un cambio backend, espande lo scope: fermarsi e segnalare.

## WP-PC3 — F07 HI-LO mobile layout (rischio ALTO)

**Inquadramento (CTO 2026-06-09):** NON è un mobile rotto — il portrait HI-LO è già accettato giocabile (AMBER chiuso). DIV-F07 = **parità architetturale**: HI-LO fa mobile CSS-driven con suo `matchMedia` (`hi-lo-gameplay.tsx:194`), non usa i primitive React condivisi (`useMobileLayout`/`GameMobileControlStack`/`GameMobileSettingsSheet`). HI-LO è card-centrico → i primitive (nati per board) potrebbero non calzare. Esito legittimo: migrare **oppure** documentare eccezione by-design (clean se motivata; "nessun gioco-template unico").
**Approccio (Parte A investigativa, poi decisione CTO):**
- **Parte A (KIMI, read-only):** mappa mobile HI-LO attuale vs primitive condivisi; **prova il gap reale** (screenshot/DOM portrait 390×844 + short-landscape 740×360); valuta il **fit** sulla card-UI; propone (a) migrazione piena / (b) parziale solo-hook / (c) eccezione documentata + raccomandazione. STOP CTO. Prompt: `docs/PROMPT_KIMI_WP_PC3A_HILO_MOBILE_MAP_2026-06-09.md`.
- **Gate CTO Parte A** → decido refactor vs eccezione documentata (input visivo Michele solo se emerge un miglioramento UX reale).
- **Parte B (KIMI):** solo se l'esito è migrazione; altrimenti chiudere con doc-exception.

**Gate CTO Parte B (se migrazione):** `tsc` + build verdi; browser-smoke HI-LO mobile verde; **screenshot Playwright viewport mobile** (no scrollbar/clipping); diff per file; real HI-LO invariato.
**Stima prompt:** Parte A: Brief 1 · Esec 1 · Gate 1 — Parte B (se serve): Esec 1-2 · Gate 1. **~3-7** (dipende dall'esito Parte A).

**ESITO Parte A (gate CTO 2026-06-09): ✅ PASS, con un finding RESPINTO. → DIV-F07 CHIUSO senza refactor (Opzione c).** Verificato a mano:
- HI-LO usa GIÀ `GameMobileControlStack` (`hi-lo-gameplay.tsx:1051`) nel branch `useMobileLayout` (:1045) → core DIV-F07 già risolto (audit stale).
- `GameMobileSettingsSheet` non applicabile (HI-LO senza config in-game) → eccezione by-design giustificata.
- **RESPINTO** "How-To-Play 'Continua' tagliato → utente bloccato": il gate condiviso (`game-runtime.css:95,312`) ha `.game-how-to-play-panel{max-height:calc(100svh-36px);overflow-y:auto}` + `.game-how-to-play-continue{position:sticky;bottom:0}` + `onClick={onContinue}` sull'overlay (tap ovunque chiude). Nessun blocco funzionale. Artefatto visivo → ricontrollo in CTO-MOBILE, nessun fix dispatchato.
**DECISIONE CTO:** nessun WP-PC3 Parte B (no refactor rischioso). DIV-F07 chiuso: parità + eccezione documentata. Cleanup OPZIONALE WP-PC3b: estrarre `useMobileLayout` (matchMedia duplicato in 3 file) in hook condiviso `game-runtime/use-mobile-layout.ts` — DRY, COINS lo riusa; 1 prompt KIMI, basso rischio.

## CTO-MOBILE — Parity check finale (io, non KIMI)

Dopo WP-PC2/PC3: screenshot Playwright viewport mobile su Mines/BOXE/HI-LO + reasoning, per chiudere il mobile-check differito del tronco frontend. ~1-2 prompt (CTO).

**ESITO (sign-off CTO 2026-06-09): ✅ PASS.** Evidenza KIMI (screenshot + DOM @390×844, edge :3000, demo):
- Layout: Mines/BOXE/HI-LO board+bet+azioni dentro il viewport, zero clipping, zero scrollbar.
- HI-LO How-To-Play gate: "Continua" non tagliato (bottom 803<844) + tap-overlay chiude → NON bloccante (conferma il finding respinto in WP-PC3).
- Display 2dp: saldo/payout a "N.00".
- **Adjudicazione CTO:** il bet INPUT mostra il valore grezzo ("5"/"5.5"), NON 2dp → corretto (input editabile; forzare 2dp = anti-UX). F08 riguarda i display importo, già a 2dp. Nessun gap.

## STATO FINALE PRE-COINS (2026-06-09)

**Esecuzione COMPLETA, tutti i gate PASS.** WP-PC1 ✅ · WP-PC2 (F08 display 2dp) ✅ · WP-PC3 (F07 → parità già presente + eccezione `GameMobileSettingsSheet` documentata, no refactor) ✅ · CTO-MOBILE ✅. Branch `feature/pre-coins` (commit a9ceb28, 06f0048, d9c7d07). WP-PC3b (DRY hook `useMobileLayout`) rinviato (trivial, non blocca COINS).

**Restano (non-KIMI):** (1) validazione desktop aggregata Michele su :3000; (2) merge `feature/pre-coins` → `main`; (3) accorpare al merge i doc di pianificazione (questo file + prompt) + nota eccezione `GameMobileSettingsSheet` nel Playbook/atlas. Poi: **gate documentale COINS** (6 doc riconciliati a v3.4; `docs/games/coins/*` è pre-bonifica).

---

## Clausola forzante evidenza (in OGNI prompt KIMI)

"Esplicita ciascuna evidenza richiesta nella risposta finale + auto-attestazione.
Se manca anche una sola evidenza = task FAILED a priori; non dichiarare done."

## Stima totale pre-COINS

~12-16 prompt (KIMI esec + gate CTO + 1 review desktop Michele per PC2/PC3 + mobile CTO).

## DECISIONE PRODUCT/PRIORITÀ (Michele) — CHIUSA 2026-06-09

**DECISO: Opzione A — chiudere F07/F08 ORA, prima di COINS.** Scope pieno:
WP-PC1 + WP-PC2 + WP-PC3 + CTO-MOBILE. Baseline frontend pulito, nessun debito di
parità nel gioco 4. F06 (audio HI-LO) resta PARCHEGGIATO (già deciso).

## Dopo questo piano → ingresso COINS (fuori scope "prima di COINS")

Gate documentale COINS: il materiale `docs/games/coins/*` è del 2026-05-25 (pre-bonifica) e va
riconciliato col canonico v3.4 (demo anonimo per tutti, HI-LO canonico demo, host-owned
`platform_rounds`, layering repository+state_machine+round_gateway+typed adapter). Poi i 6
documenti finali (source inventory, decision map, 12-surface status, SPEC, MATH_SPEC,
ARCHITECTURE_MAPPING). **Niente codice COINS prima della chiusura documentale.**
