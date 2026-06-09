Status: ACTIVE
Last meaningful update: 2026-05-25

# CTO Review - WP-PLATFORM-SETTINGS-READONLY-INVENTORY

Documento sorgente:
`docs/PLATFORM_SETTINGS_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md`

## 1. Verdetto CTO

**APPROVE WITH MANDATORY CORRECTIONS.**

L'analisi è la più "ben confezionata" delle 4: ha già un descriptor contract
formale (11 fields), una initial inventory matrix completa (28 rows), masking
rules esplicite. Verificato in codice campione:

- `backend/app/core/config.py` carica env defaults (JWT secret, server seed,
  site password, DB/Redis URL) - claim brief corretta;
- `frontend/app/ui/player-register-page.tsx:13` ha hardcoded access password
  default lato client - gap reale e critical;
- `backend/app/api/routes/health.py:17-27` `/ready` non verifica DB/Redis -
  gap real;
- `backend/app/api/dependencies.py:89-99` RBAC fallback "missing admin profile
  = superadmin" - gap critical.

4 correzioni obbligatorie + 4 raccomandate sotto.

## 2. Sintesi non-tecnica (per Michele)

Questo WP costruisce una "pagina di stato" del backoffice dove operatori e
sviluppatori possono vedere:

- quali variabili di configurazione sono attive (es. URL del database,
  timeout di sessione, password di accesso al sito);
- da dove arrivano (file env, codice hardcoded, database, registry);
- chi può vederle (alcune sono mascherate, altre nascoste, altre visibili);
- quale è il livello di rischio (es. JWT secret = critical, app name = low);
- se cambiarle richiede riavvio.

**Importante:** è SOLO read-only. Niente form per modificare. Costruire un
editor è pericoloso senza prima classificare tutto. È il primo passo verso
una eventuale "centralina di configurazione" futura, ma non aspettarsi
"l'editor".

Ha già scoperto 4 problemi di sicurezza concreti nel codice attuale (vedi
sezione 7 Gap):

1. password client default hardcoded nel frontend;
2. health endpoint che dice "OK" anche se DB è down;
3. fallback RBAC che dà privilegi superadmin quando manca profilo admin;
4. token admin passato via query string a CMS v2 lab.

Questi 4 vanno classificati esplicitamente come "gap" nel UI, non nascosti.

## 3. Cosa è solido nell'analisi

| Area | Verdetto CTO |
| --- | --- |
| Read-only only, niente editor | ✅ Decisione critica, conferma. |
| Descriptor contract 11 fields | ✅ Esaustivo. Verificato design space. |
| Masking rules 4 livelli (`hidden`, `masked`, `read_only`, `editable_future`) | ✅ Differenziazione corretta. |
| Initial inventory matrix 28 rows | ✅ Copre core. Vedi 5.1 per aggiunte. |
| Superadmin-only requirement | ✅ Settings page è high-security. |
| Slice S1 (descriptor contract) → S2 (backend read model) → S3 (UI) → S4 (game registry health) → S5 (Error Matrix placeholder bloccata fino a WP1) | ✅ Sequenza giusta. |
| Identificazione 4 gap esistenti (S1 list) come `gap`, non "verde silenzioso" | ✅ Critico. Vedi 4.1. |
| Stop-and-Ask elencati | ✅ Coprono i rischi prodotto. |
| `editable_future` come visibility distinta da `read_only` | ✅ Forward-thinking. |
| Mining e visualizzazione "configured / missing" per `hidden` (no value) | ✅ Pattern corretto. |

## 4. Correzioni obbligatorie (Parte A deve risolverle)

### 4.1 Gap section: scrittura risk write-up obbligatoria

Slice S1 dice "explicitly classify current conflicts as `gap`, not silently
green". Lista 4 gap. Parte A deve produrre **per ogni gap** un risk write-up:

| Gap | Severità | Impatto | Mitigazione MVP | Mitigazione lungo termine |
| --- | --- | --- | --- | --- |
| `site_access.client_default` hardcoded `frontend/app/ui/player-register-page.tsx:13` | Critical | Frontend leak credenziale | Mostrare in Settings come `gap`, badge red. NO fix in questo WP. | WP separato `WP-FRONTEND-SECRET-AUDIT`: rimozione client-side default + flow registration via temporary token. |
| `health.ready_db_redis` non verifica `backend/app/api/routes/health.py:17-27` | High | Health UI dice OK con DB down | Mostrare in Settings come `gap`, badge yellow. NO fix in questo WP. | WP separato `WP-HEALTH-READINESS-DB-REDIS`: implementare ping ai dependent services. |
| `auth.rbac_fallback` `backend/app/api/dependencies.py:89-99` "missing admin profile = superadmin" | Critical | Privilege escalation se profilo admin manca | Mostrare in Settings come `gap`, badge red. **Backend endpoint Settings NON deve usare questo fallback** (Slice S2 esplicito). | WP separato `WP-AUTH-RBAC-EXPLICIT-PROFILE`: rimuovere fallback, richiedere profilo esplicito. |
| `cms_v2_lab.admin_token_in_query` `frontend/app/ui/admin-shell-panel.tsx:81` | High | URL/log/history exposure di admin token | Mostrare in Settings come `gap`, badge yellow. NO fix in questo WP. | WP separato `WP-CMS-V2-LAB-TOKEN-HANDOFF`: postMessage o cookie httpOnly invece di query string. |

