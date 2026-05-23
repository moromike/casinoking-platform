# CasinoKing - Code Architecture Mermaid Map

Status: ACTIVE  
Last meaningful update: 2026-05-23
Scope: navigational code map for humans. This does not replace `docs/SOURCE_OF_TRUTH.md` or the architecture atlas docs; it is a visual index for finding the right layer quickly.

## How To View It

You do not need to copy diagrams one by one.

Fastest local option on Windows:

1. Open this file in Cursor or VS Code.
2. Press `Ctrl+Shift+V` to open Markdown Preview.
3. The Mermaid diagrams render inline in the preview.

Useful alternatives:

- `Ctrl+K V` opens the preview side-by-side with the markdown source.
- GitHub renders Mermaid automatically when this file is opened in the repository UI.
- Mermaid Live Editor is useful only when editing a single diagram interactively; in that case copy just one `mermaid` block.

## 1. System Overview

```mermaid
flowchart LR
  User["Player / Admin browser"] --> FE["Next.js frontend<br/>frontend/app"]
  FE --> APIClient["Frontend API clients<br/>frontend/app/lib"]
  APIClient --> BE["FastAPI backend<br/>backend/app"]

  subgraph Docker["Local / Docker services"]
    BE --> PG["Postgres"]
    BE --> Redis["Redis"]
    FE --> NextDev["Next dev server<br/>localhost:3000"]
  end

  BE --> Routes["API routes<br/>backend/app/api/routes"]
  Routes --> Modules["Domain modules<br/>backend/app/modules"]
  Modules --> DB["DB models / repositories"]
  Modules --> Assets["Asset registry / storage"]

  FE --> PlayerUI["Player runtime UI"]
  FE --> AdminUI["Admin / backoffice UI"]
  FE --> AccountUI["Account / lobby UI"]
```

## 2. Frontend Route And UI Ownership

```mermaid
flowchart TB
  subgraph App["frontend/app"]
    Routes["Routes<br/>(player), account, admin, login, register, mines, boxe, hi-lo"]
    Lib["lib<br/>API, auth, runtime helpers"]
    UI["ui<br/>component domains"]
  end

  subgraph UIDomains["frontend/app/ui"]
    Runtime["game-runtime<br/>shared player primitives"]
    Mines["mines<br/>Mines player + admin adapter"]
    Boxe["boxe<br/>BOXE player runtime"]
    BoxeBO["boxe-backoffice<br/>BOXE admin editor"]
    HiLo["hi-lo<br/>HI-LO player runtime"]
    HiLoBO["hi-lo-backoffice<br/>HI-LO admin editor"]
    TitleEditor["title-editor<br/>shared admin editing shell"]
    GamesAdmin["games<br/>admin engine / title list"]
    Site["site<br/>site shell and CMS UI"]
    Audit["audit<br/>admin audit surfaces"]
    Components["components<br/>generic UI pieces"]
  end

  Routes --> UI
  Routes --> Lib
  UI --> Runtime
  UI --> Mines
  UI --> Boxe
  UI --> BoxeBO
  UI --> HiLo
  UI --> HiLoBO
  UI --> TitleEditor
  UI --> GamesAdmin
  UI --> Site
  UI --> Audit
  UI --> Components

  GamesAdmin --> TitleEditor
  Mines --> Runtime
  Boxe --> Runtime
  HiLo --> Runtime
  Mines --> TitleEditor
  BoxeBO --> TitleEditor
  HiLoBO --> TitleEditor
```

## 3. Player Game Runtime Inheritance

