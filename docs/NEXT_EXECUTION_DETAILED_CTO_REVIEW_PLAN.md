# CasinoKing - Next Execution Detailed CTO Review Plan

## Stato

Documento operativo aggiornato dopo validazione CTO.

Non autorizza implementazioni automatiche. Serve a trasformare i prossimi macro
step in un piano leggibile, sequenziato e parallelizzabile.

Aggiornamento: 2026-05-07.

Decisione utente recepita:

- produzione non e' un obiettivo immediato;
- external adapter / Fase 9b-c resta rinviato;
- il lavoro continua ancora in locale per un periodo esteso;
- Mines deve introdurre una i18n foundation runtime fatta bene;
- le label player-facing Mines non devono restare hardcoded;
- il piano single-language precedente e' superato per Mines;
- il prossimo blocco deve restare documentato e validabile dal CTO prima del
  codice.

Aggiornamento post review CTO:

- epic Mines i18n foundation approvato;
- nessun caveat CTO viene rifiutato;
- F7-C deve essere chiuso prima di I18N-1;
- lingua pubblicata Mines iniziale raccomandata: `it`;
- una sola lingua pubblicata per gioco/config Mines;
- allowlist editoriale Mines: `it`, `en`, `de`, `es`;
- nessun selector lingua nel gioco;
- nessun `ck_player_locale`;
- nessun parametro `locale` player-side;
- i18n globale platform e produzione restano rinviate.

## Contesto consolidato

Sono gia' chiusi o in prima chiusura:

- smoke E2E manuale;
- rimozione legacy master launch;
- Site backoffice compatto;
- Player lobby visual QA;
- preview admin con token dedicato;
- launch pubblico title-aware per varianti non-master;
- LOG operativo backoffice;
- primo pattern popup errori Mines;
- copy English nelle aree Games/Lobby/Mines gia' toccate.

Il prossimo step consigliato nei piani attivi e':

```text
F7-C deep refactor con route dedicate,
gating per Games overview Slice 3+.
```

La review CTO ha approvato l'epic i18n con caveat tecnici, integrati nei
documenti collegati.

Sequenza CTO integrata:

1. Smoke E2E.
2. Master launch legacy removal.
3. Site compact + Player lobby QA, mergeable se piccoli.
4. F7-C deep refactor + route dedicate.
5. Mines i18n foundation epic, I18N-1 ... I18N-8.

Nota:

- F7-C e' un cantiere unico, completato una volta sola;
- F7-C funge da prerequisito sia per Games overview Slice 3+ sia per i18n;
- i18n non sale di priorita' sopra smoke/master/site/player.

## Analisi multi-agentica usata

Questa pianificazione integra tre analisi parallele:

1. F7-C / route dedicate / detail Games-Mines.
2. Copy, label, messaggi in-game e i18n foundation Mines.
3. Titolo Mines visibile in-game e distinzione dai nomi esistenti.

Output chiave dei brief:

- F7-C e' un refactor funzionale, non estetico.
- Oggi non esiste ancora una struttura i18n/multilingua completa.
- Esiste pero' una presentation config per Title:
  `title_configs.rules_sections_json` e `title_configs.ui_labels_json`.
- La direzione aggiornata e' una locale map versionata Title-level per Mines.
- Il titolo in-game e' hardcoded nel frontend come `MINES`.
- Con i18n Mines, il titolo in-game deve diventare la key localizzata
  `game.title`.

## Documenti figli

Questo master plan si appoggia a tre piani specifici:

- `docs/F7_C_GAMES_DETAIL_ROUTE_REFACTOR_PLAN.md`
- `docs/MINES_COPY_LABELS_AND_I18N_READINESS_PLAN.md`
- `docs/MINES_I18N_CTO_REVIEW_BRIEF.md`
- `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`
- `docs/MINES_I18N_STRING_INVENTORY.md`
- `docs/MINES_IN_GAME_TITLE_PLAN.md`

