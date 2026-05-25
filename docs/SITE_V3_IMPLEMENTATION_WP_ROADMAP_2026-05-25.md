Status: ACTIVE
Last meaningful update: 2026-05-25

# Site V3 - Implementation WP Roadmap

## 0. Scopo

Questo documento traduce i piani Site V3 in work package eseguibili. Non
autorizza ancora codice: definisce ordine, dipendenze, gate e output attesi.

## 1. Sequenza Raccomandata

```text
WP0 Audit Rescue        DONE
WP1 Product Contract    DOC
WP1-FOLLOWUP Lock Docs  DOC
WP2 Backend MVP         CODE
WP3 Admin Builder MVP   CODE
WP4 Public Renderer MVP CODE
WP5 Visual/Product QA   CODE/DESIGN
WP6 Cleanup/Promotion   CODE/DOC
```

## 2. WP0 - Audit Rescue

Stato: completato.

Output:

- `docs/SITE_V3_AUDIT_RESCUE_2026-05-25.md`;
- `frontend-v2` classificato come materiale di consulto;
- salvare solo registry/picker/editor/preview come idee;
- non promuovere il lab.

## 3. WP1 - Product Contract

Tipo: doc-only.

Output:

- `docs/SITE_V3_PRODUCT_CONTRACT_2026-05-25.md`;
- `docs/SITE_V3_MODULE_TAXONOMY_2026-05-25.md`;
- `docs/SITE_V3_LIFECYCLE_API_SECURITY_PLAN_2026-05-25.md`;
- questa roadmap.

Gate:

- decisioni product minime esplicite;
- V1 isolation rule chiara;
- moduli MVP dichiarati;
- draft/live/published-only definito;
- Stop-before-code riportati in chat.

Effort stimato: 2-4 prompt.

## 4. WP1-FOLLOWUP - Lock Decisions And Repo Guardrails

Tipo: doc-only/config repo.

Decisione lockata 2026-05-25 - Michele approved.

Output:

- aggiornamento dei 6 documenti `SITE_V3_*_2026-05-25.md` con decisioni chiuse;
- `.gitignore` per `frontend-v2/` lab temporaneo e `frontend-v3/` ownership WP4;
- README/open loops aggiornati;
- prompt follow-up persistito.

Gate:

- nessun codice runtime toccato;
- nessuna route/migration Site V3 creata;
- `cms_v2_*` non modificato;
- `frontend-v2/` non modificato, solo gitignorato.

Effort stimato: 2-3 prompt.

## 5. WP2 - Backend MVP

Tipo: codice.

Stato: completato in `feature/site-v3-wp2-backend-brief` il 2026-05-25.

Dipendenze:

- WP1 approvato;
- WP1-FOLLOWUP mergeato;
- brief Parte A CTO consegnato con DDL/API/payload/error codes/test plan;
- decisione lockata: usare nuove tabelle `site_v3_pages`,
  `site_v3_page_versions`, `site_v3_modules`; `cms_v2_*` dormiente.

Ownership probabile:

- `backend/app/api/routes/site_v3_admin.py`;
- `backend/app/api/routes/site_v3_public.py`;
- `backend/app/modules/platform/site_v3/`;
- migration SQL `backend/migrations/sql/0045__site_v3_persistence.sql`;
- tests backend e contract published-only.

Output:

- admin list/get/save/validate/publish;
- public get published page;
- snapshot/version minimo;
- validation engine;
- audit event;
- `admin_audit_log` con `payload_json.source=site_v3`;
- AppError/CK.* errors;
- RBAC admin esplicito via bridge lockato `require_admin_area("games")`.

Gate:

- draft save non modifica public;
- public only published;
- validation error blocca publish;
- audit save/publish;
- V1 site CMS tests invariati.

Stop-before-code Parte A:

- non creare route o migration finche' il brief CTO non fissa URL exact,
  payload shape, DDL completo, error code namespace `SITEV3.*` e test matrix;
- non modificare `cms_v2_*`;
- non creare `frontend-v3/` nel WP2.

Effort stimato originale: 8-14 prompt.
Effort ricalibrato dal brief Parte A: 10-16 prompt.
Effort reale: 1 prompt lungo di esecuzione, suddiviso in commit atomici.

## 6. WP3 - Admin Builder MVP

Tipo: codice.

Stato: brief Parte A prodotto in
`docs/SITE_V3_WP3_ADMIN_BUILDER_BRIEF_2026-05-25.md`. Non iniziare Parte B
finche' il brief non e' approvato da CTO.

Dipendenze:

- WP2 admin APIs disponibili.

Ownership probabile:

- `frontend/app/admin/site-v3/...` o route equivalente;
- `frontend/app/ui/site-v3-admin/*`;
- CSS admin dedicato/shared;
- no modifiche player V1 salvo link admin shell.

Output:

- page list;
- page editor;
- module picker;
- module config editor;
- preview draft;
- validation display;
- save draft;
- publish live;
- dirty state affidabile;
- niente token query.

Gate:

- admin funziona su `:3000`;
- save draft si attiva a ogni modifica;
- publish richiede validation;
- visual admin pulito;
- non apre piu' builder esterno come finale.

Effort stimato: 12-20 prompt.

## 7. WP4 - Public Renderer MVP

Tipo: codice.

Dipendenze:

- WP2 public API;
- WP3 almeno un modo di pubblicare contenuti.

Ownership probabile:

- nuova app `frontend-v3/` pulita su `:3001`;
- public module renderers;
- API client public-only.

Output:

- homepage V3 published;
- game grid da catalogo;
- hero/promo/rich text/footer;
- responsive desktop/mobile;
- fallback errori puliti;
- link a gioco/account V1 dove serve.

Gate:

- renderer non richiede admin token;
- non legge draft;
- niente overflow orizzontale;
- product walkthrough su `:3001`;
- V1 `:3000` resta funzionante.

Effort stimato: 10-18 prompt.

## 8. WP5 - Visual/Product QA

Tipo: codice/design.

Output:

- polish visual;
- asset reali o placeholder dichiarati;
- mobile refinement;
- screenshot side-by-side V1/V3 dove utile;
- Product Owner walkthrough.

Gate:

- Michele vede builder e renderer;
- moduli non sembrano demo tecnica;
- mobile accettabile;
- V1 non regressa;
- issue list residua classificata.

Effort stimato: 6-12 prompt.

## 9. WP6 - Cleanup/Promotion

Tipo: codice/doc.

Output:

- cestinare `frontend-v2/` lab secondo decisione lockata;
- rimuovere o ignorare artefatti `.next` / `node_modules`;
- aggiornare README/open loops;
- aggiornare architecture map se cambiano boundary;
- eventuale piano promozione V3 a nuovo sito default.

Gate:

- repo pulito;
- nessun artefatto build committato;
- docs puntano al percorso corretto;
- servizio `:3001` ha significato definitivo.

Effort stimato: 2-5 prompt.

## 10. Multiagent Strategy

Parallelismo possibile solo dopo WP1:

| WP | Parallelizzabile | Note |
| --- | --- | --- |
| WP2 Backend | Si' | Puo' partire da solo dopo contratto. |
| WP3 Admin | Parziale | Serve mock API o WP2 pronto. |
| WP4 Renderer | Parziale | Serve public API o fixture contract. |
| WP5 Visual | No iniziale | Meglio dopo MVP reale. |
| WP6 Cleanup | No | Deve avvenire alla fine. |

Strategia consigliata:

1. WP2 backend in un worktree.
2. WP3 admin builder in un worktree dopo API contract stabile.
3. WP4 renderer in parallelo con fixture JSON solo se il contract payload e'
   congelato.

## 11. Capability Matrix End-To-End

| Capability | DB | Backend | Admin UI | Public UI | Tests | Docs | Stato | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Page draft | WP2 green | WP2 green | WP3 | n/a | WP2 green | WP2 brief + roadmap | Backend green | Draft save increments `draft_version`; public remains unchanged. |
| Publish snapshot | WP2 green | WP2 green | WP3 | WP4 consume | WP2 green | WP2 brief + roadmap | Backend green | Publish writes immutable `site_v3_page_versions` snapshot. |
| Module registry | n/a/code | WP2 green | WP3 | WP4 render | WP2 green | WP2 brief + roadmap | Backend green | 7 MVP manifests registered and validated server-side. |
| Game grid | read catalog | WP2 green | WP3 config | WP4 render | WP2 green | WP2 brief + roadmap | Backend green | Title validation hits live catalog/site publication. |
| Assets | registry ref | WP2 warning-only | WP3 picker | WP4 render | WP2 partial | WP2 brief + roadmap | Backend partial | WP2 accepts `asset_ref`; upload/picker remains WP3/focused asset WP. |
| i18n model | WP2 green | WP2 green | WP3 | WP4 | WP2 green | WP2 brief + roadmap | Backend green | Locale model is present; MVP supports `it/en/de/es` with migration needed for more. |
| V1 isolation | no V1 DB change | no `cms_v2_*` change | none/read-only | none/read-only | regression gate | WP2 brief + roadmap | Green | `cms_v2_*`, frontend V1 and runtime games untouched. |

## 12. Definition Of Done Site V3 MVP

MVP e' chiuso solo quando:

- admin builder vive su `:3000`;
- public renderer vive su `:3001`;
- una homepage/lobby published e' visibile;
- almeno i moduli MVP renderizzano con content reale;
- game grid lancia giochi tramite flussi esistenti;
- draft/live sono separati;
- public non legge draft;
- V1 resta operativo;
- Michele fa walkthrough e non trova "lab tecnico travestito da sito".
