# PROMPT KIMI — CTO-MOBILE evidence pass (read-only capture)

> Incollare in KIMI **dopo** conferma che `:3000` è healthy. READ-ONLY: nessun file modificato, nessun commit. Solo Playwright + screenshot + misure DOM. Il CTO valuta.

## Scopo
Raccogliere l'evidenza per il sign-off CTO finale del tronco pre-COINS: (1) parità layout mobile dei 3 giochi, (2) verifica visiva del display 2dp (WP-PC2), (3) conferma che il How-To-Play gate NON blocca su portrait (chiusura del finding respinto in WP-PC3 Parte A). Branch attivo del codice servito: `feature/pre-coins` (frontend rebuildato).

## Setup
- Target: public edge **http://localhost:3000** (canonico Michele).
- Viewport mobile: **portrait 390×844**. Modalità **demo/anonima (no login)** per ciascun gioco.
- Browser: Playwright (chromium), device scale realistico.

## Per ciascun gioco (Mines / BOXE / HI-LO)
1. Avvia il gioco in demo, supera eventuali gate (How-To-Play, table-balance non si applica al demo), raggiungi il gameplay.
2. **Display 2dp:** imposta un bet intero (es. `5`) e cattura screenshot + il TESTO DOM del campo bet e del saldo → devono mostrare **"5.00"** (e relativo suffisso CHIP dove previsto). Poi prova un decimale (es. `5.5`) → "5.50".
3. **Layout mobile:** misure DOM (bounding box + overflowX/overflowY + presenza scrollbar) di board, bet input, action buttons. Atteso: **niente scrollbar, niente clipping**, controlli dentro il viewport.
4. Screenshot del gameplay a 390×844.

## HI-LO specifico (chiusura finding respinto)
5. All'apertura del How-To-Play gate su portrait 390×844: cattura screenshot e **conferma che il bottone "Continua" è raggiungibile** (è `position:sticky;bottom:0` nel pannello con `overflow-y:auto`) **e/oppure** che un tap sull'overlay chiude il gate (`onClick` sull'overlay). Atteso: il gate NON blocca — l'utente entra nel gameplay. Riporta come si è chiuso il gate.

## Vincoli
- READ-ONLY. Zero file modificati, zero commit. Solo evidenza.
- Se un gioco NON raggiunge il gameplay in demo su mobile → è un problema reale: cattura lo stato e FERMATI segnalando (non dichiarare done).

## Evidence richiesta nella risposta finale (auto-attestazione)
1. Per i 3 giochi: screenshot gameplay 390×844 + testo DOM bet/saldo con valori 2dp ("5.00", "5.50").
2. Per i 3 giochi: misure DOM board/bet/actions (box + overflowX/Y + scrollbar) → conferma no-clip/no-scroll.
3. HI-LO: screenshot del How-To-Play gate + descrizione di come è stato chiuso (bottone sticky raggiungibile o tap-overlay) → conferma NON bloccante.
4. Conferma "READ-ONLY: zero file modificati, zero commit" (`git status` pulito sul tracked).

**Clausola forzante:** esplicita CIASCUNA evidenza sopra + auto-attestazione. Se manca anche una sola evidenza (in particolare gli screenshot mobile reali e i valori 2dp) = task FAILED a priori; non dichiarare done.
