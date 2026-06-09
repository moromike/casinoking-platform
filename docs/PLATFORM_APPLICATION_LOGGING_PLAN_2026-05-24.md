Status: ACTIVE
Last meaningful update: 2026-05-24

# Platform Application Logging Plan

CTO approval required before implementation.

CTO review: `docs/PLATFORM_APPLICATION_LOGGING_CTO_REVIEW_2026-05-24.md`.

Current-state CTO review:
`docs/PLATFORM_APPLICATION_LOGGING_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`.

CTO status: architecture approved, implementation narrowed. This plan may
proceed only after the current-state audit and only for the MVP scope defined
below.

## 1. Problematica

CasinoKing oggi ha alcuni log applicativi, ma non ha ancora un sistema di
logging strutturato di piattaforma. Il backend usa `logging` Python in punti
isolati, ad esempio per il timeout sweeper, mentre molte failure passano da
eccezioni, response envelope o UI error dialog senza una traccia operativa
correlabile.

Il rischio non e' solo tecnico. In un prodotto casino, quando succede un errore
serve poter rispondere rapidamente a domande come:

- quale request ha fallito?
- quale utente, wallet, round, title o access session era coinvolto?
- l'errore ha impatto finanziario o solo UX?
- il retry e' stato automatico o manuale?
- c'e' un ledger transaction collegato?
- il problema e' singolo, ricorrente o sistemico?

Senza logging strutturato, la piattaforma dipende da messaggi testuali dispersi
e da query manuali su tabelle diverse. Questo non scala, e soprattutto non e'
un buon asset per supporto, debug, audit e produzione.

## 2. Principio di architettura

Non tutto cio' che "racconta cosa e' successo" deve finire nei log applicativi.
CasinoKing deve distinguere quattro livelli:

| Livello | Scopo | Persistenza primaria | Uso |
| --- | --- | --- | --- |
| Ledger | Contabilita' | `ledger_transactions`, `ledger_entries` | Fonte di verita' economica |
| Audit operativo | Mutazioni admin non finanziarie | `admin_audit_log` | Chi ha cambiato cosa |
| Replay/fairness | Ricostruzione round | tabelle gioco / payload replay | Spiegare outcome |
| Application logs | Debug/runtime operations | stdout JSON / log sink | Diagnosi tecnica |

Il logging applicativo deve essere:

- strutturato, preferibilmente JSON;
- correlabile con `request_id` / `correlation_id`;
- leggero sul path di gioco;
- privo di token, password e payload sensibili;
- campionato dove gli eventi sono rumorosi;
- separato da ledger e audit DB.

## 3. Direzione alto livello

Introdurre un layer di observability di piattaforma con:

1. middleware backend per generare o propagare `request_id`;
2. logging JSON standardizzato;
3. campi comuni per ogni evento;
4. categorie e livelli chiari;
5. policy di retention;
6. integrazione con error code registry;
7. gate per nuovi giochi e nuovi endpoint.

La direzione non e' "loggare tutto". La direzione e' loggare gli eventi giusti
con abbastanza contesto da poterli correlare senza appesantire il sistema.

## 3.1 Dipendenze CTO

Questo piano dipende da:

1. request/support id foundation;
2. error code registry MVP;
3. field redaction policy;
4. event-name registry minimo.

Non implementare logging strutturato prima di avere almeno request id e un
codice errore stabile per le eccezioni non gestite. Senza questi due elementi,
i log sarebbero tecnicamente piu' ordinati ma ancora poco correlabili.

## 4. Modello logico dei log

Ogni application log strutturato dovrebbe avere almeno:

| Campo | Descrizione |
| --- | --- |
| `timestamp` | ISO UTC |
| `level` | debug/info/warning/error/critical |
| `event_name` | Nome stabile, es. `access_session.timeout_sweep_failed` |
| `request_id` | Id request corrente, se presente |
| `correlation_id` | Id piu' ampio, opzionale |
| `error_code` | Codice errore piattaforma, se collegato |
| `actor_type` | player/admin/system |
| `actor_id` | id utente/admin o system job, se consentito |
| `game_code` | mines/boxe/hi_lo, se rilevante |
| `title_code` | title coinvolto, se rilevante |
| `platform_round_id` | round platform, se rilevante |
| `access_session_id` | sessione real-money, se rilevante |
| `ledger_transaction_id` | solo riferimento, non dump ledger |
| `message` | breve testo tecnico |
| `details` | oggetto piccolo, sanificato |

## 5. Categorie eventi

Categorie consigliate:

- `request`: request completata/fallita, solo se utile o in sampling;
- `auth`: token invalidi, refresh, demo provisioning, permission denied;
- `game_runtime`: start/pick/cashout/skip/retry lato backend;
- `access_session`: apertura, chiusura, timeout, auto-settlement;
- `ledger`: anomalie tecniche, idempotency conflict, reconciliation failure;
- `admin`: errori tecnici durante publish/upload/config;
- `system_job`: sweeper, reconciliation, retention job;
- `integration`: asset storage, DB, cache, eventuali servizi esterni;
- `security`: pattern sospetti, rate limit, accessi negati ripetuti.

## 6. Cosa non loggare

Vietato:

- token JWT o bearer token;
- password, reset token, session secret;
- server seed non rivelato;
- dati carta/pagamento reali se in futuro integrati;
- payload asset binari/base64;
- interi body request non sanificati;
- PII non necessaria;
- micro-eventi frontend ad alta frequenza.

