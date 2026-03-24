# CasinoKing – Documento 11 v2

API Contract dettagliato – allineato al modello finanziario v3

Scopo del documento
Definire il contratto API applicativo di CasinoKing in modo coerente con il modello wallet/ledger v3. Questa versione chiarisce auth, ruoli, idempotenza, error handling, ownership, riferimenti contabili e comportamento degli endpoint che impattano saldo, ledger e sessioni di gioco.

## 1. Cosa cambia rispetto alla v1

- Allineamento esplicito con wallet snapshot materializzato + ledger come fonte primaria contabile.
- Allineamento con il piano dei conti (ledger_accounts) e con il modello double-entry.
- Idempotenza formalizzata per endpoint sensibili.
- Comportamento di errore e retry reso più preciso.
- Riferimenti finanziari e di sessione inseriti nel contratto API.

## 2. Convenzioni API generali

- Base path suggerito: /api/v1
- JSON come formato standard request/response
- Tutti gli endpoint autenticati richiedono bearer token salvo eccezioni pubbliche
- Timestamps in ISO 8601 UTC
- ID principali in UUID
- Le operazioni che muovono denaro/chip o chiudono stati usano idempotency semantics dove previsto

## 3. Envelope standard di risposta

Success
{
"success": true,
"data": { ... },
"meta": { ...optional... }
}

Errore
{
"success": false,
"error": {
"code": "INSUFFICIENT_BALANCE",
"message": "Not enough available balance",
"details": { ...optional... }
}
}

## 4. Autenticazione e ruoli

| Ruolo | Accesso | Esempi |
| --- | --- | --- |
| Guest | pubblico limitato | health, site access, register, login |
| Player | owner-only | wallet, own sessions, own mines actions |
| Admin | amministrativo | bonus, adjustments, user management, reporting |

## 5. Header standard

Authorization: Bearer <token>
Content-Type: application/json
Idempotency-Key: <required on sensitive POST endpoints>
X-Request-Id: <optional but recommended>

## 6. Idempotenza – regola definitiva

- Obbligatoria su start game, cashout, admin credit/bonus/adjustment, signup credit interno, bonus grant.
- Fortemente consigliata su tutti i POST che producono side-effect non idempotenti.
- La stessa Idempotency-Key sullo stesso endpoint e stesso attore deve restituire lo stesso risultato logico o uno stato equivalente.
- Se payload e chiave non coincidono con la richiesta originale, il sistema deve rispondere con conflitto o errore esplicito.

## 7. Error codes principali

| Code | HTTP | Uso |
| --- | --- | --- |
| UNAUTHORIZED | 401 | token mancante/non valido |
| FORBIDDEN | 403 | ruolo o ownership non validi |
| VALIDATION_ERROR | 422 | payload non valido |
| INSUFFICIENT_BALANCE | 409 | fondi insufficienti |
| GAME_STATE_CONFLICT | 409 | stato sessione incompatibile |
| IDEMPOTENCY_CONFLICT | 409 | chiave riusata con payload incompatibile |
| RESOURCE_NOT_FOUND | 404 | risorsa inesistente |
| CONCURRENCY_CONFLICT | 409 | lock/state changed |
| INTERNAL_ERROR | 500 | errore inatteso |

## 8. Endpoint pubblici / auth

| Metodo | Endpoint | Uso | Note |
| --- | --- | --- | --- |
| POST | /api/v1/site/access | verifica password globale sito | fase MVP |
| POST | /api/v1/auth/register | registrazione utente | crea user + wallet + credito iniziale |
| POST | /api/v1/auth/login | login | token response |
| POST | /api/v1/auth/password/forgot | reset password start | email flow |
| POST | /api/v1/auth/password/reset | reset password complete | token based |
| GET | /api/v1/health/live | liveness | pubblico |
| GET | /api/v1/health/ready | readiness | infra/devops |

## 9. Contract specifico – register

