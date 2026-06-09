Status: ACTIVE
Last meaningful update: 2026-05-25

# CTO Review - WP-FINANCE-REPLAY-REGISTRY-RETENTION

Documento sorgente:
`docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md`
Documento companion:
`docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md`

## 1. Verdetto CTO

**APPROVE WITH MANDATORY CORRECTIONS AND SCOPE RECONCILIATION.**

L'analisi è la più importante delle 4 in termini di rischio business e
prerequisito a COINS. Diagnosi solida: verificato in codice che
`admin-finance-panel.tsx:614-625` fa fallback BOXE per qualunque
`game_code != "hi_lo"`, `player-account-page.tsx:1636-1643` fa fallback Mines
per qualunque `game_code != "boxe" && != "hi_lo"`,
`access_sessions/service.py:577-605` ha branching esplicito Mines/BOXE/HI-LO
per auto-settlement, `rounds/service.py:399-403` scrive settlement metadata
solo con `game_code + safe_reveals_count` (concettualmente Mines-shaped per
tutti i giochi).

Tutte le claim chiave del brief sono validate in codice da CTO Claude.

**Issue di scope-reconciliation:** questo WP **sovrappone parzialmente** con
il `WP-FINANCE-REPLAY-ACCOUNT-REGISTRY` che CTO Claude ha scritto stasera per
COINS (prompt Codex in
`docs/games/coins/PROMPT_CODEX_WP_FINANCE_REPLAY_REGISTRY_2026-05-25.md`).
Va riconciliato come UN solo WP. Vedi sezione 13.

5 correzioni obbligatorie + 3 raccomandate sotto.

## 2. Sintesi non-tecnica (per Michele)

Questo è il WP più delicato per il business. Tocca come la piattaforma
**spiega i soldi**: chi ha vinto cosa, perché la balance è cambiata di X
euro, quale gioco ha generato la transazione. Oggi tre cose vanno male e
diventano disastrose al quarto gioco:

1. **Replay sbagliato:** se un domani aggiungiamo COINS senza fixare questo,
   il pulsante "Replay" su admin finance per un round COINS aprirà il replay
   di BOXE (bug silenzioso). Stesso bug per il player: replay di un gioco
   sconosciuto apre il replay di Mines.
2. **Metadata Mines-shaped:** ogni transazione di ledger ha un campo
   `safe_reveals_count` che ha senso solo per Mines, ma è scritto per tutti
   i giochi. BOXE non ha "reveals", ha "picks". HI-LO ha "predictions".
3. **Settlement implicito:** il sistema sa fare auto-cashout su disconnect
   ma con codice hardcoded per Mines/BOXE/HI-LO. Aggiungere COINS = aggiungere
   un quarto if-branch, esattamente quello che Rule 18 del playbook vieta.

Soluzione: registry che ogni gioco compila. Niente più "if game === ...".
Niente più fallback implicito. Forward-only metadata (non riscriviamo la
storia). No auto-repair (no fix automatici a transazioni passate).

Costo: alto. Benefici: enormi. È prerequisito reale a COINS, non opzionale.

## 3. Cosa è solido nell'analisi

| Area | Verdetto CTO |
| --- | --- |
| Diagnosi 22 punti file:line | Verificata. Spot-check su 5 punti, tutti corretti. |
| Rule 18 (Playbook) compliance: registry obbligatorio per game 4+ | ✅ Centrale. |
| Unknown game = "Replay unavailable", no fallback | ✅ Allineato a tua direttiva 2026-05-25 ("nessun debito"). |
| Forward-only metadata, no rewrite history | ✅ Conservativo. Corretto. |
| No auto-repair | ✅ Auto-repair su soldi è rischio alto. |
| Settlement taxonomy 7 valori (`manual_cashout`, `auto_cashout`, `refund_no_progress`, `loss`, `admin_void`, `expired_no_settlement`, `quarantined`) | ✅ Coerente con Rule 22 playbook e auto-settle attuale `access_sessions/service.py:649-820`. |
| Slice F1-F5 (registry+fallback removal → Mines admin parity → metadata forward → retention doc → reconciliation report) | ✅ Sequenza giusta. |
| BOXE wallet_type forced `cash` bug identificato | ✅ Importante - bug product-visible. |
| Mines player history fallback identificato (`player-game-registry.ts:27-29`) | ✅ Importante - data quality. |
| Cross-link a `GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md` | ✅ Quel doc è il contratto reference. |

