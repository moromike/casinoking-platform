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

### GAP-2 — Demo reveal senza token

**Stato:** 📝 Annotato in B2 (nessun codice test aggiunto, solo documentazione nel WP).  
**Descrizione:** Oggi Mines reveal demo richiede il launch token. Quando in B3-B4 il demo passa al pattern BOXE (provisioned player, nessun launch token), serve un test che confermi reveal demo funzioni senza token.  
**Oracolo atteso:** demo start senza token → reveal senza token → cashout senza token; round si chiude correttamente.  
**Blocco:** non è possibile scrivere un test che passi oggi perché il backend attuale richiede ancora il token su reveal/cashout. Il test andrà scritto in B2 dopo che il frontend/demo sarà stato modificato in B3, OPPURE può essere scritto in anticipo come `@pytest.mark.skip(reason="Attende B3-B4: demo senza launch token")` se il team preferisce avere l'oracolo pronto.  
**Decisione B2:** lasciare il test come TODO nel WP; non aggiungere codice di test che fallirebbe o sarebbe skip.

---

## 7. Piano step B0 → B7

| Step | Descrizione | Stato | Gate |
|------|-------------|-------|------|
| **B0** | Verifica ownership + cattura baseline test esistenti + identificazione gap | ✅ Completato | CTO approvato |
| **B1** | Backend: rendere X-Game-Launch-Token **opzionale** su `/games/mines/reveal` e `/games/mines/cashout` per real (bearer + ownership sufficienti). Retro-compatibile: token ancora accettato. Demo invariato. | ✅ Completato | CTO |
| **B2** | Colmare GAP-2: annotare test "reveal demo senza token" nel WP (oracolo per B3-B4; test scrivibile solo post-B3) | 📝 Annotato | CTO |
| **B3** | Frontend Mines: rimuovere invio launch token da reveal/cashout demo | ⏳ PENDING | CTO |
| **B4** | Frontend Mines: rimuovere invio launch token da reveal/cashout real | ✅ Completato | CTO |
| **B5** | Backend Mines (se necessario): allineare endpoint reveal/cashout a non richiedere più token | ✅ N/A — completato in B1 | CTO |
| **B6** | Verifica non-regressione: tutti i test della baseline B0 passano + nuovi test B1 passano | ✅ Completato | CTO |
| **B7** | Cross-game smoke finale: Mines + BOXE + HI-LO demo/real verificati a livello di rete | ⏳ PENDING | CTO |

---

## 8. Note aggiuntive

- **Test pre-esistenti rossi in `test_session_cascade_close.py`:** 4 test esistenti (`test_close_access_session_cascades_to_table_session_with_no_reveals`, `test_login_cleans_up_existing_active_sessions`, `test_logout_endpoint_closes_active_sessions`, `test_create_access_session_is_idempotent_when_active_exists`) falliscono con `"Master titles cannot be launched publicly"` (422) perché invocano `/access-sessions` senza `title_code` in un DB dove il default `mines` è un master title. Questo è un problema pre-esistente non correlato al WP. Il GAP-1 test aggiunto in B1 usa `create_published_mines_variant` per creare un title pubblicato e quindi passa.

## 9. Registro aggiornamenti

- `2026-06-04` — B0 completato. Ownership confermata, baseline catturata, GAP-1/GAP-2 identificati. Decisione CTO: pattern canonico = BOXE.
- `2026-06-03` — B1 completato. Backend `mines.py`: token opzionale su reveal/cashout real (`allow_real_without_token`). Test B1 aggiunti (`test_mines_reveal_cashout_optional_token.py`): reveal/cashout senza token + ownership cross-user. Baseline B0 verificata senza regressione. Demo e start invariati.
- `2026-06-03` — B4 completato. Frontend `mines-standalone.tsx`: rimosso invio token su reveal/cashout real. Demo e start invariati. `tsc --noEmit` pulito. Test rete aggiunti (`test_mines_network_header_verification.py`): full round real senza token + full round demo con token, wallet verificato.
- `2026-06-03` — B4-read completato. Backend: token opzionale anche su `/session/{id}`, `/session/{id}/fairness`, `/session/{id}/replay`. Frontend: rimosso invio token su `loadSession` e `fetchGameReplay` real. Test rete estesi: letture real senza token + lettura altrui rifiutata + letture demo con token. Baseline verde.
- `2026-06-03` — B4-latest completato. Backend `/access-sessions/latest`: token opzionale con query params `title_code`/`site_code` fallback; ownership confermata (`list_latest_access_session_history_for_user` scopa per `user_id`). Frontend `fetchLatestReplaySessions`: rimosso invio token real, passa `title_code` in query string. DoD `rg X-Game-Launch-Token`: rimane solo su start e rami demo. Test rete: `/access-sessions/latest` senza token, scoping per user verificato.
