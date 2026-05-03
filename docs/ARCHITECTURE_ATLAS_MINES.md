# CasinoKing - Architecture Atlas Mines

Mappa non tecnica del gioco Mines, dei suoi layer e dei riferimenti ai file.

## Scopo

Questo documento serve per orientarsi nel gioco Mines senza dover leggere subito il codice.

Non sostituisce i documenti canonici in `docs/word/` e gli allegati runtime in `docs/runtime/`.
Serve come indice operativo: ogni blocco ha un codice stabile, una spiegazione semplice e i file principali dove cercarlo.

## Come usare i codici

I codici sono intenzionalmente numerati a salti.
Esempio:

- `MINES_FRONTEND_00100` = shell visuale principale del gioco.
- `MINES_ENGINE_00300` = logica server-authoritative della round.
- `MINES_PLATFORM_00500` = confine tra gioco e piattaforma economica.

Per trovare un file:

```powershell
rg -n "start_session|cashout_session|reveal_cell" backend/app/modules/games/mines
rg -n "MinesStandalone|MinesBoard|MinesRulesModal" frontend/app/ui/mines
```

## Vista semplice a livelli

```text
MINES_FRONTEND
  mostra gioco, griglia, bottoni, stato, config
  |
  v
MINES_API
  riceve start, reveal, cashout, session, fairness
  |
  v
MINES_ENGINE
  decide stato round, reveal, win/loss, payout corrente
  |
  v
MINES_RNG_FAIRNESS
  genera board, seed, hash, verifica fairness
  |
  v
MINES_RUNTIME_MATH
  payout runtime, RTP, moltiplicatori supportati
  |
  v
MINES_PLATFORM_BOUNDARY
  apre/chiude round economica verso wallet e ledger
  |
  v
PLATFORM_WALLET_LEDGER
  contabilita', saldo, double-entry, idempotenza
```

## Glossario semplice

| Termine | Significato semplice |
| --- | --- |
| Frontend Mines | La parte che il player vede e clicca. |
| API Mines | Le porte backend chiamate dal frontend. |
| Game engine | Il cervello server-side della partita. |
| RNG | La generazione casuale della board. |
| Fairness | Prove verificabili che la board non e' stata manipolata dopo. |
| Runtime payout | Le tabelle ufficiali usate per calcolare i moltiplicatori. |
| RGS | Concetto di "Remote Game Server": nel repo attuale non e' un servizio separato, ma Mines + API + engine + RNG formano il nucleo RGS concettuale del gioco. |
| Platform boundary | Il punto in cui il gioco chiede alla piattaforma di muovere soldi/chip. |
| Skin | Aspetto visivo: colori, spazi, simboli, densita', tema. |
| Core | Regole, matematica, RNG, stato, payout. |

## Mappa dei blocchi Mines

