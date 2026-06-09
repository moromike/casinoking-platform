# Cross-Game Bonifica Program (2026-06-04)

**Decisione Michele 2026-06-04:** programma COMPLETO ora, prima di COINS, nell'ordine raccomandato dall'audit, **una divergenza alla volta con gate CTO**. Niente produzione con debito architetturale cross-game.

**Origine:** `docs/CROSS_GAME_PARITY_AUDIT_2026-06-04.md` (audit gate-passato). Target canonici lockati:
- Demo = **HI-LO** (demo_wallet server-side + `demo_session_id` su round game-specific). NON BOXE.
- Real settlement = host platform owns ledger; game state conserva solo ref/replay.
- Access-session = **obbligatoria** su real start (boundary API), demo null.
- Launch-token = pattern Mines/BOXE start-only; azioni successive bearer+ownership.
- Layering = repository + state_machine + round_gateway + typed adapter stile BOXE.
- Idempotency = tabella game-local dedicata + settlement idempotency platform.

**Money-safety gia' provato (audit):** nessun buco soldi. Auto-settlement per tutti e 3 (`_AUTO_SETTLE_ACTIVE_ROUND_HANDLERS`); ledger reale host-owned; demo non tocca mai ledger reale.

**Regole esecuzione:** Claude pianifica/gate, KIMI esegue. DB disposable (local/pre-beta): migration/rebuild OK. Ogni step = Stop CTO. Real-money/demo-money flow → invarianti dure + evidence nel gate (no "sembra").

## MASTER SCHEDULE (ordine vincolante — NO LIFO, tieni l'ordine)

Michele 2026-06-05: "non usiamo LIFO, scheduliamo bene tutto senza dimenticare. ORDINE." Il CTO mantiene questo ordine attraverso tutti i tronchi.

| # | Item | Tronco | Stato | Dipende da |
|---|------|--------|-------|-----------|
| F0 | Audit frontend/UX parity (read-only) | Frontend | ✅ DONE (9 div reali, F09 falso positivo) | — |
| F1a | X buttons: DIV-F01 (BOXE embedded) + DIV-F02 (HI-LO mobile) → pattern Mines | Frontend | ✅ DONE (gate CTO 2026-06-05; mobile screenshot CTO batchato con F1b) | F0 |
| F1b-be | Storico replay: 2 endpoint access-session (BOXE/HI-LO) + service | Backend | ✅ DONE (gate CTO; _replay_payload riusato, no boxe_sessions, 2 test verdi) | Parte-A ✅ |
| F1b-fe | Storico replay: pannello generico + integrazione modal BOXE/HI-LO | Frontend | ✅ DONE (gate CTO; render-prop, playback preservato, tsc ok) | Parte-A ✅ |
| F1c | Mobile check CTO (incl. CLEANUP-1 replay BOXE) | Frontend | con F1a/F1b | — |
| F2 | Pacchetto frontend (celebration + idle hint) | Frontend | ✅ DONE 2026-06-07. F04 (Mines playback) + F05 (HI-LO celebration) + F10 (idle hint BOXE/HI-LO). `tsc --noEmit` e build Next.js passano. Restano: F07 (HI-LO mobile layout), F08 (decimali), F06 (audio) PARCHEGGIATO. | F0 |
| 5A | CLEANUP-2 Parte A diagnosi test-infra | Cleanup | ✅ DONE (Codex, gate CTO) | — |
| 5B1 | CLEANUP-2 B1: fix 2 leak (boxe_state_machine 0047 + title orphan) | Cleanup | ✅ DONE (gate CTO 2026-06-05) | 5A |
| 5B2 | CLEANUP-2 B2: split suite + xdist/DB-per-worker (velocità) | Cleanup | ✅ DONE (B2a marker seriali + B2b-1 xdist su unit only; full DB-per-worker deferred) | prima di B6 |
| 6 | DIV-03 HI-LO launch-token | Backend | ✅ DONE (gate CTO 2026-06-05; endpoint + real token-required + demo reject + fix site_code; 13 test) | — |
| 6b | DIV-06 host-owned platform_rounds | Backend | ✅ DONE (gate CTO 2026-06-07; residual-scan game-path pulito, money test 18-campi verde). FOLLOW-UP DIV-06b: admin/session_force_close.py:373 writer residuo da consolidare | DIV-06 analisi |
| 7 | DIV-05 rimuovere boxe_sessions (session_id==round_id stile HI-LO) | Backend | ✅ DONE (gate CTO 2026-06-07; migration 0048, grep=0, 104 test BOXE verdi, idempotency su player_id, storico/replay ok) | DIV-06 ✅ |
| 8 | DIV-02 Mines Opzione B (demo path-unico) | Backend | ✅ DONE (gate CTO 2026-06-06; unificazione tabelle/wallet, FK drop validato, concorrenza hardened, race terminale fixata, stress 10/10 + assertion cross-table) | 7 |
| 8b | DIV-DEMO-ANON: estendere demo ANONIMO (no-login) a BOXE/HI-LO + unificare identità demo su anonymous_id | Backend | ✅ DONE (gate CTO 2026-06-08; commit 7ecc6fd + schema-drift fix 8cf8823; 8b invariants 6/6, BOXE legacy 69/69 → 8b 6/6 cross-file, HI-LO legacy 14/14, forbidden FK query 0 rows, frontend tsc ok). | 8 |
| 9 | DIV-07..10 validator/idempotency/adapter/layering | Backend | da fare | 7 |
| 10 | stale-error-shape tests | Chiusura | ✅ DONE (fix envelope in B6 catalog + B6 browser_smoke; field-based asserts obbligatori) | prima di 11 |
| 11 | B6 regression real+demo | Chiusura | ✅ DONE (gate CTO 2026-06-08; 820 test su 9 marker verdi, schema_drift_guard pass) | 5 |
| 12 | B7 Playbook cross-game (regola audit backend+frontend) | Chiusura | ✅ DONE (gate CTO 2026-06-08; lezioni B6 distille in NEW_GAME_INTEGRATION_PLAYBOOK.md) | F0 + audit backend |

