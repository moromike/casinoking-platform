Status: ACTIVE
Last meaningful update: 2026-05-25

# CTO Review - WP-PLATFORM-REQUEST-ID-AND-STRUCTURED-LOGGING-MVP

Documento sorgente:
`docs/PLATFORM_APPLICATION_LOGGING_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md`

## 1. Verdetto CTO

**APPROVE WITH MANDATORY CORRECTIONS** prima di Parte B. Dipendenza hard su
WP1 (Error/Request Foundation MVP). Non implementare in parallelo a WP1.

L'analisi è corretta nella diagnosi (verificato in codice: `main.py` ha solo
un `logger.exception` nel timeout loop alle linee 67-68, nessun middleware
request-context, nessun helper structured). La sequenza L1→L2→L3→L4
(request context owned by WP1 → logger helper + redaction → exception/job
integration → read-only settings status) è la giusta.

Ma 5 correzioni obbligatorie e 3 raccomandate sotto.

## 2. Sintesi non-tecnica (per Michele)

Questo WP costruisce il sistema di log applicativi. Oggi se qualcosa fallisce
nel backend (un round non si chiude, un timeout di sweep), il log è una stringa
generica come "Access-session timeout sweep failed". Non si può cercare per
giocatore, per gioco, per richiesta. Il customer support non può ricostruire
cosa è successo a un singolo cliente.

Il WP introduce:

1. log strutturati (JSON con campi stabili, non stringhe);
2. un piccolo registro di "eventi" tipizzati (es. `system.unhandled_exception`,
   `access_session.auto_settlement_failed`);
3. redazione automatica di token, password, seed, JWT prima di scrivere il log;
4. integrazione con il `request_id` del WP1 (così ogni log è correlabile alla
   richiesta che lo ha generato).

Non implementa: log nel database (volutamente), telemetria frontend (esclusa),
log di request/response body (esclusa per privacy). MVP minimo per ottenere
osservabilità senza esporre dati sensibili.

Vincolo importante: non parte prima di WP1 perché senza `request_id` un log
strutturato resta non correlabile (più costoso e meno utile).

## 3. Cosa è solido nell'analisi

| Area | Verdetto CTO |
| --- | --- |
| Hard dep su WP1 dichiarata esplicitamente | Corretta. Logging senza request_id è prematuro. |
| Event registry MVP minimo (6 eventi) | Corretta - "do not add high-volume gameplay telemetry" è la regola giusta. |
| Lista redaction keys (`token`, `secret`, `password`, `server_seed`, `jwt`, `reset_token`, `launch_token`, etc.) | Corretta come baseline. Vedi 4.1 per pattern. |
| No DB-backed logs in MVP | Corretta - DB log è costoso e non MVP-appropriate. |
| No request/response body logging | Corretta - privacy + log spam risk. |
| No frontend telemetry MVP | Corretta - support_id è il ponte verso log backend. |
| Timeout sweeper come primo proof event | Corretta - è platform-owned e money-relevant. |
| Distinzione `access_logs.py` (DB audit login) vs application log | Corretta - sono due cose diverse, gergo confondibile. |
| Distinzione admin audit fingerprint vs application log | Corretta. |
| Identificazione URL/query string come sensibili (CMS v2 lab token in URL) | Corretta - rischio reale. |

## 4. Correzioni obbligatorie (Parte A deve risolverle)

### 4.1 Redaction policy: lista exact match insufficiente

Il brief elenca keys exact match (`authorization`, `token`, `jwt`, `secret`,
ecc.). Funziona per quei nomi precisi. Non funziona per:

- `bearer_token`, `auth_header`, `api_token`, `csrf_token` (custom names);
- field name camelCase in payload TypeScript (es. `authToken` non match
  `authorization`);
- nested key `{user: {credentials: {pwd: "..."}}}` (`pwd` non in list).

**Correzione richiesta:** policy a 2 livelli:

1. **Exact key list** (come da brief, baseline).
2. **Pattern matcher** su key name (case-insensitive):
   - suffix: `_token`, `_secret`, `_password`, `_pwd`, `_key`, `_seed`,
     `_credential`, `_authorization`
   - substring: contains `secret`, `password`, `token`, `seed`, `credential`,
     `authorization`, `bearer`
3. **Value heuristic** (low priority MVP, future): se valore matcha pattern
   JWT (`eyJ...`), base64 lungo > 40 char, treat as sensitive anche se key
   non è in lista.

Parte A deve produrre la lista finale + i pattern + i test che verificano
copertura sulle variant comuni.

### 4.2 Truncation / clamp size non quantificata

Il brief dice "Truncate long strings and nested payloads". Non quantifica.

**Correzione richiesta:** specificare:

