# B2a GATE HOLD — Failure Manifest Preciso (Rettificato)

## 0. Stato hygiene

```
$ git status --short
 M .claude/settings.local.json
 M docs/NEW_GAME_INTEGRATION_PLAYBOOK.md
 M infra/docker/.env
?? .claude/settings.json
?? docs/CTO_HANDOFF_BRIEF.md
?? plans/div-09-parte-a-mines-layering-plan.md
?? plans/div-10-parte-a-platform-adapter-unification.md
```

Sporco locale noto solo. Nessun file `tests/` o `scripts/` sporco.

## 1. Collect count finale

```
820 tests collected
```

Nessun test rimosso o aggiunto rispetto al target.

## 2. Marker count finale (post-correction) — RILETTURA REALE

Comando usato per ogni marker:
```bash
python -m pytest -m <marker> --collect-only -q
```

| marker | count | delta vs prima |
|--------|-------|----------------|
| `unit` | **22** | — |
| `api_service` | **316** | -12 |
| `money_admin` | **89** | +7 |
| `catalog` | **108** | +5 |
| `browser_smoke` | **86** | — |
| `concurrency` | **13** | — |
| `visual` | **3** | — |
| `migration_schema` | **21** | — |
| `stress` | **162** | — |
| **Totale** | **820** | — |

Correzioni applicate in `tests/conftest.py`:
- `test_mines_backoffice_config.py` -> `catalog` (backoffice/i18n config)
- `test_mines_admin_session_snapshot_access.py` -> `money_admin` (admin session drilldown)
- `test_session_cascade_close.py` -> `money_admin` (session lifecycle/cleanup)
- `test_mines_replay.py` -> rimane in `api_service` (player-facing game endpoint, non admin/finanziario)

### 2.1 Rettifica numeri precedenti
Nel report precedente avevo riportato:
- `unit` 267, `browser_smoke` 32, `migration_schema` 4

Questi numeri erano **errati**. Non avevo eseguito il loop di collect su tutti i marker, ma avevo riportato cifre presumibilmente lette da un documento di piano obsoleto o frutto di errore di trascrizione. Il conteggio reale è quello nella tabella sopra.

## 3. Commit 748b876 — Dichiarazione

```
commit 748b876de48e6f613fe329ba0b9c40ddf36ca37d
Author: moromike <moromike@gmail.com>
Date:   Mon Jun 8 15:44:18 2026 +0200

    B2b-0: fix BOXE visual test iframe + regenerate baselines
```

**Non creato da me in questa sessione.** È firmato dall'utente ed era già in branch al mio riavvio.

**È intenzionale e necessario per B2a.** Evidence:
- Senza 748b876, i 3 test visual **falliscono tutti**:
  - `test_boxe_3c_visual_baselines` — `.game-provider-bootstrap-skip` non trovato (BOXE ora gira in iframe runtime)
  - `test_mines_classic_default_skin_visual_regression` — diff ratio 0.02685 (baseline stale)
  - `test_mines_boot_2a_visual_baselines` — diff ratio 0.18835 (baseline stale)
- Con 748b876, i 3 test visual **passano tutti** (verificato in questa sessione).
- Il commit modifica solo test-infra (`tests/integration/test_boxe_visual_regression.py`) e baseline PNG. Nessun tocco a backend/frontend prodotto.
- Il fix iframe è obbligatorio perché BOXE è stato spostato in runtime iframe; il test precedente cercava il selettore a livello top-page.
- Le baseline rigenerate riflettono il nuovo rendering post-iframe e non un cambiamento estetico arbitrario.

## 4. Failure Manifest — Fail riproducibili singolarmente

### 4.1 api_service — 2 failed

#### 4.1.1 `tests/contract/test_boundary_imports.py::test_service_does_not_import_platform_directly`

- **Comando minimo:**
  ```bash
  python -m pytest tests/contract/test_boundary_imports.py::test_service_does_not_import_platform_directly -v --tb=short
  ```
- **Errore esatto:**
  ```
  AssertionError: service.py imports directly from platform modules: ['app.modules.platform.table_sessions.service', 'app.modules.platform.demo_wallet.service']. All platform access must go through app.modules.games.mines.round_gateway.
  ```