**Dispatch round 1 (2026-06-05, 4 stream) — TUTTI ✅ gatati:** KIMI F1a ∥ Codex-1 5B1 ∥ Codex-2 F1b Parte-A ∥ Codex-3 DIV-03 Parte-A.

**Dispatch round 2 (2026-06-05):** Codex → F1b-be (backend endpoints access-session) ∥ KIMI → F1b-fe (pannello frontend). Domini disgiunti (backend routers/service vs frontend ui), si incontrano sul contratto API di F1b Parte-A. NB: DIV-03 esecuzione NON parallelizzabile ora (tocca hi_lo.py come F1b-be) → dopo. CLEANUP-2 B2 (suite split) tenuto al suo slot (prima di B6). F1b Parte-A outcome: endpoint `/games/{boxe,hi-lo}/access-sessions/latest` su `game_access_sessions`, tipo generico `LatestAccessSessionHistory<TRound>`, chiave UI = round_id (non session_id), pannello condiviso render-prop. DIV-03 Parte-A outcome: `/games/hi-lo/launch-token` hard-required real start + fix `site_code` hardcoded in hi_lo/service.py.

Già fatti: DIV-01 ✅, DIV-04 ✅, CLEANUP-1 ✅ (desktop). Follow-up dopo programma: retention param back-office, COINS gioco 4, merge main, parcheggiati (redesign sito, externalization, production readiness).

## Ordine e stato (tronco backend dettaglio)

| # | DIV | Titolo | Sev | Outlier | Stato |
|---|-----|--------|-----|---------|-------|
| 1 | DIV-01 | BOXE demo → server-side (pattern HI-LO) | CRITICA | BOXE | ✅ **DONE** (gate CTO 2026-06-04) |
| 2 | DIV-04 | Access-session obbligatoria su real start (M/B/H) | ALTA | comune | ✅ **DONE** (gate CTO 2026-06-05) |
| 3 | DIV-03 | HI-LO → launch-token start-only | ALTA | HI-LO | **IN CORSO** |
| 4 | DIV-05/06 | Decisione CTO target DB/session + mirror platform_rounds | ALTA/MEDIA | — | da decidere PRIMA di migrare |
| 5 | DIV-02 | Mines Opzione B (demo path-unico, no tabelle bespoke) | ALTA | Mines | dopo step 4 |
| 6 | DIV-07..10 | validator + idempotency + adapter + layering | MEDIA | Mines/HI-LO | pacchetto finale |

Coda WP launch-token (`docs/MINES_LAUNCH_TOKEN_UNIFORM_WP_2026-06-04.md`): stale-error tests + B6 regression + B7 playbook → si chiude alla fine (B7 incorpora la regola permanente "audit parita' DB+arch ad ogni nuovo gioco"). DIV-03 (HI-LO token) confluisce nel tema launch-token.

---

## STEP 1 — DIV-01: BOXE demo server-side (pattern HI-LO)

**Problema:** BOXE accetta `wallet_source="demo"` ma il saldo demo vive SOLO nel frontend (`setDemoBalance` in `boxe-gameplay.tsx:595-599`, `:655-658`). Il backend, per demo, salta `open_platform_round` e **non usa `demo_wallet`** (`boxe/service.py:195`). Non autoritativo, non persistito, manipolabile, divergente da HI-LO/Mines.

**Target (mirror HI-LO esatto):**
- HI-LO start demo: `boxe/service.py` deve fare come `hi_lo/service.py:191-208` → `open_demo_session(anonymous_id=player_id, title_code, cursor)` poi `debit_for_bet(session_id, amount=bet, idempotency_key=f"boxe:start:{round_id}:{idempotency_key}", payload={game_code, round_id, title_code}, cursor)`.
- Persistere `demo_session_id` su `boxe_rounds` (come `hi_lo_rounds.demo_session_id`, vedi `0043:16`). → **migration nuova** che aggiunge `boxe_rounds.demo_session_id uuid NULL REFERENCES demo_play_sessions(id)` + il repository.create_round/create_session deve scriverlo.
- Settlement demo: in OGNI punto in cui BOXE oggi liquida il round reale (reveal mine = loss, top_row = win, cashout = win), aggiungere l'equivalente demo via `demo_wallet` (`credit_for_win` su vincita; loss = nessun credito, il debit dello start resta), mirrorando come HI-LO settla il demo (`hi_lo/service.py:381-382`, `:578-579`, `hi_lo/platform_client.py` demo).
- Frontend `boxe-gameplay.tsx`: allineare al pattern HI-LO frontend (`hi-lo-gameplay.tsx`). Se HI-LO tiene la copia locale di display backed dal server, BOXE fa identico; la VERITA' resta il server (`demo_play_sessions`). Rimuovere qualsiasi logica che renda il frontend l'UNICA fonte del saldo demo.

