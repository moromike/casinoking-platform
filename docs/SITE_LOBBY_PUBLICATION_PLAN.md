# CasinoKing - Site Lobby Publication Plan

## Stato

Slice 1 gia' implementata.

Slice 2 e Slice 3 implementate in prima versione:

- vista Site/Lobby separata dalla configurazione giochi;
- gestione compatta di varianti pubblicabili;
- preview alimentata da `GET /api/v1/games/library`;
- preview master da backoffice tramite token admin dedicato, senza pubblicare il
  master come item lobby;
- metadata lobby modificabili;
- validazione backend per evitare pubblicazione di Title senza config live.

Slice 4 ha un primo polish visuale, con loading/error/empty state e layout
responsive. Resta consigliato uno smoke browser manuale con dati reali prima di
considerarla definitiva dal punto di vista visuale.

Questo documento separa la gestione del sito/lobby dalla gestione tecnica dei
giochi. Nasce dopo Fase 7, che ha introdotto una libreria pubblica minima:
varianti non-master visibili se `lobby_visibility=visible` e demo/real attivi.

## Obiettivo

Creare una gestione leggera della pagina giochi del sito, senza trasformare il
backoffice in un CMS completo.

La vista Site/Lobby deve permettere di decidere:

- quali giochi appaiono nella lobby;
- in quale modalita': demo, real o entrambe;
- con quale nome/descrizione editoriale;
- in quale ordine;
- con quale stato visuale minimo.

Non deve permettere di configurare il gioco. Quello resta nel backoffice giochi.

## Principio guida

Separare sempre:

```text
Backoffice Giochi
  crea varianti, configura regole, tema, asset, preview

Site / Lobby Publishing
  decide cosa appare sul sito e come viene presentato nella lobby
```

La pubblicazione sito usa Title gia' esistenti. Non crea engine, non crea
varianti, non modifica matematica o configurazione runtime.

## Utenti target

### Operatore sito / contenuti

Vuole comporre la pagina giochi e decidere cosa il player vede.

### Product owner

Vuole controllare quali varianti sono esposte in demo/real e in quale ordine.

### Admin tecnico

Vuole verificare mapping Site/Title e stato di disponibilita', ma senza usare
questa pagina come editor tecnico.

## Architettura informativa target

### Livello 1 - Site Overview

Vista del sito corrente, per ora `CasinoKing`.

Nota multi-site: oggi il solo site operativo e' `casinoking`. Il site selector
resta fuori scope finche' non esiste un secondo site reale; il codice nuovo deve
comunque evitare hardcoding nascosti fuori dal boundary della pagina Site.

Contenuti:

- stato Site;
- numero giochi visibili;
- numero giochi demo-enabled;
- numero giochi real-enabled;
- link alla pagina lobby player;
- accesso a "Gestisci lobby giochi".

### Livello 2 - Lobby Games Manager

Vista principale del cantiere.

Contenuti:

- anteprima concettuale della lobby;
- lista giochi pubblicabili;
- lista giochi visibili;
- stati demo/real;
- ordinamento;
- nome/descrizione lobby;
- eventuale featured.

### Livello 3 - Lobby Item Detail

Pannello laterale o detail leggero di un gioco nella lobby.

Contenuti:

- title di riferimento;
- engine;
- stato config live;
- toggle visibile/nascosto;
- toggle demo;
- toggle real;
- display name lobby;
- descrizione lobby;
- posizione/featured;
- preview player.

Non deve contenere:

- config griglia/mine;
- editor tema;
- upload asset di gioco;
- duplicazione variante;
- publish config live.

## Mockup concettuale testuale

### Site Publishing Overview

```text
Sito: CasinoKing
------------------------------------------------------------
Lobby giochi          2 visibili     Demo: 2     Real: 2
Homepage              fuori scope
Pagine contenuto      fuori scope

[Gestisci lobby giochi] [Apri sito]
```

### Lobby Games Manager

