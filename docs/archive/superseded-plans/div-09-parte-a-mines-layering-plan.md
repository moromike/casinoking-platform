# DIV-09 Parte-A — Piano di Refactor LAYERING per Mines

> **Task**: estrarre `repository.py` + `state_machine.py` da `mines/service.py`, portando Mines alla stessa stratificazione canonica di BOXE / HI-LO.  
> **Scope**: solo pianificazione (read-only). Nessuna modifica di codice.  
> **Commit target**: `feature/site-v3-cms-ia-cleanup` (o sotto-branch dedicato).  
> **Linea guida**: zero diff comportamentale soldi. Il flusso real/demo/settlement/idempotenza/locking deve rimanere identico.

---

## 1. Mappa blocco-per-blocco di `mines/service.py` (1895 righe)

### 1.1 Service entry-point (orchestrazione + business logic)

| # | Funzione | Riga | Classificazione | Note |
|---|----------|------|-----------------|------|
| 1 | `start_session()` | 58-257 | **SERVICE** | Validazione input, idempotenza (chiama `_get_existing_session_by_idempotency`), fairness nonce, branching demo vs real, INSERT via `_insert_mines_game_round`, idempotency save, response building |
| 2 | `reveal_cell()` | 978-1145 | **SERVICE** | `pg_advisory_xact_lock`, `_get_session_for_update`, branching demo vs real settlement, chiamata a `_close_game_round_as_lost` / `_update_game_round_after_safe_reveal` / `_close_game_round_as_won`, idempotency save |
| 3 | `cashout_session()` | 1146-1363 | **SERVICE** | `pg_advisory_xact_lock`, idempotency check, `_get_session_for_update`, branching demo vs real settlement, `_close_game_round_as_won`, idempotency save, response building |

### 1.2 Query di lettura (READ) — estrarre in `repository.py`

| # | Funzione | Riga | Classificazione | Note |
|---|----------|------|-----------------|------|
| 4 | `get_session_for_user()` | 259-424 | **REPOSITORY** | SELECT con JOIN `platform_rounds`, replay, serialization |
| 5 | `list_recent_sessions_for_user()` | 426-433 | **REPOSITORY** | SELECT recenti |
| 6 | `list_session_history_page_for_user()` | 434-506 | **REPOSITORY** | Paginazione con cursor |
| 7 | `list_latest_access_session_history_for_user()` | 507-616 | **REPOSITORY** | Access session history |
| 8 | `get_session_replay_for_user()` | 617-709 | **REPOSITORY** | Replay payload per user |
| 9 | `get_session_replay_for_admin()` | 710-762 | **REPOSITORY** | Replay payload per admin |
| 10 | `get_session_fairness_for_user()` | 899-977 | **REPOSITORY** | Fairness info |
| 11 | `session_exists()` | 1365-1377 | **REPOSITORY** | `SELECT 1` esistenza |
| 12 | `session_belongs_to_user()` | 1380-1393 | **REPOSITORY** | `SELECT 1` ownership |
| 13 | `_get_existing_session_by_idempotency()` | 1681-1710 | **REPOSITORY** | JOIN `platform_rounds` + `mines_game_rounds` per idempotency lookup |
| 14 | `_get_existing_session_by_idempotency_outside_tx()` | 1713-1726 | **REPOSITORY** | Stessa funzione fuori transazione |
| 15 | `_get_closed_round_mine_positions()` | 1767-1795 | **REPOSITORY** | SELECT `mine_positions_json` |

### 1.3 Helper di lettura — estrarre in `repository.py`

| # | Funzione | Riga | Classificazione | Note |
|---|----------|------|-----------------|------|
| 16 | `_build_session_replay_payload()` | 763-818 | **REPOSITORY** | Trasforma DB row in replay JSON |
| 17 | `_serialize_session_history_row()` | 819-857 | **REPOSITORY** | Trasforma DB row in history JSON |
| 18 | `_encode_session_history_cursor()` | 858-881 | **REPOSITORY** | Cursor encode (base64+json) |
| 19 | `_decode_session_history_cursor()` | 867-881 | **REPOSITORY** | Cursor decode |
| 20 | `_build_cashout_response_from_existing()` | 1738-1766 | **REPOSITORY** | SELECT ledger per cashout esistente |
| 21 | `_start_response_from_existing()` | 1848-1875 | **REPOSITORY** | Build response da DB row |

