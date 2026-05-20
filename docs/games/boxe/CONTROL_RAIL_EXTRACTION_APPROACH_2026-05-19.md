Status: ACTIVE
Last meaningful update: 2026-05-19

# BOXE - Control Rail Shared Extraction Approach - 2026-05-19

## 1. Scope And Sources

Questo documento copre solo Parte A del WP
`WP-PLAYER-GAMEPLAY-CONTROL-RAIL-SHARED-EXTRACTION`: validazione approccio prima
dell'esecuzione. Non autorizza modifiche runtime finche' CTO/product owner non
approvano Parte B.

Fonti lette:

- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` v2, inclusi `GameRuntimeShell As
  Platform Pattern`, `Mandatory Game-Agnosticity Audits` e `Pre-Phase Mandatory
  Audits`.
- `docs/NEW_GAME_BRIEF_TEMPLATE.md` v2, in particolare default
  `GameControlRail`, left rail decision e GameRuntimeShell consume.
- `docs/games/boxe/BOXE_FULL_PARITY_AUDIT_2026-05-19.md`, sezioni 2, 5 e 6.
- `frontend/app/ui/mines/mines-gameplay.tsx`,
  `frontend/app/ui/mines/mines-action-buttons.tsx`,
  `frontend/app/ui/mines/mines-balance-footer.tsx`,
  `frontend/app/ui/mines/mines-mobile-settings-sheet.tsx` e CSS rail/mobile in
  `frontend/app/ui/mines/mines.css`.
- `frontend/app/ui/boxe/boxe-gameplay.tsx`,
  `frontend/app/ui/boxe/boxe-settings-panel.tsx`,
  `frontend/app/ui/boxe/boxe-bet-panel.tsx` e CSS correlato.
- `frontend/app/ui/game-runtime/`, incluso `game-runtime.css`.
- Memoria CTO
  `feedback_boxe_visual_uniformity.md`.

Vincoli confermati:

- zero modifiche Mines functional behavior;
- zero backend, schema/migration e `frontend/app/ui/title-editor/`;
- Mines visual baseline invariato e' gate hard;
- BOXE deve ricevere left rail ergonomicamente simile a Mines, non pixel-perfect;
- pattern `GameXxx` in `frontend/app/ui/game-runtime/`.

## 2. Risposta 1 - Granularita' Extraction

Raccomandazione: estrazione scomposta, con `GameControlRail` come shell
composizionale e primitive stateless dedicate:

- `GameControlRail`: contenitore/form/layout lato sinistro, header tools slot,
  settings slot, bet panel slot/action area, footer slot.
- `GameSettingsPanel`: opzionale ma raccomandato come primitive semplice per
  sezioni/righe settings, non come schema completo.
- `GameBetPanel`: input puntata + `GameQuickChips` + action buttons.
- `GameQuickChips`: selector preset importi, riusabile anche in table gate se in
  futuro si vuole deduplicare.
- `GameBalanceFooter`: balance + win/potential win display.
- `GameActionButtons`: BET/COLLECT stateless. Puo' essere interno a
  `GameBetPanel` ma va tenuto esportabile se HI-LO avra' action layout proprio.

Opzione monolitica `GameControlRail` unica:

- pro: minore numero file, prima integrazione piu' veloce;
- pro: minore rischio di incoerenza iniziale fra subcomponenti;
- contro: forza Mines e BOXE a incastrarsi nello stesso contratto, anche dove
  differiscono;
- contro: rende piu' difficile riusare solo quick chips/balance/action in mobile
  o in futuri giochi;
- contro: rischia di creare una "mega-prop API" fragile e Mines-shaped.

Opzione scomposta:

- pro: rispetta il pattern gia' presente in Mines, dove `MinesActionButtons` e
  `MinesBalanceFooter` sono stateless;
- pro: permette migrazione atomica con baseline Mines controllabile dopo ogni
  passo;
- pro: permette a BOXE di consumare la stessa ergonomia senza importare semantica
  Mines;
- pro: HI-LO potra' riusare rail/bet/footer e cambiare solo settings/board;
- contro: piu' file e piu' contratti da nominare bene;
- contro: CSS extraction va fatta con ordine, altrimenti aumenta il rischio di
  specificity drift.

Decisione proposta: scomposta, ma non iper-astratta. Il rail e' shared, lo state
resta nei wrapper di gioco, e le primitive sono "dumb components" con props
esplicite.

## 3. Risposta 2 - Game-Specific Content Delivery

Raccomandazione: pattern A, slot `children`, con piccola libreria di primitive
shared per righe/settings; evitare per ora schema dichiarativo completo e plugin
registry.

Concretamente:

```tsx
<GameControlRail
  header={runtimeToolsSlot}
  settings={<MinesSettingsControls ... />}
  bet={<GameBetPanel ... />}
  footer={<GameBalanceFooter ... />}
