Status: ACTIVE
Last meaningful update: 2026-05-25

# Site V3 - Audit Rescue del Lab Gemini

## 0. Executive Verdict

Il lab `frontend-v2/` non va promosso a Site V3 cosi' com'e'. Contiene alcuni
pezzi utili da recuperare, ma la sua architettura nasce dal lato sbagliato:
mette il builder/editor su `:3001`, mentre il prodotto target richiede:

- builder Site V3 dentro l'admin esistente su `localhost:3000`;
- renderer pubblico Site V3 su `localhost:3001`;
- Site V1 intatto fino a promozione esplicita;
- nessun token admin in query string;
- nessun commit di `.next` / `node_modules`;
- nessuna pubblicazione "green" senza walkthrough Product Owner.

Questa audit e' doc-only e serve a decidere cosa salvare, cosa buttare e quale
WP aprire dopo.

## 1. Scope Auditato

| Area | File | Esito |
| --- | --- | --- |
| Lab app shell | `frontend-v2/app/page.tsx` | Builder/lab, non renderer pubblico. |
| Registry moduli | `frontend-v2/app/lib/modules/registry.ts` | Recuperabile come idea, non come contratto finale. |
| Preview/editor/picker | `frontend-v2/app/ui/*` | Recuperabili come UX seed, da riscrivere nel design admin. |
| Renderer moduli | `frontend-v2/app/ui/modules/ModuleRenderer.tsx` | Placeholder, richiede sanitizzazione/contratti. |
| Client API lab | `frontend-v2/app/lib/api-cms.ts` | Pattern base, ma legato a `/admin/cms-v2`. |
| API backend | `backend/app/api/routes/cms_v2.py` | MVP lab, non ancora Site V3 production-grade. |
| Service backend | `backend/app/modules/platform/cms_v2/service.py` | CRUD minimale, no versioning/snapshot. |
| Schema DB | `backend/migrations/sql/0044__cms_v2_persistence.sql` | Seed utile, incompleto per V3. |
| Entry admin | `frontend/app/ui/admin-shell-panel.tsx` | Link rinominato `Site v3 (Lab)`, apre ancora `:3001`. |

## 2. Findings Pignoli

| # | Finding | Evidence | Verdetto |
| --- | --- | --- | --- |
| 1 | `frontend-v2` e' un Module Composer, non il sito pubblico. | `frontend-v2/app/page.tsx:181` mostra `CMS v2 / Module Composer Lab`; `:189`, `:257`, `:268` montano preview/editor/picker. | Riscrivere boundary. |
| 2 | Il lab conserva token admin da URL/localStorage. | `frontend-v2/app/page.tsx:23-33`, `:62-63`, `:93-94`. | Da non usare in V3 finale. |
| 3 | Il registry moduli e' un buon seme, ma troppo piccolo/lab-oriented. | `frontend-v2/app/lib/modules/registry.ts:48`, `:55`, `:67`, `:86`, `:102`, `:113`. | Salvage con refactor. |
| 4 | Editor schema-driven recuperabile. | `frontend-v2/app/ui/ModuleEditor.tsx:28`. | Salvage con validazione, help text, i18n, asset picker. |
| 5 | Picker per categorie recuperabile. | `frontend-v2/app/ui/ModulePicker.tsx:42`. | Salvage UX, non visual finale. |
| 6 | Preview con controlli di ordine/delete e debug registry e' da ripulire. | `frontend-v2/app/ui/ComposerPreview.tsx:84`, `:147`, `:154`. | Salvage concetto, riscrivere UI. |
| 7 | Rich text usa HTML non sanitizzato nel renderer. | `frontend-v2/app/ui/modules/ModuleRenderer.tsx:82`. | Security gate prima di production. |
| 8 | Client API parla solo con endpoint admin CMS v2. | `frontend-v2/app/lib/api-cms.ts:5`, `:9`, `:13`, `:20`. | Rifare contratto Site V3 admin/public. |
| 9 | Backend usa HTTPException raw, non AppError/platform registry. | `backend/app/api/routes/cms_v2.py:20`, `:26`, `:36`, `:60`. | Da allineare a error foundation. |
| 10 | Publish e' update diretto dello status, senza snapshot/versione. | `backend/app/api/routes/cms_v2.py:31-46`. | Non basta per V3. |
| 11 | Public endpoint commenta published-only ma non lo applica davvero. | `backend/app/api/routes/cms_v2.py:56`, `:62`. | Bug/gap da chiudere prima del renderer. |
| 12 | Save draft elimina e reinserisce tutti i moduli. | `backend/app/modules/platform/cms_v2/service.py:107`, `:113`. | Accettabile solo come MVP lab; serve audit trail/versioning. |
| 13 | Update draft aggiorna solo il titolo pagina, non status/snapshot. | `backend/app/modules/platform/cms_v2/service.py:87-88`. | Contratto incompleto. |
| 14 | Schema DB non ha versioning, locale, snapshot published, module schema version, validation state. | `backend/migrations/sql/0044__cms_v2_persistence.sql:9-38`. | Seed utile, non finale. |
| 15 | Admin link e' stato rinominato correttamente a `Site v3 (Lab)`, ma apre ancora il lab. | `frontend/app/ui/admin-shell-panel.tsx:58`, `:109`. | OK temporaneo, non finale. |
| 16 | `frontend-v2` contiene build/dependency artifacts non versionati. | Inventory locale: `.next` 122 file, `node_modules` 9099 file. | Non committare. |

## 3. Salvage / Rewrite Matrix

