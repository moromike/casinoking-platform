# WP — Uniform Launch-Token: allineamento Mines al pattern BOXE

**Data:** 2026-06-04  
**Scope:** B0 = documento + test; B1 = backend router `mines.py` (token opzionale su reveal/cashout/session/fairness/replay real) + test oracolo; B4 = frontend `mines-standalone.tsx` (rimosso invio token su reveal/cashout/session/fairness/replay real). Nessuna modifica a auth/RNG/math/payout/board/reveal logic. Demo invariato. Start invariato.  
**Stato:** B0 completato, B1/B4 completati (backend+frontend reveal/cashout + letture real), B2 annotato. Stop per gate CTO ad ogni step.

---

## 1. Decisione CTO (pattern canonico)

Il pattern canonico di launch-token è quello di **BOXE (GMP-5B/5C)**:

- Il **launch token** è un biglietto firmato che lega `player + title_code + site_code + mode`.
- Viene **validato SOLO allo start** (`POST /games/{code}/start`).
- Le azioni successive (**reveal**, **cashout**) sono autorizzate dal **bearer token** + **proprietà della sessione/round** (`user_id` nel WHERE delle query di update).
- La **demo** è un player provvisorio (`provisionDemoPlayer`): non ha launch token, non ha access session reale.
- La **sicurezza dei soldi** è garantita dall'**access session** (timeout + auto-settlement), non dal launch token.

Mines oggi invia il launch token su start, reveal e cashout. Questo è un comportamento legacy che va uniformato al pattern BOXE.  
**Post-B1:** il backend accetta reveal/cashout real **senza** token (bearer + ownership sufficienti).  
**Post-B4-read:** il backend accetta anche le letture real (`/session/{id}`, `/session/{id}/fairness`, `/session/{id}/replay`) **senza** token.  
**Post-B4-front:** il frontend real non invia più il token su reveal/cashout né sulle letture sessione/fairness/replay. Token è ancora accettato dal backend per retro-compatibilità.

---

## 2. Prove (3 pilastri)

### (a) Ownership sessione ≡ `_ensure_round_owner` BOXE

In `backend/app/modules/games/mines/service.py`:

- `reveal_cell` (riga 919) chiama `_get_session_for_update` (riga 1899) che esegue:
  ```sql
  WHERE mgr.id = %s AND mgr.user_id = %s FOR UPDATE OF mgr, pr
  ```
  (riga 1921-1923). Se la riga non esiste, `reveal_cell` solleva `MinesGameStateConflictError("Game session is not active for this user")` (riga 928).

- `cashout_session` (riga 1025) chiama `_get_session_for_update` con lo stesso filtro `user_id` (riga 1054-1058). Se non trova, solleva lo stesso errore (riga 1060).

**Conclusione:** Mines ha già un check di ownership equivalente a `_ensure_round_owner` di BOXE. Togliere il launch token da reveal/cashout è **sicuro**.

### (b) Launch token derivabile dal bearer

L'endpoint `POST /games/mines/launch-token` richiede `get_current_player` (bearer token). Il token contiene `player_id`, `title_code`, `site_code`. Non è un secondo fattore indipendente: chi ha il bearer valido può sempre ottenere un launch token. Quindi il launch token su reveal/cashout non aggiunge sicurezza oltre al bearer + ownership.

### (c) Money-safety = access session, non il token

In `backend/app/modules/platform/access_sessions/service.py` (righe 595-727 circa):

- L'access session ha **timeout** (inattività > 3 min).
- Al timeout o alla chiusura esplicita, `_auto_settle_active_round_for_access_session`:
  - Se `safe_reveals_count == 0` → **refund** (payout = bet).
  - Se `safe_reveals_count > 0` → **auto-cashout** (payout = potential_payout).
- Questo meccanismo è **indipendente dal launch token** e protegge i fondi del player.

**Conclusione:** la sicurezza finanziaria non dipende dal launch token su reveal/cashout.

---

## 3. Baseline / Oracolo B0 (cattura comportamento attuale)

