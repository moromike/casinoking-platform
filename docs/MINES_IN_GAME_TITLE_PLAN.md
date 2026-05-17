Status: COMPLETED
Last meaningful update: 2026-05-08

# CasinoKing - Mines In-Game Title Plan

## Stato

Piano operativo aggiornato dopo review CTO.

Aggiornamento 2026-05-07:

- se il piano i18n Mines viene implementato ora, il titolo in-game non deve
  nascere come colonna separata obbligatoria;
- il titolo in-game deve diventare la key localizzata `game.title` dentro la
  locale map del Title;
- la proposta `title_configs.in_game_title` resta solo come opzione di
  compatibility projection della lingua pubblicata, se il CTO la richiede.

Aggiornamento post review CTO:

- `game.title` e' confermato come source of truth del titolo in-game;
- non si introduce una nuova source separata per il titolo runtime;
- `game_titles.display_name` resta per backoffice/catalogo/lobby;
- il player vede il titolo della lingua pubblicata nella locale map published.
- allowlist editoriale Mines: `it`, `en`, `de`, `es`;
- runtime e config pubblicata restano single-locale;
- nessun selector in-game, nessun `ck_player_locale`, nessun parametro locale
  player-side;
- backoffice UI resta IT-only per questo epic.

Questo documento risponde alla richiesta:

```text
permettere la modifica del titolo del gioco Mines,
cioe' il titolo visibile in-game.
```

Non riguarda:

- `title_code`;
- nome variante admin;
- nome lobby;
- descrizione lobby;
- theme visuale.

## Stato attuale

Oggi il titolo visibile nel frame di gioco e' hardcoded nel frontend:

```text
MINES
```

Il punto UI e' il wordmark in:

```text
frontend/app/ui/mines/mines-stage-header.tsx
```

Il player Mines usa `title_code` dall'URL per:

- config runtime;
- theme;
- launch token;
- access session;
- table session;
- round real/demo.

Pero' il testo visibile nel frame non deriva ancora dalla config del Title.

## Modello nomi attuale

| Campo | Owner | Uso | Non usarlo per |
| --- | --- | --- | --- |
| `title_code` | Platform catalog | Identita' tecnica stabile | Copy visibile. |
| `game_titles.display_name` | Games backoffice | Nome variante/admin/catalogo | Titolo in-game se serve controllo separato. |
| `site_titles.lobby_display_name` | Site/Lobby | Nome editoriale nella lobby player | Frame di gioco. |
| `site_titles.lobby_description` | Site/Lobby | Descrizione card lobby | Frame di gioco. |
| `title_configs.ui_labels_json` | Title config | Label operative demo/real | Titolo gioco. |
| `theme_tokens_json` | Theme | Visual token | Copy/titoli. |

Problema:

- manca un campo semanticamente pulito per il titolo in-game.

## Proposta precedente

Aggiungere un campo title-level publish-gated in `title_configs`:

```text
in_game_title
draft_in_game_title
```

Semantica:

- `in_game_title`: valore published visto dal player;
- `draft_in_game_title`: bozza backoffice;
- fallback: `Mines`;
- deve essere scritto nella lingua dichiarata dalla configurazione Title;
- plain text;
- no HTML;
- max 60 o 80 caratteri, da decidere con CTO;
- trim lato backend;
- stringa vuota non ammessa.

Perche' `title_configs`:

- e' config generica per Title;
- e' gia' draft/publish;
- viene composta nel payload runtime Mines;
- non e' Site-specific;
- non e' engine-specific matematica.

## Proposta aggiornata con i18n Mines

Se si implementa `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`, il titolo
in-game vive nel catalogo i18n:

```text
title_locale_maps.locales_json[locale].copy["game.title"]
```

Semantica:

- ogni lingua editoriale puo' avere il proprio titolo in-game nel draft;
- il player vede solo il titolo della lingua pubblicata;
- le lingue editoriali ammesse sono `it`, `en`, `de`, `es`;
- la lingua pubblicata puo' essere proiettata in un campo legacy se serve
  compatibilita';
- `title_code`, `game_titles.display_name` e `site_titles.lobby_display_name`
  restano separati.

