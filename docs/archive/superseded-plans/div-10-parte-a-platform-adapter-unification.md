# DIV-10 Parte-A — Piano di uniformazione Platform Client al typed adapter (pattern BOXE)

> **Task**: portare Mines e HI-LO allo stesso typed adapter facade di BOXE (`PlatformGameAdapter` via `get_default_platform_adapter()`), eliminando il class-based Protocol custom di Mines e le funzioni dirette di HI-LO.  
> **Scope**: solo pianificazione (read-only). Nessuna modifica di codice.  
> **Decisione**: si esegue (perfezione-first).

---

## 1. Mappa forma ATTUALE del platform_client dei 3 giochi

### 1.1 BOXE — typed adapter canonico (`backend/app/modules/games/boxe/platform_client.py` : 388 righe)

**Pattern**: `InProcessBoxePlatformAdapter` implementa `PlatformGameAdapter` (Protocol da `app.modules.platform.game_modules.adapter`). Singleton `_DEFAULT_PLATFORM_ADAPTER` + `get_default_platform_adapter()`.

**Metodi adapter (interfaccia canonica)**:
```python
class InProcessBoxePlatformAdapter:
    def open_round(self, request: PlatformOpenRoundRequest) -> PlatformOpenRoundResult
    def settle_win(self, request: PlatformSettleWinRequest) -> PlatformSettlementResult
    def settle_loss(self, request: PlatformSettleLossRequest) -> PlatformSettlementResult
```

