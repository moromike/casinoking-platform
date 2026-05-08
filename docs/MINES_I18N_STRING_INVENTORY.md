# CasinoKing - Mines i18n String Inventory

## Stato

Inventario operativo aggiornato dopo review CTO.

Questo documento accompagna:

- `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`

Obiettivo:

- censire tutte le stringhe player-facing del runtime Mines;
- distinguere copy runtime, copy admin e valori tecnici;
- proporre il namespace delle chiavi i18n;
- rendere verificabile il vincolo: nessuna label player-facing hardcoded nei
  componenti Mines.

## Scope

In scope:

- gioco Mines player;
- launch gate real-mode;
- demo mode UI;
- board labels e aria-label;
- header, payout preview text, balance footer;
- mobile settings;
- rules modal;
- messaggi runtime, errori e overlay;
- copy HTML rules configurabile da backoffice;
- titolo in-game.

Fuori scope in questa fase:

- backoffice platform generale;
- menu admin globali;
- lobby player generale, salvo passaggio futuro del locale al gioco;
- finance/reporting;
- payout runtime, RTP, RNG, wallet, ledger.

## Vincoli CTO recepiti

- allowlist editoriale Mines: `it`, `en`, `de`, `es`;
- lingua pubblicata iniziale raccomandata: `it`;
- una sola lingua pubblicata per gioco/config;
- runtime e config pubblicata restano single-locale;
- nessun selector lingua nel gioco;
- nessun `ck_player_locale`;
- nessun parametro `locale` player-side;
- manifest strict: le key extra sono warning in draft e bloccanti al publish;
- `actions.*` e `board.face.*`: max 32 caratteri;
- `errors.*` brevi: max 80 caratteri;
- `title_locale_maps.locales_json[locale].rules_sections.*.body_html`: soft
  warning a 5KB, senza hard limit iniziale;
- `rules_sections_json` e' solo projection legacy della lingua pubblicata;
- le stringhe IT sono scritte nativamente dall'utente;
- le stringhe EN/DE/ES sono generate con AI e reviewed da umano;
- nessuna traduzione machine-only e' publish-able.

## File analizzati

Frontend player/runtime:

- `frontend/app/ui/mines/mines-standalone.tsx`
- `frontend/app/ui/mines/mines-stage-header.tsx`
- `frontend/app/ui/mines/mines-board.tsx`
- `frontend/app/ui/mines/mines-rules-modal.tsx`
- `frontend/app/ui/mines/mines-balance-footer.tsx`
- `frontend/app/ui/mines/mines-action-buttons.tsx`
- `frontend/app/ui/mines/mines-mobile-settings-sheet.tsx`
- `frontend/app/lib/helpers.ts`
- `frontend/app/lib/types.ts`

Backoffice/config:

- `frontend/app/ui/mines/mines-backoffice-editor.tsx`
- `backend/app/modules/games/mines/backoffice_config.py`
- `backend/app/modules/platform/catalog/title_config_service.py`
- `backend/app/api/routes/admin.py`
- `backend/app/api/routes/mines.py`
- `backend/migrations/sql/0025__title_configs_split.sql`

## Principio di inventario

Una stringa entra nel catalogo se:

- e' visibile al player;
- e' letta da screen reader o aria-label player-facing;
- compare in un dialog, overlay, stato o messaggio;
- compare dentro rules/game info;
- e' un default di contenuto editoriale del gioco.

Una stringa non entra nel catalogo se:

- e' un CSS class name;
- e' un codice tecnico;
- e' un event name;
- e' una enum interna;
- e' una stringa solo admin/backoffice non mostrata al player.

## Inventario player-facing

Stato implementativo aggiornato 2026-05-08:

- manifest frontend/backend creato per le key runtime inventariate, incluse
  `quick_launch.*`;
- default catalog disponibili per `it`, `en`, `de`, `es`;
- il runtime pubblico espone `presentation_config.i18n` da
  `title_locale_maps` o default catalog usando solo la lingua pubblicata della
  config;
- key `language.*`, componenti selector lingua, `ck_player_locale` e parametri
  `locale` player-side restano fuori target e lo scan li blocca nei path
  runtime;