```text
Lobby giochi - CasinoKing
------------------------------------------------------------
Disponibili                              Visibili in lobby

Mines Classic        master              -
Mines 2000           variante            1  demo+real  [Modifica]
Mines Original       variante            2  demo+real  [Modifica]

[Anteprima lobby]
```

L'anteprima lobby deve leggere la stessa fonte della lobby player reale:
`GET /api/v1/games/library`. Non deve nascere una preview parallela con regole
diverse.

### Lobby Item Detail

```text
Mines 2000
title_code: mines002a     engine: mines
------------------------------------------------------------
Visibilita'      [visible]
Modalita'        [x] Demo   [x] Real
Nome lobby       Mines 2000
Descrizione      Variante pubblicata del catalogo CasinoKing.
Ordine           2
Featured         no

[Salva pubblicazione] [Nascondi] [Preview player]
```

## Relazione con Backoffice Giochi

Da Backoffice Giochi:

- si vede se una variante e' pubblicata in lobby;
- si puo' aprire il Site Publishing in contesto;
- non si gestisce la lobby inline.

Da Site Publishing:

- si vede se un Title e' configurabile o master;
- si vede se la config live esiste;
- si puo' aprire il dettaglio gioco in altra sezione;
- non si modifica il gioco inline.

Questa relazione evita il problema attuale: azioni di catalogo, config e sito
tutte nella stessa vista.

## Backend/API

Contratti gia' disponibili:

```text
GET /api/v1/games/library
GET /api/v1/catalog/sites/casinoking/titles
PUT /api/v1/admin/sites/{site_code}/titles/{title_code}/publication
```

Per una prima implementazione possono bastare.

Validazione backend attuale:

- i master restano non pubblicabili come item lobby;
- una variante puo' diventare `visible`, `demo_enabled` o `real_enabled` solo
  se e' lanciabile e possiede una config live pubblicata;
- per Mines la validazione usa `title_configs.published_at` e i payload
  pubblicati in `mines_title_configs`;
- `hidden` con demo/real off resta permesso anche se la config manca.

Hardening launch attuale:

- per varianti non-master, il launch token pubblico applica anche i flag
  Site/Lobby;
- `lobby_visibility=visible` e' richiesta per qualsiasi launch pubblico della
  variante;
- `demo_enabled=true` e' richiesta per `mode=demo`;
- `real_enabled=true` e' richiesta per `mode=real`;
- il launch pubblico richiede sempre `title_code` esplicito;
- i Title master sono rifiutati dal launch pubblico con
  `LAUNCH_REJECTED_MASTER`;
- il backoffice usa `POST /admin/games/titles/{title_code}/preview-launch` per
  ottenere un `preview_token` firmato e aprire master/hidden Title in demo;
- `preview=1` senza token non e' un bypass pubblico;
- il master non entra nella library player e non e' pubblicabile come item
  lobby.

Ordinamento in prima implementazione:

- si persiste con l'endpoint singolo `PUT /publication` per ogni Title toccato;
- un drag/drop o controllo su/giu' puo' quindi produrre N chiamate ordinate;
- un endpoint batch di reorder si valuta solo se il flusso diventa lento,
  fragile o difficile da rendere atomico lato UI.

Possibile endpoint futuro per vista editoriale:

```text
GET /api/v1/admin/sites/{site_code}/lobby
```

Payload concettuale:

```json
{
  "site": {},
  "available_titles": [],
  "visible_titles": []
}
```

Da introdurre solo se migliora davvero il frontend. Non e' necessario per il
primo refactor.

## Modello dati attuale

La pubblicazione lobby vive in `site_titles`:

- `lobby_visibility`;
- `demo_enabled`;
- `real_enabled`;
- `lobby_display_name`;
- `lobby_description`;
- `featured`;
- `position`.

Questo e' sufficiente per una gestione lobby leggera.

Enum corrente:

- `lobby_visibility = hidden`;
- `lobby_visibility = visible`.

Non esistono oggi stati `draft` o `scheduled`: vanno considerati fuori scope
finche' non saranno progettati esplicitamente.

