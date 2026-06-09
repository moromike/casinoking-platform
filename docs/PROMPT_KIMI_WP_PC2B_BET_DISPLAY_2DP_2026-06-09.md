# PROMPT KIMI — WP-PC2 Parte B: unifica display importi a sempre-2dp

> Incollare in KIMI. Esecuzione frontend. Branch corrente: `feature/pre-coins`. Gate CTO finale.

## Contesto (delta dalla Parte A, gate PASS)
Parte A ha provato: l'input bet è già decimale ovunque, i backend accettano decimali (nessun cambio backend), i normalizzatori vanno bene. **Unico gap = display formatter incoerente.** Decisione visiva Michele: **importi CHIP SEMPRE a 2 decimali** ("5.00 CHIP"), su tutti e 3 i giochi, gameplay E replay.

## Canonico (vincolante)
- Importi CHIP (bet, saldo, vincita/payout) = **sempre `toFixed(2)`**, niente strip del `.00`.
- **NON introdurre formattazione locale**: niente separatore migliaia, niente virgola decimale. Mantieni lo stile separatore attuale (punto decimale). La decisione è SOLO sul numero di decimali (=2).
- Preferenza architetturale (clean): UN formatter condiviso, non 3 copie locali divergenti. Riusa gli helper condivisi `formatChipAmount`/`formatWholeChipDisplay` (`frontend-v3/app/lib/helpers.ts:175,220`, già sempre-2dp) dove le call-site lo permettono; elimina le varianti locali che strippano.

## Punti di modifica (dalla mappa Parte A — verifica i file:line attuali)
1. **BOXE gameplay** — formatter locale `formatChipAmount` (`boxe-gameplay.tsx:1357`) fa `toFixed(2).replace(/\.00$/, "")`. → rimuovi lo strip (sempre 2dp) o instrada allo shared helper. Verifica tutte le sue call-site nel file restino corrette (suffisso CHIP dove serve).
2. **HI-LO gameplay** — formatter locale `formatChipValue` (`hi-lo-gameplay.tsx:1282`) fa lo stesso strip. → idem.
3. **Mines gameplay** (`formatWholeChipDisplay`) e **tutti i replay viewer** (`formatChipAmount` shared) sono GIÀ 2dp → **nessun cambio** (conferma soltanto).
4. **HI-LO replay multiplier** (`hi-lo-replay-viewer.tsx:297`, `toFixed(4)`): trova come HI-LO mostra il **moltiplicatore live in gameplay** (cita file:line) e **allinea il replay a QUEL formato** per coerenza intra-gioco. (NB: è un moltiplicatore, non un importo CHIP — non forzare 2dp se il gameplay usa di proposito una precisione diversa: in quel caso allinea a gameplay.)
5. `isValidAmount` (`helpers.ts:179`, regex `^\d+(\.\d{1,6})?$`) già accetta decimali → **nessun cambio**.

## Scope boundary
- SOLO il game-runtime (gameplay + replay viewer dei 3 giochi). NON toccare account/statement page, finance admin, table-balance gate: fuori scope F08.
- SOLO display. ZERO modifiche a parse/normalizzazione/invio bet, ZERO backend, ZERO money-flow (idempotency/round/settlement invariati).

## STOP-AND-ASK (ferma e segnala, non improvvisare)
- Se un formatter locale ha differenze comportamentali oltre lo strip (suffisso/locale/edge-case null) che NON mappano 1:1 sullo shared helper → segnala prima di consolidare.
- Se il moltiplicatore live HI-LO non è individuabile o usa una precisione chiaramente intenzionale ≠ 2dp → segnala.

## Commit
`git add -A && git commit -m "WP-PC2: unify chip amount display to always-2dp across Mines/BOXE/HI-LO gameplay+replay"`

## Evidence richiesta nella risposta finale (auto-attestazione)
1. `tsc --noEmit` verde (output) + `npm run build` (frontend-v3) verde (coda output).
2. Diff per file (solo frontend display; conferma nessun file backend/test-money toccato).
3. **Prova di coerenza 2dp**: per ciascuno dei 3 giochi, mostra che un importo intero rende come "N.00" — preferibile assert DOM/browser-smoke o screenshot del bet/saldo (es. bet 5 → "5.00 CHIP"); stessa cosa nel replay.
4. Punto 4: file:line del formato moltiplicatore gameplay HI-LO + conferma che replay ora lo rispecchia.
5. SHA commit + auto-attestazione: "zero modifiche a parse/invio bet, zero backend, zero money-flow; solo display."

**Clausola forzante:** esplicita CIASCUNA evidenza sopra + auto-attestazione. Se manca anche una sola evidenza = task FAILED a priori; non dichiarare done.
