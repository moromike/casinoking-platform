# DIV-02 Parte-A — Design: Mines Opzione B (demo path-unico, via tabelle/funzioni demo bespoke)

**Stato:** read-only / design gate CTO  
**Esecutore:** KIMI  
**Data:** 2026-06-05  
**Scope:** solo analisi e piano; nessuna modifica al codice.

---

## 1. Mappa dello stato attuale (demo Mines)

### 1.1 Schema DB (migration `0027__demo_sessions.sql`)

| Tabella | Scopo | Relazioni |
|---------|-------|-----------|
| `demo_play_sessions` | Sessione demo condivisa (anon_id, balance, title) | FK `game_titles(title_code)` |
| `demo_round_events` | Eventi wallet demo (bet/win/loss) per sessione | FK `demo_play_sessions(id)`, unique `(demo_play_session_id, idempotency_key)` |
| `demo_mines_game_rounds` | **Tabella demo bespoke di Mines**. Stato board completo (mine positions, revealed cells, multipliers, status `active/won/lost/cancelled`) | FK `demo_play_sessions(id)`, unique `(anonymous_id, idempotency_key)` |

Il round reale di Mines vive invece in `mines_game_rounds` (migration `0012` e successive) con FK a `platform_rounds`.

### 1.2 Funzioni demo separate in `mines/service.py`

| Funzione | Riga | Note |
|----------|------|------|
| `start_demo_session` | 169 | Apre `demo_play_session`, chiama `DemoPlatformGameClient.open_round`, inserisce in `demo_mines_game_rounds` |
| `reveal_demo_cell` | 1122 | Legge `demo_mines_game_rounds`, applica logica reveal, chiama `DemoPlatformGameClient.settle_loss` se mine, altrimenti aggiorna stato demo round |
| `cashout_demo_session` | 1238 | Legge `demo_mines_game_rounds`, chiama `DemoPlatformGameClient.settle_win`, chiude round demo |
| `get_demo_session_for_anonymous` | 1343 | Legge `demo_mines_game_rounds` per stato sessione |
| `get_demo_session_replay_for_anonymous` | 668 | Legge `demo_mines_game_rounds` per replay demo (incl. mine positions se chiuso) |
| `get_demo_session_fairness_for_anonymous` | 1411 | Legge fairness da `demo_mines_game_rounds` |
| `demo_session_exists` | 1458 | Check esistenza su `demo_mines_game_rounds` |

Helper privati demo (circa 10 funzioni, righe 1598–2180 circa): `_insert_demo_mines_game_round`, `_close_demo_game_round_as_lost`, `_close_demo_game_round_as_won`, `_update_demo_game_round_after_safe_reveal`, `_get_demo_session_for_update`, `_get_existing_demo_session_by_idempotency`, `_build_demo_cashout_response_from_existing`, `_demo_start_response_from_existing`, ecc.

### 1.3 Client demo: `DemoPlatformGameClient` (`mines/platform_client.py:357`)

Implementa la stessa interfaccia del client real (`InProcessPlatformGameClient`) ma parla al **demo wallet** invece che a ledger/platform rounds:

| Metodo | Riga | Scopo |
|--------|------|-------|
| `open_round` | 363 | `open_demo_session` + `debit_for_bet` (demo wallet) |
| `settle_win` | 520 | `credit_for_win` (demo wallet) |
| `settle_loss` | 558 | `record_loss` (demo wallet) |
| `get_existing_cashout_by_key` | 421 | Idempotency cashout su `demo_round_events` |
| `build_cashout_idempotency_key` | 467 | `mines:demo:cashout:{user_id}:{key}` |
| `get_round_start_snapshot` | 491 | Legge ultimo evento `bet` della demo session |
| `is_open_round_idempotency_violation` | 471 | Sempre `False` (idempotency gestita dal demo wallet) |
| `is_settlement_idempotency_violation` | 481 | Sempre `False` |

### 1.4 Router demo (`mines.py`)

Il router ha **due path** per ogni azione (token e token-less B3), e in ognuno un **branch demo separato**:

- **Start**: demo branch a `417-455` (token) e `547-583` (token-less)
- **Reveal**: demo branch a `669-697` (token) e `752-780` (token-less)
- **Cashout**: demo branch a `845-873` (token) e `925-953` (token-less)
- **Replay**: demo branch a `1008-1028` (token) e `1065-1085` (token-less)
- **Session**: demo branch a `1156-1176` (token) e `1214-1234` (token-less)
- **Fairness**: demo branch a `1299-1319` (token) e `1356-1376` (token-less)

Il demo branch rifiuta esplicitamente `access_session_id` (422) e chiama le funzioni `*_demo_*` del service.

### 1.5 Idempotency demo attuale

- **Start**: unique index su `demo_mines_game_rounds(anonymous_id, idempotency_key)` + check `request_fingerprint` (service.py:205-215).
- **Reveal**: nessuna idempotency key esplicita; protezione tramite `FOR UPDATE` + check cella già rivelata.
- **Cashout**: idempotency su `demo_round_events(demo_play_session_id, idempotency_key)` via `DemoPlatformGameClient.get_existing_cashout_by_key`.

### 1.6 Replay / history demo

- **Replay**: `GET /games/mines/session/{session_id}/replay` chiama `get_demo_session_replay_for_anonymous`, che legge **direttamente da `demo_mines_game_rounds`** (service.py:675-710). Costruisce il payload con `_build_session_replay_payload` e aggiunge `mode="demo"`.
- **History paginata**: **non esiste** un endpoint di lista demo per Mines. `GET /games/mines/sessions` è real-only (`platform_rounds`). `GET /games/mines/access-sessions/latest` è real-only (`game_access_sessions`).

### 1.7 Frontend demo Mines

Il frontend `mines-standalone.tsx` distingue demo vs real e passa `wallet_type="demo"` / `wallet_source="demo"`. Non c'è una history paginata demo specifica nel backend; se il frontend mostra storico demo, lo fa client-side o non è previsto.

---

## 2. Target canonico (pattern HI-LO / BOXE post-DIV-01/DIV-05)

### 2.1 Schema target

Una sola tabella `mines_game_rounds` con:
- `platform_round_id uuid NULL` (per real)
- `demo_session_id uuid NULL REFERENCES demo_play_sessions(id)` (per demo)
- `access_session_id uuid NULL` (per real)
- `table_session_id uuid NULL` (per real)

**Drop tabella `demo_mines_game_rounds`** e tutti i suoi indici.

### 2.2 Path unico target

Una sola funzione per azione nel service, con branch interno:

```python
if wallet_source == "demo":
    demo_session = open_demo_session(...)
    demo_session = debit_for_bet(...)
    # crea round in mines_game_rounds con demo_session_id
else:
    platform_open = open_platform_round(...)
    # crea round in mines_game_rounds con platform_round_id
```

Esempi canonici già lockati:
- **HI-LO**: `hi_lo/service.py:122-287` (start unico con branch demo a 195-213)
- **BOXE**: `boxe/service.py:145-300` (start unico con branch demo a 224-250)

### 2.3 Idempotency target

Tabella dedicata `mines_idempotency_keys` (come `boxe_idempotency_keys` e `hi_lo_idempotency_keys`):
- `player_id uuid NOT NULL REFERENCES users(id)`
- `round_id uuid NULL REFERENCES mines_game_rounds(id) ON DELETE CASCADE`
- `operation`, `idempotency_key`, `request_fingerprint`, `response_json`
- Unique `(player_id, operation, idempotency_key)`

### 2.4 Replay / history target

- **Replay**: unico endpoint che legge da `mines_game_rounds` (indipendentemente da `demo_session_id` o `platform_round_id`).
- **History real**: `game_access_sessions` + `platform_rounds` (già esistente).
- **History demo**: nessuna tabella demo bespoke; se in futuro servirà una lista demo, si farà filtrando `mines_game_rounds` per `demo_session_id IS NOT NULL` (come BOXE/HI-LO).

---

## 3. Piano puntuale per file

### 3.1 Migration (`backend/migrations/sql/0049__mines_demo_unify.sql` — numero successivo)