| Oggetto | Azione | Note |
| --- | --- | --- |
| `ModuleManifest` / `MODULE_REGISTRY` | Salvage con refactor | Diventa `SiteV3ModuleRegistry`, con schema version, category, surfaces, i18n, validation, preview renderer, public renderer. |
| `configSchema` editor | Salvage con refactor | Va integrato nel design admin, con descrizioni, validation, required/max length, asset picker e traduzioni. |
| `ModulePicker` | Salvage UX | Buona idea di catalogo moduli; visual da rifare. |
| `ComposerPreview` | Salvage concetto | Serve preview draft/live stabile, senza debug registry product-facing. |
| `ModuleRenderer` | Reference only | I renderer sono placeholder; rich text richiede sanitizzazione. |
| `frontend-v2/app/page.tsx` | Non salvare come architettura | Troppa logica mischiata: token, state builder, save/publish, shell. |
| `api-cms.ts` | Reference only | Utile come wrapper fetch, ma endpoint e auth vanno rifatti. |
| `cms_v2` backend | Seed tecnico | Rinominare/avvolgere come Site V3 solo dopo contratto. |
| `cms_v2` migration | Seed tecnico | Richiede estensioni: snapshot/versioning/locale/schema_version/audit. |
| `.next`, `node_modules` | Non committare | Sono artefatti, non sorgente. |

## 4. V1 Coexistence Matrix

| Surface V1 | Site V3 deve fare | Note |
| --- | --- | --- |
| Lobby/player site attuale | Non toccare | V1 resta operativo su `:3000`. |
| Game library/cards | Consumare via adapter | Niente duplicazione del catalogo giochi. |
| Launch cashier / real-money gate | Riutilizzare routing esistente | V3 non inventa un nuovo money gate. |
| Login/register/account | Fuori MVP V3 | Link/route a V1 salvo decisione product esplicita. |
| Game runtime pages | Fuori scope V3 | Mines/BOXE/HI-LO restano stand-alone. |
| Site assets esistenti | Consumare da API/registry | Non duplicare asset ownership. |
| Admin shell | Builder vive qui | No admin token handoff esterno. |

## 5. Target Architecture Decision

Decisione proposta:

1. `frontend-v2/` resta artefatto di consulto fino a cleanup.
2. Il builder Site V3 finale vive dentro `frontend/app/ui/...` admin su `:3000`.
3. Il renderer pubblico Site V3 vive su `:3001`, ma solo quando esiste il
   contratto backend/public API.
4. Il backend non deve restare concettualmente `cms_v2`: il naming puo' essere
   migrato gradualmente, ma i nuovi documenti e UI devono dire `Site V3`.
5. Ogni modulo Site V3 deve avere due renderer distinti:
   - admin preview renderer;
   - public player renderer.
6. Ogni modulo deve dichiarare cosa salva, cosa pubblica, come valida e come
   gestisce mobile.

## 6. Next WP Raccomandati

| Ordine | WP | Tipo | Output |
| --- | --- | --- | --- |
| 1 | WP-SITEV3-CONTRACT | Doc-only | Product scope, module taxonomy, lifecycle draft/live, security, visual principles, questions closed. |
| 2 | WP-SITEV3-BACKEND-MVP | Code | Admin/public API, draft/published snapshot, validation, audit, tests. |
| 3 | WP-SITEV3-ADMIN-BUILDER-MVP | Code | Builder dentro admin `:3000`, page list, module picker/editor, preview, save/publish. |
| 4 | WP-SITEV3-PUBLIC-RENDERER-MVP | Code | Renderer pubblico su `:3001`, published pages only, responsive modules. |
| 5 | WP-SITEV3-PRODUCT-POLISH | Code/design | Visual quality, mobile, SEO/meta, Product Owner walkthrough. |

## 7. Stop-And-Ask Prima Del Codice

Domande da chiudere in `WP-SITEV3-CONTRACT`:

1. V3 MVP include solo homepage/lobby o anche pagine contenuto?
2. Le lingue sono subito `it/en/de/es` come i giochi?
3. Login/register/account restano V1 nel MVP?
4. Rollback/version history e' MVP o fase 2?
5. Moduli MVP minimi: header, hero, game grid, promo band, rich text, footer?
6. V3 deve essere preview-only finche' non sostituisce V1, o pubblicabile su
   route reale gia' in MVP?
7. Dopo l'audit, `frontend-v2/` va cancellato e ricreato pulito oppure mantenuto
   temporaneamente come lab non versionato?

## 8. Capability Matrix

| Capability | Stato oggi | Target V3 | Gate |
| --- | --- | --- | --- |
| Site V1 isolation | Green | Green | Nessun diff V1. |
| Admin builder boundary | Red | Green | Builder dentro admin `:3000`. |
| Public renderer boundary | Red | Green | `:3001` renderizza solo published pages. |
| Secure auth handoff | Red | Green | No token query/localStorage lab flow. |
| Draft/live lifecycle | Partial | Green | Snapshot published separato dal draft. |
| Module registry | Partial | Green | Manifest versionato e validato. |
| Module editor UX | Partial | Green | Help, i18n, validation, assets, mobile. |
| Rich text safety | Red | Green | Sanitizzazione/allowlist. |
| Backend errors | Red | Green | AppError / CK.* envelope. |
| Versioning/audit | Red | Green | Save/publish/delete auditabili. |
| Product visual quality | Red | Green | Walkthrough PO su `:3000` e `:3001`. |

## 9. CTO Recommendation

Procedere con Site V3, ma non con produzione codice adesso.

Il prossimo step sano e' `WP-SITEV3-CONTRACT`: un documento piu' corto del piano
generale, ma piu' vincolante, che chiude scope, moduli MVP, lifecycle,
sicurezza, visual quality e gate. Solo dopo quel contratto ha senso iniziare a
spostare pezzi nel backoffice o a creare il renderer pubblico su `:3001`.