- max string length per field: **256 chars** (con suffix `…[truncated]`);
- max nested depth: **3** (oltre, mostra `{...truncated...}`);
- max payload total bytes serialized: **8KB** (oltre, droppa `details` e logga
  warning `log.payload_truncated`).

Questi numeri sono proposta CTO; Parte A può counter-proporre con motivazione.

### 4.3 `log_event` signature da dichiarare

Il brief dice `log_event(event_name, level, details, ...)`. Manca specifica:

- come si attacca `request_id`? Auto da ContextVar di WP1, o esplicito
  parametro?
- `level` è string (`"info"`, `"warning"`, `"error"`, `"critical"`) o enum?
- `details` è dict serializzabile? Cosa succede se contiene un oggetto
  non-JSON-serializable (es. `datetime`, `Decimal`)?
- come si configura il sink (stdout JSON in MVP)?

**Correzione richiesta:** Parte A produce signature finale + esempio di
chiamata + comportamento per:
- non-serializable value (fallback `str()` + warning event);
- mancato `request_id` (fallback `"-"` + warning event);
- exception inside redaction (skip log, raise no error to caller).

### 4.4 `critical` senza pager: definire policy

Il brief marca `access_session.auto_settlement_failed` come `critical`. Bene
semantico. Ma il sink MVP è stdout JSON Docker. Nessun pager, nessuna alert.

**Correzione richiesta:** dichiarare esplicitamente:

- MVP: `critical` è solo etichetta per filtro/query log future. Non implica
  paging/alerting automatico.
- post-MVP: WP separato `WP-CRITICAL-EVENT-ALERTING` collegherà critical
  events a un sink alerting (PagerDuty/email/Slack). Non in MVP.

Senza questa chiarezza, qualcuno potrebbe presumere che `critical` faccia
qualcosa di operativo e tralasciare il monitoring umano.

### 4.5 Log sink decision esplicita

Il brief non specifica dove vanno fisicamente i log strutturati. Possibili:

- stdout (Docker collect);
- file rotante;
- syslog;
- CloudWatch/Loki/etc.

**Decisione CTO MVP:** **stdout JSON line-delimited**, raccolto da Docker.
Coerente con `infra/docker/docker-compose.yml`. Production sink (CloudWatch
o equivalent) in WP separato post-MVP.

Parte A conferma e dichiara.

## 5. Correzioni raccomandate

### 5.1 Event versioning policy

Quando si aggiunge un campo a evento esistente, è un breaking change per chi
ha alert/query salvate? Per MVP: append-only campi, no remove. Documentare.

### 5.2 Rate-limit log spam protection

Se un loop genera 1000 `system.unhandled_exception` al minuto, il sink stdout
si satura e i log utili si perdono. MVP può vivere senza, ma annotare:

- post-MVP: rate-limit per event_name + same error_code = max N/min, oltre
  emette `log.rate_limited` summary.

### 5.3 Frontend support_id correlation flow

Il brief dice "no frontend telemetry". Bene. Ma serve dichiarare il flow:

- player vede error → support_id visibile in dialog;
- player copia/screenshot e contatta support;
- support cerca per support_id in stdout JSON log;
- support trova event con tutti i campi e ricostruisce.

Questo flow va documentato nel `BACKOFFICE_MANUAL.md` o in un nuovo
`SUPPORT_OPERATIONS_GUIDE.md`. Brief può rimandare ma deve citarlo.

## 6. Rischi e blind spot identificati

| # | Rischio | Severità | Mitigazione proposta |
| --- | --- | --- | --- |
| R1 | Redaction list non cattura varianti (custom field name) | Alta | Pattern matcher (4.1) |
| R2 | Payload non-clampato satura sink | Media | Truncation policy (4.2) |
| R3 | `critical` event genera false expectation di alerting | Media | Policy esplicita (4.4) |
| R4 | Log sink ambiguo blocca produzione | Bassa | Decision MVP stdout (4.5) |
| R5 | Loop crash genera log spam | Bassa | Annotare per post-MVP (5.2) |
| R6 | Support workflow non documentato | Bassa | Cross-link doc (5.3) |
| R7 | `request_id` non disponibile in background tasks (asyncio.to_thread) | Media | ContextVar propagation strategy (verificare in 4.3) |

R7 è importante: `main.py:66` usa `asyncio.to_thread(timeout_expired_access_sessions)`.
Il `request_id` ContextVar di WP1 non si propaga automaticamente attraverso
thread boundaries. Per il timeout sweeper non c'è "request" (è background job),
quindi serve un `job_id` invece. Parte A deve chiarire:

- request-bound logs usano `request_id`;
- job-bound logs (sweeper) usano `job_id` (uuid generato all'inizio del job);
- evento `access_session.timeout_sweep_failed` ha `job_id`, non `request_id`.

## 7. Anti-pattern check vs Playbook + Memory

| Regola | Verdetto |
| --- | --- |
| Playbook Rule 25 - no hardcoded runtime/error copy | ✅ Log events non sono copy player. |
| Playbook anti-pattern "leaving upload constraints implicit" | ✅ Redaction policy esplicita. |
| Memory `feedback_clean_architecture_priority` | ✅ Logging è strutturato + tipizzato, no debito. |
| Memory `feedback_codex_chat_continuity` | ✅ Brief è snello. |
| Memory `feedback_michele_validation_style` | ⚠️ Logging non ha UI visibile. Validation Michele = customer support workflow funziona (5.3). Senza UI non c'è "vedo su localhost:3000". Manual gate: "verify backend log can be searched by request id". Sufficiente. |
| Memory `feedback_capability_matrix_rule` | ⚠️ Brief manca capability matrix. Aggiungere come per WP1. |

## 8. Dipendenze e sequencing

| Dipendenza | Stato | Risk |
| --- | --- | --- |
| `WP-ERROR-REQUEST-FOUNDATION-MVP` | hard dep (request_id, support_id, AppError, central handlers) | Se parte prima, l'integrazione `system.unhandled_exception` non ha AppError da catturare. |
| `WP-FINANCE-REPLAY-REGISTRY` | independent | OK parallelo |
| `WP-PLATFORM-SETTINGS-READONLY-INVENTORY` | independent in MVP | Slice S4 (Logging status row) può linkare a questo WP post-closure |

**Verdetto sequencing:** WP2 = SECONDO dopo WP1. Conferma packet.

## 9. Acceptance criteria - validazione

Brief test gates sono coperti. Aggiunte richieste:

| Gate aggiuntivo richiesto da CTO | Motivo |
| --- | --- |
| Test redaction su variant key name (`bearerToken`, `authHeader`) | 4.1 pattern matcher |
| Test truncation su string > 256 char | 4.2 clamp |
| Test `log_event` con non-serializable value | 4.3 fallback |
| Test sweep timeout job uses `job_id`, not `request_id` | R7 context |
| Test no `server_seed` raw in any logged event (negative test) | Security baseline |
| Manual gate: support workflow simulation (player vede support_id → support cerca log → trova evento) | 5.3 flow |

## 10. Stop-and-Ask aggiuntivi (oltre quelli del brief)

- se durante L3 si scopre che `access_session.auto_settlement_failed` richiede
  campi sensibili (es. wallet balance esatto in log per debug), Stop-and-Ask
  - regola: log payment-relevant amounts is OK, log wallet balance is NOT OK
    in MVP;
- se sink stdout va in conflitto con docker-compose log driver, Stop-and-Ask
  prima di cambiare driver;
- se Parte A scopre che `logger.exception` esistente in `main.py:67` non si
  può convertire a structured senza change semantics, Stop-and-Ask
  (probabilmente keep legacy line + emit structured event in parallelo per N
  giorni).

## 11. Domande aperte da chiudere con Product Owner (Michele)

Nessuna in MVP. Tutto è infrastruttura backend, no UI player/admin visibile.
Eccezione: se WP4 (Settings) decidesse di mostrare "log retention policy"
visibile a operatore, allora Michele decide la durata (60/90/180 giorni).
Per ora retention = `documented placeholder`, no deletion job.

## 12. Raccomandazione finale per Codex (prompt readiness)

WP è **pronto per Parte A** dopo merge di WP1.

Prompt structure consigliato:

```
You are CTO assistant. Parte A: validate approach, counter-propose if gap.
Parte B: execution starts only after CTO approval AND WP1 already merged.

Read:
- docs/PLATFORM_APPLICATION_LOGGING_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md
- docs/PLATFORM_APPLICATION_LOGGING_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md (this)
- docs/PLATFORM_APPLICATION_LOGGING_PLAN_2026-05-24.md
- WP1 merged state on main

Mandatory in Parte A output:
1. Capability matrix
2. Redaction policy v2 (exact list + pattern matcher) + test plan (CTO review 4.1)
3. Truncation/clamp numbers + test (CTO review 4.2)
4. `log_event` final signature spec (CTO review 4.3)
5. `critical` level policy declaration (no auto-paging MVP) (CTO review 4.4)
6. Log sink decision (stdout JSON) + docker-compose check (CTO review 4.5)
7. `job_id` vs `request_id` strategy for background tasks (CTO review R7)

Then proceed with Slice L2. Slice L1 is OWNED BY WP1 (already merged).
```

Stima effort: 8-14 prompts MVP, depending on redaction edge cases discovery.