- rules shell, messaggi round, errori/overlay, table entry, balance/footer,
  mobile settings e quick launch passano dal resolver;
- backoffice traduzioni minimo implementato nel detail Mines con lingua
  pubblicata, `Titolo in-game`, copy manifest e rules HTML; publish coverage
  blocking implementato backend-side.

| Area | Oggi | File | Key target |
| --- | --- | --- | --- |
| Titolo frame | `MINES` | `mines-stage-header.tsx` | `game.title` |
| Exit aria | `Exit Mines` | `mines-stage-header.tsx` | `actions.exit_aria` |
| Stato vittoria | `You won {{amount}}...` | `mines-standalone.tsx` | `round.won_notice` |
| Stato perdita | `You hit a mine.` | `mines-standalone.tsx` | `round.lost_notice` |
| Bet | `Bet` / DB `ui_labels` | `mines-standalone.tsx` | `actions.bet` |
| Bet loading | `Betting...` / DB `ui_labels` | backend defaults | `actions.bet_loading` |
| Collect | `Collect` / DB `ui_labels` | `mines-standalone.tsx` | `actions.collect` |
| Collect loading | `Collecting...` / DB `ui_labels` | backend defaults | `actions.collect_loading` |
| Game info aria | `Game info` | `mines-standalone.tsx` | `actions.game_info` |
| Demo badge | `DEMO MODE` | `mines-standalone.tsx`, `mines-mobile-settings-sheet.tsx` | `mode.demo_badge` |
| Grid label | `Grid size` | `mines-standalone.tsx` | `settings.grid_size` |
| Mines label | `Mines` | `mines-standalone.tsx` | `settings.mines` |
| Mine summary | `{{count}} mines` | `mines-standalone.tsx` | `settings.mines_count_label` |
| Bet amount | `Bet amount` | `mines-standalone.tsx` | `settings.bet_amount` |
| Game settings aria/title | `Game settings` | `mines-mobile-settings-sheet.tsx` | `settings.game_settings` |
| Done | `Done` | `mines-mobile-settings-sheet.tsx` | `actions.done` |
| Demo balance | `Demo balance` | `mines-balance-footer.tsx` | `balance.demo` |
| Balance | `Balance` | `mines-balance-footer.tsx` | `balance.default` |
| Balance wallet | `Balance ({{walletType}})` | `mines-balance-footer.tsx` | `balance.wallet` |
| Table balance | `Table balance` | `mines-standalone.tsx` | `balance.table` |
| Win | `Win` | `mines-balance-footer.tsx` | `balance.win` |
| Chip suffix | `CHIP` | `helpers.ts` | `currency.chip_suffix` |
| Cell aria mine | `Cell {{cell}}, mine` | `mines-board.tsx` | `board.aria.mine` |
| Cell aria safe | `Cell {{cell}}, safe` | `mines-board.tsx` | `board.aria.safe` |
| Cell aria hidden | `Cell {{cell}}, hidden` | `mines-board.tsx` | `board.aria.hidden` |
| Cell face mine | `MINE` | `mines-board.tsx` | `board.face.mine` |
| Cell face safe | `SAFE` | `mines-board.tsx` | `board.face.safe` |
| Cell face hidden | `PICK` | `mines-board.tsx` | `board.face.hidden` |
| Rules aria | `Game info Mines` | `mines-rules-modal.tsx` | `rules.dialog_aria` |
| Rules title | `GAME INFO - MINES` | `mines-rules-modal.tsx` | `rules.header_title` |
| Rules intro | `Rules readable...` | `mines-rules-modal.tsx` | `rules.intro` |
| Rules section title | `Ways to win` | `mines-rules-modal.tsx` | `rules.ways_to_win` |
| Rules section body | HTML da locale map, proiettato legacy nella lingua pubblicata | `title_locale_maps.locales_json[locale].rules_sections.*.body_html`; legacy `title_configs.rules_sections_json` | `rules_sections.ways_to_win.body_html` |
| Rules payout title | `Payout display` | `mines-rules-modal.tsx` | `rules.payout_display` |
| Safe reveal row | `Safe reveal {{index}}` | `mines-rules-modal.tsx` | `rules.safe_reveal` |
| Settings section title | `Settings menu` | `mines-rules-modal.tsx` | `rules.settings_menu` |
| Bet collect title | `Bet & collect` | `mines-rules-modal.tsx` | `rules.bet_collect` |
| Error dialog title | `Action needed` | `mines-standalone.tsx` | `errors.action_needed` |
| Error OK | `OK` | `mines-standalone.tsx` | `actions.ok` |
| Auth expired | `Your sign-in session...` | `mines-standalone.tsx` | `errors.auth_invalid` |
| Session closed title | `Session closed` | `mines-standalone.tsx` | `runtime.session_closed_title` |
| Session closed text | `This game session was closed...` | `mines-standalone.tsx` | `runtime.session_closed_text` |
| Reload required title | `Reload required` | `mines-standalone.tsx` | `runtime.reload_required_title` |
| Reload required text | `The game session is no longer...` | `mines-standalone.tsx` | `runtime.reload_required_text` |
| Demo closed | `Demo session closed...` | `mines-standalone.tsx` | `runtime.demo_closed_text` |
| Restoring hand title | `Restoring hand` | `mines-standalone.tsx` | `runtime.restoring_title` |
| Restoring hand text | `We are syncing...` | `mines-standalone.tsx` | `runtime.restoring_text` |
| Session expired title | `Session expired` | `mines-standalone.tsx` | `runtime.session_expired_title` |
| Session expired text | `The inactive session expired...` | `mines-standalone.tsx` | `runtime.session_expired_text` |
| Session expiring title | `Session expiring` | `mines-standalone.tsx` | `runtime.session_expiring_title` |
| Session expiring text | `This inactive session is expiring...` | `mines-standalone.tsx` | `runtime.session_expiring_text` |
| Network suffix | `Could not reach the server...` | `mines-standalone.tsx` | `errors.network_suffix` |
| Back to site aria | `Back to site` | `mines-standalone.tsx` | `actions.back_to_site_aria` |
| Launch eyebrow | `Mines` | `mines-standalone.tsx` | `game.title` |
| Table entry title | `Choose your table balance` | `mines-standalone.tsx` | `launch.choose_table_balance` |
| Balance source aria | `Balance source` | `mines-standalone.tsx` | `launch.balance_source_aria` |
| Real money | `Real money` | `mines-standalone.tsx` | `launch.real_money` |
| Bonus | `Bonus` | `mines-standalone.tsx` | `launch.bonus` |
| Available balance | `Available balance` | `mines-standalone.tsx` | `launch.available_balance` |
| Maximum | `Maximum` | `mines-standalone.tsx` | `launch.maximum` |
| Table entry amount | `Table entry amount` | `mines-standalone.tsx` | `launch.table_entry_amount` |
| Enter game | `Enter game` | `mines-standalone.tsx` | `launch.enter_game` |
| Entering | `Entering...` | `mines-standalone.tsx` | `launch.entering` |
| Grid cells label | `{{count}} cells` | `helpers.ts` | `format.cells` |
| Quick start | `Quick start` | `helpers.ts` | `quick_launch.quick_start.label` |
| Quick start desc | `Low-friction entry...` | `helpers.ts` | `quick_launch.quick_start.description` |
| Standard table | `Standard table` | `helpers.ts` | `quick_launch.standard_table.label` |
| Standard table desc | `Balanced setup...` | `helpers.ts` | `quick_launch.standard_table.description` |
| High volatility | `High volatility` | `helpers.ts` | `quick_launch.high_volatility.label` |
| High volatility desc | `Higher risk preset...` | `helpers.ts` | `quick_launch.high_volatility.description` |