Questi documenti vanno letti insieme ai piani gia' attivi:

- `docs/NEXT_UX_SLICES_CTO_REVIEW_PLAN.md`
- `docs/PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md`
- `docs/BACKOFFICE_GAMES_UX_REORGANIZATION_PLAN.md`
- `docs/TITLE_EDITOR_SHELL_PLAN.md`
- `docs/PRODUCT_COPY_ENGLISH_CLEANUP_PLAN.md`
- `docs/I18N_FOUNDATION_DEFERRED_DECISION.md`
- `docs/PLAYER_LOBBY_UX_PLAN.md`
- `docs/SITE_LOBBY_PUBLICATION_PLAN.md`
- `docs/PRODUCT_CLOSURE_BACKLOG.md`

## Sequenza raccomandata

### Step 0 - Baseline e re-smoke leggero

Scopo:

- partire da stack locale healthy;
- confermare che il flusso admin -> Site/Lobby -> player lobby -> Mines sia
  ancora verde;
- non aprire F7-C sopra uno stato ambiguo.

Verifiche:

- `docker compose ... ps`;
- frontend `200`;
- backend health `200`;
- query Postgres;
- almeno un smoke manuale rapido su Games detail, preview, lobby demo.

Output:

- nessun codice;
- nota di esito nel task corrente o nel documento di smoke se si raccolgono
  nuove evidenze strutturate.

### Step 1 - F7-C route e detail refactor

Documento guida:

- `docs/F7_C_GAMES_DETAIL_ROUTE_REFACTOR_PLAN.md`

Stato implementativo aggiornato 2026-05-08:

- route foundation implementata;
- overview/category route implementata per Mines;
- direct detail route implementata;
- prime estrazioni UI applicate su overview e command bar;
- smoke automatico frontend verde;
- rebuild Docker backend/frontend eseguito;
- HTTP smoke locale verde su `/admin/games`, `/admin/games/mines`,
  `/admin/games/mines/titles/mines_classic` e route negative client-side;
- F7-C route/detail e' stabilizzato abbastanza per procedere con Mines i18n;
- la decomposizione completa di `MinesBackofficeEditor` resta debito tecnico,
  non gating per I18N-1/I18N-7.

Scopo:

- introdurre route dedicate:

```text
/admin/games
/admin/games/[engine]
/admin/games/[engine]/titles/[title_code]
```

- ridurre stato fragile dentro `CasinoKingConsole`;
- separare overview, category e variant detail;
- decomporre gradualmente `mines-backoffice-editor.tsx`;
- non cambiare backend salvo blocco pratico confermato.

Dipendenze:

- Site/Lobby e Player lobby gia' chiusi;
- master launch hardening gia' chiuso;
- token preview admin gia' attivo.

Accettazione:

- deep link detail caricabile;
- master read-only;
- varianti modificabili;
- config/theme/assets/rules/labels restano nel detail variante;
- overview/category non montano editor engine-specific lunghi;
- `npx tsc --noEmit` e build frontend verdi;
- smoke admin su create/open/preview/back.

### Step 2 - Mines i18n foundation epic

Documento guida:

- `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`
- `docs/MINES_I18N_STRING_INVENTORY.md`

Scopo:

- introdurre una foundation multilingua reale per il runtime Mines;
- eliminare label player-facing hardcoded;
- creare manifest chiavi, resolver frontend e locale map versionata;
- definire publish gating su copertura completa;
- non toccare payout, RTP, RNG, wallet o ledger.

Decisione CTO recepita:

```text
title_locale_maps
presentation_config.i18n
frontend/app/ui/mines/i18n/**
```

Vincoli:

- lingua pubblicata iniziale raccomandata `it`;
- una sola lingua pubblicata per config;
- allowlist editoriale `it`, `en`, `de`, `es`;
- nessun selector lingua nel gioco;
- nessun `ck_player_locale`;
- nessun parametro `locale` player-side;
- key extra fuori manifest bloccanti al publish;
- `ui_labels_json` resta projection legacy, non source of truth frontend dopo
  i18n.

Regole:

- HTML ammesso solo nei body rules;
- placeholder validati dal backend;
- fallback non deve mascherare locale incomplete;
- public runtime vede solo published locale map;
- master ancora read-only;
- `game.title` sostituisce il titolo hardcoded.

Collocazione consigliata:

- dentro il detail variante F7-C, tab `Translations` o `Content`;
- non dentro Site/Lobby;
- non dentro Theme.

Prerequisito:

- F7-C chiuso prima di I18N-1.

### Step 3 - Inventario stringhe, resolver e coverage Mines

Documento guida:

- `docs/MINES_I18N_STRING_INVENTORY.md`
- `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`

Scopo:

- chiarire cosa e' oggi configurabile per Title;
- mappare label e messaggi in-game;
- evitare un finto sistema multilingua incompleto;
- portare fuori tutte le label player-facing;
- garantire coverage prima del publish.

Decisione corrente:

- backoffice UI resta IT-only in questo epic;
- Mines runtime i18n attiva;
- locale map versionata per Title;
- lingua pubblicata iniziale raccomandata `it`;
- allowlist editoriale iniziale `it`, `en`, `de`, `es`;
- una sola lingua pubblicata per config;
- nessun language selector Mines nel player;
- niente i18n globale platform in questa fase.

Output previsto:

- inventario stringhe Mines player;
- manifest chiavi;
- `title_locale_maps`;
- resolver frontend;
- backoffice translations editor;
- publish gating per locale incomplete;
- content production plan: EN AI + review utente, IT scritta nativamente,
  human read-through;
- static scan bloccante, preferibilmente ESLint custom rule;
- backward compat `ui_labels_json` come projection legacy;
- messaggi player-friendly per error code/context;
- test/smoke sulla lingua pubblicata con mobile 375px; cross-language solo via
  publish di config test con lingua diversa.

### Step 4 - Games overview Slice 3+

Prerequisito:

- F7-C chiuso o almeno route/detail stabilizzati.

Scopo:

- evolvere Games overview senza riportare editor complessi in overview;
- migliorare operator flow solo dopo che detail e category hanno confini chiari.

Possibili contenuti futuri:

- variant detail piu' pulito;
- separazione ulteriore dei tab detail;
- diagnostica subordinata;
- stato config/live/draft piu' leggibile.

Fuori scope:

- Site/Lobby publishing inline;
- config Mines in overview;
- nuovi engine.

### Step 5 - Error and notification pattern progressivo

Documento di contesto:

- `docs/PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md`
- eventuale futuro `docs/ERROR_NOTIFICATION_PATTERN.md`

Scopo:

- definire pattern per toast/banner/dialog/inline;
- applicarlo solo dove si tocca codice;
- non fare refactor globale.

Ordine consigliato:

1. Mines player error mapping gia' iniziato.
2. F7-C admin detail: stati save/publish/load.
3. Site/Lobby e LOG solo quando vengono riaperti.
4. Player auth/launch intent in una slice separata.

Accettazione:

- nuovi errori non espongono messaggi tecnici grezzi;
- backend error code usati quando disponibili;
- nessun cambio payload backend senza piano.

### Step 6 - Reporting e identificativo round/spin visibile

Documenti di contesto:

- `docs/PRODUCT_CLOSURE_BACKLOG.md`
- `docs/FINANCIAL_AREA_EXECUTION_PLAN.md`
- `docs/FINANCIAL_UI_REFACTOR_PLAN.md`

Stato:

- pianificato;
- non va implementato dentro F7-C;
- richiede design dedicato prima del codice.

Problema da risolvere:

- rendere visibile un identificativo round/spin nei report senza inventare una
  nuova identita' scollegata dal modello contabile e Mines.

