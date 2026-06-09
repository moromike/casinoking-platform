Status: ACTIVE
Last meaningful update: 2026-05-25

# Site V3 - WP3 Admin Builder MVP Brief Parte A

## 0. Executive Verdict

WP3 e' stato approvato e implementato il 2026-05-25 su
`feature/site-v3-wp3-admin-builder`. Il backend WP2 definisce il contratto
dati/API; WP3 costruisce il builder admin dentro il backoffice esistente su
`localhost:3000`, senza promuovere il vecchio lab `frontend-v2/` e senza
toccare il renderer pubblico V3 su `:3001`.

Scope Parte A:

- documento only;
- nessun codice frontend creato;
- nessuna route backend creata;
- nessuna migration creata;
- nessuna modifica a `cms_v2_*`;
- nessuna modifica a player V1, giochi, wallet, ledger o runtime;
- nessuna modifica a `frontend-v2/` o `frontend-v3/`.

Decisione CTO/Codex: WP3 deve essere eseguito doc-first per evitare un altro
"lab tecnico travestito da prodotto". Il builder e' verde solo se funziona,
salva, valida, pubblica, mostra errori, e Michele riesce a usarlo su `:3000`
senza interpretare campi tecnici nascosti.

## 0.1 Implementation Closure

Output implementato:

- route admin interna `/admin/site-v3`;
- entry point `Site V3` nella shell admin esistente;
- page list con filtri locale/status;
- editor page identity;
- module composer per i 7 moduli MVP;
- field editor descriptor-driven;
- draft validation con errori leggibili e codici support;
- save draft;
- publish live;
- archive;
- version history read-only;
- composition preview dichiarata admin-only;
- static contract test di parita' descriptor TypeScript/Python;
- browser smoke draft -> invalid validate -> save draft -> valid validate ->
  publish -> history.

## 1. Required Reading Per Parte B

Prima del codice WP3 leggere in ordine:

1. `docs/README.md`
2. `docs/TASK_EXECUTION_GUARDRAILS.md`
3. `docs/DOCUMENTATION_MAINTENANCE.md`
4. `docs/SITE_V3_PRODUCT_CONTRACT_2026-05-25.md`
5. `docs/SITE_V3_MODULE_TAXONOMY_2026-05-25.md`
6. `docs/SITE_V3_LIFECYCLE_API_SECURITY_PLAN_2026-05-25.md`
7. `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md`
8. `docs/SITE_V3_WP2_BACKEND_BRIEF_2026-05-25.md`
9. backend WP2 reale:
   - `backend/app/api/routes/site_v3_admin.py`
   - `backend/app/modules/platform/site_v3/manifests/modules.py`
   - `backend/app/modules/platform/site_v3/validation/engine.py`
   - `backend/app/modules/platform/site_v3/service.py`
10. admin V1 reale:
   - `frontend/app/admin/page.tsx`
   - `frontend/app/admin/games/page.tsx`
   - `frontend/app/ui/casinoking-console.tsx`
   - `frontend/app/ui/admin-shell-panel.tsx`
   - `frontend/app/ui/site/*`
   - `frontend/app/ui/title-editor/*`

## 2. Current Admin Context

Il backoffice attuale vive in una singola shell React:

| Area | File reale | Nota WP3 |
| --- | --- | --- |
| Admin root | `frontend/app/admin/page.tsx` | Renderizza `CasinoKingConsole area="admin"`. |
| Games route | `frontend/app/admin/games/page.tsx` | Usa la stessa console con routing games. |
| Games detail | `frontend/app/admin/games/[engine]/titles/[title_code]/page.tsx` | Pattern utile per deep-link admin. |
| Shell sezioni | `frontend/app/ui/admin-shell-panel.tsx` | Oggi contiene un bottone `Site v3 (Lab)` che apre `http://localhost:3001`; WP3 non deve lasciarlo come finale. |
| Console admin | `frontend/app/ui/casinoking-console.tsx` | Orchestratore reale per login, sezioni, token admin e pannelli. |
| Site V1 | `frontend/app/ui/site/*` | Materiale utile, ma non e' Site V3 e non va promosso copiandolo alla cieca. |