### 1.4 Query di scrittura (WRITE) — estrarre in `repository.py`

| # | Funzione | Riga | Classificazione | Note |
|---|----------|------|-----------------|------|
| 22 | `_insert_mines_game_round()` | 1408-1476 | **REPOSITORY** | INSERT `mines_game_rounds` |
| 23 | `_close_game_round_as_lost()` | 1478-1503 | **REPOSITORY** | UPDATE `status = 'lost'` con `WHERE status = 'active'` |
| 24 | `_close_game_round_as_won()` | 1504-1537 | **REPOSITORY** | UPDATE `status = 'won'` con `WHERE status = 'active'` |
| 25 | `_update_game_round_after_safe_reveal()` | 1538-1566 | **REPOSITORY** | UPDATE `safe_reveals_count`, `multiplier`, `payout` |
| 26 | `_get_session_for_update()` | 1568-1601 | **REPOSITORY** | SELECT FOR UPDATE (lock riga DB) |
| 27 | `_save_idempotency_result()` | 1603-1648 | **REPOSITORY** | INSERT/UPSERT `mines_idempotency_keys` |
| 28 | `_get_idempotency_result()` | 1651-1678 | **REPOSITORY** | SELECT `mines_idempotency_keys` |
| 29 | `_get_next_fairness_nonce()` | 1727-1737 | **REPOSITORY** | `SELECT nextval('fairness_nonce_seq')` |

### 1.5 State / validazione — estrarre in `state_machine.py`

| # | Funzione | Riga | Classificazione | Note |
|---|----------|------|-----------------|------|
| 30 | `_ensure_session_active()` | 1826-1832 | **STATE_MACHINE** | Precondizione: `status == 'active'` |
| 31 | `_validate_cell_index()` | 1833-1837 | **STATE_MACHINE** | Bound check su `cell_index` vs `grid_size` |

### 1.6 Helper puri / formattazione — restano nel service o utility

| # | Funzione | Riga | Classificazione | Note |
|---|----------|------|-----------------|------|
| 32 | `_normalize_cell_list()` | 882-898 | **UTILITY** | Normalizzazione input JSON cells |
| 33 | `_ordered_unique_cells()` | 888-898 | **UTILITY** | Deduplicazione e ordinamento celle |
| 34 | `_build_request_fingerprint()` | 1796-1825 | **UTILITY** | SHA256 fingerprint request |
| 35 | `_parse_bet_amount()` | 1838-1847 | **UTILITY** | `Decimal` parsing |
| 36 | `_normalize_title_code()` | 1876-1882 | **UTILITY** | `strip().upper()` |
| 37 | `_normalize_site_code()` | 1883-1889 | **UTILITY** | `strip().lower()` |
| 38 | `_format_amount()` | 1890-1893 | **UTILITY** | Formattazione display |
| 39 | `_format_multiplier()` | 1894-1895 | **UTILITY** | Formattazione display |

---

## 2. Confronto con BOXE e HI-LO (pattern target)

### 2.1 BOXE (`backend/app/modules/games/boxe/`)

```
boxe/
├── repository.py        ← CRUD + idempotency + lock + apply_transition
├── state_machine.py     ← Enum status/event + LEGAL_TRANSITIONS + transition()
├── service.py           ← Orchestrazione (validazione input, chiama repo, chiama demo_wallet/platform, build response)
└── round_gateway.py     ← Già esiste anche per Mines
```

**Metodi BOXE repository (firme canoniche):**
- `create_round(connection, ...)` → INSERT `boxe_rounds`
- `get_round(connection, round_id)` → SELECT
- `lock_round(connection, round_id)` → `LockedRound(id, status)` via SELECT FOR UPDATE
- `apply_transition(connection, round_id, event)` → lock + `state_machine.transition()` + `update_round_status`
- `update_round_status(connection, round_id, new_status, *, closed_at_expr=...)` → UPDATE generico
- `record_pick(connection, ...)` → INSERT `boxe_picks`
- `get_pick_by_idempotency_key(connection, ...)` → SELECT idempotency
- `save_idempotency_result(connection, ...)` → INSERT/UPSERT `boxe_idempotency_keys`
- `get_idempotency_result(connection, ...)` → SELECT idempotency
- `list_terminal_rounds(connection, ...)` → SELECT con `status IN TERMINAL_STATUSES`