Raccomandazione:

- non aggiungere `in_game_title` come nuova source of truth se la locale map
  viene implementata subito;
- il backoffice deve esporre un campo esplicito `Titolo in-game` per chiarezza
  editoriale, ma quel campo deve leggere e salvare esclusivamente la key i18n
  `game.title` dentro la locale map del Title;
- `Titolo in-game` e' quindi solo una label/esperienza di editing, non un
  secondo campo persistente e non una seconda source of truth;
- usare `game.title` nel wordmark, nelle aria-label e nei titoli rules dove
  serve il nome del gioco;
- mantenere `in_game_title` come nome concettuale nel backoffice solo se aiuta
  l'operatore, ma salvarlo come key i18n.

## API target legacy

Questa sezione vale solo se il CTO decide di implementare il titolo in-game come
campo separato invece della key i18n `game.title`.

### Admin config

Estendere i payload esistenti:

```text
GET  /api/v1/admin/games/titles/{title_code}/config
PUT  /api/v1/admin/games/titles/{title_code}/config
POST /api/v1/admin/games/titles/{title_code}/config/publish
```

Shape concettuale:

```json
{
  "published": {
    "in_game_title": "Mines"
  },
  "draft": {
    "in_game_title": "Mines Lagoon"
  }
}
```

Il campo vive accanto a `rules_sections` e `ui_labels`, non dentro
`ui_labels`.

### Public runtime config

Estendere:

```text
GET /api/v1/games/mines/config?title_code={title_code}
```

Shape concettuale:

```json
{
  "presentation_config": {
    "in_game_title": "Mines Lagoon"
  }
}
```

Regola:

- il player vede solo published;
- la preview admin continua a usare published finche' non viene progettata una
  preview draft separata.

## Backend implementation plan legacy

Da usare solo se `in_game_title` resta campo separato.

### Slice T1 - Migration

Migration candidata:

```text
backend/migrations/sql/0031__title_in_game_title.sql
```

Schema:

```sql
ALTER TABLE title_configs
    ADD COLUMN IF NOT EXISTS in_game_title varchar(80) NOT NULL DEFAULT 'Mines',
    ADD COLUMN IF NOT EXISTS draft_in_game_title varchar(80) NULL;
```

Possibile check:

```sql
CHECK (char_length(trim(in_game_title)) > 0)
```

Decisione CTO:

- max 60 o 80 caratteri.

### Slice T2 - Service title config

File:

- `backend/app/modules/platform/catalog/title_config_service.py`;
- `backend/app/modules/games/mines/backoffice_config.py`.

Azioni:

1. Caricare `in_game_title` e `draft_in_game_title`.
2. Inserire default `Mines` quando la row config e' creata da zero.
3. Normalizzare il campo in update draft.
4. Pubblicare draft -> published nella stessa transazione del config publish.
5. Includere il campo nell'audit payload come hash o changed field, secondo
   pattern esistente.

Accettazione:

- publish resta atomico;
- nessun drift fra parte generica e Mines-specific;
- master resta read-only per mutation correnti.

### Slice T3 - API models

File:

- `backend/app/api/routes/admin.py`.

Azioni:

1. Estendere `MinesBackofficeConfigRequest` con `in_game_title`.
2. Validare tramite service, non solo Pydantic.
3. Restituire il campo in `get_admin_backoffice_config`.
4. Restituire il campo in `get_public_backoffice_config`.

Accettazione:

- vecchi title senza campo usano fallback;
- PUT con titolo vuoto viene rifiutato;
- GET admin mostra draft/published.

## Frontend implementation plan legacy

Da usare solo se il titolo non viene risolto dal catalogo i18n.

### Slice T4 - Types e runtime consumption

File:

- `frontend/app/lib/types.ts`;
- `frontend/app/ui/mines/mines-standalone.tsx`;
- `frontend/app/ui/mines/mines-stage-header.tsx`.

Azioni:

1. Aggiungere `in_game_title?: string` a `MinesPresentationConfig`.
2. Calcolare `gameTitle = presentation_config.in_game_title ?? "Mines"`.
3. Passare `gameTitle` a `MinesStageHeader`.
4. Renderizzare il titolo con fallback.

