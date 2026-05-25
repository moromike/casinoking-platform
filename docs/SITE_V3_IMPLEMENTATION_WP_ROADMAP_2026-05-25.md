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

Stato: completato in `feature/site-v3-wp3-admin-builder` il 2026-05-25.

Dipendenze:

- WP2 admin APIs disponibili e mergeate;
- brief Parte A approvato con decisioni lockate.

Ownership probabile:

- `frontend/app/admin/site-v3/...` o route equivalente;
- `frontend/app/ui/site-v3-admin/*`;
- CSS admin dedicato/shared;
- no modifiche player V1 salvo link admin shell.

Output:

- page list con filtri locale/status;
- page editor per identita' pagina;
- module picker per i 7 moduli MVP;
- module config editor con campi descriptor TypeScript;
- preview draft di composizione;
- validation display con codici support;
- save draft;
- publish live;
- archive;
- version history read-only;
- dirty state affidabile;
- niente token query;
- route interna admin `/admin/site-v3`, non builder esterno.

Gate:

- admin funziona su `:3000`;
- save draft si attiva a ogni modifica;
- publish richiede validation e draft salvato;
- visual admin pulito;
- non apre piu' builder esterno come finale;
- contract descriptor parity frontend/backend verde;
- browser smoke draft/validate/publish verde.

Effort stimato: 12-20 prompt.
Effort reale: 1 prompt lungo di esecuzione, con build, contract e browser smoke.

## 7. WP4 - Public Renderer MVP

Tipo: codice.

Stato: completato in `feature/site-v3-wp4-public-renderer` il 2026-05-25.

Dipendenze:

- WP2 public API;
- WP3 almeno un modo di pubblicare contenuti.

Ownership probabile:

- nuova app `frontend-v3/` pulita su `:3001`;
- public module renderers;
- API client public-only.
- `.gitignore` per rendere tracciabili i sorgenti `frontend-v3/` mantenendo
  ignorati `.next`, `node_modules`, `out`, `dist`.

Output:

- homepage V3 published su `:3001`;
- route dinamica `/pages/[page_code]`;
- game grid da catalogo pubblico;
- hero/promo/rich text/header/footer;
- responsive desktop/mobile;
- fallback errori puliti;
- link a gioco/account V1 dove serve.

Gate:

- renderer non richiede admin token;
- non legge draft;
- niente overflow orizzontale;
- browser smoke desktop/mobile verde;
- product walkthrough su `:3001`;
- V1 `:3000` resta funzionante.

Effort stimato: 10-18 prompt.
Effort reale: 1 prompt lungo di esecuzione, con build, contract e browser smoke.

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
Effort reale prima tranche: 1 prompt lungo di esecuzione. Il renderer e'
stato separato in componenti per modulo, usa `/games/library` per le card
gioco e `/site/home` come fallback pubblico per hero/promo V1 quando il modulo
V3 non ha ancora asset dedicati.
Effort reale seconda tranche: 1 prompt. Il builder admin ora espone un module
picker umano per tipologia (`Global structure`, `Hero and banners`,
`Game catalog`, `Promos and editorial`, `Text and legal`) con spiegazioni
operative per ogni modulo, invece della select tecnica piatta.
Effort reale terza tranche: 1 prompt. I campi asset del builder ora espongono
un picker visuale dei `homepage_banner` gia' presenti nel Site/CMS V1 tramite
`/admin/sites/{site_code}/assets`, mantenendo il fallback manuale `public_url`.
Effort reale quarta tranche: 1 prompt. Il renderer pubblico `frontend-v3` ora
presenta una homepage piu' completa per walkthrough: header sticky con brand,
nav di fallback, azioni `Login` + `Account` verso V1, game grid live senza
doppioni e solo title lanciabili, count giochi, hero con fallback banner V1 meno
invasivo e promo rail ancorata. Resta necessario il gate runtime su `:3001`
quando backend/Docker sono disponibili.
Effort reale quinta tranche: 1 prompt. Le label operative del CMS Site V3 e i
fallback pubblici del renderer sono stati riallineati in inglese: module picker,
field hints, asset picker, default navigation, empty states, CTA fallback, date
format e validation/status copy restano coerenti con un backoffice internazionale.

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
| WP3 Admin | Completato | Usa WP2 reale; niente mock API. |
| WP4 Renderer | Completato | Usa public API reale e browser smoke su `:3001`. |
| WP5 Visual | In corso | Renderer modulare reale + riuso asset V1 pubblici + picker moduli per tipologia nel builder + homepage walkthrough polish + CMS copy in English. |
| WP6 Cleanup | No | Deve avvenire alla fine. |

Strategia consigliata:

1. WP2 backend in un worktree.
2. WP3 admin builder in un worktree dopo API contract stabile.
3. WP4 renderer in parallelo con fixture JSON solo se il contract payload e'
   congelato.

## 11. Capability Matrix End-To-End

| Capability | DB | Backend | Admin UI | Public UI | Tests | Docs | Stato | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Page draft | WP2 green | WP2 green | WP3 green | n/a | WP2+WP3 green | WP2 brief + roadmap + manual | Admin green | Draft save increments `draft_version`; public remains unchanged; builder exposes dirty state. |
| Publish snapshot | WP2 green | WP2 green | WP3 green | WP4 consume | WP2+WP3 green | WP2 brief + roadmap + manual | Admin green | Publish writes immutable `site_v3_page_versions` snapshot and UI shows history. |
| Module registry | n/a/code | WP2 green | WP5 picker green | WP4 render | WP2+WP3+WP5 green | WP2 brief + roadmap + manual | Admin green | 7 MVP manifests registered server-side and mirrored in TypeScript; admin picker groups them by human composition category. |
| Game grid | read catalog | WP2 green | WP3 config green | WP4 render | WP2+WP3 green | WP2 brief + roadmap | Admin green | Title validation hits live catalog/site publication; builder uses live title options. |
| Assets | registry ref | WP2 warning-only | WP5 picker green | WP5 V1 fallback + WP4 render | WP2+WP3+WP5 partial | WP2 brief + roadmap + manual | Admin partial | Admin builder can pick existing Site V1 `homepage_banner` assets; upload remains in Site home media panel and richer asset picker/upload remains dedicated future WP. |
| i18n model | WP2 green | WP2 green | WP3 locale filter/editor | WP4 | WP2+WP3 green | WP2 brief + roadmap | Admin green | Locale model is present; MVP supports `it/en/de/es` with migration needed for more. |
| V1 isolation | no V1 DB change | no `cms_v2_*` change | internal admin route only | none/read-only | regression gate | WP2 brief + roadmap | Green | `cms_v2_*`, frontend V1 and runtime games untouched; admin shell no longer opens external lab as final builder. |
| Public renderer | n/a | WP2 public API green | n/a | WP5 visual tranche green | WP4+WP5 build green; browser gate pending backend runtime | WP4 brief + roadmap | Green-major | Runs in `frontend-v3/` on `:3001`, published-only, with one file/component per MVP module, public V1 asset fallback, complete header/footer shell, live game grid, and product visual walkthrough still required before final Site V3 closure. |

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
