# CasinoKing Documentation Map

Porta di ingresso per umani e AI che arrivano sul progetto.

## Prima lettura obbligatoria

Leggere sempre, in questo ordine:

1. `docs/SOURCE_OF_TRUTH.md`
2. `docs/TASK_EXECUTION_GUARDRAILS.md`
3. `docs/DOCUMENTATION_MAINTENANCE.md`
4. `docs/AI_CRITICAL_JUDGMENT_RULES.md`

Poi leggere i documenti sotto in base al tema del task.

`AGENTS.md` non e' una fonte primaria: contiene solo un puntatore a questi
documenti condivisi, perche' non e' garantito che sia letto da tutte le AI.

## Lettura proporzionata

Non leggere tutta la documentazione a ogni task.

Usare questo criterio:

1. leggere sempre i documenti obbligatori della sezione precedente
2. identificare il dominio coinvolto
3. leggere solo atlas, piani e fonti canoniche necessari per quel dominio
4. se il task e' solo operativo e non modifica codice o architettura, non leggere documenti di dominio non coinvolti

Esempi:

- `git status`, commit, push: bastano i documenti obbligatori e il controllo dello stato git
- riavvio ambiente locale: aggiungere `docs/LOCAL_ENV_RESTART_PROCEDURE.md`
- modifica Mines UI: aggiungere `docs/ARCHITECTURE_ATLAS_MINES.md` e i documenti Mines pertinenti se cambia comportamento ufficiale
- modifica wallet, ledger, cashout, accounting: aggiungere i documenti financial/API/DB indicati in `docs/SOURCE_OF_TRUTH.md`

Se il task tocca aree critiche o c'e' ambiguita', leggere di piu' e fermarsi prima di scegliere arbitrariamente.

## Evidenza di lettura

Quando una AI fa onboarding o prepara un task, deve distinguere chiaramente:

- file effettivamente letti
- file solo individuati o citati
- file non letti perche' non necessari al dominio del task

Non dichiarare "ho letto" un file se e' stato solo visto in una lista, dedotto da un entry point o citato da un altro documento.

Per task reali, prima di implementare deve confermare almeno:

1. documenti core effettivamente letti
2. documenti di dominio effettivamente letti
3. documenti volutamente non letti per lettura proporzionata

## Documenti di orientamento rapido

