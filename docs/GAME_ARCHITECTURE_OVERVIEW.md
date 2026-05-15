# Game Architecture Overview

Documento di progetto per review CTO.

## Stato del documento

- Tipo: overview architetturale e glossario operativo.
- Stato: bozza pronta per review CTO.
- Ambito: Casino Platform, Game Runtime Layer, Mines, RNG/fairness, wallet/ledger boundary, frontend player/admin.
- Non sostituisce: `docs/SOURCE_OF_TRUTH.md`, `docs/ARCHITECTURE_ATLAS_MINES.md`, `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`, documenti canonici Word e allegati runtime.

## Perche' esiste questo documento

Il progetto ha raggiunto un punto in cui "gioco", "piattaforma", "CMS", "runtime" e "integrazione esterna" vengono nominati spesso, ma non sempre con lo stesso significato.

Questo documento serve a fissare una lingua comune prima di aprire altri cantieri:

1. spiegare che cosa e' oggi la parte game di CasinoKing;
2. distinguere la piattaforma casino dal modulo gioco proprietario;
3. dare un nome al layer di integrazione tra gioco e piattaforma;
4. chiarire cosa significa "monolite" in questo progetto;
5. indicare quali confini non vanno violati quando si aggiungono giochi, UX o CMS.

La ragione pratica e' semplice: se il confine resta implicito, ogni nuova feature rischia di tirarsi dietro wallet, ledger, launch, sessioni e frontend in modo confuso.

## Naming proposto

| Nome | Significato | Owner |
| --- | --- | --- |
| Casino Platform | Il core casino: auth, users, wallet, ledger, catalogo, site, lobby, admin, audit, launch, access session, table session e platform rounds. | Piattaforma |
| Game Runtime Layer | Il layer platform-owned che permette a un gioco di essere lanciato, autorizzato, contabilizzato e chiuso. Include launch token, access session, table session, platform rounds e settlement. | Piattaforma |
| Frontend Game Boot Runtime | Il runtime frontend comune che prepara una schermata gioco: route/query, storage locale, stato boot, theme shell, intro/how-to-play, overlay runtime e preferenze audio. Non possiede wallet, ledger, RNG, payout o settlement. | Frontend platform/game |
| Game Adapter | Il contratto tecnico usato dal gioco per chiedere alla piattaforma aperture round, settlement, stato tavolo e chiusure. Oggi e' in-process (`PlatformGameClient`), domani potra' avere implementazione HTTP. | Boundary Platform/Game |
| Game Module | Il gioco proprietario vero e proprio. Per ora Mines: API, engine, stato round, RNG/fairness, payout runtime, frontend dedicato. | Gioco |
| RGS | Concetto architetturale: il server autorevole del gioco. Oggi non e' un servizio fisico separato; nel caso Mines coincide concettualmente con API+engine+RNG/fairness+payout runtime. | Concetto futuro |
| Site CMS | Area editoriale per decidere cosa vede il player su sito, lobby, homepage, banner e contenuti pubblici. | Backoffice/CMS |
| Game Catalog CMS | Area backoffice per Engine/Title/Site, configurazione varianti, pubblicazione, asset e copy del gioco. | Backoffice/Game Ops |

Decisione proposta: usare "Game Adapter" per il layer di integrazione game -> platform. "Piattaforma" da sola e' troppo generica; "Game Adapter" dice esattamente che e' un contratto al confine.

## Lettura ad alto livello

CasinoKing oggi e' un modular monolith: un solo repository e un solo backend applicativo, ma con domini gia' separati logicamente.

```text
Player Browser
  -> Frontend Platform
     -> Lobby / Account / Auth
     -> Mines Frontend

Backend CasinoKing
  -> Casino Platform
     -> Auth / Users
     -> Wallet / Ledger
     -> Game Runtime Layer
     -> Catalog / Site / Admin / Audit

  -> Game Module: Mines
     -> Mines API
     -> Mines Engine
     -> RNG / Fairness
     -> Payout Runtime
     -> Presentation / Theme / i18n

Frontend Game Shell
  -> GameBootShell
     -> route/storage/launch context
     -> title theme provider
     -> provider intro / how-to-play / runtime overlays
     -> MinesGameplay or future NewGameGameplay
```