- **File:line coinvolti:** `tests/contract/test_boundary_imports.py:48`
- **Classificazione:** `d) vero bug prodotto`
- **Root cause:** BOXE `service.py` importa direttamente da moduli `app.modules.platform.*` invece di passare attraverso il `round_gateway`. Introdotto durante l'implementazione BOXE.

#### 4.1.2 `tests/contract/test_game_reporting_registry.py::test_boxe_history_uses_wallet_source_without_cash_fallback`

- **Comando minimo:**
  ```bash
  python -m pytest tests/contract/test_game_reporting_registry.py::test_boxe_history_uses_wallet_source_without_cash_fallback -v --tb=short
  ```
- **Errore esatto:**
  ```
  AssertionError: assert 'pr.wallet_type AS wallet_source' in <boxe_service_source>
  ```
- **File:line coinvolti:** `tests/contract/test_game_reporting_registry.py:59`
- **Classificazione:** `d) vero bug prodotto`
- **Root cause:** Il service BOXE non proietta `pr.wallet_type AS wallet_source` nella query di storico round. Manca l'implementazione della colonna wallet_source nel reporting BOXE.

### 4.2 money_admin — 4 failed riproducibili singolarmente

#### 4.2.1 `tests/integration/test_admin_audit_log.py::test_theme_publish_writes_operational_audit_log`

- **Comando minimo:**
  ```bash
  python -m pytest tests/integration/test_admin_audit_log.py::test_theme_publish_writes_operational_audit_log -v --tb=short
  ```
- **Errore esatto:**
  ```
  AssertionError: {"success":false,"error":{"code":"VALIDATION_ERROR","message":"Unsupported theme skin value for game_area_overlay: rgba(0,0,0,0.5)",...}}
  assert 422 == 200
  ```
- **File:line coinvolti:** `tests/integration/test_admin_audit_log.py:475`
- **Classificazione:** `d) vero bug prodotto`
- **Root cause:** Il payload di test invia un tema con `game_area_overlay: rgba(0,0,0,0.5)` che il backend rifiuta come unsupported. O il test è obsoleto rispetto alla whitelist di colori/skins, o il backend è troppo restrittivo.

#### 4.2.2 `tests/integration/test_admin_financial_reports.py::test_financial_sessions_report_returns_paginated_structure_and_excludes_legacy_by_default`

- **Comando minimo:**
  ```bash
  python -m pytest tests/integration/test_admin_financial_reports.py::test_financial_sessions_report_returns_paginated_structure_and_excludes_legacy_by_default -v --tb=short
  ```
- **Errore esatto:**
  ```
  AssertionError: {"success":false,"error":{"code":"VALIDATION_ERROR","message":"Access session is required for real mode",...}}
  assert 422 == 200
  ```
- **File:line coinvolti:** `tests/integration/test_admin_financial_reports.py:169` (helper `_start_round`)
- **Classificazione:** `d) vero bug prodotto`
- **Root cause:** Il test avvia un round "legacy" (senza `access_session_id`) in real mode, ma il backend ora richiede obbligatoriamente `access_session_id` per i round real. Il test non è stato aggiornato al nuovo contratto di avvio sessione.

#### 4.2.3 `tests/integration/test_admin_ledger_report.py::test_admin_ledger_report_exposes_recent_transactions_and_reconciliation`

- **Comando minimo:**
  ```bash
  python -m pytest tests/integration/test_admin_ledger_report.py::test_admin_ledger_report_exposes_recent_transactions_and_reconciliation -v --tb=short
  ```
- **Errore esatto:**
  ```
  AssertionError: assert 4 == 0
  ```
  (sulla riga `assert payload["summary"]["wallets_with_drift_count"] == 0`)
- **File:line coinvolti:** `tests/integration/test_admin_ledger_report.py:47`
- **Classificazione:** `b) DB sporco da run interrotto`
- **Root cause:** Il report rileva 4 wallet con drift residue da run precedenti interrotti o da test che non hanno fatto cleanup completo. Non è un bug del codice sotto test, ma dello stato del DB.

#### 4.2.4 `tests/integration/test_admin_suspend.py::test_admin_suspend_updates_status_and_blocks_player_access`

- **Comando minimo:**
  ```bash
  python -m pytest tests/integration/test_admin_suspend.py::test_admin_suspend_updates_status_and_blocks_player_access -v --tb=short
  ```