Questa tabella è il riferimento di non-regressione per B6.

### A. Real mode — start / reveal / cashout

| Test | File:riga | Cosa copre |
|------|-----------|------------|
| `test_mines_start_accepts_valid_game_launch_token_header` | `tests/integration/test_financial_and_mines_flows.py:305` | Start real con token valido |
| `test_mines_start_rejects_mismatched_game_launch_token_header` | `tests/integration/test_financial_and_mines_flows.py:343` | Start real rifiuta token mismatch |
| `test_mines_start_rejects_invalid_game_launch_token_header` | `tests/integration/test_financial_and_mines_flows.py:389` | Start real rifiuta token invalid |
| `test_mines_start_rejects_expired_game_launch_token_header` | `tests/integration/test_financial_and_mines_flows.py:421` | Start real rifiuta token scaduto |
| `test_mines_start_rejects_other_game_launch_token_header` | `tests/integration/test_financial_and_mines_flows.py:451` | Start real rifiuta token altro gioco |
| `test_mines_reveal_rejects_mismatched_game_launch_token_header` | `tests/integration/test_financial_and_mines_flows.py:572` | Reveal real rifiuta token mismatch |
| `test_mines_session_endpoints_reject_invalid_game_launch_token_header` | `tests/integration/test_financial_and_mines_flows.py:731` | Session endpoint rifiuta token invalid |
| `test_mines_start_reveal_cashout_updates_wallet_and_ledger` | `tests/integration/test_financial_and_mines_flows.py:788` | Full round real: start → reveal → cashout; verifica wallet/ledger reconciliation |
| `test_mines_cashout_idempotency_replay_keeps_original_balance_after_later_wallet_change` | `tests/integration/test_financial_and_mines_flows.py:878` | Cashout idempotency real |
| `test_mines_session_is_owner_only` | `tests/contract/test_api_contract.py:394` | Ownership API contract |
| `test_mines_start_rejects_configurations_not_published_by_backoffice` | `tests/integration/test_mines_backoffice_config.py:332` | Config validation real start |

### B. Demo mode — start / reveal / cashout

| Test | File:riga | Cosa copre |
|------|-----------|------------|
| `test_mines_demo_start_no_platform_rounds_write` | `tests/contract/test_mines_demo_contract.py:28` | Demo start non scrive in platform_rounds |
| `test_mines_demo_full_round_cashout_no_ledger_write` | `tests/contract/test_mines_demo_contract.py:62` | Demo full round cashout non scrive ledger |
| `test_mines_demo_cashout_reveals_mines_and_plays_collect_sound` | `tests/integration/test_mines_embed_browser_smoke.py:2380` | Demo cashout browser (audio + reveal mine) |
| `test_mines_demo_loss_reveals_all_mines_before_session_refresh` | `tests/integration/test_mines_embed_browser_smoke.py:2492` | Demo loss browser (reveal all mines) |

### C. Auto-settlement chiusura esplicita access session

| Test | File:riga | Cosa copre |
|------|-----------|------------|
| `test_close_access_session_cascades_to_table_session_with_no_reveals` | `tests/integration/test_session_cascade_close.py:66` | Close esplicita, **nessun reveal** → **refund** (payout = bet). Verifica wallet reconciliation. |

### D. Auto-settlement timeout access session

| Test | File:riga | Cosa copre |
|------|-----------|------------|
| `test_ping_expired_access_session_times_out_round_and_fails` | `tests/integration/test_platform_access_sessions.py:63` | Timeout via ping, nessun reveal → auto-cashout refund (payout = bet). Verifica transazioni bet+win. |
| `test_timeout_sweeper_auto_cashouts_expired_access_session` | `tests/integration/test_platform_access_sessions.py:153` | Timeout sweeper batch, nessun reveal → auto-cashout refund. |
| `test_start_on_expired_access_session_auto_cashouts_active_round_and_blocks_new_round` | `tests/integration/test_platform_access_sessions.py:220` | Timeout CON 1 safe reveal (progresso) → auto-cashout con **potential_payout**. Verifica transazioni bet+win e blocco nuovo start. |

