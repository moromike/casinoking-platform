Status: ACTIVE
Last meaningful update: 2026-05-20

# BOXE - Visual Uniformity Approach - 2026-05-20

WP: `WP-V-VISUAL-UNIFORMITY` - Parte A, approach validation.

## 1. Scope Decision

Questo documento copre solo Parte A. Non autorizza modifiche runtime finche'
CTO/product owner non approvano Parte B.

Obiettivo: allineare il gameplay player-facing BOXE al reference Mines per
shell, top bar, chip, action buttons, balance footer e rimozione dei tre
elementi product gia' decisi:

- tag `98% RTP`;
- eyebrow `BOXE001` / `title_code`;
- barra stato `IDLE / Scegli box sicura`.

Out of scope confermati:

- nessun backend;
- nessuna migration/schema;
- nessun title-editor/admin;
- nessun cambio di board geometry BOXE, che resta ownership WP-G;
- nessuna modifica funzionale Mines oltre al consumo compatibile di primitive
  shared.

## 2. Fonti Lette

- `AGENTS.md` come puntatore, non fonte primaria.
- `docs/SOURCE_OF_TRUTH.md`.
- `docs/TASK_EXECUTION_GUARDRAILS.md`.
- `docs/DOCUMENTATION_MAINTENANCE.md`.
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`.
- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`, sezioni 6.3 e 13.1.
- `docs/games/boxe/BOXE_FULL_PARITY_AUDIT_2026-05-19.md`.
- `frontend/app/layout.tsx`.
- `frontend/app/ui/game-runtime/`, in particolare primitive gia' estratte e
  `game-runtime.css`.
- `frontend/app/ui/mines/mines-standalone.tsx`.
- `frontend/app/ui/mines/mines-gameplay.tsx`.
- `frontend/app/ui/mines/mines-stage-header.tsx`.
- `frontend/app/ui/mines/mines-runtime-tools.tsx`.
- `frontend/app/ui/mines/mines.css`.
- `frontend/app/ui/boxe/boxe-standalone.tsx`.
- `frontend/app/ui/boxe/boxe-gameplay.tsx`.
- `frontend/app/ui/boxe/boxe-settings-panel.tsx`.
- `frontend/app/ui/boxe/boxe-payout-display.tsx`.
- `frontend/app/ui/boxe/boxe.css`.
- `tests/contract/test_game_runtime_frontend_boundary.py`.
- `tests/integration/test_boxe_smoke.py`.

Mockup BOXE aperti come riferimento visivo:

- `assets/Games/boxe/boxe2 stato idle base .png`;
- `assets/Games/boxe/boxe4.png`;
- `assets/Games/boxe/boxe5.png`;
- `assets/Games/boxe/boxe6.png`;
- `assets/Games/boxe/boxe7.png`.

## 3. Controproposta Su Multiagentica Parte B

Il brief chiede due WP paralleli, ma WP-V e WP-G hanno overlap potenziale su
`frontend/app/ui/boxe/boxe.css`. Il Playbook dice che la multiagentica si attiva
solo con write scope file-isolated o con piano di merge chiaro
(`docs/NEW_GAME_INTEGRATION_PLAYBOOK.md:651`).

Decisione proposta:

1. Parte A resta doc-only nel worktree principale.
2. Parte B puo' partire in due worktree separati solo se:
   - WP-V tocca product shell, top bar, controls e classi non board;
   - WP-G tocca solo `.boxe-pyramid-*`, board component e ladder/board area;
   - ogni modifica CSS comune viene spostata in `game-runtime.css`, non
     duplicata in `boxe.css`.
3. Se durante Parte B entrambi devono modificare gli stessi blocchi di
   `boxe.css`, STOP: serializzare, con WP-V prima, perche' la shell visuale e'
   il reference player-facing della wave.

## 4. Tabella Divergenze Pre/Post

