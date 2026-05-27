Status: ACTIVE
Last meaningful update: 2026-05-27

# Site V3 - WP-V3-PREVIEW-LIVE Brief Parte A

## 0. Executive Verdict

Site V3 oggi ha un builder admin funzionante (`/admin/site-v3` su `:3000`) e un
renderer pubblico (`frontend-v3/` su `:3001`) che mostra solo le pagine
**published**. L'operatore CMS modifica un draft, salva, valida e pubblica al
buio: l'unico modo per vedere il risultato visivo è **pubblicare** e aprire
`:3001`. Questo è il pain point operativo #1 segnalato dalla review CTO del
2026-05-27 ed è il blocco principale all'usabilità quotidiana del CMS.

Scope WP-V3-PREVIEW-LIVE: aggiungere un **pannello preview persistente** nel
builder admin che renderizza il **draft corrente** via iframe verso una route
preview-only del renderer pubblico, autorizzata da un **draft-preview token
server-only**, mai esposta in query string, mai accessibile senza
autenticazione admin.

Scope Parte A (questo documento):

- documento only;
- nessun codice scritto;
- nessuna route backend creata;
- nessuna migration DB richiesta (in compenso WP-V3-DB-MIGRATION-ALEMBIC e' WP separato);
- nessuna modifica a `frontend/` admin shell V1 fuori da `/admin/site-v3`;
- nessuna modifica a Site V1 player, giochi, wallet, ledger, runtime;
- nessuna modifica a `cms_v2_*` o `frontend-v2/`;
- nessuna modifica al contratto **published-only** del renderer pubblico per le
  route esistenti (`/`, `/pages/[page_code]`, `/site-v3/sites/.../pages/...`).

Decisione CTO: il preview-draft NON deve mai inquinare il contratto
published-only. Una route separata (`/preview/[token]`) e un endpoint pubblico
separato (`GET .../preview-draft` con header token) garantiscono che il
codice published-only resti invariante. Il token deve essere server-only,
short-lived, scoped alla singola coppia `(site_code, page_code)` e mai
visibile lato player.

## 1. Required Reading Per Parte B

Prima di scrivere codice WP-V3-PREVIEW-LIVE leggere in ordine:

1. `docs/README.md`
2. `docs/TASK_EXECUTION_GUARDRAILS.md`
3. `docs/DOCUMENTATION_MAINTENANCE.md`
4. `docs/AI_CRITICAL_JUDGMENT_RULES.md`
5. `docs/SITE_V3_PRODUCT_CONTRACT_2026-05-25.md`
6. `docs/SITE_V3_MODULE_TAXONOMY_2026-05-25.md`
7. `docs/SITE_V3_LIFECYCLE_API_SECURITY_PLAN_2026-05-25.md`
8. `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md`
9. `docs/SITE_V3_ADMIN_NAVIGATION_RESTRUCTURE_APPROACH_2026-05-26.md`
10. Backend Site V3 reale:
    - `backend/app/api/routes/site_v3_admin.py`
    - `backend/app/api/routes/site_v3_public.py`
    - `backend/app/modules/platform/site_v3/service.py`
    - `backend/app/modules/platform/site_v3/repository.py`
    - `backend/app/modules/platform/site_v3/validation/engine.py`
    - `backend/app/modules/platform/site_v3/manifests/modules.py`
11. Frontend admin Site V3 reale:
    - `frontend/app/admin/site-v3/page.tsx`
    - `frontend/app/ui/site-v3-admin/site-v3-admin-builder.tsx`
    - `frontend/app/ui/site-v3-admin/site-v3-admin-descriptors.ts`
12. Frontend pubblico Site V3 reale:
    - `frontend-v3/app/page.tsx`
    - `frontend-v3/app/pages/[page_code]/page.tsx`
    - `frontend-v3/app/lib/api.ts`
    - `frontend-v3/app/ui/site-v3-public-page.tsx`
    - `frontend-v3/app/ui/modules/*`
13. Pattern token JWT esistente nel backend (per riferimento implementativo):
    - `backend/app/modules/auth/security.py`
    - `backend/app/modules/platform/game_launch/service.py` (preview_token admin)

Non leggere oltre il necessario. Distinguere file effettivamente letti da file
solo individuati nelle citazioni.

## 2. Current State (post WP5 sesta/settima/ottava/nona/decima/undicesima tranche)

### 2.1 Renderer pubblico

`frontend-v3/` Next.js 15 su `:3001`. Routes:

- `/` -> SSR home con `pageCode="home"`
- `/pages/[page_code]` -> SSR pagina dinamica

Tutte chiamano `frontend-v3/app/lib/api.ts::loadSiteV3Page(pageCode)` che
chiama `GET /site-v3/sites/{site}/pages/{page_code}?locale={locale}` con
`cache: "no-store"`. Restituisce snapshot **published** o fallback se la
pagina non e' pubblicata.

### 2.2 Builder admin

`frontend/app/ui/site-v3-admin/site-v3-admin-builder.tsx` (~2289 righe, 81KB)
contiene 11 viste navigate da `currentView`: overview, siteSettings, pages,
pageDetail, composition, modules, moduleCategory, moduleType,
moduleInstance, validation, versions.

Stato attuale "preview" nel builder:

- `SiteV3DraftPreview` (rig 1920-1945) e' solo una preview **testuale** in tab
  "Versions": estrae `headline` da ogni modulo e mostra una lista plain. Non
  e' un rendering reale.

### 2.3 Cosa manca

L'operatore CMS modifica un draft e non puo' vedere il risultato visivo prima
di pubblicare. Il render reale e' raggiungibile solo dopo `publish`, aprendo
`:3001/pages/{page_code}`. Il giro di feedback e' lento e disincentiva la
pubblicazione: l'operatore tende a sotto-iterare oppure a pubblicare versioni
non rifinite per vederle.

## 3. Target

Aggiungere un pannello preview persistente nel builder admin che mostra
il **draft corrente** renderizzato lato pubblico, in iframe, autorizzato da
un token server-only.

### 3.1 Comportamento atteso

1. Sulla schermata di pagina (Settings / Composition / Module instance /
   Validation) il builder mostra un pannello "Preview live" come sezione
   collassabile in fondo o come pannello laterale (decisione visuale Parte B).
2. Al primo apertura del pannello, il builder chiede un draft-preview-token
   al backend admin.
3. Il pannello mostra un iframe pointing a `:3001/preview/{token}`.
4. Il renderer pubblico, sulla route `/preview/{token}`, valida il token, chiama
   l'endpoint pubblico `preview-draft` con il token in header, riceve uno
   snapshot **del draft corrente** (non published), renderizza i moduli con
   gli stessi component dei published, con un **banner top** "PREVIEW DRAFT
   - non pubblicato".
5. Quando l'operatore modifica un campo nel builder e l'editor state cambia,
   l'iframe si refresha automaticamente (debounced 1000ms) chiedendo
   eventualmente un nuovo token se il draft_version e' avanzato.

### 3.2 Sicurezza

- token JWT con payload `{site_code, page_code, draft_version, admin_id, exp}`
- expire 15 minuti
- mai in query string
- header dedicato `X-Draft-Preview-Token`
- endpoint `preview-draft` valida token, controlla `site_code` e `page_code`,
  controlla che `draft_version` nel token sia >= `draft_version` corrente DB
  (rigetto se draft e' stato modificato dopo emissione token e admin non ha
  refreshato)
- il token NON puo' essere usato per accedere ad altre pagine
- il token NON puo' essere usato dopo expire
- l'endpoint published rimane invariato: NON deve mai accettare il
  draft-preview-token in alternativa al published

### 3.3 Vincoli architetturali

- nessuna modifica al published-only contract delle route esistenti;
- nessuna modifica al rich-text sanitization (preview applica stessa sanitize
  della publish);
- nessuna modifica al snapshot immutabile di `site_v3_page_versions`;
- l'iframe deve essere same-origin (via Next.js rewrite **OR** allow-list CSP)
  per evitare CORS lockout in dev locale;
- niente caching aggressivo sul preview (`cache: no-store`).

## 4. Approach Tecnico

### 4.1 Backend admin endpoint

Nuovo endpoint sotto `backend/app/api/routes/site_v3_admin.py`:

```text
POST /admin/site-v3/sites/{site_code}/pages/{page_code}/draft-preview-token
```

- Auth: `require_admin_area("games")`.
- Body: nessuno (page_code/site_code in path).
- Response: `{ token: string, preview_url: string, expires_at: ISO8601 }`.
- preview_url = `{SITE_V3_PUBLIC_BASE_URL}/preview/{token}` (da config).
- Comportamento:
  1. Carica `page` dal repository (lock NOT necessario).
  2. Se page non esiste -> 404 `SITEV3.PREVIEW.PAGE_NOT_FOUND`.
  3. Costruisce payload JWT: `{site_code, page_code, draft_version, admin_id, iat, exp}`.
  4. Firma con SECRET dedicato `SITE_V3_DRAFT_PREVIEW_SECRET` (env, separato da
     gli altri secret).
  5. Restituisce.
- Audit: scrivere `site_v3.preview_token.issue` con
  `(admin_id, site_code, page_code, draft_version, exp)` su `admin_audit_events`.

### 4.2 Backend public endpoint

Nuovo endpoint sotto `backend/app/api/routes/site_v3_public.py`:

```text
GET /site-v3/sites/{site_code}/pages/{page_code}/preview-draft?locale={locale}
Header: X-Draft-Preview-Token: <token>
```

- Auth: nessuna (il token e' l'autorizzazione).
- Comportamento:
  1. Legge `X-Draft-Preview-Token` dal header. Se assente -> 401
     `SITEV3.PREVIEW.TOKEN_MISSING`.
  2. Valida JWT con `SITE_V3_DRAFT_PREVIEW_SECRET`. Se invalido -> 401
     `SITEV3.PREVIEW.TOKEN_INVALID`.
  3. Controlla `exp`. Se scaduto -> 401 `SITEV3.PREVIEW.TOKEN_EXPIRED`.
  4. Controlla che `site_code` e `page_code` del payload combacino col path.
     Se no -> 403 `SITEV3.PREVIEW.TOKEN_SCOPE_MISMATCH`.
  5. Carica page + modules correnti dal DB.
  6. Verifica che `draft_version` corrente >= `draft_version` del payload.
     Se draft e' stato avanzato e il token e' obsoleto, ritorna 409
     `SITEV3.PREVIEW.TOKEN_STALE` con `current_draft_version` nel payload, che
     il client puo' usare per richiedere un nuovo token.
  7. Costruisce snapshot **identico a quello del published** ma con
     `is_preview: true`, `draft_version` invece di `published_version`,
     `published_at: null`.
  8. Applica la stessa sanitizzazione HTML del publish flow
     (`sanitize_html=True` in `_normalize_modules`).
  9. Restituisce snapshot.
- Cache: `Cache-Control: no-store`. Mai cacheare.
- Logging: log request con `request_id` (gia' middleware) + admin_id estratto
  dal token.

### 4.3 Service layer

Nuovo file `backend/app/modules/platform/site_v3/preview_service.py`:

- funzione `issue_draft_preview_token(session, site_code, page_code, admin_id) -> dict`
- funzione `validate_draft_preview_token(token) -> dict` (payload validato)
- funzione `build_draft_snapshot(session, site_code, page_code, locale) -> dict`
  che costruisce snapshot da `site_v3_pages` + `site_v3_modules` correnti,
  non da `site_v3_page_versions`.

Riusare il piu' possibile la logica di build snapshot gia' presente in
`service.py::publish_page` ma estratta in helper condiviso. NON duplicare
codice; estrarre, NON copy-paste.

### 4.4 Renderer pubblico

Nuova route `frontend-v3/app/preview/[token]/page.tsx`:

- SSR con `cache: no-store`.
- Estrae `token` dal path param.
- Estrae `site_code` e `page_code` dal token decodificato lato server (oppure
  fa una pre-call per ottenere il payload non firmato).
- Chiama `GET /site-v3/sites/{site_code}/pages/{page_code}/preview-draft` con
  `X-Draft-Preview-Token: {token}` header.
- Renderizza con gli stessi component dei published page
  (`SiteV3PublicPage` riusato), con prop `mode="preview"` che mostra un
  banner top sticky "PREVIEW DRAFT - non pubblicato".
- Error states:
  - 401/403/410 -> mostra messaggio "Preview token non valido o scaduto"
  - 409 (stale) -> messaggio "Draft modificato, ricarica dal builder"

Nuova lib `frontend-v3/app/lib/preview.ts` con funzione
`loadSiteV3Preview(token)`.

Estrazione consigliata: trasformare `SiteV3PublicPage` per accettare prop
opzionale `mode: 'published' | 'preview'`. Default 'published'. NON duplicare
il component.

### 4.5 Admin builder UI

Nuovo component `frontend/app/ui/site-v3-admin/site-v3-draft-preview-panel.tsx`:

- prop: `{ siteCode, pageCode, draftVersion, isDirty }`.
- state interno: `token, previewUrl, tokenExpiresAt, isLoading, error`.
- effect:
  - on mount o cambio `pageCode/draftVersion` -> chiama
    `POST /admin/site-v3/.../draft-preview-token` e popola state.
  - on `isDirty` change debounced 1000ms -> chiede nuovo token.
- render:
  - se `error` -> messaggio con bottone "Ritenta".
  - se loading -> spinner.
  - se OK -> iframe a `previewUrl` con `sandbox="allow-same-origin allow-scripts"`.
  - badge "Preview aggiornata <N secondi fa>".
  - bottone manual "Refresh preview".
  - bottone "Open in new tab" che apre `previewUrl` in tab separata.

Mount del component in `site-v3-admin-builder.tsx` come sezione collassabile
(default aperta) sotto le schermate di pagina:

- pageDetail
- composition
- moduleInstance
- validation

NON montare su: pages list, modules library, overview, siteSettings,
moduleCategory, moduleType (sono superfici non legate a una pagina specifica).

Lo stato "espanso/collassato" deve essere persistito in localStorage chiave
`site_v3_preview_panel_expanded` per non dimenticare la preferenza utente.

### 4.6 Config / env

Nuova variabile env backend:

```
SITE_V3_DRAFT_PREVIEW_SECRET=<random 64 char hex>
SITE_V3_PUBLIC_BASE_URL=http://localhost:3001
```

Aggiungere a:
- `infra/docker/.env` (placeholder con istruzioni)
- `backend/app/core/config.py`
- documentation in `docs/LOCAL_ENV_RESTART_PROCEDURE.md` se rilevante per setup

NON committare secret reali nel repo.

## 5. Error Cases Espliciti

| Caso | Comportamento atteso | Error code |
| --- | --- | --- |
| Token assente in header | 401 + messaggio admin | SITEV3.PREVIEW.TOKEN_MISSING |
| Token firma invalida | 401 + messaggio admin | SITEV3.PREVIEW.TOKEN_INVALID |
| Token scaduto | 401 + messaggio "Token scaduto, ricarica" | SITEV3.PREVIEW.TOKEN_EXPIRED |
| Token per altra pagina | 403 | SITEV3.PREVIEW.TOKEN_SCOPE_MISMATCH |
| Draft avanzato dopo emissione token | 409 + current_draft_version | SITEV3.PREVIEW.TOKEN_STALE |
| Page non esiste | 404 | SITEV3.PREVIEW.PAGE_NOT_FOUND |
| Draft senza moduli | 200 con snapshot vuoto + banner "Nessun modulo nel draft" | (no error) |
| Iframe CSP block | log errore, fallback "Apri in nuova tab" | (no error) |
| `SITE_V3_DRAFT_PREVIEW_SECRET` non configurato | startup error backend | startup |

Tutti gli error code seguono il pattern `SITEV3.PREVIEW.<CASE>` per uniformita'
con namespace esistente `SITEV3.*` definito in WP2.

## 6. Test Plan

### 6.1 Contract test backend

File: `tests/contract/test_site_v3_draft_preview.py`

Test:
- POST draft-preview-token con admin valido -> 200 + token + url
- POST draft-preview-token senza auth -> 401
- POST draft-preview-token per page inesistente -> 404
- GET preview-draft con token valido -> 200 + snapshot draft
- GET preview-draft senza token -> 401
- GET preview-draft con token scaduto -> 401
- GET preview-draft con token scope mismatch -> 403
- GET preview-draft con token stale (draft avanzato) -> 409 + current_draft_version
- GET preview-draft NON aggiorna `site_v3_page_versions`
- GET preview-draft NON modifica audit `publish/save_draft` (audit suo: `preview_token.issue`)

### 6.2 Security test

File: `tests/integration/test_site_v3_preview_security.py`

Test:
- preview-draft endpoint NON e' raggiungibile con admin JWT (deve usare draft-preview-token)
- published endpoint NON accetta draft-preview-token
- published endpoint per pagina draft non pubblicata -> 404 (invariato)
- token non puo' essere usato come bearer per `/admin/site-v3/*` endpoint
- token mai in query string nei log/access log
- HTML sanitization applicata anche al preview (regression del manifesto rich_text_safe)

### 6.3 Browser smoke admin

Script Playwright (o equivalente esistente) che:
1. Login admin
2. Apre `/admin/site-v3`
3. Carica home page draft
4. Verifica che il pannello preview sia visibile e mostri il draft
5. Modifica `hero_banner.headline`
6. Aspetta debounce + refresh iframe
7. Verifica nuovo contenuto nell'iframe (assertion su DOM dell'iframe se possibile, altrimenti screenshot pre/post)
8. Bottone "Open in new tab" funziona
9. Sezione preview collassabile salva stato in localStorage

### 6.4 Regression invariata

- `frontend-v3/app/page.tsx` -> home published carica come prima
- `frontend-v3/app/pages/[page_code]/page.tsx` -> dynamic published carica come prima
- `/site-v3/sites/.../pages/{page_code}` published endpoint -> response identica pre/post WP
- `site_v3_page_versions` table NON ha nuove righe da preview
- audit eventi `publish/save_draft/validate/archive` invariati
- player V1 (login, register, account, cashier, mines, boxe, hi-lo) zero regression

## 7. Stop-Before-Code

Non aprire codice se:

- Michele non ha approvato la Parte A (questo documento).
- L'env var `SITE_V3_DRAFT_PREVIEW_SECRET` non e' stata aggiunta alla config.
- L'endpoint preview-draft viene proposto senza header dedicato (token in query).
- Il preview viene proposto leggendo `site_v3_page_versions` invece di
  `site_v3_pages` + `site_v3_modules`.
- Il sanitize HTML viene saltato per il preview.
- Il published-only contract viene mischiato con preview (es. lo stesso
  endpoint accetta entrambi).
- Si propone di duplicare `SiteV3PublicPage` invece di estendere con prop `mode`.
- Si propone caching del preview snapshot.
- Si propone di non emettere audit token issue.

Se uno di questi salta -> rifiutare il commit, riaprire la Parte A.

## 8. File Paths Coinvolti

### Backend
- nuovo: `backend/app/api/routes/site_v3_admin.py` -> aggiunge endpoint `draft-preview-token`
- nuovo: `backend/app/api/routes/site_v3_public.py` -> aggiunge endpoint `preview-draft`
- nuovo: `backend/app/modules/platform/site_v3/preview_service.py`
- modifica: `backend/app/modules/platform/site_v3/service.py` -> estrai helper `build_snapshot_from_modules`
- modifica: `backend/app/core/config.py` -> nuovi env var
- modifica: `infra/docker/.env` -> placeholder

### Frontend admin
- nuovo: `frontend/app/ui/site-v3-admin/site-v3-draft-preview-panel.tsx`
- modifica: `frontend/app/ui/site-v3-admin/site-v3-admin-builder.tsx` -> mount panel su 4 viste
- modifica: `frontend/app/globals.css` -> CSS panel + iframe responsive

### Frontend pubblico
- nuovo: `frontend-v3/app/preview/[token]/page.tsx`
- nuovo: `frontend-v3/app/lib/preview.ts`
- modifica: `frontend-v3/app/ui/site-v3-public-page.tsx` -> prop `mode: 'published' | 'preview'`
- nuovo: `frontend-v3/app/ui/preview-banner.tsx`

### Test
- nuovo: `tests/contract/test_site_v3_draft_preview.py`
- nuovo: `tests/integration/test_site_v3_preview_security.py`
- nuovo: `tests/browser/test_site_v3_admin_preview_panel.py` (o equivalente Playwright)

### Docs
- aggiornare: `docs/BACKOFFICE_MANUAL.md` -> sezione Site V3 preview
- aggiornare: `docs/ACTIVE_OPEN_LOOPS.md` -> riga WP avviato/chiuso
- aggiornare: `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md` -> entry log
- nuovo (questo file): `docs/SITE_V3_WP_PREVIEW_LIVE_BRIEF_2026-05-27.md`

## 9. Effort

Stima Parte B: **8-12 prompt Codex**, distribuibili in 1-2 sessioni lunghe.

Breakdown:
- backend endpoints + service: 2-3 prompt
- frontend admin panel + integration: 2-3 prompt
- frontend public route + preview-banner + lib: 1-2 prompt
- contract test: 1 prompt
- security test: 1 prompt
- browser smoke: 1 prompt
- docs/audit/logs update: 1 prompt

## 10. Definition of Done

Il WP e' chiuso quando tutti i punti sotto sono veri:

| Capability | Verifica | Stato target |
| --- | --- | --- |
| Endpoint admin draft-preview-token | contract test green + audit emesso | green |
| Endpoint public preview-draft | contract test green + security test green | green |
| Preview panel visibile in admin | browser smoke green su 4 viste | green |
| Auto-refresh debounced 1s on dirty | browser smoke verifica | green |
| Token mai in query | grep nei log + security test | green |
| Published endpoint invariato | contract regression green | green |
| Snapshot draft sanitizzato | manifesto HTML test su rich_text_safe | green |
| Audit token issue su `admin_audit_events` | integration test | green |
| Browser smoke Michele su `:3000/admin/site-v3` | walkthrough demo | green |
| BACKOFFICE_MANUAL.md aggiornato | doc review | green |
| ACTIVE_OPEN_LOOPS.md aggiornato | doc review | green |
| Roadmap entry log inserita | doc review | green |
| V1 player regression zero | smoke run | green |

## 11. Capability Matrix End-to-End

| Capability | DB | Backend | API | Admin UI | Public UI | CSS | Test | Docs | Stato target | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Draft preview token issue | nessuno | preview_service.py | POST draft-preview-token | n/a (header X-Draft-Preview-Token uso interno) | n/a | n/a | contract | brief WP | green | server-only secret JWT |
| Preview draft snapshot | nessuno | preview_service.py + service.py refactor | GET preview-draft | n/a | route /preview/[token] | banner CSS | contract+security | brief WP | green | published-only invariato |
| Preview panel admin | n/a | n/a | client calls token+iframe | new component | n/a | iframe responsive | browser | manual+brief | green | mount su 4 viste di pagina |
| Token security | n/a | sign/verify | header-only, no query | client storage in state | n/a | n/a | security test | brief WP | green | exp 15m, scope page-specific |
| Audit token issue | nessuno (riuso `admin_audit_events`) | preview_service.py | n/a | n/a | n/a | n/a | integration | brief WP | green | source=site_v3, action=preview_token.issue |
| HTML sanitization preview | nessuno | engine.py reuse | n/a | n/a | renderer reuse | n/a | regression | brief WP | green | stessa allowlist publish |

## 12. Implementation Log Entry Format

A chiusura WP, aggiungere entry in roadmap:

```
### [2026-XX-XX] - WP-V3-PREVIEW-LIVE
**Discovery / Decision**: <1-2 righe>
**Why it matters**: <1-3 righe>
**What we did**: <1-3 righe>
**Affects**: <link a file/sezione>
```

Esempio template:

```
### [2026-XX-XX] - WP-V3-PREVIEW-LIVE
**Discovery / Decision**: pannello preview persistente con JWT scoped per (site, page) e iframe same-origin via Next rewrite per dev locale.
**Why it matters**: prima del WP l'operatore pubblicava al buio. Il preview live cambia il giro di feedback da minuti a secondi.
**What we did**: endpoint admin issue + endpoint public preview-draft + panel admin + route /preview/[token] + helper snapshot estratto.
**Affects**: backend/app/modules/platform/site_v3/preview_service.py, frontend/app/ui/site-v3-admin/site-v3-draft-preview-panel.tsx, frontend-v3/app/preview/[token]/page.tsx.
```

## 13. Prompt Codex Esecutivo (Parte B)

Quando Parte A e' approvata, il prompt Codex per Parte B sara' (placeholder
per chat continuity):

```
Lavoro WP-V3-PREVIEW-LIVE Parte B esecuzione.

Brief Parte A approvato: docs/SITE_V3_WP_PREVIEW_LIVE_BRIEF_2026-05-27.md.

Vincoli da rispettare letteralmente:
- non leggere site_v3_page_versions per preview
- token mai in query
- riuso SiteV3PublicPage con prop mode
- audit preview_token.issue obbligatorio
- regression zero su published endpoints e player V1

Sequenza commit suggerita:
1. backend: config env + secret + preview_service.py + endpoint admin issue
2. backend: endpoint public preview-draft + sanitize
3. backend: helper build_snapshot_from_modules estratto da service.py publish
4. backend: contract test + security test
5. frontend admin: preview panel + mount in 4 viste + CSS
6. frontend public: route /preview/[token] + lib preview + banner + mode prop
7. browser smoke admin (Playwright)
8. docs: BACKOFFICE_MANUAL + ACTIVE_OPEN_LOOPS + roadmap entry log

Output finale: PR feature/site-v3-wp-preview-live con 8 commit atomici, capability matrix green.
```

Questo prompt va salvato anche come file separato quando si arriva all'esecuzione.

## 14. Decisione CTO Pending Da Michele

Una sola decisione product/UX prima della Parte B:

- **Posizione visiva del pannello**: collassabile in fondo a tutta larghezza,
  oppure laterale destro fisso, oppure tab dedicata?

Default proposto CTO: **collassabile in fondo a tutta larghezza** (espanso di default),
perche':
- non riduce lo spazio orizzontale dell'editor (preview verticale completa)
- e' coerente con pattern CMS classici (es. WordPress preview)
- mobile-friendly: su schermi stretti collassa naturalmente

Se Michele preferisce laterale o tab, modificare 4.5 di conseguenza prima della
Parte B.

## 15. Stop-Before-Code Riassunto

Tre cose che bloccano la Parte B se non chiarite:

1. approvazione Michele su questo brief
2. decisione UX punto 14 (posizione pannello)
3. conferma env `SITE_V3_DRAFT_PREVIEW_SECRET` puo' essere aggiunta a infra/docker

Nessun codice scritto in Parte A. Tutto cio' che sopra e' progetto, non esecuzione.
