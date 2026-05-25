Status: ACTIVE
Last meaningful update: 2026-05-25

# Site V3 - WP4 Public Renderer MVP Brief Parte A

## 0. Executive Verdict

WP4 e' stato approvato e implementato il 2026-05-25 su
`feature/site-v3-wp4-public-renderer`. WP2 e WP3 sono chiusi: il backend
pubblica snapshot published-only e il builder admin vive dentro
`localhost:3000/admin/site-v3`.

WP4 deve creare il renderer pubblico Site V3 in una nuova app `frontend-v3/`
su `localhost:3001`.

Scope Parte A:

- documento only;
- nessun file `frontend-v3/` creato;
- nessuna route backend creata;
- nessuna modifica a `frontend/` player/admin V1;
- nessuna modifica a `cms_v2_*`;
- nessuna modifica a wallet, ledger, giochi runtime o backoffice games.

Decisione CTO/Codex: WP4 e' green solo se rende una pagina published reale,
da API pubbliche, senza token admin, senza leggere draft, con layout bello e
responsive. Un renderer tecnico "a blocchi" non e' sufficiente.

## 0.1 Implementation Closure

Output implementato:

- `.gitignore` aggiornato per tracciare i sorgenti `frontend-v3/`;
- nuova app Next.js `frontend-v3/`;
- dev/start su porta `3001`;
- API client public-only con default `http://localhost:8000/api/v1`;
- route `/` per `page_code=home`;
- route `/pages/[page_code]` per testare pagine published dinamiche;
- renderers pubblici per i 7 moduli MVP;
- game grid e featured game risolti tramite `/games/library`;
- fallback per pagina non pubblicata;
- CSS responsive senza overflow orizzontale nei gate testati;
- contract test statico boundary;
- browser smoke che pubblica una pagina test, apre `:3001`, verifica desktop
  e mobile, e non usa admin token.

## 1. Required Reading Per Parte B

Prima del codice WP4 leggere in ordine:

1. `docs/README.md`
2. `docs/TASK_EXECUTION_GUARDRAILS.md`
3. `docs/DOCUMENTATION_MAINTENANCE.md`
4. `docs/SITE_V3_SCOPE_AND_ARCHITECTURE_PLAN_2026-05-25.md`
5. `docs/SITE_V3_PRODUCT_CONTRACT_2026-05-25.md`
6. `docs/SITE_V3_MODULE_TAXONOMY_2026-05-25.md`
7. `docs/SITE_V3_LIFECYCLE_API_SECURITY_PLAN_2026-05-25.md`
8. `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md`
9. `docs/SITE_V3_WP2_BACKEND_BRIEF_2026-05-25.md`
10. `docs/SITE_V3_WP3_ADMIN_BUILDER_BRIEF_2026-05-25.md`
11. backend public contract reale:
    - `backend/app/api/routes/site_v3_public.py`
    - `backend/app/modules/platform/site_v3/service.py`
    - `backend/app/modules/platform/catalog/library_service.py`
12. frontend V1 solo come reference read-only:
    - `frontend/app/ui/player-lobby-page.tsx`
    - `frontend/app/ui/site/*`

## 2. Current Public Backend Contract

WP4 consuma solo endpoint pubblici.

| Endpoint | Metodo | Uso renderer |
| --- | --- | --- |
| `/site-v3/sites/{site_code}/pages/{page_code}?locale=it` | GET | carica lo snapshot published della pagina. |
| `/site-v3/sites/{site_code}/navigation?locale=it` | GET | trova `global_header` / `global_footer` published dove disponibili. |
| `/site-v3/sites/{site_code}/manifest?locale=it` | GET | lista pagine published e manifest moduli pubblici. |
| `/games/library?site_code={site_code}` | GET | dati catalogo pubblici per `game_grid` e `featured_game`. |

Regole:

- nessun endpoint `/admin/*` nel renderer pubblico;
- nessun token admin o player richiesto per leggere una pagina published;
- errori `SITEV3.PAGE.NOT_FOUND` e `SITEV3.PAGE.NOT_PUBLISHED` generano una
  pagina fallback pubblica, non un crash tecnico;
- `game_grid` e `featured_game` non duplicano dati gioco: usano `title_code`
  nello snapshot e risolvono display/card/mode dal catalogo pubblico.

## 3. Public Snapshot Shape

`GET /site-v3/sites/casinoking/pages/home?locale=it` ritorna envelope platform:

```json
{
  "success": true,
  "data": {
    "site_code": "casinoking",
    "page_code": "home",
    "locale": "it",
    "title": "Homepage",
    "published_version": 1,
    "version_id": "uuid",
    "published_at": "2026-05-25T12:00:00+00:00",
    "modules": [
      {
        "id": "uuid",
        "module_code": "hero_banner",
        "schema_version": 1,
        "slot_key": "main",
        "sort_order": 0,
        "config_json": {}
      }
    ]
  }
}
```

WP4 deve tipizzare questo shape in `frontend-v3/`, senza importare type da
`frontend/app/ui/site-v3-admin/*`.