```mermaid
flowchart TB
  subgraph SharedRuntime["frontend/app/ui/game-runtime"]
    Boot["GameBootShell / launch context"]
    TopBar["GameTopBar"]
    Rail["GameControlRail / mobile stack"]
    Bet["GameBetPanel / quick chips / action buttons"]
    Balance["GameBalanceFooter"]
    HTP["GameHowToPlayGate"]
    Info["GameInfoRulesModal"]
    Error["GameActionError / copy adapter"]
    Storage["game-storage / audio preferences"]
  end

  subgraph MinesPlayer["frontend/app/ui/mines"]
    MinesStandalone["mines-standalone.tsx"]
    MinesGameplay["mines-gameplay.tsx"]
    MinesBoard["mines-board.tsx"]
    MinesRules["mines-rules-modal.tsx"]
    MinesReplay["mines-replay-viewer.tsx"]
    MinesI18n["mines-i18n/*"]
  end

  subgraph BoxePlayer["frontend/app/ui/boxe"]
    BoxeStandalone["boxe-standalone.tsx"]
    BoxeGameplay["boxe-gameplay.tsx"]
    Pyramid["boxe-pyramid-board.tsx"]
    Payout["boxe-payout-display.tsx"]
    BoxeRules["boxe-rules-modal.tsx"]
    BoxeReplay["boxe-replay-viewer.tsx"]
    BoxeI18n["boxe-i18n/*"]
  end

  subgraph HiLoPlayer["frontend/app/ui/hi-lo"]
    HiLoStandalone["hi-lo-standalone.tsx"]
    HiLoGameplay["hi-lo-gameplay.tsx"]
    HiLoRuntime["use-hi-lo-runtime.ts"]
    HiLoRules["hi-lo-rules-modal.tsx"]
    HiLoReplay["hi-lo-replay-viewer.tsx"]
    HiLoHowTo["hi-lo-how-to-visual.tsx"]
    HiLoI18n["hi-lo-i18n/*"]
    HiLoCss["hi-lo.css"]
    HiLoAssets["public/game-assets/hi-lo/*"]
  end

  MinesStandalone --> Boot
  MinesStandalone --> TopBar
  MinesStandalone --> HTP
  MinesGameplay --> Rail
  MinesGameplay --> Bet
  MinesGameplay --> Balance
  MinesGameplay --> MinesBoard
  MinesGameplay --> MinesRules
  MinesGameplay --> MinesReplay
  MinesGameplay --> Error
  MinesRules --> Info
  MinesGameplay --> MinesI18n

  BoxeStandalone --> Boot
  BoxeStandalone --> TopBar
  BoxeStandalone --> HTP
  BoxeGameplay --> Rail
  BoxeGameplay --> Bet
  BoxeGameplay --> Balance
  BoxeGameplay --> Pyramid
  BoxeGameplay --> Payout
  BoxeGameplay --> BoxeRules
  BoxeGameplay --> BoxeReplay
  BoxeGameplay --> Error
  BoxeRules --> Info
  BoxeGameplay --> BoxeI18n

  HiLoStandalone --> Boot
  HiLoStandalone --> HTP
  HiLoStandalone --> HiLoHowTo
  HiLoStandalone --> HiLoI18n
  HiLoGameplay --> Rail
  HiLoGameplay --> Bet
  HiLoGameplay --> Balance
  HiLoGameplay --> Error
  HiLoGameplay --> HiLoRules
  HiLoRules --> Info
  HiLoRules --> HiLoI18n
  HiLoGameplay --> HiLoRuntime
  HiLoReplay --> HiLoRuntime
  HiLoGameplay --> HiLoCss
  HiLoReplay --> HiLoCss
  HiLoCss --> HiLoAssets

  RuntimeBoundary["Boundary rule:<br/>game-runtime must not import game UI folders"] -. guards .-> SharedRuntime
  GameBoundary["Game UI folders do not import each other"] -. guards .-> MinesPlayer
  GameBoundary -. guards .-> BoxePlayer
  GameBoundary -. guards .-> HiLoPlayer
```

## 4. Backend Platform And Game Flow

