# CasinoKing Active Open Loops

Registro breve delle cose aperte che non devono restare affidate alla memoria
della singola AI.

## Regola

Quando un punto viene chiuso, aggiornare questo file nello stesso task o spiegare
perche' non serve piu'. Non sostituisce i piani operativi; serve da cruscotto.

## P0 - Da Non Dimenticare

| Area | Stato | Prossima azione |
| --- | --- | --- |
| Mines V1 | Accettata: baseline BOOT-2A.0 congelata su `main`; baseline visual stabilizzata in BOOT-2A.0.5 usando `mines_classic` read-only. | Mantenere baseline verde durante BOOT-2A.3; eventuali modifiche a configurazione/asset `mines_classic` richiedono refresh dedicato delle baseline. |
| BOOT-2A Game Boot Shell | In esecuzione: BOOT-2A.0, BOOT-2A.0.5, BOOT-2A.1 e BOOT-2A.2 merged; 2/5 WP successivi merged after BOOT-2A.0. | Aprire BOOT-2A.3 da `main` aggiornato ed estrarre la shell visuale di boot. |
| Mines browser full smoke legacy debt | Aperto: full `test_mines_embed_browser_smoke.py` ha 14 failure legacy fuori scope BOOT-2A.1, tra endpoint admin vecchio, launcher/home, table gate real e aspettative mobile obsolete. | Pulire o riclassificare prima di BOOT-2A.4, quando l'estrazione gameplay richiedera' contratto verde su tutto il file. |
| Mines audio runtime | V1 implementato: asset kind audio, backoffice Sounds, hook `useMinesSounds`, controlli FX mute/volume e runtime events. | Caricare asset audio reali sui Title e fare QA uditiva; musica resta fuori scope. |
| Mines provider intro | BOOT-2B V1 implementato: real mode Table Balance Gate prima dell'intro, preload media, video MP4 8s, poster fallback e progress bar frontend. BOOT-2A refactor shell e' in esecuzione dopo baseline congelata. | Testare intro desktop/mobile; ottimizzare video mobile; poi decidere se mantenere 8s sempre o introdurre policy V2 sessionStorage/intro breve. |
| Mines How To Play Gate | V1 implementato dopo intro e prima del gameplay, con copy default/i18n. | QA copy/layout mobile; V2 "non mostrare piu'" solo se diventa fastidioso. |
| Mines runtime clock | V1 implementato come clock compatto `HH:mm` Europe/Rome. | Spostare su Site config quando esiste il contratto platform; override Title solo se necessario. |
| Mines skin estesa | SKIN-X0 audit fatto, SKIN-X1+ non implementati. | Backend kind/caps + runtime + backoffice per title logo, game area background, cell face-down background e button presets. |

## P1 - Prodotto/UX

| Area | Stato | Prossima azione |
| --- | --- | --- |
| Site mockup/redesign | Banner media CMS-2D completato; redesign visuale sito non fatto. | Raccogliere reference, scegliere direzione Premium Casino Lobby, produrre mockup prima del redesign. |
| Player account/cassa | Read model e UI cassa/storico gioco sono stati rifatti, ma validazione utente finale resta aperta. | Test utente su Cassa, Storico gioco, replay e compattezza; decidere eventuali correzioni. |
| Replay retention/storicizzazione | Concetto emerso, non progettato. | Piano futuro su retention/storicizzazione replay/report prima di produzione. |
| Nuovo gioco proprietario | Obiettivo macro futuro, non aperto come implementazione. | Chiudere prima runtime Mines/skin/audio/boot; poi disegnare nuovo engine con Game Adapter dedicato. |

## Chiarimenti Chiusi

| Punto | Esito |
| --- | --- |
| Banner sito caricabili | Implementato: `site_assets.homepage_banner`, admin upload/select/delete e render player con fallback. |
| BOOT-1 cashout reveal mine | Implementato: dopo cashout/auto-win il round e' chiuso e il frontend mostra le mine ricevute dal backend. |
| Assets locali `assets/` | Cartella di servizio non versionata; gli asset runtime entrano solo tramite registry o path pubblico dichiarato. |
