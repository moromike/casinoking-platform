Status: ACTIVE
Last meaningful update: 2026-05-24

# Platform Error Code Registry Plan

CTO approval required before implementation.

CTO review: `docs/PLATFORM_ERROR_CODE_REGISTRY_CTO_REVIEW_2026-05-24.md`.

Current-state CTO review:
`docs/PLATFORM_ERROR_CODE_REGISTRY_CURRENT_STATE_CTO_REVIEW_2026-05-24.md`.

CTO status: approved as first implementation foundation after current-state
audit. Implement incrementally; do not migrate all backend routes in one pass.

## 1. Problematica

CasinoKing ha gia' un envelope API con `error.code` e `error.message`, e il
frontend ha adapter come `GameActionError` / `buildGameErrorMessage`. Pero' il
contratto non e' ancora universale:

- alcune route possono restituire `HTTPException(detail=...)`;
- non ogni errore visibile mostra un codice;
- la UI spesso mappa errori a copy utente senza esporre support id/codice;
- i codici non sono catalogati in un registro consultabile;
- non e' chiaro quali errori sono retryable, auditabili o critici;
- admin e player non hanno una matrice unica.

Il risultato e' che quando Michele vede un errore in gioco, il messaggio e'
leggibile ma non sempre diagnosticabile. Per support e produzione serve sempre
un codice stabile.

## 2. Principio di architettura

Ogni errore attraversa questa pipeline:

```text
Exception / validation failure
  -> AppError typed
  -> API error envelope
  -> frontend ApiRequestError
  -> localized UI copy + visible code/support id
  -> structured application log
```

La copy utente non e' il codice errore. Il codice errore non e' tradotto. Il
backend non deve esporre stringhe tecniche grezze come messaggio player.

## 3. Direzione alto livello

Creare un registro errori di piattaforma con:

1. codici stabili namespaced;
2. mapping HTTP status;
3. severita';
4. retryability;
5. visibilita' player/admin;
6. copy key frontend;
7. log level;
8. eventuale audit requirement;
9. runbook/action suggerita;
10. backoffice read-only matrix.

## 4. Formato codice

Formato consigliato:

```text
CK.<DOMAIN>.<ERROR_NAME>
```

Esempi:

```text
CK.AUTH.INVALID_TOKEN
CK.AUTH.SESSION_EXPIRED
CK.WALLET.INSUFFICIENT_BALANCE
CK.LEDGER.IDEMPOTENCY_CONFLICT
CK.GAME.ROUND_CLOSED
CK.MINES.INVALID_CELL
CK.BOXE.INVALID_PICK
CK.HILO.SKIP_LIMIT_REACHED
CK.ADMIN.CONFIG_VALIDATION_FAILED
CK.SYSTEM.SERVICE_UNAVAILABLE
```

Regole:

- mai riusare un codice per significato diverso;
- mai tradurre il codice;
- deprecare, non cancellare, i codici pubblicati;
- i codici tecnici interni possono essere piu' granulari della copy utente.

Namespace CTO:

- `CK.AUTH.*` per autenticazione/sessione;
- `CK.WALLET.*` per saldo/wallet/table balance;
- `CK.LEDGER.*` per idempotenza/contabilita';
- `CK.ADMIN.*` per backoffice;
- `CK.SYSTEM.*` per infrastruttura/unexpected;
- `CK.MINES.*`, `CK.BOXE.*`, `CK.HILO.*` per errori game-specific.

Durante la migrazione, i vecchi codici brevi (`INSUFFICIENT_BALANCE`,
`ROUND_CLOSED`, ecc.) restano supportati dal frontend classifier, ma i nuovi
endpoint e i nuovi errori devono emettere codici `CK.*`.

## 5. Error envelope target

Risposta target:

```json
{
  "success": false,
  "error": {
    "code": "CK.HILO.ROUND_CLOSED",
    "message": "La mano e' gia' conclusa.",
    "support_id": "req_01J..."
  }
}
```

Campi opzionali:

```json
{
  "details": {
    "field": "bet_amount",
    "retryable": false
  }
}
```

`details` non deve contenere segreti o stack trace.

MVP response contract:

```json
{
  "success": false,
  "error": {
    "code": "CK.SYSTEM.INTERNAL_ERROR",
    "message": "Servizio temporaneamente non disponibile.",
    "support_id": "req_..."
  }
}
```

`support_id` e' obbligatorio per errori backend. In MVP coincide con
`request_id`.

## 6. UI player/admin

Player:

```text
La mano e' gia' conclusa.
Codice: CK.HILO.ROUND_CLOSED
```

Admin/support:

```text
CK.HILO.ROUND_CLOSED · req_01J...
Round already terminal during prediction retry.
```

La UI deve sempre:

- mostrare codice errore;
- mostrare azione possibile, se esiste;
- non mostrare stack trace;
- non mostrare backend detail grezzo;
- localizzare il messaggio, non il codice.

Display CTO:

- player UI mostra il codice in riga secondaria compatta;
- admin/support UI puo' mostrare anche support id e dettagli sanificati;
- il codice non deve dominare il messaggio utente;
- il pulsante retry/dismiss resta guidato da `retryable`.

## 7. Registro errori

Schema logico:

| Campo | Descrizione |
| --- | --- |
| `code` | Codice stabile |
| `domain` | auth/wallet/ledger/game/admin/system |
| `http_status` | status API |
| `default_message_key` | chiave i18n |
| `player_visible` | boolean |
| `admin_visible` | boolean |
| `retryable` | boolean |
| `log_level` | warning/error/critical |
| `audit_required` | none/admin/financial/security |
| `support_action` | testo/runbook breve |
| `deprecated` | boolean |

In MVP puo' essere file codice typed. In fase successiva puo' essere esposto in
backoffice come matrice read-only o configurabile solo per copy/action.

Source of truth CTO:

- MVP: modulo backend typed, versionato nel codice;
- frontend riceve codici dall'API e usa mapping i18n/copy;
- backoffice Error Matrix legge il registry, ma non lo modifica;
- DB registry non approvato finche' non emerge una necessita' product reale.

## 8. Approccio a basso livello

### 8.1 Backend AppError

Introdurre una classe o dataclass:

```text
AppError(code, status_code, message_key, details, cause)
```

Le route non dovrebbero costruire `HTTPException(detail="...")` a mano per casi
applicativi. Devono lanciare o convertire in `AppError`.

`AppError` deve includere:

- `code`;
- `status_code`;
- `message`;
- `public_message_key` o messaggio pubblico gia' risolto lato backend;
- `details` sanificati;
- `retryable`;
- `log_level`.

### 8.2 Exception handlers FastAPI

Handler centralizzati:

- `AppError` -> envelope;
- validation error -> `CK.VALIDATION.INVALID_REQUEST`;
- auth error -> codici `CK.AUTH.*`;
- unexpected exception -> `CK.SYSTEM.INTERNAL_ERROR` con support id.

Validation errors:

- possono mantenere dettagli campo/locazione se non sensibili;
- non devono esporre stack trace;
- devono usare un codice stabile;
- frontend puo' mostrare messaggio breve e codice.

### 8.3 Frontend ApiRequestError

Estendere `ApiRequestError` con:

- `code`;
- `status`;
- `supportId`;
- `details`;
- `retryable`, se fornito.

Game runtime e admin UI ricevono sempre lo stesso oggetto.

Backward compatibility:

- `ApiRequestError` deve continuare a funzionare con envelope vecchio;
- i game error adapter devono riconoscere sia codici `CK.*` sia vecchi codici
  finche' la migrazione non e' completa;
- ogni nuovo codice deve avere copy in tutte le locale supportate dal gioco o
  dalla piattaforma.

### 8.4 GameActionError

`GameActionError` deve accettare:

- message localizzato;
- code visibile;
- support id;
- retry action;
- dismiss action.

Ogni gioco passa copy localizzata ma non rimuove il codice.

## 9. Error matrix backoffice

La matrice errori appartiene al Platform Settings Control Center, ma il registry
e' la fonte dati.

Vista minima:

- code;
- domain;
- HTTP status;
- player/admin visibility;
- retryable;
- log level;
- support action;
- last seen count se in futuro si collega ai log.

MVP consigliato: read-only. Editare error semantics live e' rischioso.

## 10. Gate implementativi

- Nessun `HTTPException(detail="stringa grezza")` per errori applicativi nuovi.
- Ogni errore visibile mostra codice.
- Ogni codice e' nel registry.
- Ogni codice ha copy in tutte le locale supportate.
- Unexpected exception non espone stack trace.
- Application log include `error_code` e `request_id`.
- Test API verifica envelope.
- Test UI verifica codice visibile.

MVP approvato:

- current-state audit degli errori;
- error registry backend typed;
- `AppError`;
- request/support id nel response envelope;
- handlers per `AppError`, validation, unexpected exception;
- `ApiRequestError` esteso;
- `GameActionError` mostra codice/support id;
- migrazione di 1-2 domini iniziali.

Primi domini consigliati:

1. auth/session/game launch;
2. wallet/table balance;
3. HI-LO runtime action errors.

Fuori MVP:

- migrazione completa di tutte le route;
- DB-backed editable error registry;
- modifica semantica live dei codici;
- nascondere codici ai player.

## 11. Effort stimato

Parte A dettagliata: 3-5 prompt.

Parte B MVP:

- registry + AppError: 4-7 prompt;
- exception handlers: 3-5 prompt;
- frontend ApiRequestError/GameActionError: 3-6 prompt;
- backoffice matrix read-only: 3-5 prompt;
- migration route-by-route: variabile, 1-3 prompt per dominio.

Totale MVP iniziale: 13-23 prompt.

## 12. Stop-and-Ask

Fermarsi se:

- product vuole nascondere i codici ai player;
- si vuole rendere editabile il significato dei codici da backoffice;
- emergono errori che richiedono policy legale;
- route critiche non possono migrare senza cambiare contratti API;
- codice errore e copy utente vengono confusi.