```mermaid
flowchart LR
  subgraph APIRoutes["backend/app/api/routes"]
    MinesRoute["mines.py"]
    BoxeRoute["boxe.py"]
    HiLoRoute["hi_lo.py"]
    DemoRoute["demo.py"]
    AccountRoute["account.py"]
    AdminRoute["admin.py / admin_assets.py"]
    CatalogRoute["games_library.py / platform_catalog.py"]
    TableRoute["platform_table_sessions.py"]
    ThemeRoute["title_theme.py"]
  end

  subgraph GameModules["backend/app/modules/games"]
    MinesService["mines/service.py"]
    MinesRuntime["mines/runtime.py"]
    MinesRandom["mines/randomness.py"]
    MinesFairness["mines/fairness.py"]

    BoxeService["boxe/service.py"]
    BoxeState["boxe/state_machine.py"]
    BoxeMath["boxe/math.py"]
    BoxeRandom["boxe/randomness.py"]
    BoxeFairness["boxe/fairness.py"]

    HiLoService["hi_lo/service.py"]
    HiLoState["hi_lo/state_machine.py"]
    HiLoMath["hi_lo/math.py"]
    HiLoRandom["hi_lo/randomness.py"]
    HiLoFairness["hi_lo/fairness.py"]
  end

  subgraph Platform["backend/app/modules/platform"]
    Launch["game_launch/service.py"]
    Access["access_sessions/service.py"]
    TableSessions["table_sessions/service.py"]
    Rounds["rounds/service.py"]
    Catalog["catalog/*"]
    Assets["asset_registry/*"]
    DemoWallet["demo_wallet/service.py"]
    Audit["admin_audit/service.py"]
  end

  subgraph MoneyAndAuth["Core business modules"]
    Auth["auth/*"]
    Users["users/*"]
    Wallet["wallet/service.py"]
    Ledger["ledger/service.py"]
    Account["account/service.py"]
  end

  MinesRoute --> MinesService
  BoxeRoute --> BoxeService
  HiLoRoute --> HiLoService
  DemoRoute --> DemoWallet
  AccountRoute --> Account
  AdminRoute --> Catalog
  AdminRoute --> Assets
  CatalogRoute --> Catalog
  TableRoute --> TableSessions
  ThemeRoute --> Catalog

  MinesService --> MinesRuntime
  MinesService --> MinesRandom
  MinesService --> MinesFairness
  MinesService --> Rounds
  MinesService --> TableSessions

  BoxeService --> BoxeState
  BoxeService --> BoxeMath
  BoxeService --> BoxeRandom
  BoxeService --> BoxeFairness
  BoxeService --> Rounds
  BoxeService --> TableSessions

  HiLoService --> HiLoState
  HiLoService --> HiLoMath
  HiLoService --> HiLoRandom
  HiLoService --> HiLoFairness
  HiLoService --> Rounds
  HiLoService --> TableSessions
  HiLoService --> DemoWallet

  Launch --> Access
  Launch --> Catalog
  Rounds --> Wallet
  Wallet --> Ledger
  Auth --> Users
```

## 5. Backoffice And Title Editor Flow

```mermaid
flowchart TB
  AdminRoot["/admin/games"] --> GamesOverview["games-overview.tsx"]
  GamesOverview --> CategoryView["game-category-view.tsx"]
  CategoryView --> MasterCard["game-master-card.tsx"]
  CategoryView --> VariantList["game-variant-list.tsx"]
  VariantList --> DetailLink["/admin/games/{engine}/titles/{title_code}"]

  DetailLink --> TitleShell["title-editor/title-editor-shell.tsx"]
  TitleShell --> Registry["title-editor/engine-editor-registry.ts"]

  subgraph SharedAdmin["title-editor shared primitives"]
    CommandBar["TitleEditorCommandBar"]
    Tabs["tabs/*<br/>overview, copy, rules, config, assets, theme, sound"]
    Status["status / validation / publish controls"]
    Sound["title-sound-assets-editor.tsx"]
  end

  subgraph MinesAdmin["frontend/app/ui/mines"]
    MinesEngine["mines-engine-editor.tsx"]
    MinesBackoffice["mines-backoffice-editor.tsx"]
    MinesGrid["mines-grid-config-editor.tsx"]
    MinesTheme["mines-theme-editor.tsx"]
    MinesAssets["mines-board-assets-editor.tsx"]
    MinesSound["mines-sound-assets-editor.tsx"]
    MinesI18nAdmin["mines-i18n-admin-editor.tsx"]
  end

  subgraph BoxeAdmin["frontend/app/ui/boxe-backoffice"]
    BoxeEngine["boxe-engine-editor.tsx"]
    BoxeOverview["boxe-config-overview.tsx"]
    BoxeTheme["boxe-theme-editor.tsx"]
    BoxeAssets["boxe-assets-editor.tsx"]
  end

  subgraph HiLoAdmin["frontend/app/ui/hi-lo-backoffice"]
    HiLoAdminEngine["hi-lo-engine-editor.tsx"]
    HiLoAdminOverview["hi-lo-config-overview.tsx"]
    HiLoAdminTheme["hi-lo-theme-editor.tsx"]
    HiLoAdminAssets["hi-lo-assets-editor.tsx"]
  end

  Registry --> MinesEngine
  Registry --> BoxeEngine
  Registry --> HiLoAdminEngine
  TitleShell --> CommandBar
  TitleShell --> Tabs
  TitleShell --> Status

  MinesEngine --> MinesBackoffice
  MinesBackoffice --> MinesGrid
  MinesBackoffice --> MinesTheme
  MinesBackoffice --> MinesAssets
  MinesBackoffice --> MinesSound
  MinesBackoffice --> MinesI18nAdmin

  BoxeEngine --> BoxeOverview
  BoxeEngine --> BoxeTheme
  BoxeEngine --> BoxeAssets
  BoxeEngine --> Tabs
  BoxeEngine --> Sound

  HiLoAdminEngine --> HiLoAdminOverview
  HiLoAdminEngine --> HiLoAdminTheme
  HiLoAdminEngine --> HiLoAdminAssets
  HiLoAdminEngine --> Tabs
  HiLoAdminEngine --> Sound
```

