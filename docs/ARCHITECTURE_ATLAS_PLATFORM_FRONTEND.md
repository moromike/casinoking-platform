Status: ACTIVE
Last meaningful update: 2026-05-29

# CasinoKing - Architecture Atlas Platform + Frontend

Mappa non tecnica della piattaforma CasinoKing, del frontend player/admin, del backend, del database e dei moduli contabili.

## Scopo

Questo documento serve per capire come sono collegate le parti principali della piattaforma.

Non sostituisce i documenti canonici in `docs/word/`.
Serve come indice operativo con codici stabili e riferimenti ai file.

## Come usare i codici

Esempio:

- `PLATFORM_FRONTEND_00100` = frontend player.
- `PLATFORM_BACKOFFICE_00200` = backoffice admin.
- `PLATFORM_ACCOUNTING_00500` = wallet e ledger.
- `PLATFORM_IDENTITY_00400` = registrazione, login, profilo player.

Per trovare un file:

```powershell
rg -n "register|login|wallet|ledger|admin" backend/app frontend/app
rg -n "CREATE TABLE users|CREATE TABLE wallet_accounts|CREATE TABLE ledger" backend/migrations/sql
```

## Vista generale

```text
Player Browser
  |
  v
Frontend Player
  |
  v
Platform API
  |
  +--> Auth / Identity
  +--> Wallet
  +--> Ledger
  +--> Games gateway
  +--> Reporting
  +--> Access logs
  |
  v
PostgreSQL
```

```text
Admin Browser
  |
  v
Admin Frontend / Backoffice
  |
  v
Admin API
  |
  +--> Users
  +--> Wallet operations
  +--> Ledger reports
  +--> Bonus / adjustment
  +--> Mines config
  +--> Admin management
  |
  v
PostgreSQL / Audit / Ledger
```

## Glossario semplice

| Termine | Significato semplice |
| --- | --- |
| Frontend player | Il sito che vede il giocatore. |
| Frontend admin | Il backoffice per operatori/admin. |
| API | Le porte backend chiamate dal frontend. |
| Auth | Login, token, password, ruolo. |
| Identity | Dati anagrafici e profilo utente. |
| Wallet | Saldo operativo veloce del player. |
| Ledger | Registro contabile primario. |
| Snapshot | Copia del saldo attuale nel wallet, aggiornata insieme al ledger. |
| Double-entry | Ogni movimento ha due lati contabili bilanciati. |
| Admin action | Operazione manuale tracciata. |
| CMS | Nel progetto attuale non e' un CMS separato generico; alcune funzioni CMS-like vivono nel backoffice, per esempio configurazione Mines. |
| RGS platform | Concetto di piattaforma che ospita e governa giochi; oggi non e' un servizio separato chiamato RGS, ma platform rounds, launch, access session e wallet/ledger formano il nucleo platform per i giochi. |

## Mappa frontend player

| Codice | Blocco | Cosa fa | File principali |
| --- | --- | --- | --- |
| `PLATFORM_FRONTEND_00100` | Player shell | Layout principale player e navigazione in Site V3. Le vecchie route dirette V1 login/register/account reindirizzano a Site V3 e non sono piu' prodotto player. | `frontend-v3/app/ui/player-shell.tsx`, `frontend-v3/app/login/page.tsx`, `frontend-v3/app/register/page.tsx`, `frontend-v3/app/account/page.tsx`, `frontend/app/lib/site-v3-redirect.ts` |
| `PLATFORM_FRONTEND_00110` | Homepage/lobby | Pagina ingresso player Site V3: root pubblico `:3000/` e renderer diretto `:3001/` leggono snapshot published Site V3, renderizzano moduli homepage/lobby e consumano `GET /games/library` per le griglie gioco. Il root diretto V1 `:3002/` non e' piu' lobby player: reindirizza a `/admin`. Il vecchio `PlayerLobbyPage` V1 resta quarantinato finche' i riferimenti legacy non vengono migrati o ritirati. | `frontend-v3/app/page.tsx`, `frontend-v3/app/ui/**`, `frontend/app/(player)/page.tsx`, `frontend/app/ui/player-lobby-page.tsx`, `backend/app/api/routes/games_library.py`, `backend/app/api/routes/site_v3_public.py` |
| `PLATFORM_FRONTEND_00120` | Login player | Login player Site V3 separato dal backoffice admin; consuma `/auth/login` senza duplicare il backend auth. | `frontend-v3/app/login/page.tsx`, `frontend-v3/app/ui/player-login-page.tsx` |
| `PLATFORM_FRONTEND_00130` | Registrazione player | Form registrazione player guest-only in Site V3: se il browser ha gia' un token player salvato, la pagina non mostra il form e reindirizza ad Account. `/register` legge il modulo pubblicato `system_registration_form` dalla pagina CMS di sistema `register` per copy, visibilita' campi e step documenti, con fallback default se la pagina non e' pubblicata. | `frontend-v3/app/register/page.tsx`, `frontend-v3/app/ui/player-register-page.tsx`, `frontend-v3/app/ui/registration-form-config.ts`, `backend/app/modules/platform/site_v3/manifests/modules.py` |
| `PLATFORM_FRONTEND_00140` | Account player | Dashboard account, wallet e storico gioco in Site V3. ACC-1/2/3 separano Cassa finanziaria e Storico gioco; CASHIER-1/2/3 sostituiscono la Cassa card-based con statement filtrabile su `/account/statement-movements` e detail lazy su `/account/statement-movements/{movement_id}`. `/account/wallet-movements` resta tecnico/diagnostico fuori UI player. Storico gioco usa sessioni Mines paginabili e richiama il replay game-owned per rivedere la mano; Accessi resta pending finche' non esiste endpoint player-safe. | `frontend-v3/app/account/page.tsx`, `frontend-v3/app/ui/player-account-page.tsx`, `frontend-v3/app/ui/mines/mines-replay-viewer.tsx`, `backend/app/api/routes/account.py`, `backend/app/modules/account/service.py`, `docs/ACCOUNT_WALLET_GAME_HISTORY_REDESIGN_PLAN.md`, `docs/ACCOUNT_ACC_1_ENDPOINT_AUDIT.md`, `docs/ACCOUNT_CASHIER_MOVEMENTS_REDESIGN_ANALYSIS.md` |
| `PLATFORM_FRONTEND_00150` | Storage player auth | Token e stato player lato browser. Site V3 e' il path pubblico; helper V1 restano solo per compatibilita' runtime/debug durante il retirement. | `frontend-v3/app/lib/player-auth.ts`, `frontend/app/lib/player-storage.ts`, `frontend/app/lib/auth-storage.ts` |
| `PLATFORM_FRONTEND_00160` | API client frontend | Wrapper fetch verso backend. | `frontend-v3/app/lib/api.ts`, `frontend/app/lib/api.ts` |
| `PLATFORM_FRONTEND_00170` | Tipi frontend | Tipi TypeScript condivisi tra pagine/componenti. | `frontend-v3/app/lib/types.ts`, `frontend/app/lib/types.ts` |
| `PLATFORM_FRONTEND_00180` | Componenti comuni | Bottoni e piccoli componenti riusabili. | `frontend/app/ui/components/button.tsx` |