## 4. Frontend V3 App Boundary

Target:

```text
frontend-v3/
  app/
  public/
  scripts/
  package.json
  package-lock.json
  next.config.ts
  tsconfig.json
```

Decisione proposta:

- usare Next.js come `frontend/`, con dependency minime `next`, `react`,
  `react-dom`, TypeScript;
- porta dev `3001`;
- `NEXT_PUBLIC_API_BASE_URL` opzionale, default `http://localhost:8000`;
- niente auth admin;
- niente dipendenza runtime da `frontend/`;
- niente import da `frontend-v2/`;
- copiare solo pattern semplici quando serve, non componenti monolitici V1.

Nota repo importante: `.gitignore` oggi contiene `frontend-v3/` per evitare
commit accidentali prima di WP4. Parte B deve sostituire quella regola con una
nota di ownership e lasciare tracciabili i sorgenti `frontend-v3/`; gli artefatti
`**/.next`, `**/node_modules`, `**/out`, `**/dist` sono gia' ignorati.

## 5. Routing Target

MVP routes:

| Route `frontend-v3` | Page code | Note |
| --- | --- | --- |
| `/` | `home` | homepage default. |
| `/pages/[page_code]` | dynamic | utile per testare altre pagine published. |
| `/not-found` o fallback interno | n/a | errore pubblico pulito. |

Parametri query ammessi:

- `site_code`, default `casinoking`;
- `locale`, default `it`.

Parametri vietati:

- admin token;
- draft flag;
- preview admin.

## 6. Module Renderer Contract

Ogni modulo MVP deve avere renderer pubblico dedicato.

| Module | Public behavior MVP | Fallback |
| --- | --- | --- |
| `global_header` | brand, nav links, login/account link V1. | header minimale brand-only. |
| `hero_banner` | headline, body, CTA gioco/path, media public URL se presente. | testo senza media. |
| `game_grid` | card grid da catalogo pubblico filtrata da `title_codes` se presenti. | empty state elegante. |
| `featured_game` | card grande con title, card asset, demo/real CTA. | fallback nascosto con warning console dev-only. |
| `promo_band` | banda editoriale con copy, CTA URL/path, media se presente. | render copy-only. |
| `rich_text_safe` | HTML gia' validato/sanitizzato backend, render con allowlist CSS. | se vuoto non renderizzare. |
| `global_footer` | legal text + link list. | footer minimale. |

Il renderer deve gestire module unknown senza crash:

- mostrare fallback invisibile o piccolo warning non tecnico in dev;
- non rompere la pagina;
- registrare il codice modulo in console solo in development.

## 7. Game Links And V1 Handoff

Site V3 non sostituisce login/account/cashier o game runtime.

Link target MVP:

| Intent | Route |
| --- | --- |
| Login | `http://localhost:3000/login` |
| Account | `http://localhost:3000/account` |
| Gioco demo | `http://localhost:3000/{gameRoute}?title_code={title_code}&mode=demo` o launch cashier V1 se disponibile |
| Gioco real | launch cashier / route V1 esistente, senza inventare wallet flow |

Parte B deve verificare il routing reale in `frontend/app/ui/player-lobby-page.tsx`
prima di fissare i link. Se esiste un helper launch V1 riusabile solo copiando
troppo codice, preferire link semplice e documentare il follow-up.

## 8. Visual Direction MVP

WP4 non deve sembrare "lab".

Direzione:

- casino lobby premium, scura ma leggibile;
- hero reale come primo segnale;
- game grid ordinata e scansionabile;
- card con asset veri quando disponibili;
- footer e header sobri;
- nessuna barra di scorrimento orizzontale;
- mobile portrait trattato come gate, non come dopo-pensiero;
- testo sempre leggibile, niente bianco su fondo chiaro;
- niente "module inspector" visibile al player.

Il public renderer puo' usare placeholder solo se la configurazione published
manca di asset, ma il placeholder deve sembrare intenzionale.

## 9. Asset URL Policy

Asset source ammesse:

- `asset_ref.public_url` nello snapshot;
- game card `public_url` da `/games/library`;
- asset pubblico statico in `frontend-v3/public/` solo per placeholder
  dichiarati.

Regole:

- non importare asset da `assets/` direttamente;
- non esporre file path locali;
- URL backend relativi vanno risolti rispetto a `NEXT_PUBLIC_API_BASE_URL`;
- se `public_url` e' esterno, renderizzarlo solo come immagine/video normale,
  non come HTML.

## 10. Tests And Gates Parte B

Gate build:

- `cd frontend-v3 && npm run build` PASS;
- `cd frontend-v3 && npm run lint` o script equivalente PASS se configurato;
- `frontend` V1 build non deve rompersi se toccata `.gitignore`/docs.

Gate contract:

- public API non richiede admin token;
- `/` carica `home` published;
- pagina draft/non published mostra fallback, non contenuto draft;
- `game_grid` consuma `/games/library` e non dati hardcoded;
- unknown module non crasha.

Gate browser:

- `localhost:3001/` desktop 1365x768;
- mobile portrait 390x844;
- mobile landscape 844x390;
- nessun overflow orizzontale;
- CTA gioco/account puntano a V1;
- Product Owner walkthrough su `:3001`.

Gate isolamento:

- `frontend/` V1 non modificato salvo eventuale doc/config non runtime;
- `cms_v2_*` non toccato;
- `backend/` non toccato salvo test fixture se indispensabile;
- `frontend-v2/` non toccato;
- wallet/ledger/game runtime non toccati.

## 11. Test Data Strategy

Parte B deve poter testare anche se non esiste ancora una pagina Site V3
published manuale.

Opzioni accettate:

1. fixture backend/test che crea e pubblica `home` via API/service;
2. script dev `tools/site_v3_seed_home.py` idempotente, solo se approvato;
3. istruzioni manuali usando `/admin/site-v3` per creare `home`.

Default CTO: per test automatizzati usare fixture; per demo locale fornire uno
script seed idempotente solo se il Product Owner deve aprire `:3001` subito.

## 12. File Ownership Parte B

Consentito:

- `.gitignore` per rendere tracciabile `frontend-v3/`;
- `frontend-v3/**` sorgenti;
- `tests/contract/test_site_v3_public_renderer_contract.py`;
- `tests/integration/test_site_v3_public_renderer_browser.py`;
- docs Site V3 / README / active loops.

Vietato:

- `frontend-v2/**`;
- `frontend/app/ui/player-lobby-page.tsx` salvo Stop-and-Ask;
- `frontend/app/ui/site-v3-admin/**` salvo bug minimo scoperto e approvato;
- `backend/app/api/routes/site_v3_*` salvo Stop-and-Ask;
- wallet/ledger/game runtime.

## 13. Commit Sequence Raccomandata Parte B

1. `chore(site-v3): allow tracking frontend-v3 public renderer source`
2. `feat(site-v3): scaffold public renderer app on port 3001`
3. `feat(site-v3): add public api client and snapshot types`
4. `feat(site-v3): render header hero promo rich text and footer modules`
5. `feat(site-v3): render game grid and featured game from public catalog`
6. `feat(site-v3): add responsive public visual polish`
7. `test(site-v3): cover public renderer published-only gates`
8. `docs(site-v3): update wp4 capability matrix and operating notes`

## 14. Effort Stimato Parte B

Stima: 10-18 prompt.

| Slice | Prompt stimati | Note |
| --- | --- | --- |
| scaffold + gitignore | 1-2 | Include package/Next config/port 3001. |
| API client/types | 2 | Envelope, errors, catalog join. |
| module renderers static/content | 3-4 | Header/hero/promo/rich text/footer. |
| games modules | 2-3 | Catalog join, CTA V1, card assets. |
| visual responsive | 2-4 | Desktop/mobile/overflow gate. |
| tests/docs | 2-3 | Browser, contract, capability matrix. |

## 15. Stop-And-Ask

Fermarsi e chiedere CTO/Michele se:

- `frontend-v3/` non puo' essere tracciato senza rompere la governance repo;
- il public backend endpoint non espone abbastanza dati per renderizzare una
  pagina reale;
- serve un nuovo endpoint backend per catalog/game cards oltre
  `/games/library`;
- il routing V1 per gioco real/demo richiede refactor wallet/cashier;
- il renderer richiede leggere draft o admin API;
- il visual MVP rischia di sembrare un lab tecnico;
- mobile produce overflow orizzontale non risolvibile con CSS locale.

## 16. Capability Matrix WP4

| Capability | Backend/API | Public UI | Tests | Docs | Stato target |
| --- | --- | --- | --- | --- | --- |
| Published page fetch | WP2 green | WP4 green | contract/browser | roadmap/brief | Green |
| Published-only enforcement | WP2 green | WP4 fallback green | contract/browser | lifecycle | Green |
| Module renderer 7 MVP | WP2 manifest | WP4 green | renderer smoke | taxonomy | Green |
| Game catalog consume | `/games/library` green | WP4 green | contract/browser | taxonomy | Green |
| V1 handoff links | V1 route existing | WP4 links | browser/manual pending | product contract | Green-major |
| Responsive/no horizontal scroll | n/a | WP4 CSS green in smoke | browser desktop/mobile | module taxonomy | Green |
| V1 isolation | no backend/V1 change | no frontend V1 change | contract/regression | README/open loops | Green |
| Product owner gate | n/a | walkthrough `:3001` pending | manual pending | README/open loops | Required for final visual closure |

## 17. Decision Brief Per CTO/Michele

Default consigliati:

- approvare WP4 Parte B con nuova app `frontend-v3/` tracciata in git;
- correggere `.gitignore` in Parte B per permettere i sorgenti `frontend-v3/`;
- usare endpoint pubblici esistenti, niente nuove API backend nel MVP;
- usare `/games/library` per risolvere card e modalita' dei giochi;
- homepage default `page_code=home`;
- renderer `:3001` senza admin token;
- product walkthrough obbligatorio prima di chiamare WP4 green.