| # | Divergenza | Current evidence | Post-fix proposto |
| ---: | --- | --- | --- |
| 1 | Product shell BOXE non usa shell Mines/reference. | Mines compone `productShellClassName` con `mines-product-shell` e varianti in `frontend/app/ui/mines/mines-standalone.tsx:374`; BOXE passa solo `boxe-product-shell` in `frontend/app/ui/boxe/boxe-standalone.tsx:313`. CSS BOXE ridefinisce width, min-height, padding e background in `frontend/app/ui/boxe/boxe.css:8`. | Estrarre `.game-product-shell` in `game-runtime.css`; Mines usa `game-product-shell mines-product-shell ...`, BOXE usa `game-product-shell boxe-product-shell`. |
| 2 | Dimensioni shell desktop divergenti. | Mines desktop centra una shell `width: min(1160px, calc(100vw - 32px))` e altezza controllata in `frontend/app/ui/mines/mines.css:1243`; BOXE usa `width: min(1040px, 100%)` e min-height in `frontend/app/ui/boxe/boxe.css:8`. | Portare dimensioni/padding shell condivise in `.game-product-shell`; lasciare solo token game-specific se necessari. |
| 3 | Top bar Mines esiste come composizione ricca, BOXE ha header locale minimale. | Mines `MinesStageHeader` renderizza title centrato e close in `frontend/app/ui/mines/mines-stage-header.tsx:138`; runtime tools con clock/audio sono in `frontend/app/ui/mines/mines-runtime-tools.tsx:67`; BOXE header e' locale in `frontend/app/ui/boxe/boxe-gameplay.tsx:500`. | Estrarre `GameTopBar` in `game-runtime/`: slot info, clock/audio tools, mode badge, title/logo, close button. Mines deve consumarlo senza diff visuale. |
| 4 | Eyebrow `BOXE001` visibile solo su BOXE. | BOXE stampa `runtimeConfig.title_code` in `frontend/app/ui/boxe/boxe-gameplay.tsx:502`; Mines nasconde l'eyebrow nello stage in `frontend/app/ui/mines/mines.css:2175`. | Rimuovere eyebrow BOXE dal gameplay. Se serve debug title code, tenerlo fuori runtime player. |
| 5 | Tag `98% RTP` visibile solo su BOXE. | BOXE stampa `<strong>{runtimeConfig.rtp_label} RTP</strong>` in `frontend/app/ui/boxe/boxe-gameplay.tsx:505`; il test smoke lo aspetta in `tests/integration/test_boxe_smoke.py:152`. | Rimuovere tag dal gameplay e aggiornare test smoke: verificare gameplay/action/config request, non `98% RTP`. |
| 6 | Barra stato/footer BOXE aggiunge copy di stato assente in Mines. | BOXE renderizza `.boxe-round-footer`, `.boxe-round-state` e meta in `frontend/app/ui/boxe/boxe-gameplay.tsx:536`; CSS dedicato in `frontend/app/ui/boxe/boxe.css:28`. | Rimuovere la barra. Gli stati restano in action disable, board reveal, collect amount e warning/error. |
| 7 | Rows/difficulty sono rettangoli stile dashboard. | `BoxeSettingsPanel` usa `.boxe-segmented-control` in `frontend/app/ui/boxe/boxe-settings-panel.tsx:27`; CSS rettangolare in `frontend/app/ui/boxe/boxe.css:136`. | Estrarre `.game-chip` / `.game-chip-row` shared. BOXE rows/difficulty diventano pillole come quick chips, con active verde pieno. |
| 8 | Multipliers BOXE non sono pillole coerenti con Mines. | `BoxePayoutDisplay` usa `boxe-payout-step` in `frontend/app/ui/boxe/boxe-payout-display.tsx:13`; CSS outline/card in `frontend/app/ui/boxe/boxe.css:75`. Mines preview chips sono pillole in `frontend/app/ui/mines/mines-stage-header.tsx:151`. | Usare lo stesso stile `.game-chip` per multiplier ladder, con classi stato `active/reached/next` scoped al ladder. |
| 9 | Primary/secondary actions non sono allineate a Mines. | BOXE usa `GameActionButtons` ma classi locali in `frontend/app/ui/boxe/boxe-gameplay.tsx:441`; CSS action in `frontend/app/ui/boxe/boxe.css:317`. | Consolidare stile action in `game-runtime.css`: BET verde pieno quando idle; COLLECT mantiene capability `collectButtonClassName` per diventare primary durante round attivo. |
| 10 | Balance footer BOXE e' piu' maiuscolo/bordato di Mines. | Shared `GameBalanceFooter` esiste in `frontend/app/ui/game-runtime/game-balance-footer.tsx:24`, ma BOXE aggiunge `boxe-balance-footer` in `frontend/app/ui/boxe/boxe-gameplay.tsx:475` e CSS locale in `frontend/app/ui/boxe/boxe.css:305`. | Spostare stile compatto in shared; BOXE consuma senza bordo/card extra, labels coerenti con Mines. |

## 5. Granularita' Parte B

