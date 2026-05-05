# CasinoKing - Demo Mode Plan - Fase 6

## Stato

Fase 6 chiusa.

- F6-A completata: migrazione, token anonimo demo, demo launch token e test contract.
- F6-B completata: demo wallet service con idempotenza, lock e test integration.
- F6-C completata: `DemoPlatformGameClient`, branching router Mines su `mode=demo`, round demo end-to-end e regressione real-mode mirata.
- F6-D completata: frontend demo con `anonymous_token`, game launch token demo, badge/saldo chip e reset sessione demo.
- F6-E completata: suite demo mirata verde e documentazione riallineata. Il polish finale e' nel commit `150f2fc`.

## Fonti lette per aprire il cantiere

File effettivamente letti:

- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/README.md`
- `docs/ARCHITECTURE_ATLAS_MINES.md`
- `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`
- `docs/THEME_SYSTEM_PLAN.md`
- Roadmap v3 esterna: `C:\Users\michelem.INSIDE\.claude\plans\dunque-parliamo-di-gioco-snuggly-badger.md`
- `backend/app/modules/platform/game_launch/service.py`
- `backend/app/api/routes/mines.py`
- `backend/app/modules/games/mines/platform_client.py`
- `frontend/app/ui/mines/mines-standalone.tsx` (prime 120 righe)

File individuati ma non letti integralmente:

- `backend/app/modules/games/mines/service.py` — engine agnostico; F6 non lo modifica
- `backend/app/modules/platform/rounds/service.py` — real rounds; F6 non li tocca
- `backend/app/modules/platform/table_sessions/service.py` — real sessions; F6 non le tocca
- documenti Word canonici in `docs/word/`

Motivo: Fase 6 riguarda un wallet sandbox parallelo al ledger reale. Non cambia
matematica, RNG, fairness, wallet reale o ledger.

## Obiettivo

Rendere ogni Title giocabile in `mode=demo` da browser anonimo, senza login,
senza scrivere su `platform_rounds` o `ledger_transactions`. La sessione demo
parte da 100 chip; esaurendo i chip la sessione si chiude; una nuova sessione
ricomincia da 100.

## Non-obiettivi (prima slice F6)

- Demo da utente loggato (schema lo supporta via `user_id` NULL; implementazione in fase successiva).
- Rinnovabilita' intra-sessione (chip esauriti = nuova sessione; nessuna ricarica intra-sessione).
- Preview iframe/modal.
- Nuovi giochi oltre a Mines.
- Cambio gameplay, matematica, RTP, RNG, fairness, wallet reale, ledger.

## Regole non negoziabili

1. **Zero scritture su `platform_rounds` e `ledger_transactions` in demo.** Mai.
2. **Server-authoritative:** il frontend non decide outcome; l'engine Mines resta identico.
3. **Idempotenza:** ogni debit/credit demo porta un `idempotency_key`; stessa key = stesso effetto.
4. **Transazione DB atomica** per debit-bet e credit-win.
5. **Row-level lock (`SELECT … FOR UPDATE`)** sulla `demo_play_sessions` durante operazioni.
6. **`anonymous_token` firmato dal server:** il browser non genera identita', la riceve.
7. **Nessun login richiesto.**
8. **Rate limit soft** per `anonymous_token` su `open_demo_session` (anti-abuse, non blocking MVP).

## Design `anonymous_token`

### Flusso anonymous_token

1. Il browser chiama `POST /api/v1/demo/token` senza autenticazione.
2. Il server genera un UUID (`anonymous_id`), lo firma come JWT HS256 usando
   `settings.jwt_secret` (campo della classe `Settings` in
   `backend/app/core/config.py`, env var `JWT_SECRET`), TTL es. 30 giorni.
3. Payload JWT: `{ "sub": "<uuid>", "kind": "demo_anon", "iat": ..., "exp": ... }`.
4. Il server risponde con `{ "success": true, "data": { "anonymous_token": "<jwt>" } }`.
5. Il browser salva in `localStorage["ck_demo_anon_token"]`.

### Come il browser ottiene il game launch token demo

Il `anonymous_token` da solo non e' sufficiente per chiamare le API di gioco:
anche in demo il router Mines legge un `X-Game-Launch-Token` standard (stesso
header del flusso real). Il flusso completo per ottenere il game launch token
demo e':

1. Il browser ha un `anonymous_token` valido (preso o ricaricato da localStorage).
2. Il browser chiama `POST /api/v1/demo/launch` (nuovo endpoint, no auth) con
   `title_code` nel body e `X-Demo-Token: <anonymous_token>` nell'header.
3. Il server verifica la firma del `anonymous_token`, ne estrae `anonymous_id`
   (`sub`), e rilascia un game launch token JWT con
   `{ "title_code": ..., "mode": "demo", "anonymous_id": ..., "site_code": ... }`.
4. Il server risponde con `{ "success": true, "data": { "game_launch_token": "<jwt>" } }`.
5. Il browser usa `X-Game-Launch-Token: <jwt>` per tutte le chiamate di gioco
   (start, reveal, cashout) — identico al flusso real.

Questo separa le responsabilita':
- `anonymous_token`: identita' del browser, lunga durata (30 giorni).
- `game_launch_token`: token di sessione di lancio specifico per titolo+sessione,
  stessa struttura del flusso real, breve durata (es. 4 ore).

### Verifica server

Il server verifica la firma del game launch token a ogni richiesta di gioco
(identico al flusso real). Il router estrae `mode=demo` dal payload e inietta
`DemoPlatformGameClient`. Token non firmato o scaduto: 401, il client richiede
un nuovo game launch token da `POST /api/v1/demo/launch`.

### MVP stateless

Nessuna tabella `demo_tokens` in DB nella prima slice. Il server firma e
verifica; niente persistenza lato server. Aggiungere persistenza solo se
servono revoca o audit piu' solidi (backlog aperto).

## Schema dati proposto

### `backend/migrations/sql/0027__demo_sessions.sql`

```sql
CREATE TABLE demo_play_sessions (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    -- anonymous_id e' il campo 'sub' estratto e verificato dal anonymous_token JWT.
    -- Non salviamo il JWT grezzo: salviamo solo l'UUID firmato dal server.
    anonymous_id          UUID         NOT NULL,
    -- user_id e' NULL nell'MVP (demo anonima); usato in futuro per demo da utente loggato.
    user_id               UUID         NULL REFERENCES users(id),
    title_code            VARCHAR(64)  NOT NULL REFERENCES game_titles(title_code),
    balance_chips         NUMERIC(18, 6) NOT NULL,
    starting_balance_chips NUMERIC(18, 6) NOT NULL DEFAULT 100,
    opened_at             TIMESTAMPTZ  NOT NULL DEFAULT now(),
    closed_at             TIMESTAMPTZ  NULL,
    status                VARCHAR(16)  NOT NULL DEFAULT 'active'
    -- status: 'active' | 'exhausted' | 'closed'
    -- CHECK: (anonymous_id IS NOT NULL AND user_id IS NULL)
    --     OR (anonymous_id IS NULL AND user_id IS NOT NULL)
    -- opzionale in MVP; aggiungere se si decide di supportare entrambi i path
);