## 4. Correzioni obbligatorie (Parte A deve risolverle)

### 4.1 Reconciliazione scope con prompt COINS WP-FINANCE-REPLAY-ACCOUNT-REGISTRY

Vedi sezione 13. Decisione CTO: il prompt COINS è un **subset** di questo WP.
Cancellare il prompt COINS dedicato e usare questo come unico WP. Parte A
deve aggiornare:

- `docs/games/coins/PROMPT_CODEX_WP_FINANCE_REPLAY_REGISTRY_2026-05-25.md` →
  marcare SUPERSEDED, redirigere a questo WP;
- `docs/ACTIVE_OPEN_LOOPS.md` riga COINS → riferimento aggiornato;
- `docs/games/coins/COINS_OPEN_QUESTIONS_2026-05-25.md` sezione N1 →
  riferimento aggiornato.

### 4.2 Slice F2 (Mines admin replay parity) - verifica backend prima

Brief Slice F2 dice "wire Mines admin replay viewer into admin finance" e
cita `backend/app/api/routes/mines.py:801` come backend endpoint esistente.

**Verifica obbligatoria in Parte A:**

- l'endpoint Mines admin replay esiste effettivamente in
  `backend/app/api/routes/mines.py`?
- ritorna lo stesso shape di BOXE/HI-LO admin replay?
- include `server_seed` come da contratto?

Se no, F2 si espande backend-side. Codex deve dichiarare lo scope reale dopo
verifica.

### 4.3 BOXE wallet_type bug: trattamento esplicito

`frontend/app/ui/player-account-page.tsx:1581-1587` forza `wallet_type: cash`
per BOXE history. Brief Slice F1 lo cita come "BOXE history adapter marks
it legacy/unknown, not silently cash".

**Decisione CTO obbligatoria:**

- WP corregge questo? O lo annota come fix separato?
- Se corregge: backend `backend/app/modules/games/boxe/service.py:647-904`
  deve esporre `wallet_source` esplicito. Migration + backfill?
- Se annota: il fix va in WP-BOXE-WALLET-SOURCE-EXPOSURE separato.

Proposta CTO Claude: **correggere in questo WP** (è dentro la finestra
forward-metadata). Backend BOXE espone `wallet_source`, frontend usa quello
invece di forzare cash. No migration storica - se BOXE history pre-fix non
ha wallet_source, mostra "legacy / unknown" come da brief.

### 4.4 `settlement_kind` location decision esplicita

Brief sezione "Stop-Before-Code Decisions" del packet dice "Start in
forward-only ledger metadata; decide later if platform_rounds column needed".

**Decisione CTO MVP:** **solo ledger metadata JSON**. Niente column su
`platform_rounds` in MVP. Reasoning:

- query performance OK per finance drilldown (ledger detail già usa metadata);
- column su `platform_rounds` richiede migration + backfill, fuori scope
  forward-only;
- se in futuro reporting volume cresce, WP separato aggiunge column con
  trigger sync da metadata.

Parte A conferma e Parte B implementa solo metadata.

### 4.5 Registry "metadata_completeness" semantica

Brief descriptor include `metadata_completeness`. Manca enum esplicito.

**Decisione CTO:** valori MVP:

- `complete` = tutti i campi del forward contract (game_code, title_code,
  site_code, wallet_type, platform_round_id, game_round_id, access_session_id,
  settlement_kind, idempotency_key_hash, replay_ref, metadata_schema_version)
  presenti;
- `partial` = mancano alcuni opzionali (es. game_round_id == platform_round_id);
- `legacy` = pre-fix, no metadata_schema_version, alcuni campi assenti
  (ledger pre-existente).

Admin finance detail mostra il badge `metadata_completeness` per ogni row.

## 5. Correzioni raccomandate

### 5.1 Reconciliation report (Slice F5) - definire trigger