POST /api/v1/auth/register
Request:
{
"email": "player@example.com",
"password": "********",
"site_access_password": "********"
}

Response:
{
"success": true,
"data": {
"user_id": "uuid",
"wallets": [
{"wallet_type": "cash", "currency_code": "CHIP", "balance_snapshot": "1000.000000"},
{"wallet_type": "bonus", "currency_code": "CHIP", "balance_snapshot": "0.000000"}
],
"bootstrap_transaction_id": "uuid"
}
}

- Il credito iniziale è un effetto di business interno e deve produrre ledger_transaction + ledger_entries coerenti.
- La response può esporre l'id della bootstrap transaction per audit/debug interno, non necessariamente in UI finale.

## 10. Wallet endpoints

| Metodo | Endpoint | Uso | Note |
| --- | --- | --- | --- |
| GET | /api/v1/wallets | lista wallet utente | owner only |
| GET | /api/v1/wallets/{wallet_type} | saldo e metadati | cash/bonus |
| GET | /api/v1/ledger/transactions | storico transazioni | owner/admin |
| GET | /api/v1/ledger/transactions/{id} | dettaglio transazione | owner/admin |

## 11. Wallet response model

{
"success": true,
"data": [
{
"wallet_type": "cash",
"currency_code": "CHIP",
"balance_snapshot": "875.340000",
"status": "active",
"ledger_account_code": "PLAYER_CASH_<user>"
},
{
"wallet_type": "bonus",
"currency_code": "CHIP",
"balance_snapshot": "20.000000",
"status": "active",
"ledger_account_code": "PLAYER_BONUS_<user>"
}
]
}

## 12. Mines endpoints

| Metodo | Endpoint | Idempotency | Uso | Note |
| --- | --- | --- | --- | --- |
| POST | /api/v1/games/mines/start | Required | avvia partita | crea sessione + bet |
| POST | /api/v1/games/mines/reveal | Optional/Conditional | apre cella | stateful action |
| POST | /api/v1/games/mines/cashout | Required | chiude in win | financially sensitive |
| GET | /api/v1/games/mines/session/{id} | No | recupera stato | owner/admin |
| GET | /api/v1/games/mines/config | No | config e limiti | pubblico o player |

## 13. Contract specifico – start game

POST /api/v1/games/mines/start
Headers:
Idempotency-Key: 6f7d...

Request:
{
"grid_size": 25,
"mine_count": 3,
"bet_amount": "10.000000",
"wallet_type": "cash"
}

Response:
{
"success": true,
"data": {
"game_session_id": "uuid",
"status": "active",
"grid_size": 25,
"mine_count": 3,
"bet_amount": "10.000000",
"safe_reveals_count": 0,
"multiplier_current": "1.0000",
"wallet_balance_after": "990.000000",
"ledger_transaction_id": "uuid"
}
}

- La richiesta produce side-effects finanziari: richiede Idempotency-Key.
- Il backend deve lockare i record necessari e fallire in modo controllato in caso di conflitto/concorrenza.
- La response può includere ledger_transaction_id per audit e debugging, soprattutto in ambienti non finali.

## 14. Contract specifico – reveal

POST /api/v1/games/mines/reveal
Request:
{
"game_session_id": "uuid",
"cell_index": 7
}

Response safe:
{
"success": true,
"data": {
"game_session_id": "uuid",
"status": "active",
"result": "safe",
"safe_reveals_count": 1,
"multiplier_current": "1.1136",
"potential_payout": "11.136000"
}
}

Response mine:
{
"success": true,
"data": {
"game_session_id": "uuid",
"status": "lost",
"result": "mine",
"safe_reveals_count": 0
}
}

- Reveal non crea sempre movimento ledger: se safe, aggiorna solo stato di gioco.
- Se la sessione è già chiusa, deve rispondere con GAME_STATE_CONFLICT.
- Ownership e stato active devono essere verificati sempre lato server.

## 15. Contract specifico – cashout