Accettazione:

- default resta visivamente `Mines`;
- variante con titolo pubblicato mostra il titolo corretto;
- nessun cambio a launch/session/payout.

### Slice T5 - Backoffice UI

Collocazione:

- detail variante F7-C;
- sezione Overview o Content/Rules;
- non Site/Lobby;
- non Theme.

Azioni:

1. Input `In-game title`.
2. Stato draft/published coerente con save/publish config.
3. Non permettere edit su master.
4. Validazione UI soft, backend autorevole.

Accettazione:

- modifica -> save draft -> publish live;
- reload detail mostra valore salvato;
- player vede il valore solo dopo publish;
- lobby display name resta invariato.

### Slice T6 - CSS e mobile

Problema:

- titoli lunghi possono rompere header/board su mobile.

Azioni:

1. Definire max-width wordmark.
2. Gestire wrap o clamp professionale.
3. Testare viewport 375px.
4. Non scalare font con viewport width.

Accettazione:

- titolo lungo non crea overflow orizzontale;
- payout chips e subtitle restano leggibili;
- desktop e mobile senza overlap.

## Test

Backend:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:56543/casinoking'
python -m pytest tests/integration/test_title_configs_split.py tests/integration/test_mines_backoffice_config.py
python -m pytest tests/integration/test_game_library_publication.py tests/integration/test_platform_catalog_bootstrap.py
```

Test da aggiungere/aggiornare:

- admin GET config espone `in_game_title`;
- PUT draft cambia solo draft;
- publish espone il valore nel public runtime config;
- master mutation resta rifiutata;
- `/games/library` non cambia nome lobby;
- `game_titles.display_name` non cambia;
- title vuoto/troppo lungo rifiutato.

Frontend:

```powershell
cd frontend
npx tsc --noEmit
npm run build
```

Smoke:

1. Crea o usa variante Mines.
2. Apri detail.
3. Imposta `In-game title = Mines Lagoon`.
4. Salva draft.
5. Verifica player non cambia prima del publish.
6. Pubblica live.
7. Apri demo.
8. Verifica wordmark `Mines Lagoon`.
9. Verifica lobby card invariata se `lobby_display_name` non e' cambiato.
10. Verifica mobile 375px.

## Relazione con i18n

Questo piano da solo non introduce multilingua.

Il piano i18n Mines, invece, introduce la locale map e quindi sposta il titolo
in-game in `game.title`.

Fonte attiva:

```text
docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md
```

Regola:

- `game.title` e rules/label dello stesso locale devono essere complete prima
  del publish;
- i body rules dello stesso locale vivono in
  `title_locale_maps.locales_json[locale].rules_sections.*.body_html`;
- `rules_sections_json` resta projection legacy della lingua pubblicata e non
  source editoriale;
- fallback non deve mascherare una lingua pubblicata incompleta;
- il titolo non deve essere hardcoded in `MinesStageHeader`.

## Fuori scope

- cambiare `title_code`;
- rinominare varianti admin;
- modificare lobby display name;
- preview draft;
- CMS;
- i18n foundation;
- theme tokens;
- payout/RTP/RNG/fairness;
- wallet/ledger;
- production/external adapter.

## Decisioni CTO

- Confermato: `game.title` e' la source of truth del titolo in-game quando
  i18n Mines viene implementata.
- Confermato: il backoffice espone il campo `Titolo in-game`, ma lo salva in
  `title_locale_maps.locales_json[locale].copy["game.title"]`; nessuna seconda
  source of truth viene introdotta.
- Projection legacy `in_game_title`: non necessaria come nuova source; ammissibile
  solo come projection della lingua pubblicata se servira' compatibilita'
  futura.
- Confermare max length raccomandata per `game.title`: 60 o 80.
- Confermare master read-only anche per questo contenuto.
- Confermato: player vede solo la lingua pubblicata della locale map.
- Confermato: publish gating su copertura i18n completa.
- Confermato: allowlist editoriale Mines `it`/`en`/`de`/`es`, runtime e config
  pubblicata single-locale, nessun selector o parametro locale player-side.
