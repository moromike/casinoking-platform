# CasinoKing - Product UX Execution Sequence Plan

## Stato

Piano operativo da validare prima di implementare.

Questo documento coordina i prossimi cantieri UX/prodotto dopo la prima fase
funzionale di F7. Non sostituisce i piani specifici gia' esistenti; li ordina,
li collega e introduce il nuovo cantiere trasversale Copy/i18n.

## Decisione di sequenza

Ordine proposto da Michele e confermato come coerente:

```text
0. Product copy / i18n foundation
1. Games overview UX
2. Error and notification system
3. Game admin change log / audit leggero
4. Player lobby / game cards
5. Site / Lobby backoffice
```

Nota: il punto 0 e' stato inserito come prerequisito trasversale. Non era nella
lista originale 2-3-4-5-1, ma evita di rifare copy e label due volte durante i
refactor.

## Perche' questo ordine

### 0 - Product copy / i18n foundation

Spiegazione:

Prima di rifare schermate e componenti, bisogna decidere come gestire testi e
lingua. Se si ridisegna Games, poi errori, poi lobby, ma ogni area continua ad
avere stringhe hardcoded sparse, il progetto accumula debito immediato.

Output atteso:

- English-first come regola prodotto;
- copy layer minimo;
- tassonomia chiavi;
- confine UI copy / contenuto DB;
- piano di migrazione progressivo.

Documento guida:

- `docs/PRODUCT_COPY_AND_I18N_FOUNDATION_PLAN.md`

### 1 - Games overview UX

Spiegazione:

La sezione Games e' il cuore operativo del modello Engine / Title / Site. Se
questa vista resta tecnica e confusa, ogni altra azione su varianti, preview e
configurazione sara' difficile da capire. Inoltre il refactor Games e' gia'
iniziato: conviene consolidarlo prima di aggiungere altri layer.

Output atteso:

- elenco master/varianti chiaro;
- duplicazione nel livello elenco/categoria;
- dettaglio variante separato;
- master bloccato e previewable;
- azioni principali comprensibili.

Documento guida:

- `docs/BACKOFFICE_GAMES_UX_REORGANIZATION_PLAN.md`

### 2 - Error and notification system

Spiegazione:

Mines ora ha un primo dialog errore migliore, ma il prodotto ha bisogno di uno
standard comune. Errori, conferme e warning sono parte della UX, non dettagli
secondari. Vanno progettati dopo la fondazione copy, cosi' i messaggi sono gia'
English-first e key-based.

Output atteso:

- pattern unico per errori player-facing;
- pattern per conferme/warning backoffice;
- mapping codici API -> copy prodotto;
- design coerente per dialog/toast/banner;
- regole su quando bloccare UI e quando mostrare messaggio non bloccante.

Documento da creare quando si apre il cantiere:

- `docs/ERROR_NOTIFICATION_SYSTEM_PLAN.md`

### 3 - Game admin change log / audit leggero

Spiegazione:

Dopo avere chiarito Games e notifiche, ha senso introdurre un LOG backoffice.
Non deve tracciare gameplay, wallet o ledger: deve solo dare visibilita' alle
modifiche di configurazione e pubblicazione. Farlo prima della UX Games sarebbe
prematuro, perche' non sarebbe ancora chiaro dove mostrarlo e quali azioni
sono davvero primarie.

Output atteso:

- menu/sezione LOG separata;
- eventi backoffice gioco/lobby;
- storico leggibile da operatori;
- niente impatto su round, wallet, ledger o accounting.

Documento da creare quando si apre il cantiere:

- `docs/GAME_ADMIN_CHANGE_LOG_PLAN.md`

### 4 - Player lobby / game cards

Spiegazione:

Quando Games e notifiche sono piu' solide, si passa alla superficie player. La
lobby pubblica deve mostrare giochi e varianti come prodotto, non come record
tecnici. Questo punto deve precedere il grande polish del Site/Lobby backoffice,
perche' il backoffice deve governare una esperienza player gia' definita.

Output atteso:

- card giochi professionali;
- CTA demo/real chiare;
- stati hidden/demo/real coerenti;
- copy inglese;
- preview reale dei giochi pubblicati;
- migliore uso dello spazio nella homepage/lobby.

Documento guida:

- `docs/SITE_LOBBY_PUBLICATION_PLAN.md` per il confine publishing;
- atlas Platform/Frontend per la lobby player.

Documento da creare quando si apre il cantiere:

- `docs/PLAYER_LOBBY_UX_PLAN.md`

### 5 - Site / Lobby backoffice

Spiegazione:

Questa area va fatta dopo la lobby player, perche' il backoffice Site deve
gestire cio' che il player vede. Se la player lobby non e' ancora definita, la
vista backoffice rischia di essere una tabella tecnica oppure un CMS troppo
generico. Tenerla ultima permette di costruire una UI compatta e professionale
con un perimetro chiaro.