## Mappa backoffice admin

| Codice | Blocco | Cosa fa | File principali |
| --- | --- | --- | --- |
| `PLATFORM_BACKOFFICE_00200` | Admin front end | Backoffice admin pubblico in `frontend-v3`: generic `/admin`, `/admin/site-v3` e `/admin/games/**` sono serviti da V3. V1 diretto mantiene solo redirect debug verso Site V3 fino a WP-MIG6; il public edge non dipende piu' da V1 per admin o asset statici dopo WP-MIG5F. | `frontend-v3/app/admin/page.tsx`, `frontend-v3/app/admin/site-v3/page.tsx`, `frontend-v3/app/admin/games/**`, `frontend-v3/app/ui/casinoking-console.tsx`, `frontend-v3/app/ui/admin-shell-panel.tsx`, `frontend-v3/app/ui/admin-site-v3-page.tsx`, `frontend-v3/app/ui/admin-games-page.tsx`, `frontend/app/admin/page.tsx`, `frontend-v3/public/` |
| `PLATFORM_BACKOFFICE_00210` | Admin auth storage | Token e stato admin separati dal player, duplicati nel V3 admin shell per le migrazioni `/admin`, `/admin/site-v3` e `/admin/games/**` senza cambiare le API admin. | `frontend-v3/app/lib/admin-storage.ts`, `frontend/app/lib/admin-storage.ts` |
| `PLATFORM_BACKOFFICE_00220` | Admin API route | Endpoint amministrativi principali, incluso force-close sessioni gioco per operatori finance. | `backend/app/api/routes/admin.py` |
| `PLATFORM_BACKOFFICE_00230` | Admin service | Logica backoffice: utenti, finance, report, bonus, adjustment. | `backend/app/modules/admin/service.py` |
| `PLATFORM_BACKOFFICE_00240` | My Space admin | Profilo admin e cambio password admin, servito dal generic `/admin` V3. | `frontend-v3/app/ui/admin-my-space.tsx`, `backend/app/api/routes/admin.py` |
| `PLATFORM_BACKOFFICE_00250` | Admin management | Gestione admin/superadmin e aree visibili, servita dal generic `/admin` V3. | `frontend-v3/app/ui/admin-management.tsx`, `backend/migrations/sql/0017__admin_roles_and_permissions.sql` |
| `PLATFORM_BACKOFFICE_00260` | Finance panel | Vista finance/admin lato frontend, incluse dimensioni Engine/Title/Site nei report sessioni. Il report sessioni banco e' tabellare, supporta page size 25/50/100, il click sull'email apre la scheda giocatore e il drill-down read-only mostra eventi round con `platform_round_id` e ledger transaction id. In WP-MIG5E vive in V3 senza cambiare backend finance/ledger. | `frontend-v3/app/ui/admin-finance-panel.tsx`, `frontend-v3/app/ui/casinoking-console.tsx`, `frontend-v3/app/ui/game-reporting-registry.tsx`, `backend/app/modules/admin/service.py` |
| `PLATFORM_BACKOFFICE_00270` | Player admin panel | Gestione/lettura player nel backoffice, inclusa azione finance di force-close sessioni Mines attive e sezione Accessi giocatore compatta. In WP-MIG5E vive in V3. | `frontend-v3/app/ui/player-admin-panel.tsx`, `frontend-v3/app/ui/access-log.tsx` |
| `PLATFORM_BACKOFFICE_00280` | Access log UI | Log accessi e audit visuale; supporta layout compatto riusabile nella scheda giocatore. | `frontend-v3/app/ui/access-log.tsx`, `backend/app/modules/platform/access_logs.py` |
| `PLATFORM_BACKOFFICE_00285` | Admin operational audit | Log operativo non finanziario per modifiche backoffice su Title/config/lobby/assets. Usa `admin_audit_log` e resta separato da `admin_actions`, che rimane finanziaria e ledger-linked. Traccia publish config Title, publish tema, pubblicazione lobby e upload/delete asset; la UI `LOG` espone lettura, filtri, paginazione e detail JSON senza rollback/export. | `backend/app/modules/platform/admin_audit/service.py`, `backend/migrations/sql/0030__admin_audit_log.sql`, `backend/app/api/routes/admin.py`, `frontend-v3/app/ui/audit/admin-audit-log.tsx`, `frontend-v3/app/ui/admin-shell-panel.tsx`, `backend/app/modules/games/mines/backoffice_config.py`, `backend/app/modules/platform/catalog/admin_title_service.py`, `backend/app/modules/platform/catalog/theme_service.py`, `backend/app/modules/platform/asset_registry/service.py` |
| `PLATFORM_BACKOFFICE_00290` | Mines CMS-like config | Editor backoffice Mines per draft/publish, regole, asset, config, ora pilotabile da `title_code` dinamico tramite shell Title e diviso in componenti dedicati per overview, i18n/copy/rules, Grid & mines, board assets, Sounds e Tema. In V3 gli editor admin Mines vivono in `mines-backoffice` per non mescolare runtime player e backoffice. | `frontend-v3/app/ui/mines-backoffice/mines-backoffice-editor.tsx`, `frontend-v3/app/ui/mines-backoffice/mines-config-overview.tsx`, `frontend-v3/app/ui/mines-backoffice/mines-i18n-admin-editor.tsx`, `frontend-v3/app/ui/mines-backoffice/mines-grid-config-editor.tsx`, `frontend-v3/app/ui/mines-backoffice/mines-board-assets-editor.tsx`, `frontend-v3/app/ui/mines-backoffice/mines-sound-assets-editor.tsx`, `frontend-v3/app/ui/mines-backoffice/mines-theme-editor.tsx`, `frontend-v3/app/ui/title-editor/title-editor-shell.tsx`, `frontend-v3/app/ui/title-editor/engine-editor-registry.ts`, `backend/app/modules/games/mines/backoffice_config.py` |
| `PLATFORM_BACKOFFICE_00292` | Title Editor game-agnostic shell | Shell backoffice Title refactorata whitelist-based: registry lazy per engine `mines`/`boxe`/`hi_lo`, `EngineEditorProps<TConfig>` generico, command bar con busy action `admin-${engineCode}-backoffice-*`, config runtime caricata da `/games/${engineCode}/config?title_code=...` e diagnostics slot per engine. La route admin vive in `frontend-v3` dopo WP-MIG5D; V1 mantiene solo redirect diretto. | `frontend-v3/app/ui/title-editor/engine-editor-registry.ts`, `frontend-v3/app/ui/title-editor/title-editor-shell.tsx`, `frontend-v3/app/ui/title-editor/title-editor-command-bar.tsx`, `frontend-v3/app/ui/admin-games-page.tsx`, `frontend-v3/app/ui/mines-backoffice/mines-engine-diagnostics.tsx`, `frontend-v3/app/ui/boxe-backoffice/boxe-engine-editor.tsx`, `frontend-v3/app/ui/hi-lo-backoffice/hi-lo-engine-editor.tsx`, `tests/contract/test_title_editor_agnostic.py`, `tests/integration/test_title_editor_agnostic_frontend.py` |
| `PLATFORM_BACKOFFICE_00295` | Catalogo giochi, master e varianti | Pannello backoffice V3 per ispezionare Site, Engine, master e varianti; `Games` e' un hub engine, `/admin/games/mines` apre il livello Mines e le sue varianti, e il detail Title resta su `/admin/games/[engine]/titles/[title_code]`. Per Mines mostra `mines_classic` come master bloccato ma previewable tramite token admin dedicato, le varianti modificabili/rinominabili e l'azione `Create variant`, con normalizzazione/validazione frontend del `title_code` coerente con il backend. Il detail diretto carica il Title da catalogo e valida l'engine route. | `frontend-v3/app/admin/games/**`, `frontend-v3/app/ui/platform-catalog-panel.tsx`, `frontend-v3/app/ui/games/games-overview.tsx`, `frontend-v3/app/ui/games/game-category-view.tsx`, `frontend-v3/app/ui/games/game-master-card.tsx`, `frontend-v3/app/ui/games/game-variant-list.tsx`, `frontend-v3/app/ui/games/game-status-badges.tsx`, `frontend-v3/app/ui/admin-games-page.tsx`, `frontend-v3/app/lib/title-code.ts`, `frontend/app/admin/games/**`, `backend/app/api/routes/platform_catalog.py`, `backend/app/api/routes/admin.py`, `backend/app/modules/platform/catalog/admin_title_service.py`, `backend/app/modules/platform/game_launch/service.py` |
| `PLATFORM_BACKOFFICE_00297` | Site/Lobby publishing | Area backoffice separata dalla configurazione gioco: gestisce visibilita' lobby, demo/real, ordine, featured e metadata editoriali dei Title. La vista usa un layout compatto gestione/preview e la preview legge `GET /games/library`; il backend blocca la pubblicazione di varianti senza config live. Il panel principale resta orchestratore, con summary, row editor, preview e helper draft estratti per preparare l'evoluzione CMS editoriale. | `frontend/app/ui/site/site-lobby-publication-panel.tsx`, `frontend/app/ui/site/site-lobby-summary.tsx`, `frontend/app/ui/site/site-lobby-title-row.tsx`, `frontend/app/ui/site/site-lobby-preview.tsx`, `frontend/app/ui/site/site-lobby-draft.ts`, `frontend/app/ui/admin-shell-panel.tsx`, `frontend/app/ui/casinoking-console.tsx`, `backend/app/api/routes/platform_catalog.py`, `backend/app/api/routes/admin.py`, `backend/app/modules/platform/catalog/admin_title_service.py`, `backend/app/modules/platform/catalog/library_service.py` |
| `PLATFORM_BACKOFFICE_00298` | Site CMS homepage slots | CMS-2A/D e' il vecchio flusso V1 per homepage/banner: tabella `site_home_slots`, API pubblica `/site/home`, API admin `/admin/sites/{site_code}/home-slots`, target `title_demo`/`title_real`, `site_assets.homepage_banner` e audit operativo. Dopo Site V3/WP-MIG4B non e' piu' la homepage pubblica principale; resta legacy/quarantinato finche' i riferimenti del vecchio `PlayerLobbyPage` non vengono migrati o ritirati. | `frontend/app/ui/site/site-home-slots-panel.tsx`, `frontend/app/ui/player-lobby-page.tsx`, `frontend/app/ui/casinoking-console.tsx`, `backend/app/api/routes/site_cms.py`, `backend/app/modules/platform/site_cms/service.py`, `backend/app/main.py`, `backend/migrations/sql/0033__site_home_slots.sql`, `backend/migrations/sql/0034__site_assets.sql`, `tests/integration/test_site_home_slots.py` |
| `PLATFORM_BACKOFFICE_00299` | Site V3 CMS admin/public renderer | Workstream Site V3 promosso fuori dal vecchio lab: public renderer dedicato nel servizio Docker `frontend-v3` diretto su `:3001`, V1 diretto su `:3002` solo come host debug/redirect fino a WP-MIG6. Il servizio `edge` espone Site V3 come root pubblico `:3000`, instrada login/registrazione/account, shell gioco pubbliche, `/admin/**`, `/_next`, favicon, `/game-assets` e `/brand` a `frontend-v3`, e serve Mines/BOXE/HI-LO runtime da `frontend-v3/app/runtime/*`. Le route dirette V1 `/login`, `/register`, `/account`, `/mines`, `/boxe`, `/hi-lo`, `/admin`, `/admin/site-v3` e `/admin/games/**` reindirizzano a Site V3 preservando o stabilizzando l'ownership pubblica; il root diretto V1 `:3002/` reindirizza a `/admin`. WP-MIG4C fissa il target di estrazione runtime giochi in `frontend-v3/app/runtime/{game}` senza cambiare backend wallet/ledger/payout/RNG; WP-MIG4D/E/F applicano il pattern a BOXE, HI-LO e Mines. WP-MIG5B/C/D/E sposta il builder, la shell login admin, generic `/admin`, game admin/title editor e pannelli finance/player/settings/audit in `frontend-v3`; WP-MIG5F sposta gli asset statici pubblici residui in `frontend-v3/public` e rimuove l'upstream V1 dall'edge. Il lab locale `frontend-v2/` e' stato rimosso in WP6; `cms_v2_*` resta dormiente come memoria storica, non come prodotto Site V3. | `frontend-v3/app/admin/page.tsx`, `frontend-v3/app/admin/site-v3/page.tsx`, `frontend-v3/app/admin/games/**`, `frontend-v3/app/ui/casinoking-console.tsx`, `frontend-v3/app/ui/admin-site-v3-page.tsx`, `frontend-v3/app/ui/admin-games-page.tsx`, `frontend-v3/app/ui/site-v3-admin/**`, `frontend-v3/app/ui/title-editor/**`, `frontend-v3/app/ui/games/**`, `frontend-v3/app/ui/admin-finance-panel.tsx`, `frontend-v3/app/ui/player-admin-panel.tsx`, `frontend-v3/app/ui/admin-platform-settings-panel.tsx`, `frontend-v3/public/**`, `frontend/app/admin/**`, `frontend/app/lib/site-v3-redirect.ts`, `frontend-v3/app/**`, `frontend/app/(player)/page.tsx`, `infra/docker/edge.conf`, `infra/docker/frontend-v3.Dockerfile`, `infra/docker/docker-compose.yml`, `backend/app/modules/platform/site_v3/**`, `backend/app/api/routes/site_v3_admin.py`, `backend/app/api/routes/site_v3_public.py`, `docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md`, `docs/SITE_V3_V1_RETIREMENT_PLAN_2026-05-29.md`, `docs/SITE_V3_RUNTIME_EXTRACTION_CONTRACT_2026-05-29.md` |