## Backoffice strings

Il backoffice contiene molte stringhe hardcoded in italiano e inglese dentro:

- `frontend/app/ui/mines/mines-backoffice-editor.tsx`
- `frontend/app/ui/mines/mines-grid-config-editor.tsx`
- `frontend/app/ui/mines/mines-theme-editor.tsx`

Per questo piano non diventano runtime i18n del gioco.

Regola:

- le label dell'editor traduzioni sono UI platform/admin;
- il backoffice resta IT-only per questo epic anche se l'editor gestisce
  contenuti Mines `it`/`en`/`de`/`es`;
- il backoffice e' escluso dallo scan statico `lint:i18n` di I18N-8, perche'
  quel gate riguarda solo copy player-facing del runtime Mines;
- l'editor deve mostrare all'operatore un campo esplicito `Titolo in-game`;
- quel campo e' una label admin e deve leggere/scrivere la key player-facing
  `game.title` nella locale selezionata, senza creare un campo persistente
  separato o una seconda source of truth;
- possono restare nel cantiere product copy/backoffice;
- non devono essere salvate nel catalogo i18n del player;
- non devono contaminare `theme_tokens_json`.

## Namespace proposto

```text
game.*
mode.*
actions.*
settings.*
balance.*
currency.*
board.*
rules.*
errors.*
runtime.*
launch.*
format.*
quick_launch.*
```

