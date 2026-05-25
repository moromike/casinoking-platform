Status: ACTIVE
Last meaningful update: 2026-05-25

# CTO Review - WP-ERROR-REQUEST-FOUNDATION-MVP

Documento sorgente:
`docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_BRIEF_2026-05-25.md`
Documento companion:
`docs/PLATFORM_ERROR_REGISTRY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md`

## 1. Verdetto CTO

**APPROVE WITH MANDATORY CORRECTIONS** prima di entrare in Parte B (codice).

L'analisi è solida nei file:line citati (verificati in codice da CTO Claude):
`backend/app/api/responses.py` lines 11-27 ha solo `code/message/details` senza
support_id/request_id/retryable; `backend/app/main.py` lines 31-60 non ha
middleware request-id né exception handler globali; quindi il brief
correttamente identifica gap reali, non immaginari.

La sequenza E1→E7 (transport compatibility → registry/handlers → first domain
migration D1 auth/launch → D2 wallet/idempotency → UI diagnostic → HI-LO proof
→ route-by-route backlog) è la sequenza giusta. Compatibility-first invece di
big-bang rename è la decisione corretta.

Ci sono però 6 correzioni obbligatorie e 4 raccomandate elencate sotto. Codex
deve risolverle in Parte A (validate approach) prima di partire con Parte B.

## 2. Sintesi non-tecnica (per Michele)

Questo WP costruisce le fondamenta del sistema errori. Oggi quando un errore
arriva al giocatore o all'admin, il messaggio è generico, non c'è un codice
identificativo del problema, non c'è un "ID di supporto" che permetta al
customer support di ritrovare l'errore nei log. Il WP introduce:

1. un identificatore unico per ogni richiesta (`request_id`);
2. un "support_id" che il giocatore può copiare e dare al supporto;
3. una tabella di codici errore stabili (es. `CK.AUTH.SESSION_EXPIRED`,
   `CK.WALLET.INSUFFICIENT_BALANCE`);
4. handler centrali che evitano che dettagli tecnici grezzi raggiungano il
   giocatore.

Non risolve tutti gli errori in un colpo solo. Risolve la **base** su cui ogni
errore futuro si appoggerà. Scelta giusta: prima la base, poi i singoli temi.

Rischio principale: l'analisi sottovaluta che Mines ha un pattern di errore
custom diverso da BOXE/HI-LO. Senza una baseline visuale, c'è rischio che il
"compact diagnostic line" finisca diverso tra Mines e gli altri. Correzione
obbligatoria #2 sotto.

## 3. Cosa è solido nell'analisi