Questo write-up è il valore principale del WP. Senza, è solo "una tabella".

### 4.2 Endpoint Settings: superadmin-only NON usa RBAC fallback

Brief Slice S2 dice "do not rely on 'missing admin profile means superadmin'
for this endpoint; require an explicit superadmin profile or add a
CTO-approved compatibility exception".

**Decisione CTO obbligatoria:** **non usare il fallback**. Endpoint Settings
richiede profilo admin esplicito con role `superadmin`. Se utente passa il
gate dependencies del fallback ma non ha profilo esplicito, endpoint Settings
restituisce 403 con `CK.AUTH.FORBIDDEN` (dipende da WP1 per il codice; se
WP1 non ancora merged, usare codice legacy temporaneo).

Aggiungere test: utente con admin token ma senza profilo esplicito NON può
leggere Settings.

### 4.3 Game Registry Health (Slice S4) - source of truth

Brief Slice S4 dice "show each game: backend code registered, frontend
player registry present, title-editor registry present, finance/replay
descriptor present, error namespace present, smoke status".

Verificato in codice: registries esistono in 3 luoghi diversi:

- `backend/app/modules/platform/game_codes.py` - tuple
- `frontend/app/ui/player-game-registry.ts` - dict
- `frontend/app/ui/title-editor/engine-editor-registry.ts:35` - dict

**Decisione CTO obbligatoria:** Parte A dichiara:

- backend `game_codes.py` è la source of truth in MVP;
- frontend registries sono adapter del backend, devono concordare;
- Settings health row mostra: backend ✅, player registry ✅, title-editor ✅,
  finance/replay descriptor (deriva da WP3) ✅, error namespace (deriva da
  WP1) ✅;
- ❌ in qualunque colonna = badge red + nome WP che lo risolverà.

Questo richiede che WP3 (Finance Registry) e WP1 (Error Foundation) siano
mergiati prima che Slice S4 produca dati significativi. Altrimenti Slice S4
mostra "in attesa di WP3/WP1".

### 4.4 Capability matrix mancante

Come WP1/WP2/WP3, brief manca capability matrix. Aggiungere. Template:

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Descriptor contract | n/a | NEW | n/a | n/a | n/a | n/a | NEW | UPDATE | TBD | code-backed list |
| Backend read model superadmin-only | n/a | NEW | NEW | n/a | n/a | n/a | NEW | UPDATE | TBD | masking applied |
| Frontend Platform Settings UI | n/a | n/a | parse | NEW | n/a | NEW | NEW | UPDATE | TBD | no editable input |
| Game registry health | n/a | NEW | extend | NEW | n/a | n/a | NEW | UPDATE | TBD | aggregator |
| Error Matrix placeholder | n/a | n/a | n/a | NEW | n/a | n/a | NEW | UPDATE | TBD | blocked by WP1 |
| Gap risk write-up doc | n/a | n/a | n/a | n/a | n/a | n/a | n/a | NEW | TBD | sub-WPs created |

## 5. Correzioni raccomandate

### 5.1 Inventory matrix: aggiunte consigliate

Brief lista 28 setting. Aggiunte CTO consigliate:

| Key | Source | Owner | Visibility | Risk | Notes |
| --- | --- | --- | --- | --- | --- |
| `game_launch.signing_key` | env | security | hidden | critical | Se key separata da `jwt.secret` per launch token. Verificare in `app/core/config.py`. |
| `mines.payout_runtime_path` | code | finance | read_only | critical | `docs/runtime/CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json` - se cambiato senza rebuild, RTP rotto. |
| `boxe.payout_runtime_path` | code | finance | read_only | critical | Idem per BOXE. |
| `hi_lo.payout_runtime_path` | code | finance | read_only | critical | Idem per HI-LO. |
| `frontend.api_base_url` | env (build-time) | infra | read_only | high | Drift produzione vs locale. |
| `i18n.allowed_locales` | code | product | read_only | medium | `("it", "en", "de", "es")` per Mines/BOXE/HI-LO. |
| `crypto_wallet.enabled` | n/a | product | n/a | n/a | Annotare come **future fase 2 produzione** (tua decisione Q3 COINS multivaluta). |
| `replay.retention_online_days` | document | finance/legal | read_only | high | 30 giorni (tua decisione COINS Q10). |
| `replay.retention_cold_storage` | document | finance/legal | read_only | high | TBD legal. |