## Mappa backend platform

| Codice | Blocco | Cosa fa | File principali |
| --- | --- | --- | --- |
| `PLATFORM_BACKEND_00300` | FastAPI app | Avvio app, router principale, health. | `backend/app/main.py`, `backend/app/api/router.py`, `backend/app/api/routes/health.py` |
| `PLATFORM_BACKEND_00310` | Config backend | Env, settings, URL DB/Redis, CORS. | `backend/app/core/config.py`, `infra/docker/.env` |
| `PLATFORM_BACKEND_00320` | DB connection | Connessione PostgreSQL. | `backend/app/db/connection.py` |
| `PLATFORM_BACKEND_00330` | API responses/dependencies | Envelope response, auth dependency. | `backend/app/api/responses.py`, `backend/app/api/dependencies.py` |
| `PLATFORM_BACKEND_00340` | Migration tool | Applicazione migrazioni SQL. | `backend/app/tools/apply_migrations.py`, `backend/migrations/sql` |
| `PLATFORM_BACKEND_00350` | Bootstrap admin locale | Creazione admin locale. | `backend/app/tools/bootstrap_local_admin.py` |
| `PLATFORM_BACKEND_00360` | Account read models | Endpoint player-safe read-only per viste Account: `/account/wallet-movements` resta tecnico/contabile; `/account/statement-movements` espone righe business filtrabili per la Cassa; `/account/statement-movements/{movement_id}` espone detail player-safe paginato. Tutti derivano da ledger/wallet e non cambiano i write path wallet/ledger. | `backend/app/api/routes/account.py`, `backend/app/modules/account/service.py`, `tests/integration/test_account_wallet_movements.py` |

