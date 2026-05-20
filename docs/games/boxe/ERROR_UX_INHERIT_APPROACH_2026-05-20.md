Status: ACTIVE
Last meaningful update: 2026-05-21

# BOXE - Error UX Inherit Approach - 2026-05-20

WP: `WP-E-ERROR-UX-INHERIT` - Parte A, approach validation.

## 1. Scope Decision

Questo documento copre solo Parte A. Non autorizza modifiche runtime finche'
CTO/product owner non approvano Parte B.

Obiettivo: rimuovere la UX errore BOXE-only che mostra messaggi backend grezzi
nel gameplay e portare BOXE sul pattern Mines/platform:

- errore classificato in un punto unico;
- copy user-facing controllata;
- nessuna stringa backend grezza in UI player;
- presentazione visuale ereditata da game-runtime/Mines;
- auto-recovery del token demo scaduto/invalido quando possibile.

Out of scope Parte A:

- nessuna modifica codice;
- nessuna modifica backend;
- nessuna modifica auth architecture di Mines o BOXE;
- nessun refactor wallet/ledger/table session;
- nessun cambio visuale Mines in Parte B senza gate zero-diff.

Controproposta critica: il brief dice "auto-recovery 401 in
`ensureActionToken()`". Nello stato corrente `ensureActionToken()` non chiama
un endpoint protetto: restituisce il token cached o ne provisiona uno nuovo.
Il `401 Invalid bearer token` emerge durante `startBoxeRound`,
`revealBoxePick` o `cashoutBoxeRound`. Quindi Parte B non deve aggiungere una
validazione remota a ogni `ensureActionToken()`. Deve invece intercettare il
401 al boundary dell'azione, droppare il token, re-provisionare demo e ritentare
una sola volta con la stessa idempotency key.

## 2. Fonti Lette

- `docs/README.md`.
- `docs/SOURCE_OF_TRUTH.md`.
- `docs/TASK_EXECUTION_GUARDRAILS.md`.
- `docs/DOCUMENTATION_MAINTENANCE.md`.
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`.
- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`, sezioni 6.3 e 13.2.
- `docs/games/boxe/VISUAL_UNIFORMITY_APPROACH_2026-05-20.md`.
- `docs/games/boxe/GAMEPLAY_PYRAMID_APPROACH_2026-05-20.md`.
- `frontend/app/lib/api.ts`.
- `frontend/app/lib/player-storage.ts`.
- `frontend/app/ui/game-runtime/game-boot-shell.tsx`.
- `frontend/app/ui/game-runtime/game-boot-decision-flow.tsx`.
- `frontend/app/ui/game-runtime/game-table-balance-gate.tsx`.
- `frontend/app/ui/game-runtime/game-storage.ts`.
- `frontend/app/ui/mines/mines-standalone.tsx`.
- `frontend/app/ui/mines/mines.css`.
- `frontend/app/ui/mines/i18n/mines-copy-defaults.ts`.
- `frontend/app/ui/boxe/boxe-standalone.tsx`.
- `frontend/app/ui/boxe/boxe-gameplay.tsx`.
- `frontend/app/ui/boxe/use-boxe-runtime.ts`.
- `frontend/app/ui/boxe/boxe.css`.
- `backend/app/api/dependencies.py` individuato per origine dei messaggi 401.

## 3. Audit Mines Error Pattern

Mines non usa un toast runtime per questi errori. Il pattern effettivo e':
handler centralizzato -> status/copy controllata -> `errorDialog` slot shared
-> overlay dialog Mines.