1. **Drop `demo_mines_game_rounds`** e i suoi indici (`idx_demo_mines_game_rounds_anon_idempotency`, `idx_demo_mines_game_rounds_anon_created`).
2. **Aggiungi `demo_session_id` a `mines_game_rounds`**:
   ```sql
   ALTER TABLE mines_game_rounds
       ADD COLUMN IF NOT EXISTS demo_session_id uuid NULL REFERENCES demo_play_sessions(id);
   CREATE INDEX IF NOT EXISTS idx_mines_game_rounds_demo_session_id
       ON mines_game_rounds(demo_session_id) WHERE demo_session_id IS NOT NULL;
   ```
3. **Aggiungi `access_session_id` e `table_session_id` a `mines_game_rounds`** (se mancanti; verificare schema attuale). BOXE/HI-LO ce li hanno direttamente sulla round table.
4. **Crea `mines_idempotency_keys`** (pattern HI-LO/BOXE):
   ```sql
   CREATE TABLE mines_idempotency_keys (
       id uuid PRIMARY KEY,
       player_id uuid NOT NULL REFERENCES users(id),
       round_id uuid NULL REFERENCES mines_game_rounds(id) ON DELETE CASCADE,
       operation varchar(32) NOT NULL,
       idempotency_key varchar(128) NOT NULL,
       request_fingerprint varchar(128) NOT NULL,
       response_json jsonb NOT NULL,
       created_at timestamptz NOT NULL DEFAULT now(),
       expires_at timestamptz NULL,
       CONSTRAINT mines_idempotency_keys_operation_check
           CHECK (operation IN ('start_round', 'reveal', 'cashout', ...)),
       CONSTRAINT mines_idempotency_keys_player_operation_key
           UNIQUE (player_id, operation, idempotency_key)
   );
   CREATE INDEX idx_mines_idempotency_keys_round ON mines_idempotency_keys(round_id) WHERE round_id IS NOT NULL;
   ```

### 3.2 `backend/app/modules/games/mines/service.py`

**Rimuovere** le seguenti funzioni demo separate:
- `start_demo_session` (riga 169)
- `reveal_demo_cell` (riga 1122)
- `cashout_demo_session` (riga 1238)
- `get_demo_session_for_anonymous` (riga 1343)
- `get_demo_session_replay_for_anonymous` (riga 668)
- `get_demo_session_fairness_for_anonymous` (riga 1411)
- `demo_session_exists` (riga 1458)
- Tutti i helper privati demo (righe 1598–2180 circa)

**Modificare** le funzioni real esistenti (o crearne uniche se non esistono):
- `start_round` (o funzione equivalente real): aggiungere branch demo con `open_demo_session` + `debit_for_bet` (come HI-LO `service.py:195-213`).
- `reveal_cell`: aggiungere branch demo che chiama `credit_for_win`/`record_loss` via demo wallet (come HI-LO reveal/cashout).
- `cashout_round`: aggiungere branch demo che chiama `credit_for_win`.
- `get_session` / `get_replay`: unificare per leggere da `mines_game_rounds` e restituire payload indipendentemente da real/demo.

**Aggiungere** idempotency unificata:
- `save_idempotency_result` e `get_idempotency_result` in un nuovo `mines/repository.py` (o modulo dedicato), pattern HI-LO.

### 3.3 `backend/app/modules/games/mines/platform_client.py`

**Rimuovere** `DemoPlatformGameClient` (riga 357 in poi). Tutta la logica demo wallet viene gestita inline nel service (come BOXE/HI-LO).

Il client real (`InProcessPlatformGameClient`) resta invariato.

### 3.4 `backend/app/api/routes/mines.py`

**Unificare** i branch demo e real:
- Per ogni endpoint (start, reveal, cashout, replay, session, fairness), rimuovere il ramo `if mode == "demo":` o `if wallet_source == "demo":` che chiama le funzioni demo separate.
- Il router deve passare `wallet_source`/`wallet_type` al service unico, che internamente fa il branch.
- I due path (token e token-less) restano, ma entrambi chiamano la **stessa** funzione service.

### 3.5 Frontend (`frontend-v3/app/ui/mines/`)