| Codice | Blocco | Cosa fa | File principali |
| --- | --- | --- | --- |
| `MINES_FRONTEND_00100` | Mines shell player | Schermata giocabile principale: layout, stato UI, orchestration frontend. | `frontend/app/mines/page.tsx`, `frontend/app/ui/mines/mines-standalone.tsx` |
| `MINES_FRONTEND_00110` | Stage header | Titolo, close action, payout preview e stato alto della scena. | `frontend/app/ui/mines/mines-stage-header.tsx`, `frontend/app/ui/mines/mines.css` |
| `MINES_FRONTEND_00120` | Board visuale | Griglia cliccabile e celle visuali. | `frontend/app/ui/mines/mines-board.tsx`, `frontend/app/ui/mines/mines.css` |
| `MINES_FRONTEND_00130` | Azioni player | Pulsanti Bet / Collect e stati busy/disabled. | `frontend/app/ui/mines/mines-action-buttons.tsx`, `frontend/app/ui/mines/mines-standalone.tsx` |
| `MINES_FRONTEND_00140` | Wallet/footer player | Saldo visibile, vincita potenziale, footer responsive. | `frontend/app/ui/mines/mines-balance-footer.tsx`, `frontend/app/ui/mines/mines-standalone.tsx` |
| `MINES_FRONTEND_00145` | Table entry pre-game | Gate real-mode prima del render del gioco: il player sceglie wallet real/bonus e importo da portare al tavolo, oppure torna al sito. | `frontend/app/ui/mines/mines-standalone.tsx`, `frontend/app/ui/mines/mines.css` |
| `MINES_FRONTEND_00150` | Mobile settings | Sheet mobile per configurazione griglia, mine e bet. | `frontend/app/ui/mines/mines-mobile-settings-sheet.tsx` |
| `MINES_FRONTEND_00160` | Rules modal | Modale Game info e payout ladder leggibile. | `frontend/app/ui/mines/mines-rules-modal.tsx` |
| `MINES_FRONTEND_00170` | Mines CSS skin attuale | Stile visivo attuale: colori, spacing, layout, pulsanti. | `frontend/app/ui/mines/mines.css`, `frontend/app/globals.css` |
| `MINES_FRONTEND_00180` | Frontend API client | Wrapper chiamate API e tipi condivisi frontend. | `frontend/app/lib/api.ts`, `frontend/app/lib/types.ts` |
| `MINES_API_00200` | Route API Mines | Endpoint start, reveal, cashout, session e fairness di round; config e fairness current restano pubblici. | `backend/app/api/routes/mines.py` |
| `MINES_API_00210` | Launch token API | Emissione e validazione token di lancio gioco; obbligatorio sugli endpoint operativi Mines nel monolite insieme al bearer player coerente. | `backend/app/api/routes/mines.py`, `backend/app/modules/platform/game_launch/service.py` |
| `MINES_API_00220` | Access session API | Presenza estesa del player nel gioco, ping, timeout e risposta specifica a void operatore. | `backend/app/api/routes/platform_access.py`, `backend/app/modules/platform/access_sessions/service.py` |
| `MINES_ENGINE_00300` | Game service | Start, reveal, cashout, recupero sessione, stato round. | `backend/app/modules/games/mines/service.py` |
| `MINES_ENGINE_00310` | Stato round | Active, won, lost, safe reveals, celle rivelate, payout corrente. | `backend/app/modules/games/mines/service.py`, `backend/migrations/sql/0012__schema_split_platform_rounds.sql` |
| `MINES_ENGINE_00320` | Errori dominio Mines | Errori specifici gioco, conflitti stato, validazione, saldo insufficiente. | `backend/app/modules/games/mines/exceptions.py` |
| `MINES_RNG_00400` | Randomness board | Generazione posizioni mine e materiale RNG. | `backend/app/modules/games/mines/randomness.py` |
| `MINES_FAIRNESS_00410` | Fairness artifacts | Seed hash, board hash, nonce, verifica fairness. | `backend/app/modules/games/mines/fairness.py` |
| `MINES_MATH_00420` | Runtime payout | Moltiplicatori ufficiali da allegati runtime. | `backend/app/modules/games/mines/runtime.py`, `docs/runtime/CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json` |
| `MINES_PLATFORM_00500` | Platform game client + round gateway | Confine game -> platform per apertura e settlement round: `round_gateway.py` resta facciata compatibile, `platform_client.py` contiene il `PlatformGameClient` e l'implementazione in-process. | `backend/app/modules/games/mines/round_gateway.py`, `backend/app/modules/games/mines/platform_client.py` |
| `MINES_PLATFORM_00510` | Platform rounds | Round economica lato piattaforma, wallet, ledger transaction. | `backend/app/modules/platform/rounds/service.py`, `backend/migrations/sql/0012__schema_split_platform_rounds.sql` |
| `MINES_PLATFORM_00520` | Table session boundary | Collegamento tra round Mines, saldo tavolo visibile, budget/perdita massima e force-close void da backoffice. | `backend/app/modules/platform/table_sessions/service.py`, `backend/app/modules/admin/session_force_close.py`, `backend/app/api/routes/platform_table_sessions.py`, `backend/migrations/sql/0020__game_table_sessions.sql`, `backend/migrations/sql/0021__game_table_session_balance.sql`, `backend/migrations/sql/0022__admin_actions_session_void.sql` |
| `MINES_BACKOFFICE_00600` | Config backoffice Mines | Draft/publish config, regole, label, asset, griglie pubblicate. | `backend/app/modules/games/mines/backoffice_config.py`, `frontend/app/ui/mines/mines-backoffice-editor.tsx` |
| `MINES_BACKOFFICE_00610` | Asset simboli board | Safe icon e mine icon configurabili. | `frontend/app/ui/mines/mines-backoffice-editor.tsx`, `backend/migrations/sql/0011__mines_backoffice_draft_publish_assets.sql` |
| `MINES_DATA_00700` | Schema DB Mines | Tabelle `platform_rounds`, `mines_game_rounds`, `game_table_sessions`, access close reason, fairness, config. | `backend/migrations/sql/0007__mines_fairness_seed_internal.sql`, `backend/migrations/sql/0010__mines_backoffice_config.sql`, `backend/migrations/sql/0012__schema_split_platform_rounds.sql`, `backend/migrations/sql/0020__game_table_sessions.sql`, `backend/migrations/sql/0021__game_table_session_balance.sql`, `backend/migrations/sql/0022__admin_actions_session_void.sql` |
| `MINES_TEST_00800` | Test contract/integration | Contratti API, flussi wallet/ledger, concorrenza, browser smoke. | `tests/contract`, `tests/integration`, `tests/concurrency` |