| Area | Verdetto CTO |
| --- | --- |
| Diagnosi current state (envelope, handler, parser) | Corretta - verificata in codice. |
| Compatibility-first migration (no big-bang rename) | Corretta - allineata a `feedback_clean_architecture_priority` e a `feedback_codex_chat_continuity`. |
| Slice di migrazione E1-E7 / Step A-F | Sequenza corretta. |
| Registry codice MVP small (13 codici, no taxonomy globale) | Corretta - allineata a "add code only when concrete path needs it". |
| `support_id = request_id` in MVP | Conferma CTO: stesso valore. Future-proof: il contratto envelope ha campi separati, quindi separazione futura non è breaking. |
| Decisione "Player vede error code compact" | Conferma CTO. Codice e support_id sono support aid, non headline. |
| Validation namespace `CK.VALIDATION.*` esplicito | Già aggiunto nella correzione del brief. Buono. |
| HTTPException double-wrap policy | Corretta concettualmente. Va testata in modo esplicito (vedi #1 sotto). |
| Tests legacy compat preservation | Allineato con principio "non rompere route non toccate". |
| Stop-and-Ask elencati | Coprono i casi product-critical. |

## 4. Correzioni obbligatorie (Parte A deve risolverle)

### 4.1 Test gate esplicito per HTTPException nested envelope

Il brief dichiara la policy "if `exc.detail` already looks like envelope,
normalize, do not nest". Questa è una delle aree più delicate. Codex Parte A
deve produrre **uno scenario test scritto** per ognuno di questi 4 casi:

1. `HTTPException(status=400, detail={"success": false, "error": {"code": "X.LEGACY"}})`
   - aspettativa: handler riconosce envelope, aggiunge support_id/request_id,
     **non** nesta. Code resta `X.LEGACY`.
2. `HTTPException(status=400, detail="raw string")`
   - aspettativa: handler mappa per status code a safe platform code, copy
     user-facing localizzato.
3. `HTTPException(status=400, detail={"field_x": "value"})` (dict ma non envelope)
   - aspettativa: handler whitelist-only su safe keys.
4. `HTTPException(status=400, detail={"success": false, "error": {...}, "extra": "leak"})`
   - aspettativa: handler ignora campi extra, non li propaga.

Il test deve girare in CI come gate. Senza questo test, una route futura potrà
emettere envelope-in-detail e ottenere doppio-wrap silenzioso.

### 4.2 Visual baseline Mines vs shared diagnostic line

Step E5 del brief dice "Mines custom error/recovery UI gets equivalent compact
diagnostic display". Verificato in codice: `mines-standalone.tsx:1371` e
`:1813` hanno error/recovery surfaces custom diverse dal `GameActionError`
shared usato da BOXE/HI-LO.

Senza baseline visuale, il diagnostic line può finire visivamente divergente
tra Mines e shared. Rule playbook `feedback_extraction_vs_visual_uniformity`
e Rule 17 (eight-layer green check) impongono evidenza visuale side-by-side.

**Parte A deve dichiarare:**

- screenshot baseline reference (Mines pre-refactor + GameActionError
  pre-refactor) salvati in `tests/visual/artifacts/wp-error-foundation/`;
- screenshot expected post-refactor con compact diagnostic line in entrambi;
- regola: il diagnostic line deve avere stessa font-size, stesso colore,
  stessa posizione relative al messaggio principale, in entrambe le UI.

**Parte B closure gate:** screenshot side-by-side Mines vs BOXE/HI-LO dialog.

### 4.3 Frontend bug `detail → VALIDATION_ERROR` mappato esplicitamente

Verificato in codice: `frontend/app/lib/api.ts:59` e `:101` collassano qualunque
payload con `detail` a `VALIDATION_ERROR`. Questo è un bug attuale che fa sì
che envelope nested (case 1 del 4.1) vengano misclassificati frontend-side.

Il brief lo cita di passaggio ma non lo elenca come gate hard di Step C.

**Correzione:** Step C (Frontend Parsing) deve avere come acceptance criterion
esplicito:

- parser frontend, di fronte a `{detail: {success: false, error: {code: "...",
  message: "...", support_id: "...", ...}}}`, deve estrarre il code reale e
  non sostituirlo con `VALIDATION_ERROR`;
- test frontend regression per i 4 casi del 4.1 lato parser.

### 4.4 Validazione input `X-Request-ID`

Il brief dice "accept inbound `X-Request-ID` if present and valid enough for
logs". "Valid enough" non è una specifica.

**Correzione:** definire regex/lunghezza max. Default proposto CTO:

- charset: `[A-Za-z0-9_-]`;
- length: 8-64 chars;
- se invalid → generate fresh, log nota "input request id rejected"
  (non come errore, come info, no log spam).

Rischio se non specificato: log injection (newline in request_id → fake log
entries) o storage overflow.

### 4.5 Decisione esplicita su Insufficient Balance HTTP status

Il brief ha discrepanza interna:

- registry tabella dice "402 or 409";
- Step D2 dice "Do not change HTTP status silently. Decide explicitly";
- Packet stop-before-code dice "Keep current status during MVP unless CTO
  explicitly changes it".

**Decisione CTO:** in MVP **keep current HTTP status** (probabilmente 422, da
verificare in codice). Cambio status è breaking per test e per copy adapter
frontend. WP successivo (WP-WALLET-ERROR-STATUS-MIGRATION) può cambiarlo
quando product decide.

Codex Parte A deve: (a) verificare current status in tests, (b) confermare
keep-as-is, (c) annotare il cambio futuro come WP separato.

### 4.6 Capability matrix mancante

Il brief manca della **capability matrix** richiesta dal Playbook sezione 14.
Codex Parte A deve produrla. Template atteso:

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Request id middleware | n/a | NEW | NEW header | n/a | n/a | n/a | NEW | UPDATE | TBD | |
| AppError + registry | n/a | NEW | extended envelope | n/a | n/a | n/a | NEW | UPDATE | TBD | |
| Central handlers | n/a | NEW | normalize envelope | n/a | n/a | n/a | NEW | UPDATE | TBD | |
| Frontend parser | n/a | n/a | parse extended | n/a | NEW | n/a | NEW | UPDATE | TBD | |
| Game dialog diagnostic line | n/a | n/a | n/a | n/a | UPDATE | UPDATE | NEW | UPDATE | TBD | shared + Mines |
| Migrate auth/session paths | n/a | UPDATE | CK.AUTH.* | n/a | UPDATE | n/a | UPDATE | UPDATE | TBD | D1 |
| Migrate wallet/idempotency | n/a | UPDATE | CK.WALLET.* | n/a | UPDATE | n/a | UPDATE | UPDATE | TBD | D2 |

## 5. Correzioni raccomandate (Parte A può proporre alternative)

### 5.1 Request id propagation downstream

Il brief gestisce request_id solo via response header e ContextVar. Manca un
pattern per propagarlo a chiamate downstream (DB query log, future external
service calls). Per ora MVP è OK con ContextVar + logger, ma annotare:

- ContextVar `request_id_var` accessibile in tutto il backend;
- logger helper attinge a `request_id_var.get()` quando logga (sarà oggetto
  del WP successivo Logging MVP).

### 5.2 Severity per AppError

Il brief definisce `ErrorDefinition` con "log level" ma non con severity
user-facing (toast vs modal vs blocking). Per ora MVP è OK con "code + message
+ retryable", ma annotare come future field se product chiede UX differenziata.

### 5.3 i18n del message

`ErrorDefinition` ha "default message key/copy". Non è chiaro se è una key per
i18n manifest o una stringa hard. Per MVP messaggi tecnici limitati basta
stringa it; ma annotare come future key per IT/EN/DE/ES.

### 5.4 Effort estimate include bug fix #4.3?

Brief stima 12-21 prompts. Il fix `detail → VALIDATION_ERROR` (4.3) aggiunge
~1-2 prompts. Sale a 13-23 prompts realistici. Annotare.

## 6. Rischi e blind spot identificati

| # | Rischio | Severità | Mitigazione proposta |
| --- | --- | --- | --- |
| R1 | Mines custom error UI diverge visivamente da shared diagnostic line | Media | Visual baseline obbligatorio (4.2) |
| R2 | HTTPException nested envelope produce doppio wrap silenzioso | Alta | Test gate esplicito (4.1) |
| R3 | Frontend `detail → VALIDATION_ERROR` collasso continua post-WP | Alta | Test regression frontend (4.3) |
| R4 | `X-Request-ID` injection (newline, length) | Media | Regex/length validation (4.4) |
| R5 | Cambio HTTP status su insufficient balance break tests/UX | Alta | Keep current MVP (4.5) |
| R6 | Capability matrix mancante = scope sliding | Media | Aggiungere (4.6) |
| R7 | Effort estimate sottovalutato | Bassa | +1-2 prompts (5.4) |
| R8 | i18n message key vs stringa hard non definita | Bassa | Annotare per future (5.3) |

## 7. Anti-pattern check vs Playbook + Memory

| Regola | Verdetto |
| --- | --- |
| Playbook Rule 18 - no quarto game branch | ✅ Foundation è platform-level, non touching game logic |
| Playbook Rule 25 - no hardcoded runtime/error copy | ✅ Brief richiede copy adapter, i18n manifest. Coerente. |
| Memory `feedback_clean_architecture_priority` | ✅ Compatibility-first invece di big-bang, ma compat è temporanea (E7 backlog) |
| Memory `feedback_visual_first_sequencing` | ⚠️ Brief è backend-first. Per error foundation è corretto (è transport contract). |
| Memory `feedback_codex_chat_continuity` | ✅ Brief è snello, non onboarding completo. |
| Memory `feedback_michele_finds_architectural_bugs` | ⚠️ Mines custom dialog è un debito architetturale pre-esistente. Brief lo riconosce ma non lo risolve. Stop-and-Ask #6 lo cita correttamente come blocker se Mines richiede nuovo visual pattern. |
| Memory `feedback_two_step_audit_verifier` | ⚠️ Per WP foundation transport può bastare audit step 1. Per Step E5 (Mines UI) due step consigliato. |

## 8. Dipendenze e sequencing

| WP | Dipendenza | Blocca |
| --- | --- | --- |
| WP-ERROR-REQUEST-FOUNDATION-MVP (questo) | nessuna | WP2 logging, WP4 settings (Error Matrix slice), tutti i WP che useranno `CK.*` |
| WP2 - Structured logging | richiede support_id + request_id + AppError | logging settings status |
| WP3 - Finance registry | dipendenza soft (per "log/report descriptor gap after logging foundation") | COINS prerequisito |
| WP4 - Settings inventory | dipendenza soft (Slice S5 Error Matrix wait) | nessuno se S5 differito |

Verdetto: **PRIMO da implementare**. Conferma packet ordering.

## 9. Acceptance criteria - validazione

Brief test gates (sezione "Test Gate Plan") sono coperti tranne:

| Gate aggiuntivo richiesto da CTO | Motivo |
| --- | --- |
| Test HTTPException 4 scenari (4.1) | Doppio-wrap silent risk |
| Test frontend parser regression `detail → CK.code` (4.3) | Bug attuale frontend |
| Test `X-Request-ID` input validation (4.4) | Log injection |
| Test no PII/credential leak in any error response | Security baseline |
| Visual smoke side-by-side Mines vs shared diagnostic (4.2) | Visual parity |

## 10. Stop-and-Ask aggiuntivi (oltre quelli del brief)

Aggiungere a Parte A:

- se durante migrazione D1 si scopre che auth/session paths usano già un
  custom envelope diverso (es. legacy `{ok: false, code, msg}`), Stop-and-Ask
  prima di forzare migrazione;
- se la decisione "non cambiare HTTP status insufficient balance" (4.5) genera
  conflitti con tests che già si aspettano 402/409, Stop-and-Ask;
- se Mines diagnostic line richiede modifiche a `mines-standalone.tsx` >50
  lines, Stop-and-Ask (Mines è "non si tocca", interpretazione zero diff
  visivo).

## 11. Domande aperte da chiudere con Product Owner (Michele)

Nessuna in MVP. I default sono safe. Le domande emergeranno dai Stop-and-Ask.

Eccezione: se in D2 emerge che insufficient balance status va cambiato per
ragioni di customer support (UX errore retry diversa), allora Michele decide.
Non in MVP.

## 12. Raccomandazione finale per Codex (prompt readiness)

Il WP è **pronto per Parte A** con le 6 correzioni obbligatorie risolte
nel prompt iniziale.

Prompt structure consigliato per Codex:

```
You are CTO assistant. Parte A: validate approach, counter-propose if gap.
Parte B: execution starts only after CTO approval.

Read:
- docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_BRIEF_2026-05-25.md
- docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_BRIEF_2026-05-25_CTOREVIEW.md (this)
- docs/PLATFORM_ERROR_REGISTRY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md
- docs/PLATFORM_ERROR_CODE_REGISTRY_PLAN_2026-05-24.md

Mandatory in Parte A output:
1. Capability matrix (template in CTO review section 4.6)
2. Test scenario document for 4 HTTPException cases (CTO review 4.1)
3. Visual baseline plan for Mines vs shared diagnostic line (CTO review 4.2)
4. Frontend parser regression test plan (CTO review 4.3)
5. X-Request-ID input validation spec (CTO review 4.4)
6. HTTP status decision matrix for insufficient_balance (CTO review 4.5)

Then proceed with Step A (request id + envelope compat). Stop-and-Ask if any
of the additional stop conditions from CTO review section 10 trigger.
```

Stima effort: 13-23 prompts (brief + 1-2 per il fix frontend `detail`).
