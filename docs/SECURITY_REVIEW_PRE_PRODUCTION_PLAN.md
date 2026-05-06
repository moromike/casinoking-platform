# CasinoKing - Security Review Pre-Production Plan

## Stato

Piano di revisione pre-produzione. Non e' richiesto per i prossimi refactor UX,
ma e' obbligatorio prima di un deploy reale.

## Obiettivo

Definire le aree minime da rivedere prima di produzione, con particolare
attenzione a auth, authorization, rate limit e idempotenza.

## Aree da rivedere

### Authn/Authz

- ruoli admin e permessi effettivi;
- separazione auth player/admin;
- access token lifecycle;
- revoca/logout;
- scadenza token;
- protezione endpoint admin.

### JWT e sessioni

- secret production;
- TTL;
- refresh strategy se introdotta;
- storage frontend;
- comportamento su token scaduto;
- game launch token e ownership.

### Endpoint sensibili

- admin finance;
- admin game config/publish;
- lobby publication;
- game launch;
- table sessions;
- Mines start/reveal/cashout.

### Rate limiting

- auth login/register;
- demo token;
- game launch;
- admin endpoints;
- fairness/session endpoints se necessario.

### Idempotenza

- idempotency key reuse cross-user;
- idempotency key reuse cross-action;
- collision handling;
- fingerprint request;
- test concorrenza dove serve.

### Input validation

- payload admin;
- title_code/site_code;
- asset upload;
- HTML rules;
- lobby metadata;
- numeric inputs.

### Data exposure

- error messages;
- logs;
- metadata_json audit;
- PII;
- wallet/ledger information.

## Accettazione

La review e' accettabile solo se:

- non ci sono endpoint admin non protetti;
- ruoli/permessi sono chiari;
- rate limit production-grade e' progettato;
- idempotenza e ownership sono verificati sugli endpoint sensibili;
- errori non espongono dati inutili;
- esiste una lista di fix bloccanti/non bloccanti.

## Relazione con altri piani

- `PRODUCTION_READINESS_BRIEF.md`: tracker macro production.
- documenti financial core: governano wallet/ledger/idempotenza.
- atlas platform/Mines: governano mappa endpoint e frontend.

## Fuori scope

- pentest completo;
- certificazione compliance;
- WAF/CDN vendor selection;
- hardening infrastrutturale avanzato.
