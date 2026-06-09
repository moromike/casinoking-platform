# GMP-5C — BOXE Runtime Launch-Token Consumption (Approccio Parte A)

**Data:** 2026-06-03  
**Scope:** Solo frontend BOXE runtime (`frontend-v3/app/ui/boxe/`). Nessun impatto su Mines/HI-LO/backend.  
**Stato:** Parte A (analisi/approccio). **Nessun file di gioco modificato in questa fase.**

---

## 1. Contesto

GMP-5B (backend) è chiuso:
- Esiste `POST /games/boxe/launch-token` che emette un token real firmato (title_code + site_code + player_id).
- Esiste `POST /games/boxe/start` che accetta opzionalmente l'header `X-Game-Launch-Token`. Quando presente, il backend usa `title_code` e `site_code` dal token invece dei valori del payload. Quando assente, il backend fallbacka al payload legacy (`payload.title_code` + `"casinoking"`).

GMP-5C (runtime/frontend) deve:
1. Ottenere il launch token quando serve (real mode).
2. Passarlo come header `X-Game-Launch-Token` su ogni `POST /games/boxe/start` in real mode.
3. Mantenere il fallback legacy quando il token non c'è (nessuna regressione).
4. Tenere separato il path demo-token (nessun launch token in demo).

---

## 2. Da dove arriva il token nel runtime — mappa reale file:riga

### 2.1 Storage keys già esistenti per BOXE

`frontend-v3/app/ui/game-runtime/game-storage.ts:40-53`
```ts
boxe: {
  accessToken: "casinoking.access_token",
  email: "casinoking.email",
  sessionId: "casinoking.boxe_current_session_id",
  gameLaunchToken: "casinoking.boxe_launch_token",
  gameLaunchTokenExpiresAt: "casinoking.boxe_launch_token_expires_at",
  gameLaunchTitleCode: "casinoking.boxe_launch_title_code",
  demoAnonToken: "ck_boxe_demo_anon_token",
  demoGameLaunchToken: "ck_boxe_demo_game_launch_token",
  // ...
}
```
Le chiavi `gameLaunchToken`, `gameLaunchTokenExpiresAt`, `gameLaunchTitleCode` esistono già nello storage BOXE ma **non sono mai lette/scritte dal codice BOXE runtime attuale**.

### 2.2 Lettura dallo storage snapshot

`frontend-v3/app/ui/game-runtime/game-storage.ts:83-98`  
`readGameStorageSnapshot(storage, namespace)` restituisce già:
```ts
gameLaunchToken: storage.getItem(keys.gameLaunchToken) ?? "",
gameLaunchTokenExpiresAt: storage.getItem(keys.gameLaunchTokenExpiresAt) ?? "",
gameLaunchTitleCode: storage.getItem(keys.gameLaunchTitleCode) ?? "",
```
Quindi `useGameLaunchContext` (che chiama `readGameStorageSnapshot`) espone questi valori in `bootStatus.storageSnapshot`, ma `boxe-standalone.tsx` non li consuma.

### 2.3 Flusso attuale del token (senza launch token)

| Step | File | Riga | Azione |
|------|------|------|--------|
| A | `game-boot-request.ts` | 12-29 | Parsa query params (title_code, mode=demo, preview_token, embed, wallet_source). **Nessun token letto dall'URL.** |
| B | `use-game-launch-context.ts` | 39-52 | Legge `storageSnapshot` da `localStorage` (incluso `gameLaunchToken`, ma viene ignorato). |
| C | `boxe-standalone.tsx` | 79-86 | Chiama `useGameLaunchContext({ storageNamespace: BOXE_GAME_STORAGE_NAMESPACE })`. |
| D | `boxe-standalone.tsx` | 193-194 | Estrae **solo** `storageSnapshot.accessToken` come `tableGateToken`. |
| E | `boxe-standalone.tsx` | 421-433 | Passa `bootStatus.request` e `bootStatus.storageSnapshot.accessToken` a `<BoxeGameplay>`. |
| F | `boxe-gameplay.tsx` | 133-157 | `BoxeGameplay` riceve `bootRequest` e `initialAccessToken`. |
| G | `boxe-gameplay.tsx` | 171 | `const [authToken, setAuthToken] = useState(initialAccessToken);` |
| H | `boxe-gameplay.tsx` | 332-342 | `ensureActionToken()`: se `authToken` truthy → lo restituisce; se vuoto e non demo → throw; se demo → `provisionBoxeDemoPlayer()`. |
| I | `boxe-gameplay.tsx` | 350-366 | `runBoxeActionWithDemoTokenRecovery(token => action(token))` esegue l'azione con il token. |
| J | `use-boxe-runtime.ts` | 261-292 | `startBoxeRound(input)` chiama `apiRequest("/games/boxe/start", { headers: { "Idempotency-Key": ... } }, input.token)`. |
| K | `api.ts` | 145-163 | `apiRequest` aggiunge `Authorization: Bearer <token>` se presente. **Nessun `X-Game-Launch-Token`.** |