Decisione WP3:

- il builder finale deve essere interno all'admin `:3000`;
- il vecchio bottone esterno `Site v3 (Lab)` deve diventare un entry point
  interno al builder Site V3, oppure essere sostituito da un link interno
  quando il builder atterra;
- `:3001` resta riservato al public renderer WP4, non al builder.

## 3. Admin Entry Point Target

Target consigliato Parte B:

```text
/admin/site-v3
```

Pattern:

- aggiungere una route Next admin dedicata, coerente con `admin/games`;
- riusare la sessione admin esistente;
- montare il pannello dentro `CasinoKingConsole` o dentro una shell admin
  equivalente che non duplichi login/logout/menu;
- mantenere una voce chiara nel menu backoffice: `Site V3`;
- mostrare badge `Lab` solo nel label, non come scusa per UI incompleta.

Alternative ammessa:

- se la route dedicata crea troppo attrito con la console attuale, WP3 puo'
  usare solo `adminSection === "site_v3"` dentro `CasinoKingConsole`, ma deve
  comunque permettere a Michele di raggiungere il builder da `:3000/admin`
  senza aprire `:3001`.

Stop-before-code:

- se per integrare `/admin/site-v3` serve rifattorizzare pesantemente
  `CasinoKingConsole`, fermarsi e proporre un sotto-WP di shell extraction;
- non creare un secondo login admin;
- non passare token admin in query string;
- non usare `frontend-v2/` come base prodotto.

## 4. UI Surfaces WP3

WP3 MVP deve consegnare queste superfici:

| Surface | Cosa deve fare | Gate visual/funzionale |
| --- | --- | --- |
| Page list | Lista pagine Site V3 per `site_code=casinoking`, locale `it`, filtro status. | Stato vuoto, loading, errore, lista ordinata e leggibile. |
| Page detail shell | Titolo pagina, `page_code`, locale, status, draft/live summary. | Nessun campo tecnico incomprensibile senza helper. |
| Module list | Ordine moduli per slot/sort; move up/down; remove con conferma. | Nessun salto layout; controlli chiari. |
| Module picker | Aggiunge uno dei 7 moduli MVP dal registry. | Non permette moduli fuori manifest. |
| Module config editor | Campi per ogni modulo, con help, required, max length. | Save draft si attiva a ogni modifica. |
| Validation panel | Mostra `validation_json.issues[]` con severity, modulo, field, code, message. | Issue bloccanti evidenti, warning separati. |
| Command bar | Load/reload, Save draft, Validate, Publish live, Archive. | Publish bloccato o respinto se validation invalid. |
| History list | Versioni published/draft read-only. | Revert UI non presente in MVP. |
| Draft preview | Preview admin essenziale dei moduli. | Deve aiutare Michele, non essere JSON raw come default. |

## 5. API Consumption Contract

Tutte le chiamate admin usano `apiRequest` con token admin esistente.
Tutte le risposte sono envelope `success/data`; gli errori sono AppError/CK
con `code`, `message`, `request_id`, `support_id` dove disponibile.

### 5.1 List Pages

```text
GET /admin/site-v3/sites/{site_code}/pages?locale=it&status=all&page=1&limit=50
```

Response `data`:

```json
{
  "site_code": "casinoking",
  "locale": "it",
  "pages": [],
  "pagination": {
    "page": 1,
    "limit": 50,
    "total": 0
  }
}
```

WP3 UI:

- status filter: `all`, `draft`, `published`, `archived`;
- default `locale=it`;
- empty state con CTA "Crea homepage" o "Crea pagina";
- nessun accesso public API per caricare draft.

### 5.2 Get Page

```text
GET /admin/site-v3/sites/{site_code}/pages/{page_code}?locale=it
```

Response `data`:

```json
{
  "page": {},
  "modules": [],
  "published": {
    "version": 1,
    "published_at": "..."
  }
}
```

