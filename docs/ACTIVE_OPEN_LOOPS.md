# CasinoKing Active Open Loops

Registro breve delle cose aperte che non devono restare affidate alla memoria
della singola AI.

## Regola

Quando un punto viene chiuso, aggiornare questo file nello stesso task o spiegare
perche' non serve piu'. Non sostituisce i piani operativi; serve da cruscotto.

## P0 - Da Non Dimenticare

| Area | Stato | Prossima azione |
| --- | --- | --- |
| Mines audio runtime | Non implementato. Esiste il piano, ma il gioco oggi non riproduce suoni. | Implementare asset kind audio, backoffice upload/preview, hook `useMinesSounds`, controlli mute/volume e test runtime. |
| Mines provider intro | Pianificato. Serve asset finale esterno. | Michele fornisce logo/intro/poster ottimizzati; poi BOOT-2 refactor staged + intro/fallback. |
| Mines How To Play Gate | Pianificato. | Implementare tre card pre-game con copy default/i18n e V2 "non mostrare piu'". |
| Mines runtime clock | Pianificato. | Implementare clock `HH:mm` ereditato da Site, con override Title solo se necessario. |
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