**Conclusione:** il token reale fluisce oggi solo come `accessToken` (bearer auth). Il `gameLaunchToken` è inerte in BOXE.

---

## 3. Dove va aggiunto l'header `X-Game-Launch-Token`

### 3.1 Punto di iniezione dell'header

L'header deve essere aggiunto **sulla richiesta `POST /games/boxe/start`**.

Attualmente `startBoxeRound` in `frontend-v3/app/ui/boxe/use-boxe-runtime.ts:261-292` accetta solo:
```ts
type StartBoxeRoundInput = {
  token: string;
  idempotencyKey: string;
  // ... altri campi
};
```

E passa a `apiRequest`:
```ts
apiRequest("/games/boxe/start", {
  method: "POST",
  body: JSON.stringify({ ... }),
  headers: { "Idempotency-Key": input.idempotencyKey },
}, input.token);
```

**Modifica prevista:** aggiungere un campo opzionale `launchToken?: string` a `StartBoxeRoundInput` e, quando presente, includerlo nell'header:
```ts
headers: {
  "Idempotency-Key": input.idempotencyKey,
  ...(input.launchToken ? { "X-Game-Launch-Token": input.launchToken } : {}),
}
```

### 3.2 Chi chiama `startBoxeRound`

`frontend-v3/app/ui/boxe/boxe-gameplay.tsx:412` (circa):
```ts
runBoxeActionWithDemoTokenRecovery((token) => startBoxeRound({ ..., token, ... }))
```

Quindi `boxe-gameplay.tsx` è il punto che risolve il token bearer **e** deve risolvere il launch token per passarlo a `startBoxeRound`.

---

## 4. Come resta il FALLBACK legacy

Il backend già supporta il fallback:
- `backend/app/api/routes/boxe.py:135` — `game_launch_token: str | None = Header(default=None, alias="X-Game-Launch-Token")`
- `backend/app/api/routes/boxe.py:369` — se `not game_launch_token: return None`
- `backend/app/api/routes/boxe.py:149-158` — se nessun launch context, usa `payload.title_code` e `"casinoking"` come site_code.

Nel frontend, il fallback si ottiene semplicemente **non passando** `X-Game-Launch-Token` quando:
1. Il giocatore non ha un token stored valido.
2. Il giocatore è in demo mode (il backend rifiuta i launch token demo).
3. Il backend di launch-token restituisce errore.

La logica di `ensureBoxeLaunchToken` (da aggiungere in Parte B) deve essere:
- Se `isDemoMode` → restituisce `null` (nessun header).
- Se token stored esiste e non scaduto → restituisce il token.
- Se token assente/scaduto → chiama `POST /games/boxe/launch-token`, salva, restituisce.
- Se anche l'issue fallisce → restituisce `null` (fallback legacy).

---

## 5. Come resta SEPARATO il path demo-token

### 5.1 Demo mode flow (oggi)

`boxe-gameplay.tsx:332-342` (`ensureActionToken`):
```ts
if (authToken) return authToken;
if (!isDemoMode) throw new Error("Not authenticated");
return provisionBoxeDemoPlayer();
```

`provisionBoxeDemoPlayer()` chiama `POST /auth/demo` (anonimo, senza bearer token) e ottiene un `access_token` demo.

### 5.2 Separazione GMP-5C

- **Demo mode:** `ensureActionToken()` continua a usare `provisionBoxeDemoPlayer()`. **Nessun launch token viene richiesto, emesso o passato.**
- **Real mode:** `ensureActionToken()` restituisce il bearer token reale (come oggi). Un nuovo helper `ensureBoxeLaunchToken()` (separato) gestisce il launch token per il real start.
- Il backend `boxe.py:159-164` rifiuta esplicitamente i launch token reali su start demo:  
  `"Real BOXE launch tokens cannot start demo rounds"`.

---

## 6. File toccati previsti in Parte B

### 6.1 `frontend-v3/app/ui/boxe/boxe-standalone.tsx`
**Perché:** deve leggere `gameLaunchToken` e `gameLaunchTokenExpiresAt` dallo storage snapshot e passarli a `BoxeGameplay`.

**Righe interessate:**
- 193-194: aggiungere estrazione di `gameLaunchToken` e `gameLaunchTokenExpiresAt`.
- 421-433: aggiungere props a `<BoxeGameplay>`.

### 6.2 `frontend-v3/app/ui/boxe/boxe-gameplay.tsx`
**Perché:** deve ricevere il launch token, mantenerlo in stato, implementare `ensureBoxeLaunchToken()`, e passarlo a `startBoxeRound`.

**Righe interessate:**
- 133-157: aggiungere props `gameLaunchToken`, `gameLaunchTokenExpiresAt`, `setGameLaunchToken`, `setGameLaunchTokenExpiresAt`.
- 171: aggiungere `useState` per il launch token.
- 332-342 (`ensureActionToken`): nessuna modifica al bearer token flow.
- **Nuova funzione** `ensureBoxeLaunchToken()` (vicino a `ensureActionToken` o in helper): logica di validazione/refresh/issue.
- 412 (`startBoxeRound` call): passare `launchToken` come nuovo campo.