| Documento | Quando usarlo |
| --- | --- |
| `docs/PROJECT_ROOT_TREE_EXPLAINED.csv` | Per spiegare la struttura principale del repository in formato apribile/stampabile con Excel. |
| `CasinoKing.code-workspace` | Per aprire VS Code con gruppi logici numerati senza rinominare fisicamente le cartelle. |
| `docs/AI_CRITICAL_JUDGMENT_RULES.md` | Per ricordare alle AI di essere severe nei giudizi, non accondiscendenti, e di correggere scelte rischiose dell'utente. |
| `docs/GAME_ARCHITECTURE_OVERVIEW.md` | Per spiegare a piu' livelli Casino Platform, Game Runtime Layer, Game Adapter, Mines, RNG/fairness, frontend e monolite modulare. |
| `docs/CMS_ROADMAP_AND_EXTERNAL_GAMES_PLAN.md` | Per ragionare su CMS, homepage/banner, asset, giochi esterni e provider mock senza introdurre integrazioni real money premature. |
| `docs/PLAYER_ACCOUNT_UX_REDESIGN_PLAN.md` | Per ridisegnare l'area account player con summary first, estratto conto espandibile, cassa, profilo e sicurezza. |
| `docs/ACCOUNT_WALLET_GAME_HISTORY_REDESIGN_PLAN.md` | Per separare Cassa finanziaria, Storico gioco, Accessi e paginazione account. |
| `docs/ACCOUNT_ACC_1_ENDPOINT_AUDIT.md` | Per verificare quali endpoint account sono usabili, perche' `/account/wallet-movements` resta tecnico e perche' Cassa usa lo statement read model. |
| `docs/ACCOUNT_CASHIER_MOVEMENTS_REDESIGN_ANALYSIS.md` | Per rifare la pagina Cassa come estratto movimenti filtrabile, con righe business espandibili e cash/bonus separati. |
| `docs/MINES_REPLAY_VIEWER_PLAN.md` | Per capire e modificare il replay read-only delle mani Mines, richiamato da Storico gioco e riusabile in futuro da gioco/backoffice. |
| `docs/MINES_SKIN_EXTENDED_CUSTOMIZATION_PLAN.md` | Per pianificare skin Mines avanzate per Title: titolo testo/immagine, sfondo area gioco, texture celle, button styling controllato, senza toccare core/RNG/payout/wallet. |
| `docs/MINES_SOUND_ASSETS_PLAN.md` | Per introdurre suoni Mines configurabili da backoffice tramite asset registry. |
| `docs/MINES_VISUAL_EFFECTS_PLAN.md` | Per aggiungere effetti visuali Mines client-side senza toccare core/RNG/payout. |
| `docs/SITE_BANNER_AND_MOCKUP_PLAN.md` | Per completare banner/homepage media e progettare mockup sito prima del redesign. |
| `docs/ARCHITECTURE_ATLAS_MINES.md` | Per capire Mines, i layer gioco, frontend, RNG, fairness, payout, backoffice e riuso futuro. |
| `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md` | Per capire piattaforma, frontend player/admin, auth, wallet, ledger, DB, registrazione e backoffice. |
| `docs/DOCUMENTATION_MAINTENANCE.md` | Per sapere quali documenti aggiornare quando si modifica codice o architettura. |
| `docs/LOCAL_ENV_RESTART_PROCEDURE.md` | Per avviare o riavviare l'ambiente locale. |

## Fonti canoniche

I file canonici restano in:

- `docs/word/`
- `docs/runtime/`

Il riferimento pratico alla gerarchia e' sempre:

- `docs/SOURCE_OF_TRUTH.md`

I mirror markdown e i documenti operativi non devono contraddire i Word canonici o gli allegati runtime.

## Mirror e documenti tecnici numerati

La cartella `docs/md/` contiene:

- mirror markdown dei documenti canonici Word
- documenti operativi numerati successivi
- indice interno in `docs/md/INDEX.md`

Usarla quando serve leggere velocemente il contenuto senza aprire Word.

## Documenti operativi attuali

