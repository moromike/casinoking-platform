# CasinoKing - Game Admin Change Log Plan

## Stato

Slice 1 implementata: schema `admin_audit_log`, service transazionale e primo
evento `title_config_publish`.

Restano da implementare Slice 2 e Slice 3.

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

Vincoli critici di `admin_actions`:

- `target_user_id` obbligatorio;
- `wallet_type` obbligatorio con check `cash` / `bonus`;
- `direction` obbligatorio con check `credit` / `debit`;
- `amount` obbligatorio e `> 0`;
- `wallet_balance_after` obbligatorio;
- `ledger_transaction_id` obbligatorio;
- `idempotency_key` obbligatoria e unica.

Conclusione:

`admin_actions` e' una tabella finanziaria legata al ledger. Non deve essere
riusata o resa nullable per loggare modifiche operative non finanziarie.

## Schema decision

Decisione:

Creare una tabella separata `admin_audit_log` per audit operativo non
finanziario. `admin_actions` resta invariata come dominio finanziario/admin
ledger-linked.

Razionale:

- modifiche Title, Theme, Asset e Lobby non hanno un `target_user_id`;
- non hanno `wallet_type`, `direction`, `amount` o saldo risultante;
- non devono produrre `ledger_transactions`;
- non devono essere forzate dentro idempotenza finanziaria;
- popolare `admin_actions` con valori dummy falserebbe la semantica contabile;
- rendere nullable campi finanziari romperebbe invarianti e test esistenti.

Separazione dei domini:

| Tabella | Cosa traccia | Link obbligatori | Vincoli |
| --- | --- | --- | --- |
| `admin_actions` | Movimenti di denaro originati da admin | `ledger_transactions` | finanziari rigidi, idempotency unique |
| `admin_audit_log` | Modifiche di stato non finanziarie originate da admin | nessuna FK ledger | timestamp, admin, azione, risorsa, payload |

Migration prevista:

- usare il prossimo numero libero;
- allo stato attuale del repository, dopo `0029__site_title_lobby_publication.sql`
  la migration sara' `backend/migrations/sql/0030__admin_audit_log.sql`.

Schema iniziale:

```sql
CREATE TABLE admin_audit_log (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id uuid NOT NULL REFERENCES users(id),
    action_kind varchar(64) NOT NULL,
    resource_kind varchar(32) NOT NULL,
    resource_id varchar(128) NOT NULL,
    payload_json jsonb NOT NULL,
    request_fingerprint varchar(64) NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX idx_admin_audit_log_admin
    ON admin_audit_log (admin_user_id, created_at DESC);

CREATE INDEX idx_admin_audit_log_resource
    ON admin_audit_log (resource_kind, resource_id, created_at DESC);
```

Note:

- `request_fingerprint` non e' unique;
- l'audit log non e' una transazione idempotente;
- se la stessa azione viene ripetuta, deve poter generare una nuova riga;
- non salvare PII non necessaria: niente email, IP in chiaro o payload utente;
- modifiche finanziarie/manual adjustment/session void restano in
  `admin_actions`.

## Action kind iniziali

| Action kind | Resource kind | Resource id | Quando |
| --- | --- | --- | --- |
| `title_config_publish` | `title` | `title_code` | publish config live |
| `theme_publish` | `title` | `title_code` | publish theme live |
| `lobby_publication_change` | `site_title` | `site_code:title_code` | modifica visibilita', demo/real, posizione, metadata lobby |
| `title_asset_upload` | `title_asset` | `title_code:asset_key` | upload asset |
| `title_asset_delete` | `title_asset` | `title_code:asset_key` | delete asset |

Eventi futuri da valutare dopo Slice 1:

- `title_variant_create`;
- `title_profile_update`;
- `title_config_draft_save`;
- `theme_draft_save`.

## Payload minimo

Ogni evento deve avere:

- `id`;
- `admin_user_id`;
- `action_kind`;
- `resource_kind`;
- `resource_id`;
- `payload_json`;
- `request_fingerprint`;
- `created_at`.

`payload_json` deve essere compatto e operativo. Preferire diff o snapshot
before/after mirati invece di payload completi enormi.

## UI LOG

Prima versione:

- nuova voce/area LOG o pannello dentro backoffice admin;
- tabella compatta;
- filtri base per action kind, title_code, site_code, admin, data;
- detail leggero per metadata.

Non serve:

- timeline grafica complessa;
- diff visuale completo;
- rollback;
- export regolatorio.

## Sequenza

### Slice 1 - Migration, service e primo evento

- completata con `backend/migrations/sql/0030__admin_audit_log.sql`;
- completata con `backend/app/modules/platform/admin_audit/service.py`;
- `record_audit_entry(...)` accetta `cursor: psycopg.Cursor | None` per
  partecipare alla transazione chiamante;
- primo flusso strumentato: `title_config_publish`;
- chiamata audit inserita nel publish config Title dentro lo stesso cursor;
- aggiunti test mirati per schema, service transazionale e primo evento;
- verificato che `admin_actions`, ledger e wallet non vengano usati dal log
  operativo.

Accettazione Slice 1:

- migration applicabile dal runner locale;
- `admin_audit_log` contiene una riga dopo publish config Title;
- `request_fingerprint` non e' unique;
- nessun campo finanziario finto viene popolato;
- test esistenti wallet/ledger restano verdi.

### Slice 2 - Instrumentazione Games/Site

- tracciare `theme_publish`;
- tracciare `lobby_publication_change`;
- tracciare `title_asset_upload`;
- tracciare `title_asset_delete`;
- valutare solo dopo il primo passaggio se includere create variant e rename.

Accettazione Slice 2:

- ogni modifica operativa rilevante produce un evento leggibile;
- il payload contiene solo dati utili a debug e responsabilita';
- nessun payload salva PII non necessaria;
- nessun evento gameplay round-by-round.

### Slice 3 - UI LOG minima

- lista eventi;
- filtri minimi;
- detail metadata.

Accettazione Slice 3:

- nuova area LOG leggibile da backoffice;
- filtri base per action kind, resource, admin, data;
- detail JSON consultabile senza occupare la view principale;
- niente rollback, export regolatorio o timeline complessa.

## Accettazione

- nessun impatto su wallet/ledger;
- `admin_actions` resta finanziaria e ledger-linked;
- action kind operative tracciate in `admin_audit_log`;
- UI LOG leggibile;
- test/migration verdi;
- niente PII non necessaria;
- niente idempotency unique sul log operativo;
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