Analisi obbligatoria prima del codice:

- mapping tra `platform_rounds.id`;
- round Mines / `mines_game_rounds`;
- access session;
- table session;
- ledger transaction reference;
- eventuale display id leggibile per admin.

Vincoli:

- ledger resta fonte primaria per contabile;
- non creare reporting che bypassa ledger;
- nessun update a saldo;
- nessuna modifica a round storiche senza piano migration;
- attenzione a privacy e PII nei log/report.

Output richiesto prima della feature:

- piano dedicato `ROUND_REPORTING_DISPLAY_ID_PLAN.md` o aggiornamento del piano
  reporting esistente;
- matrice campi;
- query read-only;
- test di riconciliazione.

### Step 7 - Aggiustamenti Mines surface e hardening

Documenti di contesto:

- `docs/PRODUCT_CLOSURE_BACKLOG.md`
- `docs/MINES_RUNTIME_STABILISATION_PLAN.md`
- `docs/MINES_EXECUTION_PLAN.md`
- `docs/ARCHITECTURE_ATLAS_MINES.md`

Stato:

- pianificato;
- dettagli da definire per singole slice;
- non mischiare con F7-C se tocca gameplay/runtime.

Possibili stream:

- surface player e leggibilita' in-game;
- recover/error/session state;
- modale regole e label;
- hardening concorrenza/idempotenza solo con test obbligatori.

Vincoli:

- Mines resta server-authoritative;
- frontend non decide outcome, board o payout;
- payout runtime e RTP non si toccano senza documenti Mines/runtime.

### Step 8 - Production readiness e security review

Documenti:

- `docs/PRODUCTION_READINESS_BRIEF.md`
- `docs/SECURITY_REVIEW_PRE_PRODUCTION_PLAN.md`

Decisione attuale:

- non attivo come cantiere esecutivo;
- resta gating futuro;
- non blocca F7-C, i18n Mines, copy o UX locale;
- blocca qualsiasi go-live reale.

Non fare ora:

- deployment reale;
- secret strategy production;
- adapter HTTP esterno;
- hardening infrastrutturale completo.

### Step 9 - External adapter / Fase 9b-c

Documento:

- `docs/MINES_EXTERNAL_GAME_AND_TABLE_SESSION_PLAN.md`

Stato:

- rinviato;
- riprendere solo quando Michele dira' esplicitamente:

```text
voglio pubblicare in produzione
```

Da non fare ora:

- `HttpPlatformGameClient`;
- doppio path in-process/HTTP;
- contract test HTTP;
- security server-to-server;
- mTLS/HMAC/allowlist.

## Parallelizzazione multiagentica consigliata

La parallelizzazione va usata solo su write set separati.

### Agent A - Route e admin shell

Responsabilita':

- route Next dedicate;
- auth/admin session extraction;
- layout admin games;
- navigazione overview/category/detail.

Write set candidato:

- `frontend/app/admin/games/**`
- eventuali nuovi componenti `frontend/app/ui/admin/**`
- minime integrazioni in `frontend/app/ui/casinoking-console.tsx`

### Agent B - Mines editor decomposition

Responsabilita':

- hook e componenti del detail;
- separazione config/theme/assets/rules/labels;
- riduzione del monolite.

Write set candidato:

- `frontend/app/ui/mines/**`
- `frontend/app/ui/title-editor/**`

Non tocca route se Agent A le sta gestendo.

### Agent C - i18n backend/API

Responsabilita':

- migration `title_locale_maps`;
- service locale map;
- validator coverage;
- endpoint config admin/public con `locale`;
- test backend.

Write set candidato:

- `backend/migrations/sql/**`
- `backend/app/modules/platform/catalog/title_locale_service.py`
- `backend/app/modules/platform/catalog/title_config_service.py`
- `backend/app/modules/games/mines/backoffice_config.py`
- `backend/app/api/routes/admin.py`
- `backend/app/api/routes/mines.py`
- `tests/integration/test_title_configs_split.py`
- `tests/integration/test_mines_backoffice_config.py`

