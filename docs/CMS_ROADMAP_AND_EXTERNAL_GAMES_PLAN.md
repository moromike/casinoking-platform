# CMS Roadmap And External Games Plan

Documento di progetto per review CTO.

## Stato del documento

- Tipo: roadmap CMS, catalogo giochi, asset e integrazioni future.
- Stato: bozza pronta per review CTO.
- Ambito: Site CMS, Game Catalog CMS, homepage/banner, asset, giochi esterni, mock provider locale.
- Non sostituisce: `docs/SITE_CMS_EDITORIAL_UX_PLAN.md`, `docs/SITE_LOBBY_PUBLICATION_PLAN.md`, `docs/BACKOFFICE_GAMES_UX_REORGANIZATION_PLAN.md`, `docs/MINES_EXTERNAL_GAME_AND_TABLE_SESSION_PLAN.md`.

## Perche' esiste questo documento

Il backoffice sta diventando piu' vicino a un CMS, ma non deve trasformarsi subito in un CMS generico e fragile.

Oggi servono tre cose diverse:

1. governare cosa appare al player nel sito e nella lobby;
2. governare configurazione, copy, asset e pubblicazione dei giochi proprietari;
3. preparare il terreno per giochi esterni senza aprire ora una integrazione economica reale.

Questo documento mette ordine tra queste esigenze e propone una roadmap a slice.

## Lessico proposto

| Nome | Descrizione |
| --- | --- |
| Site CMS | Gestisce contenuti editoriali del sito: homepage, banner, sezioni, lobby copy, ordinamento e visibilita'. |
| Game Catalog CMS | Gestisce catalogo giochi: Engine, Title, varianti, configurazioni, theme, asset, i18n/copy e publish state. |
| Proprietary Game | Gioco sviluppato dentro CasinoKing, come Mines. Usa Game Adapter e Game Runtime Layer. |
| External Game Provider | Fornitore o prodotto esterno che puo' apparire nel catalogo, con regole di launch/settlement separate. |
| External Product | Concetto piu' ampio di gioco esterno: puo' essere slot, live casino, mini-game, contenuto demo o provider mock. |
| Provider Adapter | Futuro adapter tecnico per parlare con un provider esterno. Diverso dal Game Adapter interno del gioco proprietario. |

## Decisione principale

Non costruire ora un CMS proprietario completo.

Costruire invece superfici CMS mirate:

- Site/Lobby editorial;
- Game Catalog CMS;
- asset e media minimi;
- homepage/banner;
- modello dati per provider esterni, prima locale/mock.

Un CMS generico ora sarebbe prematuro perche' rischia di aggiungere tabelle, permessi, workflow e storage senza ancora sapere quali contenuti saranno davvero gestiti.

## Stato attuale

| Area | Stato |
| --- | --- |
| Site/Lobby Publishing | Presente: visibilita', demo/real, order, featured, publish gate. |
| Games editor | Presente: Title detail, config, theme e asset nel backoffice esistente. Da trattare come cantiere separato/completamento: route dedicate F7-C e i18n/copy. |
| Admin audit log | Presente per modifiche operative non finanziarie. |
| Asset registry | Presente per asset Title/theme. |
| Homepage/banner CMS | CMS-2A backend presente: `site_home_slots`, API admin/public e audit operativo. CMS-2B admin UI minimale completata nella sezione Site. CMS-2C player read path completato: la lobby consuma `/site/home` per il hero editoriale con fallback a `/games/library`. |
| Media library generale | Non presente. |
| Provider esterni | Non presenti. |
| Adapter provider esterno | Non presente e non necessario ora per real money. |

## Roadmap proposta

### CMS-0 - Inventario e pulizia concettuale

Obiettivo:

- elencare cosa oggi e' gia' "CMS-like";
- distinguere configurazione tecnica, configurazione gioco e contenuto editoriale;
- identificare campi duplicati o esposti con linguaggio troppo tecnico.

Output:

- mappa delle schermate backoffice coinvolte;
- lista campi editoriali vs tecnici;
- eventuali quick fix copy/UI.

Perche':

- evita di costruire un CMS nuovo sopra schermate gia' esistenti ma nominate male.

### CMS-1 - Site/Lobby editorial UX

Obiettivo:

- trasformare Site/Lobby Publishing in una vista editoriale piu' guidata;
- mostrare al backoffice il catalogo come lo vede il player;
- rendere chiari demo, real, visibilita', ordine e featured.

In scope:

- preview compatta card lobby;
- linguaggio editoriale;
- stati publish chiari;
- verifica audit log dopo publish;
- mobile/responsive admin se rilevante.

Out of scope:

- nuovo CMS DB;
- gestione provider esterni;
- banner homepage;
- pagine statiche.

### CMS-2 - Homepage banner e spotlight

Obiettivo:

- gestire banner/hero/spotlight della homepage o lobby principale.

Stato 2026-05-08:

- CMS-2A backend completato come slice sicura admin/CMS;
- aggiunta tabella `site_home_slots`;
- aggiunti endpoint `GET /api/v1/site/home?site_code=casinoking` e admin
  `/api/v1/admin/sites/{site_code}/home-slots`;
- target `title_demo` / `title_real` validati contro catalogo e Site/Lobby
  publication;
- audit operativo su `admin_audit_log` con `site_home_slot_update` e
  `site_home_slot_publish`;
- nessun launch, wallet, ledger, payout, RNG o runtime Mines modificato.

Aggiornamento CMS-2B:

- aggiunto editor admin frontend per homepage/banner slots nella sezione Site;
- la UI lista slot, crea nuovi slot e modifica title/subtitle/CTA/target,
  sort order, status e schedule;
- i target selezionabili derivano da
  `GET /api/v1/catalog/sites/casinoking/titles`, escludendo master e hidden e
  separando demo/real in base ai flag pubblicati;
- `media_asset_id` resta readonly/null: upload media e media library restano
  fuori slice;
- nessun backend, launch, wallet, ledger, payout, RNG o runtime Mines
  modificato.

Aggiornamento CMS-2C:

- la lobby player legge `GET /api/v1/site/home?site_code=casinoking` per il
  primo slot editoriale pubblicato;
- `/games/library` resta la fonte unica della griglia giochi, delle card e dei
  fallback di disponibilita';
- se `/site/home` e' vuoto o non disponibile, la lobby mantiene il copy e lo
  spotlight precedenti senza mostrare errore player;
- le CTA dello slot mappano `title_demo` e `title_real` sugli stessi link
  demo/real gia' usati dalle card gioco;
- nessun backend, launch, wallet, ledger, payout, RNG o runtime Mines
  modificato.

Entita' minima proposta:

```text
site_home_slots
  id
  site_code
  slot_key
  title
  subtitle
  cta_label
  cta_target_type
  cta_target_ref
  media_asset_id
  sort_order
  status
  starts_at
  ends_at
  created_by
  updated_by
```

Regole:

- un banner non deve lanciare un Title non pubblicabile;
- i target devono essere validati contro Site/Lobby;
- publish deve scrivere audit operativo;
- niente impatto wallet/ledger.

Perche':

- e' il primo bisogno CMS visibile lato player;
- permette di promuovere Mines o una variante senza hardcoding frontend.

### CMS-3 - Media e asset library minima

Obiettivo:

- evitare upload sparsi e asset duplicati;
- classificare asset per uso: game card, banner, icon, background, theme.

Asset type minimi:

- `game_card`;
- `homepage_banner`;
- `lobby_background`;
- `game_background`;
- `tile_hidden`;
- `tile_safe`;
- `tile_mine`;
- `tile_prize`;
- `provider_logo`.

Regole:

- asset media non cambiano matematica o runtime;
- cancellazione solo se non referenziato o con soft delete;
- preview prima di publish;
- audit upload/delete/update.

### CMS-4 - External provider catalog, solo locale/mock

Obiettivo:

- modellare giochi/prodotti esterni senza integrarli davvero in real money.

Entita' concettuali:

```text
external_game_providers
  provider_code
  display_name
  status
  integration_mode
  notes

external_games
  provider_code
  external_game_code
  display_name
  category
  supports_demo
  supports_real
  launch_mode
  thumbnail_asset_id
  metadata_json
  status

site_external_games
  site_code
  provider_code
  external_game_code
  lobby_visibility
  demo_enabled
  real_enabled
  sort_order
  featured_rank
```

