# CasinoKing - Mines i18n Foundation Implementation Plan

## Stato

Piano operativo validato dal CTO con caveat recepiti.

Questo documento recepisce la decisione prodotto del 2026-05-07:

- il gioco Mines deve avere una foundation multilingua reale;
- le label player-facing non devono restare hardcoded nei componenti;
- il runtime Mines deve usare un resolver copy/i18n;
- il backoffice deve poter gestire le traduzioni per Title;
- publish deve essere bloccato se la copertura copy non e' completa.

Aggiornamento decisione definitiva 2026-05-08:

- epic approvato, ma con runtime a lingua pubblicata unica;
- allowlist editoriale Mines: `it`, `en`, `de`, `es`;
- lingua pubblicata iniziale raccomandata: `it`;
- una sola lingua puo' essere pubblicata per gioco/config;
- nessun selector lingua nel gioco;
- nessuna persistenza `ck_player_locale`;
- nessun parametro `locale` player-side, ne' query string ne' storage locale;
- il runtime pubblico risolve sempre il bundle copy dalla lingua pubblicata
  della config;
- la config pubblicata e il runtime restano single-locale: le altre lingue
  restano contenuto editoriale non esposto al player;
- `game.title` confermato come source of truth del titolo in-game;
- F7-C deve essere chiuso prima di I18N-1.

Documenti collegati:

- `docs/MINES_I18N_CTO_REVIEW_BRIEF.md`
- `docs/MINES_I18N_STRING_INVENTORY.md`
- `docs/MINES_IN_GAME_TITLE_PLAN.md`
- `docs/F7_C_GAMES_DETAIL_ROUTE_REFACTOR_PLAN.md`
- `docs/NEXT_EXECUTION_DETAILED_CTO_REVIEW_PLAN.md`

## Decisione

La decisione definitiva e' single-published-language per gioco/config.

La precedente ipotesi di selector player-side e multi-locale selezionabile dal
giocatore non e' piu' il target per Mines.

Target nuovo:

```text
Title Mines
  -> locale/content map versionata
  -> una sola lingua pubblicata per config
  -> copy bundle risolto dal backend dalla lingua pubblicata
  -> resolver frontend senza label inline nei componenti
```

Questa foundation riguarda il runtime gioco Mines e il suo editor contenuti.
Non apre la i18n globale della platform.

Nota di scope CTO:

- la UI backoffice resta IT-only in questo epic;
- il cantiere product copy platform/backoffice resta separato;
- il tab contenuti/traduzioni gestisce contenuto player-facing Mines e lingua
  pubblicata, non traduce il backoffice stesso.

## Obiettivi

1. Rimuovere dal runtime Mines le label player-facing hardcoded.
2. Centralizzare le key in un manifest stabile.
3. Rendere pubblicabile solo una lingua completa per config.
4. Gestire rules HTML localizzate e sanitizzate.
5. Gestire titolo in-game localizzato.
6. Mantenere il runtime player senza selector lingua, storage locale o
   parametro locale player-side.
7. Mantenere compatibilita' temporanea con `rules_sections_json` e
   `ui_labels_json` come projection legacy, non come source of truth frontend
   dopo la migrazione i18n.
8. Salvare i body rules localizzati in
   `title_locale_maps.locales_json[locale].rules_sections.*.body_html`.

## Non obiettivi

- Non cambiare matematica Mines.
- Non cambiare RTP.
- Non cambiare RNG/fairness.
- Non cambiare wallet/ledger.
- Non introdurre WebSocket.
- Non localizzare subito tutto il backoffice platform.
- Non tradurre contenuti custom DB senza migration/piano.
- Non fare detection automatica della lingua come gate autorevole.
- Non introdurre selector lingua nel runtime Mines.
- Non usare `ck_player_locale`.
- Non accettare `?locale` o altri parametri locale player-side per decidere il
  bundle runtime.

## Stato tecnico attuale

Oggi esiste configurazione per Title ma non i18n:

```text
title_configs.rules_sections_json
title_configs.ui_labels_json
title_configs.draft_rules_sections_json
title_configs.draft_ui_labels_json
mines_title_configs.*
```

Il backend espone:

```text
GET  /api/v1/admin/games/titles/{title_code}/config
PUT  /api/v1/admin/games/titles/{title_code}/config
POST /api/v1/admin/games/titles/{title_code}/config/publish
GET  /api/v1/games/mines/config?title_code={title_code}
```