/>
```

BOXE passa:

```tsx
settings={<BoxeSettingsControls rows/difficulty ... />}
```

Mines passa:

```tsx
settings={<MinesSettingsControls grid/mines ... />}
```

Valutazione alternative:

- A, slot children: migliore in Parte B perche' non costringe rows/difficulty e
  grid/mines nello stesso schema. Preserva differenze di markup, aria-label,
  form semantics e disabled logic senza far crescere una config DSL.
- B, schema dichiarativo: utile solo se settings sono davvero omogenei. Oggi
  Mines usa grid size e mines count con layout 5 colonne; BOXE usa rows e
  difficulty con una difficulty verticale nel CSS attuale. Lo schema rischia di
  diventare subito pieno di escape hatch.
- C, plugin registry: prematuro per gameplay rail. Il registry e' corretto per
  editor/admin dove registri engine editor; nel runtime gameplay aggiungerebbe
  indirezione senza bisogno. Il Playbook chiede slot/adapters, non un registry
  per ogni surface.

Stop-and-Ask: se durante Parte B BOXE rows/difficulty non si riescono a rendere
con le primitive slot senza forkare meta' rail CSS, fermarsi e valutare un
`GameSettingGroup` piu' strutturato. Non partire da registry.

## 4. Risposta 3 - State Management

Il control rail non deve mantenere state di gameplay. Deve essere controlled via
props/callbacks dai wrapper.

Pattern Mines attuale:

- `MinesGameplay` riceve o calcola `controlGridSize`, `controlMineCount`,
  `betAmount`, `visibleBalance`, `potentialPayout`, `busyAction`,
  `isActiveRound`, `isInteractionLocked`, `hasTableBudget`;
- settings, bet, action e footer sono derivati da props/stato di gameplay;
- `MinesActionButtons` e `MinesBalanceFooter` sono gia' stateless;
- unico state locale legittimo nel rail/mobile e' UI-only, ad esempio
  `showMobileSettings`, non stato economico o round state.

Pattern BOXE attuale:

- `BoxeGameplay` mantiene `selectedRows`, `selectedDifficulty`, `betAmount`,
  `wallets`, `round`, `picks`, `busyAction`;
- `BoxeSettingsPanel` e `BoxeBetPanel` sono gia' controllati via props.

Decisione: `GameControlRail`, `GameBetPanel`, `GameQuickChips`,
`GameBalanceFooter` e action buttons devono essere stateless. L'unica eccezione
ammessa e' stato UI transient non economico in un wrapper mobile, se estratto.

## 5. Risposta 4 - CSS Scope E Rischi Mines Baseline

Rischio principale: Mines visual baseline non dipende solo da classi locali
isolate. Dipende da una combinazione di:

- classi globali riusate (`quick-chip`, `choice-chip`, `field`, `button`);
- selector contestuali `.mines-product-shell ...`;
- selector molto specifici `.mines-product-shell.mines-product-shell-embedded
  .mines-control-rail ...`;
- media query mobile/landscape in `mines.css`;
- layout strutturale `.mines-grid > .stack:first-child` e
  `.mines-grid > .stack:last-child`.

Approccio CSS raccomandato:

1. Promuovere le classi nuove in `game-runtime.css` con prefisso
   `game-control-*`, senza cancellare subito le classi Mines.
2. In prima migrazione, permettere a Mines di mantenere classi legacy come
   compat aliases, ad esempio `className="game-control-rail mines-control-rail
   mines-control-rail-clean"`.