Verificare che il frontend:
1. Non faccia assumzioni sulla struttura della risposta demo vs real (es. campi specifici di `demo_mines_game_rounds`).
2. Passi `wallet_source="demo"` correttamente.
3. Non chiami endpoint demo-specifici (non ce ne sono, il contract URL è lo stesso).

**Atteso:** nessuna modifica necessaria se il contract API resta invariato. Da verificare in Parte B.

### 3.6 Test

**Rimuovere** test che:
- Verificano esplicitamente la presenza di `demo_mines_game_rounds` nel DB.
- Testano le funzioni demo separate in isolamento.

**Aggiornare** test che:
- Fanno start demo: ora devono verificare che il round venga creato in `mines_game_rounds` con `demo_session_id` valorizzato e `platform_round_id` NULL.
- Verificano replay demo: ora leggono da `mines_game_rounds`.
- Verificano idempotency demo: ora usano `mines_idempotency_keys`.
- Verificano demo wallet balance: usano `demo_play_sessions` (già così, ma il round è in `mines_game_rounds`).

---

## 4. Gotcha / rischi

### 4.1 Replay demo Mines — board state e mine positions

**Problema:** `demo_mines_game_rounds` contiene `mine_positions_json` e `revealed_cells_json` inline. `mines_game_rounds` (tabella real) ha un formato diverso? Verificare se `mines_game_rounds` ha già colonne per board state, o se il replay real si appoggia a `mines_reveals` + calcolo.

**Soluzione:** prima di droppare `demo_mines_game_rounds`, verificare che `mines_game_rounds` possa ospitare tutti i campi necessari al replay demo. Se `mines_game_rounds` ha già `mine_positions_json`, `revealed_cells_json`, `status`, `multiplier_current`, `payout_current`, allora è sufficiente popolarli anche per demo. Se mancano colonne, aggiungerle nella migration.

**Azione di verifica (prima del gate):** confrontare `SELECT column_name FROM information_schema.columns WHERE table_name = 'mines_game_rounds'` con i campi usati da `_build_session_replay_payload` in `service.py`.

### 4.2 Idempotency reveal demo

**Problema:** attualmente reveal demo non ha idempotency key esplicita; si affida a `FOR UPDATE` + check cella già rivelata. Nel pattern HI-LO/BOXE, reveal ha idempotency key passata dal frontend e salvata in `*_idempotency_keys`.

**Soluzione:**
- Opzione A: aggiungere idempotency key al reveal Mines (come HI-LO/BOXE). Richiede che il frontend la passi (verificare se già la passa).
- Opzione B: mantenere il meccanismo esistente (no idempotency key reveal, solo `FOR UPDATE`) e non salvare il reveal in `mines_idempotency_keys`.

**Raccomandazione:** Opzione A per uniformità cross-game, ma solo se il frontend già passa `Idempotency-Key` sul reveal Mines. Da verificare in `mines-standalone.tsx`.

### 4.3 History demo / lista sessioni

**Problema:** oggi non c'è endpoint di lista demo per Mines. Dopo l'unificazione, il real history continua a funzionare su `platform_rounds`. Il demo history non è esposto.

**Soluzione:** per ora nessuna modifica; se in futuro servirà, si aggiungerà un filtro su `mines_game_rounds WHERE demo_session_id IS NOT NULL`. Questo è coerente con HI-LO/BOXE.

### 4.4 Cashout idempotency demo — cambio namespace

**Problema:** oggi `DemoPlatformGameClient.build_cashout_idempotency_key` genera `mines:demo:cashout:{user_id}:{key}`. Dopo l'unificazione, il cashout demo userà `credit_for_win` con una key gestita dal service (come BOXE `boxe:cashout:{round_id}:{key}`).

**Soluzione:** usare key deterministiche del tipo `mines:cashout:{round_id}:{idempotency_key}` (come HI-LO/BOXE). Il demo wallet interno gestirà il conflitto se la stessa key viene riusata.

### 4.5 Token demo vs real

**Problema:** il token path (`/games/mines/launch-token`) per demo genera un token con `mode="demo"`. Dopo l'unificazione, il token demo dovrebbe ancora essere valido? In HI-LO/BOXE, il launch token è **solo per real**; demo non usa token (il frontend non lo passa).