Gap principali:

- `ui_labels` copre poche chiavi;
- il player consuma davvero solo una parte di quelle chiavi;
- molte stringhe restano inline in `frontend/app/ui/mines/**`;
- rules section body sono configurabili, ma titoli/intro della modale no;
- titolo `MINES` e board labels `MINE/SAFE/PICK` sono hardcoded;
- errori e overlay runtime non passano da catalogo copy.

## Modello dati raccomandato

### Nuova tabella

Creare una tabella Title-level separata:

```sql
CREATE TABLE title_locale_maps (
    id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
    title_code varchar(64) NOT NULL REFERENCES game_titles(title_code),
    version integer NOT NULL,
    status varchar(16) NOT NULL CHECK (status IN ('draft', 'published', 'archived')),
    is_current boolean NOT NULL DEFAULT false,
    published_locale_code varchar(16) NOT NULL,
    fallback_locale_code varchar(16) NOT NULL,
    locales_json jsonb NOT NULL,
    completeness_json jsonb NOT NULL,
    content_hash_sha256 varchar(64) NOT NULL,
    created_by_admin_user_id uuid NULL REFERENCES users(id),
    published_by_admin_user_id uuid NULL REFERENCES users(id),
    created_at timestamptz NOT NULL DEFAULT NOW(),
    published_at timestamptz NULL,
    CHECK (jsonb_typeof(locales_json) = 'object'),
    CHECK (published_locale_code = fallback_locale_code),
    CHECK (locales_json ? published_locale_code),
    CHECK (jsonb_typeof(completeness_json) = 'object'),
    UNIQUE (title_code, version)
);

CREATE UNIQUE INDEX title_locale_maps_one_draft_per_title
    ON title_locale_maps (title_code)
    WHERE status = 'draft';

CREATE UNIQUE INDEX title_locale_maps_one_current_published_per_title
    ON title_locale_maps (title_code)
    WHERE status = 'published' AND is_current = true;
```

Motivi:

- evita di gonfiare `mines_title_configs`;
- resta Title-level e riusabile per futuri engine;
- supporta versioning e audit senza salvare payload enorme nel log;
- permette publish atomico con la config Title esistente;
- non tocca payout/RNG/wallet/ledger.
- mantiene piu' lingue editoriali nel draft/map, ma pubblica e risolve una
  sola lingua alla volta.

### Shape `locales_json`

Shape concettuale:

```json
{
  "it": {
    "copy": {
      "game.title": "Mines",
      "actions.bet": "Punta",
      "actions.collect": "Incassa",
      "board.face.mine": "MINA"
    },
    "rules_sections": {
      "ways_to_win": {
        "title": "Come vincere",
        "body_html": "<p>Scegli celle dalla griglia.</p>"
      }
    }
  }
}
```

Regole:

- allowlist editoriale Mines: `it`, `en`, `de`, `es`;
- HTML ammesso solo in
  `title_locale_maps.locales_json[locale].rules_sections.*.body_html`;
- `copy.*` e `rules_sections.*.title` sono plain text;
- il contenuto editoriale puo' contenere piu' lingue allowlisted;
- ogni runtime/config pubblicata espone esattamente una lingua;
- il cambio lingua avviene modificando la lingua pubblicata della config in
  backoffice e pubblicando la bozza;
- la lingua pubblicata deve contenere tutte le key required;
- placeholder richiesti devono essere presenti e identici al manifest;
- key sconosciute sono extra key fuori manifest;
- extra key in draft producono warning;
- extra key al publish sono bloccanti.

Limiti iniziali CTO:

- `actions.*`: 32 caratteri;
- `board.face.*`: 32 caratteri;
- `errors.*` brevi: 80 caratteri;
- `title_locale_maps.locales_json[locale].rules_sections.*.body_html`: nessun
  hard limit, soft warning a 5KB.

### Compatibilita' con campi esistenti

Durante la transizione:

- `title_configs.rules_sections_json` resta projection legacy della lingua
  pubblicata;
- `title_configs.ui_labels_json` resta projection legacy delle action label
  demo/real quando serve;
- il public runtime continua a esporre `rules_sections` e `ui_labels` finche'
  il frontend non e' migrato del tutto;
- il nuovo payload espone anche `i18n`.

Quando il frontend sara' completamente migrato:

- `rules_sections_json` e `ui_labels_json` potranno diventare compatibility
  projection read-only;