Primo scope consigliato:

- provider mock locale;
- launch demo che apre una pagina placeholder controllata;
- nessun movimento wallet/ledger;
- nessun secret reale;
- nessun webhook reale;
- audit operativo sulle modifiche.

Perche':

- non e' troppo prematuro modellare il catalogo;
- sarebbe prematuro integrare un settlement reale senza contratto provider, sicurezza e legal.

### CMS-5 - External launch adapter

Trigger:

- solo quando si decide di integrare davvero un provider, anche se in locale.

Obiettivo:

- definire come CasinoKing lancia un gioco esterno.

Contratti da decidere:

- demo launch;
- real launch;
- player identity mapping;
- session token;
- callback/webhook;
- provider balance mode;
- settlement mode;
- timeout/retry;
- audit e correlation id.

Regola non negoziabile:

- un provider esterno non deve scrivere direttamente nel wallet/ledger CasinoKing.

Modelli possibili:

| Modello | Descrizione | Rischio |
| --- | --- | --- |
| Demo only | Il provider mostra gioco demo, nessun saldo reale. | Basso |
| Seamless wallet | CasinoKing resta source of funds, provider chiama API settlement. | Alto, richiede design dedicato |
| Transfer wallet | Credito trasferito a provider e poi riconciliato. | Molto alto, sconsigliato per MVP |
| Aggregator mock | Provider locale simula flussi per test UI. | Basso |

### CMS-6 - Reporting provider esterni

Obiettivo:

- mostrare cosa e' stato lanciato e quando;
- separare reporting di lancio da reporting economico.

Primo scope:

- launch logs;
- provider status;
- errori di launch;
- audit modifiche catalogo;
- nessun report P/L finche' non esiste settlement reale.

## Prompt per asset e icone Mines

Questi prompt sono pensati per generare master bitmap. Dopo la generazione, gli asset vanno selezionati, ritagliati e ottimizzati prima di usarli nel prodotto.

### Regole comuni

- Stile: premium online casino, pulito, leggibile, non cartoon infantile.
- Palette consigliata: nero carbone, verde smeraldo, oro tenue, ciano freddo, bianco luminoso.
- Evitare testo dentro l'immagine, salvo richiesta esplicita.
- Per icone: PNG trasparente, master 1024x1024, leggibile a 64x64.
- Per banner/background: 16:9 e 21:9, spazio libero per overlay testo.
- Non usare loghi di brand reali.
- Non imitare direttamente Windows Minesweeper; prendere solo l'idea di reveal chiaro e immediato.

### Prompt base stile Mines

```text
Premium online casino Mines game visual style, elegant dark graphite interface, emerald and cyan highlights, subtle gold accents, polished 3D game objects, crisp edges, high contrast, readable at small sizes, modern gambling product aesthetic, no text, no logo, no watermark.
```

### Icona mina

```text
Create a transparent PNG icon of a stylized casino mines bomb for a premium Mines game. The object is a dark graphite spherical mine with subtle metallic facets, small emerald warning glow, soft cyan rim light, polished 3D look, centered composition, high contrast, readable at 64px, no text, no logo, no background.
```

### Icona diamante/premio

```text
Create a transparent PNG icon of a brilliant faceted diamond prize for a premium casino Mines game. The diamond is icy cyan with white highlights and a faint emerald reflection, luxury 3D render, centered, crisp silhouette, readable at 64px, no text, no logo, no background.
```

### Tile nascosta

```text
Create a square hidden tile asset for a premium Mines game board. Dark graphite beveled square, subtle brushed texture, thin emerald edge glow, slight depth, clean modern casino UI, no symbol, no text, seamless enough for a grid, transparent or flat dark background, 1024x1024.
```

### Tile safe rivelata

```text
Create a square revealed safe tile for a premium Mines game board. Dark graphite beveled tile opened with a small cyan diamond glow in the center, elegant casino style, subtle green success light, crisp grid-ready edges, no text, no logo, 1024x1024.
```

### Tile mina rivelata

```text
Create a square revealed mine tile for a premium Mines game board. Dark graphite beveled tile with a stylized mine symbol revealed in the center, red-orange danger glow kept tasteful and not cartoonish, cyan rim light, high contrast, no text, no logo, 1024x1024.
```

