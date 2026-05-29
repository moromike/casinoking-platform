Status: ACTIVE
Last meaningful update: 2026-05-29

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
WP6 Cleanup/Promotion   DONE
WP-MIG0 Handoff         CODE
WP-MIG1 Player Shell    CODE
WP-MIG2 Game Shell      CODE
WP-MIG3 Register Config CODE
WP-MIG4A V1 Direct Handoff CODE
WP-MIG4B Admin Host Isolation CODE
WP-MIG4C Runtime Extraction Contract DOC/TEST
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
Effort reale sesta tranche: 1 prompt. Il builder admin e' stato ristrutturato
da workbench compatto a CMS navigabile: menu principale stabile, `Pages`,
`Page detail`, `Composition`, `Modules`, categorie modulo, dettaglio tipo modulo
e dettaglio istanza modulo a piena larghezza. Backend, API, draft/publish e
renderer pubblico restano invariati.
Effort reale settima tranche: 1 prompt. La navigazione CMS e' stata corretta
in gerarchia umana: `Site` contiene `Dashboard` e `Site settings`; `Pages`
contiene `All pages`, `Settings`, `Composition`, `Module settings`,
`Validation` e `Versions`; `Modules` resta la libreria dei tipi modulo. Questo
evita di mettere dettagli della pagina allo stesso livello dell'elenco pagine.
Effort reale ottava tranche: 1 prompt. Il dettaglio dei moduli e' stato reso
piu' umano: i campi non sono piu' una lista piatta ma sono raggruppati in
`Content`, `Game catalog`, `Assets and media`, `Links and actions` e
`Legal and safe HTML`, sia nella scheda tipo modulo sia nell'istanza montata in
pagina.
Effort reale nona tranche: 1 prompt. La schermata `Composition` ora espone
`Duplicate` per ogni modulo montato: copia configurazione e posizione logica in
una nuova istanza draft, apre subito il dettaglio e non persiste nulla finche'
l'operatore non usa `Save draft`.
Effort reale decima tranche: 1 prompt. La lista `Composition` ora mostra uno
stato di prontezza per ogni modulo (`Ready` oppure campi obbligatori mancanti),
calcolato dai descriptor TypeScript. Questo non sostituisce la validation
backend, ma aiuta l'operatore prima del publish.
Effort reale undicesima tranche: 1 prompt. La navigazione moduli e' stata resa
coerente con `Pages`: le categorie modulo sono sottovoci del menu `Modules`;
`Module settings` non appare piu' come voce laterale autonoma; `Composition ->
Add module` apre un picker inline nella composizione invece di portare
l'operatore fuori flusso nella libreria generale.
Effort reale dodicesima tranche: 1 prompt lungo. WP-V3-PREVIEW-LIVE aggiunge
preview draft live nel builder: backend emette token preview short-lived,
header-only e auditato; endpoint pubblico `preview-draft` legge solo
`site_v3_pages` + `site_v3_modules`; `frontend-v3` riusa `SiteV3PublicPage`
con `mode="preview"`; admin monta un pannello bottom-wide collassabile nelle
viste page-bound.
Effort reale tredicesima tranche / WP-A CMS IA cleanup: 1 prompt. Regola IA
hard: `Modules` e' la libreria dei module type; `Pages -> Composition` e' la
lista delle module instance montate; il nav laterale non lista mai le istanze.
Il wizard standalone e' stato rimosso: i soli percorsi di aggiunta sono
`Composition -> Add module to page` e `Module type detail -> Mount on current
page`. Il vocabolario admin e' allineato a `module` / `module instance`; la
parola `template` non e' piu' ammessa nel CMS Site V3.

Effort reale quattordicesima tranche / WP-B theme tokens: 1 prompt. Il
renderer pubblico `frontend-v3` ora espone un blocco token unico in
`frontend-v3/app/globals.css` per font, background, superfici, testo, accenti,
bordi, radius, shadow e overlay. I valori visivi restano identici; il WP
centralizza il restyle futuro senza toccare componenti, backend, API, V1 o
nuovi module type.

Effort reale quindicesima tranche / WP5 product QA polish: 1 prompt con
sub-agent read-only. Sono stati chiusi i P1 emersi dal walkthrough tecnico:
il builder protegge le modifiche non salvate su reload, cambio locale/status e
nuova pagina; `Publish live` richiede validation green esplicita; i manual asset
URL sono limitati a `http(s)`, `/static/` e `/uploads/` lato validation backend
e renderer pubblico. Sono stati chiusi anche P2 rapidi: fallback nav pubblica
senza anchor inesistente, preview live allineata alla navigation pubblica,
header pubblico meno fragile su narrow tablet e copy admin meno tecnico
(`Selected game titles`, asset render `cover/crop with no stretch`). La stessa
tranche chiude due P3 piccoli: link admin al renderer letto da
`NEXT_PUBLIC_SITE_V3_BASE_URL` con default locale, e renderer pubblico con
`html lang="en"` coerente con la copy inglese corrente.

Effort reale sedicesima tranche / WP asset workflow: 1 prompt. Il builder Site
V3 ora collega i campi asset al flusso Site media esistente: upload multipart su
`/admin/sites/{site_code}/assets` con `asset_kind=homepage_banner`, accetta PNG,
JPEG e WebP fino a 2 MB, mostra raccomandazione 1600x900/16:9 e comportamento
render `cover/crop with no stretch`, aggiorna il picker senza uscire dal modulo
e seleziona subito il banner caricato. Il WP non introduce nuove tabelle o nuovi
asset kind; il delete resta nel pannello Site media esistente per evitare
rimozioni distruttive mentre Site V3 e V1 condividono la libreria.

## 9. WP6 - Cleanup/Promotion

Tipo: codice/doc.

Stato: completato per cleanup lab locale; promozione a default site resta
decisione prodotto separata.

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

Effort reale diciassettesima tranche / WP6 cleanup lab: 1 prompt. La directory
locale ignorata `frontend-v2/` e' stata rimossa dopo verifica che non contenesse
file tracciati (`git ls-files frontend-v2` = 0) e che il path risolto restasse
dentro il workspace. Il cleanup non tocca `cms_v2_*`: backend/schema lab restano
dormienti come memoria storica e non sono piu' collegati al prodotto Site V3.
`frontend-v3` e' ora un servizio Docker ufficiale `frontend-v3` su `:3001`, con
Dockerfile dedicato, healthcheck, CORS locale, doctor e smoke suite aggiornati.
La promozione locale del default pubblico e' stata completata con il servizio
`edge`: `:3000` serve Site V3 come root pubblico, inoltra login, registrazione,
account e shell giochi a `frontend-v3`, mantiene admin sul V1 e incapsula i
runtime giochi V1 dietro `/legacy-games/*`; `:3002` resta V1 diretto per
debug/admin/runtime e, da WP-MIG4B, il root diretto reindirizza a `/admin`.
La riscrittura reale dei runtime fuori dal V1 resta un work package dedicato.

## 9.1. WP-MIG0 - V3/V1 Player Handoff

Tipo: codice/test.

Stato: prima tranche completata il 2026-05-29.

Output prima tranche:

- Site V3 continua a servire il root pubblico su `:3000` tramite edge;
- login, registrazione e account restano proprieta' V1 secondo contratto;
- i link V3 verso login/account V1 preservano `return_to`;
- le pagine player V1 preservano `return_to` tra login, register e account guest;
- logout da una pagina player aperta con `return_to` rientra sul target Site V3
  sanitizzato;
- il bridge cross-origin `window.name` resta scoped a origin, short-lived e
  coperto da contract test;
- browser smoke reale con player temporaneo: Site V3 -> login V1 -> ritorno a
  Site V3 autenticato -> Account V1 -> logout -> ritorno a Site V3 guest.
- link gioco Site V3 verso Mines/BOXE/HI-LO V1 portano `return_to`;
- i runtime V1 Mines/BOXE/HI-LO leggono `return_to` sanitizzato e il loro
  `Back to site` rientra sul target V3 quando non sono embedded.

Gate prima tranche:

- nessun cambio a wallet, ledger, settlement o runtime giochi;
- nessuna promozione di login/account dentro `frontend-v3`;
- open redirect bloccato tramite allowlist origin e rifiuto `//`;
- build frontend V1 verde;
- contract handoff verde;
- browser smoke handoff verde.
- browser smoke link lancio gioco verde.

Prossime tranche possibili:

- solo dopo decisione prodotto, piano separato per migrare login/account e shell
  gioco fuori dal V1.

## 9.2. WP-MIG1 - Site V3 Player Shell

Tipo: codice/test.

Stato: implementato il 2026-05-29.

Output:

- Site V3 possiede le rotte player `/login`, `/register` e `/account` su
  `frontend-v3`;
- l'edge pubblico `:3000` instrada login/register/account a `frontend-v3`;
- admin e runtime giochi Mines/BOXE/HI-LO restano V1-owned dietro `frontend`;
- login/register usano gli endpoint backend esistenti `/auth/login` e
  `/auth/register`;
- account usa gli endpoint esistenti `/auth/me`, `/wallets`,
  `/account/statement-movements` e history/replay dei giochi;
- nessuna modifica a DB, wallet, ledger, settlement, payout o semantica backend
  auth/account;
- dopo WP-MIG4A/B, V1 diretto su `:3002` non conserva piu' root player,
  login/register/account come prodotto player: il root reindirizza a `/admin` e
  login/register/account reindirizzano a Site V3 preservando query.

Gate:

- build `frontend-v3` verde;
- contract route ownership verde;
- smoke browser Site V3 login/account/logout verde dopo rebuild Docker;
- route giochi/admin ancora V1.

## 9.3. WP-MIG2 - Site V3 Game Shell

Tipo: codice/test.

Stato: implementato il 2026-05-29.

Output:

- Site V3 possiede le rotte pubbliche `/mines`, `/boxe` e `/hi-lo` su
  `frontend-v3`;
- l'edge pubblico `:3000` instrada le shell gioco a `frontend-v3`;
- i runtime gioco V1 restano invariati e, prima delle slice WP-MIG4D+, sono
  serviti solo dietro `/legacy-games/mines`, `/legacy-games/boxe` e
  `/legacy-games/hi-lo`;
- la shell gioco V3 costruisce iframe same-origin con `embed=1`,
  `embed_origin`, `return_to`, title e wallet/mode params preservati;
- close/fullscreen usano il bridge game-agnostic esistente e i messaggi legacy
  compatibili;
- nessuna modifica a DB, wallet, ledger, settlement, payout o semantica runtime.

Gate:

- build `frontend-v3` verde;
- route ownership contract verde;
- smoke browser Site V3 game launch link -> shell V3 -> iframe legacy verde;
- V1 diretto su `:3002` conserva le route runtime per debug locale.

## 9.4. WP-MIG3 - Site V3 Registration System Page

Tipo: codice/test.

Stato: first slice implementato il 2026-05-29.

Output first slice:

- aggiunto modulo built-in `system_registration_form` al manifest backend e ai
  descriptor admin;
- aggiunta categoria `System pages` alla module library;
- aggiunta voce `Pages -> System pages` nel builder, con apertura/creazione
  guidata della pagina fissa `register`;
- la bozza creata monta `system_registration_form` con default compatibili col
  form esistente;
- la rotta pubblica `/register` resta una route di sistema Site V3, carica la
  pagina published `register` e consuma il primo `system_registration_form`;
- se la pagina `register` non e' pubblicata o non contiene il modulo, il form
  usa i default built-in;
- la configurazione copre copy, visibilita' dei campi opzionali, step documenti,
  legal note allowlisted e redirect post-registrazione same-origin;
- nessuna modifica a `/auth/register`, auth service, wallet bootstrap, ledger,
  cashier, payout o storage documenti.

Debito dichiarato:

- i documenti caricati sono ancora gate frontend-only e non vengono persistiti;
- consensi/checkbox legal non vanno aggiunti finche' non esiste un WP backend
  dedicato a documenti, consensi e audit;
- login/account system modules restano slice successive, per evitare di
  fingere controlli CMS non collegati al runtime reale.

Gate:

- contract manifest/admin/public verde;
- build `frontend` e `frontend-v3` verde;
- browser QA su `:3000/register` default e, se presente, snapshot pubblicata
  `register`;
- nessun cambio a DB/auth/wallet/ledger.

## 9.5. WP-MIG4A - Direct V1 Player Route Handoff

Tipo: codice/test/doc.

Stato: first slice implementato il 2026-05-29.

Output:

- aggiunto helper `frontend/app/lib/site-v3-redirect.ts`;
- `frontend/app/login/page.tsx`, `frontend/app/register/page.tsx` e
  `frontend/app/account/page.tsx` reindirizzano a Site V3 usando
  `NEXT_PUBLIC_SITE_V3_BASE_URL`;
- i parametri query sono preservati, incluso `return_to`;
- V1 diretto `:3002` resta host interno debug/admin/runtime, ma non espone piu'
  un secondo prodotto player auth/account;
- nessuna modifica ad admin, runtime giochi, backend auth/register, wallet,
  ledger, payout o settlement;
- piano dedicato creato in `docs/SITE_V3_V1_RETIREMENT_PLAN_2026-05-29.md`.

Gate:

- contract route ownership verde;
- smoke V1 direct auth/account redirect verde;
- build `frontend` verde;
- edge pubblico invariato: `:3000/login`, `/register`, `/account` restano
  serviti da `frontend-v3`.

Follow-up:

- WP-MIG4B ha completato la prima tranche di isolamento root/admin host;
- WP-MIG4C definisce il contratto di estrazione runtime giochi prima di muovere
  Mines/BOXE/HI-LO fuori da `/legacy-games/*`.

## 9.6. WP-MIG4B - Admin Host Isolation

Tipo: codice/test/doc.

Stato: first slice implementato il 2026-05-29.

Output:

- `frontend/app/(player)/page.tsx` non monta piu' `PlayerLobbyPage`;
- `frontend/app/(player)/layout.tsx` e' stato rimosso, quindi il root diretto
  V1 non passa piu' da una player shell;
- V1 diretto `:3002/` reindirizza a `/admin`;
- `PlayerLobbyPage` resta quarantinato nel repository finche' i riferimenti
  storici/test legacy non vengono migrati o ritirati;
- doctor/smoke/documentazione trattano `:3002` come host interno
  admin/runtime/debug, con `/admin` come landing interna;
- nessuna modifica a backend, admin auth, RBAC, finance, wallet, ledger,
  payout, settlement o runtime giochi.

Gate:

- contract route ownership verde;
- smoke V1 direct root redirect verde;
- doctor verifica redirect root V1 + `/admin` diretto;
- build `frontend` verde;
- edge pubblico invariato: `:3000` continua a servire Site V3 root e admin
  proxato.

Chiuso dal follow-up:

- WP-MIG4D: estrarre BOXE come primo runtime candidate in
  `frontend-v3/app/runtime/boxe`, seguendo il contratto WP-MIG4C.

## 9.7. WP-MIG4C - Runtime Extraction Contract

Tipo: doc/test.

Stato: first slice implementato il 2026-05-29.

Output:

- creato `docs/SITE_V3_RUNTIME_EXTRACTION_CONTRACT_2026-05-29.md`;
- inventario per-game di shell Site V3, route iframe legacy, route dirette V1,
  entrypoint runtime e helper condivisi;
- fissato target di migrazione: runtime island in `frontend-v3` sotto
  `/runtime/{game}`, mantenendo `/mines`, `/boxe`, `/hi-lo` come shell
  pubbliche Site V3;
- fissato contratto query/iframe: `title_code`, `mode`, `wallet_source`,
  `preview`, `preview_token`, `return_to`, `embed=1`, `embed_origin`;
- fissato contratto postMessage generic/legacy per close e fullscreen state;
- confermato che backend endpoint, wallet, ledger, settlement, payout, RNG,
  fairness e math non cambiano nelle slice di estrazione;
- aggiornato il contract storage runtime a includere `hi_lo`;
- ordine raccomandato: BOXE, HI-LO, Mines.

Gate:

- contract test runtime extraction verde;
- contract game-runtime boundary/storage verde;
- nessun cambio servito da Docker e nessun runtime spostato in questa slice.

Follow-up chiuso:

- WP-MIG4D: estrarre BOXE in `frontend-v3/app/runtime/boxe` e cambiare solo la
  shell BOXE da `/legacy-games/boxe` a `/runtime/boxe` dopo parita' verde.

## 9.8. WP-MIG4D - BOXE Runtime Extraction

Tipo: codice/test/doc.

Stato: first slice implementato il 2026-05-29.

Output:

- aggiunta route interna `frontend-v3/app/runtime/boxe/page.tsx`;
- copiato/promosso in `frontend-v3` il runtime BOXE e gli helper shared
  necessari come scaffolding di migrazione;
- la shell pubblica `frontend-v3/app/boxe/page.tsx` punta l'iframe a
  `/runtime/boxe`;
- l'edge pubblico espone `/runtime/boxe` su `frontend-v3` e rimuove
  `/legacy-games/boxe`;
- la route diretta V1 `/boxe` reindirizza a Site V3 preservando query;
- nessuna modifica a backend BOXE, wallet, ledger, settlement, payout, RNG,
  fairness o math.

Gate:

- `frontend-v3` TypeScript verde;
- contract route ownership/runtime extraction aggiornati;
- build e smoke Docker/browser da rilanciare dopo rebuild servizi.

Prossimo step:

- WP-MIG4E: estrarre HI-LO con lo stesso pattern, aggiungendo/aggiornando prima
  i browser smoke necessari per non migrare alla cieca.

## 10. Multiagent Strategy

Parallelismo possibile solo dopo WP1:

| WP | Parallelizzabile | Note |
| --- | --- | --- |
| WP2 Backend | Si' | Puo' partire da solo dopo contratto. |
| WP3 Admin | Completato | Usa WP2 reale; niente mock API. |
| WP4 Renderer | Completato | Usa public API reale e browser smoke su `:3001`. |
| WP5 Visual | Green-major | Renderer modulare reale + riuso asset V1 pubblici + CMS admin navigabile per Site/Pages/Modules invece del workbench compatto + homepage walkthrough polish + CMS copy in English + product QA guardrails su dirty state, validation-before-publish e asset URL + upload/picker banner nel builder. WP-A CMS IA cleanup chiude la separazione module type vs module instance; WP-B theme tokens centralizza il restyle pubblico in `frontend-v3/app/globals.css`. |
| WP6 Cleanup | Completato | Lab locale `frontend-v2/` rimosso; `frontend-v3` promosso nello stack Docker locale; edge locale aggiunto per rendere Site V3 il root pubblico su `:3000` lasciando V1 dietro per le rotte legacy. |
| WP-MIG0 Handoff | Green first slice | Chiude preservazione `return_to` tra Site V3 e V1 player shell con browser smoke reale e link runtime giochi con ritorno V3 sanitizzato. |
| WP-MIG1 Player Shell | Green | Sposta login/register/account in `frontend-v3` usando le API esistenti; V1 resta owner di admin e runtime giochi. |
| WP-MIG2 Game Shell | Green | Sposta `/mines`, `/boxe`, `/hi-lo` in `frontend-v3`; runtime V1 invariati dietro `/legacy-games/*` iframe same-origin. |
| WP-MIG3 Register Config | Green first slice | Collega `/register` a una pagina di sistema Site V3 con modulo `system_registration_form`, senza cambiare backend auth/wallet/ledger o storage documenti. |
| WP-MIG4A V1 Direct Handoff | Green first slice | Le route dirette V1 `/login`, `/register`, `/account` reindirizzano a Site V3 preservando query; V1 diretto resta solo host interno admin/runtime/debug. |
| WP-MIG4B Admin Host Isolation | Green first slice | Il root diretto V1 `:3002/` reindirizza a `/admin`; la vecchia lobby V1 e' quarantinata e non montata come root. |
| WP-MIG4C Runtime Extraction Contract | Green first slice | Contratto e inventario per spostare un runtime per volta in `frontend-v3/app/runtime/{game}`; BOXE ha applicato il pattern in WP-MIG4D. |
| WP-MIG4D BOXE Runtime Extraction | Green first slice | BOXE runtime vive in `frontend-v3/app/runtime/boxe`; `/legacy-games/boxe` e V1 direct `/boxe` non sono piu' superfici runtime. |

Strategia consigliata:

1. WP2 backend in un worktree.
2. WP3 admin builder in un worktree dopo API contract stabile.
3. WP4 renderer in parallelo con fixture JSON solo se il contract payload e'
   congelato.

## 11. Capability Matrix End-To-End

| Capability | DB | Backend | Admin UI | Public UI | Tests | Docs | Stato | Note |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Page draft | WP2 green | WP2 green | WP5 guardrail green | n/a | WP2+WP3+WP5 green | WP2 brief + roadmap + manual | Admin green | Draft save increments `draft_version`; public remains unchanged; builder exposes dirty state and confirms before reload/filter/locale/new-page loss. |
| Publish snapshot | WP2 green | WP2 green | WP5 validation gate green | WP4 consume | WP2+WP3+WP5 green | WP2 brief + roadmap + manual | Admin green | Publish writes immutable `site_v3_page_versions` snapshot and UI shows history; admin publish button requires saved draft and explicit validation green. |
| Module registry | n/a/code | WP2 green | WP5 navigation/editor green + WP-MIG3 system module | WP4 render | WP2+WP3+WP5+MIG3 green | WP2 brief + roadmap + manual | Admin green | 9 built-in manifests registered server-side and mirrored in TypeScript; admin exposes module categories, full module detail screens, grouped field areas, readiness state, compact add-module flow and the `system_registration_form` route-owned module. |
| CMS navigation | n/a | n/a | WP-A green | n/a | contract+frontend build green | roadmap + manual + IA brief | Admin green | Site V3 admin uses a persistent CMS menu with top-level `Site`, `Pages` and `Modules`; `Pages` contains only page screens, not mounted module instance labels. Library = module types; Composition = mounted module instances. |
| Game grid | read catalog | WP2 green | WP5 human editor green | WP4 render | WP2+WP3+WP5 green | WP2 brief + roadmap | Admin green | Title validation hits live catalog/site publication; builder uses live title options with selected-game ordering, engine grouping, search and clear controls. |
| Assets | registry ref | WP5 URL validation green + Site media upload reuse | WP5 picker/upload/manual URL green | WP5 safe URL render + V1 fallback | WP2+WP3+WP5 green | WP2 brief + roadmap + manual | Admin green-major | Admin builder can upload/select existing Site `homepage_banner` assets or use a manual public URL limited to `http(s)`, `/static/` or `/uploads/`; internal asset id/kind fields are hidden from the page module editor. Upload guidance shows PNG/JPEG/WebP, 2 MB, 1600x900/16:9 and cover/crop render behavior. |
| i18n model | WP2 green | WP2 green | WP3 locale filter/editor | WP4 | WP2+WP3 green | WP2 brief + roadmap | Admin green | Locale model is present; MVP supports `it/en/de/es` with migration needed for more. |
| V1 isolation | no V1 DB change | no `cms_v2_*` change | internal admin route only | runtime iframe only | regression gate | WP2 brief + roadmap + retirement plan | Green-major | `cms_v2_*` dormiente e `frontend-v2/` rimosso. Public player/auth/game shell sono V3. V1 diretto non espone piu' root player/login/register/account come prodotto player; resta host interno admin/runtime/debug finche' WP-MIG4C+ non migrano admin e runtime giochi. |
| Public renderer | n/a | WP2 public API green | n/a | WP5 visual/product QA green-major + WP6 Docker service + edge root + WP-MIG2 game shell + WP-MIG3 register config + WP-MIG4A/B V1 direct handoff/isolation | WP4+WP5+WP6+MIG build/doctor/smoke green | WP4 brief + roadmap + retirement plan | Green-major | Runs as Docker service `frontend-v3` from `frontend-v3/` direct on `:3001` and as public root through `edge` on `:3000`, published-only, with one file/component per MVP module, public V1 asset fallback, complete header/footer shell, live game grid, safer fallback navigation, narrow-tablet header polish, Site V3 player shell, Site V3 game shell and CMS-configurable registration route. V1 still owns admin and game runtime implementation behind legacy routes, but no longer owns direct root player/auth/account routes. |
| Public theme tokens | n/a | n/a | n/a | WP-B green | `frontend-v3` lint/build + token scan | WP-B brief + roadmap + manual | Green | `frontend-v3/app/globals.css` has one `:root` theme block for font, background, surfaces, text, accent, borders, radius, shadows and overlays. Hardcoded visual values are kept inside that block. |
| Draft preview live | n/a | WP preview green | WP preview panel green | WP5 preview parity green | contract+security+static smoke green | preview brief + roadmap + manual | Green-major | Token scoped to `(site,page,locale,draft_version)`, sent only in `X-Draft-Preview-Token`; no read from `site_v3_page_versions`; published-only endpoint unchanged; preview now loads public navigation fallback like the published renderer. |
| Lab cleanup / edge default | n/a | `cms_v2_*` dormant | n/a | n/a | contract green | roadmap + README + active loops + atlas | Green | Local ignored `frontend-v2/` lab removed in WP6; no tracked files were deleted. `frontend-v3` is part of compose/doctor/smoke and Site V3 is the local public root through `edge` on `:3000`. |
| V3/V1 player handoff | n/a | n/a | n/a | V3-owned player routes; V1 direct redirects | contract + V1/V3 build + browser smoke green | roadmap + active loops + retirement plan | Green-major | WP-MIG0 ha chiuso il ritorno sicuro tra Site V3 e V1. Dopo WP-MIG1 login/register/account sono V3-owned; WP-MIG4A sostituisce le route dirette V1 con redirect a Site V3 preservando query. |
| V1 direct auth/account retirement | no DB change | no API change | n/a | V1 direct `/login`, `/register`, `/account` redirect to V3 | contract + smoke + frontend build | retirement plan + roadmap | Green first slice | Rimuove il secondo prodotto player senza toccare admin o runtime giochi. |
| V1 direct root isolation | no DB change | no API change | V1 direct root lands on `/admin` | V1 direct root no longer mounts player lobby | contract + smoke + doctor + frontend build | retirement plan + roadmap + smoke docs | Green first slice | Rimuove la vecchia lobby come root diretto V1; `PlayerLobbyPage` resta quarantinato finche' i riferimenti legacy non sono migrati. |
| Runtime extraction contract | no DB change | no API change | n/a | target `/runtime/{game}` in Site V3 | contract runtime extraction + storage | runtime contract + roadmap + retirement plan | Green first slice | Ordine raccomandato BOXE -> HI-LO -> Mines; BOXE migrato in WP-MIG4D. |
| BOXE runtime extraction | no DB change | no API change | n/a | `/boxe` shell -> `/runtime/boxe` V3 iframe | frontend-v3 lint/build + contract + browser smoke | runtime contract + roadmap + atlas | Green first slice | `/legacy-games/boxe` rimosso dall'edge; V1 direct `/boxe` reindirizza a Site V3. |
| Site V3 player shell | no DB change | existing auth/account/wallet APIs | n/a | login/register/account V3 | frontend-v3 build + contract route ownership + browser smoke | roadmap + active loops + manual | Green | UI player spostata in `frontend-v3`; backend auth, wallet, ledger, statement e history/replay giochi restano invariati. |
| Site V3 game shell | no DB change | existing game runtime APIs | n/a | `/mines`, `/boxe`, `/hi-lo` V3 host + per-game runtime iframe | frontend-v3 build + contract route ownership + browser smoke | roadmap + active loops + manual | Green | Shell gioco pubblica spostata in `frontend-v3`; BOXE usa runtime V3, Mines/HI-LO restano temporaneamente dietro `/legacy-games/*`. |
| Site V3 registration system page | no DB change | existing `/auth/register` | `Pages -> System pages` + `system_registration_form` | `/register` consumes published CMS config with fallback | contract + frontend builds + browser smoke | roadmap + active loops + manual + atlas | Green first slice | Copy, optional field visibility, document-step gate, legal note and post-register path are CMS-configurable; no consent/document persistence and no auth/wallet/ledger semantics changed. |

## 12. Definition Of Done Site V3 MVP

MVP e' chiuso solo quando:

- admin builder vive su `:3000`;
- public renderer vive come root pubblico su `:3000` tramite `edge` e resta
  disponibile direttamente su `:3001`;
- una homepage/lobby published e' visibile;
- almeno i moduli MVP renderizzano con content reale;
- game grid lancia giochi tramite flussi esistenti;
- shell giochi pubbliche vivono su Site V3 e incapsulano runtime legacy senza
  cambiare semantica gioco;
- registrazione player e' Site V3-owned e configurabile dal CMS come pagina di
  sistema, senza duplicare backend auth/wallet/ledger;
- draft/live sono separati;
- public non legge draft;
- V1 resta operativo;
- Michele fa walkthrough e non trova "lab tecnico travestito da sito".