3. Spostare solo CSS necessario alle primitive shared, non tutto il blocco
   `mines.css`.
4. Evitare wrapper DOM aggiuntivi intorno a form/rail/footer se alterano
   selector come `.mines-grid > .stack:first-child`.
5. Fare diff visuale Mines desktop/mobile prima di far consumare BOXE.

Stop-and-Ask obbligatorio se:

- una classe Mines deve essere rimossa invece che aliasata;
- il DOM wrapper aggiuntivo cambia layout di `.mines-grid`;
- `game-runtime.css` introduce selector generici su `.button`, `.field`,
  `.quick-chip` fuori da scope `game-control-*`;
- baseline Mines diventa rossa per piu' di micro-diff non spiegato.

## 6. Risposta 5 - Mobile Responsive

Mines mobile non e' solo CSS. E' misto JS + CSS:

- JS: `useMobileLayout` decide DOM diverso. In mobile Mines non renderizza il
  desktop rail; renderizza `mines-mobile-layout`, `mines-mobile-play-stack`,
  `mines-mobile-bet-panel`, `mines-mobile-settings-summary` e
  `MinesMobileSettingsSheet`.
- CSS: dimensioni, stack, grid quick chips, bottom sheet, board sizing e
  media query sono in `mines.css`.

Decisione: Parte B deve estrarre un pattern responsive shared minimo, non
lasciare BOXE a re-implementare da zero.

Per non allargare troppo il WP, il minimo consigliato e':

- desktop: `GameControlRail` shared consumato da Mines e BOXE;
- mobile: `GameMobileControlStack` o pattern equivalente che riusa
  `GameBetPanel`, `GameBalanceFooter`, action buttons e settings summary;
- mobile settings sheet: promuovere `MinesMobileSettingsSheet` a
  `GameMobileSettingsSheet` solo se la migrazione desktop resta stabile.

No, BOXE non dovrebbe re-implementare il responsive rail in CSS locale. Sarebbe
la stessa scorciatoia che ha prodotto la divergenza attuale.

## 7. Risposta 6 - Audio/Info Buttons

Audio e info button sono runtime tools, non core bet rail. Nel codice Mines
sono visualmente dentro la rail header, ma semanticamente appartengono al futuro
WP `GameRuntimeTools`.

Decisione proposta:

- `GameControlRail` deve avere un `headerTools` slot.
- In Parte B, Mines puo' continuare a passare `MinesRuntimeTools` e info button
  nello slot, senza estrarli.
- BOXE puo' passare placeholder/tool slot minimo solo se gia' disponibile nello
  scope approvato; altrimenti non inventare runtime tools completi in questo WP.
- Non estrarre rules modal, replay viewer o audio event map in questo WP.

Stop-and-Ask se il CTO vuole che BOXE abbia info/audio gia' nel rail in Parte B:
quello sovrappone questo WP con `WP-RUNTIME-TOOLS-RULES-REPLAY-SHARED`.

## 8. Risposta 7 - Stop-And-Ask Conditions

Stop-and-Ask probabili e risposta preventiva:

| Scenario | Decisione Parte A |
| --- | --- |
| Mines rail accoppiata a session/launch context Mines-specific | Rail shared resta controlled; se servono props Mines-only, tenerle nel wrapper e passare solo dati gia' formattati. |
| BOXE rows/difficulty non mappano pulitamente | Usare settings slot. Se anche lo slot richiede CSS divergente massiccio, fermarsi e proporre `GameSettingGroup`. |
| Mines visual baseline rossa per DOM wrapper | Non accettare baseline refresh. Ridurre wrapper o aliasare classi legacy. |
| CSS conflict con `game-runtime.css` | Scope `game-control-*`; no selector globali. Se conflitto persiste, fermarsi. |
| Quick chips BOXE oggi assenti | Aggiungerli via `GameQuickChips` nel rail shared; valori possono seguire Mines default `[1,2,5,10,25]` salvo diversa decisione product. |
| BOXE primary action oggi singola BET/COLLECT | Usare action model shared con due affordance se product vuole ergonomia Mines. Se invece BOXE deve avere un solo pulsante dinamico, dichiararlo come override product. |
| Mobile BOXE richiede board-specific layout | Board resta game-specific; stack controlli condiviso. |

## 9. Risposta 8 - Effort Revisionato

La stima audit 5-8 prompt resta valida solo se Parte B viene scomposta e
protetta da gate visuali.

Stima finale raccomandata:

- Parte A: 1-2 prompt, docs-only.
- Parte B minima desktop + Mines baseline hard gate: 4-6 prompt.
- Parte B con mobile shared accettabile e BOXE baseline aggiornata: 6-9 prompt.

Quindi aggiusto leggermente la stima complessiva da 5-8 a **6-9 prompt** se il
mobile e' incluso come gate del WP. Se il CTO limita Parte B al desktop rail,
**5-7 prompt** e' realistico.

Motivo: il codice TSX e' gia' abbastanza controllato; il rischio reale e' CSS
specificity + baseline Mines + mobile DOM alternativo.

## 10. Diagramma Architetturale Proposto

```text
MinesGameplay / BoxeGameplay
  owns state, API calls, round semantics, copy resolver
  |
  | props / callbacks / game-specific children
  v
frontend/app/ui/game-runtime/
  GameControlRail
    headerTools slot
      Mines: info button + MinesRuntimeTools
      BOXE: runtime tools slot, deferred if WP overlap
    settings slot
      MinesSettingsControls: grid size + mines count
      BoxeSettingsControls: rows + difficulty
    GameBetPanel
      GameQuickChips
      bet input
      GameActionButtons
    GameBalanceFooter
      balance + win/potential collect display
  GameMobileSettingsSheet / mobile stack (if approved in Parte B)
    settings children
    shared mobile ergonomics
  |
  v
game-specific board/stage
  MinesBoard / MinesStageHeader
  BoxePyramidBoard / Boxe payout and future stage header
```

Boundary:

- `game-runtime/` non importa `mines/` o `boxe/`.
- `mines/` e `boxe/` importano componenti `game-runtime/`.
- Board, payout semantics, replay payload e backend restano game-specific.

## 11. Sub-WP Plan Per Parte B

Piano consigliato, con commit atomici:

1. `GameBalanceFooter` + `GameActionButtons`
   - Promuovere da Mines a game-runtime come componenti stateless.
   - Mines consuma i nuovi componenti con classi legacy aliasate.
   - Gate: Mines desktop/mobile visual unchanged.

2. `GameQuickChips` + `GameBetPanel`
   - Estrarre input puntata, quick chips e action composition.
   - Mines mantiene valori/copy/disabled logic identici.
   - Gate: no cambio functional behavior puntata/start/cashout.

3. `GameControlRail`
   - Estrarre contenitore desktop con `headerTools`, `settings`, `bet`,
     `footer`.
   - Mines consuma shell shared senza cambiare DOM critico oltre il minimo.
   - Gate: Mines visual baseline hard.

4. BOXE consume
   - Spostare settings + bet/balance/action nel lato sinistro shared.
   - BOXE board resta game-specific nel lato destro.
   - Aggiungere quick chips e balance/win footer coerenti con Mines.
   - Gate: BOXE baseline aggiornata per left rail correctness.

5. Mobile shared slice, se approvato nello stesso WP
   - Promuovere mobile bet/settings sheet pattern solo dopo desktop stabile.
   - Gate: Mines mobile portrait invariato; BOXE mobile non torna a dashboard
     stack locale.