## 6. Admin Backend Services

```mermaid
flowchart LR
  AdminFE["Admin frontend<br/>/admin/games"] --> AdminAPI["Admin API routes"]

  subgraph Routes["backend/app/api/routes"]
    AdminRoutes["admin.py"]
    AdminAssets["admin_assets.py"]
    CatalogRoutes["platform_catalog.py"]
    ThemeRoutes["title_theme.py"]
    SiteCMSRoutes["site_cms.py"]
  end

  subgraph CatalogServices["backend/app/modules/platform/catalog"]
    AdminTitle["admin_title_service.py"]
    TitleConfig["title_config_service.py"]
    TitleLocale["title_locale_service.py"]
    ThemeService["theme_service.py"]
    Library["library_service.py"]
  end

  subgraph GameAdminConfig["backend/app/modules/games"]
    BoxeAdminConfig["boxe/admin_config.py"]
    HiLoAdminConfig["hi_lo/admin_config.py"]
  end

  subgraph AssetServices["backend/app/modules/platform/asset_registry"]
    AssetService["service.py"]
    AssetStorage["storage.py"]
  end

  AdminAPI --> AdminRoutes
  AdminAPI --> AdminAssets
  AdminAPI --> CatalogRoutes
  AdminAPI --> ThemeRoutes
  AdminAPI --> SiteCMSRoutes

  AdminRoutes --> AdminTitle
  AdminRoutes --> BoxeAdminConfig
  AdminRoutes --> HiLoAdminConfig
  AdminTitle --> BoxeAdminConfig
  AdminTitle --> HiLoAdminConfig
  CatalogRoutes --> AdminTitle
  CatalogRoutes --> TitleConfig
  CatalogRoutes --> TitleLocale
  ThemeRoutes --> ThemeService
  AdminAssets --> AssetService
  AssetService --> AssetStorage
  Library --> AdminTitle
  HiLoAdminConfig --> TitleConfig
```

## 7. Persistence Map

```mermaid
flowchart TB
  subgraph DB["Postgres persistence groups"]
    AuthDB["auth / users"]
    MoneyDB["wallet / ledger"]
    CatalogDB["game catalog<br/>titles, variants, site status"]
    TitleDB["title config<br/>copy, theme, assets, sound"]
    SessionDB["access sessions<br/>table sessions"]
    RoundDB["platform rounds<br/>game rounds"]
    MinesDB["Mines-specific state"]
    BoxeDB["BOXE-specific state"]
    HiLoDB["HI-LO-specific state"]
    AuditDB["admin audit / access logs"]
    CMSDB["site CMS"]
  end

  AuthModule["auth + users modules"] --> AuthDB
  WalletModule["wallet + ledger modules"] --> MoneyDB
  CatalogModule["platform/catalog"] --> CatalogDB
  CatalogModule --> TitleDB
  AssetModule["asset_registry"] --> TitleDB
  AccessModule["access_sessions / table_sessions"] --> SessionDB
  RoundsModule["platform/rounds"] --> RoundDB
  MinesModule["games/mines"] --> MinesDB
  BoxeModule["games/boxe"] --> BoxeDB
  HiLoModule["games/hi_lo"] --> HiLoDB
  AuditModule["admin_audit"] --> AuditDB
  SiteModule["site_cms"] --> CMSDB
```

