# CasinoKing - F7-C Games Detail Route Refactor Plan

## Stato

Piano tecnico route/detail stabilizzato, con decomposizione residua tracciata.

Aggiornamento implementativo 2026-05-07:

- F7-C.1 route foundation implementata;
- F7-C.2 overview/category route implementata per il perimetro Mines;
- F7-C.3 direct detail route implementata con fetch da
  `GET /catalog/titles/{title_code}` e validazione engine;
- F7-C.4 avviata con estrazione `MinesConfigOverview` e
  `TitleEditorCommandBar`;
- nessun backend endpoint, payload, schema, payout, wallet o ledger e' stato
  modificato;
- I18N-1 resta bloccato finche' F7-C route/detail non viene stabilizzato con
  smoke locale sufficiente.

Aggiornamento implementativo 2026-05-08:

- route/detail F7-C stabilizzati per procedere con Mines i18n;
- `npm run lint:i18n`, `npx tsc --noEmit` e `npm run build` verdi;
- rebuild Docker backend/frontend eseguito;
- HTTP smoke locale verde su:
  - `/admin/games`;
  - `/admin/games/mines`;
  - `/admin/games/mines/titles/mines_classic`;
  - route negative client-side `/admin/games/slots/titles/mines_classic` e
    `/admin/games/typo`;
- `MinesBackofficeEditor` resta parzialmente monolitico: `MinesConfigOverview`
  e `TitleEditorCommandBar` sono estratti;
- aggiornamento successivo 2026-05-08: copy/rules i18n, labels legacy e board
  assets sono stati estratti in componenti dedicati senza cambiare API,
  payload o publish flow;
- restano nel file principale orchestration, API actions, draft state, theme
  state e updaters principali;
- questa decomposizione residua non blocca I18N-1/I18N-7, ma resta debito
  tecnico da ridurre prima di ulteriori espansioni backoffice.

Questo documento dettaglia il prossimo step F7-C indicato in:

- `docs/NEXT_UX_SLICES_CTO_REVIEW_PLAN.md`
- `docs/PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md`
- `docs/BACKOFFICE_GAMES_UX_REORGANIZATION_PLAN.md`
- `docs/TITLE_EDITOR_SHELL_PLAN.md`

F7-C e' gating per Games overview Slice 3+.

Aggiornamento CTO 2026-05-07:

- F7-C e' anche prerequisito obbligatorio per I18N-1;
- il cantiere F7-C va completato una volta sola;
- lo stesso output di F7-C serve sia Games overview Slice 3+ sia Mines i18n
  foundation;
- il tab `Translations` puo' essere predisposto, ma l'implementazione i18n
  completa resta nel cantiere I18N-* successivo.

Aggiornamento 2026-05-07:

- F7-C deve lasciare spazio al nuovo cantiere Mines i18n;
- il detail variante dovra' ospitare una tab `Translations` o `Content`;
- la i18n foundation Mines e' documentata in
  `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`;
- F7-C non deve implementare tutta la i18n da solo, ma non deve creare una
  struttura che la renda difficile.
- I18N-1 non parte prima della chiusura F7-C.

## Obiettivo

Ridurre il debito del detail Games/Mines introducendo route dedicate e
decomponendo il detail Mines senza cambiare runtime o contratti backend.

Obiettivo pratico:

```text
Backoffice
  -> Games overview
  -> Game category
  -> Variant detail route
```

Target route:

```text
/admin/games
/admin/games/[engine]
/admin/games/[engine]/titles/[title_code]
```

## Stato attuale

Oggi la route admin reale e':

```text
frontend/app/admin/page.tsx
```

Questa monta `CasinoKingConsole`.

La navigazione Games vive ancora come stato React interno:

- `adminSection`;
- `adminGamesView`;
- `selectedAdminTitle`;
- `catalogRefreshKey`.

Overview e category sono gia' parzialmente separate:

- `frontend/app/ui/platform-catalog-panel.tsx`;
- `frontend/app/ui/games/games-overview.tsx`;
- `frontend/app/ui/games/game-category-view.tsx`;
- `frontend/app/ui/games/game-master-card.tsx`;
- `frontend/app/ui/games/game-variant-list.tsx`;
- `frontend/app/ui/games/game-status-badges.tsx`.

Il detail monta:

- `frontend/app/ui/title-editor/title-editor-shell.tsx`;
- `frontend/app/ui/title-editor/engine-editor-registry.ts`;
- `frontend/app/ui/mines/mines-engine-editor.tsx`;
- `frontend/app/ui/mines/mines-backoffice-editor.tsx`.

Il monolite residuo principale e' `mines-backoffice-editor.tsx`, che oggi
contiene ancora:

- load config;
- save draft;
- publish config;
- load/save/publish theme;
- upload/delete assets;
- overview;
- rules;
- labels;
- grid config;
- tab theme;
- futuro tab translations/content;
- stato locale e command bar.

## Principi

- Non cambiare payout, RTP, RNG, fairness, wallet o ledger.
- Non spostare config/theme/assets/rules/labels in overview/category.
- Non introdurre nuovi endpoint backend salvo blocco pratico confermato.
- Non creare supporto finto per engine non-Mines.
- Non fare redesign estetico generale.
- Route dedicate servono a ridurre stato fragile, non a cambiare dominio.
- Non infilare il futuro editor traduzioni dentro overview/category.

## Slice F7-C.0 - Baseline e audit pre-refactor

Scopo:

- confermare quali file e responsabilita' sono attualmente coinvolti;
- evitare di spostare logica al buio.

Azioni:

1. Eseguire `rg` su `adminGamesView`, `selectedAdminTitle`,
   `MinesBackofficeEditor`, `TitleEditorShell`.
2. Mappare handler correnti:
   - duplicate title;
   - update title profile;
   - preview launch;
   - update publication;
   - config save/publish;
   - theme save/publish;
   - asset upload/delete.
3. Segnare i confini fra:
   - admin shell;
   - Games overview;
   - category;
   - variant detail;
   - Mines engine editor.

Output:

- nessun codice obbligatorio;
- issue notes o commento nel task;
- conferma write set prima di parallelizzare.

Accettazione:

- si conosce dove vive ogni handler;
- non ci sono modifiche runtime;
- typecheck baseline disponibile se necessario.

## Slice F7-C.1 - Route foundation

Stato: implementata.

Scopo:

- introdurre route dedicate senza cambiare comportamento osservabile.

Route:

```text
frontend/app/admin/games/page.tsx
frontend/app/admin/games/[engine]/page.tsx
frontend/app/admin/games/[engine]/titles/[title_code]/page.tsx
```

Implementazione:

- le route montano `CasinoKingConsole` con `adminGamesRoute`;
- la sessione admin resta gestita dalla shell esistente;
- dopo login diretto su una route Games, l'intent route viene ripristinato;
- non sono stati aggiunti endpoint backend.

Azioni:

1. Estrarre o creare un wrapper admin route che sappia leggere sessione admin.
2. Riutilizzare i componenti esistenti invece di duplicare UI.
3. Mantenere `/admin` compatibile come menu generale.
4. Collegare overview -> category -> detail tramite link/route.
5. Evitare route protette solo lato UI: le API restano protette dal backend.

Accettazione:

- `/admin/games` carica overview;
- `/admin/games/mines` carica category Mines;
- detail route e' raggiungibile direttamente;
- se sessione admin assente, UX porta a login/admin shell coerente;
- nessun endpoint backend nuovo.

## Slice F7-C.2 - Games overview/category route

Stato: implementata per Mines.

Scopo:

- spostare la navigazione overview/category fuori dallo stato `adminGamesView`.

Componenti da riusare:

- `PlatformCatalogPanel`;
- `GamesOverview`;
- `GameCategoryView`;
- `GameMasterCard`;
- `GameVariantList`;
- `GameStatusBadges`.

Implementazione:

- `/admin/games` carica il catalogo Games;
- `/admin/games/mines` filtra la category Mines;
- route engine sconosciute mostrano stato vuoto esplicito;
- overview/category non montano `MinesBackofficeEditor`.

Azioni:

1. `GamesOverview` deve linkare la categoria Mines.
2. `GameCategoryView` deve linkare il detail variante.
3. La creazione variante resta nella category.
4. La rinomina variante resta in lista/category.
5. Preview admin resta disponibile per master e varianti.

Accettazione:

- master Mines distinto, read-only e previewable;
- varianti in lista compatta;
- create variant funziona;
- rename variant funziona;
- open detail usa route dedicata;
- overview/category non montano `MinesBackofficeEditor`.

## Slice F7-C.3 - Variant detail route

Stato: implementata.

Scopo:

- rendere il detail variante un deep link stabile.

