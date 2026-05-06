# CasinoKing - Backoffice Games UX Reorganization Plan

## Stato

Piano operativo da approvare prima di implementare.

Questo documento nasce dopo la prima chiusura funzionale della Fase 7:
master Mines bloccato, varianti duplicabili/modificabili, pubblicazione
demo/real title-aware e player lobby dinamica.

Il problema residuo non e' tecnico, ma di esperienza d'uso: la vista attuale
mescola elenco, duplicazione, pubblicazione, dettaglio editor, config tecnica e
azioni runtime. Per un operatore non tecnico al 100% e' difficile capire dove
guardare e cosa fare.

## Obiettivo

Trasformare la sezione backoffice giochi da vista tecnica a strumento
professionale per operatori:

- elenco giochi/varianti chiaro;
- dettaglio configurazione separato;
- azioni principali visibili nel posto giusto;
- confini netti fra catalogo, configurazione gioco e pubblicazione sito;
- supporto futuro a piu' engine senza fingere che oggi siano gia' editabili.

## Principio guida

Separare sempre:

```text
Elenco / Catalogo giochi
  cosa esiste, stato, engine, varianti, azioni di catalogo

Dettaglio / Editor variante
  configurazione della singola variante
```

La pubblicazione sul sito non deve essere governata qui come flusso principale.
Da questa sezione si puo' vedere lo stato di pubblicazione e forse aprire un
link rapido, ma la gestione editoriale della lobby vive nel piano dedicato
`SITE_LOBBY_PUBLICATION_PLAN.md`.

## Utenti target

### Operatore contenuti / prodotto

Vuole capire quali giochi esistono, creare varianti, rinominarle e sapere se
sono pronte.

### Operatore gioco / configurazione

Vuole entrare nel dettaglio di una variante e modificare regole, griglia, mine,
tema e asset senza toccare il master.

### Admin tecnico

Vuole vedere engine code, title code, stato tecnico e diagnosticare mapping o
pubblicazione senza che questi dati dominino l'interfaccia.

## Architettura informativa target

### Livello 1 - Games Overview

Vista elenco, non editor.

Contenuti:

- header area "Giochi";
- filtro per engine/categoria;
- elenco categorie gioco;
- per ogni categoria: engine, master, numero varianti, stato tecnico;
- varianti come righe o card compatte;
- azioni di catalogo: duplica dal master, apri dettaglio, preview, vedi stato
  pubblicazione;
- indicatori: bozza pronta, config live, demo enabled, real enabled, hidden,
  active/inactive.

Non deve contenere:

- editor config;
- editor tema;
- asset uploader;
- fairness tools;
- form lunghi;
- tab tecnici del dettaglio.

### Livello 2 - Game Category Detail

Vista categoria engine, per esempio Mines.

Contenuti:

- master in posizione distinta e bloccata;
- varianti in elenco;
- azione "Crea variante da master";
- confronto leggero fra varianti;
- eventuale colonna "Pubblicazione sito" solo informativa.

Decisione UX:

- il master non sembra una variante normale;
- il master ha preview demo, ma non ha modifica;
- le varianti hanno "Apri dettaglio" come azione primaria.

### Livello 3 - Variant Detail

Vista operativa della singola variante.

Contenuti:

- titolo variante modificabile;
- title code visibile ma secondario;
- stato bozza/live;
- tab o sezioni: Overview, Settings, Content/Rules, Theme, Assets, Preview;
- azioni: salva bozza, pubblica configurazione live, preview demo;
- alert se la variante e' pubblicata in sito ma la config non e' aggiornata.

Non deve contenere:

- duplicazione master;
- elenco completo varianti;
- gestione editoriale della lobby;
- creazione engine;
- publishing produzione/external adapter.

## Navigazione proposta

```text
Backoffice
  -> Giochi
      -> Overview categorie
          -> Mines
              -> Master Mines Classic
              -> Varianti
                  -> Mines 2000
                      -> Dettaglio variante
```

Per la prima implementazione si puo' evitare una route Next dedicata e usare
stato interno nella shell admin. Se pero' la complessita' cresce, la route
dedicata diventa preferibile:

```text
/admin/games
/admin/games/mines
/admin/games/mines/titles/{title_code}
```

Decisione da prendere in implementation plan:

- restare nella shell attuale per ridurre impatto;
- oppure introdurre routing dedicato per chiarezza e deep link.

Trigger oggettivo:

- Slice 1 resta nello stato interno della shell se la navigazione rimane
  overview -> variante selezionata;
- se la category view introduce piu' di due livelli di stato condiviso oppure
  serve deep link stabile a categoria/title, si introduce route Next dedicata
  prima di aggiungere altra complessita'.

## Mockup concettuale testuale

