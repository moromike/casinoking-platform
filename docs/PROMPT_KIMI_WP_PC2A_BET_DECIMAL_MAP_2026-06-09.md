# PROMPT KIMI — WP-PC2 Parte A: mappa bet-decimal parity (read-only)

> Incollare in KIMI. **READ-ONLY, niente codice.** Gate CTO a fine Parte A. Branch corrente: `feature/pre-coins`.

## Contesto (delta)
DIV-F08 (audit `docs/CROSS_GAME_FRONTEND_PARITY_AUDIT_2026-06-05.md`) diceva "Mines = `inputMode="numeric"` (interi), outlier". **L'audit è PARZIALMENTE STALE:** oggi Mines usa già `inputMode="decimal"` (`mines-gameplay.tsx:740,756`). Quindi NON aggiungere il decimale dove c'è già. Devi mappare lo **stato REALE attuale** del codice, non l'audit.

**Target deciso (product, handoff 2026-06-06):** input bet **decimale** ovunque; **display cliente a 2 decimali (2dp)**; **backend 6dp** (già). Quick chips interi ok come default.

## Task — per ciascun gioco (Mines / BOXE / HI-LO), con file:line REALI attuali
1. `inputMode` passato a `GameBetPanel` (cita file:line).
2. **Normalizzatore** applicato all'input bet: nome funzione + comportamento (arrotonda a intero? mantiene decimali? quanti dp?) + file:line. (Audit cita `normalizeWholeChipInput` per Mines vs `normalizeBetInput` per BOXE/HI-LO — VERIFICA se è ancora così.)
3. **Parsing+invio** del bet al backend allo start: come viene convertito (parseFloat? arrotondamento? troncamento a 2dp?) e cosa viene spedito (cita file:line).
4. **Backend — accetta bet decimali?** Cita lo schema/validazione del payload di start per ognuno (`mines`, `boxe`, `hi_lo`): tipo del campo bet (Decimal/int/float), eventuali vincoli (`gt`, `multiple_of`, int-only). Domanda chiave: uno start con `bet=1.50` passa la validazione backend di Mines? (cita il modello Pydantic/route).
5. **Display amount** (bet, balance, payout, replay): elenca OGNI formatter usato e i suoi decimali (es. `boxe-gameplay.tsx:1361 toFixed(2)` strip `.00`; `hi-lo-replay-viewer.tsx:297 toFixed(4)`). Marca le incoerenze vs target 2dp.
6. Quick chips: valori attuali per gioco.

## Output (DoD Parte A)
- Tabella per-gioco: colonna **STATO ATTUALE** vs **TARGET (decimale + 2dp)** vs **DELTA** (cosa cambiare in Parte B), con file:line precisi.
- Lista esplicita dei punti di modifica per Parte B (frontend) + **flag se serve un cambio BACKEND** (es. Mines rifiuta decimali).
- Conferma se l'incoerenza `toFixed(4)` HI-LO replay è reale e dove.

## Vincoli
- READ-ONLY: nessun file modificato, nessun commit. Solo analisi + evidenze (file:line, snippet schema).
- Non fidarti dell'audit per lo stato attuale: leggi il codice di oggi.

## STOP-AND-ASK (ferma e segnala al CTO, non procedere)
- Se il **backend Mines rifiuta bet decimali** (vincolo int-only): è un cambio backend → espande lo scope oltre il frontend. Segnalalo, NON proporre workaround.
- Se BOXE/HI-LO hanno semantiche di arrotondamento diverse che toccano il money-flow (non solo display): segnalalo.

## Evidence richiesta nella risposta finale (auto-attestazione)
1. La tabella per-gioco completa (6 punti × 3 giochi) con file:line reali.
2. Lo snippet dello schema backend bet per i 3 giochi (punto 4) — copia-incolla.
3. Lista punti-modifica Parte B + eventuale flag backend.
4. Conferma "READ-ONLY: zero file modificati, zero commit" (`git status` pulito sul tracked).

**Clausola forzante:** esplicita CIASCUNA evidenza sopra + auto-attestazione. Se manca anche una sola evidenza = task FAILED a priori; non dichiarare done. STOP CTO a fine Parte A.