| Surface | Evidence | Implicazione |
| --- | --- | --- |
| Handler centralizzato | `handleGameError(error, context)` in `frontend/app/ui/mines/mines-standalone.tsx:1370`. | Le azioni gameplay non decidono ciascuna il testo finale. |
| Bearer auth classification | `isBearerTokenAuthError` intercettato in `frontend/app/ui/mines/mines-standalone.tsx:1371`; helper definito in `frontend/app/ui/mines/mines-standalone.tsx:1791`. | `401` e messaggi bearer/authenticated user non arrivano grezzi in UI. |
| Clear auth state | `clearAuthState(false)` in `frontend/app/ui/mines/mines-standalone.tsx:1372`; storage shared `clearStoredAuthState` in `frontend/app/ui/game-runtime/game-storage.ts:149`. | Il token invalido viene eliminato dallo storage game-aware. |
| User-facing copy | `copy("errors.auth_invalid")` in `frontend/app/ui/mines/mines-standalone.tsx:1375`. | Copy controllata, localizzabile, non backend-driven. |
| Dialog slot | `errorDialog` costruito in `frontend/app/ui/mines/mines-standalone.tsx:1489` e passato a `GameBootShell` in `frontend/app/ui/mines/mines-standalone.tsx:1668`. | Il runtime shared gia' prevede il canale overlay. |
| Dialog markup | Overlay/card in `frontend/app/ui/mines/mines-standalone.tsx:1490-1503`, con `role="alertdialog"`. | Accessibilita' e visual shell sono gia' consolidate. |
| Copy chain | `buildFriendlyGameErrorMessage` in `frontend/app/ui/mines/mines-standalone.tsx:1839`; network/action mapping in `frontend/app/ui/mines/mines-standalone.tsx:1848-1895`. | Il fallback non deve concatenare automaticamente `error.message`. |
| Network detection | `isNetworkRequestFailure` in `frontend/app/ui/mines/mines-standalone.tsx:1918`. | Le failure fetch hanno copy dedicate per contesto. |
| CSS overlay | `.mines-error-dialog-overlay` in `frontend/app/ui/mines/mines.css:2376`; `.mines-error-dialog` in `frontend/app/ui/mines/mines.css:2387`. | Lo stile da ereditare va estratto in game-runtime, con Mines zero visual diff. |
| Runtime slot | `GameBootShell` riceve `errorDialog` in `frontend/app/ui/game-runtime/game-boot-shell.tsx:26` e lo passa al decision flow in `frontend/app/ui/game-runtime/game-boot-shell.tsx:85`. | Il componente shared puo' ospitare error dialog game-agnostic. |
| Decision flow render | `GameBootDecisionFlow` renderizza `{errorDialog}` in `frontend/app/ui/game-runtime/game-boot-decision-flow.tsx:63`. | BOXE puo' ereditare senza cambiare il container. |

## 4. Audit BOXE Current Error Pattern

BOXE ha due canali locali, entrambi divergenti dal pattern Mines:

- runtime/boot error in `boxe-standalone.tsx`;
- action error inline in `boxe-gameplay.tsx`.

| Surface | Evidence | Problema |
| --- | --- | --- |
| Runtime config error | `setRuntimeError(readErrorMessage(error, "BOXE config non disponibile."))` in `frontend/app/ui/boxe/boxe-standalone.tsx:105`. | `readErrorMessage` concatena il messaggio tecnico. |
| Table balance error | `setRuntimeError(readErrorMessage(error, "Saldo tavolo non disponibile."))` in `frontend/app/ui/boxe/boxe-standalone.tsx:180`. | Canale runtime non usa copy adapter. |
| Real play auth copy | `setRuntimeError("Accedi per giocare con saldo reale.")` in `frontend/app/ui/boxe/boxe-standalone.tsx:195`. | Copy hardcoded locale, non manifest/shared. |
| Table entry error | `setRuntimeError(readErrorMessage(error, "Ingresso tavolo non disponibile."))` in `frontend/app/ui/boxe/boxe-standalone.tsx:218`. | Possibile leakage backend in UI. |
| Runtime error UI | `<div className="boxe-error" role="alert">` in `frontend/app/ui/boxe/boxe-standalone.tsx:313-317`. | Non overlay/dialog, non shared, non Mines-like. |
| Action token | `ensureActionToken()` in `frontend/app/ui/boxe/boxe-gameplay.tsx:237-248` restituisce token cached senza validazione. | Token localStorage invalido sopravvive al rebuild Docker. |
| Start action | `executeStart` usa token in `frontend/app/ui/boxe/boxe-gameplay.tsx:262-273`; catch imposta `readBoxeErrorMessage` in `frontend/app/ui/boxe/boxe-gameplay.tsx:281`. | `401` diventa errore visibile. |
| Reveal action | `executeReveal` usa token in `frontend/app/ui/boxe/boxe-gameplay.tsx:309-316`; catch in `frontend/app/ui/boxe/boxe-gameplay.tsx:326`. | Stesso gap per reveal. |
| Cashout action | `executeCashout` usa token in `frontend/app/ui/boxe/boxe-gameplay.tsx:349-354`; catch in `frontend/app/ui/boxe/boxe-gameplay.tsx:358`. | Stesso gap per cashout. |
| Inline error UI | `.boxe-error.boxe-action-error` renderizzato in `frontend/app/ui/boxe/boxe-gameplay.tsx:735-748`. | Pannello rosso BOXE-only, fuori visual inheritance. |
| Error mapping | `readBoxeErrorMessage` in `frontend/app/ui/boxe/boxe-gameplay.tsx:813-826`. | Copre solo 3 codici; fallback concatena `${fallback} ${error.message}`. |
| CSS locale | `.boxe-action-error` in `frontend/app/ui/boxe/boxe.css:306`; `.boxe-error` in `frontend/app/ui/boxe/boxe.css:313`. | Duplicazione visuale da rimuovere in Parte B. |
| API client | `readErrorMessage` concatena `fallback` e `error.message` in `frontend/app/lib/api.ts:134-140`. | Utile in admin/debug, fragile per player-facing game runtime. |