- il nuovo source of truth editoriale sara' `title_locale_maps`.

Decisione CTO sulla backward compatibility: Opzione A.

- `ui_labels_json` resta nello schema per compatibilita';
- il frontend player, dopo i18n, non lo legge piu' come source of truth;
- il public runtime preferisce `presentation_config.i18n` se presente;
- `ui_labels_json` e `rules_sections_json` restano projection legacy della
  lingua pubblicata, non del locale scelto dal player;
- `rules_sections_json` non e' source editoriale dei body rules: la source e'
  `title_locale_maps.locales_json[locale].rules_sections.*.body_html`;
- niente drop colonna in questo epic;
- evitare una coesistenza paritaria con due source of truth.

## Manifest chiavi

Creare un manifest frontend/backend condiviso come concetto.

File candidato frontend:

```text
frontend/app/ui/mines/i18n/mines-copy-manifest.ts
frontend/app/ui/mines/i18n/mines-copy-defaults.ts
frontend/app/ui/mines/i18n/mines-copy-resolver.ts
```

File candidato backend:

```text
backend/app/modules/games/mines/i18n_manifest.py
```

Stato implementativo aggiornato 2026-05-08:

- I18N-1 manifest/default catalog implementato frontend e backend per le key
  runtime inventariate, incluse `quick_launch.*`;
- default catalog disponibili per `it`, `en`, `de` ed `es`;
- I18N-2 schema/service implementato con `title_locale_maps`, versioning,
  content hash, coverage validator e una sola lingua pubblicata per config;
- I18N-3 admin/public API cablate: admin config salva locale map e public
  config espone `presentation_config.i18n`;
- `GET /api/v1/games/mines/config?title_code=...` risolve la lingua pubblicata
  e ignora eventuali parametri `locale` player-side;
- I18N-4/I18N-5 player runtime migrato su resolver per header, actions,
  board, rules shell, settings, balance, launch gate, quick launch ed errori;
- I18N-6 confermato: nessun selector lingua in-game, nessun
  `ck_player_locale`, nessun parametro `locale` player-side;
- I18N-7 implementato come editor minimo nel detail Mines: lingua pubblicata,
  campo `Titolo in-game`, copy grouped by manifest e rules HTML; coverage
  blocking e' backend-side, mentre coverage summary/diff UI resta raffinamento
  successivo. La UI i18n/rules e' stata estratta in
  `frontend/app/ui/mines/mines-i18n-admin-editor.tsx`, mantenendo
  `MinesBackofficeEditor` come orchestratore;
- I18N-8 implementato come `npm run lint:i18n` bloccante agganciato a
  `prebuild`, con scan mirata sul runtime Mines.

Il manifest definisce:

- key;
- seed editoriali per `it`, `en`, `de`, `es`;
- required/optional;
- plain text vs HTML;
- placeholder ammessi;
- max length consigliata;
- area UI;
- note layout/mobile.

Esempio:

```text
actions.bet
  required: true
  html: false
  placeholders: []
  max_length: 24

round.won_notice
  required: true
  html: false
  placeholders: ["amount"]
  max_length: 140

rules_sections.ways_to_win.body_html
  required: true
  html: true
  placeholders: []
```

## API target

### Admin GET config

Endpoint:

```text
GET /api/v1/admin/games/titles/{title_code}/config
```

Shape aggiuntiva:

```json
{
  "published": {
    "i18n": {
      "resolved_locale": "it",
      "default_locale": "it",
      "fallback_locale": "it",
      "editable_locales": ["it", "en", "de", "es"],
      "locale_map_version": 3,
      "content_hash_sha256": "...",
      "copy": {}
    }
  },
  "draft": {
    "i18n": {
      "resolved_locale": "it",
      "editable_locales": ["it", "en", "de", "es"],
      "copy": {}
    }
  }
}
```

Nota:

- per liste admin si puo' restituire solo metadata/completeness;
- per detail editor si restituisce il contenuto completo draft.
- l'admin puo' mostrare `editable_locales` dall'allowlist editoriale;
- nel runtime pubblico eventuali metadata locale non abilitano selector player
  e rappresentano solo la lingua pubblicata.
- eventuali lingue editoriali non pubblicate restano disponibili solo nel
  backoffice, non nel payload runtime.

### Admin PUT config

Endpoint:

```text
PUT /api/v1/admin/games/titles/{title_code}/config
```

Payload esteso:

```json
{
  "published_grid_sizes": [9, 16],
  "published_mine_counts": { "9": [1, 3] },
  "default_mine_counts": { "9": 1 },
  "board_assets": {},
  "locale_map": {
    "published_locale": "it",
    "locales": {}
  }
}
```

Regola:

- `rules_sections` e `ui_labels` possono restare temporaneamente accettati;
- il backend deve normalizzare verso `locale_map`;
- i nuovi client usano `locale_map`.

### Admin publish

Endpoint:

```text
POST /api/v1/admin/games/titles/{title_code}/config/publish
```

Publish atomico:

```text
BEGIN
  validate draft locale map
  update title_configs projection
  update mines_title_configs
  archive old current published locale map
  insert/update published locale map current
  record admin_audit_log title_config_publish with hashes
COMMIT
```

### Public runtime config

Endpoint:

```text
GET /api/v1/games/mines/config?title_code={title_code}
```

Regola:

- il player non invia `locale`;
- il backend usa sempre la `published_locale` della config Title;
- il runtime pubblico non espone draft o lingue alternative selezionabili;
- il runtime pubblico resta single-locale anche se il map editoriale contiene
  `it`, `en`, `de` o `es`;
- se la lingua pubblicata non contiene una key required, loggare errore
  interno e renderizzare la key letterale; il publish gate deve aver impedito
  questo caso.

Shape target:

```json
{
  "presentation_config": {
    "i18n": {
      "published_locale": "it",
      "locale_map_version": 3,
      "copy": {
        "game.title": "Mines",
        "actions.bet": "Punta"
      },
      "rules_sections": {
        "ways_to_win": {
          "title": "Come vincere",
          "body_html": "<p>...</p>"
        }
      }
    },
    "rules_sections": {},
    "ui_labels": {},
    "board_assets": {}
  }
}
```

Regola:

- il runtime pubblico non espone draft;
- il frontend usa `presentation_config.i18n.copy`;
- `rules_sections` e `ui_labels` legacy restano solo per compatibilita'
  transitoria.

## Gestione dentro il gioco

### Resolver frontend

Creare:

```text
frontend/app/ui/mines/i18n/mines-copy.ts
frontend/app/ui/mines/i18n/use-mines-copy.ts
frontend/app/ui/mines/i18n/interpolate.ts
```

Responsabilita':

- ricevere `presentation_config.i18n`;
- esporre `t(key, params?)`;
- bloccare key mancanti in sviluppo/test;
- usare fallback solo come safety net, non come comportamento normale;
- interpolare placeholder in modo controllato;
- non renderizzare HTML da `copy`;
- lasciare HTML solo alle rules gia' sanitizzate backend.

Esempio concettuale:

```text
const copy = useMinesCopy(runtimeConfig)
copy.t("actions.bet")
copy.t("round.won_notice", { amount: formattedAmount })
copy.rulesSection("ways_to_win")
```

### Prop drilling o context

Raccomandazione:

- usare un `MinesCopyProvider` locale alla shell Mines;
- i componenti player ricevono `copy` o usano hook dedicato;
- non introdurre una i18n globale Next.js per tutto il prodotto in questa fase.

Motivo:

- il cantiere riguarda Mines;
- evita di bloccare backoffice/lobby globale;
- mantiene il confine gioco/piattaforma.

### Lingua runtime

Decisione definitiva:

- la lingua runtime e' quella pubblicata nella config Title;
- il player non puo' cambiarla dal gioco;
- non esistono selector lingua in-game, launch gate, mobile settings sheet o
  rail desktop;
- non si usa `localStorage.ck_player_locale`;
- non si passa `?locale` o altro parametro locale player-side al public config;
- start/reveal/cashout restano invariati e non ricevono informazioni di lingua.

Implicazione:

- cambiare lingua pubblicata e' un'operazione editoriale/backoffice e passa da
  draft/save/publish della config, non da un controllo runtime del player.

## Content Production

Il piano tecnico non basta senza una decisione esplicita sulla produzione
contenuti.

Decisione CTO recepita:

- stringhe IT scritte nativamente dall'utente;
- stringhe EN/DE/ES generate con AI, per esempio Claude/GPT, e poi reviewed
  dall'utente o da reviewer umano;
- Translation QA tramite lettura umana completa;
- nessuna traduzione machine-only puo' essere considerata publish-able.

Implicazione:

- una lingua puo' essere pubblicata solo dopo review umana completa;
- lo smoke runtime valida la lingua pubblicata;
- eventuale smoke cross-language richiede pubblicare una config di test con
  una delle altre lingue, non usare selector player-side.

## Backoffice traduzioni

Collocazione:

- detail variante F7-C;
- tab `Translations` o `Copy`;
- non dentro `Theme`;
- non dentro `Grid & mines`;
- non dentro Site/Lobby.

Funzioni minime:

- campo lingua pubblicata per la config;
- campo esplicito `Titolo in-game` per ogni locale editoriale, mappato alla
  key `game.title`;
- add locale da allowlist editoriale `it`/`en`/`de`/`es`;
- tab per locale;
- coverage summary per locale;
- editor key/value raggruppato per area;
- editor HTML solo per rules body;
- diff draft vs published;
- save draft;

Nota:

- la UI del backoffice resta IT-only per questo epic;
- le label del tab editor non entrano nel catalogo player;
- questo epic non introduce una i18n backoffice/platform.
- l'editor contenuti Mines i18n e la scelta della lingua pubblicata fanno parte
  di questo cantiere Mines.
- publish live con gate backend.

UX importante:

- mostrare missing keys;
- mostrare placeholder richiesti;
- mostrare max length per label corte;
- evitare che l'admin modifichi key tecniche;
- master read-only come oggi.

## Titolo in-game

Il titolo in-game diventa key localizzata:

```text
game.title
```

Il backoffice deve comunque esporre un campo esplicito:

```text
Titolo in-game
```

Regola:

- il campo `Titolo in-game` legge e salva
  `title_locale_maps.locales_json[locale].copy["game.title"]`;
- la label admin non introduce `in_game_title`, `display_name` o altri campi
  come source alternative;
- la locale map resta l'unica source of truth editoriale per il titolo visibile
  nel frame di gioco.

La proposta precedente `title_configs.in_game_title` resta valida solo se il CTO
vuole una projection legacy della lingua pubblicata.

Raccomandazione:

- non aggiungere una colonna separata se si implementa subito i18n;
- salvare il titolo dentro `title_locale_maps.locales_json[locale].copy.game.title`;
- usare `game.title` nel wordmark e nel rules title;
- mantenere separati `title_code`, nome variante admin e nome lobby.

## Publish gating

Il publish della config Title deve fallire se:

- locale map draft assente;
- lingua pubblicata non presente nel draft;
- lingua pubblicata fuori allowlist;
- extra key fuori manifest al publish;
- key required mancante;
- stringa required vuota;
- placeholder obbligatorio mancante;
- placeholder ignoto presente;
- HTML presente fuori rules body;
- HTML rules non passa sanitizzazione;
- label corta supera limite hard deciso dal CTO;
- master Title viene mutato;
- altra publish concorrente produce due current map.

In draft, le extra key fuori manifest generano warning per aiutare la pulizia
editoriale. Al publish diventano bloccanti: il manifest e' il contratto.

Nessun fallback puo' rendere pubblicabile una lingua incompleta. La lingua
pubblicata deve passare coverage completo sulle key required.

Errore consigliato:

```text
VALIDATION_ERROR
I18N_COVERAGE_INCOMPLETE
```

con dettaglio:

```json
{
  "locale": "it",
  "missing_keys": ["actions.collect"],
  "invalid_placeholders": ["round.won_notice"]
}
```

## Audit

`admin_audit_log` non deve salvare l'intera locale map.

Payload consigliato:

```json
{
  "engine_code": "mines",
  "title_code": "mines_lagoon",
  "changed_fields": ["locale_map", "published_grid_sizes"],
  "locale_map": {
    "version": 4,
    "published_locale": "it",
    "editable_locales": ["it", "en", "de", "es"],
    "content_hash_sha256": "..."
  }
}
```

## Piano di implementazione dettagliato

### I18N-0 - Decisione e baseline

Azioni:

1. Registrare verdict CTO: epic approvato con caveat.
2. Confermare F7-C route/detail stabilizzato come prerequisito operativo prima
   di I18N-1.
3. Congelare allowlist editoriale Mines:

```text
it
en
de
es
```

4. Congelare lingua pubblicata iniziale raccomandata: `it`.
5. Registrare che il player non puo' selezionare lingua in runtime.
6. Registrare che `?locale`, `ck_player_locale` e altri parametri locale
   player-side sono fuori target.