POST /api/v1/games/mines/cashout
Headers:
Idempotency-Key: c4a1...

Request:
{
"game_session_id": "uuid"
}

Response:
{
"success": true,
"data": {
"game_session_id": "uuid",
"status": "won",
"payout_amount": "11.136000",
"wallet_balance_after": "1001.136000",
"ledger_transaction_id": "uuid"
}
}

- Cashout è endpoint finanziario critico: idempotenza obbligatoria.
- Se due cashout arrivano quasi insieme, uno solo deve produrre la vincita; l'altro deve ricevere risultato coerente o conflitto controllato.
- La chiusura sessione e il posting ledger devono stare nello stesso commit.

## 16. Admin endpoints sensibili

| Metodo | Endpoint | Idempotency | Uso | Financial impact |
| --- | --- | --- | --- | --- |
| POST | /api/v1/admin/users/{id}/bonus-grants | Required | assegna bonus | Yes |
| POST | /api/v1/admin/users/{id}/adjustments | Required | credit/debit manuale | Yes |
| POST | /api/v1/admin/users/{id}/suspend | Optional | sospensione account | No |
| GET | /api/v1/admin/users | No | ricerca utenti | No |
| GET | /api/v1/admin/reports/ledger | No | report contabili | No |

## 17. Contract specifico – admin adjustment

POST /api/v1/admin/users/{id}/adjustments
Headers:
Idempotency-Key: 91ab...

Request:
{
"wallet_type": "bonus",
"direction": "credit",
"amount": "50.000000",
"reason": "manual_compensation"
}

Response:
{
"success": true,
"data": {
"target_user_id": "uuid",
"wallet_type": "bonus",
"direction": "credit",
"amount": "50.000000",
"wallet_balance_after": "70.000000",
"ledger_transaction_id": "uuid",
"admin_action_id": "uuid"
}
}

- Ogni adjustment deve creare sia admin_action sia ledger_transaction coerente.
- Non sono ammessi update manuali del saldo fuori dal modello contabile.

## 18. Ownership, authz e visibilità dati

- Player può vedere solo wallet, transazioni e sessioni proprie.
- Admin può vedere dati cross-user secondo policy di ruolo.
- Gli ID non bastano: ogni endpoint owner-only deve verificare ownership lato server.
- I dettagli contabili interni (es. house account code completi) possono essere esposti solo in API admin/debug, non necessariamente nelle API player finali.

## 19. Retry policy e conflitti

- Client può ritentare richieste idempotenti con stessa Idempotency-Key.
- Client non deve ritentare indiscriminatamente reveal/cashout senza leggere lo stato risultante.
- Conflitti di stato o concorrenza devono usare 409 con error code specifico.
- Gli endpoint GET devono permettere recovery state pulito dopo errori client/network.

## 20. Collegamento al modello finanziario v3

- Ogni response finanziaria rilevante deve poter essere ricondotta a ledger_transaction_id.
- wallet_balance_after e' uno snapshot operativo post-commit.
- Il ledger resta la fonte contabile primaria e deve poter riconciliare ogni side-effect API.
- Le API non devono mai consentire mutazioni fuori dal flusso wallet/ledger ufficiale.

## 21. Testing minimo del contratto API

- Start con stessa Idempotency-Key → stesso risultato logico.
- Cashout doppio simultaneo → una sola vincita.
- Adjustment admin senza idempotency key → rifiutato.
- Wallet balance_after coerente con ledger aggregate post-transaction.
- Reveal su sessione altrui → FORBIDDEN.

## 22. Decisioni prese

- Documento 11 allineato al modello wallet/ledger v3.
- Idempotenza trattata come requisito di contratto, non solo implementativo.
- Risposte finanziarie collegate a ledger_transaction_id.
- Admin adjustment e bonus formalizzati come eventi contabili veri.

## 23. Prossimo allineamento consigliato

- Allineare la futura implementazione FastAPI e i test contract/concurrency a questo documento senza deviazioni implicite.