Output atteso:

- gestione leggera di cosa appare sul sito;
- visibilita' demo/real;
- ordinamento;
- display name/description;
- preview alimentata da `GET /games/library`;
- niente configurazione gioco dentro Site.

Documento guida:

- `docs/SITE_LOBBY_PUBLICATION_PLAN.md`

## Stato attuale sintetico

### Gia' fatto

- Master Mines bloccato e previewable.
- Varianti Mines duplicabili, rinominabili e configurabili.
- Player title-aware in demo e real.
- Pubblicazione demo/real per varianti.
- Prima separazione elenco/dettaglio Games.
- Prima vista Site/Lobby.
- Popup errore Mines iniziale.
- Compattazione editor Mines: Grid, Rules, Labels, Theme, Assets.

### Non ancora fatto

- Copy layer English-first.
- Traduzione sistematica UI in inglese.
- UX Games veramente finale per operatori.
- Notification system globale.
- LOG/audit leggero backoffice.
- Lobby player professionale.
- Site/Lobby backoffice compatto e maturo.

## Piano dettagliato per milestone

### Milestone 0 - Copy/i18n foundation

Obiettivo:

Preparare il progetto a diventare English-first senza aprire subito un sistema
multilingua completo.

Azioni:

- creare copy layer frontend;
- definire chiavi semantiche;
- introdurre glossario minimo;
- migrare una prima piccola area;
- aggiungere regola di sviluppo per nuove stringhe.

Accettazione:

- `tsc --noEmit` passa;
- nessun language switcher;
- nessuna route locale;
- almeno una area usa il copy layer;
- documento copy approvato dal CTO.

Cosa potrai fare dopo:

- iniziare a migrare schermate in inglese in modo controllato;
- chiedere nuove UI gia' English-first.

Cosa non potrai ancora fare:

- cambiare lingua da UI;
- avere contenuti DB multilingua;
- dichiarare completata la traduzione del prodotto.

### Milestone 1 - Games overview UX

Obiettivo:

Rendere la gestione giochi comprensibile per operatori non tecnici al 100%.

Azioni:

- rivedere Games Overview;
- separare categoria Mines da dettaglio variante;
- portare duplicazione nella vista elenco/categoria;
- rendere master e varianti visivamente distinti;
- usare copy inglese da layer copy per label/azioni nuove.

Accettazione:

- smoke admin: Games -> Mines -> crea variante -> variante appare in lista;
- smoke admin: apri variante -> detail separato -> torna elenco;
- master non modificabile;
- nessuna gestione lobby dentro detail;
- nessun endpoint nuovo salvo decisione esplicita.

Cosa potrai fare dopo:

- capire quali giochi/varianti esistono;
- creare varianti dal posto corretto;
- aprire dettaglio per configurare.

Cosa non potrai ancora fare:

- creare engine nuovi;
- editare engine non-Mines;
- usare Games come CMS sito;
- vedere LOG storico completo.

### Milestone 2 - Error and notification system

Obiettivo:

Trasformare errori e messaggi in un sistema coerente, non singoli fix.

Azioni:

- creare piano dedicato;
- classificare messaggi: error, warning, success, info, confirmation;
- definire componenti/pattern;
- mappare codici API principali;
- migrare Mines dialog come primo caso;
- estendere a player lobby e backoffice dove utile.

Accettazione:

- errori user-facing non espongono messaggi tecnici grezzi;
- copy in inglese da chiavi;
- dialog bloccante usato solo quando serve;
- toast/banner usati per feedback non bloccanti;
- test/smoke principali passano.

Cosa potrai fare dopo:

- vedere errori piu' professionali;
- avere messaggi coerenti tra player e backoffice;
- aggiungere nuovi messaggi senza copy hardcoded.

Cosa non potrai ancora fare:

- avere audit completo degli errori;
- cambiare lingua;
- risolvere automaticamente errori backend.

### Milestone 3 - Game admin change log / audit leggero

Obiettivo:

Dare visibilita' alle modifiche backoffice gioco/lobby senza toccare accounting.

Azioni:

- creare piano dedicato;
- decidere eventi;
- decidere storage;
- decidere UI LOG;
- registrare azioni backoffice gioco/lobby;
- mostrare elenco filtrabile.

Eventi candidati:

- variant created;
- variant renamed;
- config draft saved;
- config published;
- theme draft saved;
- theme published;
- asset uploaded/deleted;
- lobby publication changed.

Accettazione:

- LOG separato da gameplay e finance;
- eventi leggibili da operatori;
- ogni evento contiene actor, timestamp, action, target, summary;
- nessun impatto su wallet/ledger/platform rounds;
- nessun logging di payload sensibili non necessario.

