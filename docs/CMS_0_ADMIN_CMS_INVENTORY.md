Status: ACTIVE
Last meaningful update: 2026-05-09

# CMS-0 Admin CMS Inventory

Documento operativo per il cantiere admin/CMS.

## Stato

- Tipo: audit CMS-0.
- Stato: audit completato; CMS-1A componentizzazione completata in prima passata; CMS-1B prima slice UI editoriale completata frontend-only; CMS-1C bridge asset Title completato frontend-only; CMS-2A backend homepage/banner completato; CMS-2B admin UI homepage/banner completata; CMS-2C player read path completato.
- Data: 2026-05-08.
- Ambito: Site/Lobby Publishing, Game Catalog CMS, homepage/banner futuri, asset e giochi esterni a livello di inventario.
- Non modifica codice runtime, wallet, ledger, payout, RNG o launch contract.

## Perche' esiste

Prima di migliorare la UX admin/CMS serve distinguere con precisione tre cose:

1. cosa oggi e' gia' editoriale;
2. cosa e' configurazione tecnica del gioco;
3. cosa e' solo informazione di sicurezza/pubblicabilita'.

Senza questa distinzione, la prossima UI rischia di diventare un'altra vista mista: un po' CMS, un po' catalogo tecnico, un po' runtime editor.

## Fonti lette

Documenti:

- `docs/SOURCE_OF_TRUTH.md`;
- `docs/TASK_EXECUTION_GUARDRAILS.md`;
- `docs/DOCUMENTATION_MAINTENANCE.md`;
- `docs/README.md`;
- `docs/SITE_LOBBY_PUBLICATION_PLAN.md`;
- `docs/SITE_CMS_EDITORIAL_UX_PLAN.md`;
- `docs/CMS_ROADMAP_AND_EXTERNAL_GAMES_PLAN.md`;
- `docs/F7_C_GAMES_DETAIL_ROUTE_REFACTOR_PLAN.md`;
- `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`.

Codice:

- `frontend/app/ui/site/site-lobby-publication-panel.tsx`;
- `frontend/app/ui/platform-catalog-panel.tsx`;
- `frontend/app/ui/games/games-overview.tsx`;
- `frontend/app/ui/games/game-category-view.tsx`;
- `frontend/app/ui/casinoking-console.tsx`;
- `backend/app/modules/platform/catalog/admin_title_service.py`;
- `backend/app/modules/platform/catalog/library_service.py`;
- `backend/app/modules/platform/catalog/service.py`;
- `backend/app/api/routes/admin.py`;
- `backend/app/api/routes/games_library.py`;
- `backend/app/api/routes/platform_catalog.py`.

## Superfici CMS-like attuali

| Superficie | File | Stato | Note |
| --- | --- | --- | --- |
| Site/Lobby Publishing | `frontend/app/ui/site/site-lobby-publication-panel.tsx`, `frontend/app/ui/site/site-lobby-summary.tsx`, `frontend/app/ui/site/site-lobby-title-row.tsx`, `frontend/app/ui/site/site-lobby-preview.tsx`, `frontend/app/ui/site/site-lobby-draft.ts` | Implementata e componentizzata in prima passata | Il panel resta orchestratore; summary, row editor, preview e helper draft sono separati. |
| Game Catalog Overview | `frontend/app/ui/platform-catalog-panel.tsx`, `frontend/app/ui/games/*` | Implementata | E' backoffice tecnico/catalogo, non CMS editoriale. |
| Title Detail Editor | `frontend/app/ui/title-editor/*`, `frontend/app/ui/mines/*` | Implementato per Mines | Config, theme, asset, copy/i18n del gioco. Non va mischiato con Site CMS. |
| Player Lobby Preview | `GET /games/library` usato da Site/Lobby | Implementata | Fonte corretta per preview, ma visual preview e' ancora lista compatta, non card realistica. |
| Homepage/Banner CMS | `frontend/app/ui/site/site-home-slots-panel.tsx`, `frontend/app/ui/player-lobby-page.tsx`, `backend/app/modules/platform/site_cms/*`, `backend/migrations/sql/0033__site_home_slots.sql` | CMS-2A backend presente; CMS-2B admin UI presente; CMS-2C player read presente | Admin CRUD minimo, public read, target validation e audit operativo. La UI Site lista slot, crea/modifica contenuto e target; la lobby player usa il primo slot pubblicato come hero editoriale con fallback alla lobby esistente. |
| External Games Catalog | Nessun file dedicato | Non presente | Solo roadmap/mock futuro, non in CMS-1. |

## Dati disponibili oggi

### Catalogo Site/Title

Endpoint:

```text
GET /api/v1/catalog/sites/casinoking/titles
```

Usi:

- elenco Title assegnati al Site;
- master vs variant;
- engine;
- stato Title;
- stato Site/Title;
- publication metadata.

Campi rilevanti:

| Campo | Tipo | Uso CMS |
| --- | --- | --- |
| `title_code` | tecnico | Identificativo da mostrare come metadato, non come headline editoriale. |
| `engine_code` | tecnico | Filtro/contesto. |
| `display_name` | catalogo | Fallback nome lobby, non necessariamente copy player definitivo. |
| `is_master` | safety | Master preview-only, non pubblicabile come item lobby. |
| `status` | safety | Stato tecnico del Title. |
| `site_title_status` | safety | Stato assegnazione Site/Title. |
| `publication.lobby_visibility` | editoriale/prodotto | Decide se appare in lobby. |
| `publication.demo_enabled` | prodotto/launch gate | Decide CTA demo pubblica. |
| `publication.real_enabled` | prodotto/launch gate | Decide CTA real pubblica. |
| `publication.lobby_display_name` | editoriale | Nome player-facing in lobby. |
| `publication.lobby_description` | editoriale | Descrizione player-facing in lobby. |
| `publication.featured` | editoriale | Evidenza leggera multi-item. |
| `publication.position` | editoriale | Ordinamento. |

### Player library

Endpoint:

```text
GET /api/v1/games/library
```

Usi:

- preview della libreria player;
- verifica indiretta dell'ordine reale;
- fonte corretta per cio' che il player vede.

Campi:

- `display_name`;
- `catalog_display_name`;
- `description`;
- `demo_enabled`;
- `real_enabled`;
- `featured`;
- `position`;
- `engine_display_name`.

## Classificazione campi

### Editoriali

Questi sono candidati naturali per CMS-1:

- `lobby_display_name`;
- `lobby_description`;
- `featured`;
- `position`;
- preview player;
- eventuale futuro `homepage_slot` o `banner`.

### Product/Publication

Sono controlli operativi, non pura copy:

- `lobby_visibility`;
- `demo_enabled`;
- `real_enabled`.

Devono restare nella pagina Site/Lobby, ma con copy piu' chiaro e warning espliciti.

### Tecnici

Da mostrare come contesto, non come primary UI:

- `title_code`;
- `engine_code`;
- `status`;
- `site_title_status`;
- `is_master`;
- eventuali live config hints.

### Fuori dal CMS

Restano nel Game Catalog/Title Detail:

- grid size;
- mine count;
- payout/RTP;
- theme tokens di gioco;
- board assets di gioco;
- i18n/copy runtime Mines;
- preview admin master/hidden;
- duplicazione varianti;
- publish config live.

## Stato del componente Site/Lobby

Prima di CMS-1A, `site-lobby-publication-panel.tsx` faceva troppe cose insieme:

- fetch catalogo;
- fetch library preview;
- stato loading/error catalogo;
- stato loading/error library;
- draft locale publication per ogni Title;
- normalizzazione payload;
- warning publication;
- layout KPI;
- layout lista disponibili;
- form publication;
- preview order;
- helper di dirty state.

CMS-1A ha separato summary, row editor, preview e helper draft. Resta nel panel
principale l'orchestrazione fetch/stato/salvataggio, come previsto.

## Backend/API

Endpoint gia' sufficienti per CMS-1:

```text
GET /api/v1/catalog/sites/casinoking/titles
GET /api/v1/games/library
PUT /api/v1/admin/sites/{site_code}/titles/{title_code}/publication
```

Non serve introdurre ora:

```text
GET /api/v1/admin/sites/{site_code}/lobby-editor
```

Motivo:

- i dati necessari sono gia' disponibili;
- il problema immediato e' UX/component ownership, non contratto API;
- endpoint dedicato si valuta solo se il frontend inizia a duplicare troppe regole.

Endpoint aggiunti in CMS-2A backend:

```text
GET /api/v1/site/home?site_code=casinoking
GET /api/v1/admin/sites/{site_code}/home-slots
POST /api/v1/admin/sites/{site_code}/home-slots
PATCH /api/v1/admin/sites/{site_code}/home-slots/{slot_key}
```

Regole CMS-2A:

- il public read restituisce solo slot `published` attivi secondo schedule;
- `title_demo` e `title_real` richiedono Title non-master, active, visibile in
  Site/Lobby e rispettivamente `demo_enabled` / `real_enabled`;
- le modifiche scrivono audit operativo `site_home_slot_update`;
- la transizione a `published` scrive anche `site_home_slot_publish`;
- nessun endpoint lancia giochi o tocca wallet, ledger, payout, RNG o runtime
  Mines.

UI aggiunta in CMS-2B:

```text
frontend/app/ui/site/site-home-slots-panel.tsx
```

Regole CMS-2B:

- usa `GET /api/v1/admin/sites/{site_code}/home-slots` con token admin per la
  lista slot;
- usa `POST`/`PATCH /api/v1/admin/sites/{site_code}/home-slots` con token admin
  per create/update;
- usa `GET /api/v1/catalog/sites/casinoking/titles` per popolare target
  selezionabili;
- esclude target master, hidden, inattivi o non abilitati per la modalita'
  demo/real scelta;
- non gestisce upload media e non modifica `media_asset_id` salvo mantenerlo
  readonly/null nel payload;
- nessun backend, launch, wallet, ledger, payout, RNG o runtime Mines
  modificato.

Regole CMS-2C:

- `frontend/app/ui/player-lobby-page.tsx` legge `/site/home?site_code=casinoking`;
- il primo slot pubblico, gia' ordinato dal backend, sostituisce solo copy/CTA
  del hero lobby;