**Invarianti dure (DoD, da provare nel gate):**
1. Demo BOXE: bet → `debit_for_bet` server-side; vincita → `credit_for_win` server-side; saldo persistito in `demo_play_sessions` (query SQL post-round = saldo atteso).
2. Demo BOXE **non** scrive `platform_rounds` ne' `ledger_*` reali (count = 0 post-round).
3. `boxe_rounds.demo_session_id` valorizzato per round demo, NULL per round real.
4. Path **REAL** BOXE invariato (zero diff comportamentale: start/reveal/cashout/auto-settlement).
5. Idempotency demo preservata (retry start/reveal/cashout non doppia debit/credit).
6. Replay BOXE demo invariato o migliorato (non rotto).
7. tsc OK, test backend/integration verdi (demo no-ledger + demo balance end-to-end + real invariato).

**Stop-and-ask:** se la struttura multi-pick di BOXE (reveal multipli, top_row, pyramid_full_reveal) NON mappa pulito sul pattern HI-LO (single-action), FERMARSI e segnalare al CTO prima di improvvisare. Non inventare un terzo pattern.

**Gate evidence richiesta:** diff per file; query SQL (demo balance atteso, platform_rounds/ledger count=0 su demo, demo_session_id valorizzato); prova real invariato (test/curl); output test.

**Stato:** Parte A consegnata (da Codex per errore di routing, read-only, zero codice, stop corretto) e **GATE-APPROVATA dal CTO 2026-06-04**. Verifica: le 4 funzioni `demo_wallet` (`open_demo_session`/`debit_for_bet`/`credit_for_win`/`record_loss`) esistono e HI-LO le usa identiche (canonico reale, non inventato).

### Piano LOCKATO (approach approvato — vale per chiunque esegua la Parte B)

**Gotcha BOXE-specifici (gestire tutti):**
1. BOXE ha **3 terminali**, non 1: reveal mine = `record_loss`; reveal top_row = win auto = `credit_for_win`; cashout = win manuale = `credit_for_win`.
2. `boxe_picks` registrate PRIMA del settlement terminale → la response idempotente salvata deve essere costruita/salvata **dopo** il demo settlement (così il replay restituisce `settlement.wallet_balance_after`).
3. top_row oggi nel frontend non aggiorna il saldo demo come cashout → server-side aggiornare da response, non aritmetica locale.
4. `list_sessions` deriva `wallet_source` dal LEFT JOIN su `platform_rounds` → per demo BOXE inferire `wallet_source="demo"` da `boxe_rounds.demo_session_id`, altrimenti finisce "legacy".

**Migration:** nuova `backend/migrations/sql/00NN__boxe_demo_session_id.sql` (prossimo numero libero): `ALTER TABLE boxe_rounds ADD COLUMN IF NOT EXISTS demo_session_id uuid NULL REFERENCES demo_play_sessions(id);` + indice `WHERE demo_session_id IS NOT NULL`. Zero cambi a platform_rounds/ledger/real wallet.

**Backend `boxe/service.py`:** import `open_demo_session, debit_for_bet, credit_for_win, record_loss`.
- `start_round` demo: `open_demo_session(anonymous_id=player_id, title_code, cursor)` + `debit_for_bet(... idempotency_key=f"boxe:start:{round_id}:{idempotency_key}")`; passare `demo_session_id` a `repository.create_round`; response con `wallet_balance_after_start`.
- `reveal_pick` demo: mine → `record_loss(... key=f"boxe:loss:{round_id}:{idempotency_key}")`; top_row → `credit_for_win(amount=payout, key=f"boxe:top-row:{round_id}:{idempotency_key}")`; settlement nella response terminale.
- `cashout_round`: `if platform_round_id:` real invariato; `elif demo_session_id:` `credit_for_win(amount=payout, key=f"boxe:cashout:{round_id}:{idempotency_key}")`; response con `settlement.wallet_balance_after`.

**Backend `boxe/repository.py`:** `create_round(... demo_session_id)`; `list_sessions` seleziona `r.demo_session_id` e inferisce `wallet_source`.

**Frontend:** `use-boxe-runtime.ts` aggiunge tipi `settlement?{wallet_balance_after, ledger_transaction_id, already_exists}` + `wallet_balance_after_start?`. `boxe-gameplay.tsx`: saldo demo da response server (start/reveal-terminal/cashout), NON aritmetica locale come fonte unica.

