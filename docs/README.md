# CasinoKing Documentation Map

Porta di ingresso per umani e AI che arrivano sul progetto.

## Prima lettura obbligatoria

Leggere sempre, in questo ordine:

1. `docs/SOURCE_OF_TRUTH.md`
2. `docs/TASK_EXECUTION_GUARDRAILS.md`
3. `AGENTS.md`
4. `docs/DOCUMENTATION_MAINTENANCE.md`

Poi leggere i documenti sotto in base al tema del task.

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
| Platform/Game split | `CATALOG_ENGINE_TITLE_SITE_PLAN.md`, `TITLE_CODE_PROPAGATION_PLAN.md`, `TITLE_CONFIG_PLAN.md`, `MINES_EXTERNAL_GAME_AND_TABLE_SESSION_PLAN.md`, `PLATFORM_GAME_SEPARATION_AND_ENVIRONMENTS_MASTERPLAN_2026_04.md`, `PLATFORM_GAME_CONTRACT_AND_ENVIRONMENTS_IMPLEMENTATION_BLUEPRINT_2026_04.md`, `PLATFORM_GAME_M1_EXECUTION_PACKAGE_2026_04.md`, `PLATFORM_GAME_M1_FILE_BY_FILE_EXECUTION_PLAN_2026_04.md` |
| Consolidamento post Fase 3 | `docs/md/CasinoKing_Documento_37_Catalogo_Engine_Title_Site.md`, `docs/md/CasinoKing_Documento_38_Configurazione_Per_Title.md` |
| Product backlog | `PRODUCT_CLOSURE_BACKLOG.md`, `NEXT_STEPS_2026_04_08.md`, `EXECUTION_PLAN_APRIL_2026.md` |
| Mines stabilisation | `MINES_RUNTIME_STABILISATION_PLAN.md`, `MINES_EXECUTION_PLAN.md` |
| Finance | `FINANCIAL_AREA_DESIGN.md`, `FINANCIAL_AREA_EXECUTION_PLAN.md`, `FINANCIAL_UI_REFACTOR_PLAN.md` |
| UI / UX | `UI_UX_BLUEPRINT_P0.md`, `UI_UX_ACTION_PLAN_P0.md`, `EPIC_6_UI_REFACTOR_PLAN.md` |
| Auth/admin | `AUTH_SEPARATION_PLAN.md`, `AUTH_CLEANUP_P0.md` |
| Beta / infra | `BETA_HOSTING_DECISION_MEMO_2026_04.md`, `LOCAL_ENV_RESTART_PROCEDURE.md` |

## Roadmap macro-cantieri registrati (2026-05-04)

Questa sezione serve come fotografia di alto livello per umani e AI. Non e' autorizzazione a implementare: ogni cantiere va aperto solo quando Michele dara' istruzioni di dettaglio.

| Cantiere | Stato | Documenti di partenza |
| --- | --- | --- |
| Aggiustamenti gioco Mines | Pianificato, dettagli da definire | `docs/ARCHITECTURE_ATLAS_MINES.md`, `docs/MINES_EXTERNAL_GAME_AND_TABLE_SESSION_PLAN.md`, documenti Mines canonici/runtime |
| Backoffice UI, leggibilita' menu e reporting | Pianificato, dettagli da definire | `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`, documenti admin/finance canonici |
| Identificativo spin/round visibile nei report | Pianificato dentro il cantiere backoffice/reporting | Verificare prima il mapping tra `platform_rounds.id`, round Mines e eventuale display id; non introdurre schema o logica senza disegno dedicato |
| Modifiche sito web/player frontend | Pianificato, dettagli da definire | `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`, documenti UI/UX |
| Crypto wallet proprietario | Pianificato, richiede design dedicato | `docs/SOURCE_OF_TRUTH.md`, documenti financial core, atlas platform; area critica wallet/ledger/idempotenza |
| Mines external HTTP adapter, Fase 9b/c | Rinviato | Riprendere quando Michele dira' esplicitamente "voglio pubblicare in produzione" |

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