Il monolite non e' il problema in se'. Il problema nasce solo se il codice del gioco torna a possedere direttamente responsabilita' della piattaforma.

La regola architetturale resta:

- la piattaforma possiede soldi, identita', sessioni di accesso, ledger, audit e pubblicazione;
- il gioco possiede board, stato round, reveal, payout potenziale, RNG e fairness;
- il frontend mostra e invia azioni, ma non decide mai outcome, board, payout o saldo.

## Lettura a medio livello: flusso real mode

### 1. Pubblicazione e lobby

```text
Admin Backoffice
  -> configura Engine/Title/Site
  -> pubblica config Title
  -> pubblica visibilita' lobby
  -> audit log operativo

Player Lobby
  -> legge catalogo pubblicato
  -> mostra solo Title pubblicabili
  -> lancia con title_code esplicito
```

Il `title_code` e' parte dell'identita' commerciale del gioco. Non e' un dettaglio estetico: serve a sapere quale variante e' stata lanciata, pubblicata, configurata e rendicontata.

### 2. Launch

```text
Lobby CTA real
  -> Game Runtime Layer emette/valida launch token
  -> crea access session
  -> crea table session
  -> apre Mines con title_code/site_code
```

Regole:

- un master non e' lanciabile pubblicamente;
- richieste senza `title_code` devono fallire;
- il frontend puo' decidere il redirect o il messaggio, non puo' inventare un default.

### 3. Start round

```text
Mines Frontend
  -> POST /games/mines/start
     -> Mines API
        -> Mines Engine valida richiesta gioco
        -> Game Adapter open_round(...)
           -> Casino Platform valida table session e wallet
           -> Platform round
           -> ledger transaction bet
           -> wallet snapshot update
        -> Mines crea round tecnica
        -> RNG/fairness prepara board server-side
```

La parte critica e' `open_round(...)`: deve restare atomica. Non va spezzata in "validate" + "reserve" separati perche' in concorrenza riaprirebbe il rischio di superare budget o saldo.

### 4. Reveal

```text
Mines Frontend
  -> POST /games/mines/reveal
     -> Mines API
        -> Mines Engine legge round server-side
        -> decide safe/mine
        -> aggiorna stato round
        -> restituisce solo lo stato visibile al player
```

Il frontend non conosce la board completa prima del tempo. La reveal e' sempre server-authoritative.

### 5. Cashout o perdita

```text
Cashout
  -> Mines Engine calcola payout da runtime ufficiale
  -> Game Adapter settle_win(...)
  -> Casino Platform scrive ledger win e aggiorna wallet

Mine hit
  -> Mines Engine chiude round lost
  -> Game Adapter settle_loss(...)
  -> Casino Platform consuma la perdita gia' riservata
```

I payout non devono essere hardcoded in UI o in formule improvvisate. Devono derivare dagli allegati runtime ufficiali e restare con RTP > 90% e < 100% nelle configurazioni supportate.

## Lettura a basso livello, senza scendere nel codice

### Casino Platform

Responsabilita':

- autenticazione player/admin;
- ruoli e permessi;
- wallet snapshot materializzato;
- ledger double-entry;
- piano dei conti;
- idempotenza su operazioni economiche;
- catalogo Engine/Title/Site;
- pubblicazione Site/Lobby;
- launch token;
- access session;
- table session;
- platform rounds;
- audit finanziario e operativo;
- reportistica e riconciliazione.

Non deve delegare al gioco:

- saldo;
- bonus/adjustment;
- ledger posting;
- accounting round;
- riconciliazione;
- autorizzazione economica.

### Game Runtime Layer

E' la parte della piattaforma che rende giocabile un titolo.

Responsabilita':

- emettere e validare launch token;
- legare player, site, title e game code;
- aprire access session;
- creare table session con budget massimo;
- aprire platform round;
- registrare bet/win/loss/void;
- chiudere sessioni in modo idempotente;
- proteggere retry e concorrenza;
- fornire al gioco un contratto stabile tramite Game Adapter.

