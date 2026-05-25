Status: ACTIVE
Last meaningful update: 2026-05-25

# CasinoKing Active Open Loops

Registro breve delle cose aperte che non devono restare affidate alla memoria
della singola AI.

## Regola

Quando un punto viene chiuso, aggiornare questo file nello stesso task o spiegare
perche' non serve piu'. Non sostituisce i piani operativi; serve da cruscotto.

## P0 - Da Non Dimenticare

| Area | Stato | Prossima azione |
| --- | --- | --- |
| Mines V1 | Accettata: baseline BOOT-2A.0 congelata su `main`; baseline visual stabilizzata in BOOT-2A.0.5 usando `mines_classic` read-only. BOOT-2A e' chiuso lato docs/atlas. | Mantenere baseline verde; eventuali modifiche a configurazione/asset `mines_classic` richiedono refresh dedicato delle baseline. |
| BOOT-2A Game Boot Shell | Chiuso: `GameBootShell`, `GameBootDecisionFlow`, helper route/storage, `useGameLaunchContext`, `useGameAudioPreferences` e separazione `MinesStandalone` wrapper / `MinesGameplay` sono documentati. Target line count rivisto a 2000; `mines-standalone.tsx` e' a 1939 righe con `wc -l`. | Non riaprire BOOT-2A. Per il secondo gioco partire da `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`; debiti residui in `docs/MINES_PENDING_TOPICS.md`. |
| Mines browser full smoke legacy debt | Aperto: full browser smoke legacy ha 11 failure note residue fuori scope BOOT-2A.5. | Pulire prima del rilascio o quando diventa bloccante per un altro work package. |
| Mines audio runtime | V1 implementato: asset kind audio, backoffice Sounds, hook `useMinesSounds`, controlli FX mute/volume e runtime events. | Caricare asset audio reali sui Title e fare QA uditiva; musica resta fuori scope. |
| Mines provider intro | BOOT-2B V1 implementato: real mode Table Balance Gate prima dell'intro, preload media, video MP4 8s, poster fallback e progress bar frontend. BOOT-2A refactor shell completato e documentato. | Testare intro desktop/mobile; ottimizzare video mobile; poi decidere se mantenere 8s sempre o introdurre policy V2 sessionStorage/intro breve. |
| Mines How To Play Gate | V1 implementato dopo intro e prima del gameplay, con copy default/i18n. | QA copy/layout mobile; V2 "non mostrare piu'" solo se diventa fastidioso. |
| Mines runtime clock | V1 implementato come clock compatto `HH:mm` Europe/Rome. | Spostare su Site config quando esiste il contratto platform; override Title solo se necessario. |
| Mines skin estesa | Chiuso: MSK V2 mergeato in `main` il 2026-05-16 con backend asset/theme, upload backoffice per title logo/background/cell texture, runtime player wiring e WCAG publish gate. | Mantenere `mines_classic` come baseline read-only; nuove evoluzioni skin richiedono piano CTO dedicato. |
| Finance menu giochi / replay backoffice | MVP WP3 implementato in workspace: registry guard unknown, Mines/BOXE/HI-LO registrati, admin finance senza fallback BOXE, player senza fallback Mines, metadata ledger v2 forward-only, BOXE wallet source e retention policy 30gg online/no deletion. | Resta futuro il reconciliation report on-demand e ogni cold-storage/deletion job approvato legal/product. |
| Platform observability / errori / settings installazione | WP-ERROR-REQUEST-FOUNDATION-MVP implementato: request/support id, AppError/registry MVP, central handlers, frontend diagnostic line e test contract. Approach: `docs/PLATFORM_ERROR_REQUEST_FOUNDATION_MVP_APPROACH_2026-05-25.md`. | Prossima azione: partire da logging MVP. In parallelo si possono avviare finance/replay registry e settings read-only inventory. |
| CMS v2 / perimetro CMS | Aperto ma deferred da Michele il 2026-05-24: se ne parla dopo. CTO triage in `docs/OPEN_TOPICS_CTO_REVIEW_2026-05-24.md`; esperimento Gemini/lab non va portato avanti acriticamente. | Non iniziare codice CMS. Quando Michele riapre il tema, aprire `WP-CMS-V2-RESCUE-SCOPE`: auditare artefatti CMS v2, decidere cosa salvare/cestinare/rifare, ridefinire perimetro. |
| HI-LO moltiplicatore corrente | Implementato localmente il 2026-05-24: badge gameplay mostra solo moltiplicatore corrente, senza label/incasso, e runtime/replay copy e' stato spostato nel manifest i18n. | Product test su `localhost:3000`, poi commit dedicato insieme alla regola Playbook no-hardcoded runtime/error copy. |
| COINS - nuovo gioco proprietario (Fase 0) | Aperto 2026-05-25: 25 Q product + round 2 follow-up CHIUSI il 2026-05-25 sera. Decisioni archiviate in `docs/games/coins/COINS_OPEN_QUESTIONS_2026-05-25.md`. Prerequisiti stretti Rule 18 registry ed embed parity implementati in workspace il 2026-05-25. | Verifica gate finale/commit dei 2 prerequisiti, poi aprire Fase 1 COINS Architecture Mapping. Resta fuori scope il WP finance-retention ampio. |
| WP-FINANCE-REPLAY-REGISTRY-RETENTION (prerequisito COINS) | Implementato MVP in workspace: unknown game unavailable, backend auto-settlement registry mantenuto con settlement taxonomy, forward metadata JSON, BOXE wallet source, retention doc. Il prompt COINS-only iniziale è SUPERSEDED. | Gate mirati + commit dedicato; aprire WP separati per reconciliation report e cold storage/deletion dopo decisione legal/product. |
| WP platform foundation - 4 review CTO | WP1 Error Foundation chiuso in workspace. Restano WP2 Logging, WP3 Finance registry/retention, WP4 Settings inventory. Tutte le review CTO restano fonte primaria per i mandatory. | Ordine operativo: WP2 Logging in serie; WP3 Finance + WP4 Settings possono procedere in parallelo dopo il commit WP1. |
| WP-EMBED-MODE-PARITY-BOXE-HILO (prerequisito COINS) | Implementato in workspace il 2026-05-25: `useGameEmbedBridge(gameCode)` in `game-runtime/`; Mines/BOXE/HI-LO consumano close + fullscreen-state; admin Mines launcher mantiene compat legacy. | Gate finale/commit. Audit: `docs/games/coins/EMBED_MODE_PARITY_AUDIT_2026-05-25.md`. |