Raccomandazione: non un singolo commit gigante e non un commit per ogni selector.
Usare 4 commit atomici nel branch WP-V:

1. `feat(game-runtime): add product shell, top bar and chip primitives`
   - nuovi componenti/CSS shared;
   - nessun consume game-specific ancora.
2. `refactor(mines): consume shared visual shell without visual drift`
   - Mines mantiene alias legacy;
   - baseline Mines desktop/mobile obbligatoria prima del commit successivo.
3. `refactor(boxe): consume shared visual shell and remove extra header state`
   - BOXE consuma shell/topbar/chip/action/footer;
   - rimuove RTP, title_code eyebrow e round status bar;
   - aggiorna smoke test che oggi cerca `98% RTP`.
4. `test(visual): add side-by-side visual evidence for wave2 visual uniformity`
   - baseline/screenshot side-by-side e report differenze residue.

Motivo: separa rischio shared, compat Mines e consumo BOXE. Se il commit 2
produce diff Mines, si ferma prima di toccare BOXE.

## 6. Mines Compat Alias Plan

Obiettivo: zero diff visuale Mines.

Approccio:

- Non cancellare classi legacy nella prima iterazione.
- `productShellClassName` Mines diventa:

```tsx
"panel game-product-shell mines-product-shell mines-product-shell-clean ..."
```

- CSS shared in `game-runtime.css` definisce solo primitive prefissate:
  `.game-product-shell`, `.game-top-bar`, `.game-chip`, `.game-action-buttons`,
  `.game-balance-footer`.
- CSS Mines mantiene alias e override esistenti:
  - `.mines-product-shell` resta valido;
  - `.mines-product-shell-clean` resta valido;
  - `.mines-product-shell-mobile` e `.mines-product-shell-embedded` restano
    responsabili delle varianti mobile/embed.
- `MinesStageHeader` puo' diventare adapter sottile sopra `GameTopBar`, ma la
  prima Parte B non deve cambiare DOM piu' del necessario. Se il wrapper
  condiviso aggiunge un livello DOM che rompe selector tipo
  `.mines-grid > .stack:first-child`, STOP.
- `MinesRuntimeTools` non va spostato integralmente se il rischio baseline e'
  alto: `GameTopBar` puo' riceverlo come slot `runtimeTools`.

Regola CSS: nessun selector shared generico su `.button`, `.field`,
`.quick-chip` fuori da un prefisso `game-*`.

## 7. Capability Matrix End-To-End

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Stato | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Shared product shell | N/A | N/A | N/A | N/A | BOXE usa la shell Mines/reference senza toccare Mines | `mines-product-shell` compat + `boxe-product-shell` | Visual side-by-side pre/post | Questo doc | Completata | Postfix: shell embed/fullscreen riallineata a Mines su desktop/mobile/landscape. |
| Shared top/stage bar | N/A | N/A | N/A | N/A | BOXE usa stage header stile Mines: titolo, subtitle e payout sopra board | Classi stage Mines + override BOXE minimo | Visual side-by-side pre/post | Questo doc | Completata | Postfix: rimosso topbar full-width BOXE-only e close in embed. |
| Remove BOXE RTP tag | N/A | N/A | Runtime config resta invariato | N/A | Tag non renderizzato | Nessun CSS dedicato | Smoke aggiornato in WP-V | Questo doc | Completata | Decisione product gia' presa. |
| Remove BOXE title_code eyebrow | N/A | N/A | Runtime config resta invariato | N/A | Eyebrow non renderizzata | Rimozione selector residui | Visual side-by-side | Questo doc | Completata | Debug fuori runtime player. |
| Remove BOXE round state bar | N/A | N/A | N/A | N/A | Nessun footer status extra | Rimozione `.boxe-round-footer` | Smoke cashout su stato action/terminal | Questo doc | Completata | Non rimuove error/warning. |
| Shared chip controls | N/A | N/A | N/A | N/A | Rows/difficulty/quick chips/multipliers coerenti con Mines; contenuto game-specific | `choice-chip`, `quick-chip`, `mines-preview-chip` | Visual states idle/active/win | Questo doc | Completata | Postfix: fix compressione difficulty e chip mobile. Board geometry fuori WP-V. |
| Shared action buttons | N/A | N/A | N/A | N/A | Bet/Collect usano gerarchia e label Mines | Mines action classes | Smoke demo cashout | Questo doc | Completata | Postfix: rimosso Collect amount BOXE-only dal bottone. |
| Shared balance footer | N/A | N/A | Wallet backend invariati | N/A | Balance/win footer compatto e typography Mines | `mines-balance-footer` + override embed/mobile | Visual + existing smoke | Questo doc | Completata | Postfix: label non uppercase e demo debit ottimistico su start. |
| Desktop layout parity | N/A | N/A | N/A | N/A | Rail sinistra + stage/board destra come Mines | `mines-grid`, `stack`, `mines-stage-board` | `post_side_by_side_*desktop.png` | Questo doc | Completata | Divergenze residue solo board/payout count game-specific. |
| Mobile layout parity | N/A | N/A | N/A | N/A | Stage, board, balance, bet/actions, settings summary seguono ordine Mines | `mines-mobile-layout` + shared mobile stack/sheet | `post_side_by_side_*mobile*.png` | Questo doc | Completata | Postfix: rail mobile BOXE-only rimosso. |
| Win state parity | N/A | N/A | N/A | N/A | Nessun overlay win BOXE-only; subtitle stage come Mines | `.boxe-stage-subtitle.is-visible` | `post_side_by_side_win_desktop.png` | Questo doc | Completata | Board reveal resta game-specific. |