**Metodi BOXE state_machine:**
- `BoxeRoundStatus` (Enum)
- `BoxeTransitionEvent` (Enum)
- `LEGAL_TRANSITIONS: dict[BoxeRoundStatus, dict[BoxeTransitionEvent, BoxeTransition]]`
- `transition(from_status, event) -> BoxeTransition`
- `validate_pick_attempt(...)` / `validate_collect_attempt(...)`
- `BoxeStateTransitionError(from_status, event, reason)`

### 2.2 HI-LO (`backend/app/modules/games/hi_lo/`)

Struttura identica a BOXE. Differenze:
- `update_round_after_active_skip()` — logica specifica HI-LO
- `update_round_after_prediction()` — calcolo payout/multiplier inline
- `record_action()` — INSERT `hi_lo_actions`
- `get_actions()` — SELECT actions per replay

### 2.3 Mappa di cosa Mines deve replicare

| Pattern BOXE/HI-LO | Equivalente Mines | Dove va |
|--------------------|-------------------|---------|
| `create_round()` | `_insert_mines_game_round()` | `repository.py` |
| `get_round()` | `get_session_for_user()` (semplificato) | `repository.py` |
| `lock_round()` | `_get_session_for_update()` → rinominare `lock_round()` | `repository.py` |
| `apply_transition()` | Nuovo: `apply_transition(connection, session_id, event)` | `repository.py` |
| `update_round_status()` | `_close_game_round_as_lost` / `_won` → generalizzare | `repository.py` |
| `record_pick()` / `record_action()` | `_update_game_round_after_safe_reveal()` | `repository.py` |
| `save_idempotency_result()` | `_save_idempotency_result()` | `repository.py` |
| `get_idempotency_result()` | `_get_idempotency_result()` | `repository.py` |
| `get_pick_by_idempotency_key()` | `_get_existing_session_by_idempotency()` | `repository.py` |
| `list_terminal_rounds()` | Nuovo (per history) | `repository.py` |
| `BoxeRoundStatus` | `MinesRoundStatus` (active, won, lost, cancelled) | `state_machine.py` |
| `BoxeTransitionEvent` | `MinesTransitionEvent` (start, reveal_safe, reveal_mine, cashout) | `state_machine.py` |
| `LEGAL_TRANSITIONS` | `LEGAL_TRANSITIONS: active→{reveal_safe,reveal_mine,cashout}, ...` | `state_machine.py` |
| `transition()` | `transition(from_status, event)` | `state_machine.py` |
| `validate_pick_attempt()` | `validate_reveal_attempt(session, cell_index)` | `state_machine.py` |
| `validate_collect_attempt()` | `validate_cashout_attempt(session)` | `state_machine.py` |

### 2.4 Firme repository — standard BOXE/HI-LO da rispettare

- **Primo argomento**: `connection: psycopg.Connection[DictRow]`
- **Nessuna gestione transazione interna**: il chiamante (service.py) apre `with db_connection() as conn:`
- **Lock**: `lock_round()` restituisce un dataclass `LockedRound(id, status)` (come BOXE)
- **Apply transition**: il repository NON chiama direttamente demo_wallet o platform; chiama solo `update_round_status`

---

## 3. Seams Critici e RISCHI

### 3.1 R1 — `pg_advisory_xact_lock(hashtext(session_id))` (DIV-02)

**Posizione**: riga 982 in `reveal_cell`, riga 1157 in `cashout_session`.

**Comportamento**: il lock advisory PostgreSQL (`pg_advisory_xact_lock`) garantisce mutua esclusione tra `reveal_cell` e `cashout_session` sullo stesso `session_id`, indipendentemente dal `FOR UPDATE` riga.

**Rischio**: se spostato in `repository.lock_round()` senza che il service lo chiami esplicitamente, si perde la sequenza lock-advisory → lock-riga → business-logic.  
**Mitigazione**: il service.py deve continuare a chiamare `pg_advisory_xact_lock` come **prima operazione** dentro la transazione, prima di `repository.lock_round()`. Il repository NON deve gestire il lock advisory.

