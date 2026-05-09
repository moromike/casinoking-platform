# Mines Replay Viewer Plan

## Stato

- Tipo: piano/contratto operativo per replay round Mines.
- Stato: V1.1 implementata.
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
  -> renderizza board e timeline in sola lettura

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
- V1 ricostruisce l'ordine dalle celle salvate in `revealed_cells_json`;
- V2 dovra' introdurre un event log se servono tempi reali per reveal/cashout.

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
steps[]
  step_index
  cell_index
  result
  safe_reveals_count
  multiplier
  payout_amount
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

## Frontend V1

Componente:

```text
frontend/app/ui/mines/mines-replay-viewer.tsx
```

Responsabilita':

- renderizzare una board Mines non interattiva;
- mostrare frame iniziale, step reveal e board finale;
- usare `MinesBoard` come visuale, senza duplicare la griglia;
- esporre controlli Inizio/Indietro/Avanti/Finale;
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

- il comando non compare durante una mano attiva;
- il replay viene caricato lazy;
- demo e real usano lo stesso endpoint tramite launch token;
- il replay e' sotto il board, non sostituisce lo stato runtime del gioco;
- iniziare una nuova mano resetta il replay corrente.

## Integrazione Backoffice

Nel report finance, il dettaglio sessione espone `Rivedi mano` per i round
Mines.

Decisione di prodotto:

- il report finance resta prospettiva banco/GGR;
- il replay resta prospettiva mano/player ed e' uguale alla view player;
- il bottone replay non cambia il significato delle colonne finance;
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
- eventuale pagina fairness verificabile.

## Criteri Di Accettazione

- Un player puo' aprire `Storico gioco`, espandere una sessione e cliccare
  `Rivedi mano`.
- Il replay mostra board, step e finale senza rendere la board interattiva.
- Round chiuso mostra mine finali.
- Round attivo non mostra mine nascoste.
- Endpoint respinge round di altri player.
- Il runtime Mines puo' mostrare il replay dell'ultima mano chiusa.
- Il backoffice finance puo' aprire il replay di un round Mines dal dettaglio
  sessione.
- Nessun path wallet/ledger/RNG/payout viene modificato.