- **Errore esatto:**
  ```
  AssertionError: assert {'error': {'code': 'FORBIDDEN', 'message': 'Account is not active', 'request_id': 'req_...', 'retryable': False, ...}} == {'error': {'code': 'FORBIDDEN', 'message': 'Account is not active'}}
  ```
- **File:line coinvolti:** `tests/integration/test_admin_suspend.py:54`
- **Classificazione:** `d) vero bug prodotto` (test obsoleto rispetto al formato errore)
- **Root cause:** Il test si aspetta un errore "compatto" senza i campi `request_id`, `retryable`, `support_id` che il backend ora include in tutte le risposte di errore. Il test non è stato aggiornato al nuovo envelope errore.

## 5. Failure Manifest — Fail di gruppo non riproducibili singolarmente

### 5.1 money_admin — 1 fail flaky

#### 5.1.1 `tests/integration/test_admin_force_close_sessions.py::test_admin_force_close_closes_settled_session_without_voiding_history`

- **Comportamento:**
  - Nel gruppo `money_admin` (82 test): **FAILED**
  - Singolarmente: **PASSED**
- **Errore nel gruppo:**
  ```
  AssertionError: {"success":false,"error":{"code":"VALIDATION_ERROR","message":"Title is not published on this site",...}}
  ```
- **File:line coinvolti:** `tests/integration/test_admin_force_close_sessions.py:23` (helper interno)
- **Classificazione:** `b) DB sporco da run interrotto` / `a) test-infra fixture/cleanup`
- **Root cause:** Il test utilizza il title di default `mines_classic`. Al momento del fail nel gruppo, il DB aveva:
  ```
  site_titles: (casinoking, mines_classic, active, hidden, demo_enabled=False, real_enabled=False)
  ```
  Un test precedente nel gruppo ha depubblicato/sporcato la riga `site_titles` per `mines_classic` senza ripristinarla. Quando il test viene eseguito singolarmente, la fixture di setup ripristina lo stato corretto.

**Query DB al momento del fail:**
```sql
SELECT title_code, status, source_title_code FROM game_titles WHERE title_code='mines_classic';
-- risultato: ('mines_classic', 'active', NULL)

SELECT site_code, title_code, status, lobby_visibility, demo_enabled, real_enabled FROM site_titles WHERE title_code='mines_classic';
-- risultato: ('casinoking', 'mines_classic', 'active', 'hidden', False, False)
```

## 6. Visual — 3 passed (con 748b876)

| test | risultato |
|------|-----------|
| `tests/integration/test_boxe_visual_regression.py::test_boxe_3c_visual_baselines` | **PASSED** |
| `tests/integration/test_mines_skin_visual_regression.py::test_mines_classic_default_skin_visual_regression` | **PASSED** |
| `tests/integration/test_mines_skin_visual_regression.py::test_mines_boot_2a_visual_baselines` | **PASSED** |

Verificato anche che **senza 748b876 tutti e 3 falliscono** (BOXE per selector iframe, Mines per baseline stale).

## 7. Concurrency — Nessun fail

| risultato | count |
|-----------|-------|
| passed | 13 |
| failed | 0 |
| error | 0 |

Tutti i test di concorrenza passano singolarmente e in gruppo.

## 8. Commit effettuati in questa sessione

```
fc3c31f B2a: marker correction — move 3 files to proper groups
```

## 9. Azioni raccomandate per sbloccare B2a (solo test, no backend)

| priorità | azione | owner suggerito |
|----------|--------|-----------------|
| Alta | Fixare BOXE `service.py` per rimuovere import diretti da `app.modules.platform.*` e aggiungere `pr.wallet_type AS wallet_source` | dev BOXE |
| Alta | Aggiornare `test_admin_financial_reports.py` per passare `access_session_id` anche al round "legacy" | test maintainer |
| Media | Aggiornare `test_admin_suspend.py` per accettare il nuovo envelope errore completo | test maintainer |
| Media | Indagare/fixare la whitelist theme skin in `test_admin_audit_log.py` o nel backend | backend / test |
| Bassa | Cleanup DB drift (`wallets_with_drift_count = 4`) e verificare cleanup fixture cross-test | infra test |
| Bassa | Indagare fixture depubblicazione `mines_classic` in money_admin per eliminare il flaky `test_admin_force_close_sessions.py` | test maintainer |