Origine backend del caso osservato:

- `backend/app/api/dependencies.py:17` emette `Missing or invalid bearer token`;
- `backend/app/api/dependencies.py:39`, `:48`, `:54` emettono
  `Invalid bearer token`;
- `backend/app/api/dependencies.py:62` emette `Authenticated user not found`.

## 5. Decisione Architetturale

Estrarre una piccola superficie shared in `frontend/app/ui/game-runtime/`.
Nomi suggeriti:

- `game-action-error.tsx`;
- `game-error-copy-adapter.ts`;
- estensione CSS in `game-runtime.css`.

### 5.1 Componenti

`GameActionError` deve coprire il caso action retryable e il caso runtime
blocking senza duplicare CSS game-specific:

```ts
type GameActionErrorProps = {
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  onDismiss?: () => void;
  testId?: string;
};
```

Per Parte B la presentazione primaria deve essere dialog/overlay, per ereditare
Mines. Non introdurre un nuovo toast o una nuova barra rossa.

Mines puo' restare consumatore del markup attuale o migrare a
`GameActionError` solo se il gate visuale e' zero-diff. BOXE deve consumare il
nuovo componente e rimuovere `.boxe-action-error` / `.boxe-error` per action
errors.

### 5.2 Copy Adapter

`GameErrorCopyAdapter` non deve importare Mines o BOXE. Deve classificare
`ApiRequestError` e network errors in un tipo shared:

```ts
type GameErrorKind =
  | "auth_invalid"
  | "validation"
  | "insufficient_balance"
  | "round_closed"
  | "network"
  | "service_unavailable"
  | "reload_required"
  | "generic";
```

Ogni gioco fornisce una mappa copy:

```ts
type GameErrorCopyMap = Record<GameErrorKind, string>;
```

Questo evita import cross-game e rende HI-LO beneficiario automatico del
pattern: nuovo gioco = copy map + retry/recovery hooks.

### 5.3 Runtime Ownership

Responsabilita' shared:

- classificare status/code/message tecnico;
- bloccare leakage del messaggio backend;
- fornire markup/CSS accessibile;
- supportare retry/dismiss.

Responsabilita' game-specific:

- scegliere context (`start`, `reveal`, `cashout`, `load-runtime`);
- eseguire cleanup auth/session;
- decidere se retry automatico e' consentito;
- fornire copy localizzata.

## 6. Auto-Recovery 401

### 6.1 BOXE

Implementazione proposta in Parte B:

1. Aggiungere helper locale o shared:

```ts
function isBearerTokenAuthError(error: unknown): boolean
```

Allineare il matcher a Mines:

- `ApiRequestError.status === 401`;
- message contiene `bearer token` o `authenticated user`;
- eventualmente `403 account is not active`.

