Status: ACTIVE
Last meaningful update: 2026-05-21

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
rg -n "MinesStandalone|MinesGameplay|MinesBoard|MinesRulesModal" frontend-v3/app/ui/mines
rg -n "GameBootShell|GameBootDecisionFlow|useGameLaunchContext|useGameAudioPreferences" frontend-v3/app/ui/game-runtime
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
| GameBootShell | Shell frontend comune che monta theme, gate, intro, how-to-play, overlay runtime e gameplay quando il boot e' pronto. |
| MinesStandalone | Wrapper stabile della route Mines: orchestra boot, token/sessioni, runtime config e passa il controllo a `MinesGameplay`. |
| MinesGameplay | Gameplay Mines isolato: board, azioni, replay, effetti, ladder e bridge audio Mines-specific. |

## Mappa dei blocchi Mines

| Codice | Blocco | Cosa fa | File principali |
| --- | --- | --- | --- |
| `MINES_FRONTEND_00100` | Mines standalone wrapper | Export stabile del runtime interno `/runtime/mines`: legge boot context comune, orchestra token/sessioni/config/runtime Mines-specific e monta `GameBootShell` + `MinesGameplay`. La route pubblica `/mines` resta shell Site V3 e monta questo runtime in iframe; la route diretta V1 `/mines` reindirizza a Site V3. Il wrapper passa booleans, contenuti e callback al decision flow comune, ma contiene ancora orchestration API/session/token/config specifica Mines; non e' una shell generica da copiare per altri giochi. | `frontend-v3/app/mines/page.tsx`, `frontend-v3/app/runtime/mines/page.tsx`, `frontend-v3/app/ui/mines/mines-standalone.tsx`, `frontend-v3/app/ui/game-runtime/game-boot-shell.tsx`, `frontend-v3/app/ui/game-runtime/game-boot-decision-flow.tsx`, `frontend-v3/app/ui/game-runtime/use-game-launch-context.ts`, `frontend/app/mines/page.tsx`, `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md` |
| `MINES_FRONTEND_00105` | Mines gameplay isolato | Gameplay Mines estratto dal wrapper: board, controlli, reveal/cashout, replay, latest sessions, payout ladder, effetti e bridge audio verso `useMinesSounds`. Consuma primitive control-rail condivise da `game-runtime/`; non importa `@/app/lib/api`. | `frontend-v3/app/ui/mines/mines-gameplay.tsx`, `frontend-v3/app/ui/mines/types.ts`, `frontend-v3/app/ui/mines/mines-board.tsx`, `frontend-v3/app/ui/game-runtime/game-control-rail.tsx`, `frontend-v3/app/ui/game-runtime/game-bet-panel.tsx`, `frontend-v3/app/ui/game-runtime/game-action-buttons.tsx`, `frontend-v3/app/ui/game-runtime/game-balance-footer.tsx`, `frontend-v3/app/ui/mines/mines-replay-viewer.tsx`, `frontend-v3/app/ui/mines/use-mines-sounds.ts` |
| `MINES_FRONTEND_00110` | Stage header | Titolo, close action, payout preview e stato alto della scena. | `frontend-v3/app/ui/mines/mines-stage-header.tsx`, `frontend-v3/app/ui/mines/mines.css` |
| `MINES_FRONTEND_00120` | Board visuale | Griglia cliccabile e celle visuali. | `frontend-v3/app/ui/mines/mines-board.tsx`, `frontend-v3/app/ui/mines/mines.css` |
| `MINES_FRONTEND_00130` | Azioni player | Pulsanti Bet / Collect e stati busy/disabled dentro il gameplay Mines, tramite primitive shared. | `frontend-v3/app/ui/game-runtime/game-action-buttons.tsx`, `frontend-v3/app/ui/mines/mines-gameplay.tsx` |
| `MINES_FRONTEND_00140` | Wallet/footer player | Saldo visibile, vincita potenziale, footer responsive dentro il gameplay Mines, tramite primitive shared. | `frontend-v3/app/ui/game-runtime/game-balance-footer.tsx`, `frontend-v3/app/ui/mines/mines-gameplay.tsx` |
| `MINES_FRONTEND_00145` | Table entry pre-game | Gate real-mode prima del render del gioco: il player sceglie wallet real/bonus e importo da portare al tavolo; il frontend propaga il `title_code` dell'URL a access session, table session e launch token. La shell visuale vive in `game-runtime`, mentre `MinesStandalone` conserva la callback table-session Mines. | `frontend-v3/app/ui/mines/mines-standalone.tsx`, `frontend-v3/app/ui/game-runtime/game-table-balance-gate.tsx`, `frontend-v3/app/ui/game-runtime/game-runtime.css` |
| `MINES_FRONTEND_00150` | Mobile settings | Sheet mobile e stack controlli per configurazione griglia, mine e bet, tramite primitive shared con classi Mines legacy aliasate. | `frontend-v3/app/ui/game-runtime/game-mobile-settings-sheet.tsx`, `frontend-v3/app/ui/game-runtime/game-mobile-control-stack.tsx`, `frontend-v3/app/ui/mines/mines-gameplay.tsx` |
| `MINES_FRONTEND_00160` | Rules modal | Modale Game info e payout ladder leggibile. Il contenuto Mines resta in `mines-rules-modal.tsx`, mentre shell dialog/tab/close vive nel runtime condiviso `GameInfoRulesModal`; classi e output visuale Mines sono preservati. | `frontend-v3/app/ui/mines/mines-rules-modal.tsx`, `frontend-v3/app/ui/game-runtime/game-info-rules-modal.tsx` |
| `MINES_FRONTEND_00170` | Mines CSS skin attuale | Stile visivo attuale: colori, spacing, layout, pulsanti. | `frontend-v3/app/ui/mines/mines.css`, `frontend-v3/app/globals.css` |
| `MINES_FRONTEND_00180` | Frontend API client | Wrapper chiamate API e tipi condivisi frontend. | `frontend-v3/app/lib/api.ts`, `frontend-v3/app/lib/types.ts` |
| `MINES_FRONTEND_00190` | Effetti visuali Mines | VF-1/VF-2 implementate: sparkle safe reveal, pulse mine hit e confetti win/cashout client-side, con `prefers-reduced-motion` e senza cambiare outcome, RNG, payout o settlement. VF-3 asset-based rinviata. Dopo BOOT-2A.4b gli effetti vivono nel gameplay Mines. | `frontend-v3/app/ui/mines/mines-win-celebration.tsx`, `frontend-v3/app/ui/mines/mines-board.tsx`, `frontend-v3/app/ui/mines/mines-gameplay.tsx`, `frontend-v3/app/ui/mines/mines.css`, `docs/MINES_VISUAL_EFFECTS_PLAN.md` |
| `MINES_FRONTEND_00195` | Mines replay viewer | Viewer read-only riusabile per rivedere una mano Mines da Storico gioco, runtime gioco e superfici backoffice di supporto: usa `MinesBoard`, mostra solo fotografia finale/esito/mine/diamanti scoperti e non decide outcome. Nel runtime vive nella modal Game info/Regole come tab `REPLAY`, non sotto il board, e per player autenticato carica le ultime 3 access session del Title corrente. Dopo BOOT-2A.4b e' montato dal gameplay Mines, non dal wrapper boot. Usa skin base semplificata, non asset custom del Title. La copy condivisa vive accanto al viewer per evitare divergenze tra superfici. | `frontend-v3/app/ui/mines/mines-replay-viewer.tsx`, `frontend-v3/app/ui/mines/mines-replay-copy.ts`, `frontend-v3/app/ui/mines/mines-gameplay.tsx`, `frontend-v3/app/ui/mines/mines-rules-modal.tsx`, `frontend/app/ui/player-account-page.tsx`, `docs/MINES_REPLAY_VIEWER_PLAN.md` |
| `MINES_FRONTEND_00197` | Provider bootstrap e runtime tools | BOOT-2A shell refactor completato: `GameBootShell`, `GameBootDecisionFlow` e helper `game-runtime/` gestiscono theme shell, audio preferences, table gate, intro, how-to-play, overlay runtime e mount del gameplay. BOOT-2B/3/4/5 V1 implementati: real mode mostra prima il Table Balance Gate con form/CSS condivisi in `game-runtime` e callback table-session Mines, pre-carica intro media, poi intro provider `moromike lab` MP4 8s con poster/progress bar condiviso in `game-runtime`, How To Play Gate i18n con layout/CSS condivisi in `game-runtime`, clock runtime compatto Europe/Rome e controlli FX mute/volume. Restano pianificati: ottimizzazione video mobile, Site config per clock e backoffice copy/clock gate. Implementato anche reveal mine dopo cashout/auto-win quando il round e' chiuso. Il layer e' frontend/runtime, non core: non tocca RNG, payout, wallet, ledger o fairness. | `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`, `docs/MINES_PROVIDER_BOOTSTRAP_UX_PLAN.md`, `docs/MINES_SOUND_ASSETS_PLAN.md`, `frontend-v3/app/ui/game-runtime/game-boot-shell.tsx`, `frontend-v3/app/ui/game-runtime/game-boot-decision-flow.tsx`, `frontend-v3/app/ui/game-runtime/game-provider-bootstrap.tsx`, `frontend-v3/app/ui/game-runtime/game-how-to-play-gate.tsx`, `frontend-v3/app/ui/game-runtime/game-table-balance-gate.tsx`, `frontend-v3/app/ui/game-runtime/use-game-launch-context.ts`, `frontend-v3/app/ui/game-runtime/use-game-audio-preferences.ts`, `frontend-v3/app/ui/mines/mines-how-to-play-visual.tsx`, `frontend-v3/app/ui/mines/mines-runtime-tools.tsx`, `frontend-v3/app/ui/mines/use-mines-sounds.ts`, `frontend-v3/app/ui/mines/mines-standalone.tsx`, `frontend-v3/public/brand/moromike-lab/` |
| `MINES_API_00200` | Route API Mines | Endpoint start, reveal, cashout, session e fairness di round; config e fairness current restano pubblici. La lista player `/games/mines/sessions` supporta `limit` e cursor per lo Storico gioco account. | `backend/app/api/routes/mines.py`, `tests/integration/test_mines_session_history_pagination.py` |
| `MINES_API_00210` | Launch token API | Emissione e validazione token di lancio gioco; il token trasporta `game_code`, `title_code`, `site_code`, `mode` e supporta `real` e `demo` con ownership diversa. Il launch pubblico richiede sempre un `title_code` esplicito, rifiuta i Title master con codice stabile `LAUNCH_REJECTED_MASTER` e rispetta `lobby_visibility`, `demo_enabled` e `real_enabled`; il backoffice usa un token preview admin firmato per aprire master o varianti nascoste in demo senza pubblicarle in lobby. Il frontend Mines legge `title_code` e, se presente, `preview_token` dall'URL; senza `title_code` valido torna alla lobby. | `backend/app/api/routes/mines.py`, `backend/app/modules/platform/game_launch/service.py`, `backend/app/modules/platform/catalog/service.py`, `backend/app/api/routes/admin.py`, `backend/app/api/routes/demo.py`, `frontend-v3/app/ui/mines/mines-standalone.tsx` |
| `MINES_API_00220` | Access session API | Presenza estesa del player nel gioco, ping, timeout e risposta specifica a void operatore; persiste anche `title_code` e `site_code`. | `backend/app/api/routes/platform_access.py`, `backend/app/modules/platform/access_sessions/service.py` |
| `MINES_API_00230` | Demo launch token API | Endpoint demo: `POST /demo/token` emette identita' anonima firmata, `POST /demo/launch` emette game launch token `mode=demo` senza login per launch pubblici quando riceve un `title_code` pubblicabile esplicito. Se riceve un `preview_token` admin valido, puo' emettere un launch demo per master o varianti nascoste senza passare dai flag lobby pubblici. | `backend/app/api/routes/demo.py`, `backend/app/modules/platform/game_launch/service.py` |
| `MINES_API_00240` | Config pubblica per Title | `GET /games/mines/config?title_code=...` restituisce runtime Mines con presentation config pubblicata del Title richiesto. | `backend/app/api/routes/mines.py`, `backend/app/modules/games/mines/backoffice_config.py` |
| `MINES_API_00250` | Replay round Mines | Endpoint read-only per replay: `GET /games/mines/session/{session_id}/replay` per player/runtime real/demo, `GET /games/mines/admin/session/{session_id}/replay` per backoffice autorizzato e `GET /games/mines/access-sessions/latest` per ultime 3 access session del player/Title con sole mani chiuse. Espone snapshot finale/fairness, non scrive stato e non invia mine nascoste su round attivi, nemmeno ad admin: il backend resta autorevole e puo' custodire il board segreto, ma il dato non esce finche' il round non e' chiuso. | `backend/app/api/routes/mines.py`, `backend/app/modules/games/mines/service.py`, `tests/integration/test_mines_replay.py`, `tests/integration/test_mines_session_history_pagination.py`, `docs/MINES_REPLAY_VIEWER_PLAN.md` |
| `MINES_ENGINE_00300` | Game service | Start, reveal, cashout, recupero sessione, stato round. | `backend/app/modules/games/mines/service.py` |
| `MINES_ENGINE_00310` | Stato round | Active, won, lost, safe reveals, celle rivelate, payout corrente. | `backend/app/modules/games/mines/service.py`, `backend/migrations/sql/0012__schema_split_platform_rounds.sql` |
| `MINES_ENGINE_00320` | Errori dominio Mines | Errori specifici gioco, conflitti stato, validazione, saldo insufficiente. | `backend/app/modules/games/mines/exceptions.py` |
| `MINES_RNG_00400` | Randomness board | Generazione posizioni mine e materiale RNG. | `backend/app/modules/games/mines/randomness.py` |
| `MINES_FAIRNESS_00410` | Fairness artifacts | Seed hash, board hash, nonce, verifica fairness. | `backend/app/modules/games/mines/fairness.py` |
| `MINES_MATH_00420` | Runtime payout | Moltiplicatori ufficiali da allegati runtime. | `backend/app/modules/games/mines/runtime.py`, `docs/runtime/CasinoKing_Documento_07_Allegato_B_Payout_Runtime_v1.json` |
| `MINES_MATH_CERT_00430` | Math certification material | Materiale audit retroattivo per la math Mines esistente: spec formale, simulator esterno standalone, parity check simulator/backend e stress framework on-demand env-gated. Non modifica runtime, RNG, fairness, API, schema, frontend, wallet o ledger. | `docs/games/mines/MATH_SPEC.md`, `tools/mines_math_simulator.py`, `tests/stress/mines_math/` |
| `MINES_PLATFORM_00500` | Platform game client + round gateway | Confine game -> platform per apertura e settlement round: `round_gateway.py` resta facciata compatibile, `platform_client.py` propaga anche `title_code` e `site_code` nella fase di open round. | `backend/app/modules/games/mines/round_gateway.py`, `backend/app/modules/games/mines/platform_client.py` |
| `MINES_PLATFORM_00510` | Platform rounds | Round economica lato piattaforma, wallet, ledger transaction e identita' commerciale `title_code`/`site_code` per audit e reporting. | `backend/app/modules/platform/rounds/service.py`, `backend/migrations/sql/0012__schema_split_platform_rounds.sql`, `backend/migrations/sql/0024__title_and_site_code_propagation.sql` |
| `MINES_PLATFORM_00520` | Table session boundary | Collegamento tra round Mines, saldo tavolo visibile, budget/perdita massima e force-close void da backoffice; persiste `title_code`/`site_code`. | `backend/app/modules/platform/table_sessions/service.py`, `backend/app/modules/admin/session_force_close.py`, `backend/app/api/routes/platform_table_sessions.py`, `backend/migrations/sql/0020__game_table_sessions.sql`, `backend/migrations/sql/0021__game_table_session_balance.sql`, `backend/migrations/sql/0022__admin_actions_session_void.sql`, `backend/migrations/sql/0024__title_and_site_code_propagation.sql` |
| `MINES_DEMO_00900` | Demo wallet | Wallet chip demo anonimo con sessione da 100 chip, idempotenza, row-level lock e nessuna scrittura su ledger/platform rounds. | `backend/app/modules/platform/demo_wallet/service.py`, `backend/migrations/sql/0027__demo_sessions.sql` |
| `MINES_DEMO_00910` | DemoPlatformGameClient | Implementazione demo del boundary `PlatformGameClient`: open debita chip demo, win accredita chip demo, loss registra evento senza double-debit. | `backend/app/modules/games/mines/platform_client.py` |
| `MINES_DEMO_00920` | Round tecnico Mines demo | Stato tecnico Mines demo separato da `mines_game_rounds` real per rispettare la FK obbligatoria verso `platform_rounds` e garantire zero scritture platform/ledger in demo. | `backend/app/modules/games/mines/service.py`, `backend/migrations/sql/0027__demo_sessions.sql` |
| `MINES_DEMO_00930` | Frontend anonymous demo flow | Il frontend ottiene `anonymous_token` da `POST /demo/token` (long-lived, localStorage), poi `game_launch_token` demo da `POST /demo/launch` (short-lived). `isDemoMode = demoAnonToken.length > 0`: tutte le chiamate di gioco usano `X-Game-Launch-Token` senza Bearer; il chip balance (100 per round) e' aggiornato da `wallet_balance_after` nelle risposte start/cashout. | `frontend-v3/app/ui/mines/mines-standalone.tsx` |
| `MINES_BACKOFFICE_00600` | Config backoffice Mines per Title | Draft/publish config per varianti Mines: `mines_classic` e' il master bloccato, le varianti hanno `source_title_code` verso il master e sono le sole modificabili; regole e label vivono in `title_configs`, griglie/mine/default e board assets in `mines_title_configs`. F7-C mantiene API e payload invariati e prosegue la decomposizione UI: command bar, overview, i18n/copy/rules, labels legacy, board assets, grid config e theme sono componenti separati, mentre `MinesBackofficeEditor` resta orchestratore. Il publish config Title scrive anche un evento operativo `title_config_publish` in `admin_audit_log`, nella stessa transazione. | `backend/app/modules/games/mines/backoffice_config.py`, `backend/app/modules/platform/catalog/title_config_service.py`, `backend/app/modules/platform/catalog/admin_title_service.py`, `backend/app/modules/platform/admin_audit/service.py`, `backend/app/api/routes/admin.py`, `frontend/app/ui/title-editor/title-editor-shell.tsx`, `frontend/app/ui/title-editor/title-editor-command-bar.tsx`, `frontend/app/ui/title-editor/engine-editor-registry.ts`, `frontend/app/ui/mines/mines-engine-editor.tsx`, `frontend/app/ui/mines/mines-backoffice-editor.tsx`, `frontend/app/ui/mines/mines-config-overview.tsx`, `frontend/app/ui/mines/mines-i18n-admin-editor.tsx`, `frontend/app/ui/mines/mines-legacy-labels-editor.tsx`, `frontend/app/ui/mines/mines-board-assets-editor.tsx`, `frontend/app/ui/mines/mines-grid-config-editor.tsx`, `frontend/app/ui/mines/mines-theme-editor.tsx` |
| `MINES_BACKOFFICE_00610` | Asset simboli board per Title | Safe icon e mine icon sono caricabili nel registro platform `title_assets` tramite API admin e usati dal backoffice/board come URL statici; upload/delete asset scrivono eventi operativi in `admin_audit_log`; i data-URL legacy restano supportati e possono essere convertiti dal comando one-shot. | `frontend/app/ui/mines/mines-backoffice-editor.tsx`, `frontend-v3/app/ui/mines/mines-board.tsx`, `backend/app/api/routes/admin_assets.py`, `backend/app/modules/platform/asset_registry/service.py`, `backend/app/tools/migrate_mines_board_asset_data_urls.py`, `backend/migrations/sql/0011__mines_backoffice_draft_publish_assets.sql`, `backend/migrations/sql/0025__title_configs_split.sql`, `backend/migrations/sql/0026__title_assets.sql`, `docs/ASSET_REGISTRY_PLAN.md` |
| `MINES_BACKOFFICE_00620` | Suoni Mines per Title | Implementato V1: asset registry accetta `audio_safe_reveal`, `audio_mine_hit`, `audio_collect`, `audio_win` con cap 1 MB; backoffice detail Mines ha sezione Sounds con upload/preview/delete; runtime usa `useMinesSounds`. I kind legacy `audio_lose` e `audio_click` restano solo compatibilita' DB e non sono uploadable dalla nuova UI. | `docs/MINES_SOUND_ASSETS_PLAN.md`, `backend/migrations/sql/0035__title_audio_asset_kinds.sql`, `backend/app/modules/platform/asset_registry/service.py`, `frontend/app/ui/mines/mines-sound-assets-editor.tsx`, `frontend-v3/app/ui/mines/use-mines-sounds.ts`, `frontend-v3/app/ui/mines/mines-runtime-tools.tsx`, `frontend-v3/app/ui/mines/mines-standalone.tsx` |
| `MINES_SKIN_01000` | Theme runtime per Title | Mines applica design tokens risolti per `title_code` tramite ThemeProvider e CSS custom properties; i default preservano la skin corrente quando il DB non ha tema; admin API minima salva draft e publish dei tokens. | `frontend/app/lib/theme/title-theme-provider.tsx`, `frontend-v3/app/ui/mines/mines-standalone.tsx`, `frontend-v3/app/ui/mines/mines.css`, `frontend/app/ui/mines/mines-theme-editor.tsx`, `backend/app/modules/platform/catalog/theme_service.py`, `backend/app/api/routes/title_theme.py`, `docs/THEME_SYSTEM_PLAN.md` |
| `MINES_SKIN_01005` | Preview demo Title | Dal backoffice il master o una variante possono aprire `/mines?title_code=<title>&mode=demo&preview=1&preview_token=<token>` dopo emissione admin `POST /admin/games/titles/{title_code}/preview-launch`; usa config/theme pubblicati, non la bozza, e non pubblica il master o una variante nascosta in lobby. | `frontend/app/ui/games/games-overview.tsx`, `frontend/app/ui/games/game-variant-list.tsx`, `frontend/app/ui/site/site-lobby-publication-panel.tsx`, `frontend-v3/app/ui/mines/mines-standalone.tsx`, `backend/app/api/routes/admin.py`, `backend/app/api/routes/demo.py` |
| `MINES_SKIN_01010` | Skin estesa per Title | Implementato V2: titolo in-game testo/immagine con fallback a `game.title`, background della sola area gioco, texture celle face-down e controlli button styling allowlistati. Publish theme blocca combinazioni sotto soglia WCAG per testo/UI. Resta skin, non core: non tocca RNG, payout, RTP, wallet, ledger o settlement. | `frontend/app/ui/mines/mines-theme-editor.tsx`, `frontend/app/ui/mines/mines-backoffice-editor.tsx`, `frontend-v3/app/ui/mines/mines-standalone.tsx`, `frontend-v3/app/ui/mines/mines-gameplay.tsx`, `frontend-v3/app/ui/mines/mines-stage-header.tsx`, `frontend-v3/app/ui/mines/mines-board.tsx`, `frontend-v3/app/ui/mines/mines.css`, `backend/app/modules/platform/catalog/theme_service.py`, `backend/app/modules/platform/asset_registry/service.py`, `backend/migrations/sql/0037__title_game_card_asset_kind.sql`, `backend/migrations/sql/0038__title_skin_asset_kinds.sql`, `docs/MINES_SKIN_EXTENDED_CUSTOMIZATION_PLAN.md`, `docs/MINES_SKIN_X0_AUDIT.md`, `docs/THEME_SYSTEM_PLAN.md`, `docs/ASSET_REGISTRY_PLAN.md`, `docs/MINES_IN_GAME_TITLE_PLAN.md` |
| `MINES_DATA_00700` | Schema DB Mines | Tabelle `platform_rounds`, `mines_game_rounds`, `game_table_sessions`, access close reason, fairness, config per Title, propagazione `title_code`/`site_code`, metadata master/variante, tabelle demo separate e constraint `title_assets` esteso ai kind audio runtime Mines, `game_card` e asset skin Title. | `backend/migrations/sql/0007__mines_fairness_seed_internal.sql`, `backend/migrations/sql/0010__mines_backoffice_config.sql`, `backend/migrations/sql/0012__schema_split_platform_rounds.sql`, `backend/migrations/sql/0020__game_table_sessions.sql`, `backend/migrations/sql/0021__game_table_session_balance.sql`, `backend/migrations/sql/0022__admin_actions_session_void.sql`, `backend/migrations/sql/0024__title_and_site_code_propagation.sql`, `backend/migrations/sql/0025__title_configs_split.sql`, `backend/migrations/sql/0027__demo_sessions.sql`, `backend/migrations/sql/0028__title_master_variants.sql`, `backend/migrations/sql/0035__title_audio_asset_kinds.sql`, `backend/migrations/sql/0037__title_game_card_asset_kind.sql`, `backend/migrations/sql/0038__title_skin_asset_kinds.sql` |
| `MINES_TEST_00800` | Test contract/integration | Contratti API, flussi wallet/ledger, concorrenza, browser smoke. | `tests/contract`, `tests/integration`, `tests/concurrency` |