7. Registrare content production plan.
8. Rieseguire smoke locale baseline.

Accettazione:

- nessun codice i18n scritto prima di F7-C route/detail stabilizzato;
- F7-C e i18n hanno ordine chiaro, con decomposizione editor residua tracciata
  come debito tecnico non gating;
- caveat CTO integrati nei documenti.

### I18N-1 - Manifest e default catalog

Write set:

- `frontend/app/ui/mines/i18n/**`
- `backend/app/modules/games/mines/i18n_manifest.py`
- `docs/MINES_I18N_STRING_INVENTORY.md`

Azioni:

1. Creare manifest completo delle key.
2. Creare seed IT nativo.
3. Creare seed EN/DE/ES generati con AI e reviewed da umano.
4. Definire placeholder e max length.
5. Definire regole extra key: warning draft, blocco al publish.
6. Aggiungere test unitari manifest/placeholder.

Accettazione:

- ogni stringa inventariata ha key;
- il manifest e' leggibile da backend validator e frontend resolver;
- nessuna UI cambia ancora comportamento.

### I18N-2 - Schema e service locale map

Write set:

- `backend/migrations/sql/0031__title_locale_maps.sql`
- `backend/app/modules/platform/catalog/title_locale_service.py`
- `backend/app/modules/games/mines/backoffice_config.py`
- `backend/app/modules/platform/catalog/title_config_service.py`
- test backend.

Azioni:

1. Creare tabella `title_locale_maps`.
2. Seed `it`, `en`, `de` ed `es` coerenti con il content production plan.
3. Implementare draft load/update.
4. Implementare validator completeness.
5. Implementare publish current version.
6. Aggiornare audit hash.

Accettazione:

- migration applicabile;
- fresh DB crea lingua pubblicata iniziale valida;
- publish atomico;
- nessun cambio a payout/ledger.

### I18N-3 - API admin/public

Write set:

- `backend/app/api/routes/admin.py`
- `backend/app/api/routes/mines.py`
- contract/integration tests.

Azioni:

1. Estendere admin GET/PUT/PUBLISH con `locale_map`.
2. Estendere public config con `presentation_config.i18n` risolto dalla lingua
   pubblicata, senza parametro `locale` player-side.
3. Restituire `presentation_config.i18n`.
4. Mantenere `rules_sections` e `ui_labels` legacy.
5. Aggiungere error detail per coverage incompleta.
6. Validare che il public runtime non accetti selector/query/storage locale
   come fonte di risoluzione.

Accettazione:

- `GET /games/mines/config?title_code=x` risolve la lingua pubblicata;
- richieste con `locale` non cambiano il bundle runtime;
- il payload espone `published_locale` come metadata;
- draft non visibile pubblicamente;
- vecchi test config restano verdi o aggiornati in modo compatibile.

### I18N-4 - Resolver frontend

Write set:

- `frontend/app/ui/mines/i18n/**`
- `frontend/app/lib/types.ts`
- `frontend/app/lib/helpers.ts`

Azioni:

1. Estendere `MinesPresentationConfig` con `i18n`.
2. Implementare `useMinesCopy`.
3. Spostare formatting label sensibili fuori da helper hardcoded.
4. Aggiungere interpolazione sicura.
5. Aggiungere test TypeScript/unit se infrastruttura disponibile.

Accettazione:

- resolver funziona con locale `it`, `en`, `de` ed `es`;
- fallback e missing key sono tracciabili;
- nessuna dipendenza da browser locale come fonte unica.

### I18N-5 - Migrazione componenti player

Write set:

- `frontend/app/ui/mines/mines-standalone.tsx`
- `frontend/app/ui/mines/mines-stage-header.tsx`
- `frontend/app/ui/mines/mines-board.tsx`
- `frontend/app/ui/mines/mines-rules-modal.tsx`
- `frontend/app/ui/mines/mines-balance-footer.tsx`
- `frontend/app/ui/mines/mines-mobile-settings-sheet.tsx`
- `frontend/app/ui/mines/mines-action-buttons.tsx`

Azioni:

1. Header: `game.title`, `actions.exit_aria`.
2. Actions: `actions.bet`, `actions.collect`, loading labels.
3. Controls: grid, mines, bet amount, settings.
4. Board: face labels e aria.
5. Rules: title, intro, section titles, safe reveal rows.
6. Errors: dialog title, OK, auth/session/network/runtime overlay.
7. Table entry: wallet source, amount, enter game.
8. Balance: demo/table/win/currency labels.