## Placeholder ammessi

| Placeholder | Uso |
| --- | --- |
| `{{amount}}` | Importi gia' formattati dal codice. |
| `{{seconds}}` | Countdown sessione. |
| `{{cell}}` | Numero cella visibile. |
| `{{count}}` | Conteggi generici. |
| `{{index}}` | Progressivo safe reveal. |
| `{{walletType}}` | Nome wallet gia' risolto/localizzato. |
| `{{gameTitle}}` | Titolo del gioco risolto dal catalogo. |
| `{{fallback}}` | Prefisso/suffisso errore tecnico gia' localizzato. |

Regole:

- ogni key dichiara la lista placeholder ammessi;
- il backend blocca publish se una traduzione contiene placeholder ignoti;
- il backend blocca publish se mancano placeholder obbligatori;
- HTML e' ammesso solo nei body rules.

## Criteri di completezza

Un locale pubblicabile e' completo se:

- e' la lingua pubblicata scelta per la config;
- tutte le chiavi required esistono in quella lingua;
- nessuna stringa required e' vuota;
- i placeholder combaciano con il manifest;
- i body HTML rules passano sanitizzazione;
- le label con max length non superano il limite;
- il frontend non dipende da fallback o da lingua scelta dal player;
- smoke desktop e mobile non mostrano overflow evidente.
- gli smoke cross-language coprono `it`/`en`/`de`/`es` pubblicando una lingua
  alla volta su config di test, senza selector player.

## Scan da eseguire in implementation

Implementazione I18N-8:

- aggiungere in `frontend` lo script npm `lint:i18n`;
- usare una scan mirata dei file runtime Mines, non dell'intero backoffice;
- divieto di literal string JSX player-facing nei file runtime scansionati;
- allowlist esplicita per icone, codici tecnici, enum, classi e test fixture;
- output bloccante, non warning silenzioso.
- backoffice escluso per questo epic: resta IT-only e le sue label non entrano
  nel catalogo i18n player.

File target iniziali:

```text
frontend/app/ui/mines/mines-standalone.tsx
frontend/app/ui/mines/mines-stage-header.tsx
frontend/app/ui/mines/mines-board.tsx
frontend/app/ui/mines/mines-rules-modal.tsx
frontend/app/ui/mines/mines-balance-footer.tsx
frontend/app/ui/mines/mines-action-buttons.tsx
frontend/app/ui/mines/mines-mobile-settings-sheet.tsx
frontend/app/lib/helpers.ts
```

```powershell
rg -n "You won|You hit|Game info|DEMO MODE|Grid size|Bet amount|Action needed|Choose your table balance|Real money|Bonus|Available balance|Maximum|Enter game|Session expired|MINE|SAFE|PICK|Demo balance|Win" frontend/app/ui/mines frontend/app/lib/helpers.ts
rg -n "aria-label=|placeholder=|>[^<>{}]*[A-Za-z][^<>{}]*<" frontend/app/ui/mines
```

Accettazione:

- dopo la migrazione i match player-facing residui devono essere giustificati
  come valori tecnici, enum, classi, numeri o test.
- `npm run lint:i18n` deve fallire con exit non-zero se trova match non
  allowlisted nei file runtime Mines.