## Mappa identita', registrazione e login

| Codice | Blocco | Cosa fa | File principali |
| --- | --- | --- | --- |
| `PLATFORM_IDENTITY_00400` | Auth API | Register, login, reset password, change password. | `backend/app/api/routes/auth.py` |
| `PLATFORM_IDENTITY_00410` | Auth service | Creazione utente, credenziali, login, cambio password. | `backend/app/modules/auth/service.py` |
| `PLATFORM_IDENTITY_00420` | Security tokens/password | Hash password, JWT, reset token. | `backend/app/modules/auth/security.py` |
| `PLATFORM_IDENTITY_00430` | Users schema | Tabelle utenti, credenziali, PII iniziale. | `backend/migrations/sql/0003__users_auth_foundations.sql`, `backend/migrations/sql/0015__add_user_pii_fields.sql` |
| `PLATFORM_IDENTITY_00440` | Register frontend | Form player registration solo per guest in Site V3; un player gia' autenticato viene mandato su `/account`. Copy e struttura del form possono essere configurati dal CMS tramite `system_registration_form`, ma il submit resta `/auth/register`. | `frontend-v3/app/register/page.tsx`, `frontend-v3/app/ui/player-register-page.tsx`, `frontend-v3/app/ui/registration-form-config.ts` |
| `PLATFORM_IDENTITY_00450` | Login frontend | Login player Site V3. | `frontend-v3/app/login/page.tsx`, `frontend-v3/app/ui/player-login-page.tsx` |
| `PLATFORM_IDENTITY_00460` | Access logs | Audit accessi login e backoffice. | `backend/app/modules/platform/access_logs.py`, `backend/migrations/sql/0019__access_logs.sql` |

