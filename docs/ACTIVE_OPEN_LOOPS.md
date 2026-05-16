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
| BOOT-2A Game Boot Shell | Chiuso: `GameBootShell`, helper route/storage, `useGameLaunchContext`, `useGameAudioPreferences` e separazione `MinesStandalone` wrapper / `MinesGameplay` sono documentati. Target line count rivisto a 2000; `mines-standalone.tsx` e' a 1939 righe con `wc -l`. | Non riaprire BOOT-2A. Per il secondo gioco partire da `docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`; debiti residui in `docs/MINES_PENDING_TOPICS.md`. |
| Mines browser full smoke legacy debt | Aperto: full browser smoke legacy ha 11 failure note residue fuori scope BOOT-2A.5. | Pulire prima del rilascio o quando diventa bloccante per un altro work package. |
| Mines audio runtime | V1 implementato: asset kind audio, backoffice Sounds, hook `useMinesSounds`, controlli FX mute/volume e runtime events. | Caricare asset audio reali sui Title e fare QA uditiva; musica resta fuori scope. |
| Mines provider intro | BOOT-2B V1 implementato: real mode Table Balance Gate prima dell'intro, preload media, video MP4 8s, poster fallback e progress bar frontend. BOOT-2A refactor shell completato e documentato. | Testare intro desktop/mobile; ottimizzare video mobile; poi decidere se mantenere 8s sempre o introdurre policy V2 sessionStorage/intro breve. |
| Mines How To Play Gate | V1 implementato dopo intro e prima del gameplay, con copy default/i18n. | QA copy/layout mobile; V2 "non mostrare piu'" solo se diventa fastidioso. |
| Mines runtime clock | V1 implementato come clock compatto `HH:mm` Europe/Rome. | Spostare su Site config quando esiste il contratto platform; override Title solo se necessario. |
| Mines skin estesa | Chiuso: MSK V2 mergeato in `main` il 2026-05-16 con backend asset/theme, upload backoffice per title logo/background/cell texture, runtime player wiring e WCAG publish gate. | Mantenere `mines_classic` come baseline read-only; nuove evoluzioni skin richiedono piano CTO dedicato. |

## P1 - Prodotto/UX

| Area | Stato | Prossima azione |
| --- | --- | --- |
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