| Area | Documenti |
| --- | --- |
| Platform/Game split | `GAME_ARCHITECTURE_OVERVIEW.md`, `CATALOG_ENGINE_TITLE_SITE_PLAN.md`, `TITLE_CODE_PROPAGATION_PLAN.md`, `TITLE_CONFIG_PLAN.md`, `ASSET_REGISTRY_PLAN.md`, `THEME_SYSTEM_PLAN.md`, `MINES_EXTERNAL_GAME_AND_TABLE_SESSION_PLAN.md`, `PLATFORM_GAME_SEPARATION_AND_ENVIRONMENTS_MASTERPLAN_2026_04.md`, `PLATFORM_GAME_CONTRACT_AND_ENVIRONMENTS_IMPLEMENTATION_BLUEPRINT_2026_04.md`, `PLATFORM_GAME_M1_EXECUTION_PACKAGE_2026_04.md`, `PLATFORM_GAME_M1_FILE_BY_FILE_EXECUTION_PLAN_2026_04.md` |
| Editor / Backoffice | `TITLE_EDITOR_SHELL_PLAN.md`, `BACKOFFICE_GAMES_UX_REORGANIZATION_PLAN.md`, `F7_C_GAMES_DETAIL_ROUTE_REFACTOR_PLAN.md`, `SITE_LOBBY_PUBLICATION_PLAN.md`, `SITE_CMS_EDITORIAL_UX_PLAN.md`, `CMS_ROADMAP_AND_EXTERNAL_GAMES_PLAN.md`, `CMS_0_ADMIN_CMS_INVENTORY.md`, `GAME_ADMIN_CHANGE_LOG_PLAN.md` |
| Demo mode | `DEMO_MODE_PLAN.md` |
| Consolidamento post Fase 3 | `docs/md/CasinoKing_Documento_37_Catalogo_Engine_Title_Site.md`, `docs/md/CasinoKing_Documento_38_Configurazione_Per_Title.md` |
| Product backlog | `PRODUCT_CLOSURE_BACKLOG.md`, `NEXT_STEPS_2026_04_08.md`, `EXECUTION_PLAN_APRIL_2026.md`, `AI_CRITICAL_JUDGMENT_RULES.md` |
| CTO review / next execution | `NEXT_EXECUTION_DETAILED_CTO_REVIEW_PLAN.md`, `E2E_MANUAL_SMOKE_PLAN.md`, `MASTER_LAUNCH_LEGACY_REMOVAL_PLAN.md`, `NEXT_UX_SLICES_CTO_REVIEW_PLAN.md` |
| Mines stabilisation | `MINES_RUNTIME_STABILISATION_PLAN.md`, `MINES_EXECUTION_PLAN.md`, `MINES_IN_GAME_TITLE_PLAN.md`, `MINES_REPLAY_VIEWER_PLAN.md`, `MINES_SKIN_EXTENDED_CUSTOMIZATION_PLAN.md`, `MINES_I18N_CTO_REVIEW_BRIEF.md`, `MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`, `MINES_I18N_STRING_INVENTORY.md` |
| Finance | `FINANCIAL_AREA_DESIGN.md`, `FINANCIAL_AREA_EXECUTION_PLAN.md`, `FINANCIAL_UI_REFACTOR_PLAN.md` |
| UI / UX | `PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md`, `PLAYER_LOBBY_UX_PLAN.md`, `PLAYER_ACCOUNT_UX_REDESIGN_PLAN.md`, `ACCOUNT_WALLET_GAME_HISTORY_REDESIGN_PLAN.md`, `ACCOUNT_ACC_1_ENDPOINT_AUDIT.md`, `ACCOUNT_CASHIER_MOVEMENTS_REDESIGN_ANALYSIS.md`, `SITE_BANNER_AND_MOCKUP_PLAN.md`, `PRODUCT_COPY_ENGLISH_CLEANUP_PLAN.md`, `MINES_COPY_LABELS_AND_I18N_READINESS_PLAN.md`, `MINES_I18N_CTO_REVIEW_BRIEF.md`, `MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`, `MINES_I18N_STRING_INVENTORY.md`, `I18N_FOUNDATION_DEFERRED_DECISION.md`, `UI_UX_BLUEPRINT_P0.md`, `UI_UX_ACTION_PLAN_P0.md`, `EPIC_6_UI_REFACTOR_PLAN.md` |
| Auth/admin | `AUTH_SEPARATION_PLAN.md`, `AUTH_CLEANUP_P0.md` |
| Beta / infra | `BETA_HOSTING_DECISION_MEMO_2026_04.md`, `LOCAL_ENV_RESTART_PROCEDURE.md`, `PRODUCTION_READINESS_BRIEF.md`, `SECURITY_REVIEW_PRE_PRODUCTION_PLAN.md` |

## Roadmap macro-cantieri registrati (2026-05-04)

Questa sezione serve come fotografia di alto livello per umani e AI. Non e' autorizzazione a implementare: ogni cantiere va aperto solo quando Michele dara' istruzioni di dettaglio.