### 3.2 R2 — Close ottimistiche `WHERE status = 'active'`

**Posizione**: `_close_game_round_as_lost` (r.1478) e `_close_game_round_as_won` (r.1504).

**Comportamento**: `UPDATE mines_game_rounds SET status = %s WHERE id = %s AND status = 'active'` impedisce il double-settlement se due request concorrenti arrivano (es. cashout mentre reveal sta processando la mina).

**Rischio**: se generalizzato in `update_round_status()` senza la clausola `WHERE status = 'active'`, si riapre il race condition.  
**Mitigazione**: `repository.update_round_status()` per Mines DEVE includere `WHERE status = 'active'` per le transizioni verso stati terminali (`won`, `lost`).

### 3.3 R3 — Demo wallet path

**Posizioni**:
- `start_session` r.123-181: `open_demo_session()` + `debit_for_bet()`
- `reveal_cell` r.1002-1027: `record_loss()` (demo)
- `reveal_cell` r.1060-1080: `credit_for_win()` (demo, auto-win)
- `cashout_session` r.1248-1285: `credit_for_win()` (demo)

**Rischio**: l'ordine delle chiamate demo (demo_round → debito → game_round → idempotency) è critico. Se il repository inizia a gestire demo, si rompe la separazione layering.  
**Mitigazione**: le chiamate a `demo_wallet.service` rimangono nel **service.py** come orchestrazione. Il repository si limita a CRUD su `mines_game_rounds`.

### 3.4 R4 — Real settlement path (platform)

**Posizioni**:
- `start_session` r.191-255: `open_round()` da `round_gateway.py`
- `reveal_cell` r.1035-1047: `settle_round_loss()`
- `reveal_cell` r.1070-1080: `settle_round_win()` (auto-win)
- `cashout_session` r.1267-1285: `settle_round_win()`

**Rischio**: l'ordine tra platform round e game round è fisso. Se il repository chiama platform, viola il layering (il repository non deve dipendere da `round_gateway`).  
**Mitigazione**: `round_gateway` resta chiamato dal **service.py** come oggi.

### 3.5 R5 — Idempotenza e `request_fingerprint`

**Posizione**: `_save_idempotency_result` (r.1603), `_get_idempotency_result` (r.1651), `_get_existing_session_by_idempotency` (r.1681).

**Comportamento**: idempotency key + `request_fingerprint` SHA256. Se il fingerprint cambia (stessa key, payload diverso) → errore.

**Rischio**: spostando in repository, il calcolo del fingerprint (`_build_request_fingerprint`) è un helper puro che può rimanere nel service o diventare utility. La logica di conflict check deve rimanere identica.  
**Mitigazione**: il repository riceve `request_fingerprint: str` già calcolato dal service. Non calcola lui.

### 3.6 R6 — Fairness nonce e artifact creation

**Posizione**: `_get_next_fairness_nonce` (r.1727), `create_fairness_artifacts` (chiamato in `start_session`).

**Rischio**: la sequenza è: (1) genera nonce, (2) crea artifacts, (3) INSERT game round con nonce. Se il nonce viene generato nel repository dopo l'INSERT, si rompe il replay.  
**Mitigazione**: `repository.get_next_fairness_nonce(connection)` restituisce il valore; il service passa il nonce a `repository.create_round()`. La creazione artifacts (`create_fairness_artifacts`) resta nel service (o in un fairness service separato).

### 3.7 R7 — Replay / history JSON shape

**Posizione**: `_build_session_replay_payload` (r.763), `_serialize_session_history_row` (r.819).

**Rischio**: i test di replay (`test_mines_replay.py`) e history (`test_mines_player_session_history.py`, `test_mines_session_history_pagination.py`) fanno assert esatti sulla struttura JSON. Qualsiasi spostamento di questi helper in repository non deve cambiare la shape.  
**Mitigazione**: questi helper sono puri (trasformano `dict` → `dict`). Possono essere spostati in repository senza rischi, ma **i test gate HARD devono passare senza modifiche**.

### 3.8 R8 — `wallet_type` whitelist (DIV-07)

**Posizione**: riga 72-74 in `start_session`.

**Comportamento**: `normalized_wallet_type = wallet_type.strip().lower()` con whitelist `{cash, bonus, demo}`.