**Soluzione:** Mantenere il token demo se il frontend lo usa, oppure allineare a HI-LO (token solo real). Da verificare se `mines-standalone.tsx` richiede token per demo.

### 4.6 Concorrenza / race condition

**Problema:** il reveal demo attuale usa `FOR UPDATE` su `demo_mines_game_rounds`. Dopo l'unificazione, il reveal unico userà `FOR UPDATE` su `mines_game_rounds`. Verificare che `mines_game_rounds` abbia la stessa granularità di lock (per riga) e che non ci siano deadlock con altre tabelle.

---

## 5. Conferma: path REAL invariato

Il path real Mines subisce **zero modifiche comportamentali**:
- `open_platform_round` continua a funzionare identico.
- `mines_game_rounds` continua a ospitare i round real con `platform_round_id` valorizzato.
- `platform_rounds`, ledger, wallet reale, `game_access_sessions`, `game_table_sessions` non vengono toccati.
- L'unico cambiamento su `mines_game_rounds` è l'aggiunta della colonna nullable `demo_session_id`, che non influenza i round real.

---

## 6. Effort + ordine micro-step

### Effort stimato

- **Migration + schema**: S (1 file SQL, ~30 righe)
- **Service unificazione (drop funzioni demo, branch unico)**: L (~400-700 righe tra rimozioni e modifiche)
- **Platform client (drop DemoPlatformGameClient)**: S (~100 righe rimosse)
- **Router unificazione**: M (~150-250 righe, rimozione branch demo)
- **Idempotency (nuova tabella + repository)**: M (~100-200 righe)
- **Test aggiornamento**: M/L (~200-400 righe, rimozione test obsoleti + nuovi assert)
- **Frontend verifica**: S (read-only, verifica tsc)

**Totale stimato**: **L** (600-1000 righe nette, come da audit originale).

### Ordine micro-step (sequenziale, gate CTO dopo ogni blocco)

| # | Step | File principali | Criterio gate |
|---|------|-----------------|---------------|
| 1 | Migration: drop `demo_mines_game_rounds`, add `demo_session_id` a `mines_game_rounds`, crea `mines_idempotency_keys` | `0049__mines_demo_unify.sql` | Schema up/down OK; `mines_game_rounds` ha tutte le colonne necessarie per replay demo |
| 2 | Repository idempotency + round read/write unificati | `mines/repository.py` (nuovo o esistente) | Test repository isolati verdi |
| 3 | Service: unificare start/reveal/cashout con branch demo, rimuovere funzioni demo | `mines/service.py` | Test demo start+reveal+cashout verdi; balance demo corretto |
| 4 | Platform client: rimuovere `DemoPlatformGameClient` | `mines/platform_client.py` | Zero ref a `DemoPlatformGameClient` nel codice |
| 5 | Router: unificare branch demo/real | `mines.py` | Contract API invariato; demo e real respondono OK |
| 6 | Replay/history/fairness unificati | `mines/service.py` + router | Replay demo e real funzionanti; mine positions corrette |
| 7 | Test suite: rimuovere test obsoleti, aggiungere assert unificati | `tests/integration/test_mines*.py` | Suite Mines verde (incl. demo + real + replay) |
| 8 | Frontend check | `frontend-v3/` | `tsc --noEmit` OK; nessuna modifica necessaria o fix minimi |

---

## 7. Verifiche pre-gate da fare in Parte B (esecuzione)

Prima di scrivere codice, il CTO deve decidere:

1. **Colonne `mines_game_rounds`:** confermare che `mines_game_rounds` abbia già tutti i campi necessari a ospitare lo stato demo (mine positions, revealed cells, multiplier ladder, status). Se mancano, quali aggiungere?
2. **Idempotency reveal:** il frontend Mines passa già `Idempotency-Key` sul reveal? Se no, aggiungiamo idempotency reveal o manteniamo il meccanismo attuale?
3. **Launch token demo:** il frontend richiede token demo per Mines? Se sì, manteniamo; se no, allineiamo a HI-LO (token solo real).
4. **Backfill dati:** il DB è disposable (pre-beta), quindi nessun backfill necessario. Confermare.

---

*Fine documento design. STOP CTO. Niente codice fino a approvazione piano.*