Questo layer e' il punto giusto per preparare future integrazioni esterne, non il frontend e non il modulo Mines.

### Game Adapter

Il Game Adapter e' il nome proposto per il boundary tecnico.

Interfaccia concettuale:

```text
GameAdapter
  open_round(...)              # atomico: validate + reserve + debit + ledger bet
  settle_win(...)              # accredita payout e chiude economicamente
  settle_loss(...)             # consuma perdita riservata
  void_round(...)              # reversal/void amministrativo
  get_table_session_state(...) # read-only per UI/status
```

Stato attuale:

- implementazione in-process (`PlatformGameClient`);
- nessun servizio HTTP separato;
- sufficiente per sviluppo locale;
- separazione fisica rinviata al momento in cui si vorra' pubblicare o integrare provider esterni reali.

Vincolo:

- non esporre `validate_table_session` come operazione separata;
- non fare scrivere al gioco direttamente wallet/ledger;
- non creare doppio path economico "per comodita'".

### Mines Game Module

Responsabilita':

- API di gioco;
- engine server-authoritative;
- stato round Mines;
- grid, mine count, safe reveals;
- reveal safe/mine;
- potenziale payout;
- cashout game-side;
- RNG e fairness;
- configurazione runtime per Title;
- skin/theme/i18n del gioco;
- frontend Mines.

Non responsabilita':

- non possiede il wallet;
- non scrive ledger direttamente come nuova feature;
- non decide se il player puo' spendere soldi senza passare dal Game Adapter;
- non rende una variante pubblica senza Site/Lobby Publishing.

### RNG e fairness

Mines deve restare server-authoritative.

La sequenza corretta e':

1. il server prepara o determina la board secondo il modello fairness;
2. il player invia solo indici cella o azioni;
3. il server decide outcome sulla base dello stato round;
4. il frontend riceve stato visibile, payout potenziale e messaggi;
5. eventuali dati fairness vengono esposti in lettura, non usati dal client per decidere outcome.

La modifica UX proposta per la mine hit, cioe' rivelare subito tutte le mine quando il player clicca una mina, e' coerente con questo modello se resta solo presentazionale: il backend comunica la round persa e le posizioni rivelabili, il frontend mostra tutte le mine insieme senza cambiare payout, RNG, board o settlement.

### Frontend player

Responsabilita':

- lobby pubblica;
- login/register/account;
- apertura gioco;
- boot runtime comune per giochi proprietari;
- schermata table entry;
- UI Mines;
- feedback errori;
- estratto conto e storico sessioni;
- responsive/mobile.

Non responsabilita':

- calcolare saldo autorevole;
- calcolare payout autorevole;
- decidere mine/safe;
- creare default di `title_code`;
- bypassare errore di pubblicazione.

### Frontend Game Boot Runtime

Responsabilita':

- normalizzare i parametri URL di lancio gioco;
- leggere storage locale legacy tramite helper dedicati;
- rappresentare lo stato `boot`, `launch_ready`, `runtime_ready` e `fatal`;
- montare theme provider, Table Balance Gate, provider intro, How To Play,
  error dialog e overlay runtime;
- esporre preferenze audio FX comuni al gameplay;
- montare il gameplay solo quando il runtime e' pronto.

Non responsabilita':

- non decide outcome;
- non calcola payout;
- non muove wallet o ledger;
- non sostituisce Game Adapter o Game Runtime Layer backend;
- non importa componenti Mines nella parte comune.

Stato dopo BOOT-2A: Mines usa `GameBootShell`, `useGameLaunchContext`,
helper route/storage e `useGameAudioPreferences`; `MinesStandalone` resta wrapper
Mines-specific e monta `MinesGameplay`. Il dettaglio operativo vive in
`docs/ARCHITECTURE_ATLAS_GAME_RUNTIME.md`.

### Frontend admin/backoffice

Responsabilita':

- gestire Engine/Title/Site;
- pubblicare configurazioni;
- pubblicare lobby;
- gestire copy, i18n, theme e asset;
- mostrare audit operativo;
- supportare preview admin.