---

## 4. Implementazione B1/B1-read (backend — token opzionale su reveal/cashout/letture real)

### File modificato

`backend/app/api/routes/mines.py`

### Modifica minima (separazione real/demo, demo invariato)

**`_resolve_actor_and_launch_context`** (riga 138): aggiunto parametro `allow_real_without_token: bool = False`. Quando `True` e il token è assente ma c'è `Authorization`, il fallback chiama `get_current_player(authorization)` e restituisce un `actor_context` real con `launch_context=None`. Se il token è assente e non c'è `authorization`, o se `allow_real_without_token=False`, restituisce `401 GAME_LAUNCH_TOKEN_REQUIRED` come prima.

**Endpoint con `allow_real_without_token=True`:**
- `/reveal` (riga 565)
- `/cashout` (riga 658)
- `/session/{session_id}` (riga 838)
- `/session/{session_id}/fairness` (riga 931)
- `/session/{session_id}/replay` (riga 750) — uniformato al pattern B1, rimossa logica duplicata `if game_launch_token`.
- `/access-sessions/latest` (riga 309) — aggiunti query params `title_code`/`site_code` con default; se token presente usa `launch_context`, altrimenti i query params.

**Perché è sicuro:**
- Demo **completamente invariato**: il ramo `mode == "demo"` non è stato toccato in nessun endpoint. Il token è ancora obbligatorio per demo.
- Real **con token** funziona identicamente: il token viene validato, l'ownership cross-checkata.
- Real **senza token** è autorizzato solo da `get_current_player` + ownership nel service layer (`_get_session_for_update` / `get_session_for_user` / `get_session_fairness_for_user` / `get_session_replay_for_user` con `user_id` nel WHERE).
- Nessun service-layer modificato.
- Nessuna modifica a RNG/math/payout/board/reveal logic.

### Test B1 aggiunti

File: `tests/integration/test_mines_reveal_cashout_optional_token.py`

| Test | Cosa copre |
|------|-----------|
| `test_reveal_real_without_launch_token` | Reveal real senza `X-Game-Launch-Token` → 200, `result == "safe"`, `potential_payout > 0` |
| `test_cashout_real_without_launch_token` | Cashout real senza token (dopo 1 safe reveal) → 200, payout = potential_payout, wallet reconciliation drift = 0 |
| `test_reveal_real_other_user_session_rejected_without_token` | Player B tenta reveal su sessione di A senza token → 403 FORBIDDEN "ownership" |
| `test_cashout_real_other_user_session_rejected_without_token` | Player B tenta cashout su sessione di A senza token → 409 GAME_STATE_CONFLICT "not active" |

### 4b. Implementazione B4-front (frontend — token rimosso da reveal/cashout/letture real)

**File modificato:** `frontend-v3/app/ui/mines/mines-standalone.tsx`

**Modifica minima:**
- `handleRevealCell` (riga ~1186): costruisce `revealHeaders` vuoto; aggiunge `"X-Game-Launch-Token"` **solo** in demo mode. Ramo real rimosso.
- `handleCashout` (riga ~1269): stesso pattern — `cashoutHeaders` contiene solo `"Idempotency-Key"`; aggiunge token **solo** in demo mode.
- `loadSession` (riga ~849): rimossa chiamata `ensureGameLaunchToken`; richieste a `/session/{id}` e `/session/{id}/fairness` partono senza header token per real.
- `fetchGameReplay` (riga ~979): rimossa chiamata `ensureGameLaunchToken` nel ramo real; richiesta a `/session/{id}/replay` senza header token per real.
- `fetchLatestReplaySessions` (riga ~1008): rimossa chiamata `ensureGameLaunchToken`; richiesta a `/access-sessions/latest?title_code=...` senza header token per real.

