# CasinoKing - Site CMS Editorial UX Plan

## Stato

Piano operativo iniziale.

Questo documento nasce dal feedback del 2026-05-08: la gestione attuale del
sito/lobby funziona, ma resta troppo tecnica e "da programmatore". L'obiettivo
non e' creare subito un CMS proprietario completo, ma rendere il backoffice Site
piu' editoriale, leggibile e guidato.

Aggiornamento 2026-05-08:

- CMS-UX-1 completata come audit operativo in
  `docs/CMS_0_ADMIN_CMS_INVENTORY.md`;
- CMS-UX-2 completata come componentizzazione controllata:
  `site-lobby-publication-panel.tsx` resta orchestratore fetch/draft/save, con
  summary, row editor, preview e helper draft estratti in file dedicati;
- CMS-1B: prima slice UI editoriale frontend-only completata. Site/Lobby
  separa "Lobby visibile" e "Catalogo disponibile", usa una preview card
  compatta piu' vicina alla lobby player, sposta `title_code`/engine a metadati
  secondari e rende warning/save state piu' comprensibili in backoffice IT;
- CMS-1C: bridge frontend-only completato. Site/Lobby chiarisce che icone e
  asset della card si configurano nel Game Detail/Title assets e aggiunge link
  diretti a `/admin/games/{engine_code}/titles/{title_code}` da row e preview;
- nessun endpoint backend, payload, schema, wallet, ledger, payout, RNG o
  launch contract e' stato modificato.

## Decisione

Per ora CasinoKing non introduce un CMS generale interno.

Evoluzione raccomandata:

```text
Site / Lobby Publishing
  -> editor editoriale guidato per cio' che appare nella lobby giochi

Headless CMS futuro
  -> homepage, banner, landing, pagine statiche, FAQ, contenuti marketing

Core platform
  -> auth, wallet, ledger, launch, gioco, config runtime, publish gate
```

Questa separazione evita due rischi:

- costruire un monolite CMS proprietario troppo grande;
- spostare nel CMS contenuti o azioni che appartengono alla piattaforma sicura.

## Cosa migliorare ora

La prima evoluzione deve riguardare la UX della sezione `Site`, non il modello
finanziario e non la configurazione tecnica dei giochi.

Target:

- mostrare la lobby come la vede il player;
- modificare nome, descrizione, stato demo/real e ordinamento con linguaggio
  editoriale;
- ridurre esposizione di codici tecnici nel flusso principale;
- mantenere `title_code`, engine e stati tecnici disponibili ma secondari;
- rendere chiaro cosa e' pubblicato sul sito rispetto a cosa e' configurato
  live nel gioco;
- prevenire pubblicazioni incoerenti con messaggi comprensibili.

## Confini

Resta nel backoffice Games/Mines:

- creazione varianti;
- configurazione griglia/mine;
- tema gioco;
- asset di gioco;
- copy player-facing del gioco;
- publish config live del gioco.

Resta in Site/Lobby:

- visibilita' in lobby;
- modalita' demo/real;
- nome e descrizione lobby;
- ordine;
- featured;
- preview della lobby player.

Resta fuori da questo piano:

- homepage marketing;
- pagine statiche;
- blog/FAQ;
- termini/privacy;
- promo engine;
- wallet, ledger, auth, KYC;
- gameplay e payout.

## Architettura consigliata

Non creare un nuovo servizio CMS ora.

Usare i dati gia' esistenti:

```text
site_titles
  lobby_visibility
  demo_enabled
  real_enabled
  lobby_display_name
  lobby_description
  featured
  position
```

Usare le API gia' disponibili finche' bastano:

```text
GET /api/v1/catalog/sites/casinoking/titles
GET /api/v1/games/library
PUT /api/v1/admin/sites/{site_code}/titles/{title_code}/publication
```

Valutare un endpoint dedicato solo se il frontend resta troppo complesso:

```text
GET /api/v1/admin/sites/{site_code}/lobby-editor
```

Regola: introdurlo solo per semplificare davvero la UI, non per creare un CMS
generico.

## UX target

### Vista principale

Una vista a due livelli:

```text
Lobby pubblicata
  anteprima concreta dei giochi visibili

Catalogo disponibile
  giochi pubblicabili/nascosti con azioni rapide
```

### Detail editoriale

Per ogni gioco:

- titolo lobby;
- descrizione breve con limite caratteri;
- stato visibile/nascosto;
- demo on/off;
- real on/off;
- featured;
- posizione;
- preview player;
- link al detail tecnico in Games.

I campi tecnici restano disponibili in un blocco "Dettagli tecnici" collassabile
o meno dominante.

## Slice operative

### CMS-UX-1 - Audit UI corrente

Stato: completata. Vedi `docs/CMS_0_ADMIN_CMS_INVENTORY.md`.

- misurare cosa e' tecnico e cosa e' editoriale nella vista Site/Lobby;
- identificare campi obbligatori, warning e stati vuoti;
- non cambiare backend.

Accettazione:

- lista dei problemi UX reali;
- nessun cambio runtime.

### CMS-UX-2 - Componentizzazione controllata

Stato: completata in prima passata.

Estrarre componenti medi, non micro-componenti:

```text
site-lobby-publication-panel.tsx
  -> site-lobby-summary.tsx
  -> site-lobby-preview.tsx
  -> site-lobby-title-row.tsx
  -> site-lobby-draft.ts
```

Accettazione:

- il pannello principale resta orchestratore;
- componenti sotto 250-350 righe quando possibile;
- nessun payload/API cambiato.

### CMS-UX-3 - UI editoriale

Stato: prima slice CMS-1B frontend-only completata; restano possibili raffinamenti successivi.

- trasformare la lista tecnica in un editor guidato;
- anteprima piu' vicina alla lobby reale;
- campi con limiti chiari;
- warning prima del save;
- CTA primarie coerenti.

Accettazione:

- un operatore non tecnico capisce cosa andra' online;
- `title_code` e engine non spariscono, ma non dominano la pagina.

### CMS-1C - Bridge asset Title

Stato: completata frontend-only.

- Site/Lobby non introduce upload icone o asset;
- row e preview card mostrano che icona/card asset vivono nel dettaglio gioco;
- i link puntano al detail esistente
  `/admin/games/{engine_code}/titles/{title_code}`;
- endpoint, payload e modello di pubblicazione restano invariati.

### CMS-UX-4 - Hardening

- typecheck;
- build;
- smoke HTTP;
- test manuale con credenziali admin reali;
- responsive desktop/tablet/mobile.

## Note architetturali

Questo cantiere non deve diventare un monolite.

Soglia pratica:

- se un file supera circa 800-1000 righe e contiene piu' responsabilita',
  valutare estrazione;
- evitare componenti microscopici che hanno solo un label e un div;
- separare editoriale, configurazione gioco, publish runtime e preview.

## Fuori scope esplicito

- integrazione WordPress/Strapi;
- nuovo database CMS;
- gestione pagine statiche;
- i18n globale platform;
- promo/bonus engine;
- asset manager generale;
- produzione.
