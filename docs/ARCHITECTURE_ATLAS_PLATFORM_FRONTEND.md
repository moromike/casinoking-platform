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
| `PLATFORM_FRONTEND_00100` | Player shell | Layout principale player e navigazione. | `frontend/app/(player)/layout.tsx`, `frontend/app/ui/player-shell.tsx` |
| `PLATFORM_FRONTEND_00110` | Homepage/lobby | Pagina ingresso player, card Mines, link login/register. | `frontend/app/(player)/page.tsx`, `frontend/app/ui/player-lobby-page.tsx` |
| `PLATFORM_FRONTEND_00120` | Login player | Login separato dal backoffice admin. | `frontend/app/login/page.tsx`, `frontend/app/ui/player-login-page.tsx` |
| `PLATFORM_FRONTEND_00130` | Registrazione player | Form registrazione player. | `frontend/app/register/page.tsx`, `frontend/app/ui/player-register-page.tsx` |
| `PLATFORM_FRONTEND_00140` | Account player | Dashboard account, wallet, storico sessioni. | `frontend/app/account/page.tsx`, `frontend/app/ui/player-account-page.tsx` |
| `PLATFORM_FRONTEND_00150` | Storage player auth | Token e stato player lato browser. | `frontend/app/lib/player-storage.ts`, `frontend/app/lib/auth-storage.ts` |
| `PLATFORM_FRONTEND_00160` | API client frontend | Wrapper fetch verso backend. | `frontend/app/lib/api.ts` |
| `PLATFORM_FRONTEND_00170` | Tipi frontend | Tipi TypeScript condivisi tra pagine/componenti. | `frontend/app/lib/types.ts` |
| `PLATFORM_FRONTEND_00180` | Componenti comuni | Bottoni e piccoli componenti riusabili. | `frontend/app/ui/components/button.tsx` |

## Mappa backoffice admin

| Codice | Blocco | Cosa fa | File principali |
| --- | --- | --- | --- |
| `PLATFORM_BACKOFFICE_00200` | Admin front end | Pagina backoffice admin. | `frontend/app/admin/page.tsx`, `frontend/app/ui/admin-shell-panel.tsx` |
| `PLATFORM_BACKOFFICE_00210` | Admin auth storage | Token e stato admin separati dal player. | `frontend/app/lib/admin-storage.ts` |
| `PLATFORM_BACKOFFICE_00220` | Admin API route | Endpoint amministrativi principali, incluso force-close sessioni gioco per operatori finance. | `backend/app/api/routes/admin.py` |
| `PLATFORM_BACKOFFICE_00230` | Admin service | Logica backoffice: utenti, finance, report, bonus, adjustment. | `backend/app/modules/admin/service.py` |
| `PLATFORM_BACKOFFICE_00240` | My Space admin | Profilo admin e cambio password admin. | `frontend/app/ui/admin-my-space.tsx`, `backend/app/api/routes/admin.py` |
| `PLATFORM_BACKOFFICE_00250` | Admin management | Gestione admin/superadmin e aree visibili. | `frontend/app/ui/admin-management.tsx`, `backend/migrations/sql/0017__admin_roles_and_permissions.sql` |
| `PLATFORM_BACKOFFICE_00260` | Finance panel | Vista finance/admin lato frontend. | `frontend/app/ui/admin-finance-panel.tsx` |
| `PLATFORM_BACKOFFICE_00270` | Player admin panel | Gestione/lettura player nel backoffice, inclusa azione finance di force-close sessioni Mines attive. | `frontend/app/ui/player-admin-panel.tsx` |
| `PLATFORM_BACKOFFICE_00280` | Access log UI | Log accessi e audit visuale. | `frontend/app/ui/access-log.tsx`, `backend/app/modules/platform/access_logs.py` |
| `PLATFORM_BACKOFFICE_00290` | Mines CMS-like config | Editor backoffice Mines per draft/publish, regole, asset, config. | `frontend/app/ui/mines/mines-backoffice-editor.tsx`, `backend/app/modules/games/mines/backoffice_config.py` |

## Mappa backend platform

| Codice | Blocco | Cosa fa | File principali |
| --- | --- | --- | --- |
| `PLATFORM_BACKEND_00300` | FastAPI app | Avvio app, router principale, health. | `backend/app/main.py`, `backend/app/api/router.py`, `backend/app/api/routes/health.py` |
| `PLATFORM_BACKEND_00310` | Config backend | Env, settings, URL DB/Redis, CORS. | `backend/app/core/config.py`, `infra/docker/.env` |
| `PLATFORM_BACKEND_00320` | DB connection | Connessione PostgreSQL. | `backend/app/db/connection.py` |
| `PLATFORM_BACKEND_00330` | API responses/dependencies | Envelope response, auth dependency. | `backend/app/api/responses.py`, `backend/app/api/dependencies.py` |
| `PLATFORM_BACKEND_00340` | Migration tool | Applicazione migrazioni SQL. | `backend/app/tools/apply_migrations.py`, `backend/migrations/sql` |
| `PLATFORM_BACKEND_00350` | Bootstrap admin locale | Creazione admin locale. | `backend/app/tools/bootstrap_local_admin.py` |