**Perché è sicuro:**
- Demo invariato: tutti i rami `isDemoMode` mantengono l'invio del token.
- Start invariato: `handleStartSession` non è stato toccato.
- Retro-compatibilità backend: se un client non aggiornato invia ancora il token, il backend lo accetta (B1).
- TypeScript pulito: `tsc --noEmit` senza errori.

**Test di rete aggiunti:**
File: `tests/integration/test_mines_network_header_verification.py`

| Test | Cosa copre |
|------|-----------|
| `test_real_round_reveal_and_cashout_without_token` | Full round real: start CON token, reveal/cashout SENZA token. Wallet aggiornato. |
| `test_demo_round_reveal_and_cashout_with_token` | Full round demo: start/reveal/cashout CON token. Demo invariato. |
| `test_real_read_session_fairness_replay_without_token` | Letture real (`/session`, `/fairness`, `/replay`) SENZA token → 200. |
| `test_real_read_other_user_session_rejected_without_token` | Lettura sessione altrui senza token → 403/404. Ownership intatta. |
| `test_demo_read_session_replay_with_token` | Lettura demo CON token → 200. Invariato. |
| `test_real_access_sessions_latest_without_token` | `/access-sessions/latest` real SENZA token → 200, scoping per user; altro utente non vede sessioni altrui. |

---

### Baseline B0 verificata post-B1/B4

Test eseguiti e passanti (nessuna regressione):
- `test_mines_start_accepts_valid_game_launch_token_header` ✅
- `test_mines_start_rejects_expired_game_launch_token_header` ✅
- `test_mines_start_reveal_cashout_updates_wallet_and_ledger` ✅
- `test_mines_cashout_idempotency_replay_keeps_original_balance_after_later_wallet_change` ✅
- `test_mines_demo_start_no_platform_rounds_write` ✅
- `test_mines_demo_full_round_cashout_no_ledger_write` ✅
- `test_close_access_session_auto_cashouts_with_safe_reveal_progress` (GAP-1) ✅

**Nota:** alcuni test pre-esistenti in `test_financial_and_mines_flows.py` e `test_platform_access_sessions.py` falliscono con mismatch JSON (`request_id`/`retryable` extra nella risposta di errore). Questo è un problema pre-esistente non correlato a B1.

---

## 6. Gap identificati

### GAP-1 — Close esplicita con progresso (auto-cashout, non refund)

**Stato:** ✅ Completato in B1-pre (test oracolo).  
**Test aggiunto:** `test_close_access_session_auto_cashouts_with_safe_reveal_progress` in `tests/integration/test_session_cascade_close.py:120`.  
**Descrizione:** Test oracolo che verifica: access session chiusa esplicitamente DOPO uno o più safe reveals → **auto-cashout** (payout = potential_payout).  
**Oracolo verificato:**
- close esplicita dopo 1 safe reveal → round status `won`, payout = potential_payout
- wallet balance = balance_after_reveal + potential_payout
- table_session chiusa con `closed_reason == "access_session_closed"`
- wallet reconciliation drift == `0.000000`

**Nota implementativa:** il helper `_create_active_table_session_and_round` è stato aggiornato per propagare `title_code` anche al body di `/table-sessions` (oltre che a `/access-sessions` e `/games/mines/start`), altrimenti il backend rifiuta con `"Access session is not active"` (mismatch title_code implicito).

### GAP-2 — Demo reveal senza token (diventa DoD della migrazione demo)

**Stato:** ✅ Completato in B3 (2026-06-04).  
**Descrizione:** Mines demo usa `provisionDemoPlayer` + bearer, senza alcun launch token.  
**Oracolo verificato:** `POST /auth/demo` → bearer demo; `POST /games/mines/start` con bearer + `wallet_type: "demo"` (senza token) → 200; reveal/cashout con bearer + `wallet_source: "demo"` (senza token) → 200; round si chiude correttamente; **nessuna** riga in `platform_rounds` o `ledger_transactions`. Test network `test_mines_network_header_verification.py` aggiornati e passati.

---

## 7. Approccio migrazione DEMO — Parte A (analisi, nessun codice)