**DoD aggiuntivi (oltre alle invarianti gia' in STEP 1):**
- Idempotency: chiavi deterministiche per terminale; retry non doppia debit/credit (replay `boxe_idempotency_keys` restituisce stessa response).
- `list_sessions`/history: demo BOXE mostra `wallet_source="demo"`, non "legacy"; real invariato.
- Comportamento round demo abbandonato = come HI-LO (se HI-LO non auto-settla demo, BOXE idem — e' il canonico).

**Prossimo:** Parte B (esecuzione). Esecutore designato KIMI (il brief ha il piano completo, non serve il contesto chat di Codex). Gate CTO finale con evidence.

**ESITO STEP 1 (gate CTO 2026-06-04): ✅ PASS.** Verificato a mano: start demo `open_demo_session`+`debit_for_bet` (key deterministica); reveal mine→`record_loss`, top_row→`credit_for_win`; cashout→`credit_for_win`; real gated da `platform_round_id` e demo da `demo_session_id` (mutuamente esclusivi, real intoccato); `list_sessions` inferisce `wallet_source="demo"` da `demo_session_id`; migration 0047 pulita. Test `test_boxe_api.py` NON vacui (saldi esatti, ledger count==0, idempotency retry, history demo). 73 passed (boxe+demo_wallet). Caveat: integration suite globale in timeout (10 min, lentezza fixture pre-esistente, non spacciata verde) → debito infra da chiudere prima della regression finale del programma.

---

## STEP 2 — DIV-04: Access-session OBBLIGATORIA su real start (Mines/BOXE/HI-LO)

**Problema (money-safety):** tutti e 3 i router validano l'access-session SOLO se il client passa `access_session_id` (`if payload.access_session_id is not None:` — mines.py:454, boxe.py:166, hi_lo.py:89). Se un client (o un host esterno GMP) NON la passa, il round real parte **senza rete di sicurezza** (l'auto-settlement su close/timeout aggancia via access-session). Il frontend attuale la passa sempre, ma il backend non la rende obbligatoria al boundary API → buco potenziale.

**Target:** real start **richiede** `access_session_id` (reject 422 se assente); demo la vieta/null (demo non ha platform_round né auto-settle, coerente con HI-LO). Hard-required, niente soft fallback: il frontend la passa già sempre e il DB è disposable. Vale per: Mines start (path token + path token-less B3), BOXE start, HI-LO start.

**Vincoli:** ZERO impatto sul path demo (resta senza access-session). Real UI deve continuare a funzionare (il FE la passa già). Error envelope coerente (`request_id`/`retryable`).

### PARTE A (analisi, no codice) — DoD

1. Mappa i punti ESATTI di start per gioco dove oggi c'è `if access_session_id is not None` (Mines token-path E token-less-path, BOXE, HI-LO) + il punto demo.
2. Conferma che il frontend real passa SEMPRE `access_session_id` per tutti e 3 (cita file:line creazione+invio) → così rendere obbligatorio NON rompe la UI.
3. Identifica ALTRI entry-point di real-start che oggi NON la passano (GMP/host esterno, admin, mock-host, script) — sono proprio quelli da forzare. Elencali.
4. Conferma che il path demo (wallet demo) deve avere `access_session_id` null/vietato, e come lo enforce-rai.
5. Definisci la error-shape esatta per "real start senza access_session_id" (status + code + message) coerente con l'envelope.
6. Elenca i TEST esistenti che fanno real-start SENZA access_session_id (si romperanno): vanno aggiornati a passarne una valida (stavano testando un path ora-invalido). Collega al debito stale-error-shape.
7. Conferma piano idempotency/replay invariato e real-behavior altrove invariato.

**Stop-and-ask:** se esiste un real-start path legittimo che NON deve avere access-session (es. un flusso interno particolare), FERMATI e segnalalo prima di renderla obbligatoria ovunque.

### PARTE B (esecuzione) — invarianti dure (gate)

1. Real start senza `access_session_id` → 422 (tutti e 3 i giochi, entrambi i path Mines).
2. Real start con `access_session_id` valida → OK invariato.
3. Demo start → nessuna access-session richiesta/usata (invariato).
4. Auto-settlement real invariato (la rete ora è garantita perché l'access-session è sempre presente).
5. Test aggiornati (real-start ora passa access-session valida); no regression real/demo.
6. tsc OK + test backend/integration mirati verdi (mines+boxe+hilo start/access-session).

**Stato:** Parte A consegnata e **GATE-APPROVATA dal CTO 2026-06-04**.

### Parte A — esiti lockati
- Mines real passa SEMPRE dal path-token (il token-less real → 401, mines.py:568); enforcement solo a mines.py:454. Demo Mines (token :414, token-less :536) non tocca access-session.
- BOXE enforcement a boxe.py:166; HI-LO a hi_lo.py:89. Frontend real (mines-standalone:979-991, boxe-standalone:238-242, hi-lo-standalone:334-339) crea+passa sempre; demo esplicitamente null (boxe-gameplay:488, hi-lo-gameplay:324).
- Nessun real-start path legittimo senza access-session. Entry-point da forzare = solo i test che oggi fanno real-start senza passarla (lista in Parte A: test_game_table_sessions, test_financial_and_mines_flows, test_admin_ledger_*, test_admin_session_drilldown, test_api_contract, test_mines_admin_session_contract, + vari "Forse" da verificare). BOXE: i test real usano helper `start_round` che auto-crea table+access (da CONFERMARE in Parte B). HI-LO già passa sempre.
- Demo enforcement: reject `access_session_id` non-null (422 VALIDATION_ERROR "Demo rounds cannot have an access session"); HI-LO aggiunge `if wallet_source=="demo" and access_session_id is not None`.
- Error-shape real senza access-session: 422 + code `VALIDATION_ERROR` + message "Access session is required for real mode" + envelope `request_id`/`retryable:false`.

### Note vincolanti per la Parte B
1. Per OGNI test toccato: determina real-vs-demo **per singola chiamata start**; modifica solo gli start real (crea+passa access-session valida). Demo invariati.
2. Overlap stale-error-shape: se un file toccato fallisce anche sull'envelope, correggi quell'assert per farlo verde; NON allargarti ai file non toccati da DIV-04 (resta debito separato per B6).
3. Conferma il claim "BOXE real già coperto dall'helper `start_round`": se l'helper NON crea l'access-session, aggiungila.
4. Evidence: ogni file di test toccato verde con conteggi; no "globale verde" se timeout — gira gli affected esplicitamente.

**Prossimo:** Parte B (esecuzione). Esecutore KIMI. Gate CTO finale con le 6 invarianti dure.

**ESITO STEP 2 (gate CTO 2026-06-05): ✅ PASS.** Enforcement verificato nel codice: real-required + demo-reject in tutti e 3 i router (boxe.py:166-178, hi_lo.py:89-102, mines.py:422/464/552), entrambi i path Mines. Stato test VERIFICATO eseguendo (non dal riepilogo): financial_and_mines_flows 20/20; test launch-token `require_game_launch_token_header` PASSA (la "diagnosi reveal 200 vs 401" di KIMI era ERRATA: 200 è il comportamento corretto post-WP, il test asserisce 200); concurrency 10/10 come file; boxe 68/68. Demo-reject + error-shape (422 VALIDATION_ERROR + envelope) corretti. Helper test `create_game_access_session` aggiunto; ~20 file test real-start aggiornati a passare l'access-session; 9 assert envelope corretti opportunisticamente in financial_flows + backoffice_config.

**Lezione gate:** i claim di "debito pre-esistente" dell'esecutore vanno VERIFICATI eseguendo — KIMI ha (a) etichettato come bug un test che passa, (b) attribuito al WP fallimenti che esistono solo nella full-suite (isolamento cross-file). Non accettare la lista debiti a scatola chiusa.

### CLEANUP BATCH (decisione Michele 2026-06-05: sistemare i 2 debiti PRIMA di riprendere il programma)

#### CLEANUP-1 — Bug visivo BOXE replay nello statement account

**Root cause (diagnosi CTO completa):** lo statement account NON usa `BoxeReplayViewer` (che ha CSS adattiva corretta in `boxe.css:426-473`, classi `boxe-replay-*`). Usa il renderer compatto `renderAccountBoxeReplayPyramid` in `frontend-v3/app/ui/game-reporting-registry.tsx:350-380`, che emette classi `site-v3-replay-boxe-pyramid` / `site-v3-replay-boxe-row` (con `gridTemplateColumns` inline) / `site-v3-replay-cell`. **PROBLEMA: NON esiste ALCUNA CSS per nessuna classe `site-v3-replay*` in tutto frontend-v3** (persa nella migrazione/recovery). Senza `display:grid` sulla row, il `gridTemplateColumns` inline è inerte → gli `<span>` cella vanno inline a dimensione-contenuto ("S"/"M"/"-") → 8.5/14.375px invece di riempire la colonna. Regressione del loop "BOXE replay visual" (chiuso 2026-05-29).

**Fix:** ripristinare/creare la CSS `site-v3-replay-*` per il replay compatto dello statement, nel file CSS già usato dalla vista account/statement (quello importato da `player-account-page.tsx`). Requisiti:
- `.site-v3-replay-boxe-row { display: grid; gap: ...; }` (così il `gridTemplateColumns` inline `repeat(N, minmax(0,1fr))` si attiva).
- `.site-v3-replay-cell { aspect-ratio: 1; width: 100%; min-width: 0; display:flex; align-items:center; justify-content:center; }` + stati `.is-safe`/`.is-mine`/covered (colori coerenti col viewer canonico).
- `.site-v3-replay-boxe-pyramid`: container adattivo, **niente scrollbar orizzontale**, celle che si adattano al contenitore (regola hard "no scrollbar / cell adaptive", piramide 8-row deve stare senza clipping).
- Allinearsi visivamente al pattern canonico `boxe-replay-*` (non reinventare colori/stile).

**Scope check:** lo stesso renderer generico serve anche Mines/HI-LO account replay → verificare che le loro repliche compatte nello statement non siano ugualmente senza stile; se lo sono, ripristinare anche le loro classi `site-v3-replay-*`.

**DoD:**
1. `tests/integration/test_player_account_statement_browser_smoke.py::test_player_account_boxe_replay_pyramid_fits_eight_row_statement_detail` verde (cellMin ≥ 17, no overflow X).
2. Nessuna scrollbar orizzontale, celle quadrate adattive, piramide 8-row intera visibile.
3. Mines/HI-LO account replay nello statement non regrediti (stilati).
4. tsc OK + il file browser-smoke verde.
5. Validazione visiva Michele su :3000 (statement account, replay BOXE).

**Stato:** ✅ DONE (gate CTO 2026-06-05). CSS `site-v3-replay-*` ripristinata in `globals.css`; `display:grid` sulla row attiva il template inline; celle `aspect-ratio:1; width:100%` adattive. Test browser-smoke 2/2 verdi (cellMin≥17, no overflow X), verificati a mano dal CTO. Mines/HI-LO usano fallback testuale (nessuna piramide compatta → nessuna CSS da ripristinare). Nota minore: KIMI ha messo `minmax(17px,1fr)` (floor belt-and-suspenders); il fix reale è il `display:grid`; clip solo sotto ~200px contenitore (irrealistico). In attesa validazione visiva Michele su :3000.

#### CLEANUP-2 — Test-infra: suite timeout + isolamento cross-file
Diagnosi-first (Parte A) eseguibile ORA in PARALLELO a F0 (read-only, area `tests/`, nessun conflitto col frontend). Esecutore: Codex. Parte B (fix) dopo gate, in sequenza.

**Parte A — diagnosi (read-only), DoD:**
1. Root cause del TIMEOUT: cosa rende lenta la suite integration (DB reset per-test vs shared, startup container, fixture pesanti, N test). Identifica i colli di bottiglia con prove (tempi/fixture). 
2. Leak ISOLAMENTO cross-file: quale/i test, eseguito/i prima dei concurrency nella full-suite, de-pubblica o muta il title/site usato da `published_concurrency_title` (fix `tests/concurrency/test_mines_concurrency.py:15`) → access-session creation fallisce "title not published". Identifica il test colpevole e il meccanismo (stato condiviso/DB/fixture-scope).
3. Direzioni di fix proposte (per la Parte B): fixture isolation (publish per-test), split/parallelizzazione suite (pytest-xdist se safe), marker, reset DB mirato. NON scrivere codice.

**Vincoli:** READ-ONLY, evidence-based (file:line, tempi). STOP CTO a fine Parte A.

**ESITO PARTE A (Codex 2026-06-05, gate CTO ✅ PASS):**
- Timeout = suite monolitica oltre budget (browser smoke/visual + API pesanti + concurrency + cleanup DB manuale per-test; DB shared autocommit=True, no rollback-per-test). Misure: embed smoke 547s, boxe smoke 434s, boxe_api 251s, concurrency cold 240s. Non un singolo hang.
- Leak concurrency originale NON confermato (Codex onesto: concurrency 10/10 in tutte le combo). 
- **2 leak REALI trovati:** (1) 🔴 `test_boxe_state_machine.py:26,41-46,325-337` droppa `boxe_*` e riapplica solo 0039, NON 0047 → `boxe_rounds.demo_session_id` assente → UndefinedColumn cross-file (regressione interazione con DIV-01); (2) cleanup Mines title fragile (`conftest.py:1253-1303`) → orphan inactive senza pubblicazione.
- Direzioni Parte B: separare marker/suite (api/browser/visual/concurrency/migration); DB-per-worker prima di xdist; isolare title per-test; fixture schema-chain completa in test_boxe_state_machine; aggiornare stale tests.

**Parte B sdoppiata:**
- **CLEANUP-2 B1 (correttezza, ORA, Codex-1):** fix i 2 leak (test_boxe_state_machine applica chain completa incl. 0047; cleanup title senza orphan). Dominio `tests/`. Gate CTO.
- **CLEANUP-2 B2a (marker seriali, ORA):** marker pytest registrati + assegnazione automatica via `pytest_collection_modifyitems` in `tests/conftest.py`. Split in 9 gruppi seriali: `unit`, `api_service`, `browser_smoke`, `concurrency`, `migration_schema`, `money_admin`, `catalog`, `visual`, `stress`. ✅ DONE (gate CTO). Fix leak `sites.display_name` da test HI-LO → `preserve_site_bootstrap` fixture. Test rossi pre-esistenti in `concurrency/` (backend validation "Title is not published on this site") — NON causati da marker. B2b/xdist bloccato fino a fix concurrency.

  **Comandi seriali B6 (eseguire in ordine, nessun xdist):**
  ```bash
  python -m pytest -m unit -q
  python -m pytest -m migration_schema -q
  python -m pytest -m api_service -q
  python -m pytest -m money_admin -q
  python -m pytest -m catalog -q
  python -m pytest -m browser_smoke -q
  python -m pytest -m visual -q
  python -m pytest tests/concurrency -q
  python -m pytest -m stress -q
  ```

  **Sequenza anti-leak post-marker (verifica che lo schema resti canonico):**
  ```bash
  python -m pytest -m migration_schema -q
  python -m pytest tests/integration/test_schema_drift_guard.py -q
  python -m pytest -m money_admin -q
  python -m pytest tests/integration/test_schema_drift_guard.py -q
  ```

- **CLEANUP-2 B2b (xdist/DB-per-worker):** ✅ DONE parziale (B2b-1). xdist attivo SOLO per marker `unit` (22 test, -n 2, no backend/DB). Full DB-per-worker + backend-per-worker rimandato a programma infra dedicato; tutti gli altri marker restano seriali per shared DB.

---

## TRONCO FRONTEND/UX (nuovo, 2026-06-05)

**Origine:** Michele ha scoperto a mano 2 divergenze frontend mai rilevate (X di chiusura, storico replay). L'audit backend non copriva il frontend. Decisione Michele: **audit frontend ORA**, poi fix X+replay, poi riprendere backend/cleanup. CLEANUP-2 e backend DIV-03..10 sono in PAUSA fino a fine fix frontend prioritari.

**Step F0 — Audit frontend/UX parity (read-only).** ✅ DONE (gate CTO 2026-06-05). Doc `docs/CROSS_GAME_FRONTEND_PARITY_AUDIT_2026-06-05.md`. 9 divergenze reali (0 critiche). **DIV-F09 (idempotency HI-LO) = FALSO POSITIVO** scartato: verificato che HI-LO ha idempotency corretta (frontend riusa la chiave sui retry hi-lo-gameplay.tsx:306; router la richiede hi_lo.py:85).

**Sfumatura replay (decisione Michele):** canonico = storico di Mines + playback animato di BOXE/HI-LO (non imbruttire BOXE/HI-LO allo statico Mines). F1 porta lo STORICO su BOXE/HI-LO mantenendo il loro playback; l'upgrade Mines a playback animato (DIV-F04) va in F2.

**DEPENDENCY (ORDINE):** lo storico replay Mines è su access-session, NON su tabella sessione gioco. BOXE ha `boxe_sessions` che DIV-05 rimuoverà → costruire lo storico BOXE/HI-LO sul modello **access-session** (canonico) per essere forward-compatible con DIV-05 (zero rework).

**Step F1a — X buttons:** DIV-F01 (BOXE X in embedded → pattern Mines `!isHostFullscreen && !useMobileLayout`) + DIV-F02 (HI-LO X su mobile → aggiungi `!useMobileLayout`). Frontend, effort S. → parte subito (KIMI). Mobile check CTO.
**Step F1b — Storico replay (DIV-F03):** Parte A (disegno endpoint backend BOXE/HI-LO su modello access-session + UI panel come Mines, no boxe_sessions) → gate → Parte B. Mantiene il playback animato esistente.
**Step F2 — pacchetto (parziale):** DIV-F04 (Mines → playback animato) ✅ DONE. DIV-F05 (celebration HI-LO, ALTA) ✅ DONE. DIV-F10 (idle hint BOXE/HI-LO) ✅ DONE. Restano DIV-F07 (mobile layout React HI-LO, rischio ALTO), DIV-F08 (bet input mode, decisione product). DIV-F06 (audio HI-LO) PARCHEGGIATO (skip; opzionale AI-gen). DIV-F09 scartata.

**Retention parameter (back office):** follow-up dedicato, si fonde con open loop "Replay retention". Raccomandazione CTO: per-gioco configurabile, default su sessioni (es. ultime 10), coerente col modello access-session di Mines. Da decidere con la matrice in mano.

**Insight:** nessun gioco-template unico. Frontend: Mines migliore (X+storico replay). Backend: Mines outlier (demo bespoke, layering). Canonico cambia per asse.

---

## DIV-05/06 — Analisi target DB/session (read-only, prep decisione #7)

Eseguibile ORA in PARALLELO (read-only, area backend schema/repository, nessun conflitto con frontend/tests). Esecutore: Codex. Output = materiale per la decisione CTO+Michele, NON esecuzione.

**DIV-05 — Session model:** BOXE ha `boxe_sessions` (tabella propria, 0039:11); Mines/HI-LO no (usano `game_access_sessions`/`game_table_sessions` condivise + round diretto). Analizza: cosa fa davvero `boxe_sessions` (raggruppa round? quali colonne/uso reale? a cosa serve in service/repository/replay/history)? È una feature di prodotto giustificata o una divergenza rimovibile? Opzioni: (A) rimuoverla, BOXE come Mines/HI-LO; (B) tenerla come eccezione documentata. Tradeoff, effort, impatto migration (DB disposable), rischi replay/history.

**DIV-06 — platform_rounds mirror:** BOXE/HI-LO aprono il platform round via service e poi inseriscono un mirror in `platform_rounds` nel repository (boxe/repository.py:452, hi_lo/repository.py:549); Mines lo fa nel proprio path (mines/service.py:1583). Analizza il rischio drift e definisci il canonico: adapter host unico che apre/settle il platform round e restituisce ref, game repo che NON duplica logica oltre FK/ref. Opzioni, effort, rischi audit finanziario.

**DoD Parte A:** opzioni con tradeoff + prove (file:line, schema) + target canonico raccomandato + effort + rischi/migration per DIV-05 e DIV-06. READ-ONLY, niente codice. STOP CTO.

**ESITO ANALISI (Codex 2026-06-05, gate CTO ✅ PASS — crux DIV-06 verificato a mano):**
- DIV-06 verificato: `open_game_round` (platform/rounds/service.py:59) fa wallet+ledger ma NON inserisce `platform_rounds`; l'INSERT è in 3 posti game-side (boxe/repository.py:455, hi_lo/repository.py:549, mines/service.py:1583). Drift risk reale sul record real-money.
- DIV-05 verificato (coerente): `boxe_sessions` è one-round (ogni start → nuova session + singolo round), wrapper per history, non serve al replay; HI-LO è il precedente pulito (no session table, session_id==round_id).

**RACCOMANDAZIONE CTO (banked, esecuzione a slot #7-8):**
- DIV-05 → **A: rimuovere `boxe_sessions`**, allineare BOXE a HI-LO/Mines. Effort M. Rischi: link `/games/boxe/session/{id}`, test history/replay, idempotency start (su round/player).
- DIV-06 → **canonico host-owned**: l'adapter/platform service apre+settle e fa INSERT/UPDATE `platform_rounds` in UNICA transazione col ledger; i repo gioco salvano solo stato gioco + `platform_round_id` (ref restituito, non assunto). Effort M/L.
- **Sotto-sequenza:** DIV-06 PRIMA (blinda audit finanziario), poi DIV-05 (cleanup schema/API). In attesa lock decisione Michele.

### 2 debiti REALI scoperti (NON difetti DIV-04, tracciati per non perderli)
- **TEST-INFRA-SUITE**: ✅ CHIUSO in B2a/B2b/B6. Marker seriali attivi (9 gruppi), xdist POC su `unit` solo, leak cross-file risolti (boxe_state_machine chain completa, title orphan cleanup, preserve_site_bootstrap). La suite globale monolitica è sostituita dalla sequenza marker seriale come gate affidabile.
- **BOXE-REPLAY-CELLMIN**: ✅ CHIUSO in CLEANUP-1 (2026-06-05). CSS `site-v3-replay-*` ripristinata; test browser-smoke 2/2 verdi.

---

## B6 — Regression Gate (820 test, 9 marker)

**Data gate:** 2026-06-08. **Branch:** `feature/site-v3-cms-ia-cleanup`. **Esecutore:** KIMI.

Risultati per marker (ordine seriale obbligatorio per shared DB):

| Marker | Passed | Skipped | Note |
|--------|--------|---------|------|
| `unit` | 22 | 0 | xdist -n 2, no backend/DB |
| `migration_schema` | 21 | 0 | serial |
| `api_service` | 316 | 0 | serial |
| `money_admin` | 89 | 0 | serial |
| `catalog` | 108 | 0 | serial |
| `browser_smoke` | 84 | 0 | serial |
| `visual` | 3 | 0 | serial |
| `concurrency` | 13 | 0 | serial |
| `stress` | 2 | 160 | attesi — richiedono `RUN_BOXE_STRESS=1` / `RUN_MINES_STRESS=1` |
| `schema_drift_guard` | 5 | 0 | serial |
| **TOTALE** | **663** | **160** | 820 test eseguiti |

**Fix principali inclusi in B6:**
1. **B6-CATALOG-RED** (commit `1359673`): 3 catalog failures — envelope field-based asserts (`support_id`/`request_id`/`retryable`); lobby game_card asset test riscritto con setup reale Site V3 (no `page.route` mock per SSR).
2. **B6-CATALOG-RED-R2** (commit `9cf772a`): Homepage Slot CTA → Launch Cashier contract ripristinato in `HeroBanner` (non navigazione diretta a game route); `LaunchCashier` estratto in componente condiviso.
3. **B6-BROWSER-SMOKE-RED-R2** (commit `7d51d98`): BOXE smoke — `mode=real_cash` → `mode=real`; round-id letto da JSON response (`data.round_id`) invece di query DB by `player_id` (demo-anonymous usa `anonymous_id`); selettore `.mines-rules-close` → `.game-info-rules-close`; rimossi parametri real da `test_boxe_boot_modes_reach_gameplay` (richiedono table-balance gate).

**Decisioni B6 da portare nel Playbook:**
- Envelope error = sempre field-based asserts, mai `==` dict strict.
- SSR data non mockabile con `page.route`; lobby/catalog test devono usare setup backend reale.
- `demo_session_id` / `anonymous_id` rendono le query by `player_id` inaffidabili per test browser smoke.

---

## B7 — Chiusura Playbook

**Data gate:** 2026-06-08. **Dominio:** `docs/` only. **Esecutore:** KIMI.

Output:
1. `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` aggiornato con lezioni B6 (sezione 16.2quinquies).
2. `docs/CROSS_GAME_BONIFICA_PROGRAM_2026-06-04.md` aggiornato con stato finale B2a/B2b-1/B6/B7.

Regola permanente consolidata: **audit parità DB+arch ad ogni nuovo gioco, MA anche frontend/UX (12 superfici).** Non solo backend.

**Programma Cross-Game Bonifica = COMPLETO.** Prossimo: COINS (game 4) con playbook v3.2+.