Accettazione:

- scan non trova label player-facing hardcoded non giustificate;
- desktop e mobile renderizzano `en`;
- `it` mostra copy italiano dove configurato;
- round attivo non viene alterato.

### I18N-6 - Runtime lingua pubblicata e rimozione selector

Write set:

- `frontend/app/ui/mines/mines-standalone.tsx`
- eventuali componenti selector lingua Mines da rimuovere se presenti
- CSS Mines.

Azioni:

1. Leggere `presentation_config.i18n.published_locale`.
2. Non mostrare selector lingua nel gioco.
3. Non persistere preferenze in `localStorage.ck_player_locale`.
4. Non ricaricare public config con `locale`.
5. Verificare che start/reveal/cashout non ricevano parametri lingua.

Accettazione:

- il runtime renderizza solo la lingua pubblicata;
- non esistono controlli player-facing per cambiare lingua;
- scan non trova `ck_player_locale` o `?locale` nel path player Mines;
- mobile 375px senza overflow.

### I18N-7 - Backoffice editor traduzioni

Prerequisito consigliato:

- F7-C route/detail almeno stabilizzato.

Write set:

- `frontend/app/ui/mines/mines-backoffice-editor.tsx`
- nuovi componenti `frontend/app/ui/mines/i18n-editor/**` o
  `frontend/app/ui/title-editor/**`
- API client/types.

Azioni:

1. Aggiungere tab `Translations`.
2. Gestire lingua pubblicata della config.
3. Aggiungere locale da allowlist editoriale `it`/`en`/`de`/`es`.
4. Editor grouped by namespace.
5. Editor rules HTML separato.
6. Coverage report.
7. Save draft e publish gating.

Accettazione:

- admin vede missing key prima del publish;
- publish fallisce con messaggio leggibile se manca copy;
- master read-only;
- variante modificabile.

### I18N-8 - Static scan e QA

Write set:

- script frontend `lint:i18n` basato su scan mirata dei file runtime Mines;
- docs smoke.

Azioni:

1. Aggiungere scan per stringhe player-facing residue nei file runtime Mines.
2. Aggiungere uno script `frontend` `lint:i18n` basato su regex allowlisted e
   path mirati.
3. Rendere lo scan bloccante: exit non-zero, non warning silenzioso.
4. Escludere il backoffice dallo scan: la UI backoffice resta IT-only in
   questo epic e non entra nel catalogo player/runtime.
5. Aggiungere test backend coverage.
6. Aggiungere smoke desktop/mobile.
7. Aggiungere Playwright/browser smoke se infrastruttura disponibile.

Accettazione:

- `npx tsc --noEmit` verde;
- `npm run lint:i18n` verde da `frontend`;
- `npm run build` verde;
- backend test config/i18n verdi;
- smoke completo `it`/`en`/`de`/`es` su demo dopo I18N-7, pubblicando di volta
  in volta una config di test single-locale;
- no overflow evidente su 375px.

## Parallelizzazione multiagentica

Usare agenti solo con write set separati.

### Agent A - Backend/schema

Responsabilita':

- migration `title_locale_maps`;
- service locale map;
- validator completeness;
- public/admin API.

Write set:

- `backend/migrations/sql/**`
- `backend/app/modules/platform/catalog/title_locale_service.py`
- `backend/app/modules/games/mines/backoffice_config.py`
- `backend/app/api/routes/admin.py`
- `backend/app/api/routes/mines.py`
- backend tests.

### Agent B - Frontend resolver/player

Responsabilita':

- manifest TS;
- resolver/hook/provider;
- refactor componenti player.

Write set:

- `frontend/app/ui/mines/i18n/**`
- `frontend/app/ui/mines/mines-*.tsx`
- `frontend/app/lib/types.ts`
- `frontend/app/lib/helpers.ts`

Non tocca backoffice editor se Agent C lavora in parallelo.

### Agent C - Backoffice translations UI

Responsabilita':

- tab traduzioni;
- coverage report;
- editor rules/copy per locale.

Write set:

- `frontend/app/ui/mines/mines-backoffice-editor.tsx`
- `frontend/app/ui/mines/i18n-editor/**`
- `frontend/app/ui/title-editor/**`

Parte dopo che Agent A ha stabilizzato payload API o lavora su mock types.

### Agent D - QA/static scan/docs