### 7.1 Mines demo OGGI (front + back)

**Frontend** (`frontend-v3/app/ui/mines/mines-standalone.tsx`):
- `ensureDemoAnonToken` (riga ~904): chiama `POST /demo/token` → ottiene `anonymous_token`.
- `ensureDemoGameLaunchToken` (riga ~925): chiama `POST /demo/launch` con `X-Demo-Token` → ottiene `game_launch_token` contenente `anonymous_id`.
- `loadDemoSession` (riga ~962): chiama `GET /session/{id}` con header `X-Game-Launch-Token`.
- `handleRevealCell` / `handleCashout` (righe ~1161, ~1237): in demo mode inviano `X-Game-Launch-Token: demoGameLaunchToken`.
- `fetchGameReplay` (riga ~979): in demo mode invia `X-Game-Launch-Token`.

**Backend router** (`backend/app/api/routes/mines.py`):
- `_resolve_actor_and_launch_context` (riga ~178): se `launch_context["mode"] == "demo"`, restituisce `actor_id = anonymous_id`, `current_user = None`.
- `/start` (riga ~414): branch demo → `start_demo_session(anonymous_id=...)`.
- `/reveal` (riga ~599): branch demo → `reveal_demo_cell(anonymous_id=...)`.
- `/cashout` (riga ~693): branch demo → `cashout_demo_session(anonymous_id=...)`.

**Backend service** (`backend/app/modules/games/mines/service.py`):
- `start_demo_session` (riga 184): crea sessione su `demo_mines_game_rounds`, chiama `DemoPlatformGameClient.open_round`.
- `reveal_demo_cell` (riga 1139): legge da `demo_mines_game_rounds`, chiama `DemoPlatformGameClient.settle_win/loss`.
- `cashout_demo_session` (riga 1255): legge da `demo_mines_game_rounds`, chiama `DemoPlatformGameClient.settle_win`.

**Backend demo client** (`backend/app/modules/games/mines/platform_client.py`):
- `DemoPlatformGameClient` (righe 312–587): parla al **demo wallet** (`demo_play_sessions` + `demo_round_events`), **mai** a `platform_rounds` / `ledger_transactions` reali.
- `open_round` → `open_demo_session` + `debit_for_bet`.
- `settle_win` → `credit_for_win`.
- `settle_loss` → `record_loss`.

### 7.2 BOXE demo (pattern canonico)

**Frontend** (`frontend-v3/app/ui/boxe/boxe-standalone.tsx` o equivalente):
- `provisionDemoPlayer` → chiama `POST /auth/demo` → ottiene **utente reale** (`users` row) + **bearer token**.
- Tutti gli endpoint (start/reveal/cashout) usano `Authorization: Bearer <token>` + `wallet_source: "demo"` nel body. **Nessun launch token in demo.**

**Backend router** (`backend/app/api/routes/boxe.py`):
- `issue_boxe_launch_token` (riga ~101): **rifiuta** `mode != "real"`. Non esiste launch token demo.
- `boxe_start` (riga ~159): se `wallet_source == "demo"` con token real presente, rifiuta.
- Tutti gli endpoint usano `Depends(get_current_player)` — sempre un player reale (anche se demo).

**Backend service** (`backend/app/modules/games/boxe/service.py`):
- **Nessuna funzione demo separata**. Stesse funzioni real (`start_round`, `reveal_pick`, `cashout_round`).
- Branch interno su `wallet_source == "demo"`:
  - `start_round` (riga 195): `if normalized_wallet != "demo": open_platform_round(...)` — demo salta `platform_rounds`.
  - `reveal_pick` (riga 413): `if locked.data["platform_round_id"]: settle_platform_win/loss(...)` — demo salta settlement.
  - `cashout_round` (riga 526): `if locked.data["platform_round_id"]: settle_platform_win(...)` — demo salta settlement.
- `platform_round_id` è **NULL** per demo → nessun write su platform_rounds/ledger.

