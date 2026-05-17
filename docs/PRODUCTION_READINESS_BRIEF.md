Status: ACTIVE
Last meaningful update: 2026-05-07

# CasinoKing - Production Readiness Brief

## Stato

Tracker pre-produzione. Non autorizza il deploy production.

## Obiettivo

Registrare il debito necessario prima di pubblicare CasinoKing in produzione.

Questo documento non blocca i prossimi cantieri UX, ma blocca qualsiasi
decisione "andiamo live".

## Principio

Il fatto che lo stack locale funzioni non significa che il prodotto sia pronto
per produzione.

## Checklist macro

### Migrations

- strategia migration esplicita;
- rollback/forward fix documentato;
- backup prima delle migration;
- smoke post-migration;
- gestione dati seed/config.

### Secrets e config

- niente secret production in `.env` locale;
- secret manager/vault;
- rotazione JWT secret;
- gestione per ambiente: local/staging/prod;
- CORS per domini reali.

### Security headers

- CORS ristretto;
- CSP;
- HSTS;
- secure cookies se si passera' a cookie auth;
- protezione base clickjacking.

### Rate limiting

- sostituire limit in-memory dove non scala;
- rate limit su auth;
- rate limit su demo token;
- rate limit su game launch;
- rate limit su endpoint admin sensibili.

### Observability

- log strutturati;
- correlation/request id;
- metriche base;
- alerting;
- healthcheck production-grade;
- error tracking.

### Database

- backup automatici;
- restore drill;
- retention;
- monitoring connessioni;
- slow query/logging;
- storage growth.

### Audit/log retention

- `admin_audit_log` non deve avere un hard cap di 500 righe in produzione;
- 500 puo' essere usato come batch size per pruning/archiviazione manutentiva;
- definire `ADMIN_AUDIT_LOG_RETENTION_DAYS` prima del go-live;
- definire `ADMIN_AUDIT_LOG_PAYLOAD_MAX_BYTES` se i payload audit iniziano a
  crescere;
- vietare PII/token/file payload nei log operativi;
- valutare archiviazione o backup prima di qualsiasi cancellazione automatica.

### Frontend delivery

- build immutable;
- cache policy;
- asset strategy;
- error boundary;
- smoke su mobile/desktop.

### Operations

- runbook restart;
- runbook incident;
- ambiente staging;
- checklist release;
- ownership chiara.

## Fuori scope immediato

- Kubernetes;
- multi-region;
- compliance completa;
- external HTTP adapter Fase 9b/c;
- crypto wallet proprietario.

## Gating

Prima della produzione devono esistere almeno:

- `SECURITY_REVIEW_PRE_PRODUCTION_PLAN.md` validato;
- migration strategy;
- secret strategy;
- backup/restore strategy;
- observability minima;
- rate limiting production-grade sugli endpoint sensibili.
