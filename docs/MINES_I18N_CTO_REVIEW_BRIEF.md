Status: COMPLETED
Last meaningful update: 2026-05-08

# CasinoKing - Mines i18n CTO Review Brief

## Stato

Brief per revisione CTO.

Aggiornamento post review CTO 2026-05-07:

- verdict CTO: epic approvato con caveat tecnici;
- nessun punto del feedback CTO viene rifiutato;
- le decisioni aperte sono chiuse in questo documento;
- F7-C resta prerequisito prima di iniziare I18N-1;
- lo smoke cross-language resta a fine I18N-7 e avviene pubblicando config di
  test con lingue diverse, non via selector player.

Aggiornamento decisione definitiva 2026-05-08:

- una sola lingua pubblicata per gioco/config Mines;
- allowlist editoriale Mines: `it`, `en`, `de`, `es`;
- nessun selector lingua nel gioco;
- nessun `ck_player_locale`;
- nessun parametro `locale` player-side;
- runtime e config pubblicata restano single-locale;
- il backoffice resta IT-only in questo epic;
- l'editor contenuti Mines i18n e la scelta della lingua pubblicata restano
  parte del cantiere Mines.

Documenti tecnici di dettaglio:

- `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`
- `docs/MINES_I18N_STRING_INVENTORY.md`
- `docs/MINES_COPY_LABELS_AND_I18N_READINESS_PLAN.md`
- `docs/MINES_IN_GAME_TITLE_PLAN.md`
- `docs/F7_C_GAMES_DETAIL_ROUTE_REFACTOR_PLAN.md`

## Decisione recepita

Il CTO ha validato l'apertura del cantiere:

```text
Mines i18n foundation
```

Target:

- niente label player-facing hardcoded nel runtime Mines;
- locale map versionata per Title;
- lingua pubblicata controllata per config;
- resolver frontend Mines;
- editor traduzioni nel detail Title;
- coverage report;
- publish gating backend;
- smoke desktop/mobile sulla lingua pubblicata; smoke cross-language possibile
  solo pubblicando config di test con lingua diversa, non via selector player.

## Verdetto CTO recepito

Verdetto:

```text
Approvato.
```

Condizioni recepite:

- risposte CTO integrate nel brief e nel piano implementativo;
- 3 caveat tecnici aggiunti prima dell'implementazione;
- F7-C chiuso prima di I18N-1;
- ogni slice I18N-* ha test/smoke locali;
- smoke cross-language solo a fine I18N-7, tramite publish di config test con
  lingua diversa.

Motivo del pivot:

- il decision record precedente rinviava la i18n fino alla seconda lingua reale;
- il supporto editoriale `it`/`en`/`de`/`es` soddisfa il trigger per Mines;
- il pivot e' limitato al runtime player-facing Mines, non alla platform
  globale.

## Raccomandazione tecnica

Usare una tabella separata Title-level:

```text
title_locale_maps
```

Non mettere la locale map in:

- `mines_title_configs`;
- `theme_tokens_json`;
- `site_titles`;
- wallet/ledger/reporting.

Motivo:

- i contenuti localizzati sono Title-level;
- non sono matematica di gioco;
- non sono theme;
- non sono Site/Lobby;
- devono essere versionati e publish-gated.

## Impatto runtime

Il public config Mines espone il bundle della lingua pubblicata:

```text
GET /games/mines/config?title_code={title_code}
```

Il payload espone:

```text
presentation_config.i18n
```

Il frontend usa solo:

```text
useMinesCopy(...)
copy.t("actions.bet")
copy.t("round.won_notice", { amount })
copy.rulesSection("ways_to_win")
```

Regola:

- il player non cambia lingua dal gioco;
- start/reveal/cashout non ricevono parametri lingua;
- il backend risolve sempre dalla lingua pubblicata della config;
- fallback non deve nascondere una lingua pubblicata incompleta.

## Impatto backoffice

Nel detail route F7-C:

```text
/admin/games/[engine]/titles/[title_code]
```

aggiungere tab:

```text
Translations
```

Funzioni:

- lingua pubblicata per la config;
- add locale da allowlist editoriale `it`/`en`/`de`/`es`;
- editor key/value;
- editor rules HTML;
- coverage per locale;
- save draft;
- publish live con gate backend.

Nota di scope:

- la UI backoffice resta IT-only in questo epic;
- la i18n platform-wide resta un cantiere separato futuro;
- il tab `Translations` gestisce contenuto player-facing, non traduce il
  backoffice stesso.

## Titolo in-game

Con i18n Mines, il titolo in-game non deve diventare una source of truth
separata.

Usare:

```text
game.title
```

Separati e invariati:

- `title_code`;
- `game_titles.display_name`;
- `site_titles.lobby_display_name`;
- `site_titles.lobby_description`.

## Gating backend

Publish fallisce se:

- lingua pubblicata assente dal draft;
- lingua pubblicata fuori allowlist;
- key extra fuori manifest presente al publish;
- key required mancante;
- placeholder obbligatorio mancante;
- placeholder ignoto presente;
- HTML fuori rules body;
- rules HTML non sanitizzato;
- label corta oltre il limite hard;
- master Title mutato;
- publish concorrente crea due current maps.

In draft:

- key extra fuori manifest produce warning;
- al publish diventa bloccante.

Limiti iniziali:

- `actions.*`: 32 caratteri;
- `board.face.*`: 32 caratteri;
- `errors.*` brevi: 80 caratteri;
- `title_locale_maps.locales_json[locale].rules_sections.*.body_html`: nessun
  hard limit iniziale, soft warning a 5KB;
- `title_configs.rules_sections_json` / `rules_sections_json` e' solo
  projection legacy della lingua pubblicata.

## Test minimi

Backend:

```powershell
python -m pytest tests/integration/test_title_configs_split.py tests/integration/test_mines_backoffice_config.py
python -m pytest tests/contract/test_mines_runtime_contract.py tests/integration/test_game_library_publication.py
```

Frontend:

```powershell
cd frontend
npx tsc --noEmit
npm run build
```

Smoke:

- Mines demo con lingua pubblicata `it`;
- config di test pubblicata con lingua `en`, `de` o `es`, senza selector
  player;
- rules modal;
- error dialog;
- board aria/labels;
- mobile 375px;
- label lunghe.

Nota:

- questi smoke completi si eseguono a fine I18N-7;
- prima di allora ogni slice I18N-* deve avere test/smoke locali coerenti con
  il suo perimetro.

## Decisioni CTO chiuse

1. `title_locale_maps`: confermato.
2. Allowlist editoriale Mines: `it`, `en`, `de`, `es`.
3. Lingua pubblicata iniziale raccomandata: `it`, per mercato primario.
4. Una sola lingua pubblicata per gioco/config.
5. Nessun selector lingua nel gioco.
6. Nessuna persistenza `ck_player_locale`.
7. Nessun parametro `locale` player-side.
8. Se la lingua pubblicata non ha una key required: log, render key letterale,
   bug interno bloccato dal publish gate.
9. Cambio lingua solo via backoffice publish della config.
10. `game.title`: source of truth del titolo in-game.
11. `game_titles.display_name`: resta backoffice/lobby catalog, non titolo
    runtime.
12. Key extra: strict mode.
13. Extra key in draft: warning.
14. Extra key al publish: bloccante.
15. Max length iniziali: 32 per `actions.*` e `board.face.*`, 80 per
    `errors.*` brevi, soft warning 5KB per body HTML rules.
16. i18n globale platform: rinviata.
17. Backoffice UI: resta IT-only in questo epic.
18. Runtime e config pubblicata: restano single-locale; il player vede solo la
    lingua pubblicata.
19. Rules body: source editoriale in
    `title_locale_maps.locales_json[locale].rules_sections.*.body_html`;
    `rules_sections_json` resta projection legacy della lingua pubblicata.

## Caveat tecnici obbligatori

### 1. Content Production

Il piano deve distinguere tooling da contenuto:

- stringhe EN generate con AI, poi reviewed dall'utente;
- stringhe IT scritte nativamente dall'utente;
- Translation QA con human read-through;
- nessuna traduzione machine-only puo' essere pubblicabile.

### 2. Static Scan Implementation

Implementazione preferita:

- ESLint custom rule su `frontend/app/ui/mines/**`;
- vieta literal string in JSX text player-facing;
- allowlist per icone, codici tecnici, enum, classi, test fixture;
- output bloccante in build/lint.

Fallback accettabile:

- script `lint:i18n` con scan regex dedicato;
- exit code non-zero se trova violazioni non allowlisted.

La scansione non deve essere warning silenzioso.

### 3. Backward Compatibility `ui_labels_json`

Decisione: Opzione A.

- `title_configs.ui_labels_json` resta nello schema per backward
  compatibility;
- dopo i18n il frontend player non lo legge piu' come source of truth;
- il public runtime preferisce `presentation_config.i18n` quando presente;
- `ui_labels_json` puo' restare projection legacy della lingua pubblicata;
- niente drop colonna in questo epic;
- evitare coesistenza paritaria con due source of truth.

## Sequenza integrata

Ordine macro confermato:

1. Smoke E2E.
2. Master launch legacy removal.
3. Site compact + Player lobby QA, mergeable se piccoli.
4. F7-C deep refactor + route dedicate.
5. Mines i18n foundation epic: I18N-1 ... I18N-8.

Regola:

- F7-C e' cantiere unico, completato una volta sola;
- F7-C e' prerequisito sia per Games overview Slice 3+ sia per i18n;
- i18n non sale sopra smoke/master/site/player;
- I18N-1 parte solo dopo chiusura F7-C.

## Rischio principale

Il rischio non e' tecnico puro: e' creare una falsa i18n.

Contromisura:

- manifest completo;
- inventario stringhe;
- resolver obbligatorio;
- scan hardcoded labels;
- publish gate backend;
- QA umano sulle traduzioni.