WP3 UI:

- questo e' il punto di partenza dello stato editor;
- `page.draft_version` diventa `expected_draft_version`;
- `modules` viene serializzato come baseline per dirty-state.

### 5.3 Save Draft

```text
PUT /admin/site-v3/sites/{site_code}/pages/{page_code}/draft
```

Payload:

```json
{
  "locale": "it",
  "title": "Homepage",
  "expected_draft_version": 3,
  "modules": [
    {
      "id": "optional-existing-module-id",
      "client_id": "local-id-for-new-modules",
      "module_code": "hero_banner",
      "schema_version": 1,
      "slot_key": "hero",
      "sort_order": 0,
      "config_json": {}
    }
  ]
}
```

Response `data`:

```json
{
  "page": {},
  "modules": []
}
```

WP3 UI:

- Save draft button attivo quando `serializedCurrentState !== serializedSavedState`;
- dopo save riuscito, aggiornare `draft_version`, modules e baseline saved;
- se arriva conflitto versione, mostrare errore con `support_id` e proporre
  reload, non sovrascrivere silenziosamente.

### 5.4 Validate

```text
POST /admin/site-v3/sites/{site_code}/pages/{page_code}/validate
```

Payload identico a draft senza `expected_draft_version`.

Response `data`:

```json
{
  "status": "valid",
  "issues": []
}
```

WP3 UI:

- validate puo' girare sullo stato locale non ancora salvato;
- non deve salvare implicitamente;
- deve popolare il validation panel e il publish readiness badge.

### 5.5 Publish

```text
POST /admin/site-v3/sites/{site_code}/pages/{page_code}/publish
```

Payload:

```json
{
  "locale": "it",
  "expected_draft_version": 4
}
```

Response `data`:

```json
{
  "page": {},
  "version": {}
}
```

WP3 UI:

- se ci sono modifiche locali non salvate, chiedere save draft prima di publish;
- se validation e' invalid, mostrare errori e non fingere publish;
- dopo publish, aggiornare history, published summary e status.

### 5.6 Archive

```text
POST /admin/site-v3/sites/{site_code}/pages/{page_code}/archive
```

Payload:

```json
{
  "locale": "it"
}
```

WP3 UI:

- conferma esplicita prima di archiviare;
- archiviare non cancella fisicamente;
- dopo archive tornare a page list o mostrare status archived read-only.

### 5.7 Versions

```text
GET /admin/site-v3/sites/{site_code}/pages/{page_code}/versions?locale=it
```

Response `data`:

```json
{
  "page": {},
  "versions": []
}
```

WP3 UI:

- history list read-only;
- mostra versione, status, published_at, created_at;
- niente revert UI in MVP, per decisione lockata.

## 6. Module Editor Contract

Il builder deve derivare UI e validation expectations dai 7 moduli MVP. In WP3
non esiste ancora endpoint manifest; quindi la soluzione accettata e':

- duplicare un descriptor TypeScript minimo e dichiarato, allineato a
  `backend/app/modules/platform/site_v3/manifests/modules.py`;
- aggiungere test/static check che i 7 `module_code` siano identici al backend;
- annotare come future improvement un endpoint read-only
  `/admin/site-v3/module-manifests`.

Descriptor minimo Parte B:

| Module | Slot ammessi | Campi admin |
| --- | --- | --- |
| `global_header` | `header` | `brand_label`, `nav_items`, `login_label`, `account_label` |
| `hero_banner` | `main`, `hero` | `headline`, `body`, `cta_label`, `cta_title_code`, `media_asset_ref` |
| `game_grid` | `main`, `games` | `heading`, `title_codes` |
| `featured_game` | `main`, `feature` | `title_code`, `headline`, `body`, `cta_label` |
| `promo_band` | `main`, `promo` | `headline`, `body`, `cta_label`, `cta_url` |
| `rich_text_safe` | `main`, `content`, `footer` | `html` |
| `global_footer` | `footer` | `legal_text`, `links` |

Field controls:

| Field type backend | Control WP3 | Note |
| --- | --- | --- |
| `string` | input/textarea in base a max length | Mostrare limite e contatore. |
| `html` | textarea rich text safe MVP | Mostrare allowlist tag; no editor libero con script/style. |
| `title_code` | title picker | Consuma catalog/admin; non copia lista giochi hardcoded. |
| `title_code_list` | multi title picker ordinabile | Validazione title esistente lato server resta canonica. |
| `nav_items` | repeater label + target | Max items visibile; move/remove. |
| `asset_ref` | asset ref picker/manual public URL MVP | Upload dedicato solo se esiste gia' endpoint compatibile; altrimenti STOP o WP asset dedicato. |
| `boolean` | toggle | Non presente nei 7 manifest attuali, ma supportabile. |

## 7. Dirty-State Rule

Questo e' gate hard, perche' il problema e' gia' emerso in altri backoffice:
`Save draft` deve attivarsi a ogni modifica.

Implementation guidance Parte B:

1. Normalizzare stato editor in un oggetto stabile:

```text
{
  page: { title, page_code, locale },
  modules: [
    { module_code, schema_version, slot_key, sort_order, config_json }
  ]
}
```

2. Ordinare modules e keys prima della serializzazione.
3. Salvare `lastSavedSnapshot` dopo GET e dopo save riuscito.
4. Calcolare `isDirty` con confronto deterministico.
5. Ogni field editor deve mutare solo attraverso un reducer/dispatcher centrale.
6. Publish con dirty state deve bloccare e chiedere save draft.

Gate specifico:

- cambiare ogni campo di ogni modulo deve accendere Save draft;
- aggiungere/rimuovere/riordinare modulo deve accendere Save draft;
- dopo save riuscito Save draft torna disabilitato;
- reload confermato se ci sono modifiche non salvate.

## 8. Validation UX

WP3 deve rendere la validation leggibile per un product owner, non solo per
uno sviluppatore.

Mapping:

| Backend issue | UI |
| --- | --- |
| `severity=error` | blocco rosso/critico, publish non consentito |
| `severity=warning` | warning giallo, publish consentito se backend lo consente |
| `module_id` | nome modulo + posizione |
| `field` | label campo human-readable |
| `code` | sempre visibile in piccolo, utile per supporto |
| `message` | testo principale |

Regola AppError:

- se una chiamata fallisce, mostrare `error.message`, `error.code`,
  `supportId` e `requestId` quando presenti;
- non mostrare stack trace o JSON raw come UI primaria;
- non mangiare errori di publish/validation.

## 9. Preview Contract

Preview MVP e' admin-only e non sostituisce il public renderer WP4.

Deve:

- mostrare una preview ordinata dei 7 moduli;
- evidenziare title refs non risolti o asset mancanti;
- rendere `rich_text_safe` con sanitizzazione/preview sicura o testo escape;
- aiutare Michele a capire "come verra' composta la pagina".

Non deve:

- promettere pixel parity con `frontend-v3/` prima di WP4;
- leggere public API published;
- usare token admin in iframe verso `:3001`;
- diventare un mini-site separato.

## 10. Asset Strategy WP3

Decisione:

- WP3 non crea nuove tabelle asset;
- WP3 puo' consumare asset registry/platform se esiste gia' un endpoint
  compatibile;
- se il picker/upload Site V3 richiede backend nuovo, aprire WP dedicato
  `SITE-V3-ASSET-PICKER` invece di infilarlo nel builder.

Per ogni campo `asset_ref`, la UI deve mostrare:

- formati attesi del modulo;
- dimensioni raccomandate;
- comportamento render previsto (`cover`, crop possibile, no stretch);
- stato "asset mancante" come warning chiaro.

## 11. RBAC/Auth

WP3 usa la sessione admin esistente e il token admin gia' gestito da
`CasinoKingConsole`.

Regole:

- chiamate admin con bearer token;
- nessun token in query string;
- 403 usa `CK.AUTH.FORBIDDEN`;
- se admin non ha area `games`, mostrare access denied coerente col resto
  dell'admin;