- `/games/library` resta fonte unica della griglia giochi e dello spotlight di
  fallback;
- errore o assenza slot CMS non produce errore player e lascia invariata la
  lobby precedente;
- nessun backend, launch, wallet, ledger, payout, RNG o runtime Mines
  modificato.

## Gap attuali

| Gap | Impatto | Decisione |
| --- | --- | --- |
| `SiteLobbyPublicationPanel` troppo grande | Rende rischioso il polish CMS-1 | Splittare prima della UI editoriale. |
| Preview non identica alla card lobby reale | L'operatore non vede esattamente il risultato finale | Migliorare in CMS-1 usando dati `GET /games/library`; non duplicare regole. |
| Nessun homepage/banner CMS | Non gestibile home marketing | CMS-2, dopo CMS-1. |
| Nessuna media library generale | Card/banner non hanno asset dedicati | CMS-3, non CMS-1. |
| Nessun site selector | Oggi esiste solo `casinoking` | Out of scope finche' non arriva un secondo Site. |
| Reorder non batch | Molte chiamate se si fa drag/drop | Accettabile finche' non emerge lentezza o incoerenza. |
| External games non presenti | Non si possono gestire provider esterni | Solo modellazione futura/mock in CMS-4. |

## Primo scope consigliato: CMS-1A

Stato: completato in prima passata.

Obiettivo:

- rendere Site/Lobby manutenibile prima di ridisegnarla.

Write set usato:

```text
frontend/app/ui/site/site-lobby-publication-panel.tsx
frontend/app/ui/site/site-lobby-summary.tsx
frontend/app/ui/site/site-lobby-title-row.tsx
frontend/app/ui/site/site-lobby-preview.tsx
frontend/app/ui/site/site-lobby-draft.ts
```

Azioni completate:

1. Estrarre helper/draft in `site-lobby-draft.ts`.
2. Estrarre KPI/header in `site-lobby-summary.tsx`.
3. Estrarre row form Title in `site-lobby-title-row.tsx`.
4. Estrarre preview order in `site-lobby-preview.tsx`.
5. Lasciare fetch e orchestration nel panel principale.

Non fare in CMS-1A:

- redesign visuale importante;
- homepage banner;
- endpoint nuovo;
- asset manager;
- provider esterni;
- modifiche backend.

Accettazione:

- comportamento invariato;
- `npx tsc --noEmit` verde;
- `tests/integration/test_frontend_smoke.py` verde;
- smoke admin Site/Lobby manuale o browser se disponibile;
- nessuna regressione su lobby player.

## Secondo scope: CMS-1B

Stato: completato in prima slice frontend-only dopo CMS-1A.

Obiettivo:

- rendere Site/Lobby piu' editoriale e meno tecnica.

Azioni completate nella prima slice:

- preview piu' vicina alle card player;
- separazione visiva tra "Lobby visibile" e "Catalogo disponibile";
- warning publication piu' comprensibili;
- title code ed engine come metadati secondari;
- save state esplicito tra "Modifiche non salvate" e pubblicazione allineata.

Resta fuori da questa slice:

- detail leggero/accordion per edit copy;
- endpoint nuovi, site selector, drag/drop, reorder batch, homepage/banner.

## Terzo scope: CMS-1C

Stato: completato frontend-only.

Obiettivo:

- risolvere il gap UX su icone/card asset senza spostare upload o asset manager
  dentro Site/Lobby.

Azioni completate:

- nota chiara sulle row Site/Lobby: icona e asset della card si configurano nel
  Game Detail, area Asset del titolo;
- link diretto da ogni row variante a
  `/admin/games/{engine_code}/titles/{title_code}`;
- link diretto anche dalle preview card visibili;
- nessun endpoint, payload, schema, asset upload o publish flow modificato.

## Parallelismo con Player Account

Il player account puo' avanzare in parallelo solo su PA-UX-1/PA-UX-3 frontend-only:

- overview account;
- estratto conto summary-first basato sulle sessioni gia' disponibili.

Aggiornamento 2026-05-08: PA-UX-1 e' stata completata frontend-only in
parallelo a CMS-1B, usando solo wallet snapshot, sessioni Mines e transazioni
gia' caricate da `/account`.

Non aprire PA-UX-2 Cassa evoluta finche' non viene deciso un endpoint read-only piu' ricco per movimenti ledger.

Priorita' corrente:

1. Validare CMS-1B/C UI editoriale Site/Lobby con smoke admin/manuale.
2. Validare PA-UX-1 overview account con smoke player/manuale.
3. CMS-2 homepage/banner dopo validazione CMS-1.

## Decisioni per CTO

| Decisione | Proposta |
| --- | --- |
| Nuovo endpoint lobby editor | No in CMS-1A. Usare endpoint esistenti. |
| Site selector | Fuori scope finche' esiste solo `casinoking`. |
| Reorder batch | Fuori scope finche' non serve atomicita' reale. |
| Homepage banner | CMS-2, non CMS-1. |
| Media library | CMS-3, non CMS-1. |
| External games | Solo mock/futuro, non in CMS-1. |
