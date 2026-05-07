# CasinoKing - Next UX Slices CTO Review Plan

## Stato

Documento operativo da usare per validare con CTO la prossima slice di lavoro.

Non autorizza implementazioni automatiche: registra contesto, opzioni, aree
toccate e decisioni richieste.

Aggiornamento 2026-05-07:

- Site backoffice compatto completato e verificato.
- Player lobby visual QA completata in prima chiusura, con cleanup varianti test
  pubblicate e verifica responsive 375px su lobby/Mines demo.
- Resta come prossima slice tecnica F7-C con route dedicate.

## Contesto

Dopo Games overview, Site/Lobby Publishing, LOG operativo e Player Lobby Slice
1, restano tre possibili direzioni operative:

1. Site backoffice compatto.
2. Player lobby visual QA.
3. Games detail / F7-C monolite.

Queste direzioni toccano layer diversi e non devono essere fuse in un singolo
intervento:

```text
Games
  crea e configura varianti

Site/Lobby
  decide cosa appare sul sito

Player lobby
  consuma GET /api/v1/games/library

Games detail / F7-C
  riduce debito tecnico del detail Mines
```

## Perche' Serve Scegliere Una Slice

La scelta della prossima slice serve a evitare di mischiare:

- layout;
- comportamento;
- publishing;
- runtime;
- refactor tecnico.

Il rischio principale e' trasformare un polish UI in un cambio architetturale
implicito, oppure compensare dati Site/Lobby non ancora stabili con hardcoding
nel frontend player.

## Sequenza Consigliata

La sequenza consigliata dentro questo documento era:

1. Site backoffice compatto. Completato.
2. Player lobby visual QA. Completato.
3. Games detail / F7-C monolite, come slice tecnica dedicata. Prossimo.

Motivo:

- Site/Lobby e' la fonte editoriale della lobby player;
- stabilizzare Site/Lobby rende il QA player piu' affidabile;
- F7-C resta importante, ma va trattato come refactor funzionale isolato e non
  come polish visuale.

Sequenza operativa complessiva raccomandata:

1. Smoke E2E manuale, secondo `docs/E2E_MANUAL_SMOKE_PLAN.md`. Completato.
2. Rimozione eccezione legacy master launch, secondo
   `docs/MASTER_LAUNCH_LEGACY_REMOVAL_PLAN.md`. Completato.
3. Site backoffice compatto. Completato.
4. Player lobby visual QA. Completato.
5. F7-C deep refactor con route dedicate. Prossimo.

Senza lo step 2, Site backoffice compatto e Player lobby visual QA lavorano su
un layer launch ancora instabile. Lo step 5 puo' essere posticipato se non si
prevede di estendere Games overview oltre Slice 2A a breve.

## Aree Toccate E Perche'

### Site Backoffice Compatto

Codice atlas:

- `PLATFORM_BACKOFFICE_00297`

File principali:

- `frontend/app/ui/site/site-lobby-publication-panel.tsx`
- `frontend/app/ui/admin-shell-panel.tsx`
- `backend/app/modules/platform/catalog/admin_title_service.py`
- `backend/app/modules/platform/catalog/library_service.py`

Perche':

- governa visibilita', demo/real, ordine, featured e metadata lobby;
- deve restare separato dalla configurazione gioco;
- la preview deve restare allineata a `GET /api/v1/games/library`.

### Player Lobby Visual QA

Codice atlas:

- `PLATFORM_FRONTEND_00110`

File principali:

- `frontend/app/(player)/page.tsx`
- `frontend/app/ui/player-lobby-page.tsx`
- `backend/app/api/routes/games_library.py`

Perche':

- e' la vista pubblica percepita dal player;
- deve consumare la library, non decidere regole editoriali;
- deve mostrare varianti come prodotti, non record tecnici.

### Games Detail / F7-C Monolite

Codici atlas:

- `PLATFORM_BACKOFFICE_00295`
- `PLATFORM_BACKOFFICE_00290`
- `MINES_BACKOFFICE_00600`
- `MINES_BACKOFFICE_00610`
- `MINES_SKIN_01000`

File principali:

- `frontend/app/ui/mines/mines-backoffice-editor.tsx`
- `frontend/app/ui/mines/mines-engine-editor.tsx`
- `frontend/app/ui/mines/mines-grid-config-editor.tsx`
- `frontend/app/ui/mines/mines-theme-editor.tsx`
- `frontend/app/ui/title-editor/title-editor-shell.tsx`
- `frontend/app/ui/title-editor/engine-editor-registry.ts`

Perche':

- il detail Mines resta un monolite grande;
- le evoluzioni successive del detail richiedono separazione piu' netta;
- config, theme, assets, rules e labels devono restare nel detail variante, non
  contaminare overview/category.

## Obiettivi

- Rendere Site/Lobby piu' compatto, leggibile e operativo.
- Verificare che la player lobby rappresenti fedelmente i dati pubblicati.
- Separare il debito tecnico del detail Games/F7-C da polish e QA.
- Non introdurre CMS completo.
- Non introdurre nuovi engine.
- Non introdurre regole editoriali frontend parallele.
- Non modificare runtime Mines, payout, RTP, RNG o fairness.