`featured` oggi e' un flag multi-item, non una garanzia "un solo featured per
site". La UX puo' mostrarlo come evidenza editoriale leggera. Se in futuro si
vorra' un solo featured per lobby, servira' una decisione di prodotto e una
validazione dedicata.

`position` e' numerico e governa l'ordinamento relativo dei giochi visibili.

## Stati UI da progettare

- nessun gioco pubblicabile;
- nessun gioco visibile;
- variante visibile solo demo;
- variante visibile demo+real;
- title inactive;
- config live assente o non aggiornata;
- master non pubblicabile;
- errore permessi;
- salvataggio in corso;
- preview lobby.

## Criteri visuali

- vista piu' editoriale del backoffice giochi, ma sempre operativa;
- layout a due colonne possibile: disponibili / visibili;
- evitare un CMS generico;
- usare preview concreta della lobby quando utile;
- rendere chiaro "pubblicato sul sito" rispetto a "config pubblicata live";
- usare copy breve, non tecnico, ma non nascondere title code/engine ai tecnici.

## Sequenza implementativa proposta

### Slice 1 - Pagina Site Publishing minima

Stato: implementata prima versione.

- nuova sezione backoffice "Sito" o "Site";
- sottosezione "Lobby giochi";
- lista Title disponibili e visibili;
- toggle hidden/visible, demo, real;
- salvataggio tramite endpoint esistente.

Accettazione Slice 1:

- `tsc --noEmit` passa;
- smoke admin: apri Site -> Lobby giochi -> modifica visibilita' -> salva;
- la lobby player aggiornata legge il risultato da `GET /games/library`;
- nessuna configurazione gioco e nessuna duplicazione variante sono presenti
  nella pagina Site;
- site corrente `casinoking` dichiarato nel boundary UI/API usato.

### Slice 2 - Ordinamento e preview

Stato: implementata in prima versione.

- posizione drag/drop o controlli su/giu';
- preview compatta della lobby;
- link al player.

Accettazione Slice 2:

- reorder persiste usando `PUT /publication` per i Title modificati;
- ricaricando la pagina l'ordine resta stabile;
- preview lobby usa `GET /games/library`, come il player;
- master non pubblicabili non entrano nella preview player.

### Slice 3 - Metadata lobby

Stato: implementata in prima versione.

- display name;
- descrizione;
- featured;
- validazioni UI;
- warning se manca config live.

Validazioni minime:

- non salvare `lobby_visibility=visible` se il Title non ha config live;
- `demo_enabled=true` richiede che il Title sia avviabile in demo;
- `real_enabled=true` richiede che il Title sia avviabile in real;
- master bloccato non pubblicabile come item lobby ordinario.

Accettazione Slice 3:

- display name e descrizione si salvano e compaiono nella lobby;
- warning/errore impedisce una pubblicazione incoerente;
- featured e position sono visibili senza trasformare la pagina in CMS completo;
- nessun endpoint nuovo introdotto salvo decisione esplicita successiva.

### Slice 4 - Polish visuale

Stato: prima passata implementata, smoke visuale manuale ancora consigliato.

- layout professionale;
- stati vuoti;
- loading;
- errori;
- mobile/tablet;
- verifica con screenshot.

Accettazione Slice 4:

- screenshot desktop/tablet/mobile senza overlap o confusione tra config e sito;
- stati empty/loading/error comprensibili per operatore non tecnico;
- copy breve e operativo;
- nessuna regressione su lobby player demo/real.

## Fuori scope

- CMS completo del sito;
- homepage;
- pagine statiche;
- creazione varianti;
- configurazione gioco;
- asset upload di gioco;
- engine management;
- payout/RTP/RNG/fairness;
- produzione/external adapter.

## Accettazione

Il cantiere e' accettabile quando:

- da Backoffice Giochi non si gestisce piu' editorialmente la lobby;
- da Site Publishing si capisce cosa appare sul sito;
- demo e real sono stati espliciti;
- la lobby player resta alimentata dal backend;
- un operatore non tecnico puo' pubblicare/nascondere/ordinare giochi senza
  entrare nel dettaglio config.