### 5.2 Audit log dei changes settings (post-MVP)

Quando settings diventeranno editable (post-MVP), serve audit log delle
modifiche. Brief non ne parla. Annotare come `WP-PLATFORM-SETTINGS-AUDIT-LOG`
post-MVP, dipendente da WP2 logging foundation.

### 5.3 Settings status come "fonte di verità" per healthcheck operativi

Slice S4 game registry health è un caso. Espandere il concetto a:

- "feature flags health" (se in futuro avremo feature flags);
- "deploy version vs runtime version mismatch";
- "asset storage path exists / accessible";
- "background jobs running";

Annotare per post-MVP `WP-PLATFORM-OPERATIONAL-HEALTH-DASHBOARD`.

### 5.4 `editable_future` semantica esplicita

Brief usa `editable_future` ma non spiega cosa scatena la trasformazione in
`editable_now`. Proposta CTO: ogni `editable_future` ha campo opzionale
`editable_when` (string descrittiva, es. "after WP-FINANCE-RECONCILIATION
ships", "after legal sign-off", "after WP-AUTH-RBAC-EXPLICIT-PROFILE").
Aiuta a non perdere i pezzi.

## 6. Rischi e blind spot identificati

| # | Rischio | Severità | Mitigazione |
| --- | --- | --- | --- |
| R1 | Settings UI espone secret per bug masking | Critical | Test no-leak (giusto in brief) + manual review |
| R2 | RBAC fallback `superadmin = missing profile` consente bypass Settings | Critical | Endpoint Settings esplicito no-fallback (4.2) |
| R3 | Gap UI mostrati come `gap` ma nessuno apre i WP di fix → debt invisibile | Media | Gap risk write-up con nome WP fix (4.1) |
| R4 | Game Registry Health mostra dati incompleti se WP3/WP1 non mergiati | Media | Slice S4 "in attesa di WP3/WP1" esplicito (4.3) |
| R5 | Inventory matrix incompleta (RTP payout path mancante) | Alta | Aggiungere (5.1) |
| R6 | Capability matrix mancante | Media | Aggiungere (4.4) |
| R7 | Audit log delle modifiche future non pianificato | Bassa | Annotare (5.2) |
| R8 | UI definition list senza disabled inputs ok in pattern, ma test visivo necessario | Bassa | Manual gate (giusto in brief) |

## 7. Anti-pattern check vs Playbook + Memory

| Regola | Verdetto |
| --- | --- |
| Playbook anti-pattern "leaving upload constraints implicit" | ✅ Settings descriptor è esplicito per ogni field. |
| Playbook anti-pattern "treating mockups as background inspiration" | N/A - no visual mockup product. UI pattern definition list standard. |
| Memory `feedback_clean_architecture_priority` | ✅ Read-only, no edits = no shortcut tentati. |
| Memory `feedback_permissions_open_setup` | ✅ Settings NON applicabile a permission system Claude Code. |
| Memory `feedback_michele_validation_style` | ⚠️ Settings UI testabile su localhost:3000 (manual gate giusto). |
| Memory `feedback_capability_matrix_rule` | ⚠️ Brief manca capability matrix. Aggiungere (4.4). |
| Memory `feedback_codex_delivery_communication_rule` | ✅ Slice S5 esplicitamente "blocked by WP1". No "fatto" ambiguo. |
| Memory `feedback_two_step_audit_verifier` | ⚠️ Per audit gap classification (4.1), two-step audit utile: step 1 inventory, step 2 verifica masking effettivo. |

## 8. Dipendenze e sequencing

| Dipendenza | Stato | Risk |
| --- | --- | --- |
| `WP-ERROR-REQUEST-FOUNDATION-MVP` | soft dep (Slice S5 Error Matrix placeholder bloccata) | Le altre 4 slice non sono bloccate |
| `WP-PLATFORM-REQUEST-ID-AND-STRUCTURED-LOGGING-MVP` | soft dep (Slice S4 logging status row mostra info da WP2) | Le altre slice non sono bloccate |
| `WP-FINANCE-REPLAY-REGISTRY-RETENTION` | soft dep (Slice S4 finance descriptor health, retention row) | Le altre slice non sono bloccate |

**Verdetto sequencing:** WP4 = **PARALLELO** a WP2/WP3. Solo S5 e parte di
S4 bloccate. S1+S2+S3 procedono indipendenti.

Se Michele vuole massimizzare throughput: dopo WP1 merge, lanciare in
parallelo Codex su 3 worktree:
- worktree A: WP2 logging
- worktree B: WP3 finance registry
- worktree C: WP4 settings (S1+S2+S3 only, S4/S5 dopo)

Ownership di file disgiunti (WP2 = `backend/app/core/logging.py`; WP3 =
`admin-finance-panel.tsx`, `player-account-page.tsx`, `access_sessions/`;
WP4 = nuovo `backend/app/modules/platform/settings/` + nuovo
`frontend/app/ui/admin-settings-panel.tsx`). Conflitti merge bassi.

## 9. Acceptance criteria - validazione

Brief test gates sono buoni. Aggiunte richieste:

| Gate aggiuntivo | Motivo |
| --- | --- |
| Negative test: utente con admin token ma senza profilo esplicito NON può leggere Settings (no fallback) | 4.2 |
| Test ogni gap descriptor è presente con badge + nome WP fix | 4.1 |
| Test descriptor contract rifiuta row missing `evidence` field | 4 di brief è generale ma `evidence` specifico è critical per supportability |
| Test masking: per ogni row con `visibility = hidden`, response JSON contiene SOLO `configured: bool`, non valore | sicurezza |
| Test masking: per row con `visibility = masked`, response contiene partial value (es. host only) | sicurezza |
| Manual gate: superadmin vede 28+ setting; admin "normale" vede 403 | RBAC |
| Manual gate: per ogni gap critical, badge rosso visibile in UI | 4.1 visibility |

## 10. Stop-and-Ask aggiuntivi

Aggiungere a Parte A:

- se durante S1 si scopre che mascherare un setting richiede una secret-rotation
  (es. JWT secret va rotato per essere safe), Stop-and-Ask (rotation è policy
  separata);
- se S2 endpoint backend richiede modifica `dependencies.py` per non usare il
  fallback (RBAC bug), Stop-and-Ask (potenziale break di altre route che si
  appoggiano al fallback);
- se S4 game registry health richiede backend già conscio di WP3 finance
  descriptor (descriptor non ancora esistente), Stop-and-Ask (S4 può essere
  draftato ma non implementato fino a WP3 ship);
- se Michele chiede di mostrare un valore "configured / missing" anche per
  `hidden`, Stop-and-Ask: brief lo include già, conferma.

## 11. Domande aperte da chiudere con Product Owner (Michele)

**Q1 - Conferma masking severity per ogni hidden:**
- JWT secret: hidden (no value, no hash). ✅
- Mines server seed: hidden. ✅
- DB URL: hidden. ✅
- Site password: hidden. ✅

**Q2 - Inventory aggiunte (5.1):**
- aggiungere RTP payout runtime paths come `read_only critical`?
- aggiungere `replay.retention_online_days = 30` come placeholder doc?
- annotare `crypto_wallet.enabled` come `editable_future = fase 2 produzione`?

(Risposta preferita CTO: sì a tutti e 3.)

**Q3 - Action items per 4 gap critical:**
Ognuno dei 4 gap richiede un WP separato di fix. Michele approva la creazione
di 4 ticket Open Loops?

(Risposta preferita CTO: sì, creare 4 entry P0 o P1 in
`docs/ACTIVE_OPEN_LOOPS.md` per tracking, ma il fix avviene quando arriva il
momento — non MVP di questo WP.)

## 12. Raccomandazione finale per Codex (prompt readiness)

WP è **pronto per Parte A** dopo le 4 correzioni obbligatorie.

Prompt structure consigliato:

```
You are CTO assistant. Parte A: validate approach, counter-propose if gap.
Parte B: execution starts only after CTO approval.

Read:
- docs/PLATFORM_SETTINGS_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md
- docs/PLATFORM_SETTINGS_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md (this)
- docs/PLATFORM_INSTALLATION_SETTINGS_BACKOFFICE_PLAN_2026-05-24.md

Mandatory in Parte A output:
1. Capability matrix (CTO review 4.4)
2. Gap risk write-up per i 4 gap (CTO review 4.1) con nome WP fix proposto
3. Verifica RBAC fallback NON usato in endpoint Settings (CTO review 4.2)
4. Game Registry Health source-of-truth decision (CTO review 4.3)
5. Inventory matrix updated con RTP paths + retention + crypto future (5.1)
6. `editable_when` field per ogni `editable_future` row (5.4)
7. Test plan per masking negativo (CTO review section 9)

Then proceed with Slice S1 (descriptor contract only). S5 BLOCKED until WP1 ships.

Parallel-friendly: questo WP può girare in worktree separato da WP2 + WP3.
```

Stima effort: **10-15 prompts MVP** (Slice S1-S4; S5 +2 dopo WP1 merge).
