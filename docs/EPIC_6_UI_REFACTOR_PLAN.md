# EPIC 6: Finalizzazione Sito Web Player - Piano di Refactoring UI/CSS

## Contesto e Obiettivo
L'EPIC 6 mira a rimuovere l'effetto "prototipo" dal sito player. Questo significa uniformare l'aspetto di layout, bordi, ombre e colori (Gerarchia Visiva e CSS) e standardizzare il comportamento interattivo, specialmente per Call To Action (CTA) e stati di caricamento (Loader). L'obiettivo è prevenire i salti ("scatti") visivi dovuti a cambi di testo durante le attese e centralizzare le regole visive di Tailwind o puro CSS.

## Stato Attuale vs Target
* **Attuale:**
  - `globals.css` contiene molte ripetizioni di `border-radius`, `box-shadow` e sfondi per i componenti.
  - Il caricamento (es. Login, Registrazione, Bet in Mines) è gestito alterando il label del `<button>` e disabilitandolo. Questo fa cambiare la larghezza del bottone, causando scatti visivi sgradevoli.
  - Nessun componente UI condiviso per i pulsanti.
* **Target:**
  - Variabili CSS standardizzate per i raggi (`radius`), le ombre (`shadows`) e i gradienti, usate coerentemente ovunque nel `globals.css`.
  - Componente React `<Button>` riutilizzabile che racchiude logica di link/azione e un sistema nativo di `isLoading` con SVG Spinner centrato, preservando la larghezza.
  - Pagine Player pulite senza logica ripetitiva di cambi di testo `isBusy ? "Loading..." : "Submit"`.

## Piano di Azione

### 1. Refactoring CSS in `globals.css`
- Introdurre e utilizzare le variabili:
  ```css
  :root {
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 24px;
    --radius-pill: 999px;
    --shadow-sm: 0 4px 12px rgba(2, 6, 23, 0.15);
    --shadow-md: 0 12px 28px rgba(2, 6, 23, 0.25);
    --shadow-lg: 0 24px 60px rgba(2, 6, 23, 0.34);
    /* Altri colori invariati o riutilizzati */
  }
  ```
- Sostituire globalmente i valori hardcoded (18px, 22px, ecc.) per bordi e le ombre hardcoded con le nuove variabili.

### 2. Creazione Componente `<Button>`
- Creare un nuovo componente `frontend/app/ui/components/button.tsx` in grado di fare sia da `<button>` che da `next/link`.
- Supportare le properties `variant` ("primary", "secondary", "ghost") e `isLoading`.
- Quando `isLoading` è attivo: nascondere l'opacità del testo e mostrare al centro uno spinner CSS/SVG, mantenendo invariato l'ingombro del pulsante per evitare layout shifts.
- Integrare l'animazione `spin` nel `globals.css`.

### 3. Integrazione nelle View Player
- **Autenticazione:** `player-login-page.tsx`, `player-register-page.tsx`. Sostituire `<button>` e `<Link>` e togliere la logica del testo alternato, attivando solo `isLoading={busyAction === '...'}`.
- **Navigazione:** `player-shell.tsx`, `player-lobby-page.tsx`.
- **Account:** `player-account-page.tsx`.
- **Mines:** `mines-standalone.tsx`, `mines-action-buttons.tsx`. Passare la corretta prop `isLoading` (calcolata in base a `busyAction`) e togliere `bet_loading` text modifier.

## TODO List per Code

# TODO List — EPIC 6: UI e CSS Refactoring

## Contesto
Finalizzazione dell'estetica Player. Standardizziamo bordi, ombre e bottoni. Introdotto `<Button>` condiviso con spinner state nativo.

## Pre-condizioni
Leggere `frontend/app/globals.css`, `frontend/app/ui/player-login-page.tsx`, `frontend/app/ui/mines/mines-standalone.tsx`.

## Task

### Task 1: Definizione Variabili e Componente Button
- File: `frontend/app/globals.css`, `frontend/app/ui/components/button.tsx` (da creare)
- Azione:
  1. Aggiungere le variabili CSS per radius (`--radius-sm`, `--radius-md`, `--radius-lg`, `--radius-xl`, `--radius-pill`) e shadow (`--shadow-sm`, `--shadow-md`, `--shadow-lg`) in `:root` di `globals.css`.
  2. Implementare la logica CSS per `.button-content`, `.is-loading`, `.button-spinner` in `globals.css`.
  3. Creare `button.tsx` esportando `<Button>` con props standard (variant, isLoading, href polimorfico).
- Vincoli: Mantenere design dark mode coerente. Il testo originale deve svanire (opacity: 0) quando `is-loading` è presente per evitare il collasso.
- Criterio di completamento: Componente pronto e classi CSS pronte.

### Task 2: Standardizzazione Variabili in CSS Globale
- File: `frontend/app/globals.css`
- Azione:
  - Sostituire le varie occorrenze di `border-radius: 18px`, `22px`, `24px` con `var(--radius-lg)` o `var(--radius-xl)`.
  - Sostituire `border-radius: 999px` con `var(--radius-pill)`.
  - Sostituire le varie regole di `box-shadow` su pannelli e card con `var(--shadow-md)` o `var(--shadow-lg)`.
- Vincoli: Non stravolgere la logica o la griglia di posizionamento.
- Criterio di completamento: Meno hardcoding nel CSS e classi pulite.

### Task 3: Refactoring Auth & Shell
- File: `frontend/app/ui/player-login-page.tsx`, `frontend/app/ui/player-register-page.tsx`, `frontend/app/ui/player-shell.tsx`
- Azione:
  - Sostituire `Link` "button" e `<button>` classici con il componente `<Button>`.
  - In Login/Register, rimuovere il text flip (es. `busyAction === 'login' ? "Signing in..." : "Sign in"`) tenendo il testo standard "Sign in" e passando `isLoading={busyAction === "login"}`.
- Criterio di completamento: I form di auth usano il nuovo loader senza "scatti".

### Task 4: Refactoring Lobby e Account
- File: `frontend/app/ui/player-lobby-page.tsx`, `frontend/app/ui/player-account-page.tsx`
- Azione:
  - Aggiornare i CTA principali a usare il `<Button>`.
- Criterio di completamento: Pagine uniformate.

### Task 5: Refactoring Mines UI
- File: `frontend/app/ui/mines/mines-standalone.tsx`, `frontend/app/ui/mines/mines-action-buttons.tsx`
- Azione:
  - In `mines-action-buttons.tsx`: Convertire `Bet` e `Collect` in `<Button>`. Accettare le props `isBetLoading` e `isCollectLoading` da parent.
  - In `mines-standalone.tsx`: Rimuovere il fallback `bet_loading` e `collect_loading` (tenere i label originali sempre). Passare a `MinesActionButtons` le flag loader.
- Criterio di completamento: Quando un giocatore betta, il pulsante non cambia grandezza ma mostra uno spinner.

## Ordine di esecuzione
I task dal 1 al 5 devono essere eseguiti in sequenza.

## Rischi e attenzioni
- Cambiare i border-radius può avere side-effect su layout molto affollati (es. card Admin).
- In Mines, non alterare i `disabled` attr e la logica state-machine di base.
- Nessuna validazione Ask è necessaria, si tratta puramente di frontend UI/UX senza impatti sul ledger o session state.