## P1 - Prodotto/UX

| Area | Stato | Prossima azione |
| --- | --- | --- |
| CMS v2 / Module Composer | CMSV2-4 completato ma da rivalutare: Module Editor interattivo implementato nel lab 3001; supporto per configurazione moduli via schema (registry); integrazione nel backoffice legacy (port 3000) con bottone "Site v2". Michele segnala che il lavoro Gemini va verificato criticamente. | Non procedere oltre acriticamente: audit CMS v2, ridefinizione perimetro, poi decidere se recuperare o rifare. |
| Site mockup/redesign | Banner media CMS-2D completato; redesign visuale sito non fatto. | Raccogliere reference, scegliere direzione Premium Casino Lobby, produrre mockup prima del redesign. |
| Player account/cassa | Read model e UI cassa/storico gioco sono stati rifatti, ma validazione utente finale resta aperta. | Test utente su Cassa, Storico gioco, replay e compattezza; decidere eventuali correzioni. |
| Replay retention/storicizzazione | Concetto emerso, non progettato. | Piano futuro su retention/storicizzazione replay/report prima di produzione. |
| Nuovo gioco proprietario | Obiettivo macro futuro, non aperto come implementazione. BOOT-2A sblocca il piano/design della shell frontend, non autorizza codice gioco. | Disegnare nuovo engine con Game Adapter dedicato e checklist `NewGameStandalone` in `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`. |

## Chiarimenti Chiusi

| Punto | Esito |
| --- | --- |
| Banner sito caricabili | Implementato: `site_assets.homepage_banner`, admin upload/select/delete e render player con fallback. |
| BOOT-1 cashout reveal mine | Implementato: dopo cashout/auto-win il round e' chiuso e il frontend mostra le mine ricevute dal backend. |
| Assets locali `assets/` | Cartella di servizio non versionata; gli asset runtime entrano solo tramite registry o path pubblico dichiarato. |
| Finance drilldown | Chiuso: drilldown read-only mergeato in `main` il 2026-05-16; usa endpoint detail esistente e non modifica wallet/ledger/RNG/payout/settlement. |