Non responsabilita':

- correggere runtime finanziario con update diretti;
- creare scorciatoie che saltano publish gate;
- mischiare audit operativo e ledger-linked admin actions.

## Che cosa significa "monolite game"

Oggi il rischio non e' avere un repository unico. Il rischio e' avere un confine mentale debole.

Monolite accettabile:

- codice nello stesso repo;
- moduli separati;
- dipendenze esplicite;
- boundary `Game Adapter`;
- test di concorrenza/idempotenza;
- documentazione aggiornata.

Monolite pericoloso:

- Mines che scrive direttamente nuove logiche wallet/ledger;
- frontend che applica default magici su Title;
- publish e launch mescolati;
- sessioni gioco senza ownership chiara;
- adapter bypassato per risolvere rapidamente bug economici;
- config di gioco che cambia payout/RTP senza runtime ufficiale.

## Stato attuale

| Area | Stato |
| --- | --- |
| Mines proprietario | Implementato come primo Game Module. |
| Game Adapter | Presente in-process, non HTTP. |
| Launch token | Obbligatorio sui flussi operativi Mines. |
| Table session | Implementata come limite sessione platform-owned. |
| Wallet/ledger | Platform-owned, double-entry, snapshot materializzato. |
| Demo mode | Separato da ledger/platform rounds real. |
| Title/Site publishing | Implementato e usato dalla lobby. |
| Admin audit log operativo | Implementato per modifiche non finanziarie. |
| Frontend Game Boot Runtime | BOOT-2A completato: shell e helper comuni disponibili per preparare un secondo gioco senza copiare `MinesStandalone`. |
| RGS separato | Non presente come servizio fisico; concetto futuro. |

## Target ragionevole

Nel breve:

- mantenere il modular monolith;
- rafforzare documentazione e naming;
- non introdurre adapter HTTP finche' non serve davvero;
- continuare con slice UX/CMS piccole e testabili;
- evitare nuove feature economiche senza guardrail finanziari.

Nel medio:

- rendere il Game Adapter abbastanza stabile da supportare un secondo gioco proprietario;
- usare `GameBootShell` come base frontend del secondo gioco, lasciando gameplay
  e decision flow specifici al gioco finche' non esiste evidenza di riuso;
- modellare nel CMS la differenza tra gioco proprietario e gioco esterno;
- disegnare contratti locali/mock per provider esterni;
- migliorare account player e reporting senza cambiare ledger.

Nel lungo:

- se si andra' in produzione o integrazione esterna, introdurre `HttpPlatformGameClient`, sicurezza server-to-server, contract test e osservabilita' completa;
- solo allora valutare separazione fisica di servizi/repository.

## Decisioni da validare con CTO

| Decisione | Proposta |
| --- | --- |
| Nome del boundary | Usare "Game Adapter". |
| Nome del layer platform di gioco | Usare "Game Runtime Layer". |
| RGS | Trattarlo come concetto, non come servizio attuale. |
| Separazione fisica | Rinviare finche' non c'e' go-live o integrazione reale. |
| Nuovi giochi proprietari | Devono usare Game Adapter e Game Runtime Layer, non integrare wallet/ledger a mano. |
| Modifica reveal mine hit | Ammessa come UX/game presentation se non tocca RNG, payout, settlement o ledger. |

## Criteri di accettazione del modello

Il modello e' rispettato se:

- ogni movimento economico passa dalla piattaforma;
- ogni round real ha identita' Title/Site quando applicabile;
- il gioco resta server-authoritative;
- il frontend non decide outcome;
- il Game Adapter resta il punto di passaggio per settlement;
- demo e real restano separati;
- le modifiche editoriali passano da publish/audit.

Il modello e' violato se:

- una nuova feature Mines aggiorna saldo o ledger fuori dai service platform;
- una variante master diventa lanciabile pubblicamente;
- il frontend inventa `title_code` o fallback silenti;
- un provider esterno puo' scrivere direttamente sui wallet;
- una config di CMS altera payout/RTP senza runtime ufficiale e test.