Cosa potrai fare dopo:

- vedere chi ha cambiato una variante;
- vedere quando una config e' stata pubblicata;
- ricostruire modifiche operative base.

Cosa non potrai ancora fare:

- usare il LOG come audit finanziario;
- fare rollback automatico;
- tracciare ogni round/spin gameplay;
- sostituire ledger o admin action finanziarie.

### Milestone 4 - Player lobby / game cards

Obiettivo:

Far apparire la lobby player come prodotto reale, non come debug visuale del
catalogo.

Azioni:

- creare piano dedicato;
- ridisegnare game card;
- chiarire CTA Demo/Real;
- definire stati disponibili/non disponibili;
- usare immagini/asset coerenti;
- usare copy inglese;
- verificare desktop/mobile.

Accettazione:

- lobby legge sempre `GET /games/library`;
- varianti visibili appaiono con display name corretto;
- demo/real lanciano il title corretto;
- master non appare come item ordinario;
- layout professionale e responsivo.

Cosa potrai fare dopo:

- vedere varianti pubblicate come giochi nella lobby;
- lanciare demo/real dal sito con title corretto;
- valutare l'esperienza player prima del backoffice Site finale.

Cosa non potrai ancora fare:

- gestire homepage come CMS completo;
- programmare pubblicazioni future;
- gestire contenuti multilingua da UI.

### Milestone 5 - Site / Lobby backoffice

Obiettivo:

Rendere la gestione lobby compatta e professionale, separata dalla config gioco.

Azioni:

- rivedere layout Site/Lobby;
- separare disponibili / visibili;
- introdurre preview coerente con player lobby;
- gestire posizione/ordine;
- gestire demo/real;
- gestire display name/description;
- usare copy inglese.

Accettazione:

- Site/Lobby non crea varianti;
- Site/Lobby non modifica config Mines;
- preview usa stessa fonte della lobby player;
- salvataggi persistono;
- layout compatto, senza spreco di spazio.

Cosa potrai fare dopo:

- decidere cosa appare sul sito;
- ordinare giochi;
- abilitare demo/real;
- modificare nome/descrizione lobby.

Cosa non potrai ancora fare:

- CMS completo;
- scheduling pubblicazioni;
- multilingua contenuti;
- gestione engine;
- produzione/external adapter.

## Dipendenze tra cantieri

```text
Copy/i18n foundation
  -> Games overview UX
  -> Error/notification system
  -> Game admin LOG
  -> Player lobby UX
  -> Site/Lobby backoffice UX
```

Dipendenze specifiche:

- Games overview deve restare separato da Site/Lobby.
- Notification system deve usare copy layer.
- LOG deve arrivare dopo aver chiarito azioni Games/Site.
- Player lobby deve precedere il polish Site/Lobby.
- Site/Lobby deve gestire solo pubblicazione, non configurazione gioco.

## Documenti da produrre in futuro

Da creare solo quando Michele apre il relativo cantiere:

- `docs/ERROR_NOTIFICATION_SYSTEM_PLAN.md`;
- `docs/GAME_ADMIN_CHANGE_LOG_PLAN.md`;
- `docs/PLAYER_LOBBY_UX_PLAN.md`.

Spiegazione: non creiamo ora piani troppo dettagliati per cantieri non ancora
aperti. Questo documento registra ordine, obiettivi, confini e accettazione; i
piani specifici arriveranno quando servira' implementare.

## Regole trasversali

- UI prodotto in inglese.
- Nessun nuovo testo hardcoded nelle aree gia' migrate al copy layer.
- Separare sempre configurazione gioco e pubblicazione sito.
- Separare sempre gameplay/wallet/ledger da backoffice UX.
- Non introdurre engine non-Mines finche' non viene richiesto un cantiere
  dedicato.
- Non introdurre CMS completo sotto la scusa della lobby.
- Non introdurre external HTTP adapter finche' Fase 9b/c resta rinviata.

## Verifiche per ogni milestone implementativa

Minimo:

- `npx tsc --noEmit`;
- `npm run build`;
- smoke browser o endpoint coerente con l'area;
- container frontend aggiornato se cambia UI servita;
- documentazione aggiornata se cambia flusso, responsabilita' o mapping.

Per aree backend:

- test contract/integration pertinenti;
- nessun bypass wallet/ledger;
- idempotenza preservata dove coinvolta.

## Checklist CTO

- Confermare ordine 0-1-2-3-4-5.
- Confermare che Site/Lobby resta ultimo tra questi cantieri.
- Confermare che copy/i18n e' fondazione English-first, non multilingua completo.
- Confermare che Games governa varianti/config, Site governa pubblicazione.
- Confermare che LOG e' backoffice operativo, non audit finanziario.
- Confermare che player lobby viene progettata prima del polish Site backoffice.