### Games Overview

```text
Giochi
------------------------------------------------------------
[Mines]  Engine: mines          Master: Mines Classic
         Varianti: 2            Pubblicate: demo 2 / real 2

         [Apri categoria] [Crea variante]

Altri engine
------------------------------------------------------------
Nessun altro engine configurabile da backoffice.
```

### Mines Category

```text
Mines
------------------------------------------------------------
Master
  Mines Classic        master bloccato
  title: mines_classic
  [Preview demo]

Varianti
------------------------------------------------------------
Nome              Stato config    Lobby          Azioni
Mines 2000        live            demo+real      [Apri] [Preview]
Mines Original    live            demo+real      [Apri] [Preview]

[Crea variante da master]
```

### Variant Detail

```text
Mines 2000
title_code: mines002a     engine: mines
------------------------------------------------------------
[Overview] [Settings] [Rules] [Theme] [Assets] [Preview]

Settings
  Grid sizes
  Mine counts
  Defaults

Azioni
  [Salva bozza] [Pubblica config live] [Preview demo]
```

## Struttura funzionale dettagliata

### Overview categorie

Responsabilita':

- leggere catalogo Site/Title;
- raggruppare per engine;
- distinguere master e varianti;
- mostrare stato sintetico;
- portare l'utente a categoria o dettaglio.

Azioni consentite:

- apri categoria;
- crea variante se esiste master supportato;
- preview master/variante usando il flusso demo anonimo gia' introdotto in F6,
  senza inventare una preview ad-hoc;
- apri Site Publishing solo come link contestuale, non come editor inline.

### Category detail

Responsabilita':

- mettere il master al centro come sorgente;
- rendere la creazione variante un flusso guidato;
- mostrare varianti esistenti in modo confrontabile.

Azioni consentite:

- crea variante da master;
- rinomina variante;
- apri dettaglio variante;
- preview demo tramite anonymous-token/F6;
- consultare stato demo/real.

Azioni da evitare:

- edit config inline;
- publish config inline;
- gestione lobby inline.

### Variant detail

Responsabilita':

- configurare un Title concreto;
- salvare bozza;
- pubblicare config live;
- gestire tema e asset della variante;
- previeware il risultato pubblicato.

Azioni consentite:

- salva bozza;
- pubblica config;
- salva/publish tema;
- upload/delete asset;
- preview demo tramite anonymous-token/F6;
- ritorna all'elenco.

Azioni da evitare:

- creare varianti;
- pubblicare in lobby;
- creare engine;
- modificare master.

## Componenti frontend target

Possibile decomposizione:

```text
frontend/app/ui/games/
  games-overview.tsx
  game-category-view.tsx
  game-variant-list.tsx
  game-variant-detail.tsx
  game-master-card.tsx
  game-status-badges.tsx
```

Componenti esistenti da assorbire o ridurre:

- `platform-catalog-panel.tsx`: oggi mischia catalogo, duplicazione,
  pubblicazione e selezione; in Slice 1 va sostituito/deprecato come pannello
  monolitico e il suo ruolo va ridotto a overview/lista, senza editor inline;
- `title-editor-shell.tsx`: resta base del dettaglio variante;
- `mines-backoffice-editor.tsx`: resta editor engine-specific, ma va montato
  solo dentro detail.

Per Slice 1 il target minimo e' intenzionalmente piccolo:

- `games-overview.tsx`;
- `game-variant-list.tsx`;
- eventuale helper compatto per badge/stati solo se riduce duplicazione reale.

`game-category-view.tsx`, `game-variant-detail.tsx`, `game-master-card.tsx` e
altri componenti emergono nelle slice successive quando il flusso lo richiede.

## Backend/API

Non serve introdurre subito nuovi endpoint se i contratti F7 bastano:

```text
GET  /catalog/sites/casinoking/titles
POST /admin/games/titles/{source_title_code}/duplicate
PUT  /admin/games/titles/{title_code}/profile
GET  /admin/games/titles/{title_code}/config
PUT  /admin/games/titles/{title_code}/config
POST /admin/games/titles/{title_code}/config/publish
GET/PUT/POST theme endpoints
GET/POST/DELETE asset endpoints
```

Possibile futuro endpoint solo se il frontend diventa troppo compositivo:

```text
GET /admin/games/catalog
```

Da valutare dopo il primo refactor UI, non prima.

## Stati UI da progettare

- loading catalogo;
- catalogo vuoto;
- master assente o mal configurato;
- nessuna variante;
- variante selezionata;
- variante con bozza non pubblicata;
- publish config in corso;
- errore validazione config;
- errore permessi;
- engine non supportato.

## Criteri visuali