### 6.3 `frontend-v3/app/ui/boxe/use-boxe-runtime.ts`
**Perché:** `startBoxeRound` deve accettare e inoltrare `launchToken` come header.

**Righe interessate:**
- 261-292: estendere `StartBoxeRoundInput` con `launchToken?: string` e iniettare l'header.

### 6.4 File NON toccati
- `frontend-v3/app/ui/game-runtime/*` — lo storage e il boot request sono già pronti.
- `frontend-v3/app/lib/api.ts` — `apiRequest` supporta già headers custom via `init.headers`.
- **Mines/HI-LO** — nessuna modifica.
- **Backend** — GMP-5B è chiuso.

---

## 7. Rischi e cosa NON va toccato

| # | Rischio | Mitigazione |
|---|---------|-------------|
| 1 | Regressione demo mode | Il launch token viene richiesto **solo** in real mode. Demo mode non tocca `ensureBoxeLaunchToken`. Test smoke demo conferma. |
| 2 | Regressione fallback legacy | Se `ensureBoxeLaunchToken` restituisce `null`, `startBoxeRound` **non** aggiunge `X-Game-Launch-Token`. Il backend fallbacka al payload. Test smoke real senza token conferma. |
| 3 | Token scaduto in storage | `ensureBoxeLaunchToken` deve controllare `expires_at` lato frontend (la validazione backend avviene solo su `/start`). Se scaduto, chiama `/launch-token` di nuovo. |
| 4 | Conflitto con Mines launch token | BOXE usa storage keys diverse (`casinoking.boxe_launch_token` vs `casinoking.mines_launch_token`). Zero conflitto. |
| 5 | Math/payout/board/RNG | **Fuori scope.** Nessun file di logica di gioco toccato. Solo wiring del token nel layer API. |

**Cosa NON va toccato:**
- `boxe-pyramid-board.tsx`, `boxe-math.ts`, `boxe-replay-viewer.tsx` — logica di gioco.
- `frontend-v3/app/ui/mines/*` — nessun impatto su Mines.
- `frontend-v3/app/ui/hi-lo/*` — nessun impatto su HI-LO.
- Backend — GMP-5B è chiuso.

---

## 8. Micro-step Parte B (gated) e come si verifica

### Step B1 — `boxe-standalone.tsx` wiring
- Aggiungere state e props per `gameLaunchToken` / `gameLaunchTokenExpiresAt`.
- **Gate:** `tsc --noEmit` pulito; smoke demo si apre normalmente.

### Step B2 — `boxe-gameplay.tsx` helper `ensureBoxeLaunchToken`
- Implementare logica:
  1. Se demo → restituisci `null`.
  2. Se token stored esiste e `expires_at` non scaduto → restituisci token.
  3. Altrimenti → `POST /games/boxe/launch-token` (con bearer token).
  4. Salva in storage + stato.
  5. Se errore → restituisci `null` (fallback).
- **Gate:** `tsc --noEmit` pulito; smoke demo si apre (nessun effetto in demo).

### Step B3 — `use-boxe-runtime.ts` header injection
- Aggiungere `launchToken` a `StartBoxeRoundInput`.
- Iniettare `X-Game-Launch-Token` header quando presente.
- **Gate:** `tsc --noEmit` pulito.

### Step B4 — Integration wiring in `boxe-gameplay.tsx`
- Passare `launchToken` da `ensureBoxeLaunchToken()` alla chiamata `startBoxeRound()`.
- **Gate:** `tsc --noEmit` pulito.

### Step B5 — Verifica smoke tripla
1. **Demo mode** (`mode=demo`): gameplay demo si apre, si scommette, si gioca. **Nessun** `X-Game-Launch-Token` deve essere inviato. Conferma via Network tab o proxy log.
2. **Real mode CON token** (player autenticato, `/games/boxe/launch-token` emette token): `POST /games/boxe/start` contiene header `X-Game-Launch-Token`. Il backend usa `title_code` dal token.
3. **Real mode fallback SENZA token** (player autenticato, ma cancelliamo il token dallo storage prima del test): `POST /games/boxe/start` **non** contiene `X-Game-Launch-Token`. Il backend usa `payload.title_code`. Nessuna regressione.

### Step B6 — Regression cross-game
- Smoke Mines e HI-LO demo passano (zero modifiche a questi giochi).

---

## Checklist gate CTO Parte A

- [x] Mappa reale del flusso token confermata con riferimenti file:riga.
- [x] Punto di iniezione header identificato (`use-boxe-runtime.ts:261-292`).
- [x] Fallback legacy documentato (backend supporta già token opzionale).
- [x] Separazione demo-token documentata (demo mode non tocca il launch token).
- [x] File toccati previsti elencati con motivazione.
- [x] Rischi e scope negativo definiti.
- [x] Micro-step Parte B con gate di verifica definiti.
- [x] **Conferma esplicita: nessun file di gioco BOXE sarà modificato senza approvazione CTO.**