**Rischio**: nessuno — è validazione input che resta nel service.

---

## 4. Test Suite Gate HARD — Elenco Completo

Totale: **242 test** (collected). Devono essere tutti PASS sia DURANTE il refactor (step-by-step) che alla fine.

### 4.1 Unit (3 test)

| File | # test | Cosa copre |
|------|--------|-----------|
| `tests/unit/test_mines_fairness.py` | 3 | Seeded generation, nonce change, hash stability |

### 4.2 Contract (≈ 40 test)

| File | # test | Cosa copre |
|------|--------|-----------|
| `tests/contract/test_mines_demo_contract.py` | ~10 | Demo wallet path completo (start → reveal → cashout / loss) |
| `tests/contract/test_mines_runtime_contract.py` | ~10 | Transizioni stato, validazione input, replay shape |
| `tests/contract/test_mines_player_session_history_contract.py` | ~10 | History API, pagination, shape JSON |
| `tests/contract/test_mines_admin_session_contract.py` | ~10 | Admin replay, admin snapshot access |

### 4.3 Integration (≈ 80 test)

| File | # test | Cosa copre |
|------|--------|-----------|
| `tests/integration/test_mines_embed_browser_smoke.py` | ~5 | Smoke end-to-end |
| `tests/integration/test_mines_reveal_cashout_optional_token.py` | ~6 | Header `X-Game-Launch-Token` opzionale |
| `tests/integration/test_mines_session_history_pagination.py` | ~8 | Cursor pagination |
| `tests/integration/test_mines_player_session_history.py` | ~8 | History per player |
| `tests/integration/test_mines_replay.py` | ~8 | Replay payload exact shape |
| `tests/integration/test_mines_fairness_seeded.py` | ~6 | Fairness seeded RNG |
| `tests/integration/test_mines_fairness_verify.py` | ~6 | Fairness verification endpoint |
| `tests/integration/test_mines_fairness_rotation.py` | ~6 | Fairness nonce rotation |
| `tests/integration/test_mines_backoffice_config.py` | ~5 | Config backoffice |
| `tests/integration/test_mines_admin_session_snapshot_access.py` | ~8 | Admin snapshot |
| `tests/integration/test_mines_network_header_verification.py` | ~5 | Header verification |
| `tests/integration/test_financial_and_mines_flows.py` | ~15 | Financial flow real + demo |

### 4.4 Concurrency (≈ 15 test)

| File | # test | Cosa copre |
|------|--------|-----------|
| `tests/concurrency/test_mines_concurrency.py` | ~10 | Race reveal vs cashout, double-reveal |
| `tests/concurrency/test_mines_fairness_rotation_concurrency.py` | ~5 | Fairness nonce race |

### 4.5 Stress (≈ 124 test)

| File | # test | Cosa copre |
|------|--------|-----------|
| `tests/stress/mines_math/test_mines_math_stress.py` | ~122 | RTP stress per ogni combinazione (grid_size, mine_count) |
| `tests/stress/mines_math/test_mines_simulator_backend_parity.py` | 2 | Parity simulator Python ↔ backend payout table + RNG |

### 4.6 Comando gate HARD

```bash
cd /c/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform
python -m pytest \
  tests/unit/test_mines_fairness.py \
  tests/contract/test_mines_demo_contract.py \
  tests/contract/test_mines_runtime_contract.py \
  tests/contract/test_mines_player_session_history_contract.py \
  tests/contract/test_mines_admin_session_contract.py \
  tests/integration/test_mines_embed_browser_smoke.py \
  tests/integration/test_mines_reveal_cashout_optional_token.py \
  tests/integration/test_mines_session_history_pagination.py \
  tests/integration/test_mines_player_session_history.py \
  tests/integration/test_mines_replay.py \
  tests/integration/test_mines_fairness_seeded.py \
  tests/integration/test_mines_fairness_verify.py \
  tests/integration/test_mines_fairness_rotation.py \
  tests/integration/test_mines_backoffice_config.py \
  tests/integration/test_mines_admin_session_snapshot_access.py \
  tests/integration/test_mines_network_header_verification.py \
  tests/integration/test_financial_and_mines_flows.py \
  tests/concurrency/test_mines_concurrency.py \
  tests/concurrency/test_mines_fairness_rotation_concurrency.py \
  tests/stress/mines_math/test_mines_math_stress.py \
  tests/stress/mines_math/test_mines_simulator_backend_parity.py \
  -v
```