## Mappa accounting, wallet e ledger

| Codice | Blocco | Cosa fa | File principali |
| --- | --- | --- | --- |
| `PLATFORM_ACCOUNTING_00500` | Wallet API | Lettura wallet player. | `backend/app/api/routes/wallets.py` |
| `PLATFORM_ACCOUNTING_00510` | Wallet service | Lettura wallet e snapshot saldo. | `backend/app/modules/wallet/service.py` |
| `PLATFORM_ACCOUNTING_00520` | Ledger API | Lettura transazioni ledger. | `backend/app/api/routes/ledger.py` |
| `PLATFORM_ACCOUNTING_00530` | Ledger service | Query ledger e storico contabile. | `backend/app/modules/ledger/service.py` |
| `PLATFORM_ACCOUNTING_00540` | Financial schema | `ledger_accounts`, `wallet_accounts`, `ledger_transactions`, `ledger_entries`. | `backend/migrations/sql/0002__financial_core_foundations.sql`, `backend/migrations/sql/0004__seed_system_ledger_accounts.sql` |
| `PLATFORM_ACCOUNTING_00550` | Admin financial operations | Bonus, adjustment, report finance e void sessioni gioco con reversal ledger. | `backend/app/modules/admin/service.py`, `backend/app/modules/admin/session_force_close.py`, `backend/app/api/routes/admin.py` |
| `PLATFORM_ACCOUNTING_00560` | Game financial bridge | Round economiche dei giochi e settlement. | `backend/app/modules/platform/rounds/service.py`, `backend/migrations/sql/0012__schema_split_platform_rounds.sql` |
| `PLATFORM_ACCOUNTING_00570` | Reconciliation tests | Controlli drift wallet/ledger. | `tests/integration/test_reconciliation_integrity.py`, `tests/integration/test_financial_and_mines_flows.py` |

## Mappa giochi come piattaforma

