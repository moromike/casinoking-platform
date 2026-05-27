Status: ACTIVE
Last meaningful update: 2026-05-27

# Prompt Codex - WP-V3-PREVIEW-LIVE Parte B (esecuzione)

Questo file e' il prompt operativo da consegnare a Codex per eseguire WP-V3-PREVIEW-LIVE.
Brief Parte A approvato: `docs/SITE_V3_WP_PREVIEW_LIVE_BRIEF_2026-05-27.md`.

---

## Prompt da copiare in Codex

```
Lavoro: WP-V3-PREVIEW-LIVE Parte B esecuzione.

Brief Parte A approvato e LOCKATO:
docs/SITE_V3_WP_PREVIEW_LIVE_BRIEF_2026-05-27.md

Decisione UX lockata (sezione 14 del brief):
- Pannello preview live in fondo, larghezza intera, collassabile, espanso di default.
- Persistere lo stato espanso/collassato in localStorage chiave `site_v3_preview_panel_expanded`.

Vincoli non negoziabili (da rispettare letteralmente):
1. NON leggere `site_v3_page_versions` per il preview. Leggere `site_v3_pages` + `site_v3_modules`
   correnti.
2. Token DRAFT-PREVIEW mai in query string. Solo header `X-Draft-Preview-Token`.
3. Riusare component `SiteV3PublicPage` con prop opzionale `mode: 'published' | 'preview'`.
   NON duplicare il component.
4. Audit `site_v3.preview_token.issue` obbligatorio in `admin_audit_events` con `source=site_v3`.
5. Regression zero su endpoint published e su Site V1 player (login/register/account/cashier/game runtime).
6. HTML sanitization applicata anche al preview (stessa allowlist del publish).
7. Mai modificare il published-only contract delle route esistenti.
8. Mai cacheare il preview (`Cache-Control: no-store`).

Env nuove (chiedere conferma prima di scrivere infra/docker/.env):
- `SITE_V3_DRAFT_PREVIEW_SECRET` (random 64 char hex, separato dagli altri secret)
- `SITE_V3_PUBLIC_BASE_URL` (default `http://localhost:3001`)

Error codes nuovi (namespace `SITEV3.PREVIEW.*`):
- TOKEN_MISSING, TOKEN_INVALID, TOKEN_EXPIRED, TOKEN_SCOPE_MISMATCH, TOKEN_STALE, PAGE_NOT_FOUND.

Sequenza commit attesa (atomici, leggibili):

1. `feat(site-v3): backend config and secret for draft preview`
   - aggiunge env vars in `backend/app/core/config.py`
   - placeholder in `infra/docker/.env`
   - NESSUN endpoint nuovo qui