## Mappa identita', registrazione e login

| Codice | Blocco | Cosa fa | File principali |
| --- | --- | --- | --- |
| `PLATFORM_IDENTITY_00400` | Auth API | Register, login, reset password, change password. | `backend/app/api/routes/auth.py` |
| `PLATFORM_IDENTITY_00410` | Auth service | Creazione utente, credenziali, login, cambio password. | `backend/app/modules/auth/service.py` |
| `PLATFORM_IDENTITY_00420` | Security tokens/password | Hash password, JWT, reset token. | `backend/app/modules/auth/security.py` |
| `PLATFORM_IDENTITY_00430` | Users schema | Tabelle utenti, credenziali, PII iniziale. | `backend/migrations/sql/0003__users_auth_foundations.sql`, `backend/migrations/sql/0015__add_user_pii_fields.sql` |
| `PLATFORM_IDENTITY_00440` | Register frontend | Form player registration. | `frontend/app/register/page.tsx`, `frontend/app/ui/player-register-page.tsx` |
| `PLATFORM_IDENTITY_00450` | Login frontend | Login player. | `frontend/app/login/page.tsx`, `frontend/app/ui/player-login-page.tsx` |
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
| `PLATFORM_GAMES_00600` | Game launch | Autorizza ingresso a un gioco con launch token; nel monolite Mines richiede bearer player + launch token coerenti sugli endpoint operativi. | `backend/app/modules/platform/game_launch/service.py`, `backend/app/api/routes/mines.py` |
| `PLATFORM_GAMES_00610` | Access sessions | Sessione di presenza player nel gioco, con close reason per distinguere timeout, lifecycle e void operatore. | `backend/app/modules/platform/access_sessions/service.py`, `backend/app/api/routes/platform_access.py` |
| `PLATFORM_GAMES_00620` | Platform rounds | Round economica comune ai giochi. | `backend/app/modules/platform/rounds/service.py` |
| `PLATFORM_GAMES_00630` | Mines module | Primo gioco proprietario; il boundary verso la platform passa da `PlatformGameClient`/`round_gateway`. | `backend/app/modules/games/mines`, `frontend/app/ui/mines` |
| `PLATFORM_GAMES_00650` | Table sessions | Sessione economica platform-owned con gate pre-game, scelta wallet real/bonus, saldo tavolo visibile e budget/perdita massima per gioco. | `backend/app/modules/platform/table_sessions/service.py`, `backend/app/api/routes/platform_table_sessions.py`, `backend/migrations/sql/0020__game_table_sessions.sql`, `backend/migrations/sql/0021__game_table_session_balance.sql` |
| `PLATFORM_GAMES_00640` | Future game modules | Spazio concettuale per giochi futuri. | Futuro: `backend/app/modules/games/<game_code>`, `frontend/app/ui/<game_code>` |

## Mappa database

| Codice | Blocco | Cosa contiene | File principali |
| --- | --- | --- | --- |
| `PLATFORM_DB_00700` | Migrazioni SQL | Evoluzione schema DB. | `backend/migrations/sql` |
| `PLATFORM_DB_00710` | Users/auth | Utenti, credenziali, PII base. | `0003__users_auth_foundations.sql`, `0015__add_user_pii_fields.sql` |
| `PLATFORM_DB_00720` | Financial core | Ledger, wallet, accounts. | `0002__financial_core_foundations.sql`, `0004__seed_system_ledger_accounts.sql` |
| `PLATFORM_DB_00730` | Mines/game rounds | Round platform e round Mines. | `0012__schema_split_platform_rounds.sql`, `0013__migrate_game_sessions_data.sql`, `0014__drop_game_sessions.sql` |
| `PLATFORM_DB_00740` | Backoffice/admin | Admin actions, admin roles, permissions, estensione `session_void`. | `0006__admin_actions_foundations.sql`, `0017__admin_roles_and_permissions.sql`, `0018__admin_last_login.sql`, `0022__admin_actions_session_void.sql` |
| `PLATFORM_DB_00750` | Game CMS-like config | Mines config draft/publish/assets. | `0010__mines_backoffice_config.sql`, `0011__mines_backoffice_draft_publish_assets.sql` |
| `PLATFORM_DB_00760` | Access/session logs | Access session e access logs. | `0016__game_access_sessions.sql`, `0019__access_logs.sql` |
| `PLATFORM_DB_00770` | Game table sessions | Budget/perdita massima per sessione di gioco e FK da `platform_rounds`. | `0020__game_table_sessions.sql` |

## Registrazione oggi

```text
Frontend register
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
| `PLATFORM_CMS_00800` | Mines backoffice config | Regole, label, asset, griglie e mine pubblicate. |
| `PLATFORM_CMS_00810` | Future skin config | Colori, padding, temi, brand, stagionalita'. |
| `PLATFORM_CMS_00820` | Future content pages | Copy e contenuti sito player, se servira'. |
| `PLATFORM_CMS_00830` | Future game catalog | Lista giochi, card, ordine lobby, visibilita'. |

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