| Codice | Blocco | Cosa fa | File principali |
| --- | --- | --- | --- |
| `PLATFORM_GAMES_00600` | Game launch | Autorizza ingresso a un gioco con launch token; il token include `game_code`, `title_code`, `site_code`, `mode` e valida la pubblicazione Site/Title. Il launch pubblico richiede `title_code` esplicito, rifiuta i Title master con codice stabile `LAUNCH_REJECTED_MASTER` e applica `lobby_visibility`, `demo_enabled` e `real_enabled`; la preview backoffice usa token admin dedicato e non pubblica master/hidden Title. | `backend/app/modules/platform/game_launch/service.py`, `backend/app/modules/platform/catalog/service.py`, `backend/app/api/routes/mines.py`, `backend/app/api/routes/admin.py`, `backend/app/api/routes/demo.py` |
| `PLATFORM_GAMES_00602` | Demo launch anonimo | Flusso demo pubblico: token anonimo firmato, launch token `mode=demo`, routing Mines senza bearer login e senza impatto ledger/platform rounds. Lo stesso endpoint accetta un `preview_token` admin firmato per demo preview backoffice di Title non pubblicati in lobby. | `backend/app/api/routes/demo.py`, `backend/app/api/routes/mines.py`, `backend/app/modules/platform/game_launch/service.py`, `backend/app/modules/platform/demo_wallet/service.py` |
| `PLATFORM_GAMES_00603` | Game library pubblica | Endpoint pubblico della libreria giochi del Site: espone varianti non-master con `lobby_visibility=visible` e demo/real abilitati. | `backend/app/api/routes/games_library.py`, `backend/app/modules/platform/catalog/library_service.py`, `backend/migrations/sql/0029__site_title_lobby_publication.sql`, `frontend/app/ui/player-lobby-page.tsx` |
| `PLATFORM_GAMES_00605` | Catalogo Engine/Title/Site | Catalogo dei giochi pubblicabili: engine tecnico, title commerciale e distribuzione site; `game_titles` distingue master/varianti e `site_titles` governa anche la pubblicazione leggera in lobby. | `backend/app/modules/platform/catalog/service.py`, `backend/app/modules/platform/catalog/admin_title_service.py`, `backend/app/api/routes/platform_catalog.py`, `backend/app/api/routes/admin.py`, `backend/migrations/sql/0023__platform_catalog_bootstrap.sql`, `backend/migrations/sql/0028__title_master_variants.sql`, `backend/migrations/sql/0029__site_title_lobby_publication.sql` |
| `PLATFORM_GAMES_00610` | Access sessions | Sessione di presenza player nel gioco, con close reason per distinguere timeout, lifecycle e void operatore; persiste `title_code` e `site_code`. | `backend/app/modules/platform/access_sessions/service.py`, `backend/app/api/routes/platform_access.py`, `backend/migrations/sql/0024__title_and_site_code_propagation.sql` |
| `PLATFORM_GAMES_00620` | Platform rounds | Round economica comune ai giochi con dimensioni Engine/Title/Site per audit e reporting. | `backend/app/modules/platform/rounds/service.py`, `backend/migrations/sql/0012__schema_split_platform_rounds.sql`, `backend/migrations/sql/0024__title_and_site_code_propagation.sql` |
| `PLATFORM_GAMES_00630` | Mines module | Primo gioco proprietario; il boundary verso la platform passa da `PlatformGameClient`/`round_gateway`. Runtime player in Site V3; backoffice editor migrato in V3 sotto cartella admin-only `mines-backoffice`. | `backend/app/modules/games/mines`, `frontend-v3/app/ui/mines`, `frontend-v3/app/ui/mines-backoffice`, `frontend/app/ui/mines` |
| `PLATFORM_GAMES_00635` | Title asset registry | Registro platform-owned degli asset per Title, aperto in Fase 4 con tabella `title_assets`, storage filesystem, mount statico, API admin e integrazione frontend Mines per simboli board, audio, card lobby e asset skin Title. Gli asset statici di fallback runtime non registrati sono ora serviti da `frontend-v3/public`. | `backend/app/modules/platform/asset_registry/storage.py`, `backend/app/modules/platform/asset_registry/service.py`, `backend/app/api/routes/admin_assets.py`, `backend/app/main.py`, `frontend-v3/public/game-assets/`, `frontend/app/lib/api.ts`, `frontend/app/ui/mines/mines-backoffice-editor.tsx`, `frontend/app/ui/mines/mines-board.tsx`, `backend/migrations/sql/0026__title_assets.sql`, `backend/migrations/sql/0035__title_audio_asset_kinds.sql`, `backend/migrations/sql/0037__title_game_card_asset_kind.sql`, `backend/migrations/sql/0038__title_skin_asset_kinds.sql`, `docs/ASSET_REGISTRY_PLAN.md` |
| `PLATFORM_GAMES_00637` | Title theme runtime | Risoluzione pubblica del tema per Title da `title_configs.theme_tokens_json`, merge con default e asset URL versionati, endpoint cacheable `/titles/{title_code}/theme`; API admin draft/publish dei tokens e skin strutturata con gate contrasto WCAG al publish. | `backend/app/modules/platform/catalog/theme_service.py`, `backend/app/api/routes/title_theme.py`, `frontend/app/lib/theme/title-theme-provider.tsx`, `frontend/app/ui/mines/mines-backoffice-editor.tsx`, `frontend/app/ui/mines/mines-theme-editor.tsx`, `frontend/app/ui/mines/mines-gameplay.tsx`, `frontend/app/ui/mines/mines.css`, `docs/THEME_SYSTEM_PLAN.md` |
| `PLATFORM_GAMES_00650` | Table sessions | Sessione economica platform-owned con gate pre-game, scelta wallet real/bonus, saldo tavolo visibile, budget/perdita massima per gioco e persistenza `title_code`/`site_code`. | `backend/app/modules/platform/table_sessions/service.py`, `backend/app/api/routes/platform_table_sessions.py`, `backend/migrations/sql/0020__game_table_sessions.sql`, `backend/migrations/sql/0021__game_table_session_balance.sql`, `backend/migrations/sql/0024__title_and_site_code_propagation.sql` |
| `PLATFORM_GAMES_00640` | Future game modules | Spazio concettuale per giochi futuri. | Futuro: `backend/app/modules/games/<game_code>`, `frontend/app/ui/<game_code>` |