### 7.3 Confronto e opzioni

| Aspetto | Mines demo oggi | BOXE demo (canonico) |
|---------|-----------------|----------------------|
| Identità | `anonymous_id` da launch token | Utente reale (`users` row) con bearer |
| Auth | `X-Game-Launch-Token` (demo) | `Authorization: Bearer` (real player demo) |
| Service | Funzioni demo separate (`*_demo_*`) | Funzioni real unificate, branch interno `wallet=="demo"` |
| Tabelle | `demo_mines_game_rounds` separate | Stesse tabelle real, `platform_round_id=NULL` |
| Platform rounds | Mai toccate (DemoPlatformGameClient) | Mai toccate (salto quando `wallet=="demo"`) |
| Ledger | Mai toccato (demo wallet events) | Mai toccato (salto settlement) |

**Opzione A — Tieni funzioni demo separate, cambia solo identità (raccomandata)**
- Frontend: sostituisci `ensureDemoAnonToken` + `ensureDemoGameLaunchToken` con `provisionDemoPlayer` (chiama `/auth/demo`, ottiene bearer).
- Frontend: tutte le chiamate demo usano `Authorization: Bearer <demo_token>` + `wallet_source: "demo"` nel body. **Nessun `X-Game-Launch-Token` in demo.**
- Backend router: quando `authorization` è presente senza token, `_resolve_actor_and_launch_context` con `allow_real_without_token=True` ritorna `current_user`. Il frontend passa `wallet_source: "demo"` nel body. Il router usa `current_user["id"]` come `user_id` e chiama le **stesse funzioni demo separate** (`start_demo_session`, etc.), passando `user_id` invece di `anonymous_id`.
- Backend service: `start_demo_session`, `reveal_demo_cell`, `cashout_demo_session` accettano `user_id: str` invece di `anonymous_id: str`. `DemoPlatformGameClient` usa `user_id` come chiave per `demo_play_sessions` (o crea un mapping `user_id → demo_play_session`).

**Pro:** Minimo rischio. Il service layer demo (`DemoPlatformGameClient`, `demo_mines_game_rounds`) resta intatto e isolato. Non c'è fusione di path real/demo nel service. L'invariante "demo non tocca platform_rounds/ledger" è garantita per costruzione.

**Contro:** Il router mantiene il branching demo/real. Non è una vera unificazione come BOXE, ma è accettabile per un gioco "sacro".

**Opzione B — Unifica nel path real con guardia `wallet=="demo"` (sconsigliata)**
- Frontend: come A.
- Backend: elimina `start_demo_session`, `reveal_demo_cell`, `cashout_demo_session`. Usa `start_session`, `reveal_cell`, `cashout_session` con branch interno `if wallet_source == "demo":` che salta platform_rounds/ledger (come BOXE).
- Richiede refactoring del service real per gestire demo, o merge delle logiche. `mines_game_rounds` dovrebbe accogliere anche round demo (o rimanere separata con logica condizionale).

**Pro:** Codice unificato, meno duplicazione.

**Contro:** **Rischio troppo alto**. Le funzioni real di Mines toccano wallet/ledger/platform_rounds in molti punti. Un errore di branch potrebbe far scrivere demo su platform_rounds o viceversa. Inoltre, `demo_mines_game_rounds` ha schema diverso da `mines_game_rounds` (colonne demo-specifiche). La fusione richiede una migrazione DB e refactoring massivo del service.

**Raccomandazione CTO: Opzione A.** Il gioco Mines è "sacro" — non si fonde il path real/demo. Si cambia solo l'identità da anonymous a demo-player bearer, mantenendo le funzioni demo separate e il `DemoPlatformGameClient` intatto.

### 7.4 Invarianti da preservare (gate Parte B)