## 12. Capability Matrix

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Stato | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Parte A approach validation | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NEW | COMPLETE | Docs-only, nessun codice runtime toccato. |
| GameActionButtons shared | n/a | n/a | n/a | n/a | UPDATED shared primitive | UPDATED `game-runtime.css` | Covered by build, smoke consumers, boundary static check | UPDATED | EXTRACTED | Stateless BET/COLLECT primitive; BOXE preserves legacy `boxe-primary-action` on the active command. |
| GameBalanceFooter shared | n/a | n/a | n/a | n/a | UPDATED shared primitive | UPDATED `game-runtime.css` | Covered by visual/smoke consumers | UPDATED | EXTRACTED | Balance + win/potential payout footer shared by Mines and BOXE. |
| GameQuickChips shared | n/a | n/a | n/a | n/a | UPDATED shared primitive | UPDATED `game-runtime.css` | Covered by BOXE quick chip smoke path and build | UPDATED | EXTRACTED | BOXE now exposes Mines-style quick chip affordance `[1,2,5,10,25]`. |
| GameBetPanel shared | n/a | n/a | n/a | n/a | UPDATED shared primitive | UPDATED `game-runtime.css` | Covered by BOXE round smoke and Mines compile gate | UPDATED | EXTRACTED | Controlled bet input + optional quick chips + action slot. |
| GameSettingsPanel shared | n/a | n/a | n/a | n/a | UPDATED shared primitive | UPDATED `game-runtime.css` | Covered by build and consumer smoke | UPDATED | EXTRACTED | Simple settings wrapper only; game-specific settings remain in Mines/BOXE. |
| GameControlRail shell | n/a | n/a | n/a | n/a | UPDATED shared shell | UPDATED scoped classes + legacy aliases | Covered by build, smoke and manual screenshot review | UPDATED | EXTRACTED | Composition shell with settings, bet panel and footer slots. |
| GameMobileControlStack shared | n/a | n/a | n/a | n/a | UPDATED mobile primitive | UPDATED scoped mobile CSS | Covered by build; mobile smoke remains gate item | UPDATED | EXTRACTED | Mobile layout primitive; no gameplay state inside shared component. |
| GameMobileSettingsSheet shared | n/a | n/a | n/a | n/a | UPDATED mobile primitive | UPDATED scoped mobile CSS | Covered by build; Mines mobile visual remains follow-up gate evidence | UPDATED | EXTRACTED | Promoted Mines sheet shape without importing Mines code. |
| Mines consumes shared rail primitives | n/a | n/a | n/a | n/a | UPDATED with same behavior target | UPDATED with `.mines-control-rail` aliases retained | Build PASS; smoke infra issue tracked separately | UPDATED | REFACTORED | Legacy classes remain present to protect `.mines-product-shell` and `.mines-grid` selectors. |
| BOXE consumes shared rail primitives | n/a | n/a | n/a | n/a | UPDATED left rail, quick chips, action buttons, balance footer | UPDATED compact BOXE rail CSS | BOXE smoke PASS; screenshot `1365x768` after fit | UPDATED | REFACTORED | Board remains game-specific; visual baseline needs CTO refresh decision after accepted rail design. |

## 13. CTO Recommendation

Procederei con Parte B solo se CTO approva questi punti:

- estrazione scomposta, non monolite;
- settings via slot children, non schema/registry per ora;
- componenti stateless controlled da wrapper di gioco;
- CSS shared scoped `game-control-*` con alias Mines per proteggere baseline;
- audio/info trattati come header slot, non estratti integralmente in questo WP;
- mobile incluso solo se accettiamo effort 6-9 prompt, altrimenti desktop-first
  5-7 prompt con WP mobile subito dopo.

No, non consiglierei una patch locale BOXE del bet panel. Sarebbe piu' veloce
nel singolo screenshot, ma contraddice il Playbook v2 e fa pagare a HI-LO lo
stesso debito.