## Macro-cantieri futuri registrati

Questa sezione e' solo orientativa. Non apre implementazione senza istruzioni di dettaglio.

| Cantiere | Stato | Nota |
| --- | --- | --- |
| Aggiustamenti gioco Mines | Pianificato | Usare questo atlas per distinguere sempre CORE, SKIN, API, PLATFORM e BACKOFFICE prima di modificare comportamento o UI. |
| Mines sound assets | Pianificato | Introdurre suoni configurabili da backoffice tramite asset registry; non embeddare suoni nel bundle salvo fallback esplicito. Piano: `docs/MINES_SOUND_ASSETS_PLAN.md`. |
| Mines visual effects | VF-1/VF-2 implementate | Effetti client-side per feedback win/loss/safe, separati da core e matematica. VF-3 asset-based resta rinviata. Piano: `docs/MINES_VISUAL_EFFECTS_PLAN.md`. |
| Mines replay viewer | V1.3 implementata | Replay read-only di una mano Mines, nato nel Game Module e richiamato da Storico gioco account, runtime Mines e superfici backoffice di supporto. La vista base e' fotografia finale, non timeline: esito, dati essenziali, diamanti scoperti e posizioni mine solo a round chiuso. Nel runtime e' dentro la modal Game info/Regole, tab `REPLAY`, non inline sotto il board, e carica le ultime 3 access session del player/Title. Usa skin base semplificata indipendente dalle skin Title. Round attivi non inviano mine nascoste; V2 richiedera' event log solo se servira' audit completo, link diretto da futuro backoffice player statement V2 e policy di retention/storicizzazione. Piano: `docs/MINES_REPLAY_VIEWER_PLAN.md`. |
| Mines provider bootstrap UX | In corso | BOOT-2A.6 shell refactor completato e documentato in `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`. BOOT-2B/3/4/5 V1 implementati: real Table Balance Gate prima dell'intro, preload intro, MP4 8s, poster fallback, progress bar frontend, How To Play Gate i18n, clock compatto e controlli audio FX. Mobile video optimization, Site config clock e musica restano follow-up. Cashout reveal delle mine e' implementato. Piano: `docs/MINES_PROVIDER_BOOTSTRAP_UX_PLAN.md`. |
| Mines extended skin customization | Pianificato | Estendere la skin per Title con logo/titolo immagine opzionale, background area gioco, texture celle face-down e preset button styling. Il piano impone asset registry, token/config allowlistati e confine rigido da core/RNG/payout/wallet. SKIN-X0 audit: `docs/MINES_SKIN_X0_AUDIT.md`. Piano: `docs/MINES_SKIN_EXTENDED_CUSTOMIZATION_PLAN.md`. |
| Mines i18n foundation | In corso | Locale/content map versionata per Title, resolver copy player, editor contenuti/traduzioni, coverage gate e lingua pubblicata unica per gioco/config; allowlist editoriale Mines `it`/`en`/`de`/`es`; runtime e config pubblicata restano single-locale; non tocca payout/RTP/RNG/wallet/ledger. Decisione definitiva: nessun selector lingua in-game, nessun `ck_player_locale`, nessun parametro `locale` player-side. Rules body in `title_locale_maps.locales_json[locale].rules_sections.*.body_html`; `rules_sections_json` solo projection legacy della lingua pubblicata. Manifest frontend/backend, default catalog `it/en/de/es`, resolver player, schema `title_locale_maps`, service backend, public config `presentation_config.i18n`, editor minimo backoffice per lingua pubblicata/copy/rules e scan `lint:i18n` bloccante sono implementati; coverage summary/diff UI resta raffinamento successivo. Piano: `docs/MINES_I18N_FOUNDATION_IMPLEMENTATION_PLAN.md`. |
| Identificativo spin/round nei report | Pianificato con backoffice/reporting | Mines deve esporre o propagare identificativi coerenti con `platform_rounds`; non inventare display id senza disegno reporting/ledger. |
| External HTTP adapter | Rinviato | Fase 9a in-process e' completata; Fase 9b/c riparte solo quando Michele dira' "voglio pubblicare in produzione". |