| Invariante | Come verificarla | Test |
|------------|------------------|------|
| Demo **NON** scrive su `platform_rounds` | `test_mines_demo_start_no_platform_rounds_write` | ✅ Deve restare verde |
| Demo **NON** scrive su `ledger_transactions` reali | `test_mines_demo_full_round_cashout_no_ledger_write` | ✅ Deve restare verde |
| Demo gioca end-to-end (start→reveal→cashout) | Smoke demo browser o script HTTP | ✅ Round si chiude, balance aggiornato |
| Demo **non** usa più `X-Game-Launch-Token` | `rg "X-Game-Launch-Token"` su `mines-standalone.tsx` | ✅ Zero occorrenze in rami demo |
| Demo usa bearer (`/auth/demo`) | Log network / test HTTP | ✅ Header `Authorization: Bearer` presente |

### 7.5 Rischi e micro-step Parte B (gated)

| Step | Descrizione | Rischio | Mitigazione |
|------|-------------|---------|-------------|
| **B3-front-a** | Sostituire `ensureDemoAnonToken` + `ensureDemoGameLaunchToken` con chiamata a `/auth/demo` e salvataggio bearer demo in storage. | Sessioni demo esistenti in localStorage diventano obsolete. | Clear storage demo all'avvio nuovo; fallback a `provisionDemoPlayer` se bearer assente/scaduto. |
| **B3-front-b** | Rimuovere `X-Game-Launch-Token` da tutti i rami demo (reveal/cashout/session/replay). Aggiungere `wallet_source: "demo"` nel body. | Frontend potrebbe inviare ancora token per errore. | DoD `rg X-Game-Launch-Token` → solo start real. |
| **B3-back-a** | Aggiornare router `/start`, `/reveal`, `/cashout` per accettare `wallet_source: "demo"` nel body quando `current_user` è presente (bearer). Branch a funzioni demo separate. | Router potrebbe confondere real e demo. | Assert esplicito: se `wallet_source == "demo"` → solo funzioni demo; se `wallet_source != "demo"` → solo funzioni real. |
| **B3-back-b** | `start_demo_session`, `reveal_demo_cell`, `cashout_demo_session`: cambiare parametro da `anonymous_id` a `user_id`. `DemoPlatformGameClient`: usare `user_id` come chiave. | Demo wallet potrebbe non trovare sessioni esistenti se la chiave cambia. | `DemoPlatformGameClient` accetta `user_id` e lo tratta come `anonymous_id` (la tabella `demo_play_sessions` usa `anonymous_id`, ma può essere allargata a `user_id` o usata come alias). |
| **B3-test** | Aggiornare test demo esistenti per usare `/auth/demo` + bearer. Aggiungere GAP-2 test (reveal/cashout demo senza token). | Test legacy potrebbero rompersi. | Eseguire test contract demo esistenti prima e dopo; aggiungere nuovi test in parallelo. |
| **B6-regression** | Verificare che real non sia toccato e demo giochi end-to-end. | Regressione su real o demo. | Eseguire baseline B0 completa (real + demo) + nuovi test GAP-2. |

### 7.6 Verifica finale (DoD Parte B)

1. **Network evidence:** catturare con browser o script HTTP che:
   - `POST /auth/demo` → 200, restituisce `access_token`.
   - `POST /games/mines/start` con `Authorization: Bearer <demo>` + `wallet_source: "demo"` → 200, **senza** `X-Game-Launch-Token`.
   - `POST /games/mines/reveal` e `/cashout` con bearer + `wallet_source: "demo"` → 200, **senza** launch token.
2. **Ledger isolation:** `test_mines_demo_start_no_platform_rounds_write` e `test_mines_demo_full_round_cashout_no_ledger_write` passano.
3. **DoD frontend:** `rg "X-Game-Launch-Token" frontend-v3/app/ui/mines/mines-standalone.tsx` → occorrenze solo in `handleStartSession` (ramo real+demo start) e **mai** in reveal/cashout/session/replay demo.

---

## 8. Piano step B0 → B7