**Wrapper funzioni esposte a `service.py` / `round_gateway.py`**:
| Funzione | Firma verso il gioco | Note |
|----------|---------------------|------|
| `open_round` | `(*, cursor, user_id, round_id, idempotency_key, rows, difficulty, bet_amount, wallet_type, title_code, site_code, table_session_id, access_session_id, request_fingerprint) -> BoxePlatformRoundOpenResult` | Costruisce `PlatformOpenRoundRequest`, chiama adapter, traduce risultato in dataclass BOXE-specifica |
| `settle_win` | `(*, cursor, user_id, round_id, payout_amount, safe_picks_count, idempotency_key) -> BoxePlatformRoundSettlementResult` | Costruisce `PlatformSettleWinRequest`, chiama adapter |
| `settle_loss` | `(*, cursor, user_id, round_id, safe_picks_count) -> BoxePlatformRoundSettlementResult` | Costruisce `PlatformSettleLossRequest`, chiama adapter |
| `build_cashout_idempotency_key` | helper diretto (non fa parte dell'adapter) | |

**Eccezioni tradotte**: `PlatformRoundInsufficientBalanceError` → `BoxePlatformInsufficientBalanceError`, `PlatformRoundValidationError` → `BoxePlatformValidationError`, `TableSession*` → `BoxePlatformValidationError`.

**`round_gateway.py`**: solo re-export delle funzioni wrapper (23 righe).

---

### 1.2 HI-LO — funzioni dirette (`backend/app/modules/games/hi_lo/platform_client.py` : 188 righe)

**Pattern**: **nessun adapter**, **nessun Protocol**. Funzioni che chiamano direttamente `open_game_round`, `settle_game_round_win`, `settle_game_round_loss` dal platform service.

**Funzioni dirette esposte**:
| Funzione | Firma verso il gioco | Note |
|----------|---------------------|------|
| `open_round` | `(*, cursor, user_id, round_id, idempotency_key, bet_amount, wallet_type, title_code, site_code, table_session_id, access_session_id, request_fingerprint) -> HiLoPlatformRoundOpenResult` | Chiama **direttamente** `open_game_round(..., grid_size=52, mine_count=1, game_config_payload={"deck": "standard_52"})` |
| `settle_win` | `(*, cursor, user_id, round_id, payout_amount, successful_predictions_count, idempotency_key) -> HiLoPlatformRoundSettlementResult` | Chiama **direttamente** `settle_game_round_win(..., safe_reveals_count=successful_predictions_count)` |
| `settle_loss` | `(*, cursor, user_id, round_id, successful_predictions_count) -> HiLoPlatformRoundSettlementResult` | Chiama **direttamente** `settle_game_round_loss(..., safe_reveals_count=successful_predictions_count, record_settlement_ledger_transaction=True)` |
| `build_cashout_idempotency_key` | helper diretto | |

**Eccezioni tradotte**: `PlatformRoundInsufficientBalanceError` → `HiLoPlatformInsufficientBalanceError`, `PlatformRoundValidationError` → `HiLoPlatformValidationError`, `TableSession*` → `HiLoPlatformValidationError`.

**`round_gateway.py`**: solo re-export delle funzioni (23 righe).

**Gap rispetto a BOXE**:
- Nessuna implementazione di `PlatformGameAdapter`.
- Nessun `PlatformOpenRoundRequest` / `PlatformSettleWinRequest` — parametri passati posizionalmente/kwarg a `open_game_round`.
- `grid_size=52` e `mine_count=1` sono hard-coded nel client (mapping HI-LO → parametri platform).

---

### 1.3 Mines — class-based Protocol custom + round_gateway facade (`backend/app/modules/games/mines/platform_client.py` : 346 righe + `round_gateway.py` : 150 righe)

**Pattern**: `PlatformGameClient(Protocol)` custom + `InProcessPlatformGameClient` (implementazione). Singleton gestito da `round_gateway.py` tramite `configure_platform_game_client()` / `get_platform_game_client()`.

**Metodi del client (molti più di BOXE/HI-LO)**:
| # | Metodo | Firma | Note |
|---|--------|-------|------|
| 1 | `open_round` | `(*, cursor, user_id, game_round_id, idempotency_key, grid_size, mine_count, bet_amount, wallet_type, table_session_id, access_session_id, title_code, site_code, request_fingerprint) -> MinesPlatformRoundOpenResult` | Core — apre round platform |
| 2 | `get_existing_cashout_by_key` | `(*, cursor, idempotency_key) -> dict \| None` | Extra — lookup idempotency cashout |
| 3 | `get_cashout_snapshot` | `(*, cursor, user_id, game_round_id) -> dict \| None` | Extra — snapshot per replay cashout |
| 4 | `build_cashout_idempotency_key` | `(*, user_id, idempotency_key) -> str` | Extra — namespacing key |
| 5 | `is_open_round_idempotency_violation` | `(exc: psycopg.errors.UniqueViolation) -> bool` | Extra — check constraint open |
| 6 | `is_settlement_idempotency_violation` | `(exc: psycopg.errors.UniqueViolation) -> bool` | Extra — check constraint settlement |
| 7 | `get_round_start_snapshot` | `(*, cursor, platform_round_id) -> dict` | Extra — lettura platform round per idempotency replay |
| 8 | `settle_win` | `(*, cursor, user_id, game_round_id, payout_amount, safe_reveals_count, idempotency_key) -> MinesPlatformRoundWinResult` | Core — settle vittoria |
| 9 | `settle_loss` | `(*, cursor, user_id, game_round_id, safe_reveals_count) -> MinesPlatformRoundLossResult` | Core — settle sconfitta |

**`round_gateway.py`**: facade completa con:
- `configure_platform_game_client()` / `get_platform_game_client()` — injection pattern (Fase 9a)
- Wrapper funzione per **ogni** metodo del client (9 wrapper)

**Eccezioni tradotte**: `PlatformRoundValidationError` → `MinesValidationError`, `PlatformRoundInsufficientBalanceError` → `MinesInsufficientBalanceError`, `TableSession*` → `MinesValidationError`.

**Gap rispetto a BOXE**:
- Il Protocol custom `PlatformGameClient` **non è** `PlatformGameAdapter` (tipi request/response diversi).
- I metodi core (`open_round`, `settle_win`, `settle_loss`) usano firme flat (kwargs espliciti) invece di `PlatformOpenRoundRequest` / `PlatformSettleWinRequest`.
- Il `round_gateway` è una facade pesante (150 righe) vs re-export BOXE (23 righe).

---

## 2. INTERFACCIA typed adapter canonica (da BOXE) e allineamento

### 2.1 Interfaccia canonica (`app.modules.platform.game_modules.adapter`)

```python
@runtime_checkable
class PlatformGameAdapter(Protocol):
    def open_round(self, request: PlatformOpenRoundRequest) -> PlatformOpenRoundResult: ...
    def settle_win(self, request: PlatformSettleWinRequest) -> PlatformSettlementResult: ...
    def settle_loss(self, request: PlatformSettleLossRequest) -> PlatformSettlementResult: ...
```

**Request dataclass**:
- `PlatformOpenRoundRequest`: cursor, game_code, player_ref, game_round_ref, idempotency_key, title_code, site_code, wallet_source, bet_amount, table_session_ref, access_session_ref, request_fingerprint, game_config (Mapping), correlation_id
- `PlatformSettleWinRequest`: cursor, game_code, player_ref, game_round_ref, payout_amount, successful_steps, idempotency_key, replay_ref, correlation_id
- `PlatformSettleLossRequest`: cursor, game_code, player_ref, game_round_ref, successful_steps, replay_ref, correlation_id

**Response dataclass**:
- `PlatformOpenRoundResult`: platform_round_ref, wallet_account_ref, wallet_balance_after_start, ledger_transaction_ref, table_session_ref, table_session
- `PlatformSettlementResult`: platform_round_ref, wallet_balance_after, ledger_transaction_ref, already_exists, table_session

### 2.2 Allineamento HI-LO

| Azione | Dettaglio |
|--------|-----------|
| Creare `InProcessHiLoPlatformAdapter` | Implementa `PlatformGameAdapter` (3 metodi). Internamente chiama `open_game_round` / `settle_game_round_win` / `settle_game_round_loss` con gli stessi parametri di oggi. |
| Refactor `open_round` wrapper | Costruisce `PlatformOpenRoundRequest` e chiama `adapter.open_round()`. Ritorna `HiLoPlatformRoundOpenResult` (retro-compatibilità). |
| Refactor `settle_win` / `settle_loss` wrapper | Costruisce `PlatformSettleWinRequest` / `PlatformSettleLossRequest` e chiama adapter. |
| Mantenere `build_cashout_idempotency_key` | Rimane helper diretto (non è parte dell'adapter canonico). |
| `round_gateway.py` | Resta re-export (come BOXE). |

### 2.3 Allineamento Mines

| Azione | Dettaglio |
|--------|-----------|
| Creare `InProcessMinesPlatformAdapter` | Implementa `PlatformGameAdapter` (3 metodi: open_round, settle_win, settle_loss). Internamente chiama `open_game_round` / `settle_game_round_win` / `settle_game_round_loss` con gli stessi parametri di oggi. |
| Refactor metodi core in `platform_client.py` | `open_round`, `settle_win`, `settle_loss` diventano wrapper che costruiscono `PlatformOpenRoundRequest` / `PlatformSettleWinRequest` / `PlatformSettleLossRequest`, chiamano l'adapter, e traducono in `MinesPlatformRoundOpenResult` / `MinesPlatformRoundWinResult` / `MinesPlatformRoundLossResult`. |
| Metodi extra rimangono nel `platform_client.py` | `get_existing_cashout_by_key`, `get_cashout_snapshot`, `build_cashout_idempotency_key`, `is_open_round_idempotency_violation`, `is_settlement_idempotency_violation`, `get_round_start_snapshot` — **non fanno parte** di `PlatformGameAdapter`. Restano funzioni dirette o metodi di un helper separato. |
| `round_gateway.py` | Mantiene i wrapper per tutti i metodi (core + extra). I wrapper core delegano al `platform_client` (che ora usa l'adapter). I wrapper extra delegano alle funzioni dirette. |
| Rimuovere `PlatformGameClient(Protocol)` | Sostituito da `PlatformGameAdapter` + funzioni dirette per gli extra. |

---

## 3. Seam MONEY — come garantire ZERO cambio comportamentale

### 3.1 Vincoli invarianti

| # | Invariante | Come garantito |
|---|------------|----------------|
| 1 | **Parametri verso platform service identici** | `open_game_round`, `settle_game_round_win`, `settle_game_round_loss` ricevono ESATTAMENTE gli stessi kwargs di oggi. L'adapter estrae i campi dal dataclass request e li passa 1:1. |
| 2 | **Dataclass di ritorno identici** | `MinesPlatformRoundOpenResult`, `HiLoPlatformRoundOpenResult`, `BoxePlatformRoundOpenResult`, etc. mantengono gli stessi campi e tipi. Il wrapper fa l'unpacking da `PlatformOpenRoundResult` ai campi del dataclass specifico. |
| 3 | **Eccezioni tradotte identiche** | Gli stessi `except` blocchi di oggi rimangono nel wrapper. Nessuna nuova eccezione introdotta. |
| 4 | **`round_gateway` firme invariate** | I test e il service chiamano `round_gateway.open_round`, `round_gateway.settle_round_win`, etc. Le firme dei wrapper `round_gateway` NON cambiano. |
| 5 | **`configure_platform_game_client` Mines preservato** | L'injection Fase 9a (`configure_platform_game_client`) resta disponibile per test futuri. Il nuovo `InProcessMinesPlatformAdapter` può essere wrappato da un `PlatformGameAdapter` custom se necessario. |
| 6 | **`game_config` payload identico** | `PlatformOpenRoundRequest.game_config` riceve lo stesso dict di oggi (`{"rows": ..., "difficulty": ...}` per BOXE, `{"deck": "standard_52"}` per HI-LO, `{"grid_size": ..., "mine_count": ...}` per Mines). |

### 3.2 Rischi specifici

| Rischio | Mitigazione |
|---------|-------------|
| **R1** — `cursor` vs `connection` | BOXE adapter riceve `request.cursor` (psycopg.Cursor). HI-LO e Mines wrapper attuali ricevono `cursor`. Manteniamo `cursor` nei wrapper per retro-compatibilità. Se in futuro (post-DIV-09) si vuole passare `connection`, si farà in un refactor separato. |
| **R2** — `successful_steps` naming | `PlatformSettleWinRequest` usa `successful_steps`. Per Mines questo campo è `safe_reveals_count`. Per HI-LO è `successful_predictions_count`. Il wrapper popola `successful_steps` con il valore specifico del gioco. |
| **R3** — `settle_loss` ha `record_settlement_ledger_transaction=True` solo in HI-LO | `PlatformSettleLossRequest` NON ha questo flag. Il wrapper HI-LO `settle_loss` chiama `settle_game_round_loss` con `record_settlement_ledger_transaction=True` come oggi. L'adapter canonico non lo include perché è un dettaglio HI-LO-specifico. Il wrapper HI-LO gestisce il flag internamente. |
| **R4** — `MinesPlatformRoundLossResult` ha `safe_reveals_count` | `PlatformSettlementResult` NON ha `safe_reveals_count`. Il wrapper Mines `settle_loss` aggiunge il campo dal risultato raw di `settle_game_round_loss` dopo aver ricevuto `PlatformSettlementResult` dall'adapter. |

---

## 4. Suite gate HARD

### 4.1 Mines (242 test — stessa suite di DIV-09)

```
tests/unit/test_mines_fairness.py
tests/contract/test_mines_demo_contract.py
tests/contract/test_mines_runtime_contract.py
tests/contract/test_mines_player_session_history_contract.py
tests/contract/test_mines_admin_session_contract.py
tests/integration/test_mines_embed_browser_smoke.py
tests/integration/test_mines_reveal_cashout_optional_token.py
tests/integration/test_mines_session_history_pagination.py
tests/integration/test_mines_player_session_history.py
tests/integration/test_mines_replay.py
tests/integration/test_mines_fairness_seeded.py
tests/integration/test_mines_fairness_verify.py
tests/integration/test_mines_fairness_rotation.py
tests/integration/test_mines_backoffice_config.py
tests/integration/test_mines_admin_session_snapshot_access.py
tests/integration/test_mines_network_header_verification.py
tests/integration/test_financial_and_mines_flows.py
tests/concurrency/test_mines_concurrency.py
tests/concurrency/test_mines_fairness_rotation_concurrency.py
tests/stress/mines_math/test_mines_math_stress.py
tests/stress/mines_math/test_mines_simulator_backend_parity.py
```

### 4.2 HI-LO

```
tests/unit/test_hi_lo_math_randomness.py
tests/integration/test_hi_lo_service.py
tests/integration/test_hi_lo_admin_config.py
tests/integration/test_hi_lo_smoke.py
```

### 4.3 BOXE — non-regression

```
tests/contract/test_gmp2_boxe_adapter_contract.py
tests/integration/test_boxe_api.py
tests/integration/test_boxe_state_machine.py
tests/integration/test_boxe_fairness.py
tests/integration/test_boxe_smoke.py
tests/integration/test_boxe_lobby_launch.py
tests/integration/test_boxe_admin_config.py
tests/integration/test_boxe_admin_assets.py
tests/stress/boxe_math/test_boxe_math_stress.py
tests/stress/boxe_math/test_boxe_safe_path_stress.py
```

---

## 5. Effort e ordine micro-step

### 5.1 Principi

1. Un gioco alla volta: HI-LO prima (più semplice), poi Mines.
2. Suite verde tra i passi.
3. Nessun rename di API pubblica: `round_gateway` e i test non cambiano firme.
4. Nessuna modifica ai test: se un test fallisce, il codice è sbagliato.

### 5.2 Micro-step

#### Step 1 — HI-LO: typed adapter + wrapper refactor
**Scope**:
- Creare `InProcessHiLoPlatformAdapter` che implementa `PlatformGameAdapter`.
- Refactor `open_round`, `settle_win`, `settle_loss` in `platform_client.py` per costruire `PlatformOpenRoundRequest` / `PlatformSettleWinRequest` / `PlatformSettleLossRequest` e chiamare l'adapter.
- Mantenere `build_cashout_idempotency_key` come helper diretto.
- `round_gateway.py` resta re-export (come BOXE).

**Test gate**: HI-LO suite completa.
**Effort**: ~1h.

#### Step 2 — Mines: typed adapter + wrapper refactor
**Scope**:
- Creare `InProcessMinesPlatformAdapter` che implementa `PlatformGameAdapter` (3 metodi).
- Refactor `open_round`, `settle_win`, `settle_loss` in `platform_client.py` per usare l'adapter.
- Mantenere i metodi extra (`get_existing_cashout_by_key`, `get_cashout_snapshot`, `build_cashout_idempotency_key`, `is_open_round_idempotency_violation`, `is_settlement_idempotency_violation`, `get_round_start_snapshot`) come funzioni dirette nel `platform_client.py`.
- Aggiornare `round_gateway.py`: i wrapper core delegano al `platform_client` (che usa l'adapter), i wrapper extra delegano alle funzioni dirette.
- Rimuovere `PlatformGameClient(Protocol)` custom.
- Preservare `configure_platform_game_client()` per injection (opzionale: può ricevere un `PlatformGameAdapter` custom).

**Test gate**: Mines subset veloce (unit+contract+integration no browser).
**Effort**: ~1.5h.

#### Step 3 — Cross-game verification
**Scope**:
- Verificare che tutti e 3 i giochi usino `PlatformGameAdapter` da `app.modules.platform.game_modules.adapter`.
- Verificare che `round_gateway` di ogni gioco abbia firme invariate verso il service.
- Verificare che i dataclass di ritorno specifici (`BoxePlatformRoundOpenResult`, `HiLoPlatformRoundOpenResult`, `MinesPlatformRoundOpenResult`) mantengano gli stessi campi.

**Test gate**: BOXE non-regression + HI-LO + Mines veloci.
**Effort**: ~30min.

#### Step 4 — Gate HARD completo
**Scope**:
- Eseguire tutte le suite gate di tutti e 3 i giochi.
- Eventuali iterazioni.

**Effort**: ~1-2h.

### 5.3 Effort totale stimato

| Fase | Tempo stimato |
|------|---------------|
| Step 1 (HI-LO) | 1h |
| Step 2 (Mines) | 1.5h |
| Step 3 (Cross-verification) | 30min |
| Step 4 (Gate HARD) | 1-2h |
| **Totale** | **~4-5h** |

### 5.4 Branching consigliato

Proporre sotto-branch dedicato:
```bash
git checkout -b feature/div-10-platform-adapter-unification
```
Con merge in `feature/site-v3-cms-ia-cleanup` solo dopo gate HARD verde.