Route target:

```text
/admin/games/[engine]/titles/[title_code]
```

Azioni:

1. Caricare il Title da `GET /catalog/titles/{title_code}` o da catalogo.
2. Validare `engine` della route contro `engine_code` del Title.
3. Mostrare header detail con:
   - display name admin;
   - title code;
   - engine;
   - master/variant state;
   - preview;
   - back to category.
4. Montare `TitleEditorShell`.
5. Per master, mostrare stato read-only senza editor mutabile.

Implementazione:

- `/admin/games/[engine]/titles/[title_code]` carica il Title da catalogo;
- engine route e `title.engine_code` vengono confrontati;
- loading/error non mostrano header o preview stale da `mines_classic`;
- master resta read-only tramite `TitleEditorShell`;
- il back to category usa `/admin/games/[engine]`.

Accettazione:

- refresh diretto della route funziona;
- route con engine mismatch non salva dati errati;
- master resta read-only;
- preview usa `POST /admin/games/titles/{title_code}/preview-launch`;
- ritorno alla category non dipende da stato precedente in memoria.

## Slice F7-C.4 - Decomposizione detail Mines

Stato: avviata, non chiusa.

Scopo:

- ridurre `mines-backoffice-editor.tsx` separando stato/action ownership da UI.

Componenti/hook candidati:

```text
frontend/app/ui/title-editor/
  title-editor-command-bar.tsx
  use-title-config.ts
  use-title-theme.ts
  use-title-assets.ts

frontend/app/ui/mines/
  mines-config-overview.tsx
  mines-rules-editor.tsx
  mines-labels-editor.tsx
  mines-board-assets-editor.tsx
  mines-i18n-editor.tsx
  mines-copy-coverage-panel.tsx
```

Implementazione parziale:

- `frontend/app/ui/mines/mines-config-overview.tsx` estrae la UI overview;
- `frontend/app/ui/title-editor/title-editor-command-bar.tsx` estrae la command
  bar save/load/publish;
- `frontend/app/ui/mines/mines-i18n-admin-editor.tsx` estrae lingua pubblicata,
  titolo in-game, copy player e rules HTML;
- `frontend/app/ui/mines/mines-legacy-labels-editor.tsx` estrae le label
  demo/real legacy;
- `frontend/app/ui/mines/mines-board-assets-editor.tsx` estrae la UI degli
  asset board;
- API ownership e stato draft/publish restano in `MinesBackofficeEditor`;
- non sono stati cambiati contratti o payload.

Resta:

- valutare hook `use-title-config`, `use-title-theme`, `use-title-assets`.
- valutare una futura estrazione degli handler API solo se il file resta troppo
  pesante dopo altri cantiere; evitare micro-hook prematuri.

Regola:

- `TitleEditorShell` coordina title-level;
- `MinesEngineEditor` contiene solo responsabilita' Mines-specific e compone i
  blocchi detail;
- theme e assets restano platform-owned ma montati nel detail variante.

Azioni:

1. Estrarre command bar save/publish/load.
2. Estrarre overview snapshot.
3. Estrarre rules editor.
4. Estrarre labels editor.
5. Estrarre assets editor.
6. Tenere `MinesGridConfigEditor` come engine-specific.
7. Tenere `MinesThemeEditor` come theme UI, ma con data flow piu' chiaro.
8. Lasciare un punto di estensione pulito per `Translations`/i18n editor.

Accettazione:

- endpoint e payload invariati;
- draft/publish config invariati;
- theme draft/publish invariati;
- asset upload/delete invariati;
- nessun salvataggio possibile su master;
- il detail puo' montare in seguito il coverage i18n senza riaprire overview;
- typecheck e build verdi.

## Slice F7-C.5 - Hardening e smoke

Stato: verifiche automatiche eseguite, smoke browser manuale ancora da fare.

Verifiche frontend:

```powershell
cd frontend
npx tsc --noEmit
npm run build
```

Smoke admin:

1. Login admin.
2. Apri `/admin/games`.
3. Apri `/admin/games/mines`.
4. Crea variante da master.
5. Apri detail route della variante.
6. Modifica un campo innocuo in draft.
7. Salva draft.
8. Pubblica live.
9. Preview demo.
10. Torna a category.
11. Ricarica route detail direttamente.

Verifiche gia' eseguite:

- `cd frontend; npx tsc --noEmit`;
- `cd frontend; npm run build`;
- rebuild container frontend;
- `docker compose ... ps` con frontend/backend/Postgres/Redis healthy;
- HTTP 200 su `/admin/games`;
- HTTP 200 su `/admin/games/mines`;
- HTTP 200 su `/admin/games/mines/titles/mines_classic`;
- HTTP 200 su route negative gestite lato client:
  `/admin/games/slots/titles/mines_classic`,
  `/admin/games/mines/titles/does_not_exist`,
  `/admin/games/typo`.

Backend tests:

- non obbligatori se non si tocca backend;
- se backend/API/payload vengono toccati, eseguire:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:56543/casinoking'
python -m pytest tests/integration/test_title_configs_split.py tests/integration/test_mines_backoffice_config.py
python -m pytest tests/integration/test_game_library_publication.py
```

## API esistenti da usare

```text
GET  /api/v1/catalog/sites/casinoking/titles
GET  /api/v1/catalog/titles/{title_code}
POST /api/v1/admin/games/titles/{source_title_code}/duplicate
PUT  /api/v1/admin/games/titles/{title_code}/profile
POST /api/v1/admin/games/titles/{title_code}/preview-launch
GET  /api/v1/admin/games/titles/{title_code}/config
PUT  /api/v1/admin/games/titles/{title_code}/config
POST /api/v1/admin/games/titles/{title_code}/config/publish
GET  /api/v1/games/mines/config?title_code={title_code}
GET  /api/v1/admin/titles/{title_code}/theme
PUT  /api/v1/admin/titles/{title_code}/theme
POST /api/v1/admin/titles/{title_code}/theme/publish
GET  /api/v1/admin/titles/{title_code}/assets
POST /api/v1/admin/titles/{title_code}/assets
DELETE /api/v1/admin/titles/{title_code}/assets/{asset_kind}
```

Possibile endpoint futuro solo se confermato:

```text
GET /api/v1/admin/games/catalog
```

Da non introdurre in F7-C senza blocco reale.

## Parallelizzazione consigliata

### Worker 1 - Route/admin shell

Write set:

- `frontend/app/admin/games/**`;
- wrapper admin route nuovi;
- link/navigation nei componenti overview/category.

### Worker 2 - Mines detail decomposition

Write set:

- `frontend/app/ui/mines/**`;
- `frontend/app/ui/title-editor/**`.

Nota:

- se il cantiere i18n parte in parallelo, Worker 2 non deve modificare gli
  stessi file del resolver player senza coordinamento.

### Worker 3 - Smoke/test/documentazione

Write set:

- test/smoke eventuali;
- docs e checklist finali.

### Worker 4 - Mines i18n editor integration

Write set:

- `frontend/app/ui/mines/i18n-editor/**`;
- `frontend/app/ui/mines/mines-i18n-editor.tsx`;
- `frontend/app/ui/mines/mines-copy-coverage-panel.tsx`;
- types frontend collegati al payload `locale_map`.

Parte solo dopo che il payload API e' validato o con mock type concordati.

Regola:

- Worker 1 e 2 non devono modificare lo stesso blocco di
  `casinoking-console.tsx` in parallelo senza coordinamento.

## Rischi

- Duplicare auth/session admin in route nuove.
- Lasciare `/admin` e `/admin/games` con due comportamenti divergenti.
- Trasformare F7-C in polish visuale.
- Spostare config/theme/assets fuori dal detail variante.
- Introdurre fallback implicito a `mines_classic`.
- Rompere preview admin token.

## Fuori scope

- Site/Lobby publishing.
- Player lobby.
- Error pattern globale.
- i18n foundation completa dentro F7-C: e' cantiere dedicato.
- In-game title separato come colonna: con i18n usare `game.title`.
- Reporting/spin id.
- Produzione.
- External adapter.
- Payout, RTP, RNG, fairness, wallet, ledger.

## Decisioni CTO

- Route dinamiche e non Mines-only: da confermare nel piano F7-C specifico se
  non gia' chiuse in review.
- Confermare che i tab interni del detail restano stato locale nella prima
  slice, non route annidate.
- Confermare che F7-C precede Games overview Slice 3+.
- Confermato da review i18n: F7-C precede I18N-1.
- Confermare nessun endpoint backend nuovo salvo blocco pratico.
- Confermare se il tab `Translations` viene solo predisposto in F7-C o anche
  implementato nella prima tranche i18n.