Responsabilita':

- script frontend `lint:i18n` per hardcoded labels player-facing nei file
  runtime Mines;
- smoke plan;
- documentazione finale;
- aggiornare atlas solo se cambiano responsabilita' reali.

Write set:

- `docs/**`
- eventuali test/lint dedicati.

### Agent E - F7-C integration

Responsabilita':

- route/detail dedicati se necessari per ospitare bene il tab translations;
- evitare che l'overview monti editor complessi.

Write set:

- `frontend/app/admin/games/**`
- `frontend/app/ui/games/**`
- `frontend/app/ui/casinoking-console.tsx`

## Test backend

Comandi candidati:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:56543/casinoking'
python -m pytest tests/integration/test_title_configs_split.py tests/integration/test_mines_backoffice_config.py
python -m pytest tests/integration/test_game_library_publication.py tests/contract/test_mines_runtime_contract.py
python -m pytest tests/integration/test_financial_and_mines_flows.py
```

Nuovi test:

- migration `title_locale_maps` e indici partial unique;
- admin GET include `locale_map`;
- admin PUT salva draft locale map;
- publish fallisce con missing key;
- publish fallisce con placeholder invalido;
- publish atomico non sporca published su errore;
- public config risolve la lingua pubblicata;
- public config ignora o rifiuta senza effetto decisionale eventuali parametri
  `locale` player-side legacy;
- duplicate Title copia locale map published;
- audit registra hash/versione, non payload completo;
- due publish concorrenti non producono due current published.

## Test frontend

Comandi candidati:

```powershell
cd frontend
npx tsc --noEmit
npm run build
```

Smoke:

1. Aprire Mines demo con config pubblicata in `it`.
2. Verificare header, board, buttons, rules, error dialog.
3. Pubblicare in backoffice config di test con lingua pubblicata `en`, `de` ed
   `es`, una alla volta.
4. Verificare copy inglese/tedesca/spagnola senza selector player.
5. Verificare assenza di selector lingua in-game.
6. Verificare assenza di letture/scritture `ck_player_locale`.
7. Mobile 375px.
8. Label lunghe controllate.
9. Rules HTML sanitizzato.
10. Nessun hardcoded player-facing residuo.

## Rischi

| Rischio | Mitigazione |
| --- | --- |
| Big bang troppo grande | Slice manifest/schema/resolver/editor separate. |
| Traduzioni incomplete pubblicate | Publish gate backend. |
| Fallback nasconde bug | Nessun fallback player-side; test che fallisce se la lingua pubblicata manca key required. |
| Doppia source of truth | Projection legacy temporanea documentata. |
| Editor ingestibile | Raggruppare per namespace e coverage. |
| Label lunghe rompono mobile | Max length + visual QA 375px. |
| Cambio lingua durante round confonde stato | Nessun cambio lingua player-side; cambio lingua solo via publish backoffice. |
| Audit troppo pesante | Salvare hash/versione, non payload completo. |

## Decisioni CTO recepite

- `title_locale_maps` confermata.
- Allowlist editoriale Mines confermata: `it`, `en`, `de`, `es`.
- Lingua pubblicata iniziale raccomandata: `it`.
- Una sola lingua pubblicata per gioco/config.
- Nessun selector lingua nel gioco.
- Nessuna persistenza `ck_player_locale`.
- Nessun parametro `locale` player-side.
- `game.title` confermato come source of truth del titolo in-game.
- Nessuna nuova source `in_game_title` obbligatoria in questo epic.
- Extra key fuori manifest: warning in draft, bloccante al publish.
- Max length iniziali: 32 per `actions.*` e `board.face.*`, 80 per
  `errors.*` brevi, soft warning 5KB per body HTML rules.
- Backoffice UI resta IT-only in questo epic.
- i18n globale platform resta rinviata.
- Backward compatibility `ui_labels_json`: Opzione A, schema mantenuto e
  frontend player migrato su `presentation_config.i18n`.
- `rules_sections_json`: projection legacy della lingua pubblicata; i body
  rules localizzati vivono in
  `title_locale_maps.locales_json[locale].rules_sections.*.body_html`.
- Runtime/config pubblicata: single-locale, senza selector o parametro locale
  player-side.

## Fuori scope finale

- production readiness;
- external adapter;
- wallet/ledger;
- payout runtime;
- fairness/RNG;
- full platform i18n;
- traduzione automatica;
- CMS generale.