### Sfondo gioco Mines

```text
Create a wide background image for a premium online casino Mines game screen. Dark graphite gaming table surface, subtle geometric grid pattern, emerald and cyan ambient light, soft gold highlights, enough empty space in the center for a game board and UI overlays, elegant and not busy, no text, no logo, 16:9.
```

### Sfondo homepage/lobby Mines

```text
Create a cinematic 21:9 hero banner for a premium casino Mines game featured in a website lobby. Show a refined dark gaming table with glowing diamond crystals and a few stylized mine objects, emerald/cyan light beams, luxury casino atmosphere, clear empty area on the left for text overlay, no text, no logo, high-end product photography style.
```

### Icona card sito web

```text
Create a square game card icon for a casino website showing the Mines game identity. Composition: one glowing cyan diamond and one dark stylized mine on a graphite beveled tile grid, premium casino lighting, crisp and bold at small size, no text, no logo, 1024x1024.
```

### Piccola icona menu/fav

```text
Create a minimal transparent PNG icon for a Mines game navigation item. Use a simple cyan diamond over a tiny graphite mine-grid mark, flat-polished hybrid style, extremely readable at 24px and 32px, no text, no logo, no background.
```

### Loss burst / effetto mina

```text
Create a transparent PNG visual effect for a Mines game loss reveal. Elegant red-orange pulse burst with small graphite fragments and subtle cyan rim light, premium casino style, not violent, not cartoonish, no text, no logo, centered, transparent background.
```

### Win sparkle / effetto diamante

```text
Create a transparent PNG visual effect for a Mines game safe reveal win. Cyan and emerald sparkle burst around a faceted diamond glint, premium casino style, clean, high contrast, no text, no logo, centered, transparent background.
```

## Integrazione giochi esterni: valutazione

La richiesta "un domani vorrei le API di integrazione" e' corretta, ma va separata in due livelli.

Livello da fare presto:

- modellare nel CMS che un prodotto puo' essere proprietario o esterno;
- preparare campi catalogo/provider;
- costruire un provider mock locale;
- mostrare external products in lobby senza economia reale.

Livello da non fare ora:

- real money provider;
- seamless wallet provider reale;
- callback economiche;
- gestione secret provider reali;
- settlement cross-system.

Motivo:

- il catalogo esterno e' utile per product strategy;
- l'economia esterna e' area critica e va disegnata con lo stesso rigore di wallet/ledger.

## Relazione con Game Architecture

Per giochi proprietari:

```text
Proprietary Game -> Game Adapter -> Game Runtime Layer -> Wallet/Ledger
```

Per giochi esterni:

```text
External Product -> Provider Adapter -> External Provider
                 -> Casino Platform launch/audit/catalog
                 -> settlement design dedicato solo se real money
```

Non mischiare i due adapter:

- Game Adapter: boundary interno per giochi CasinoKing;
- Provider Adapter: boundary esterno verso fornitori terzi.

## Next step consigliati

1. Chiudere review CTO su naming e scope.
2. Eseguire CMS-0 inventory.
3. Aprire CMS-1 Site/Lobby editorial UX.
4. Disegnare CMS-2 homepage banner dopo CMS-1.
5. Preparare solo il modello concettuale External Provider, senza settlement reale.
6. Rinviare API provider real money finche' non c'e' un requisito concreto.

## Decisioni da validare con CTO

| Decisione | Proposta |
| --- | --- |
| CMS generale | Non ora. Procedere per superfici mirate. |
| Homepage banner | Si, come CMS-2 dopo Site/Lobby editorial. |
| Media library | Minima, legata ad asset realmente usati. |
| External games | Modellare catalogo e mock provider, non real settlement. |
| Provider wallet | Nessun provider scrive direttamente wallet/ledger. |
| Provider real money | Richiede documento dedicato financial/security/API. |

## Criteri di accettazione

Il piano e' rispettato se:

- ogni nuova superficie CMS ha owner, audit e publish state;
- homepage/banner non bypassa lobby publication;
- asset non cambiano runtime economico o matematica;
- provider esterno resta separato da gioco proprietario;
- il mock provider non introduce finte garanzie su real money;
- il README rimanda al documento quando si parla di CMS o external games.