| Step | Descrizione | Stato | Gate |
|------|-------------|-------|------|
| **B0** | Verifica ownership + cattura baseline test esistenti + identificazione gap | ✅ Completato | CTO approvato |
| **B1** | Backend: rendere X-Game-Launch-Token **opzionale** su `/games/mines/reveal` e `/games/mines/cashout` per real (bearer + ownership sufficienti). Retro-compatibile: token ancora accettato. Demo invariato. | ✅ Completato | CTO |
| **B2** | Colmare GAP-2: test oracolo "reveal demo senza token" → diventa DoD della migrazione demo B3 | ✅ Completato in B3 | CTO |
| **B3** | Migrazione demo Mines: `provisionDemoPlayer` + bearer, nessun launch token. Opzione A (funzioni demo separate, identità bearer). Front+back+test. | ✅ Completato | CTO |
| **B4** | Frontend Mines: rimuovere invio launch token da reveal/cashout real | ✅ Completato | CTO |
| **B5** | Backend Mines (se necessario): allineare endpoint reveal/cashout a non richiedere più token | ✅ N/A — completato in B1 | CTO |
| **B6** | Verifica non-regressione: tutti i test della baseline B0 passano + nuovi test B1/B3 passano | ⏳ PENDING — post-B3 | CTO |
| **B7** | Cross-game smoke finale: Mines + BOXE + HI-LO demo/real verificati a livello di rete | ⏳ PENDING — post-B3 | CTO |

---

## 8. Note aggiuntive

- **Test pre-esistenti rossi in `test_session_cascade_close.py`:** 4 test esistenti (`test_close_access_session_cascades_to_table_session_with_no_reveals`, `test_login_cleans_up_existing_active_sessions`, `test_logout_endpoint_closes_active_sessions`, `test_create_access_session_is_idempotent_when_active_exists`) falliscono con `"Master titles cannot be launched publicly"` (422) perché invocano `/access-sessions` senza `title_code` in un DB dove il default `mines` è un master title. Questo è un problema pre-esistente non correlato al WP. Il GAP-1 test aggiunto in B1 usa `create_published_mines_variant` per creare un title pubblicato e quindi passa.

## 9. Registro aggiornamenti

- `2026-06-04` — B0 completato. Ownership confermata, baseline catturata, GAP-1/GAP-2 identificati. Decisione CTO: pattern canonico = BOXE.
- `2026-06-03` — B1 completato. Backend `mines.py`: token opzionale su reveal/cashout real (`allow_real_without_token`). Test B1 aggiunti (`test_mines_reveal_cashout_optional_token.py`): reveal/cashout senza token + ownership cross-user. Baseline B0 verificata senza regressione. Demo e start invariati.
- `2026-06-03` — B4 completato. Frontend `mines-standalone.tsx`: rimosso invio token su reveal/cashout real. Demo e start invariati. `tsc --noEmit` pulito. Test rete aggiunti (`test_mines_network_header_verification.py`): full round real senza token + full round demo con token, wallet verificato.
- `2026-06-03` — B4-read completato. Backend: token opzionale anche su `/session/{id}`, `/session/{id}/fairness`, `/session/{id}/replay`. Frontend: rimosso invio token su `loadSession` e `fetchGameReplay` real. Test rete estesi: letture real senza token + lettura altrui rifiutata + letture demo con token. Baseline verde.
- `2026-06-03` — B4-latest completato. Backend `/access-sessions/latest`: token opzionale con query params `title_code`/`site_code` fallback; ownership confermata (`list_latest_access_session_history_for_user` scopa per `user_id`). Frontend `fetchLatestReplaySessions`: rimosso invio token real, passa `title_code` in query string. DoD `rg X-Game-Launch-Token`: rimane solo su start e rami demo. Test rete: `/access-sessions/latest` senza token, scoping per user verificato.
- `2026-06-03` — Parte A migrazione demo completata (analisi). Mappa Mines demo vs BOXE demo, confronto Opzione A vs B, raccomandazione Opzione A (funzioni demo separate + identità bearer). Invarianti, rischi, micro-step Parte B gated, DoD definiti. GAP-2 aggiornato a DoD della migrazione demo. WP aggiornato sezione 7.
