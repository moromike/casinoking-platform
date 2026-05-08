# CasinoKing - Mines Copy, Labels and i18n Readiness Plan

## Stato

Documento di transizione.

La versione precedente di questo piano proponeva un modello single-language
semplice per configurazione/Title. La decisione prodotto successiva ha confermato
la lingua pubblicata unica, ma con foundation i18n reale:

```text
Mines deve avere una i18n foundation reale.
Le label player-facing non devono restare hardcoded nei componenti.
Una sola lingua e' pubblicata per gioco/config.
Il player non seleziona la lingua in runtime.
```

Il piano operativo attivo e' ora:

- `docs/MINES_I18N_CTO_REVIEW_BRIEF.md`
- `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`
- `docs/MINES_I18N_STRING_INVENTORY.md`

Questo documento resta come ponte per spiegare cosa viene superato e cosa resta
valido.

Aggiornamento post review CTO:

- epic Mines i18n approvato;
- lingua pubblicata iniziale raccomandata `it`;
- allowlist editoriale Mines `it`, `en`, `de`, `es`;
- runtime e config pubblicata restano single-locale;
- nessun selector lingua nel gioco;
- nessun `ck_player_locale`;
- nessun parametro `locale` player-side;
- key extra fuori manifest: warning in draft, bloccante al publish;
- `ui_labels_json` resta projection legacy, non source of truth player dopo
  migrazione i18n;
- `rules_sections_json` resta projection legacy della lingua pubblicata; i body
  rules localizzati vivono in
  `title_locale_maps.locales_json[locale].rules_sections.*.body_html`;
- F7-C chiuso prima di I18N-1.

## Cosa resta vero

- Oggi il codice non ha ancora una i18n foundation runtime completa.
- Oggi `title_configs.rules_sections_json` e `title_configs.ui_labels_json`
  sono la presentation config Title-level esistente.
- Oggi molte stringhe Mines player-facing sono ancora hardcoded.
- Theme non deve contenere copy.
- Payout, RTP, RNG, wallet e ledger non devono essere toccati dal cantiere copy.
- Il backoffice deve distinguere:
  - nome variante admin;
  - nome lobby;
  - `title_code`;
  - titolo in-game;
  - label/runtime copy.

## Cosa viene superato

Non e' piu' target finale:

- `content_language_code` come soluzione sufficiente;
- selector lingua in-game;
- `ck_player_locale`;
- `?locale` o parametri locale player-side;
- resolver single-language con override parziali.

La nuova direzione e':

```text
title_locale_maps
  -> locale map versionata per Title
  -> una sola lingua pubblicata per config
  -> completeness gate
  -> resolver frontend Mines
```

## Relazione con i campi esistenti

Durante la migrazione:

- `rules_sections_json` resta compatibility projection della lingua pubblicata;
- `ui_labels_json` resta compatibility projection delle action label legacy;
- il nuovo source of truth editoriale diventa la locale map versionata;
- i body rules sono localizzati in
  `title_locale_maps.locales_json[locale].rules_sections.*.body_html`;
- il public runtime espone `presentation_config.i18n`;
- il frontend Mines deve leggere dal resolver, non da stringhe inline.
- dopo la migrazione i18n, il frontend player non legge `ui_labels_json` come
  source of truth.

## Documenti da usare

Per implementare il cantiere:

1. `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`
2. `docs/MINES_I18N_STRING_INVENTORY.md`
3. `docs/MINES_I18N_CTO_REVIEW_BRIEF.md`
4. `docs/F7_C_GAMES_DETAIL_ROUTE_REFACTOR_PLAN.md`
5. `docs/MINES_IN_GAME_TITLE_PLAN.md`
6. `docs/ARCHITECTURE_ATLAS_MINES.md`
7. `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`

## Regole operative

- Non aggiungere nuove label hardcoded player-facing.
- Non promettere in backoffice label che il player non usa.
- Non usare fallback come modo normale per pubblicare locale incomplete.
- Non salvare HTML fuori dai body rules.
- Non mettere copy in `theme_tokens_json`.
- Non localizzare wallet/ledger/reporting dentro questo cantiere.
- Non cambiare gameplay endpoint per cambiare lingua.
- Non introdurre selector lingua nel runtime Mines.
- Non leggere o scrivere `ck_player_locale`.
- Non usare parametri `locale` player-side per risolvere copy.
- Non partire con I18N-1 prima di chiudere F7-C.

## Verifiche minime future

Frontend:

```powershell
cd frontend
npx tsc --noEmit
npm run build
```

Backend:

```powershell
$env:DATABASE_URL='postgresql://casinoking:casinoking@localhost:56543/casinoking'
python -m pytest tests/integration/test_title_configs_split.py tests/integration/test_mines_backoffice_config.py
python -m pytest tests/contract/test_mines_runtime_contract.py tests/integration/test_game_library_publication.py
```

Scan copy:

```powershell
rg -n "You won|You hit|Game info|DEMO MODE|Grid size|Bet amount|Action needed|Choose your table balance|Real money|Bonus|Available balance|Maximum|Enter game|Session expired|MINE|SAFE|PICK|Demo balance|Win" frontend/app/ui/mines frontend/app/lib/helpers.ts
```

I match residui dopo implementation devono essere giustificati come valori
tecnici, test, enum, classi CSS o copy admin non player-facing.