- non aggiungere area RBAC `site` in WP3.

## 12. File Ownership Parte B

Ownership consigliata:

| Area | File/cartella |
| --- | --- |
| Entry route | `frontend/app/admin/site-v3/page.tsx` |
| Admin shell integration | `frontend/app/ui/admin-shell-panel.tsx`, `frontend/app/ui/casinoking-console.tsx` |
| Site V3 admin UI | `frontend/app/ui/site-v3-admin/*` |
| Local descriptor/types | `frontend/app/ui/site-v3-admin/site-v3-admin-types.ts` |
| API client wrapper | `frontend/app/ui/site-v3-admin/site-v3-admin-api.ts` |
| CSS | preferire classi admin esistenti; eventuale `frontend/app/ui/site-v3-admin/site-v3-admin.css` importato dalla UI |
| Tests | `tests/frontend` o test Playwright esistenti se disponibili; altrimenti smoke script dedicato |
| Docs | `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md`, `docs/ACTIVE_OPEN_LOOPS.md` |

Vietato in WP3:

- `frontend-v3/`;
- `frontend-v2/`;
- backend route/service/migration salvo bug bloccante del contract WP2;
- `cms_v2_*`;
- player V1 rendering;
- game runtime.

## 13. Visual And UX Gate

WP3 non e' green se sembra un pannello tecnico fragile.

Screenshot evidence minima:

1. Admin menu con entry Site V3 interna.
2. Page list empty/non-empty.
3. Page editor con moduli.
4. Module picker.
5. Validation error visibile.
6. History list.
7. Draft preview.
8. Publish success state.

Check UX:

- layout pulito, no testi tagliati;
- niente overflow orizzontale non intenzionale;
- bottoni coerenti con admin attuale;
- Save draft/Pubblica distinguibili;
- errori con support/request id;
- helper copy sufficiente per Michele, senza diventare romanzo;
- Product Owner walkthrough su `localhost:3000/admin`.

## 14. Tests And Gates Parte B

Gate frontend:

- `npm run build` PASS;
- lint/typecheck se disponibili PASS;
- smoke browser admin:
  - login admin;
  - apri Site V3;
  - crea/carica pagina `home`;
  - aggiungi `hero_banner`;
  - modifica headline e verifica Save draft attivo;
  - save draft;
  - validate invalid su campo required vuoto;
  - validate valid;
  - publish;
  - history mostra versione;
  - archive con conferma.

Gate backend regression:

- `tests/integration/test_site_v3_backend.py` PASS;
- `tests/contract/test_site_v3_public_published_only.py` PASS;
- test V1 site CMS invariati dove esistono.

Gate isolamento:

- nessuna modifica a `frontend-v2/`;
- nessuna modifica a `frontend-v3/`;
- nessuna modifica a `cms_v2_*`;
- nessuna modifica a wallet/ledger/games runtime.

## 15. Stop-And-Ask

Fermarsi e chiedere CTO/Michele se:

- il builder non puo' stare dentro `:3000/admin` senza refactor grande della
  shell;
- serve un backend nuovo per manifest/asset picker non previsto da WP2;
- il contract WP2 non consente di salvare un caso base reale;
- Save draft non puo' essere reso affidabile con l'attuale architettura state;
- preview richiede importare componenti da `frontend-v2/`;
- si scopre che `frontend-v2/` contiene codice necessario non replicabile in
  modo pulito;
- una modifica impatta V1 player o game runtime.

## 16. Sequenza Commit Raccomandata Parte B

1. `feat(site-v3): add admin builder entry and page list`
2. `feat(site-v3): add editor state model and module composer`
3. `feat(site-v3): add module field editors and title pickers`
4. `feat(site-v3): add validation publish archive and history flows`
5. `feat(site-v3): add draft preview and admin visual polish`
6. `test(site-v3): cover admin builder smoke and dirty state`
7. `docs(site-v3): update admin builder capability matrix after wp3`

Commit piccoli, verificabili, senza mischiare CSS polish e state machine se non
necessario.

