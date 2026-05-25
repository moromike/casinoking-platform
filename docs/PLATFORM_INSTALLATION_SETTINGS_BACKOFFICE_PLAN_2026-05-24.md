Status: ACTIVE
Last meaningful update: 2026-05-24

# Platform Installation Settings Backoffice Plan

CTO approval required before implementation.

CTO review: `docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_CTO_REVIEW_2026-05-24.md`.

Current-state CTO review:
`docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`.

CTO status: read-only MVP approved after error/request foundation. Editable
settings are not approved yet.

## 1. Problematica

CasinoKing ha molti parametri e comportamenti distribuiti tra codice, env,
config per title, runtime game config e documenti. Alcuni sono correttamente
hardcoded per sicurezza; altri potrebbero essere configurabili; altri ancora
devono essere solo visibili in backoffice per dare controllo operativo.

Michele ha chiesto una sezione backoffice generale di installazione dove:

- controllare cio' che e' corretto controllare;
- vedere cio' che oggi e' embedded nel codice ma dovrebbe essere parametrico;
- consultare la matrice errori;
- governare aspetti di logging/retention/finanza senza modificare codice.

Il rischio e' creare un pannello "onnipotente" che permette di rompere math,
ledger, sicurezza o compliance live. Serve quindi distinguere tra visibile,
configurabile e bloccato.

## 2. Principio di architettura

Non tutto cio' che e' parametrico deve essere editabile.

Classificazione:

| Classe | Esempio | Backoffice |
| --- | --- | --- |
| Runtime safe config | label, default UI, retention non legale | Editabile con validation |
| Operational toggle | log level, feature flag non finanziaria | Editabile con audit |
| Sensitive config | JWT secret, DB URL, seed secret | Non visibile o masked read-only |
| Financial policy | retention ledger, payout settlement policy | Read-only o CTO/legal gated |
| Game math | RTP, probability, max win | Title/game admin con publish gate, non global casuale |
| Error registry | codice/status/retryability | Read-only MVP |

RBAC CTO:

- MVP visibile solo a superadmin;
- nessun accesso player o admin standard;
- in futuro separare `platform_settings_view` e `platform_settings_edit`;
- ogni edit futuro richiede audit operativo.

## 3. Direzione alto livello

Creare un'area backoffice:

```text
Admin -> Platform -> Installation Settings
```

Con sezioni:

1. Overview;
2. Environment;
3. Observability / Logging;
4. Error Matrix;
5. Finance & Retention;
6. Session & Recovery;
7. Game Registry Health;
8. Change History.

Ogni modifica scrive `admin_audit_log`. Le configurazioni critiche richiedono
publish o conferma forte.

CTO restriction:

La prima versione deve essere un read model, non un editor. L'obiettivo MVP e'
mostrare verita' operative e gap di configurazione, non permettere di cambiare
comportamenti live.

## 4. Modello dati logico

MVP possibile:

```text
platform_settings
  key
  value_json
  value_type
  scope
  visibility
  editable
  validation_schema_json
  updated_by
  updated_at
  published_value_json
  draft_value_json
```

Alternative:

- file/env per impostazioni infrastrutturali read-only;
- DB settings per controlli operativi;
- registry codice per error matrix e game registry;
- config per title per parametri gioco.

Non va forzato tutto nella stessa tabella se il dominio ha gia' una fonte piu'
corretta.

Source-of-truth inventory obbligatorio:

Ogni riga mostrata in UI deve dichiarare:

| Campo | Significato |
| --- | --- |
| `setting_key` | Nome stabile |
| `source_of_truth` | env/code/db/registry/title_config |
| `owner` | platform/security/finance/game/product |
| `visibility` | hidden/masked/read_only/editable |
| `restart_required` | yes/no |
| `environment_scope` | local/staging/prod/all |
| `audit_required` | yes/no |
| `risk_class` | low/medium/high/critical |

Senza questo inventario, non costruire controlli editabili.

## 5. Sezioni proposte

### 5.1 Overview

Mostra:

- ambiente corrente;
- versione app;
- timezone;
- API base;
- DB migration version;
- giochi registrati;
- stato servizi principali;
- warning su config incomplete.

### 5.2 Environment

Read-only/masked:

- `APP_ENV`;
- API prefix;
- CORS origins;
- asset storage root;
- public site code default;
- build/version metadata.

Non mostrare:

- secret JWT;
- password DB;
- token provider;
- server seeds.

Ambiente:

- local/staging possono mostrare piu' diagnostica;
- produzione deve usare masking aggressivo;
- i campi che richiedono restart devono essere read-only e indicare
  "restart required";
- CORS e storage path vanno mostrati come diagnostica, non editati in MVP.

### 5.3 Observability / Logging

Read-only MVP:

- log level effettivo;
- request id mode;
- structured logging enabled;
- redaction policy version;
- retention dichiarata;
- log sink type.

Editabile in futuro, con audit e solo dopo approvazione:

- log level runtime;
- enable structured debug for local/staging;
- retention application logs;
- payload max bytes;
- slow request threshold;
- sampling per categorie rumorose.

Read-only:

- log sink type;
- current request id mode;
- last logging health check.

### 5.4 Error Matrix

Read-only MVP da error registry:

- code;
- domain;
- http status;
- player visible;
- admin visible;
- retryable;
- log level;
- support action.

Futuro:

- override copy/support action per locale, ma non cambiare semantica codice.

MVP: solo read-only. Nessuna modifica a codice, status, retryability o log
level dalla UI.

### 5.5 Finance & Retention

Mostra e, dove sicuro, controlla:

- ledger retention policy (read-only/legal);
- replay retention days;
- admin audit retention days;
- statement pagination defaults;
- finance report batch size;
- reconciliation schedule;
- quarantine threshold.

Qualsiasi setting che puo' alterare denaro richiede CTO/legal gate.

MVP: read-only. Retention e financial policy possono essere mostrate come
decisioni/documenti collegati, non editate.

### 5.6 Session & Recovery

Parametri:

- access session timeout;
- auto-settlement job enabled;
- timeout sweep interval;
- retry max per action error;
- table balance default/min/max se platform-wide.

Nota: l'immagine di settlement resta game-specific. La piattaforma puo' dire
"serve auto-settlement", ma ogni gioco definisce refund/cashout semanticamente.

MVP: read-only. Access session timeout, sweep interval e auto-settlement policy
non sono editabili finche' non esiste un piano di rollout e test dedicato.

### 5.7 Game Registry Health

Per ogni gioco:

- registered in lobby;
- runtime route;
- finance adapter;
- replay adapter;
- error namespace;
- title editor registered;
- config completeness;
- last smoke status, se disponibile.

Questa sezione evita il problema "il gioco e' pubblicato ma non gestibile" o
"replay esiste in player ma non in admin".

### 5.8 Change History

Lista da `admin_audit_log` filtrata su `resource_kind = platform_settings`.

## 6. Approccio a basso livello

### 6.1 Read model prima della mutazione

Prima implementazione consigliata:

1. pagina read-only che aggrega stato reale;
2. Error Matrix read-only;
3. Game Registry Health;
4. solo dopo, setting editabili a basso rischio.

Questo evita di creare editor per parametri non ancora compresi.

UI rule:

I valori read-only devono sembrare read-only. Non usare input disabilitati se
sembrano campi modificabili; preferire definition list, badge, status rows e
copy esplicita "read-only".

### 6.2 Capability descriptors

Ogni setting deve dichiarare:

- owner;
- default;
- source of truth;
- editability;
- validation;
- restart required si/no;
- audit required si/no;
- environment restrictions.

### 6.3 Draft/publish

Per setting operativi:

- bozza;
- validation;
- publish;
- audit entry;
- reload behavior documentato.

Per setting semplici locali, si puo' valutare save diretto, ma default sicuro e'
draft/publish.

Non implementare draft/publish nel MVP read-only. Disegnarlo solo quando viene
approvato il primo setting editabile.

## 7. Gate implementativi

- Nessun secret visibile.
- Ogni setting ha owner e source of truth.
- Ogni modifica scrive audit.
- Nessun parametro finanziario pericoloso editabile senza gate.
- Error Matrix mostra codici dal registry.
- UI non promette controlli non implementati.
- Product Owner walkthrough su `localhost:3000/admin`.

MVP approvato:

- Platform Settings shell read-only;
- Overview;
- Environment diagnostics masked/read-only;
- Error Matrix read-only;
- Game Registry Health;
- Observability status;
- Finance retention display;
- Change History da `admin_audit_log` se gia' disponibile.

Fuori MVP:

- editing log level;
- editing session timeout;
- editing finance retention;
- editing settlement behavior;
- editing error registry;
- editing secrets/env.

## 8. Effort stimato

Parte A dettagliata: 4-6 prompt.

Parte B MVP read-only:

- backend aggregation endpoints: 4-7 prompt;
- frontend Platform Settings shell: 4-7 prompt;
- Error Matrix read-only: 3-5 prompt;
- Game Registry Health: 3-5 prompt;
- tests/docs: 3-5 prompt.

Totale MVP read-only: 17-29 prompt.

Parte B editable settings low-risk: +10-18 prompt.

## 9. Stop-and-Ask

Fermarsi se:

- un setting finanziario viene richiesto editabile;
- un secret rischia di comparire in UI;
- un parametro richiede restart ma UI lo presenta live;
- si vuole bypassare draft/publish per impostazioni critiche;
- Error Matrix viene resa editabile senza disegno formale.