CREATE INDEX idx_demo_play_sessions_anon_status
    ON demo_play_sessions (anonymous_id, status);

CREATE TABLE demo_round_events (
    id                    UUID         PRIMARY KEY DEFAULT gen_random_uuid(),
    demo_play_session_id  UUID         NOT NULL REFERENCES demo_play_sessions(id),
    kind                  VARCHAR(16)  NOT NULL,
    -- kind: 'bet' | 'win' | 'cashout' | 'reveal_safe' | 'mine_hit'
    amount                NUMERIC(18, 6) NOT NULL,
    idempotency_key       VARCHAR(128) NOT NULL,
    payload_json          JSONB        NULL,
    created_at            TIMESTAMPTZ  NOT NULL DEFAULT now()
);

CREATE UNIQUE INDEX idx_demo_round_events_idempotency
    ON demo_round_events (demo_play_session_id, idempotency_key);
```

Note: `anonymous_id` e' il `sub` UUID estratto dal JWT gia' verificato server-side
prima di qualsiasi scrittura in DB. Il JWT grezzo non viene mai persistito.
`user_id NULL` e' intenzionale nell'MVP; la FK `REFERENCES users(id)` e' gia'
nello schema per supportare demo da utente loggato senza migrazione futura.

Implementazione F6-A/B/C: oltre alle due tabelle sopra, la migrazione crea
`demo_mines_game_rounds`. Motivo: `mines_game_rounds.platform_round_id` e'
`NOT NULL REFERENCES platform_rounds(id)` nel modello real; usare la stessa
tabella avrebbe obbligato una scrittura su `platform_rounds`, vietata dal piano.
La tabella demo contiene solo stato tecnico Mines demo e mantiene separazione
fisica da ledger/platform rounds.

## API candidate

### Pubblica (no auth)

| Metodo | Path | Descrizione |
| --- | --- | --- |
| `POST` | `/api/v1/demo/token` | Emette un `anonymous_token` firmato dal server. |
| `POST` | `/api/v1/demo/launch` | Verifica `X-Demo-Token` ed emette un `game_launch_token` con `mode=demo` per il `title_code` richiesto. |

### Gioco demo

**Stessi endpoint del gioco reale**, con branching interno su `mode` letto
dal `X-Game-Launch-Token`. Il frontend non cambia URL; cambia solo il launch
token che porta `mode=demo`. Il router Mines inietta `DemoPlatformGameClient`
al posto di `InProcessPlatformGameClient`.

```
POST /api/v1/mines/start     (X-Game-Launch-Token con mode=demo)
POST /api/v1/mines/reveal
POST /api/v1/mines/cashout
GET  /api/v1/mines/session/{id}
```

Non creare prefissi `/demo/games/...` separati: il branching e' interno al
router.

## Impatto backend

### `backend/app/modules/platform/game_launch/service.py`

Rimuovere le due rejection points per `mode=demo` introdotte in Fase 2:

- In `issue_game_launch_token`: rimuovere il blocco che lancia
  `GameLaunchTokenValidationError("Demo launch mode is not available until Phase 6")`.
- In `validate_game_launch_token`: rimuovere il blocco che lancia
  `GameLaunchTokenScopeError` per `mode=demo`.

Per `mode=demo`, il game launch token trasporta `anonymous_id` al posto di
`player_id`. Il token viene emesso da `POST /api/v1/demo/launch` (non dal
path real) dopo verifica del `anonymous_token`.

### `backend/app/api/routes/mines.py`

- Leggere `mode` dal launch token validato.
- Se `mode == "demo"`: estrarre `anonymous_id` dal game launch token (gia' verificato), iniettare `DemoPlatformGameClient` con `anonymous_id`.
- Se `mode == "real"`: flusso invariato, iniettare `InProcessPlatformGameClient`.
- L'engine `MinesService` non cambia signature: riceve sempre un `PlatformGameClient`.

### `backend/app/modules/games/mines/platform_client.py`

Aggiungere `DemoPlatformGameClient` che implementa il `PlatformGameClient`
Protocol esistente. Delega tutte le operazioni a `demo_wallet.service`:

- `open_round` → `demo_wallet.debit_for_bet` (scala il bet dalla sessione demo
  attiva; questa e' l'unica scrittura di addebito per la round)
- `settle_win` → `demo_wallet.credit_for_win` (accredita vincita = bet * multiplier)
- `settle_loss` → `demo_wallet.record_loss` (registra l'esito mine su
  `demo_round_events`, aggiorna status sessione se chip = 0; **nessun debit
  aggiuntivo**: il bet e' gia' stato scalato a `open_round`)
- Getter di snapshot leggono da `demo_play_sessions` / `demo_round_events`

Il flusso contabile e' simmetrico al real:
- real: `open_round` apre la round economica (il bet esce dal wallet al
  settlement, non all'apertura); `settle_win`/`settle_loss` chiudono.
- demo: `open_round` debita subito il chip-bet (wallet demo e' semplificato,
  senza escrow separato); `settle_win` riaccredita + vincita; `settle_loss`
  chiude senza ulteriori debiti.

Nessuna scrittura su `platform_rounds` o `ledger_transactions`.

### `backend/app/modules/platform/demo_wallet/service.py` (nuovo)

```
open_demo_session(anonymous_id, title_code) -> DemoPlaySession
get_active_session(anonymous_id, title_code) -> DemoPlaySession | None
debit_for_bet(session_id, amount, idempotency_key) -> DemoPlaySession
credit_for_win(session_id, amount, idempotency_key) -> DemoPlaySession
record_loss(session_id, idempotency_key) -> DemoPlaySession
```

`record_loss` registra l'evento mine su `demo_round_events`, imposta
`status='exhausted'` se `balance_chips == 0`, non modifica `balance_chips`
(gia' azzerato dal debit a `open_round`).

Tutte le operazioni mutanti: `BEGIN; SELECT ... FOR UPDATE; ...; COMMIT;`.
`debit_for_bet` rifiuta se `balance_chips < amount`.

### `backend/app/api/routes/demo.py` (nuovo)

```
POST /api/v1/demo/token
POST /api/v1/demo/launch
```

`POST /api/v1/demo/token`: firma JWT e ritorna `anonymous_token`. Rate limit
base (es. max 10 token per IP per minuto) come protezione abuse minima.

`POST /api/v1/demo/launch`: verifica firma del `anonymous_token` da
`X-Demo-Token`, estrae `anonymous_id` (`sub`), emette un game launch token
standard con `mode=demo`, `anonymous_id`, `title_code`, `site_code`. Valida
che il Title esista e sia active in `site_titles` (stessa logica del launch
real, senza validazione `player_id`).

### `backend/app/api/router.py`

Includere il nuovo `demo_router`.

## Impatto frontend

### `frontend/app/ui/mines/mines-standalone.tsx`

Il flusso `DemoAuthResponse` attuale (fake email + access_token) va rimosso
e sostituito con il flusso `anonymous_token`:

- Al primo lancio demo: chiamare `POST /api/v1/demo/token` se
  `localStorage["ck_demo_anon_token"]` non esiste.
- Opzionalmente, decodificare il JWT lato client (senza verifica crittografica)
  solo per leggere `exp` e rilevare la scadenza prima di fare una chiamata
  inutile al server. La validazione crittografica della firma avviene
  esclusivamente server-side; il client non deve fidarsi del payload decodificato.
- Chiamare `POST /api/v1/demo/launch` con `X-Demo-Token` per ottenere il
  `game_launch_token` demo.
- Usare `X-Game-Launch-Token` per tutte le chiamate di gioco (identico al real).
- Rimuovere la dipendenza dalla fake email demo.

### `frontend/app/ui/mines/mines-balance-footer.tsx`

- Badge "DEMO" visibile quando `mode == "demo"`.
- Saldo chip residuo mostrato al posto del saldo reale.
- Toast "Chip demo esauriti" + CTA "Ricomincia": il client chiama
  `POST /api/v1/demo/launch` (stesso endpoint del lancio iniziale) per
  ottenere un nuovo game launch token; il successivo `POST /api/v1/mines/start`
  apre automaticamente una nuova `demo_play_sessions` con 100 chip. Non esiste
  un endpoint `close_demo_session` separato: la sessione si chiude internamente
  quando `DemoPlatformGameClient.settle_loss` rileva `balance_chips == 0`.

### `frontend/app/lib/api.ts` / `frontend/app/lib/types.ts`

- Tipo `DemoToken`: `{ anonymous_token: string }`.
- Tipo `DemoPlaySession`: `{ id: string; balance_chips: number; status: string; ... }`.
- Funzioni: `issueDemoToken()`, `issueDemoLaunchToken(title_code)`, `getDemoSession(title_code)`.

## Strategia compatibilita' con modalita' real

- L'engine Mines (`service.py`) non sa nulla di demo vs real: riceve un `PlatformGameClient` dal router.
- Il router legge `mode` dal JWT del launch token e inietta il client corretto.
- Stessi path API; il frontend non distingue URL demo/real.
- `platform_rounds`, `ledger_transactions`, `game_table_sessions` non vengono mai scritti in demo.
- I test real non dipendono da tabelle demo e viceversa.
- Tokens legacy (senza `mode`) ricevono fallback `real`: nessuna rottura.

## Rischi e punti aperti

| Rischio | Note |
| --- | --- |
| Stato demo orfano | Se il browser perde il token, la sessione attiva diventa irraggiungibile. Impatto basso: si apre una nuova sessione da 100 chip. |
| Token condiviso tra dispositivi | Un utente puo' portare il token in un altro browser. Accettabile: nessun valore finanziario reale. |
| Rate limit IP aggirabile | Proxy possono mascherare l'IP; il rate limit per `anonymous_token` e' piu' preciso ma aggirabile con nuovi token. Soglia da tarare in produzione. |
| FK `game_titles` su `demo_play_sessions` | Richiede F1-F3 gia' completate (garantito: `game_titles` esiste con `mines_classic`). |
| Flusso `DemoAuthResponse` legacy | Il fake login demo va rimosso; verificare prima che non sia usato da altri path. |

**Punto aperto principale:** decidere se il `anonymous_token` va nel payload
del `X-Game-Launch-Token` (un solo header) o in un header separato `X-Demo-Token`.
Prima slice: header separato per semplicita'. Consolidamento possibile in F7.

## Sequenza implementazione a slice piccole

### Slice F6-A — Infrastruttura DB e token

1. [x] Creare `backend/migrations/sql/0027__demo_sessions.sql`.
2. [x] Creare `backend/app/api/routes/demo.py` con `POST /api/v1/demo/token` e
   `POST /api/v1/demo/launch`.
3. [x] Includere il router in `backend/app/api/router.py`.
4. [x] Test `tests/contract/test_demo_token_contract.py`: firma `anonymous_token`,
   struttura risposta, rate limit emissione, `demo/launch` emette game launch
   token con `mode=demo` e `anonymous_id` corretto.

### Slice F6-B — Demo wallet service

5. [x] Creare `backend/app/modules/platform/demo_wallet/__init__.py` e `service.py`.
6. [x] Test `tests/integration/test_demo_wallet.py`: open (via `anonymous_id`),
   debit a `open_round`, credit a `settle_win`, `record_loss` senza double-debit,
   saldo esaurito, idempotenza, lock concorrente.

### Slice F6-C — `DemoPlatformGameClient` + branching router

7. [x] Aggiungere `DemoPlatformGameClient` in `backend/app/modules/games/mines/platform_client.py`.
8. [x] Rimuovere le rejection points per `mode=demo` in `game_launch/service.py`.
9. [x] Aggiungere branching in `backend/app/api/routes/mines.py`.
10. [x] Test `tests/contract/test_mines_demo_contract.py`: start, reveal, cashout in demo; verifica zero scritture su `platform_rounds` e `ledger_transactions`.

### Slice F6-D — Frontend anonymous_token

11. [x] Refactoring `mines-standalone.tsx`: rimuovere `DemoAuthResponse` fake, aggiungere flusso `anonymous_token`.
12. [x] Badge DEMO e saldo chip in UI Mines standalone.
13. [x] Aggiornare tipi/API frontend necessari al flusso demo.
14. [x] TypeScript check: `npx tsc --noEmit`.

### Slice F6-E — Verifica integrata e documentazione

15. [x] Suite test demo mirata:
    ```powershell
    python -m pytest tests/contract/test_demo_token_contract.py tests/contract/test_mines_demo_contract.py tests/integration/test_demo_wallet.py
    ```
16. [x] Verifica comportamento demo: browser anonimo -> demo -> saldo 100 chip a nuovo ingresso -> niente flash di saldo precedente.
17. [x] Aggiornare `docs/SOURCE_OF_TRUTH.md` (sezione demo / ledger).
18. [x] Aggiornare `docs/ARCHITECTURE_ATLAS_MINES.md` (nuovi blocchi `MINES_DEMO_*`).
19. [x] Aggiornare questo documento con avanzamento.

## Test obbligatori

| Test | Tipo | Cosa verifica |
| --- | --- | --- |
| `test_demo_token_emits_signed_jwt` | contract | `POST /api/v1/demo/token` ritorna JWT verificabile |
| `test_demo_token_rejects_tampered_signature` | contract | token manomesso → 401 |
| `test_demo_wallet_open_gives_100_chips` | integration | nuova sessione = 100 chip |
| `test_demo_wallet_debit_atomicity` | integration | debit atomico con row-level lock |
| `test_demo_wallet_idempotency` | integration | stessa `idempotency_key` → un solo debit |
| `test_demo_wallet_exhausted_rejects_bet` | integration | saldo 0 → errore domain |
| `test_mines_demo_start_no_platform_rounds_write` | contract | start demo: `platform_rounds` invariato |
| `test_mines_demo_cashout_no_ledger_write` | contract | cashout demo: `ledger_transactions` invariato |
| `test_mines_demo_full_round` | contract | start → reveal → cashout in demo |
| `test_mines_real_unaffected_by_demo_tables` | regression | round real non intercetta `DemoPlatformGameClient` |

## Cosa NON fare in prima slice

- Non aggiungere preview iframe/modal.
- Non aggiungere demo da utente loggato (campo `user_id` lasciato NULL).
- Non aggiungere rinnovabilita' intra-sessione.
- Non creare path API separati `/demo/games/...`: il branching e' interno al router.
- Non persistere il token demo in DB (stateless JWT basta per l'MVP).
- Non modificare matematica, RTP, RNG, fairness, wallet reale, ledger.
- Non modificare schema di `platform_rounds`, `mines_game_rounds`, `ledger_transactions`.

## Criteri di accettazione F6

F6 e' accettabile se:

- browser anonimo lancia Mines in demo senza login
- `platform_rounds` e `ledger_transactions` restano invariati dopo una sessione demo completa
- la sessione demo parte da 100 chip, chip esauriti = sessione chiusa
- retry idempotente di un bet con stessa key → un solo debit
- il gioco reale non e' influenzato dalle tabelle demo
- TypeScript check e suite pytest verdi

## Documenti da aggiornare a chiusura F6

- `docs/SOURCE_OF_TRUTH.md`: aggiungere sezione che chiarisce demo NON e' ledger ma mantiene idempotenza/lock/transazionalita'.
- `docs/ARCHITECTURE_ATLAS_MINES.md`: aggiungere blocchi `MINES_DEMO_00900` (demo wallet), `MINES_DEMO_00910` (DemoPlatformGameClient), `MINES_API_00230` (launch token demo).
- `docs/DEMO_MODE_PLAN.md`: aggiornare avanzamento e verifiche a ogni slice.
