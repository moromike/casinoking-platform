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
| Platform observability / errori / settings installazione | I 4 MVP platform sono committati: Error Foundation `1c07ced`, Structured Logging `6d83be4`, Finance/Replay Registry `e7cf96d`, Settings Read-Only Inventory `1857b00`. Gap security/settings MVP chiusi: no client default access password, `/ready` DB/Redis, RBAC explicit profile, Site v2 senza token query. Platform Settings ha filtri funzionanti, descrizioni IT/EN e CSS leggibile su fondo chiaro. | Passare a COINS Fase 1 o aprire solo i follow-up lunghi non-MVP (invite token, telemetry avanzata, CMS v2 secure handoff). |
| Payout runtime descriptor uniformity | Chiuso: esiste un contratto descriptor per-game con `game_code`, payout/math source, RTP source, replay verification source e spec hash/path. Settings lo espone come descriptor uniforme; il finance/replay registry frontend porta lo stesso concetto nei suoi adapter. | Usare questo descriptor come baseline COINS: niente quarto branch e niente nuove righe path scollegate. |
| Site V3 / perimetro nuovo sito-CMS | WP2 Backend MVP, WP3 Admin Builder MVP e WP4 Public Renderer MVP implementati. Prima tranche WP5 completata: `frontend-v3/` separa i 7 moduli in componenti dedicati, usa `/games/library` per card gioco e `/site/home` per banner/promo V1 pubblicati come fallback. | Prossimo step: walkthrough Michele su `:3000/admin/site-v3` e `:3001`; poi WP5 polish mirato su feedback e WP6 cleanup `frontend-v2/`. |
| HI-LO moltiplicatore corrente | Implementato localmente il 2026-05-24: badge gameplay mostra solo moltiplicatore corrente, senza label/incasso, e runtime/replay copy e' stato spostato nel manifest i18n. | Product test su `localhost:3000`, poi commit dedicato insieme alla regola Playbook no-hardcoded runtime/error copy. |
| COINS - nuovo gioco proprietario (Fase 0+1) | Aperto 2026-05-25: 25 Q product + round 2 follow-up CHIUSI. Decisioni archiviate in `docs/games/coins/COINS_OPEN_QUESTIONS_2026-05-25.md`. Prerequisiti stretti Rule 18 registry ed embed parity sono committati. Parte A plan prodotto in `docs/games/coins/COINS_PHASE_0_1_PLAN_2026-05-25.md`. | Approvare il plan Parte A, poi produrre i 6 documenti finali: source inventory, decision map, 12-surface status, SPEC, MATH_SPEC, ARCHITECTURE_MAPPING. Niente codice COINS prima della chiusura documentale. |
| WP-FINANCE-REPLAY-REGISTRY-RETENTION (prerequisito COINS) | MVP committato `e7cf96d`: unknown game unavailable, backend auto-settlement registry mantenuto con settlement taxonomy, forward metadata JSON, BOXE wallet source, retention doc. Il prompt COINS-only iniziale e' SUPERSEDED. | Aprire WP separati per reconciliation report on-demand e cold storage/deletion dopo decisione legal/product. |
| WP platform foundation - 4 review CTO | Chiuso come tranche MVP: WP1 Error Foundation, WP2 Logging, WP3 Finance Registry/Retention, WP4 Settings Inventory. Tutte le review CTO sono state recepite nei rispettivi implementation docs. | Non riaprire come mega-WP. Ogni gap residuo deve diventare WP dedicato con scope e gate propri. |
| WP-EMBED-MODE-PARITY-BOXE-HILO (prerequisito COINS) | Committato il 2026-05-25: `useGameEmbedBridge(gameCode)` in `game-runtime/`; Mines/BOXE/HI-LO consumano close + fullscreen-state; admin Mines launcher mantiene compat legacy. | Usare questo bridge come baseline per COINS e per ogni nuovo gioco. Audit: `docs/games/coins/EMBED_MODE_PARITY_AUDIT_2026-05-25.md`. |

## P1 - Prodotto/UX

| Area | Stato | Prossima azione |
| --- | --- | --- |
| Site V3 / Module Composer | WP3 Admin Builder MVP e WP4 Public Renderer MVP implementati. WP5 prima tranche ha trasformato il renderer in moduli separati e collegato asset pubblici V1 senza promuovere il vecchio CMS v2 lab. | WP5 resta aperto per polish visual/prodotto su test Michele; WP6 deve cestinare `frontend-v2/`. |
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
