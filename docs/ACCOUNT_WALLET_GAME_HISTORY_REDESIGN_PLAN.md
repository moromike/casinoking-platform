Status: ACTIVE
Last meaningful update: 2026-05-10

# Account Wallet And Game History Redesign Plan

Documento di progetto per riallineare `/account` dopo il feedback su Cassa, Estratto conto, movimenti e paginazione.

## Stato

- Tipo: piano operativo UX/API per account player.
- Stato: approvato; ACC-1/2/3 implementati, ACC-4 tecnico superato da
  CASHIER-1/2/3. La Cassa player ora usa lo statement business-oriented.
  ACC-5 Accessi pending.
  Vedi anche `docs/ACCOUNT_ACC_1_ENDPOINT_AUDIT.md`.
- Ambito: Cassa, movimenti wallet/ledger, storico gioco/sessioni, accessi, paginazione.
- Non sostituisce: documenti financial core, `docs/PLAYER_ACCOUNT_UX_REDESIGN_PLAN.md`, atlas platform.

## Decisione Di Prodotto

Ogni tab deve avere una responsabilita' informativa unica.

La versione attuale mescola troppo:

- sintesi finanziaria;
- movimenti ledger;
- sessioni Mines;
- dettaglio round.

Questo crea confusione. Un player deve poter capire saldo e movimenti senza leggere il dettaglio tecnico di ogni mano/round.

## Nuova Architettura Informativa

```text
/account
  Overview
    saldo principale
    massimo 3 voci miste recenti
    link verso le viste complete

  Cassa
    wallet
    saldo
    movimenti finanziari
    ricostruzione balance da eventi economici

  Storico gioco
    sessioni gioco
    summary per sessione
    dettaglio round/spin/mani su espansione

  Accessi
    login/access log player
    sessione corrente
    sicurezza base

  Profilo
    dati anagrafici read-only per ora

  Sicurezza
    cambio password
    protezioni future
```

Regola Overview:

- mostra saldo principale;
- mostra al massimo tre voci miste recenti, per esempio un movimento economico,
  una sessione gioco e un evento account se disponibile;
- ogni voce rimanda alla vista completa;
- non deve diventare una mini-Cassa o un mini-Storico gioco.

Nome del tab oggi chiamato "Estratto conto":

- preferito: `Storico gioco`;
- sconsigliato: `Partite`, perche' quando arriveranno slot o altri engine suona
  ambiguo;
- sconsigliato: `Dettaglio gioco`, perche' sembra un pannello tecnico.

Motivo: "Estratto conto" e' un concetto finanziario. Se dentro ci sono round e sessioni di gioco, il nome e' fuorviante.

## Cassa

Obiettivo:

- mostrare lo stato del wallet;
- rendere comprensibili tutti i movimenti finanziari;
- permettere la ricostruzione del saldo;
- preparare il futuro deposito/prelievo senza inventarlo ora.

Aggiornamento 2026-05-09:

- la lista card verticale introdotta in ACC-4 non e' accettabile come UX
  finale;
- Cassa deve diventare una pagina movimenti compatta con prefiltri causali,
  periodo, righe business espandibili e separazione esplicita cash/bonus;
- il dettaglio e' definito in
  `docs/ACCOUNT_CASHIER_MOVEMENTS_REDESIGN_ANALYSIS.md`.

In scope:

- saldo per wallet;
- lista movimenti wallet/ledger;
- filtri semplici per tipo/data/wallet;
- importo, segno, data, descrizione player-friendly;
- link o riferimento compatto alla sessione gioco quando il movimento deriva da gioco;
- paginazione o cursor;
- empty/loading/error states.

Out of scope:

- deposito/prelievo reale;
- modifica del modello ledger;
- derivare importi da euristiche fragili se l'endpoint non li espone;
- dettaglio di ogni round dentro Cassa.

Regola:

- Cassa mostra la sintesi economica per sessione o transazione, non il dettaglio delle singole celle/mani.

## Storico Gioco

Obiettivo:

- mostrare lo storico gioco senza pretendere di essere estratto conto finanziario.

In scope:

- sessioni Mines raggruppate;
- summary per sessione: giocato, vinto, risultato, stato, data;
- dettaglio round espandibile;
- id tecnici abbreviati solo nel dettaglio;
- paginazione;
- preparazione futura multi-game.