| Cantiere | Stato | Documenti di partenza |
| --- | --- | --- |
| Product copy / i18n | Attivo: platform/backoffice English-first senza i18n globale immediata. Per Mines l'epic i18n foundation e' approvato dal CTO con caveat recepiti e decisione definitiva: locale/content map versionata per Title, resolver player, editor contenuti/traduzioni, coverage report, publish gating, allowlist editoriale `it`/`en`/`de`/`es`, una sola lingua pubblicata per gioco/config, runtime e config pubblicata single-locale, nessun selector lingua in-game, nessun `ck_player_locale`, nessun parametro `locale` player-side. Backoffice IT-only per questo epic; editor contenuti Mines i18n/lingua pubblicata parte del cantiere Mines. Rules body in `title_locale_maps.locales_json[locale].rules_sections.*.body_html`; `rules_sections_json` solo projection legacy della lingua pubblicata. I18N-1 parte solo dopo F7-C | `docs/PRODUCT_COPY_ENGLISH_CLEANUP_PLAN.md`, `docs/MINES_I18N_CTO_REVIEW_BRIEF.md`, `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`, `docs/MINES_I18N_STRING_INVENTORY.md`, `docs/MINES_COPY_LABELS_AND_I18N_READINESS_PLAN.md`, `docs/I18N_FOUNDATION_DEFERRED_DECISION.md`, atlas platform/Mines |
| Fase 7: Editor backoffice riusabile per Title | F7-C route/detail stabilizzato: route dedicate `/admin/games`, `/admin/games/[engine]`, `/admin/games/[engine]/titles/[title_code]` implementate; direct detail carica il Title da catalogo e valida l'engine; smoke HTTP locale verde sulle route Games. `MinesBackofficeEditor` e' ora piu' orchestratore: command bar, overview, i18n/copy/rules, labels legacy, board assets, grid config e theme sono componenti separati. Restano da valutare hook config/theme/assets solo se riducono complessita' reale | `docs/TITLE_EDITOR_SHELL_PLAN.md`, `docs/BACKOFFICE_GAMES_UX_REORGANIZATION_PLAN.md`, `docs/F7_C_GAMES_DETAIL_ROUTE_REFACTOR_PLAN.md`, `docs/DEMO_MODE_PLAN.md`, `docs/THEME_SYSTEM_PLAN.md` |
| Aggiustamenti gioco Mines | Pianificato. Titolo in-game Mines confluisce nella key i18n `game.title` se il piano i18n Mines viene implementato; la skin estesa per Title e' pianificata come configurazione visuale separata da core/RNG/payout/wallet. | `docs/ARCHITECTURE_ATLAS_MINES.md`, `docs/MINES_IN_GAME_TITLE_PLAN.md`, `docs/MINES_SKIN_EXTENDED_CUSTOMIZATION_PLAN.md`, `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`, `docs/MINES_I18N_STRING_INVENTORY.md`, `docs/MINES_EXTERNAL_GAME_AND_TABLE_SESSION_PLAN.md`, documenti Mines canonici/runtime |
| Backoffice UI, leggibilita' menu e reporting | Pianificato; ordine operativo aggiornato dopo review CTO: Games overview, Site/Lobby backoffice, audit leggero, player lobby, error pattern, copy cleanup platform e i18n Mines dedicata | `docs/PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md`, `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`, `docs/BACKOFFICE_GAMES_UX_REORGANIZATION_PLAN.md`, documenti admin/finance canonici |
| Game admin change log / audit leggero | Slice 1-3 implementate: nuova tabella `admin_audit_log`, service transazionale con cursor opzionale, `title_config_publish` sul publish reale, instrumentation per theme publish/pubblicazione lobby/upload-delete asset e UI `LOG` read-only con filtri, paginazione e detail JSON. `admin_actions` resta solo finanziaria/ledger-linked | `docs/GAME_ADMIN_CHANGE_LOG_PLAN.md`, `docs/BACKOFFICE_GAMES_UX_REORGANIZATION_PLAN.md`, `docs/SITE_LOBBY_PUBLICATION_PLAN.md`, atlas platform/Mines |
| Identificativo spin/round visibile nei report | Pianificato dentro il cantiere backoffice/reporting | Verificare prima il mapping tra `platform_rounds.id`, round Mines e eventuale display id; non introdurre schema o logica senza disegno dedicato |
| Modifiche sito web/player frontend | In corso: Site/Lobby Publishing ora separa gestione sito e configurazione giochi, con metadata lobby, ordine, featured, preview da `GET /games/library`, preview master via token admin e validazione config live prima della pubblicazione. La prossima evoluzione Site/CMS e' un editor editoriale guidato, non un CMS proprietario completo: vedi `SITE_CMS_EDITORIAL_UX_PLAN.md`. Player Lobby UX Slice 1+Visual QA implementata: card professionali, spotlight compatto, CTA demo/real, copy inglese, stati loading/empty/error, cleanup varianti test pubblicate e responsive 375px verificato su lobby/Mines demo. Launch hardening applicato: il launch pubblico richiede `title_code`, rifiuta i master con `LAUNCH_REJECTED_MASTER` e rispetta i flag Site/Lobby. Mines applica primo pattern popup errori con saldo insufficiente in inglese | `docs/PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md`, `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`, `docs/SITE_LOBBY_PUBLICATION_PLAN.md`, `docs/SITE_CMS_EDITORIAL_UX_PLAN.md`, `docs/PLAYER_LOBBY_UX_PLAN.md`, documenti UI/UX |
| Crypto wallet proprietario | Pianificato, richiede design dedicato | `docs/SOURCE_OF_TRUTH.md`, documenti financial core, atlas platform; area critica wallet/ledger/idempotenza |
| Production readiness e security review | Tracker pre-produzione aggiunti; non bloccano i refactor UX ma bloccano qualsiasi go-live reale | `docs/PRODUCTION_READINESS_BRIEF.md`, `docs/SECURITY_REVIEW_PRE_PRODUCTION_PLAN.md`, documenti financial/core e atlas pertinenti |
| Mines external HTTP adapter, Fase 9b/c | Rinviato | Riprendere quando Michele dira' esplicitamente "voglio pubblicare in produzione" |
| Game architecture, CMS roadmap e player account UX | Pianificato: documenti di progetto aggiunti per review CTO su naming Platform/Game, roadmap CMS/home/banner/external games e redesign account player summary-first | `docs/GAME_ARCHITECTURE_OVERVIEW.md`, `docs/CMS_ROADMAP_AND_EXTERNAL_GAMES_PLAN.md`, `docs/PLAYER_ACCOUNT_UX_REDESIGN_PLAN.md` |