Slice F5 descrive 4 anomalie da reportare:
- bet ledger without round;
- terminal round without expected settlement;
- replay missing for terminal real-money round;
- unknown game descriptor.

Manca trigger: questa query gira on-demand (admin clicca) o batch (notturna)?

Proposta CTO: **on-demand admin only** in MVP. Batch in WP separato post-MVP
quando logging foundation di WP2 esiste.

### 5.2 Retention policy MVP - allinea con tua decisione 2026-05-25

Tua decisione di stasera: "memorizzare replay ultimi 30 giorni online,
routine giornaliera storicizza i più vecchi; parte finanziaria persistente
sempre" (Q10 / sezione M2 del doc COINS).

Brief Slice F4 dice "document replay retention policy; expose read-only
status in Platform Settings later; no deletion job until legal/product
approves".

**Allinea:** Parte A produce documento policy:

- replay retention online: **30 giorni** (rolling window);
- replay retention cold storage: **TBD by legal** (probabilmente 5 anni AAMS
  per real-money);
- ledger retention (finanziario): **forever** in MVP, decisione legal future;
- deletion job: **NON in MVP**. Policy documentata, deletion implementata
  solo dopo approvazione product/legal.

Slice F4 produce SOLO doc + read-only status. Deletion = WP separato.

### 5.3 Test gates: aggiungere regression test fallback Mines

Brief test gates sono completi tranne uno:

- regression test: dato un round con `game_code = "future_game_x"`, il sistema
  NON deve mostrare replay Mines/BOXE/HI-LO né chiamare quegli endpoint. Deve
  mostrare "Replay unavailable for future_game_x".

Questo è il test chiave che dimostra l'eliminazione del fallback.

## 6. Rischi e blind spot identificati

| # | Rischio | Severità | Mitigazione |
| --- | --- | --- | --- |
| R1 | Scope sovrapposto con prompt COINS finance registry | Alta | Reconciliazione (4.1) |
| R2 | Mines admin replay endpoint backend potrebbe non esistere o non avere shape compatibile | Media | Verifica Parte A (4.2) |
| R3 | BOXE wallet_type fix richiede backend change non chiarito | Media | Decisione (4.3) |
| R4 | `settlement_kind` migration storica tentata = disastro | Alta | Solo forward metadata (4.4) |
| R5 | Retention policy ambigua blocca legal sign-off futuro | Media | Doc retention 30gg (5.2) |
| R6 | Reconciliation report trigger ambiguo | Bassa | On-demand MVP (5.1) |
| R7 | `metadata_completeness` enum non definito → drift | Media | Enum esplicito (4.5) |
| R8 | Mines auto-cashout in `access_sessions/service.py:649` non usa registry | Alta | Slice F1 deve coprire anche backend `_auto_settle_active_round_for_access_session` |
| R9 | Mines/BOXE/HI-LO grid_size/mine_count Mines-shaped non sostituito | Media | Slice F3 metadata forward deve rinominare a `game_config_payload` o equivalente, non lasciare Mines-shape |

**R8 è importante:** verificato in codice
`backend/app/modules/platform/access_sessions/service.py:577-605` ha hardcoded
`if game_code == GAME_CODE_MINES: _auto_cashout_active_mines_round(...)` etc.
Questo è uno dei branch Rule 18 più rischiosi (money flow). Il registry deve
risolverlo, non solo frontend replay routing.

Parte A deve esplicitamente includere `_auto_settle_active_round_for_access_session`
nello scope F1 (backend auto-settlement registry).

**R9:** `backend/app/modules/games/boxe/platform_client.py:63` e
`backend/app/modules/games/hi_lo/platform_client.py:25` infilano dati
game-specific dentro Mines-shaped `grid_size`/`mine_count`. Reporting eredita
nomi sbagliati. Slice F3 deve rinominare in metadata forward a
`game_config_payload: {...}` game-specific.

## 7. Anti-pattern check vs Playbook + Memory

