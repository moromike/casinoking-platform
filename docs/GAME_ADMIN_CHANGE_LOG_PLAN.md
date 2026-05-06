# CasinoKing - Game Admin Change Log Plan

## Stato

Piano operativo da validare prima di implementare.

## Obiettivo

Introdurre un LOG operativo leggero per modifiche backoffice su giochi e lobby.

Non e' audit finanziario, non e' event sourcing e non traccia gameplay round by
round. Serve a rispondere a domande operative:

- chi ha creato una variante;
- chi ha rinominato un Title;
- chi ha pubblicato una config;
- chi ha modificato la pubblicazione lobby;
- quando e' avvenuta la modifica;
- quale oggetto e' stato toccato.

## Perche' e' prioritario

In un prodotto casino, le modifiche backoffice non possono restare invisibili.
Anche prima della produzione vera, conviene impostare il tracciamento delle
azioni operative principali.

## Confini

### Dentro scope

- modifiche catalogo/Title;
- publish config;
- theme publish;
- asset upload/delete;
- lobby publication change.

### Fuori scope

- ledger;
- wallet;
- reconciliation;
- round gameplay;
- RNG/fairness artifacts;
- event sourcing;
- rollback automatico;
- audit regolatorio completo.

## Base tecnica esistente

Esiste gia' `admin_actions`:

- creato in `backend/migrations/sql/0006__admin_actions_foundations.sql`;
- esteso in `backend/migrations/sql/0022__admin_actions_session_void.sql`;
- oggi pensato per azioni finanziarie/admin con constraint rigidi.

Action type attuali:

- `admin_adjustment`;
- `bonus_grant`;
- `session_void`.

Nota critica:

`admin_actions` oggi contiene campi finanziari obbligatori come
`target_user_id`, `wallet_type`, `direction`, `amount`, `ledger_transaction_id`.
Per usarla anche come audit operativo game/lobby serve una decisione di schema,
non basta aggiungere un valore al check constraint.

## Decisione schema da prendere

### Opzione preferita da validare

Evolvere `admin_actions` in audit nucleus condiviso, mantenendo compatibilita'
con le azioni finanziarie esistenti.

Possibili interventi:

- allargare `action_type`;
- introdurre target generici (`target_type`, `target_id`, `target_code`);
- rendere alcuni campi finanziari nullable solo per action type non finanziari;
- spostare dettagli in `metadata_json`;
- aggiungere constraint condizionali per garantire che le azioni finanziarie
  restino complete.

### Opzione fallback

Creare una tabella operativa separata, per esempio `admin_operational_actions`,
solo se estendere `admin_actions` risulta troppo invasivo o semanticamente
pericoloso.

Nota:

La review CTO preferisce estendere `admin_actions`. La fallback esiste solo per
evitare una migration sbagliata.

## Eventi candidati

| Action type | Target | Quando |
| --- | --- | --- |
| `title_variant_created` | title/source title | duplicazione variante |
| `title_profile_updated` | title | rinomina o aggiornamento profilo |
| `title_config_draft_saved` | title | save draft config |
| `title_config_published` | title | publish config live |
| `title_theme_draft_saved` | title | save draft theme |
| `title_theme_published` | title | publish theme live |
| `title_asset_uploaded` | title asset | upload asset |
| `title_asset_deleted` | title asset | delete asset |
| `lobby_publication_changed` | site/title | modifica visibilita', demo/real, posizione, metadata lobby |

## Payload minimo

Ogni evento deve avere:

- `id`;
- `admin_user_id`;
- `action_type`;
- `target_type`;
- `target_id` o `target_code`;
- `site_code` quando rilevante;
- `engine_code` quando rilevante;
- `title_code` quando rilevante;
- `summary`;
- `metadata_json`;
- `created_at`.

Non salvare payload completi enormi se non servono.

## UI LOG

Prima versione:

- nuova voce/area LOG o pannello dentro backoffice admin;
- tabella compatta;
- filtri base per action type, title_code, site_code, admin, data;
- detail leggero per metadata.

Non serve:

- timeline grafica complessa;
- diff visuale completo;
- rollback;
- export regolatorio.

## Sequenza

### Slice 1 - Schema decision

- scegliere opzione schema;
- scrivere migration plan;
- definire action type e payload;
- validare con CTO prima del codice.

### Slice 2 - Instrumentazione Games/Site

- tracciare create variant;
- tracciare rename/profile;
- tracciare config publish;
- tracciare lobby publication change.

### Slice 3 - UI LOG minima

- lista eventi;
- filtri minimi;
- detail metadata.

## Accettazione

- nessun impatto su wallet/ledger;
- azioni finanziarie esistenti restano valide;
- action type operative tracciate;
- UI LOG leggibile;
- test/migration verdi;
- niente event sourcing.

## Cosa potrai fare

- vedere chi ha fatto modifiche operative a giochi e lobby;
- ricostruire una sequenza base di publish/config;
- supportare debug e responsabilita' backoffice.

## Cosa non potrai fare

- usare il LOG come ledger;
- usare il LOG come audit regolatorio completo;
- fare rollback automatico;
- tracciare ogni giocata;
- sostituire report finanziari.