---

## 5. Effort Stimato e Ordine Micro-Step

### 5.1 Principi guida

1. **Un layer alla volta**: estrai prima il repository, poi lo state machine, infine rifattorizza il service.
2. **Suite verde tra i passi**: ogni micro-step deve lasciare tutti i 242 test PASS.
3. **Nessun rename di API pubblica**: i router (`mines/router.py`) e i test non devono cambiare.
4. **Nessuna modifica a test**: se un test fallisce, il codice è sbagliato, non il test.

### 5.2 Micro-Step

#### Step 1 — Scaffold `mines/repository.py` (idempotency + esistenza)
**Scope**: spostare in `repository.py`:
- `_save_idempotency_result`
- `_get_idempotency_result`
- `_get_existing_session_by_idempotency`
- `_get_existing_session_by_idempotency_outside_tx`
- `session_exists`
- `session_belongs_to_user`

**Firme**: primo arg `connection: psycopg.Connection[DictRow]`, come BOXE.
**Service.py**: importa e delega.
**Test gate**: tutti i test idempotency + esistenza.
**Effort**: ~1h.

#### Step 2 — Scaffold `mines/repository.py` (CRUD game round)
**Scope**: spostare in `repository.py`:
- `_insert_mines_game_round` → `create_round(connection, ...)`
- `_get_session_for_update` → `lock_round(connection, session_id) -> LockedRound`
- `_close_game_round_as_lost` → `update_round_status(connection, session_id, 'lost', ...)`
- `_close_game_round_as_won` → `update_round_status(connection, session_id, 'won', ...)`
- `_update_game_round_after_safe_reveal` → `record_safe_reveal(connection, session_id, ...)`
- `_get_next_fairness_nonce` → `get_next_fairness_nonce(connection)`
- `_get_closed_round_mine_positions` → `get_round_mine_positions(connection, session_id)`

**Attenzione**: `update_round_status` per terminali DEVE mantenere `WHERE status = 'active'` (R2).
**Test gate**: test start, reveal, cashout base.
**Effort**: ~1.5h.

#### Step 3 — Lettura (get/list/replay/history)
**Scope**: spostare in `repository.py`:
- `get_session_for_user`
- `list_recent_sessions_for_user`
- `list_session_history_page_for_user` (+ cursor helpers)
- `list_latest_access_session_history_for_user`
- `get_session_replay_for_user`
- `get_session_replay_for_admin`
- `_build_session_replay_payload`
- `_serialize_session_history_row`
- `_build_cashout_response_from_existing`
- `_start_response_from_existing`

**Attenzione**: helper JSON shape non devono cambiare (R7).
**Test gate**: replay, history, pagination, admin snapshot.
**Effort**: ~1.5h.

#### Step 4 — `mines/state_machine.py`
**Scope**: creare:
- `MinesRoundStatus(Enum)` = `active`, `won`, `lost`, `cancelled`
- `MinesTransitionEvent(Enum)` = `start`, `reveal_safe`, `reveal_mine`, `cashout`
- `LEGAL_TRANSITIONS: dict` (come BOXE/HI-LO)
- `transition(from_status, event) -> MinesTransition`
- `MinesStateTransitionError`
- `validate_reveal_attempt(session, cell_index)` → include `_validate_cell_index` + `_ensure_session_active`
- `validate_cashout_attempt(session)` → include `_ensure_session_active` + `safe_reveals_count > 0`

**Attenzione**: i test non chiamano direttamente lo state machine (chiamano il service), quindi questo step è "invisibile" ai test finché il service non viene rifattorizzato.
**Test gate**: nessuno nuovo; deve non rompere step 1-3.
**Effort**: ~1h.