## 8. Main Runtime Request Flow

```mermaid
sequenceDiagram
  participant Browser as Browser
  participant Frontend as Next.js frontend
  participant Backend as FastAPI backend
  participant Launch as platform/game_launch
  participant Game as game service
  participant Rounds as platform/rounds
  participant Wallet as wallet/ledger
  participant DB as Postgres

  Browser->>Frontend: Open game route
  Frontend->>Backend: Request launch / runtime config
  Backend->>Launch: Resolve title, mode, access session
  Launch->>DB: Read catalog, title config, access policy
  Backend-->>Frontend: Runtime payload

  Browser->>Frontend: Bet / pick / cashout
  Frontend->>Backend: Game action with action token
  Backend->>Game: Validate state and apply action
  Game->>Rounds: Create/update authoritative round
  Game->>Wallet: Debit / credit when needed
  Wallet->>DB: Persist ledger movement
  Game->>DB: Persist game-specific state
  Backend-->>Frontend: Authoritative next state
```

## 9. BOXE-Specific Gameplay Flow

```mermaid
flowchart TB
  BoxeUI["boxe-gameplay.tsx"] --> Settings["Rows / difficulty / bet controls"]
  BoxeUI --> Start["POST /games/boxe/start"]
  Start --> BoxeService["backend games/boxe/service.py"]
  BoxeService --> Math["math.py<br/>multipliers, RTP"]
  BoxeService --> Randomness["randomness.py<br/>board generation"]
  BoxeService --> State["state_machine.py"]
  BoxeService --> Reveal["pyramid_full_reveal<br/>terminal payload"]
  BoxeService --> Replay["replay payload"]

  BoxeUI --> Board["boxe-pyramid-board.tsx"]
  Board --> Geometry["cells_for_row(row, rows)<br/>rows - row + 1"]
  Board --> Assets["diamond / mine assets<br/>public/game-assets/boxe"]
  Board --> CSS["boxe.css<br/>adaptive pyramid sizing"]

  BoxeUI --> Info["boxe-rules-modal.tsx"]
  Info --> Copy["boxe-i18n/boxe-copy-defaults.ts"]
  Info --> SharedInfo["game-runtime/GameInfoRulesModal"]
```

## 10. Guarded Boundaries To Check During Refactors

```mermaid
flowchart LR
  Runtime["game-runtime"] -. must not import .-> Mines["mines"]
  Runtime -. must not import .-> Boxe["boxe"]
  Runtime -. must not import .-> HiLo["hi-lo"]
  Mines -. must not import .-> Boxe
  Boxe -. must not import .-> Mines
  HiLo -. must not import .-> Mines
  HiLo -. must not import .-> Boxe
  Frontend["frontend/app/ui"] -. should not import backend internals .-> Backend["backend/app"]

  TitleEditor["title-editor shared"] --> MinesAdmin["Mines admin adapters"]
  TitleEditor --> BoxeAdmin["BOXE admin adapters"]
  TitleEditor --> HiLoAdmin["HI-LO admin adapters"]
  MinesAdmin -. zero-diff gate when touched .-> MinesPlayer["Mines player"]
  BoxeAdmin -. game-specific only where documented .-> BoxeDocs["SPEC / MATH_SPEC / BOXE_BRIEF"]
```

## 11. HI-LO Player Runtime Flow

