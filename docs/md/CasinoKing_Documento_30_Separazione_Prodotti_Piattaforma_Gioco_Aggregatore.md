# CasinoKing - Documento 30

Architettura target separata tra piattaforma, gioco e aggregatore

Stato del documento

- Documento operativo nuovo, nato dall'analisi del coupling reale emerso durante l'implementazione.
- Integra i documenti 02, 03, 06, 11, 21, 22 e 23.
- Non sostituisce le regole finanziarie canoniche: le conferma e le ricolloca nella nuova separazione di domini.

## 1. Obiettivo

Definire in modo esplicito la target architecture corretta del progetto, evitando di trattare `sito`, `gioco Mines` e `piattaforma finanziaria` come un unico prodotto frontend/backend.

## 2. Problema emerso

L'implementazione corrente ha mostrato un coupling eccessivo tra:

- shell del sito
- shell del gioco
- API del gioco
- API finanziarie piattaforma

Questo ha prodotto una conseguenza pratica:

- Mines e' stato trattato troppo a lungo come una vista interna della piattaforma, quando invece deve vivere come modulo gioco separabile ed embeddabile.

## 3. Principio guida

CasinoKing va pensato come insieme di domini distinti:

1. `Piattaforma`
2. `Gioco Mines`
3. `Aggregatore / Sito Web`

Questi domini possono vivere nello stesso monorepo, ma non devono vivere nello stesso prodotto applicativo.

## 4. Prodotti target

### 4.1 Backend piattaforma

Responsabilita':

- identity player/admin
- sessione piattaforma
- wallet
- ledger
- reporting
- backoffice
- lifecycle finanziario delle partite
- autorizzazione di lancio verso i giochi

Il backend piattaforma non deve implementare logica interna del gameplay Mines oltre al necessario contratto di integrazione.

### 4.2 Backend gioco Mines

Responsabilita':

- configurazioni supportate del gioco
- runtime/payout table
- fairness
- seed management
- RNG
- board generation
- reveal per click
- stato tecnico della partita lato gioco
- determinazione dell'importo finale vinto

Il backend Mines non deve possedere ledger o wallet.

### 4.3 Frontend piattaforma / web player

Responsabilita':

- lobby
- login/register
- account
- catalogo giochi
- promozioni
- routing sito
- eventuale shell di lancio del gioco

Non deve contenere la UI interna del tavolo Mines.

### 4.4 Frontend gioco Mines

Responsabilita':

- UI del tavolo
- regole del gioco
- interazione con RNG/reveal backend gioco
- stato visuale della round

Deve poter vivere:

- standalone
- embeddato
- lanciato da sito CasinoKing
- lanciato da shell terza

### 4.5 Aggregatore

L'aggregatore e' il prodotto che orchestra l'accesso ai giochi.

Nel breve periodo puo' coincidere con il `web platform`.

Nel medio periodo puo' diventare prodotto separato.

Responsabilita':

- mostrare il catalogo
- aprire il gioco
- gestire il passaggio di contesto e autenticazione
- non entrare nella logica del gameplay

## 5. Regole di confine

### 5.1 Confine sito -> gioco

Il sito porta il giocatore al gioco.

Il gioco non porta il giocatore nella lobby.

Dentro il frame del gioco non devono comparire:

- login/register del sito
- account
- promo/banner del sito
- backoffice

### 5.2 Confine gioco -> finanza

Il gioco non modifica direttamente wallet o ledger.

Il gioco produce:

- richiesta di apertura round
- eventi di reveal
- esito finale / payout finale

La piattaforma registra:

- puntata iniziale
- chiusura della round
- payout finale
- effetti contabili su wallet/ledger

### 5.3 Confine gioco -> aggregatore

L'aggregatore non conosce i dettagli del board, del seed o del reveal.

L'aggregatore conosce solo:

- quale gioco lanciare
- per quale player
- con quale token/contesto

## 6. Stato attuale del codebase

### 6.1 Gia' corretto

- `/mines` e' stato separato dal contenitore generale e ora monta un componente dedicato.

### 6.2 Ancora da migrare

- `frontend/app/ui/casinoking-console.tsx` resta contenitore monolitico di:
  - lobby
  - account
  - login/register
  - admin
  - residui della vecchia vista Mines

- il backend `games/mines/service.py` oggi tocca direttamente:
  - wallet_accounts
  - ledger_transactions
  - ledger_entries
  - game_sessions

Questo conferma che oggi il backend gioco e quello piattaforma non sono ancora separati.

## 7. Decisione architetturale

La target architecture ufficiale da questo momento e':

1. backend piattaforma separato
2. backend gioco Mines separato
3. frontend web platform separato
4. frontend Mines separato
5. aggregatore come shell distinta o coincidente con web platform, ma concettualmente separata

## 8. Regola operativa

Ogni nuova modifica futura deve dichiarare prima a quale dominio appartiene:

- piattaforma
- gioco
- aggregatore

Se una modifica mescola due domini, va fermata e ripensata prima di essere implementata.