## Macro-cantieri futuri registrati

Questa sezione e' solo orientativa. Non apre implementazione senza istruzioni di dettaglio.

| Cantiere | Stato | Nota |
| --- | --- | --- |
| Aggiustamenti gioco Mines | Pianificato | Usare questo atlas per distinguere sempre CORE, SKIN, API, PLATFORM e BACKOFFICE prima di modificare comportamento o UI. |
| Identificativo spin/round nei report | Pianificato con backoffice/reporting | Mines deve esporre o propagare identificativi coerenti con `platform_rounds`; non inventare display id senza disegno reporting/ledger. |
| External HTTP adapter | Rinviato | Fase 9a in-process e' completata; Fase 9b/c riparte solo quando Michele dira' "voglio pubblicare in produzione". |

## Cosa si riusa per altri giochi simili

Se domani nasce un gioco diverso ma simile a Mines, per esempio un gioco a celle, carte, moltiplicatori o rischio progressivo:

| Da riusare | Perche' |
| --- | --- |
| Launch token e access session | Sono platform, non specifici di Mines. |
| Pattern API start/reveal/cashout | Utile come contratto mentale per giochi request-response. |
| Round gateway | Deve diventare il modello comune game -> platform. |
| Wallet/ledger/platform rounds | Sono il cuore economico comune. |
| Backoffice draft/publish | Utile per config gioco e pubblicazione controllata. |
| Pattern server-authoritative | Il frontend non deve decidere outcome. |
| Fairness/RNG come concetto | Riutilizzabile, anche se ogni gioco puo' avere prove diverse. |
| Componenti visuali di base | Shell, pulsanti, footer saldo, modal, pannelli. |

## Cosa si rifarebbe per altri giochi

| Da rifare | Perche' |
| --- | --- |
| Meccanica di gioco | Ogni gioco ha regole proprie. |
| RTP e payout runtime | Ogni gioco ha matematica propria. |
| Stato tecnico round | Mines usa celle e mine; altri giochi avranno altro stato. |
| Board/area interattiva | La UI centrale cambia con la meccanica. |
| Fairness details | Il principio resta, ma prove e hash possono cambiare. |
| Backoffice specifico | Ogni gioco richiede campi di tuning propri. |

## Versioni grafiche di Mines

Separazione desiderata:

```text
Mines Core
  regole, RNG, payout, stato, fairness

Mines Skin
  colori, simboli, padding, bordi, font, densita', animazioni
```

### Stato attuale

| Area | Stato |
| --- | --- |
| Simboli safe/mine | Gia' configurabili da backoffice. |
| Testi rules/label | Gia' configurabili da backoffice. |
| Griglie/mine pubblicate | Gia' configurabili da backoffice. |
| Colori/padding/layout | Oggi sono soprattutto CSS nel codice. |
| Stili brandizzati/stagionali | Non ancora modellati come tema configurabile. |

### Possibile evoluzione pulita

| Codice futuro | Idea |
| --- | --- |
| `MINES_SKIN_01000` | Theme preset: default, partner, seasonal. |
| `MINES_SKIN_01010` | Design tokens: colori, radius, shadow, spacing. |
| `MINES_SKIN_01020` | Board skin: celle, simboli, animazioni, reveal style. |
| `MINES_SKIN_01030` | Backoffice skin editor: controlli sicuri per colori e padding. |
| `MINES_SKIN_01040` | Skin validation: impedire combinazioni illeggibili o rotte. |

## Come trovare le cose nel codice

```powershell
# Frontend Mines
rg -n "MinesStandalone|MinesBoard|MinesRulesModal|MinesStageHeader" frontend/app/ui/mines

# API Mines
rg -n "@router\\.|start_mines_session|reveal_mines_cell|cashout_mines_session" backend/app/api/routes/mines.py

# Engine backend
rg -n "def start_session|def reveal_cell|def cashout_session" backend/app/modules/games/mines/service.py

# RNG e fairness
rg -n "generate|seed|hash|fairness|nonce" backend/app/modules/games/mines

# Payout runtime
rg -n "get_multiplier|payout|runtime" backend/app/modules/games/mines/runtime.py docs/runtime

# Confine platform/game
rg -n "PlatformGameClient|InProcessPlatformGameClient|open_round|settle_win|settle_loss" backend/app/modules/games/mines/platform_client.py backend/app/modules/games/mines/round_gateway.py
```

## Regola di orientamento

Quando parliamo di Mines, bisogna sempre chiedersi:

```text
Sto parlando di CORE, SKIN, API, PLATFORM o BACKOFFICE?
```

Questa domanda evita di mischiare grafica, matematica, conti, API e configurazione.