## 8. Stop-And-Ask Attesi

Stop obbligatorio se:

- Mines visual baseline non resta zero-diff dopo il consume shared.
- `GameTopBar` richiede spostare logica Mines di replay/rules/audio invece di
  riceverla come slot.
- BOXE ha bisogno di mantenere il round status footer per accessibilita' o test:
  in quel caso va deciso un pattern shared `GameRoundStatusBar`, ma la decisione
  product attuale dice rimuovere.
- Il test smoke BOXE fallisce solo per `98% RTP`: aggiornare il test e
  dichiarare la ragione. Se fallisce per boot/action/cashout, e' bug vero.
- WP-G modifica nello stesso momento blocchi non board in `boxe.css`.
- La rimozione del title_code eyebrow viene richiesta solo per desktop ma non
  mobile: serve una decisione unica, non due comportamenti.

## 9. Gate Parte B

Gate minimi:

- `npm run lint:i18n` e `npm run build` nel frontend del worktree WP-V.
- `python -m pytest tests/contract/test_game_runtime_frontend_boundary.py -q`.
  Se il test va in timeout per infrastruttura nota, gate sostitutivo statico:
  nessun import da `mines` o `boxe` dentro `game-runtime/`.
- BOXE smoke: almeno `tests/integration/test_boxe_smoke.py::test_boxe_demo_safe_sequence_cashout_resets_to_bet`.
- Mines visual regression: desktop + mobile ZERO diff.
- Side-by-side Mines vs BOXE in 6 stati:
  - idle desktop;
  - active desktop;
  - win desktop;
  - idle mobile portrait;
  - active mobile portrait;
  - landscape rotation.
- Tabella differenze residue: ogni differenza deve essere `game-specific`,
  `known WP-G board`, oppure fixata.
- No diff in `backend/`, migrations/schema, `frontend/app/ui/title-editor/`.

## 10. Effort Estimate

Stima Parte B: 7-10 prompt.

Breakdown:

- 1-2 prompt per shared shell/topbar/chip CSS.
- 2-3 prompt per Mines consume + baseline zero-diff.
- 2-3 prompt per BOXE consume + rimozioni + test smoke update.
- 2 prompt per screenshot side-by-side, report pixel e fix finale.

Rischio alto: Mines baseline. Se il nuovo `GameTopBar` altera DOM/CSS Mines, la
Parte B puo' crescere di 3-5 prompt.

## 11. Prompt Parte B Consigliato

```text
Esegui WP-V Visual Uniformity Parte B secondo
docs/games/boxe/VISUAL_UNIFORMITY_APPROACH_2026-05-20.md.

Branch/worktree: feature/wave2-visual-uniformity in worktree dedicato.

Ordine obbligatorio:
1. Aggiungi primitive shared product shell/topbar/chip/action/footer in
   frontend/app/ui/game-runtime/ e game-runtime.css.
2. Migra Mines con alias legacy e verifica zero diff visuale.
3. Migra BOXE, rimuovendo RTP tag, title_code eyebrow e round status footer.
4. Aggiorna i test che assertano quei testi rimossi.
5. Produci side-by-side Mines vs BOXE nei 6 stati richiesti.

STOP se Mines non resta zero-diff o se WP-G sta modificando gli stessi blocchi
CSS non board.
```