2. Aggiungere una funzione di esecuzione action:

```ts
async function runBoxeActionWithDemoTokenRecovery<T>(
  action: (token: string) => Promise<T>,
): Promise<T>
```

3. Flusso:

- usa `ensureActionToken()` normalmente;
- se l'API ritorna `401` bearer e `bootRequest.forceDemoMode === true`:
  - rimuove `casinoking.access_token` e `casinoking.email` tramite
    `clearStoredAuthState(window.localStorage, BOXE_GAME_STORAGE_NAMESPACE)`;
  - resetta `authToken`;
  - chiama `provisionBoxeDemoPlayer()`;
  - salva il nuovo token;
  - ritenta una sola volta la stessa action con la stessa idempotency key;
- se fallisce ancora, mostra copy user-facing.

4. Se `forceDemoMode === false`, niente auto-provision. Mostrare copy auth
sessione scaduta e richiedere ricarica/login.

### 6.2 Mines Gap Analogo

Mines ha gia' il pattern di classificazione e clear auth per bearer invalid in
`frontend/app/ui/mines/mines-standalone.tsx:1370-1377`. Non ha lo stesso gap
demo osservato per BOXE perche' il demo Mines usa `/demo/token` e
game-launch-token demo, non `/auth/demo` bearer cached come BOXE.

Gap residuo Mines: il caso bearer invalid real mode e' user-visible con
`errors.auth_invalid`; non e' silent auto-recovery. Non cambiarlo in WP-E senza
decisione separata, perche' toccherebbe auth/session policy del reference game.

## 7. Mapping Tecnico -> Copy User-Facing

| Technical signal | User-facing copy | Recovery | Note |
| --- | --- | --- | --- |
| `401` + `bearer token` / `authenticated user` | `Sessione scaduta, ricarica` | Demo BOXE: silent re-provision + retry once. Real: dialog. | Non mostrare `Invalid bearer token`. |
| `403 account is not active` | `Sessione scaduta, ricarica` | No silent retry in real. | Match Mines classifier. |
| `422` / `VALIDATION_ERROR` | Messaggio tradotto specifico, es. `Controlla puntata e selezioni.` | No auto retry. | Non mostrare payload grezzo. |
| `INSUFFICIENT_BALANCE` | `Saldo insufficiente.` | No retry automatico. | Business error. |
| `BONUS_WALLET_EMPTY` | `Saldo bonus vuoto.` | No retry automatico. | Business error. |
| `ROUND_ALREADY_CLOSED` | `La mano e' gia' conclusa.` | Offer dismiss/reload, no blind retry. | Existing BOXE copy ok. |
| Network/fetch failure | `Connessione instabile. Riprova.` | Manual retry. | Context can refine start/play/sync. |
| `5xx` / `API_ERROR` | `Servizio temporaneamente non disponibile.` | Manual retry. | No backend detail. |
| Unknown error | `Operazione non riuscita. Riprova.` | Manual retry if idempotent. | No `error.message` append in player UI. |

## 8. Capability Matrix End-To-End

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Stato | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Shared game action error | N/A | N/A | N/A | N/A | Mines-compatible dialog consumed by BOXE; HI-LO ready | `frontend/app/ui/game-runtime/game-runtime.css` | `tests/visual/artifacts/wave3_error_ux_2026-05-21/boxe_action_error_dialog.png` | Questo doc | Parte B completed | Mines not migrated in WP-E; shared component is BOXE consumer only. |
| Error classification adapter | N/A | N/A | Reads `ApiRequestError` only | N/A | No backend string leakage | N/A | Frontend build + manual visual 422/401 harness | Questo doc | Parte B completed | `api.ts` global fallback unchanged for admin/debug surfaces. |
| BOXE 401 demo recovery | N/A | No change | Same endpoints | N/A | Silent re-provision + retry once | N/A | `tests/visual/artifacts/wave3_error_ux_2026-05-21/boxe_401_recovery_note.md` | Questo doc | Parte B completed | Same idempotency key is reused by the action closure. |
| BOXE runtime error slot | N/A | N/A | N/A | N/A | `GameBootShell` `errorDialog` uses shared overlay | Shared dialog CSS | `tests/visual/artifacts/wave3_error_ux_2026-05-21/boxe_runtime_error_dialog.png` | Questo doc | Parte B completed | Local `.boxe-error` / `.boxe-action-error` removed. |
| Mines visual stability | N/A | N/A | N/A | N/A | Zero code diff in `frontend/app/ui/mines/**` | No Mines CSS touched | Git diff gate | Questo doc | Gate passed by scope | Mines migration intentionally out of scope for WP-E Parte B. |