## Cosa si riusa per altri giochi simili

Se domani nasce un gioco diverso ma simile a Mines, per esempio un gioco a celle, carte, moltiplicatori o rischio progressivo:

| Da riusare | Perche' |
| --- | --- |
| Launch token e access session | Sono platform, non specifici di Mines. |
| GameBootShell, GameBootDecisionFlow e helper game-runtime | Route/query, storage, launch context, theme shell, intro/how-to-play, overlay runtime e preferenze audio sono riusabili senza importare Mines. Vedi `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`. |
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
| `MINES_SKIN_01000` | Theme runtime per Title: prima slice implementata con default e CSS variables. |
| `MINES_SKIN_01010` | Skin estesa per Title: implementata V2 con titolo testo/immagine, background area gioco, texture celle, button styling controllato e gate contrasto publish. |
| `MINES_SKIN_01020` | Board skin avanzata: simboli, animazioni e reveal style oltre alla texture face-down. |
| `MINES_SKIN_01030` | Backoffice skin editor: rifinitura UX/preview live oltre ai controlli sicuri gia' presenti. |
| `MINES_SKIN_01040` | Skin validation avanzata: oltre al gate contrasto, impedire combinazioni visive rotte. |

## Come trovare le cose nel codice

```powershell
# Frontend Mines
rg -n "MinesStandalone|MinesGameplay|MinesBoard|MinesRulesModal|MinesStageHeader" frontend-v3/app/ui/mines
rg -n "GameBootShell|GameBootDecisionFlow|useGameLaunchContext|useGameAudioPreferences" frontend-v3/app/ui/game-runtime

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