## Checkpoint di ripresa rapido

Quando Michele dira' "riprendiamo", anche in una nuova chat, partire da qui.

Stato consolidato:

- Games overview, Site/Lobby Publishing con vista compatta, LOG operativo,
  Player lobby Slice 1+Visual QA, preview admin token, primo error popup Mines
  e copy English nelle aree toccate sono implementati e documentati.
- Il backoffice apre preview demo con token admin dedicato; `preview=1` da solo
  non e' una autorizzazione backend.
- Il launch pubblico richiede `title_code` esplicito, rifiuta i master con
  `LAUNCH_REJECTED_MASTER` e rispetta `lobby_visibility`, `demo_enabled` e
  `real_enabled`.
- Lo smoke E2E manuale e' stato eseguito su branch/commit versionati; i finding
  visuali secondari sono chiusi nella prima Player lobby visual QA e tracciati
  in `docs/PRODUCT_CLOSURE_BACKLOG.md`.
- L'ambiente locale e' stato verificato con frontend/backend/Postgres/Redis
  healthy dopo il restart frontend.

Prossimo passo consigliato:

1. Raffinare l'editor traduzioni Mines con coverage summary/diff UI se serve
   prima della prossima review CTO.
2. Eseguire audit CMS-UX-1 su Site/Lobby e decidere la prima slice editoriale.
3. Riprendere Games overview Slice 3+ solo sopra route/detail stabilizzati.

Documenti da leggere per ripartire:

- `docs/NEXT_EXECUTION_DETAILED_CTO_REVIEW_PLAN.md`
- `docs/F7_C_GAMES_DETAIL_ROUTE_REFACTOR_PLAN.md`
- `docs/MINES_I18N_CTO_REVIEW_BRIEF.md`
- `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`
- `docs/MINES_I18N_STRING_INVENTORY.md`
- `docs/MINES_COPY_LABELS_AND_I18N_READINESS_PLAN.md`
- `docs/MINES_IN_GAME_TITLE_PLAN.md`
- `docs/MINES_SKIN_EXTENDED_CUSTOMIZATION_PLAN.md`
- `docs/E2E_MANUAL_SMOKE_PLAN.md`
- `docs/MASTER_LAUNCH_LEGACY_REMOVAL_PLAN.md`
- `docs/NEXT_UX_SLICES_CTO_REVIEW_PLAN.md`
- `docs/PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md`
- `docs/PLAYER_LOBBY_UX_PLAN.md`
- `docs/SITE_LOBBY_PUBLICATION_PLAN.md`
- `docs/SITE_CMS_EDITORIAL_UX_PLAN.md`
- `docs/CMS_0_ADMIN_CMS_INVENTORY.md`
- `docs/GAME_ARCHITECTURE_OVERVIEW.md`
- `docs/CMS_ROADMAP_AND_EXTERNAL_GAMES_PLAN.md`
- `docs/PLAYER_ACCOUNT_UX_REDESIGN_PLAN.md`
- `docs/BACKOFFICE_GAMES_UX_REORGANIZATION_PLAN.md`
- `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
- `docs/ARCHITECTURE_ATLAS_MINES.md`

## Archivio

La cartella `docs/archive/` contiene documenti storici, prompt, note di sessione o piani superati.

L'indice dell'archivio e' `docs/archive/README.md`.

Regola:

- non usarli come fonte primaria
- consultarli solo per contesto storico
- se un documento archiviato torna rilevante, creare o aggiornare un documento operativo attuale invece di modificare direttamente lo storico

## Percorsi consigliati

### Se devi lavorare su Mines

1. `docs/SOURCE_OF_TRUTH.md`
2. `docs/TASK_EXECUTION_GUARDRAILS.md`
3. `docs/ARCHITECTURE_ATLAS_MINES.md`
4. Documenti Mines canonici indicati in `SOURCE_OF_TRUTH.md`
5. Allegati runtime in `docs/runtime/`

### Se devi lavorare su wallet, ledger, accounting

1. `docs/SOURCE_OF_TRUTH.md`
2. `docs/TASK_EXECUTION_GUARDRAILS.md`
3. `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
4. Documento 05 v3, 11 v2, 12 v3, 13 v3

### Se devi lavorare su frontend player/admin

1. `docs/SOURCE_OF_TRUTH.md`
2. `docs/TASK_EXECUTION_GUARDRAILS.md`
3. `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
4. Se riguarda Mines, anche `docs/ARCHITECTURE_ATLAS_MINES.md`

### Se devi lavorare su ambiente locale

1. `docs/SOURCE_OF_TRUTH.md`
2. `docs/TASK_EXECUTION_GUARDRAILS.md`
3. `docs/LOCAL_ENV_RESTART_PROCEDURE.md`

## Regola pratica per AI nuove

I file root specifici per agenti (`AGENTS.md`, `CLAUDE.md`, `GEMINI.md`, `ANTIGRAVITY.md`) devono restare leggeri e puntare a questa guida condivisa.

Prima di modificare codice, una AI deve poter rispondere a queste domande:

1. Quale dominio sto toccando?
2. Quali documenti governano quel dominio?
3. Quali codici atlas identificano i blocchi coinvolti?
4. Quali test/verifiche sono obbligatorie?
5. Quale documento devo aggiornare se cambio comportamento, architettura o mapping file?

Durante il task, una AI deve seguire questo metodo:

1. identificare dominio e documenti da leggere
2. proporre o eseguire il passo minimo corretto per la richiesta
3. implementare solo cio' che e' stato chiesto
4. evitare miglioramenti non richiesti: se utili, proporli soltanto
5. chiudere dichiarando verifiche eseguite e impatto documentale

Prima di chiudere un task, una AI deve dichiarare:

1. quali documenti ha letto
2. quali documenti ha aggiornato
3. se non ha aggiornato documenti, perché non era necessario secondo `docs/DOCUMENTATION_MAINTENANCE.md`