## Slice 1 - Site Backoffice Compatto

Stato: completata in prima chiusura il 2026-05-07.

### Scope

- Completare polish e smoke visuale della vista Site/Lobby gia' implementata in
  prima versione.
- Migliorare leggibilita' di stati, controlli e preview.
- Mantenere `GET /api/v1/games/library` come fonte della preview player.
- Se Slice 1 e Slice 2 risultano entrambe inferiori a una giornata di lavoro,
  possono essere eseguite nello stesso cantiere, mantenendo verifiche e
  accettazione separate.

### Accettazione

- Site/Lobby non crea varianti.
- Site/Lobby non modifica config Mines.
- Salvataggi persistono.
- Preview usa `GET /api/v1/games/library`.
- Layout desktop/tablet/mobile senza overlap.
- Stati loading/error/empty leggibili.
- Nessun endpoint nuovo salvo blocco pratico confermato.

## Slice 2 - Player Lobby Visual QA

Stato: completata in prima chiusura il 2026-05-07.

### Scope

- Validare la lobby player con dati reali dopo Site/Lobby.
- Verificare card, copy, CTA e responsive.
- Correggere solo problemi visuali o di stato emersi dal QA.
- Se Slice 1 e Slice 2 risultano entrambe inferiori a una giornata di lavoro,
  possono essere eseguite nello stesso cantiere, mantenendo verifiche e
  accettazione separate.

### Accettazione

- La lobby legge solo `GET /api/v1/games/library`.
- Master non renderizzati come item ordinari.
- CTA demo/real lanciano il `title_code` corretto.
- Player anonimo con real disponibile va a login.
- Nomi e descrizioni lunghi non rompono le card.
- Nessun hardcoding di pubblicazione nel frontend.

## Slice 3 - Games Detail / F7-C Monolite

### Scope

- Aprire una slice tecnica dedicata per decomporre il monolite del detail Mines.
- Mantenere separati overview, category view e variant detail.
- Spostare complessita' solo quando riduce responsabilita' reali del componente.
- Introdurre route dedicate per il detail, con pattern target:
  `/admin/games/[engine]/titles/[title_code]`.
- Evitare nuovo stato condiviso fragile dentro la shell admin quando il detail
  viene spezzato.
- Dichiarare F7-C come gating per Games overview Slice 3+.

Fino alla chiusura di F7-C, Games overview non deve essere estesa oltre Slice
2A.

### Accettazione

- Config, theme, assets, rules e labels restano nel detail variante.
- Overview/category non montano editor engine-specific lunghi.
- Master resta read-only.
- Nessun cambio a payout, RTP, RNG, fairness.
- Nessun cambio backend non pianificato.
- `tsc --noEmit` e build frontend verdi.

## Dipendenze

- Site/Lobby prima di Player lobby QA.
- F7-C prima di ulteriori evoluzioni profonde del detail Games.
- F7-C e' gating per Games overview Slice 3+.
- Preview player e lobby devono restare allineate a `GET /api/v1/games/library`.
- Preview backoffice resta tramite token admin dedicato.
- Production readiness e security review restano gating per go-live, non
  bloccanti per queste slice UX.

## Fuori Scope

- CMS completo.
- Homepage e pagine statiche.
- Scheduling editoriale.
- Creazione engine non-Mines.
- Payout, RTP, RNG e fairness.
- Wallet, ledger e accounting.
- i18n foundation.
- Rimozione dell'eccezione legacy master launch, coperta da
  `docs/MASTER_LAUNCH_LEGACY_REMOVAL_PLAN.md` e raccomandata dopo lo smoke E2E
  e prima di queste slice UX.
- Produzione o external adapter.

## Rischi

- Mischiare publishing sito e configurazione gioco.
- Fare QA player su dati non realistici.
- Trasformare F7-C in refactor estetico troppo ampio.
- Introdurre hardcoding frontend per compensare dati Site/Lobby.
- Toccare launch/runtime Mines senza decisione esplicita.
- Aggiungere stati editoriali non previsti, come draft o scheduled.

## Decisioni CTO Recepite

- Sequenza: Site compatto -> Player visual QA -> F7-C dedicato, dentro il
  percorso UX; nella sequenza operativa complessiva precedono smoke E2E e master
  launch removal.
- F7-C e' gating per Games overview Slice 3+.
- Site selector fuori scope finche' esiste solo `casinoking`; diventa in-scope
  quando viene aggiunto un secondo Site al catalogo.
- `featured` resta multi-item; nessun vincolo "un solo featured" finche' non
  diventa requisito di prodotto.
- L'eccezione legacy master launch non viene toccata in queste slice UX ed e'
  coperta da `docs/MASTER_LAUNCH_LEGACY_REMOVAL_PLAN.md`.
- F7-C deve introdurre route dedicate
  `/admin/games/[engine]/titles/[title_code]`.
- Nessun endpoint nuovo salvo blocco pratico del frontend confermato.