#### Step 5 — Refactor `service.py` per usare repository + state_machine
**Scope**:
- `start_session`: usa `repository.get_next_fairness_nonce`, `repository.create_round`, `repository.save_idempotency`, `state_machine.transition(..., start)`
- `reveal_cell`: `pg_advisory_xact_lock` → `repository.lock_round` → `state_machine.transition` → `repository.record_safe_reveal` / `repository.update_round_status`
- `cashout_session`: `pg_advisory_xact_lock` → `repository.lock_round` → `state_machine.transition` → `repository.update_round_status`
- Mantenere nel service: branching demo/real, chiamate `demo_wallet` e `round_gateway`, response building, fingerprint calculation.

**Attenzione**: `pg_advisory_xact_lock` rimane nel service (R1). Demo/real settlement rimane nel service (R3, R4).
**Test gate**: **full suite 242 test**.
**Effort**: ~2h.

#### Step 6 — Pulizia e Gate HARD finale
**Scope**:
- Rimuovere funzioni orfane da `service.py`.
- Verificare che `service.py` sia ridotto a ~600-800 righe (da 1895).
- Eseguire gate HARD completo.
- Eventuali iterazioni.
**Effort**: ~1-2h.

### 5.3 Effort totale stimato

| Fase | Tempo stimato |
|------|---------------|
| Step 1 | 1h |
| Step 2 | 1.5h |
| Step 3 | 1.5h |
| Step 4 | 1h |
| Step 5 | 2h |
| Step 6 | 1-2h |
| **Totale** | **8-9h** (~2 giornate di lavoro) |

### 5.4 Branching consigliato

Proporre un sotto-branch dedicato per isolare il refactor:
```bash
git checkout -b feature/div-09-mines-layering
```
Con merge in `feature/site-v3-cms-ia-cleanup` solo dopo gate HARD verde.

---

## Appendice A — Note di implementazione dettagliate

### A.1 `LockedRound` per Mines

Come BOXE, il repository restituisce:
```python
@dataclass(frozen=True)
class LockedRound:
    id: str
    status: MinesRoundStatus
```

Il service dopo `lock_round()` ha la garanzia di avere la riga lockata.

### A.2 `apply_transition` per Mines

Il pattern canonico BOXE/HI-LO:
```python
def apply_transition(conn, round_id, event):
    locked = lock_round(conn, round_id)
    transition = state_machine.transition(locked.status, event)
    update_round_status(conn, round_id, transition.new_status, ...)
    return transition
```

Mines ha una complessità in più: `reveal_cell` decide **runtime** se l'evento è `reveal_safe` o `reveal_mine` (in base alla posizione della mina). Quindi il service decide l'evento, poi chiama `apply_transition`.

### A.3 `_update_game_round_after_safe_reveal` vs BOXE `record_pick`

In BOXE `record_pick` fa INSERT in `boxe_picks` (tabella azioni) + UPDATE `boxe_rounds`.  
In Mines NON c'è tabella azioni: le safe reveals sono solo un contatore sul game round. Quindi `_update_game_round_after_safe_reveal` è equivalente a `update_round_after_safe_reveal` nel repository, senza INSERT secondario.

### A.4 Demo path e `round_gateway`

Il service mantiene questo flusso esatto:
```
# start_session (demo)
open_demo_session → debit_for_bet → repository.create_round → save_idempotency

# reveal_cell (demo loss)
repository.lock_round → check mine → record_loss → repository.update_round_status('lost') → save_idempotency

# reveal_cell (demo safe)
repository.lock_round → check safe → repository.record_safe_reveal → if max_safe → credit_for_win → repository.update_round_status('won') → save_idempotency

# cashout_session (demo)
repository.lock_round → validate_cashout → credit_for_win → repository.update_round_status('won') → save_idempotency
```

### A.5 Real path

```
# start_session (real)
round_gateway.open_round → repository.create_round → save_idempotency

# reveal_cell (real loss)
repository.lock_round → check mine → round_gateway.settle_round_loss → repository.update_round_status('lost') → save_idempotency

# reveal_cell (real safe)
repository.lock_round → check safe → repository.record_safe_reveal → if max_safe → round_gateway.settle_round_win → repository.update_round_status('won') → save_idempotency

# cashout_session (real)
repository.lock_round → validate_cashout → round_gateway.settle_round_win → repository.update_round_status('won') → save_idempotency
```

L'ordine `round_gateway.settle_round_*` prima di `repository.update_round_status` è cruciale: se il platform settlement fallisce, il game round resta `active` e può essere ritentato (o gestito da admin).
