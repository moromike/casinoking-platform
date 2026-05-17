Status: ACTIVE
Last meaningful update: 2026-05-10

# Mines Replay Viewer Plan

## Stato

- Tipo: piano/contratto operativo per replay round Mines.
- Stato: V1.3 implementata.
- Data: 2026-05-10.
- Ambito: Game Module Mines, endpoint replay read-only, viewer frontend riusabile,
  integrazione nello Storico gioco account, nel runtime Mines e nel report
  finance backoffice.
- Non sostituisce: documenti canonici Mines, fairness, wallet/ledger.

## Perche' Esiste

`Storico gioco` ha senso solo se mostra cosa e' successo dentro le mani, non se
duplica la Cassa.

La Cassa risponde a:

```text
Cosa e' successo al saldo?
```

Il replay risponde a:

```text
Cosa e' successo nella mano?
```

Questa distinzione rende `Storico gioco` una vista di trasparenza, supporto e
fairness, non un secondo estratto conto.

## Decisione Architetturale

Il replay appartiene al Game Module Mines.

Motivo:

- solo Mines conosce board, celle, mine, reveal, cashout e stato round;
- Account deve richiamare il replay, non ricostruirlo;
- in futuro lo stesso viewer puo' essere richiamato dal gioco, dal backoffice o
  da un tool support senza duplicare logica visuale;
- il frontend non calcola outcome, mine o payout.

Pattern:

```text
Mines Replay API
  -> espone snapshot read-only del round

MinesReplayViewer
  -> renderizza board finale in sola lettura

Account / Storico gioco
  -> carica il replay quando il player clicca "Rivedi mano"

Mines runtime
  -> riusa lo stesso viewer per "Rivedi mano" dopo un round chiuso

Backoffice finance/support
  -> riusa lo stesso viewer dal dettaglio sessione/round
```

## Regole Non Negoziabili

- Il replay e' read-only.
- Non scrive wallet, ledger, round, sessioni o audit.
- Non ricalcola outcome.
- Non decide mine/safe lato frontend.
- Non espone `mine_positions` per round attivi.
- Espone `mine_positions` solo quando il round e' chiuso.
- La stessa regola vale per admin/backoffice: nessun operatore vede il board
  completo di una mano ancora attiva.
- Nota sicurezza: Mines resta server-authoritative. Il backend puo' avere il
  board segreto necessario a valutare reveal/cashout, ma finche' il round e'
  attivo quel dato non esce dagli endpoint player/admin. Il frontend, il
  player e l'operatore non ricevono mine nascoste.
- Usa dati gia' salvati dal backend autorevole.
- Mantiene fairness metadata come riferimento, senza promettere verifica utente
  completa finche' `user_verifiable=false`.

## Dati V1 Disponibili

Gia' disponibili oggi:

- `grid_size`;
- `mine_count`;
- `bet_amount`;
- `payout_amount`;
- `status`;
- `revealed_cells_json`;
- `mine_positions_json`;
- `title_code`;
- `site_code`;
- `wallet_type`;
- `created_at`;
- `closed_at`;
- `fairness_version`;
- `nonce`;
- `server_seed_hash`;
- `board_hash`.

Gap noto:

- non esiste ancora un event log con timestamp per ogni singolo click;
- il replay V1.2 non ricostruisce piu' lo sviluppo della mano: mostra solo
  fotografia finale, esito e posizioni mine quando il round e' chiuso;
- V2 introdurra' un event log solo se servira' una ricostruzione completa per
  audit/support, non per la vista player base.

## Endpoint V1.1

```text
GET /games/mines/session/{session_id}/replay
```

Autorizzazione:

- player autenticato;
- solo round propri;
- oppure launch token runtime valido per lo stesso player;
- oppure launch token demo valido per la sessione anonima demo;
- round di altro player = `403 FORBIDDEN`;
- round inesistente = `404 RESOURCE_NOT_FOUND`.

Endpoint backoffice:

```text
GET /games/mines/admin/session/{session_id}/replay
```

Autorizzazione:

- admin con area `finance` o superadmin;
- round inesistente = `404 RESOURCE_NOT_FOUND`;
- round attivo = payload consentito ma senza mine nascoste.

Payload concettuale:

```text
game_session_id
status
title_code
site_code
wallet_type
grid_size
mine_count
bet_amount
payout_amount
safe_reveals_count
revealed_cells
mine_positions
mine_positions_available
final_revealed_cells
multiplier_current
potential_payout
created_at
closed_at
board_reveal_available
replay_version
fairness
  fairness_version
  nonce
  server_seed_hash
  board_hash
  user_verifiable
```

Regola `mine_positions`:

- round `active`: `mine_positions=[]`, `mine_positions_available=false`;
- round `won/lost/cancelled`: `mine_positions` valorizzato,
  `mine_positions_available=true`.

Endpoint runtime per ultime sessioni player:

```text
GET /games/mines/access-sessions/latest
```

Autorizzazione:

- player autenticato;
- launch token Mines valido per lo stesso player;
- il `title_code` e `site_code` vengono presi dal launch token;
- restituisce al massimo le ultime 3 `game_access_sessions` del player per
  quel Title/Site;
- ogni access session contiene le proprie mani come snapshot finali;
- la lista include solo round chiusi, perche' una fotografia finale di un
  round attivo non esiste ancora.

## Frontend V1

Componente:

```text
frontend/app/ui/mines/mines-replay-viewer.tsx
```

Responsabilita':

- renderizzare una board Mines non interattiva;
- mostrare solo fotografia finale/esito della mano;
- usare `MinesBoard` come visuale, senza duplicare la griglia;
- mostrare metadati essenziali e fairness hash abbreviati.

Non responsabilita':

- non carica direttamente dati account;
- non decide autorizzazione;
- non ricalcola outcome;
- non modifica stato gioco.

## Integrazione Account Player

In `Storico gioco`, ogni round ha un comando:

```text
Rivedi mano
```

Il replay viene caricato lazy, solo quando richiesto.

Motivo:

- lo storico resta leggero;
- molte sessioni non generano subito carico API;
- il player apre solo le mani che vuole capire.

## Integrazione Runtime Mines

Nel gioco Mines, dopo una mano chiusa il player puo' aprire `Rivedi mano`.

Regole:

- in modal Game info tab `REPLAY`, il player autenticato vede le ultime 3
  access session del Title corrente, ognuna con le sue mani;
- ogni mano mostra solo snapshot finale, esito, mine finali se disponibili e
  diamanti/safe cells effettivamente scoperti dal player;
- il replay viene caricato lazy quando il tab `REPLAY` viene aperto;
- real autenticato usa `/games/mines/access-sessions/latest` tramite launch
  token; demo resta sul singolo replay dell'ultima mano chiusa;
- il replay vive nel layer Game info/Regole come tab `REPLAY`, accanto alla
  tab `REGOLE`;
- il replay non viene renderizzato sotto il board e non deve allungare o
  ridimensionare il riquadro di gioco;
- iniziare una nuova mano resetta il replay corrente.

## Skin Replay

Il replay usa sempre una skin base semplificata e stabile:

- icona diamante default;
- icona mina default;
- nessun asset custom del Title;
- nessuna texture cella custom;
- nessuno sfondo area gioco custom.

Motivo: il replay e' una vista di trasparenza/supporto, non una seconda
esperienza di gioco skinnabile. In futuro potra' essere migliorato graficamente,
ma ogni cambio deve essere esplicito e non deve ereditare automaticamente le
skin runtime del Title.

## Integrazione Backoffice

Il backoffice puo' riusare `MinesReplayViewer` nelle superfici di supporto che
mostrano il dettaglio player/round. Il report finance principale resta una
tabella di sessioni banco e non apre piu' un dettaglio inline quando i dati
sono gia' presenti nella riga.

Decisione di prodotto:

- il report finance resta prospettiva banco/GGR;
- il replay resta prospettiva mano/player ed e' uguale alla view player;
- il replay non deve sporcare le colonne finance ne' trasformare il report in
  uno storico gioco duplicato;
- la board completa non viene esposta se il round e' ancora `active`.

## Evoluzione V2

Quando servira' un replay ancora piu' forte:

- tabella event log per azioni round;
- timestamp per ogni reveal;
- evento cashout separato;
- velocita' replay/autoplay;
- deep link diretto a round;
- link diretto da backoffice player statement V2 quando quel read model admin
  verra' introdotto;
- policy di retention/storicizzazione per event log, fairness data e replay
  snapshot prima del volume produzione;
- eventuale pagina fairness verificabile.

## Criteri Di Accettazione

- Un player puo' aprire `Storico gioco`, espandere una sessione e cliccare
  `Rivedi mano`.
- Il replay mostra board finale senza rendere la board interattiva.
- Round chiuso mostra mine finali e diamanti/safe cells scoperti.
- Round attivo non mostra mine nascoste.
- Il replay usa la skin base semplificata, indipendente dagli asset/skin del
  Title.
- Endpoint respinge round di altri player.
- Il runtime Mines puo' mostrare le ultime 3 access session del player/Title
  nel layer Game info/Regole, senza modificare altezza/layout del board.
- Il report finance principale resta non espandibile; eventuali viste
  backoffice di supporto riusano lo stesso viewer quando aprono un round.
- Nessun path wallet/ledger/RNG/payout viene modificato.