Out of scope:

- saldo contabile;
- deposito/prelievo;
- riconciliazione wallet.

## Accessi

Obiettivo:

- separare login/access log e sicurezza operativa dallo storico gioco.

Prima slice possibile:

- mostrare ultimi accessi se endpoint gia' disponibile;
- altrimenti creare solo piano dati e lasciare tab non implementata.

Regola:

- non creare un tab finto senza dati reali. Se mancano endpoint player-safe, il tab Accessi aspetta.

## Paginazione

Decisione:

- la paginazione va fatta adesso per Cassa e Storico gioco, prima di aumentare il volume dati.

Preferenza tecnica:

- cursor-based pagination per dati ordinati per `created_at` e id;
- evitare offset se la tabella cresce o se arrivano nuovi movimenti durante la lettura;
- limite iniziale UI: 10 o 20 item per pagina;
- pulsanti `Carica altri` o paginazione semplice, non infinite scroll cieco.

Endpoint possibili:

```text
GET /ledger/transactions?limit=20&cursor=...
GET /games/mines/sessions?limit=20&cursor=...
```

Endpoint futuri migliori:

```text
GET /account/wallet-movements?limit=20&cursor=...
GET /account/game-sessions?limit=20&cursor=...
```

Nota severa:

- se `/ledger/transactions` non espone importo e saldo-after sufficienti, Cassa non puo' fingere ricostruzione balance. Serve endpoint read-only dedicato.
- ACC-1 ha confermato questo caso: `/account/wallet-movements` resta tecnico,
  mentre la Cassa player deve usare
  `GET /account/statement-movements?wallet_type=cash&period=last_30_days`.

## Slice Operative

### ACC-1 - Audit dati reali

Stato: completato.

Output:

- cosa espone oggi `/wallets`;
- cosa espone oggi `/ledger/transactions`;
- cosa espone oggi `/games/mines/sessions`;
- cosa manca per ricostruire saldo e movimenti.

Esito:

- audit completato in `docs/ACCOUNT_ACC_1_ENDPOINT_AUDIT.md`;
- creato read model read-only `/account/wallet-movements`;
- non usare `/ledger/transactions` per la Cassa player.

### ACC-2 - Rinomina e separazione tab

Stato: completato.

Azioni:

- rimuovere `Movimenti recenti` dal fondo del tab gioco;
- spostare i movimenti in Cassa;
- rinominare `Estratto Conto` in `Storico gioco`;
- mantenere Overview come summary.

### ACC-3 - Paginazione Storico Gioco

Stato: completato.

Azioni:

- backend `/games/mines/sessions?limit=...&cursor=...`;
- UI `Carica altre sessioni`;
- test integrazione su meta e cursor invalido.

### ACC-4 - Cassa movimenti

Stato: completato lato read model tecnico; superato da CASHIER-1/2/3 lato UX
finale.

Azioni:

- UI wallet-first;
- movimenti financial-first;
- usare `/account/wallet-movements`;
- dettaglio espandibile per transazione;
- nessun dettaglio round dentro Cassa.

Follow-up obbligatorio:

- CASHIER-1 completato: aggiunto `/account/statement-movements` come read
  model statement-oriented per righe aggregate e cash/bonus separati;
- CASHIER-2 completato: aggiunto detail endpoint
  `/account/statement-movements/{movement_id}`;
- CASHIER-3 completato: la UI Cassa usa prefiltri, righe compatte e detail
  lazy al posto della card list contabile;
- CASHIER-4 verifica tecnica locale completata; resta validazione utente/browser
  prima di considerare la Cassa accettata.

### ACC-5 - Accessi

Stato: pending.

Azioni:

- verificare endpoint access log player-safe;
- se presente, UI tab Accessi;
- se assente, piano endpoint read-only.

## Criteri Di Accettazione

- Cassa permette di capire saldo e movimenti.
- Storico gioco permette di capire sessioni e round.
- Le due viste non duplicano lo stesso scopo.
- Paginazione impedisce viste infinite.
- Mobile 375px non rompe layout.
- Nessun cambio wallet/ledger write path.
- Nessun deposito/prelievo finto.