- UI densa ma leggibile, da backoffice professionale;
- meno card annidate;
- tabelle o liste compatte per varianti;
- dettagli tecnici visibili ma subordinati;
- azioni primarie poche e stabili;
- badge stato piccoli e coerenti;
- niente hero, niente marketing, niente decorazione gratuita;
- gerarchia chiara: categoria -> master/varianti -> dettaglio.

## Sequenza implementativa proposta

### Prerequisito tecnico - F7-C Mines editor decomposition

`mines-backoffice-editor.tsx` resta un monolite grande. Le prime estrazioni e
compattazioni hanno migliorato la leggibilita', ma Slice 2 e Slice 3 richiedono
una decomposizione piu' profonda.

F7-C non va trattato come refactor estetico isolato: e' prerequisito tecnico
per mantenere pulita la separazione fra overview, category view e variant
detail.

Accettazione F7-C:

- config, theme, assets, rules e labels restano nel dettaglio variante;
- overview/category non montano editor engine-specific lunghi;
- il master resta read-only;
- nessun cambio a payout/RTP/RNG/fairness;
- nessun cambio backend non pianificato;
- `tsc --noEmit` e build frontend verdi.

### Slice 1 - Separazione elenco/dettaglio

Stato: implementata prima versione.

- deprecare il `PlatformCatalogPanel` monolitico come contenitore unico;
- introdurre overview/lista con `games-overview.tsx` e `game-variant-list.tsx`;
- spostare editor sotto una sezione/detail separata;
- mantenere endpoint invariati;
- testare selezione variante e ritorno elenco.

Accettazione Slice 1:

- `tsc --noEmit` passa;
- smoke admin: catalogo -> seleziona variante -> editor si apre;
- indietro/torna elenco riporta alla lista senza perdere il catalogo caricato;
- duplicazione e pubblicazione lobby non sono dentro il dettaglio editor;
- nessun endpoint nuovo introdotto.

### Slice 2 - Category view Mines

- introdurre vista categoria Mines;
- master bloccato in blocco dedicato;
- varianti in tabella/lista;
- flusso "Crea variante da master" piu' pulito.

Accettazione Slice 2:

- master Mines visibile, previewable e non modificabile;
- azione "Crea variante da master" parte dalla category view, non dal dettaglio;
- varianti esistenti sono confrontabili in lista/tabella;
- smoke: crea variante -> nuova variante appare in lista -> apri dettaglio;
- nessuna modifica a payout/RTP/RNG/fairness.

### Slice 3 - Variant detail pulito

Stato: prima pulizia implementata su header, diagnostica e command bar.

- header variante;
- tab/sezioni config;
- azioni draft/publish coerenti;
- rimuovere duplicazione e publishing lobby dal dettaglio.

Accettazione Slice 3:

- titolo variante modificabile e title code secondario;
- salva bozza e pubblica config live restano funzionanti;
- Theme/Assets restano nel detail e non contaminano l'elenco;
- il dettaglio non permette creazione varianti ne' gestione lobby;
- smoke: modifica titolo -> salva -> ricarica detail -> titolo aggiornato.

### Slice 4 - Polish visuale

- rivedere spacing, bottoni, stati, leggibilita';
- sistemare sezione Tema;
- smoke desktop/mobile.

Accettazione Slice 4:

- screenshot desktop e mobile senza card annidate incoerenti o overlap;
- bottoni della sezione Tema coerenti con il resto del backoffice;
- stati empty/loading/error leggibili;
- nessuna regressione nei flussi F7 gia' chiusi.

## Promemoria futuro - Game Admin Change Log

Serve un cantiere dedicato per un log leggero delle modifiche backoffice gioco.
Non e' parte delle slice UX sopra, ma va tenuto in roadmap.

Eventi candidati:

- variante creata;
- variante rinominata;
- config bozza salvata;
- config live pubblicata;
- tema salvato/pubblicato;
- asset caricato/eliminato;
- pubblicazione lobby modificata, con responsabilita' finale nel piano Site.

Non deve includere round gameplay, wallet, ledger o audit finanziario. Quelli
restano domini separati e molto piu' sensibili.

## Fuori scope

- CMS sito/lobby;
- creazione engine;
- engine non-Mines;
- payout/RTP/RNG/fairness;
- wallet/ledger;
- produzione/external adapter;
- redesign completo di tutto il backoffice admin.

## Accettazione

Il cantiere e' accettabile quando:

- un operatore capisce prima cosa esiste e poi dove configurarlo;
- la duplicazione vive nell'elenco/categoria, non nel dettaglio;
- la config vive nel dettaglio, non nell'elenco;
- il master non appare modificabile;
- la pubblicazione sito non viene gestita qui come CMS;
- tutti i flussi F7 restano funzionanti.