## Macro-cantieri futuri registrati

Questa sezione e' una fotografia di orientamento. Non sostituisce un piano di dettaglio e non autorizza modifiche automatiche.

| Cantiere | Stato | Nota |
| --- | --- | --- |
| Backoffice UI e leggibilita' menu | Pianificato | Prima di intervenire identificare se il cambio tocca shell admin, finance panel, player admin panel, access log o Mines config. |
| Mines i18n foundation | In corso | Cantiere circoscritto al runtime/backoffice Mines: locale/content map per Title, resolver player, editor contenuti/traduzioni, coverage gate e lingua pubblicata unica per gioco/config; allowlist editoriale Mines `it`/`en`/`de`/`es`; runtime e config pubblicata restano single-locale. Non significa i18n globale platform; la UI backoffice resta IT-only. Decisione definitiva: nessun selector lingua in-game, nessun `ck_player_locale`, nessun parametro `locale` player-side. Rules body in `title_locale_maps.locales_json[locale].rules_sections.*.body_html`; `rules_sections_json` solo projection legacy della lingua pubblicata. Manifest frontend/backend, default catalog `it/en/de/es`, resolver player, schema/service `title_locale_maps`, public config `presentation_config.i18n`, editor minimo backoffice lingua/copy/rules e scan `lint:i18n` bloccante sono implementati; coverage summary/diff UI resta raffinamento successivo. |
| Identificativo spin/round visibile nei report | Pianificato | Definire prima quale id e' esposto a player/admin: `platform_rounds.id`, id Mines, idempotency key o un nuovo display id auditabile. |
| Modifiche sito web/player frontend | Pianificato | Usare mappa frontend player e documenti UI/UX; separare lobby/account/auth da Mines. |
| Crypto wallet proprietario | Pianificato, area critica | Richiede design dedicato financial core. Non bypassare ledger double-entry, wallet snapshot, idempotenza, reconciliation e audit. |

## Mappa database

| Codice | Blocco | Cosa contiene | File principali |
| --- | --- | --- | --- |
| `PLATFORM_DB_00700` | Migrazioni SQL | Evoluzione schema DB. | `backend/migrations/sql` |
| `PLATFORM_DB_00710` | Users/auth | Utenti, credenziali, PII base. | `0003__users_auth_foundations.sql`, `0015__add_user_pii_fields.sql` |
| `PLATFORM_DB_00720` | Financial core | Ledger, wallet, accounts. | `0002__financial_core_foundations.sql`, `0004__seed_system_ledger_accounts.sql` |
| `PLATFORM_DB_00730` | Mines/game rounds | Round platform e round Mines, inclusa propagazione `title_code`/`site_code`. | `0012__schema_split_platform_rounds.sql`, `0013__migrate_game_sessions_data.sql`, `0014__drop_game_sessions.sql`, `0024__title_and_site_code_propagation.sql` |
| `PLATFORM_DB_00740` | Backoffice/admin | Admin actions, admin roles, permissions, estensione `session_void`. | `0006__admin_actions_foundations.sql`, `0017__admin_roles_and_permissions.sql`, `0018__admin_last_login.sql`, `0022__admin_actions_session_void.sql` |
| `PLATFORM_DB_00750` | Game CMS-like config | Mines config draft/publish/assets. | `0010__mines_backoffice_config.sql`, `0011__mines_backoffice_draft_publish_assets.sql` |
| `PLATFORM_DB_00760` | Access/session logs | Access session, access logs e dimensioni Title/Site per sessione gioco. | `0016__game_access_sessions.sql`, `0019__access_logs.sql`, `0024__title_and_site_code_propagation.sql` |
| `PLATFORM_DB_00770` | Game table sessions | Budget/perdita massima per sessione di gioco, FK da `platform_rounds` e dimensioni Title/Site. | `0020__game_table_sessions.sql`, `0024__title_and_site_code_propagation.sql` |
| `PLATFORM_DB_00780` | Game catalog | Engine tecnici, Title pubblicati, Site e relazione Site/Title. | `0023__platform_catalog_bootstrap.sql` |
| `PLATFORM_DB_00790` | Title assets | Registro asset per Title con URL versionati per checksum e un solo asset active per kind/Title. | `0026__title_assets.sql` |
| `PLATFORM_DB_00800` | Demo mode schema | Tabelle demo per identita' anonima, chip wallet e round tecnico Mines demo; separate dal ledger reale e da `platform_rounds`. | `0027__demo_sessions.sql` |
| `PLATFORM_DB_00810` | Site title lobby publication | Metadata leggeri di pubblicazione lobby su `site_titles`: visibilita', demo/real, nome/descrizione, featured e posizione. | `0029__site_title_lobby_publication.sql` |
| `PLATFORM_DB_00820` | Admin audit log operativo | Tabella append-only per modifiche non finanziarie originate da admin. Non ha FK ledger, non ha target user obbligatorio e non sostituisce `admin_actions`. | `0030__admin_audit_log.sql` |
| `PLATFORM_DB_00830` | Site CMS homepage slots | Slot editoriali homepage/banner per Site CMS, con status draft/published/archived, schedule, target Title validato dal service e audit operativo separato dal financial core. | `0033__site_home_slots.sql` |
| `PLATFORM_DB_00840` | Site assets homepage banner | Asset media site-owned per homepage/banner, limitati a `asset_kind = homepage_banner`, PNG/JPEG/WebP max 2 MB, consigliati 1280 x 720 px, renderizzati cover/center con possibile crop, serviti da `/static/sites/...` e associabili a `site_home_slots.media_asset_id`. | `0034__site_assets.sql` |