### 8.1 Parte B Gate Evidence Paths

- Report visuale: `tests/visual/artifacts/wave3_error_ux_2026-05-21/REPORT.md`.
- Harness Playwright: `tests/visual/capture_wave3_error_ux.py`.
- Dialog overlay: `tests/visual/artifacts/wave3_error_ux_2026-05-21/boxe_action_error_dialog.png`.
- Runtime overlay: `tests/visual/artifacts/wave3_error_ux_2026-05-21/boxe_runtime_error_dialog.png`.
- 401 recovery evidence: `tests/visual/artifacts/wave3_error_ux_2026-05-21/boxe_401_recovery_note.md`.
- Diff gate: `git diff --name-only -- frontend/app/ui/mines backend frontend/app/ui/boxe/boxe-pyramid-board.tsx` must stay empty.

### 8.2 Parte B Gate Result

- `npm run build` in `frontend/`: PASS.
- `python -m pytest tests/integration/test_boxe_smoke.py::test_boxe_demo_safe_sequence_cashout_resets_to_bet -q`: PASS.
- `python tests/visual/capture_wave3_error_ux.py --url "http://localhost:3200/boxe?title_code=boxe001&mode=demo&embed=1"`: PASS.
- 401 recovery assertion: PASS (`Bearer expired-token` then `Bearer fresh-token`, same idempotency key, no action dialog).
- Scope gate Mines/backend/board: PASS, no diff under `frontend/app/ui/mines`, `backend`, `frontend/app/ui/boxe/boxe-pyramid-board.tsx`.

## 9. Parte B Granularity

Raccomandazione: 4 sub-commit.

1. `feat(game-runtime): add shared game action error copy adapter`
   - `GameActionError`;
   - `GameErrorCopyAdapter`;
   - CSS shared copied from Mines dialog pattern with neutral class names.
2. `refactor(mines): wire shared error dialog without visual drift`
   - Solo se il zero-diff gate e' sostenibile.
   - Se rischioso, mantenere Mines markup e aggiungere shared component per
     BOXE/HI-LO con CSS equivalente documentato.
3. `refactor(boxe): inherit runtime error UX and block backend error leakage`
   - BOXE runtime and action errors use shared adapter/component.
   - Remove `.boxe-action-error` duplication.
4. `fix(boxe): recover invalid demo bearer token once`
   - Drop cached token and re-provision demo on 401.
   - Add/adjust smoke tests.

## 10. Stop-and-Ask Attesi

STOP se:

- migrare Mines al componente shared produce visual diff non-zero e non e'
  correggibile senza riscrivere CSS Mines;
- il retry automatico richiede cambiare auth architecture BOXE da `/auth/demo`
  a launch-token demo Mines-like;
- il retry automatico potrebbe duplicare una start/cashout per perdita
  idempotency key;
- product vuole una copy diversa da `Sessione scaduta, ricarica`;
- serve mostrare dettaglio tecnico backend in player UI;
- il fix richiede modifiche backend o schema.

## 11. Effort Estimate Prompt

- BOXE-only hardening senza migrare Mines: 0.5 giornata, 2-3 prompt.
- Shared `game-runtime` + BOXE consume + tests: 1-1.5 giornate, 4-6 prompt.
- Shared extraction con Mines zero-diff visual gate completo: 2 giornate,
  6-8 prompt.

Prompt Parte B suggerito: "Implementa WP-E Parte B in due fasi: prima adapter
e BOXE consume, poi Mines zero-diff solo se sostenibile; nessun messaggio
backend grezzo in player UI; invalid demo bearer token auto-recovery una volta;
Mines visual baseline obbligatoria."
