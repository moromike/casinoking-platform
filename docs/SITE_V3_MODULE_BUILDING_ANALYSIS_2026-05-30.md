Status: ACTIVE
Last meaningful update: 2026-05-30
Owner: CTO (Claude) — Analysis only, NO code until Phase 3A validated

# Site V3 — Module Building / Editing: Gap Analysis (G1)

Feature-obiettivo che ha motivato l'intera migrazione e mai completata. Michele:
"manca la parte di building (e di editing di quelli presenti) dei moduli, lo dico
da 1000 volte". Questa e' analisi a freddo del DELTA reale, verificata su codice.

## CORREZIONE CTO (2026-05-30): la mia prima diagnosi era SBAGLIATA

La prima stesura di questo doc diceva che `ModuleFieldInput` era uno stub
`return null` e che edit/clone non esistevano. FALSO — basato su un grep andato a
vuoto. Lettura del codice reale:
- `ModuleField` (`fields/module-field.tsx`) E' PIENAMENTE implementato: widget per
  string, html (textarea), boolean (checkbox), asset_ref (AssetField con upload),
  title_code (select), title_code_list (TitleListField). I 6 tipi ci sono.
- `site-v3-module-instance-screen.tsx` RENDERIZZA quei widget per editare le
  istanze montate, con readiness e required-fields check.
- `site-v3-module-studio-screen.tsx` HA gia': create, EDIT draft
  (`loadDefinitionForEdit` + `onUpdateDefinition`), clone, publish, archive.
- `site-v3-admin-api.ts` HA: list/create/updateDraft/publish/archive definitions.
- Backend: GET/POST/PUT-draft/validate/publish/archive module-definitions.

CONCLUSIONE RIVISTA: il building/editing dei moduli **esiste gia' nel codice**.
Quindi il problema riportato da Michele ("manca il building") NON e' codice
assente — e' uno di questi due, da accertare in Phase 3B Parte A:
1. e' NASCOSTO/rotto dalle regressioni CSS del recovery (Module Studio mostrava
   "0 definitions": forse non carica, forse stile illeggibile), oppure
2. e' INCOMPLETO rispetto all'aspettativa di Michele (manca un page-builder
   visuale drag&drop, o l'editing inline dal preview, non i form attuali).

Va CHIESTO/VERIFICATO cosa intende Michele per "building", invece di assumere.
Non si scrive codice su una diagnosi sbagliata.

## Backend (confermato, c'e')

Endpoint gia' esistenti in `backend/app/api/routes/site_v3_admin.py`:
- `POST /admin/site-v3/module-definitions` — crea definizione custom
- `GET  /admin/site-v3/module-definitions` — lista definizioni
- `PUT  /admin/site-v3/module-definitions/{definition_id}` — EDIT definizione
- `POST   /admin/site-v3/pages/{page_code}/modules` — aggiungi modulo a pagina
- `PUT    /admin/site-v3/pages/{page_code}/modules/{module_id}` — EDIT istanza modulo su pagina
- `DELETE /admin/site-v3/pages/{page_code}/modules/{module_id}` — rimuovi modulo da pagina

Quindi: creare, listare, MODIFICARE definizioni; aggiungere, MODIFICARE, rimuovere
istanze su pagina — il backend lo SUPPORTA. La feature non e' "da costruire da
zero": e' da CABLARE nel frontend. Questo abbassa molto costo/rischio.

## Cosa verificare davvero in Phase 3B Parte A (NON gap presunti)

Dato che il codice c'e', la Parte A di Codex deve ACCERTARE perche' Michele non
lo vede funzionare. Ipotesi da testare, non da assumere:

- IPO-1: Module Studio non carica le definizioni (lista "0 definitions" anche se
  ce ne sono) — bug di fetch/auth/site_code, oppure semplicemente non ne sono mai
  state create.
- IPO-2: le schermate building/editing erano rese illeggibili dal CSS rotto
  (pre-3A). Da ri-controllare DOPO che la 3A ha sistemato l'admin.
- IPO-3: l'aspettativa di Michele e' un page-builder VISUALE (compose la pagina
  vedendo l'anteprima, trascina/edita i moduli inline) mentre l'attuale e' a form
  + preview separata. Questo sarebbe un gap di UX/prodotto, non un bug.
- IPO-4: manca un punto d'ingresso chiaro/visibile per arrivare a building+editing
  dal flusso naturale (scoperta), non la feature in se'.

Azione: prima di stimare o scrivere codice, Codex (Parte A) riproduce il percorso
reale "crea un modulo -> montalo in pagina -> editane i contenuti -> pubblica" su
:3000 DOPO la 3A, con screenshot di ogni step, e riporta DOVE si rompe o cosa
manca rispetto all'aspettativa. Poi il CTO decide con Michele cosa significa
"building" per lui.

## Inquadramento prodotto: cos'e' un "modulo" per Michele
Vocabolario lockato (vedi [[project_site_v3_cms_ia_cleanup]]): 'module' singolo.
- Definizione = tipo di modulo (libreria, da template renderer approvato).
- Istanza = modulo montato in una pagina con i suoi valori.
Building = creare/editare DEFINIZIONI. Editing = editare ISTANZE montate. Servono
entrambi; oggi entrambi monchi per GAP-1/GAP-2.

## Sequenza proposta (Phase 3B, DOPO stabilizzazione 3A validata)
Brief in 2 parti (regola WP critico):
- Parte A (approccio): Codex mappa COSA e' gia' cablato vs stub (specie GAP-3),
  propone i 6 widget di campo + flusso edit definizioni/istanze, conferma contratti
  API. Gate CTO sull'approccio.
- Parte B (esecuzione): implementa GAP-1 (widget campi) -> GAP-2 (edit/delete def)
  -> GAP-3 (azioni page builder) -> GAP-4 (UX). Micro-step gated con screenshot.

## Gate duri
- NESSUNA modifica a game runtime / logic / backend GMP.
- Tutto scoped sotto root CMS (`.site-v3-cms-admin-page`), zero leak su admin legacy/finance.
- Backend: riusare endpoint esistenti; nuovi endpoint solo se un gap lo richiede, con test.
- Validazione Michele su :3000: creare un modulo, montarlo, editarne i contenuti, ripubblicare.

## Stato
ANALISI SOLO. Nessun codice. Si parte con Parte A solo dopo che Phase 3A
(stabilizzazione regressioni) e' validata da Michele su :3000.
