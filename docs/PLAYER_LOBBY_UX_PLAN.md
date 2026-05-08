# CasinoKing - Player Lobby UX Plan

## Stato

Piano operativo creato dopo Games overview, Site/Lobby Publishing e LOG
operativo.

Slice 1 implementata e rifinita in prima versione: lobby card professionali,
spotlight compatto, copy inglese, loading/empty/error state e CTA demo/real
basate su `GET /games/library`.

Slice 2A implementata: il backoffice apre preview demo tramite token admin
dedicato (`POST /admin/games/titles/{title_code}/preview-launch` +
`preview_token` su `/demo/launch`), non tramite bypass pubblico basato solo su
query string.

Slice 4 Visual QA completata in prima chiusura: catalogo locale ripulito dalle
varianti test pubblicate, CSS mobile rafforzato contro overflow di lobby copy,
nomi/codici lunghi e board Mines demo a 375px.

Aggiornamento visuale successivo:

- le card lobby usano un'area visual/board a dimensione fissa;
- i testi editoriali lunghi vengono limitati/clampati prima di poter allungare
  lo spazio icona;
- le description card sono tagliate lato frontend a una lunghezza massima
  compatta, mantenendo la source editoriale in `GET /games/library`.

Aggiornamento CMS-2C 2026-05-09:

- la lobby player legge anche `GET /site/home?site_code=casinoking` per il
  hero editoriale homepage/banner;
- `GET /games/library` resta la fonte delle card gioco, dello spotlight di
  fallback e delle CTA per la griglia;
- se `/site/home` e' vuoto o non disponibile, la lobby mantiene il fallback
  precedente senza errore player.

## Obiettivo

Rendere la lobby player una vista professionale e comprensibile dei giochi
pubblicati, senza trasformarla in un CMS e senza duplicare le regole di
pubblicazione del backoffice.

La lobby deve mostrare al player:

- quali varianti sono disponibili;
- quali modalita' sono disponibili per ogni variante: demo, real o entrambe;
- il nome e la descrizione editoriali decisi da Site/Lobby Publishing;
- CTA chiare per demo e real;
- stati empty/loading/error leggibili.

## Principio guida

La lobby player consuma, non decide.

```text
Games backoffice
  crea e configura varianti

Site/Lobby Publishing
  decide visibilita', demo/real, ordine, featured e metadata lobby

Player lobby
  legge GET /api/v1/games/library e renderizza cio' che riceve
```

La lobby non deve contenere logica editoriale parallela, hardcoding di varianti
o regole proprie per includere/escludere Title.

## Utenti target

### Player anonimo

Vuole provare giochi in demo e capire quali richiedono login per il real play.

### Player autenticato

Vuole entrare rapidamente nella variante scelta, in demo o real se disponibile.

### Operatore backoffice

Vuole verificare che quanto pubblicato nel Site/Lobby backoffice appaia nello
stesso ordine e con gli stessi metadata.

## Fonte dati

Unica fonte dati per le card:

```text
GET /api/v1/games/library
```

Shape attuale rilevante:

```json
{
  "site": {
    "site_code": "casinoking",
    "display_name": "CasinoKing",
    "status": "active"
  },
  "titles": [
    {
      "title_code": "mines002a",
      "engine_code": "mines",
      "engine_display_name": "Mines",
      "display_name": "Mines 2000",
      "catalog_display_name": "Mines 2000",
      "description": "...",
      "demo_enabled": true,
      "real_enabled": true,
      "featured": false,
      "position": 2
    }
  ]
}
```

Regole gia' garantite dal backend:

- solo Title non-master;
- solo Title attivi;
- solo site/title/engine attivi;
- solo `lobby_visibility=visible`;
- almeno una tra demo e real abilitata;
- ordering da backend: featured, position, display name, title code.

Hardening launch implementato dopo Slice 1:

- per varianti non-master, il launch token pubblico richiede
  `lobby_visibility=visible`;
- `mode=demo` richiede `demo_enabled=true`;
- `mode=real` richiede `real_enabled=true`;
- i link diretti a varianti nascoste o a modalita' non abilitate vengono
  respinti dal backend, non solo nascosti dalla UI.

Preview admin:

- il master Mines e le varianti nascoste sono previewable dal backoffice solo
  con `preview_token` admin firmato;
- `preview=1` da solo non e' una autorizzazione backend;
- il master non entra comunque in `GET /games/library` e non e' pubblicabile
  come item lobby ordinario.

Regola master aggiornata:

- il launch pubblico richiede `title_code` esplicito e rifiuta ogni Title
  master con codice stabile `LAUNCH_REJECTED_MASTER`;
- i test che creano varianti pubblicate devono ripulire la pubblicazione
  Site/Lobby anche quando la variante resta referenziata da round/sessioni
  storiche.

## Architettura informativa target

### Livello 1 - Lobby shell

Contenuti:

- topbar player gia' esistente;
- header compatto della lobby;
- stato sintetico del catalogo;
- area giochi immediatamente visibile.

Il primo viewport deve far capire che siamo nella lobby giochi, non in una
landing page promozionale.

### Livello 2 - Featured / primary area

Se esistono Title `featured`, la lobby puo' evidenziarli con una card piu'
larga. Se non esistono featured, non va creato un finto featured hardcoded.

### Livello 3 - Game grid

Ogni card mostra:

- engine;
- display name lobby;
- descrizione lobby o fallback breve;
- modalita' disponibili;
- CTA demo se `demo_enabled`;
- CTA real se `real_enabled`;
- login CTA se real e player anonimo;
- title code solo come dato secondario, non protagonista.

### Livello 4 - Stati

Stati obbligatori:

- loading catalog;
- empty catalog;
- API error;
- titolo demo-only;
- titolo real-only;
- titolo demo+real;
- player anonimo con real disponibile.

## Lancio giochi

### Demo

Link corrente:

```text
/mines?title_code={title_code}&mode=demo
```

Il componente Mines usa il flusso demo anonimo esistente:

- `POST /demo/token`;
- `POST /demo/launch`;
- `X-Game-Launch-Token`;
- nessun ledger o platform round reale.

### Real

Link corrente:

```text
/mines?title_code={title_code}
```

Se il player non e' autenticato, la CTA real manda a login.

Decisione Slice 1:

- non introdurre redirect intent o deep-link post-login;
- non cambiare il flusso launch token real;
- mantenere il boundary attuale.

Un redirect intent post-login si valuta in una slice successiva.

## Linee visuali

- palette scura coerente con il sito;
- niente grandi blocchi grigio chiaro;
- card compatte ma riconoscibili;
- contenuto sopra decorazione;
- visual del gioco concreto: per Mines usare un motivo board/diamond CSS,
  senza introdurre asset esterni obbligatori;
- copy nuovo in inglese;
- nessun testo tecnico come contenuto principale.

## Sequenza implementativa

### Slice 1 - Lobby cards professionali

Stato: implementata in prima versione.

Scope:

- creare `docs/PLAYER_LOBBY_UX_PLAN.md`;
- aggiornare `PlayerLobbyPage`;
- sostituire copy italiano ancora presente nella lobby;
- rendere card e stati piu' chiari;
- mantenere `GET /games/library` come unica fonte;
- mantenere link demo/real esistenti;
- aggiornare CSS scoped delle classi player lobby.

Accettazione Slice 1:

- `npx tsc --noEmit` passa;
- `npm run build` passa;
- la lobby mostra solo Title ricevuti da `/games/library`;
- master non renderizzati;
- demo CTA usa `mode=demo`;
- real CTA apre Mines se autenticato o Login se anonimo;
- copy nuovo in inglese;
- desktop e mobile senza overlap evidente.

### Slice 2 - Launch intent polish

Stato:

- preview token admin dedicato implementato in Slice 2A;
- messaggio saldo insufficiente e popup errori Mines applicati come pattern
  progressivo, senza refactor globale.

Scope ancora possibile:

- conservare l'intento real dopo login;
- distinguere visivamente "Play real" da "Login to play";
- messaggi player-friendly se un launch viene respinto dal backend;
- nessun refactor globale errori.

Trigger:

- dopo smoke manuale della Slice 1;
- se l'esperienza anonimo -> login -> gioco risulta troppo spezzata.

### Slice 3 - Lobby sections

Scope possibile:

- se il catalogo cresce, separare featured, all games e recently added;
- filtri leggeri per engine o mode;
- nessun CMS e nessuna regola editoriale frontend.

Trigger:

- almeno due engine o molte varianti pubblicate.

### Slice 4 - Visual QA

Stato: completata in prima chiusura dopo smoke E2E 2026-05-07.

Scope:

- screenshot desktop/tablet/mobile;
- verifica card lunghe con nomi/descrizioni reali;
- palette e contrasto;
- test manuale CTA demo/real.

Chiusura applicata:

- varianti test locali `mines_test_*`, `mines_auth_*` e `mines_flow_*` rimosse da
  `site_titles`, con `game_titles` inattivi quando servono ancora alle FK
  storiche;
- helper test aggiornato per non lasciare varianti test pubblicate se la
  cancellazione completa e' bloccata da round/sessioni;
- player lobby mobile 375px verificata senza overflow orizzontale;
- Mines demo mobile 375px verificata con board centrata e contenuta.
- area visual/board delle card resa a dimensione fissa; titoli, codici e
  description lunghe non devono piu' allungare lo spazio icona.

## Fuori scope

- creazione o duplicazione giochi;
- configurazione Title;
- pubblicazione lobby;
- upload asset;
- payout/RTP/RNG/fairness;
- wallet/ledger;
- CMS homepage;
- i18n foundation;
- produzione/external adapter.

## Relazione con piani attivi

- `BACKOFFICE_GAMES_UX_REORGANIZATION_PLAN.md`: crea/configura varianti.
- `SITE_LOBBY_PUBLICATION_PLAN.md`: decide cosa appare in lobby.
- `GAME_ADMIN_CHANGE_LOG_PLAN.md`: traccia modifiche backoffice, non gameplay.
- `PRODUCT_UX_EXECUTION_SEQUENCE_PLAN.md`: ordina questo cantiere dopo LOG.
- `PRODUCT_COPY_ENGLISH_CLEANUP_PLAN.md`: la lobby toccata in questo cantiere
  viene bonificata in inglese, senza introdurre i18n.

## Quando testare manualmente

Dopo Slice 1 e' utile un test manuale reale:

1. Site/Lobby: rendere visibile una variante demo+real.
2. Player lobby: verificare card, ordine e copy.
3. CTA Demo: aprire il Title corretto in demo.
4. CTA Real: da anonimo deve portare a login; da autenticato deve aprire il
   Title corretto.

Prima di questo punto non e' necessario fermarsi a testare manualmente.