## Registrazione oggi

```text
Site V3 /register
  |
  +--> published CMS page `register` + `system_registration_form`
  |    controls copy, field visibility, document step and post-register path
  |
  +--> client auth gate: token player presente = redirect /account, niente form
  |
  v
POST /auth/register
  |
  v
Auth service
  |
  +--> users
  +--> user_credentials
  +--> wallet_accounts
  +--> ledger_accounts
  +--> signup ledger transaction
```

Codici coinvolti:

- `PLATFORM_FRONTEND_00130`
- `PLATFORM_IDENTITY_00400`
- `PLATFORM_IDENTITY_00410`
- `PLATFORM_ACCOUNTING_00540`

## Registrazione futura con piu' dati e foto

Non va implementata ora.
La mappa corretta, quando arrivera', dovrebbe separare bene:

```text
Account login
  email, password, ruolo, stato

Identity profile
  nome, cognome, codice fiscale, telefono, dati anagrafici

KYC / Documenti
  foto, documento, verifica, stato approvazione

Wallet / Ledger
  saldo e contabilita'
```

Possibili codici futuri:

| Codice futuro | Idea |
| --- | --- |
| `PLATFORM_IDENTITY_01000` | Profilo identita' esteso. |
| `PLATFORM_KYC_01100` | Upload foto/documenti. |
| `PLATFORM_KYC_01110` | Stato verifica documenti. |
| `PLATFORM_KYC_01120` | Backoffice revisione documenti. |
| `PLATFORM_STORAGE_01200` | Storage file immagini/documenti. |
| `PLATFORM_AUDIT_01300` | Audit eventi identita'/KYC. |

## CMS e configurazione

Nel progetto attuale non esiste ancora un CMS generale separato.
Esistono pero' funzioni CMS-like:

| Codice | Area | Cosa configura |
| --- | --- | --- |
| `PLATFORM_CMS_00800` | Title/Mines backoffice config | Regole, label, asset, theme, griglie e mine per varianti Mines; il master Mines resta read-only e serve solo come base di duplicazione. |
| `PLATFORM_CMS_00810` | Skin/theme runtime | Colori, radius, ombre e font risolti per Title e applicati via CSS custom properties; editor visuale ancora fuori scope. |
| `PLATFORM_CMS_00820` | Future content pages | Copy e contenuti sito player, se servira'. |
| `PLATFORM_CMS_00830` | Game library publication | Pubblicazione leggera dei Title in lobby: hidden/visible, demo/real, nome/descrizione e ordinamento. Non e' un CMS completo del sito; la prima UI dedicata vive in Site/Lobby Publishing e resta separata dalla configurazione gioco. La prossima evoluzione e' un editor editoriale guidato documentato in `docs/SITE_CMS_EDITORIAL_UX_PLAN.md`. |
| `PLATFORM_CMS_00840` | Homepage/banner slots | Superficie CMS mirata per banner/hero/spotlight homepage. CMS-2A espone public read e admin CRUD minimo; CMS-2B aggiunge editor admin frontend per lista, creazione, modifica e preview compatta degli slot; CMS-2C consuma il primo slot pubblicato nella lobby player come hero editoriale; CMS-2D rende configurabile l'immagine banner tramite `site_assets.homepage_banner`, senza media library generale. |
| `PLATFORM_CMS_00850` | Site banner media e mockup | Media banner completato per upload/select/render. Resta pianificato il mockup sito prima del redesign. | `docs/SITE_BANNER_AND_MOCKUP_PLAN.md` |

## Come trovare le cose nel codice

```powershell
# Registrazione e login
rg -n "def register|def login|register_player|authenticate_user" backend/app

# Wallet e ledger
rg -n "wallet_accounts|ledger_transactions|ledger_entries|balance_snapshot" backend/app backend/migrations/sql

# Backoffice admin
rg -n "admin|bonus|adjustment|report" backend/app/api/routes/admin.py backend/app/modules/admin/service.py frontend/app/ui

# Frontend player
rg -n "PlayerLobbyPage|PlayerLoginPage|PlayerRegisterPage|PlayerAccountPage" frontend/app

# DB schema
rg -n "CREATE TABLE users|CREATE TABLE wallet_accounts|CREATE TABLE ledger_transactions|CREATE TABLE platform_rounds" backend/migrations/sql

# Game platform
rg -n "game_launch|access_session|platform_round|rounds" backend/app/modules/platform backend/app/api/routes
```

## Regola di orientamento

Quando parliamo di piattaforma, bisogna sempre chiedersi:

```text
Sto parlando di FRONTEND, API, MODULO BACKEND, DATABASE, ACCOUNTING, BACKOFFICE o FUTURA ESTENSIONE?
```

Questa domanda evita di mischiare registrazione, contabilita', backoffice, gioco e CMS.