Non tocca frontend detail finche' Agent B non espone il punto UI concordato.

### Agent D - Frontend i18n resolver/player

Responsabilita':

- manifest TS;
- resolver label Mines;
- migrazione componenti player;
- mapping errori;
- modale rules;
- test/smoke visuale.

Write set candidato:

- `frontend/app/ui/mines/i18n/**`
- `frontend/app/ui/mines/**`
- `frontend/app/lib/helpers.ts`
- eventuali test frontend/browser se presenti

Da coordinare con Agent B per non editare lo stesso blocco del monolite.

### Agent E - QA, test e documentazione

Responsabilita':

- typecheck/build;
- smoke admin/player;
- documentazione finale;
- atlas solo se cambiano responsabilita'/mapping.

Write set candidato:

- `docs/**`
- test smoke/checklist

## Dipendenze critiche

- F7-C prima di Games overview Slice 3+.
- F7-C prima di I18N-1.
- Inventario e documentazione i18n possono restare attivi ora; implementazione
  i18n parte dopo F7-C.
- Backoffice translations editor dipende da F7-C o deve essere coordinato con
  il detail route.
- Migrazione componenti player puo' partire in parallelo al backend se il
  payload `presentation_config.i18n` e' concordato.
- Reporting/spin id non parte senza piano dedicato.
- Production/external adapter non parte senza trigger esplicito.

## Fuori scope globale

- payout runtime;
- RTP;
- RNG/fairness;
- wallet/ledger write paths;
- CMS completo;
- nuovi engine;
- i18n globale platform completa;
- produzione;
- external HTTP adapter.

## Checklist CTO

Stato post review: validata con caveat integrati.

Decisioni confermate:

- route target F7-C dinamiche e non Mines-only;
- livello di route per tab interne del detail: raccomandazione, tab interne non
  route dedicate nella prima F7-C;
- `title_locale_maps` come source of truth i18n Mines;
- `game.title` come titolo in-game localizzato;
- lingua pubblicata iniziale raccomandata `it`, allowlist editoriale
  `it`/`en`/`de`/`es`;
- una sola lingua pubblicata per config;
- nessun selector lingua nel gioco;
- nessun `ck_player_locale`;
- nessun parametro `locale` player-side;
- extra key strict mode;
- content production plan;
- static scan bloccante;
- backward compat `ui_labels_json` Opzione A;
- publish gating per copertura i18n completa;
- no i18n globale platform in questa fase;
- backoffice UI resta IT-only in questo epic;
- ownership copy: theme non contiene copy;
- F7-C come prerequisito di Games overview Slice 3+;
- F7-C come prerequisito di I18N-1;
- reporting/spin id come piano separato;
- production/external adapter rinviati.

## Verifiche previste per i prossimi task

Frontend:

```powershell
cd frontend
npx tsc --noEmit
npm run build
```

Backend, solo se si tocca backend/API/schema:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:56543/casinoking'
python -m pytest tests/integration/test_title_configs_split.py tests/integration/test_mines_backoffice_config.py
python -m pytest tests/integration/test_game_library_publication.py tests/contract/test_title_theme_contract.py tests/contract/test_admin_assets_contract.py
```

Smoke manuale:

- admin login;
- Games overview;
- Mines category;
- open detail by route;
- preview admin;
- save draft;
- publish live;
- player lobby;
- demo launch del title corretto;
- mobile 375px su lobby e Mines.

## Note documentali

Questa e' una pianificazione. Le implementazioni successive dovranno aggiornare:

- atlas platform/Mines se cambiano file/responsabilita';
- piani specifici se cambia sequenza;
- test/smoke plan se si aggiungono verifiche stabili.