| Regola | Verdetto |
| --- | --- |
| Playbook Rule 18 - no quarto game branch | ✅ Centrale del WP |
| Playbook Rule 22 - real-money close auto-settlement game-specific | ✅ Settlement taxonomy esplicita |
| Playbook Rule 24 - finance/replay/reporting contract | ✅ Brief allineato a `GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md` |
| Playbook Rule 25 - no hardcoded runtime/error copy | ✅ Replay copy + settlement copy via descriptor |
| Memory `feedback_clean_architecture_priority` | ✅ Eliminazione completa fallback |
| Memory `feedback_capability_matrix_rule` | ⚠️ Brief manca capability matrix. Aggiungere. |
| Memory `feedback_two_step_audit_verifier` | ⚠️ Per surface admin finance critica + slice F1 fallback removal, two-step audit consigliato pre-merge. |
| Memory `feedback_michele_finds_architectural_bugs` | ✅ Brief ha trovato `BoxeReplayViewer` fallback - debito architetturale reale. |
| Memory `feedback_audit_entry_points_coverage` | ✅ Brief copre admin finance, player account, replay endpoints. 12-surface allineato. |
| Memory `feedback_extraction_vs_visual_uniformity` | ⚠️ Replay viewer per Mines admin (Slice F2) deve avere screenshot side-by-side vs BOXE/HI-LO admin replay. Visual contract. |

## 8. Dipendenze e sequencing

| Dipendenza | Stato | Risk |
| --- | --- | --- |
| `WP-ERROR-REQUEST-FOUNDATION-MVP` | soft dep (`Unknown game descriptor` reporting usa log foundation) | OK parallelo, soft link in F5 |
| `WP-PLATFORM-REQUEST-ID-AND-STRUCTURED-LOGGING-MVP` | soft dep | F5 reconciliation report usa log structured |
| `WP-PLATFORM-SETTINGS-READONLY-INVENTORY` | reverse dep: questo WP produce retention status visualizzato da settings (Slice S4 del WP4) | Coordinare |
| COINS (game 4) | hard dep: COINS NON parte prima del merge di questo WP | Conferma packet ordering |

**Verdetto sequencing:** WP3 = **TERZO** dopo WP1/WP2, ma F1+F2+F3 possono
partire in parallelo a WP2 logging se Codex usa worktree (CTO conferma split).

## 9. Acceptance criteria - validazione

Brief test gates sono buoni. Aggiunte richieste:

| Gate aggiuntivo | Motivo |
| --- | --- |
| Regression test fallback per `future_game_x` unknown (5.3) | Verifica eliminazione fallback |
| Backend regression test: `_auto_settle_active_round_for_access_session` usa registry (R8) | Money flow safety |
| Backend test: BOXE settlement metadata include `wallet_source` (4.3) | Bug fix |
| Frontend visual smoke: Mines admin replay viewer parity con BOXE/HI-LO (Slice F2) | Visual parity |
| Manual: admin finance detail mostra `metadata_completeness` badge per row legacy/complete/partial (4.5) | UX validation |
| Manual: player account vede "Replay non disponibile" per game sconosciuto (no Mines fallback) | Visible safety |

## 10. Stop-and-Ask aggiuntivi

Aggiungere a Parte A:

- se in Slice F1 si scopre che frontend descriptor registry richiede modifica
  type contract API (es. `game_code` ora typed enum diventa string aperta),
  Stop-and-Ask;
- se Mines admin replay endpoint (R2 di sopra) non esiste backend, Stop-and-Ask
  prima di scrivere endpoint nuovo (potrebbe essere già in MINES_REPLAY_VIEWER_PLAN);
- se BOXE wallet_source backend exposure richiede schema migration su
  `boxe_rounds` o equivalent, Stop-and-Ask (forward-only metadata vs schema
  migration);
- se Slice F4 retention 30gg confligge con requisiti legal AAMS (real-money
  audit requires 5+ anni), Stop-and-Ask (probabile decisione: 30gg = window
  visible-to-player, 5+ anni = cold storage finance/legal).

## 11. Domande aperte da chiudere con Product Owner (Michele)

**Q1 - Retention policy formale:**
- Replay visible-to-player retention: **30 giorni** (proposta Michele 2026-05-25, da formalizzare).
- Replay cold storage: indefinito o **5 anni** (AAMS) - decisione legal/product.
- Ledger retention: **forever** MVP, future legal decision.