Redaction policy MVP:

- chiavi contenenti `token`, `secret`, `password`, `authorization`, `jwt`,
  `server_seed`, `private_key` vengono sempre rimosse o sostituite con
  `[REDACTED]`;
- stringhe lunghe oltre la soglia configurata vengono troncate;
- oggetti annidati vengono sanificati ricorsivamente;
- dettagli non serializzabili vengono convertiti in descrizione breve;
- nessun payload request/response completo viene loggato di default.

Consentito:

- id tecnici;
- hash/short hash;
- importi e currency quando servono a correlare una transazione gia' presente
  nel ledger;
- error code e support id;
- riferimento a replay/audit payload, non dump completo.

## 7. Approccio a basso livello

### 7.1 Middleware request context

Backend FastAPI:

- legge `X-Request-ID` se presente;
- altrimenti genera un UUID;
- lo espone nella response header;
- lo salva in un context locale;
- lo passa agli error response.

CTO decision: in MVP `support_id` e `request_id` sono lo stesso valore. In
futuro si potra' introdurre un support id separato, ma oggi duplicare concetti
creerebbe solo confusione.

Frontend:

- conserva `request_id` ricevuto quando un'API fallisce;
- lo mostra come `support_id` o lo associa al codice errore;
- non genera id fittizi se il backend non lo ha confermato.

### 7.2 Logger helper

Introdurre un helper, ad esempio:

```text
log_event(
  event_name,
  level,
  actor,
  game_context,
  financial_refs,
  error_code,
  details,
)
```

Questo evita `logger.info("stringa libera")` sparsi. Il logger helper deve:

- applicare sanificazione;
- troncare payload lunghi;
- aggiungere request context automaticamente;
- imporre `event_name` stabile;
- impedire campi vietati.

Event-name registry MVP:

| Event name | Quando |
| --- | --- |
| `system.unhandled_exception` | Eccezione non gestita |
| `system.validation_error` | Request validation fallita |
| `access_session.timeout_sweep_failed` | Sweep timeout access session fallito |
| `access_session.auto_settlement_failed` | Auto-settlement non riuscito |
| `ledger.idempotency_conflict` | Idempotency conflict critico |
| `admin.audit_write_failed` | Scrittura audit operativo fallita |

I nuovi eventi devono essere aggiunti a un registro tipizzato, non inventati in
linea dentro i service.

### 7.3 Log levels

- `debug`: solo sviluppo locale o diagnostica temporanea.
- `info`: eventi operativi importanti ma attesi.
- `warning`: retry, timeout recuperato, config anomala non bloccante.
- `error`: failure non recuperata o azione utente fallita lato backend.
- `critical`: rischio contabile, settlement incerto, reconciliation failure.

### 7.4 Storage e retention

Per local/dev:

- stdout Docker e log container sono sufficienti.

Per produzione:

- stdout JSON verso log collector;
- retention parametrica;
- ricerca per `request_id`, `error_code`, `platform_round_id`,
  `ledger_transaction_id`;
- alert su pattern critici.

I log applicativi non devono essere la fonte primaria di audit legale. Se una
informazione deve sopravvivere per audit finanziario o ricostruzione round, deve
andare nel ledger, replay payload o audit table corretta.

Frontend/browser telemetry is explicitly out of MVP. Browser-side error
collection may be designed later, after backend request/error foundation is
stable.

## 7.5 Unexpected exception policy

Ogni eccezione non gestita deve:

- produrre log strutturato `system.unhandled_exception`;
- includere `request_id`, `error_code = CK.SYSTEM.INTERNAL_ERROR` e stack trace
  solo nel log interno;
- restituire al client un envelope generico con codice e support id;
- non esporre stack trace, SQL, path locali o dettagli infrastrutturali.

## 8. Gate implementativi

Prima di chiamare il logging "green":

- ogni response errore contiene `request_id`/`support_id`;
- ogni eccezione non gestita produce log strutturato;
- il timeout sweeper e i job system usano event names stabili;
- non ci sono token/secret nei log;
- test mirati verificano header `X-Request-ID`;
- documentata retention minima;
- Product/CTO approvano quali campi sono visibili a support/admin.

MVP approvato:

- FastAPI request id middleware;
- response header `X-Request-ID`;
- support id uguale al request id;
- logger helper strutturato;
- redaction helper;
- unexpected exception handler;
- timeout sweeper convertito a event name stabile;
- test su request id e redaction.

Fuori MVP:

- OpenTelemetry;
- log collector esterno;
- frontend telemetry;
- DB-backed application logs;
- logging completo di request/response;
- high-volume gameplay telemetry.

## 9. Effort stimato

Parte A dettagliata: 3-5 prompt.

Parte B MVP:

- middleware + logger helper: 4-7 prompt;
- error integration: dipende dal piano error registry;
- smoke/log tests: 2-4 prompt.

Totale MVP logging: 6-11 prompt, esclusi log sink production-grade.

## 10. Stop-and-Ask

Fermarsi prima di implementare se:

- si vuole scrivere application log in DB invece che stdout/log sink;
- emerge necessita' di loggare payload sensibili;
- si propone di usare i log applicativi come fonte di verita' finanziaria;
- si vuole attivare logging request/response completo;
- serve decidere retention legale.