## 17. Effort Stimato Parte B

Stima: 12-20 prompt.

Breakdown:

| Slice | Prompt stimati | Note |
| --- | --- | --- |
| Entry route + page list | 2-3 | Include rimozione/sostituzione lab external entry. |
| Editor state + dirty state | 3-4 | Parte piu' delicata: non perdere modifiche. |
| Module field editors | 3-5 | Repeater nav/items/title list richiede cura. |
| Validation/publish/history | 2-3 | Consuma WP2 API. |
| Preview + visual polish | 2-3 | Deve essere usabile a vista. |
| Tests/docs/gate | 2 | Browser smoke e capability matrix. |

## 18. Capability Matrix WP3

| Capability | Backend/API | Admin UI | Preview | Tests | Docs | Stato target |
| --- | --- | --- | --- | --- | --- | --- |
| Page list | WP2 green | WP3 green | n/a | browser smoke | roadmap/manual | Green |
| Page draft editor | WP2 green | WP3 green | si | browser smoke | roadmap/manual | Green |
| Module picker | WP2 registry | WP3 green | si | smoke/static descriptor | taxonomy/roadmap | Green |
| Module config fields | WP2 validation | WP3 green | si | field smoke | taxonomy/roadmap | Green |
| Validation display | WP2 green | WP3 green | n/a | invalid/valid smoke | lifecycle/roadmap | Green |
| Publish/archive | WP2 green | WP3 green | n/a | publish smoke | roadmap/manual | Green |
| Versions/history | WP2 green | WP3 read-only green | n/a | history smoke | lifecycle/roadmap | Green |
| Asset references | WP2 warning/minimal | WP3 manual/ref field | placeholder | partial | taxonomy/manual | Partial until asset picker WP |
| V1 isolation | WP2 green | no V1 public change | n/a | contract/regression | product contract | Green |
| Product owner gate | n/a | walkthrough `:3000` pending | screenshots pending | manual | README/open loops | Required for closure |

## 19. Open Risks

| Risk | Impatto | Mitigazione |
| --- | --- | --- |
| `CasinoKingConsole` e' gia' molto grande | Rischio di peggiorare file monolite | Creare `site-v3-admin/*` e lasciare in console solo mount/route. |
| Backend non espone manifest endpoint | Duplicazione descriptor TS/Python | Static check + future endpoint read-only. |
| Asset picker non pronto | Moduli media meno completi | MVP accetta asset ref/manual URL con warning; WP asset dedicato se serve upload vero. |
| Preview non uguale al renderer WP4 | Michele puo' confondere preview con sito finale | Label chiara "Preview admin, rendering finale in WP4". |
| Dirty-state fragile | Perdita modifiche | Reducer centrale + serialized snapshot + smoke obbligatorio. |

## 20. Decision Brief Per CTO/Michele

Default consigliati:

- approvare WP3 Parte B con builder interno a `:3000/admin`;
- non usare `frontend-v2/` come base codice;
- non aprire `frontend-v3/` in WP3;
- accettare descriptor TypeScript locale allineato al backend per i 7 moduli,
  con static check e futuro endpoint manifest;
- asset picker MVP minimale, senza backend nuovo, salvo blocker reale.

Decisioni lockate 2026-05-25 - Michele approved:

1. Route admin lockata: `/admin/site-v3`.
2. Preview admin lockata: `composition preview`, non pixel parity del public
   renderer WP4.
3. Module descriptor lockato: TypeScript duplicato nel frontend, con static
   check di parita' rispetto a
   `backend/app/modules/platform/site_v3/manifests/modules.py`.
   L'endpoint backend `/admin/site-v3/module-manifests` e' rimandato a un WP
   futuro.
4. Asset strategy MVP lockata: il campo `asset_ref` accetta `asset_id` +
   `asset_kind` oppure URL pubblico manuale, sempre con warning chiaro in UI.
   L'upload reale Site V3 e' rimandato a `WP-SITE-V3-ASSET-PICKER` dedicato.