2. `feat(site-v3): preview service and helper build_snapshot_from_modules`
   - nuovo file `backend/app/modules/platform/site_v3/preview_service.py` (issue_token, validate_token)
   - estrai helper `build_snapshot_from_modules` da `service.py::publish_page` (refactor minimo,
     stessa logica gia' esistente, nessun cambio di comportamento del publish)
   - publish_page continua a passare tutti i test esistenti

3. `feat(site-v3): admin endpoint draft-preview-token`
   - in `backend/app/api/routes/site_v3_admin.py`
   - protetto da `require_admin_area("games")`
   - audit `site_v3.preview_token.issue`

4. `feat(site-v3): public endpoint preview-draft`
   - in `backend/app/api/routes/site_v3_public.py`
   - header `X-Draft-Preview-Token` obbligatorio
   - tutti gli error codes implementati
   - sanitize HTML applicato

5. `test(site-v3): contract test draft preview admin and public`
   - `tests/contract/test_site_v3_draft_preview.py`
   - verde

6. `test(site-v3): security test preview token isolation`
   - `tests/integration/test_site_v3_preview_security.py`
   - verde

7. `feat(site-v3): public preview route and renderer mode prop`
   - `frontend-v3/app/preview/[token]/page.tsx` nuovo
   - `frontend-v3/app/lib/preview.ts` nuovo
   - `frontend-v3/app/ui/site-v3-public-page.tsx` modificato per accettare `mode` prop
   - `frontend-v3/app/ui/preview-banner.tsx` nuovo

8. `feat(site-v3): admin preview panel collapsible bottom-wide`
   - `frontend/app/ui/site-v3-admin/site-v3-draft-preview-panel.tsx` nuovo
   - integrazione in `frontend/app/ui/site-v3-admin/site-v3-admin-builder.tsx` su 4 viste
     (pageDetail, composition, moduleInstance, validation)
   - CSS in `frontend/app/globals.css`
   - localStorage chiave `site_v3_preview_panel_expanded`
   - debounce 1000ms su dirty change
   - bottoni "Refresh" e "Open in new tab"

9. `test(site-v3): browser smoke preview panel`
   - test Playwright/Selenium che apre `/admin/site-v3`, carica home draft, modifica un campo,
     vede l'iframe aggiornarsi, verifica banner preview, verifica localStorage stato

10. `docs(site-v3): update manual roadmap and open loops for preview live`
    - `docs/BACKOFFICE_MANUAL.md` sezione Site V3 preview
    - `docs/ACTIVE_OPEN_LOOPS.md` entry WP chiuso
    - `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md` entry log con discovery/why/what/affects

Branch: `feature/site-v3-wp-preview-live` da `main`.

Capability matrix end-to-end attesa (a chiusura):

| Capability | DB | Backend | API | Admin UI | Public UI | CSS | Test | Docs | Stato |
|---|---|---|---|---|---|---|---|---|---|
| Token issue | n/a | preview_service | POST | n/a | n/a | n/a | contract | brief | green |
| Preview snapshot | n/a | service refactor | GET header | n/a | route /preview | banner | contract+security | brief | green |
| Admin panel | n/a | n/a | client | new component on 4 views | n/a | iframe responsive | browser | manual | green |
| Audit token issue | n/a | preview_service | n/a | n/a | n/a | n/a | integration | brief | green |
| HTML sanitize preview | n/a | engine reuse | n/a | n/a | renderer reuse | n/a | regression | brief | green |
| Published endpoints invariati | n/a | n/a | n/a | n/a | n/a | n/a | regression | brief | green |

Stop-before-code:
- conferma a Michele se le env var possono essere aggiunte a infra/docker/.env (placeholder)
- conferma branch name + base
- iniziare con commit 1 (config), NON saltare ordine commit

Domanda Codex prima di Parte B:
- conferma che ti aspetti riusare `SiteV3PublicPage` con `mode` prop (non duplicare)
- conferma struttura JWT proposta

Definition of Done:
- 10 commit atomici sopra
- PR `feature/site-v3-wp-preview-live` con capability matrix verde
- Walkthrough Michele su `:3000/admin/site-v3`: caricare home, modificare hero_banner.headline,
  vedere iframe aggiornarsi
- V1 player (login, register, account, mines, boxe, hi-lo) zero regression
- Test esistenti Site V3 published-only restano verdi
```

---

## Note CTO per chi consegna il prompt

- Verifica che il brief Parte A sia stato letto da Codex (linea 1 del prompt).
- Se Codex propone alternative architetturali (es. WebSocket invece di polling debounced,
  oppure usare cookie HttpOnly invece di header token), valutare CTO prima di accettare.
- Il "Domanda Codex prima di Parte B" e' deliberato: Codex deve confermare i due punti
  prima di partire. Questo evita drift architetturale.

## Sessione Codex consigliata

- Tempo stimato: 1 sessione lunga (4-8 ore consecutive di lavoro Codex) oppure 2 sessioni
  separate (commit 1-6 backend + test in una, commit 7-10 frontend + docs nell'altra).
- Multiagentica NON consigliata: commit interdipendenti, serializzazione e' piu' sicura.