```mermaid
flowchart TB
  HiLoRoute["/hi-lo"] --> Standalone["hi-lo-standalone.tsx"]
  Standalone --> Boot["GameBootShell / launch context"]
  Standalone --> Provider["GameProviderBootstrap"]
  Standalone --> HTP["GameHowToPlayGate"]
  Standalone --> TableGate["GameTableBalanceGate"]
  Standalone --> Resume["GET /games/hi-lo/active-round<br/>title_code + wallet_source"]
  Standalone --> Gameplay["hi-lo-gameplay.tsx"]

  Gameplay --> Rail["GameControlRail / bet / balance / actions"]
  Gameplay --> Card["current card renderer"]
  Gameplay --> Choices["black / red / down / up predictions"]
  Gameplay --> History["round history and seed hash"]
  Gameplay --> Rules["GameInfoRulesModal"]
  Gameplay --> RuntimeApi["use-hi-lo-runtime.ts"]

  RuntimeApi --> Config["GET /games/hi-lo/config"]
  RuntimeApi --> Active["GET /games/hi-lo/active-round<br/>wallet-source isolated resume"]
  RuntimeApi --> Start["POST /games/hi-lo/start"]
  RuntimeApi --> Predict["POST /games/hi-lo/predict"]
  RuntimeApi --> Skip["POST /games/hi-lo/skip"]
  RuntimeApi --> Cashout["POST /games/hi-lo/cashout"]
  RuntimeApi --> Replay["GET /games/hi-lo/round/{id}/replay"]

  Start --> Backend["backend games/hi_lo/service.py"]
  Active --> Backend
  Predict --> Backend
  Skip --> Backend
  Cashout --> Backend
  Replay --> Backend

  Account["player-account-page.tsx"] --> Sessions["GET /games/hi-lo/sessions"]
  Account --> ReplayViewer["hi-lo-replay-viewer.tsx"]
  AdminFinance["admin-finance-panel.tsx"] --> AdminReplay["GET /games/hi-lo/admin/round/{id}/replay"]
  AdminFinance --> ReplayViewer
  Sessions --> Backend
  AdminReplay --> Backend
```

## 12. Quick File Index

| Area | Start here |
| --- | --- |
| Player runtime shared shell | `frontend/app/ui/game-runtime/` |
| Mines player | `frontend/app/ui/mines/mines-standalone.tsx`, `frontend/app/ui/mines/mines-gameplay.tsx` |
| BOXE player | `frontend/app/ui/boxe/boxe-standalone.tsx`, `frontend/app/ui/boxe/boxe-gameplay.tsx` |
| BOXE board | `frontend/app/ui/boxe/boxe-pyramid-board.tsx`, `frontend/app/ui/boxe/boxe.css` |
| HI-LO player | `frontend/app/ui/hi-lo/hi-lo-standalone.tsx`, `frontend/app/ui/hi-lo/hi-lo-gameplay.tsx`, `frontend/app/ui/hi-lo/hi-lo-replay-viewer.tsx`, `frontend/app/ui/hi-lo/use-hi-lo-runtime.ts` |
| Admin engine list | `frontend/app/ui/games/` |
| Shared title editor | `frontend/app/ui/title-editor/` |
| Mines admin editor | `frontend/app/ui/mines/mines-engine-editor.tsx`, `frontend/app/ui/mines/mines-backoffice-editor.tsx` |
| BOXE admin editor | `frontend/app/ui/boxe-backoffice/boxe-engine-editor.tsx` |
| HI-LO admin editor | `frontend/app/ui/hi-lo-backoffice/hi-lo-engine-editor.tsx`, `frontend/app/ui/hi-lo-backoffice/hi-lo-config-overview.tsx`, `frontend/app/ui/hi-lo-backoffice/hi-lo-assets-editor.tsx`, `frontend/app/ui/hi-lo-backoffice/hi-lo-theme-editor.tsx` |
| Backend routes | `backend/app/api/routes/` |
| Mines backend | `backend/app/modules/games/mines/` |
| BOXE backend | `backend/app/modules/games/boxe/` |
| HI-LO backend | `backend/app/modules/games/hi_lo/` |
| Platform catalog/admin services | `backend/app/modules/platform/catalog/` |
| Platform sessions/rounds | `backend/app/modules/platform/access_sessions/`, `backend/app/modules/platform/table_sessions/`, `backend/app/modules/platform/rounds/` |
| Assets | `backend/app/modules/platform/asset_registry/`, `frontend/public/game-assets/` |
