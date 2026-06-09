# Site V3 Recovery - Game Re-Break Analysis

Data: 2026-05-31

Stato: ANALISI ONLY. Nessun fix applicato in questo passaggio.

## Baseline corretta

La baseline visiva giochi resta `main` / Phase 1, non il backup `6141c17`.

Artifact di riferimento:
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-mines-desktop.png`
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-hi-lo-desktop.png`
- `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/game-boxe-desktop.png`
- varianti mobile nella stessa cartella.

Errore procedurale individuato: nell'ultimo ciclo ho trattato il backup `6141c17` come se fosse una sorgente sicura per ripristinare il visuale giochi. Non lo e. `6141c17` e utile per forensic/code recovery, ma la parita visiva giochi deve essere misurata contro `main` Phase 1.

## Stato working tree rilevante

File coinvolti nello stato attuale:
- `frontend-v3/app/globals.css` e sia staged sia unstaged (`MM`): stato CSS ad alto rischio perche mescola due layer di modifiche.
- `frontend-v3/app/ui/game-runtime/game-runtime.css`: modificato.
- `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx`: modifica UI X close embedded.
- `frontend-v3/app/ui/boxe/boxe-gameplay.tsx`: modifica UI X close embedded.

Non ho rilevato in questa lettura una modifica game-logic su RNG/math/payout/board/reveal. Le regressioni visive attuali puntano a CSS/layout/runtime UI, non a matematica gioco.

## Regressioni riaperte

### R0 - Host game troppo grande

File sospetto: `frontend-v3/app/globals.css:2100`.

Blocco corrente:
- `.site-v3-game-shell` usa `padding: 0.75rem` e `overflow: hidden`.
- `.site-v3-game-host` usa `height: calc(100vh - 1.5rem)` e `max-width: 1440px`.

Effetto osservato:
- a 1280px wide il frame corrente occupa quasi tutta la viewport (`x` circa 12, larghezza circa 1256), mentre la baseline Phase 1 era piu contenuta e centrata.
- Mines e HI-LO diventano piu larghi del target, il contenuto si ridistribuisce e le celle/board risultano fuori proporzione o tagliate.

Classificazione: regressione container.

### R1 - HI-LO impaginato male

File sospetti:
- `frontend-v3/app/globals.css:2107`
- `frontend-v3/app/ui/game-runtime/game-runtime.css:669`
- `frontend-v3/app/ui/game-runtime/game-runtime.css:797`
- `frontend-v3/app/ui/game-runtime/game-runtime.css:814`

Stato reale:
- la X e presente, ma la scala e il posizionamento sono trascinati dal container troppo largo.
- input puntata e bottoni si presentano raw/rettangolari rispetto alla baseline.
- `game-bet-field` oggi definisce solo `display/grid/gap`; non c'e una regola runtime scoped per l'input.
- `game-action-buttons` oggi definisce solo `display/grid/gap`; non c'e una regola runtime scoped completa per `.button` e `.button-secondary`.

Classificazione: regressione contenuto/layout, non evidenza di break funzionale math.

### R2 - Mines DEMO / info spacing e celle

File sospetti:
- `frontend-v3/app/globals.css:2100`
- `frontend-v3/app/ui/game-runtime/game-runtime.css:669`

Stato reale:
- baseline: badge `DEMO` separato, pill coerente, rail compatto.
- stato attuale: badge/pulsante info risultano vicini o su righe non coerenti a seconda della larghezza; il layout diventa fragile.
- `game-mode-badge` oggi ha solo border/background/color/white-space; manca una definizione stabile di pill/flex/min-size/padding.
- la board grande/tagliata deriva principalmente dal frame host troppo largo e alto rispetto alla baseline.

Classificazione: regressione container + contenuto.

### R3 - BOXE gate saldo diverso dagli altri

File sospetti:
- `frontend-v3/app/ui/game-runtime/game-runtime.css:472`
- `frontend-v3/app/ui/game-runtime/game-runtime.css:506`

Stato reale:
- il gate saldo BOXE usa `GameTableBalanceGate`.
- `.game-table-balance-entry-field` oggi definisce solo `gap: 8px`; l'input non riceve stile runtime dedicato.
- `.game-table-balance-gate .button` imposta min-height/radius/font-weight, ma non garantisce background/color/layout completi.
- dopo l'isolamento CSS, le vecchie regole generiche `.field input` non passano piu nei giochi; questo era corretto come confine admin/CMS, ma manca il rimpiazzo scoped runtime per i gate gioco.

Classificazione: regressione contenuto CSS/runtime. Non evidenza di problema backend table session.

### R4 - X close nei file gioco

File toccati:
- `frontend-v3/app/ui/hi-lo/hi-lo-gameplay.tsx`
- `frontend-v3/app/ui/boxe/boxe-gameplay.tsx`

Stato reale:
- HI-LO: la X embedded e stata resa sempre visibile rimuovendo il gate `!bootRequest.isEmbeddedView`.
- BOXE: la X embedded e stata resa visibile anche in embedded desktop rimuovendo `!bootRequest.isEmbeddedView` dalla condizione.

Queste modifiche non spiegano i bottoni raw o il gate saldo BOXE, ma sono comunque tocchi UI dentro file gioco e vanno mantenuti sotto controllo di parita visiva.

## Causa radice

La causa radice non e una singola proprieta CSS. E una sequenza sbagliata:

1. Ho fatto scoping/revert CSS per proteggere admin/CMS.
2. Ho poi usato il backup `6141c17` come sorgente per "ripristinare" parti del runtime.
3. Questo ha reintrodotto/lasciato uno stato dove i controlli runtime condivisi non hanno piu gli stili necessari, mentre il game host e tornato troppo largo.
4. Non ho gated ogni micro-step con screenshot side-by-side contro `main` Phase 1 prima di procedere.

## Cosa non va fatto adesso

- Non rifare i giochi.
- Non cambiare RNG/math/payout/board/reveal.
- Non toccare backend GMP.
- Non inventare un nuovo layout.
- Non usare `6141c17` come baseline visiva.

## Next step proposto, prima di qualsiasi fix

1. Freeze codice giochi e CSS runtime.
2. Generare un mini-inventario "current broken" per:
   - Mines desktop/mobile gameplay.
   - HI-LO desktop/mobile gameplay.
   - BOXE desktop/mobile gameplay.
   - gate saldo BOXE/HI-LO/Mines dove presenti.
3. Per ogni superficie, confrontare side-by-side con `baseline-main`.
4. Preparare una patch minima con due soli gruppi:
   - host frame: riportare `.site-v3-game-host` a dimensioni compatibili con baseline;
   - runtime controls: ripristinare solo input/bottoni/badge/gate saldo sotto selettori `game-*`.
5. Eseguire screenshot gate dopo ogni micro-patch.

Nessun fix e stato applicato in questa analisi.