**Q2 - Settlement taxonomy estesa: ogni gioco dichiara quale usa**
- Mines: `manual_cashout`, `auto_cashout`, `refund_no_progress`, `loss`, `admin_void`, `expired_no_settlement`, `quarantined`?
- BOXE: idem?
- HI-LO: idem?
- (Codex Parte A produce matrice gioco × settlement_kind, conferma Michele.)

**Q3 - Admin void capability (vedi packet "Admin void as platform capability? No, not until every game defines semantics"):**
- Conferma: NO platform-wide admin void in questo WP. Game-specific solo dove serve.

## 12. Raccomandazione finale per Codex (prompt readiness)

WP è **pronto per Parte A** dopo le 5 correzioni obbligatorie integrate nel
prompt iniziale + 4.1 reconciliazione scope con COINS prompt.

Prompt structure consigliato:

```
You are CTO assistant. Parte A: validate approach, counter-propose if gap.
Parte B: execution starts only after CTO approval.

Read:
- docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md
- docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md (this)
- docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md
- docs/games/coins/COINS_OPEN_QUESTIONS_2026-05-25.md (CTO context)
- docs/NEW_GAME_INTEGRATION_PLAYBOOK.md (Rule 18, 22, 24)

Mandatory in Parte A output:
1. Capability matrix
2. Audit risultati branch hardcoded (game_code == X) in:
   - admin-finance-panel.tsx
   - player-account-page.tsx
   - player-game-registry.ts
   - access_sessions/service.py
   - admin/service.py
   - rounds/service.py
   - boxe/platform_client.py, hi_lo/platform_client.py
   classificati: keep / convert-now / accepted-bridge
3. Verifica Mines admin replay endpoint (CTO review 4.2)
4. BOXE wallet_source backend exposure spec (CTO review 4.3)
5. metadata_completeness enum (CTO review 4.5)
6. Retention policy doc (CTO review 5.2)
7. Settlement taxonomy matrice gioco × kind (CTO review Q2)
8. Reconciliazione scope: redirigere prompt COINS finance registry a questo WP (CTO review 4.1)

Then proceed with Slice F1. Multiagent mode OK (F1 + F2 + F3 worktree-paralleli
se file disgiunti). Stop-and-Ask conditions: brief + CTO review section 10.
```

Stima effort: **15-25 prompts** (alta complessità).

## 13. Reconciliazione scope con prompt COINS finance registry

**Doppione identificato.** Stasera 2026-05-25 ho scritto per Michele
`docs/games/coins/PROMPT_CODEX_WP_FINANCE_REPLAY_REGISTRY_2026-05-25.md`
come prerequisito a COINS. Sovrappone parzialmente con questo WP.

| Area | Prompt COINS (subset) | Questo WP (full) |
| --- | --- | --- |
| Registry frontend account history / admin finance / replay | ✅ | ✅ |
| Removal hardcoded `if game === ...` Rule 18 | ✅ | ✅ |
| Removal Mines fallback player replay | ✅ | ✅ |
| Removal BOXE fallback admin replay | ✅ | ✅ |
| Backend auto-settlement registry (`access_sessions`) | parziale | ✅ esplicito |
| Forward-only metadata contract (`settlement_kind`, `metadata_schema_version`) | non incluso | ✅ Slice F3 |
| Settlement taxonomy 7-value | non incluso | ✅ |
| BOXE wallet_type bug | non incluso | ✅ Slice F1 |
| Mines admin replay parity wiring | non incluso | ✅ Slice F2 |
| Retention policy MVP | non incluso | ✅ Slice F4 |
| Reconciliation report | non incluso | ✅ Slice F5 |

**Decisione CTO:** mantenere QUESTO WP come canonico. Marcare prompt COINS
come SUPERSEDED. Aggiornare `docs/games/coins/COINS_OPEN_QUESTIONS_2026-05-25.md`
sezione N1 per redirigere qui. Lasciare prompt COINS embed-mode-parity invariato
(quello è un WP diverso e ortogonale).
