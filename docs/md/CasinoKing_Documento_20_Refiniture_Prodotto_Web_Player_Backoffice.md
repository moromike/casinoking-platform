# CasinoKing - Documento 20

Refiniture di prodotto per sito web player, Mines e backoffice admin

Stato del documento

- Questo documento nasce come integrazione operativa delle priorita' prodotto chiarite durante l'implementazione.
- Non sostituisce `docs/SOURCE_OF_TRUTH.md` o i documenti canonici gia' elencati li'.
- Va interpretato come documento esecutivo di chiusura prodotto, coerente con Documento 06, Documento 11, Documento 15 e `docs/PRODUCT_CLOSURE_BACKLOG.md`.
- Se in futuro verra' creato un corrispondente file canonico in `docs/word/`, questo file dovra' esserne un mirror fedele.

## 1. Obiettivo

Portare CasinoKing da demo tecnica forte a sito web di gaming credibile, con:

- esperienza player piu' vicina ai casino web embedded e non a una console tecnica
- percorso chiaro di accesso, registrazione, login e account
- ingresso naturale al catalogo casino e al gioco Mines
- backoffice admin leggibile per controllo giocatori, conto e mani

Il motore finanziario e il motore di gioco gia' costruiti restano invariati nei loro vincoli fondamentali:

- ledger come fonte primaria
- wallet snapshot materializzato
- idempotenza sugli endpoint sensibili
- Mines server-authoritative
- nessuna logica di outcome nel client

## 2. Principi di prodotto chiariti

### 2.1 Sito player first-party

- Il sito deve essere gestito direttamente dentro l'applicazione web CasinoKing.
- Non si introduce ora un CMS esterno.
- La struttura deve ricordare un sito casino reale: header, autenticazione, promo, area gioco, area account.

### 2.2 Entry point auth chiaro

- Login in alto a destra.
- Registrazione nuova utenza tramite pagine dedicate.
- Il flusso auth deve sembrare prodotto reale, non modulo di debug.

### 2.3 Account player leggibile

- L'utente autenticato deve poter vedere:
  - dati base account
  - estratto conto personale
  - crediti assegnati
  - sessioni di gioco
  - vinto/perso
- L'account deve rimanere owner-only e basato sulle API esistenti o su future estensioni coerenti con Documento 11.

### 2.4 Lobby casino semplice ma credibile

- Il sito player deve avere una sezione casino chiara.
- In una prima fase basta un solo tab o categoria `Casino`.
- Dentro la categoria deve esistere la card/icona del gioco `Mines`.

### 2.5 Apertura gioco Mines

- Il gioco deve apparire come prodotto pronto per essere giocato.
- La direzione desiderata e' compatibile con un'apertura embedded, anche tramite iframe o shell equivalente, pur mantenendo il controllo totale dell'app.
- Le parti non utili al giocatore devono essere nascoste.
- L'interfaccia del gioco va rifinita prendendo come riferimento prodotti casino reali, con particolare attenzione alla leggibilita' e alla chiarezza delle azioni.

### 2.6 Trasparenza RNG / fairness

- Il player deve poter vedere in modo comprensibile come viene gestita la correttezza del gioco.
- La spiegazione non deve essere tecnica in eccesso, ma deve mostrare almeno:
  - seed / hash o concetto equivalente
  - verificabilita' disponibile
  - riferimento alle mani / round giocati
- L'implementazione corrente non deve inventare claim non supportati.

### 2.7 Backoffice orientato all'operativita'

- Il backoffice deve permettere:
  - estratto conto generale
  - vista aggregata del giocato/vinto
  - filtri per periodo quando disponibili
  - dettaglio giocatore
  - gestione account giocatore
  - dettaglio delle sue giocate
- Le viste admin devono essere distinte dal percorso player e leggibili come strumento operativo.

## 3. Indicazioni operative per il player site

### 3.1 Header

Il sito player deve convergere verso un header con:

- brand CasinoKing
- accesso rapido a login e registrazione
- shortcut account quando autenticato
- separazione netta del percorso admin

### 3.2 Promo / hero

Il sito deve avere una zona promozionale chiara, con copy orientato alla registrazione e al gioco.

Direzione copy iniziale:

- messaggio promozionale in evidenza
- CTA registrazione
- CTA ingresso al catalogo casino

### 3.3 Catalogo casino

Prima iterazione sufficiente:

- un'unica macro area `Casino`
- card `Mines`
- stato chiaro del gioco
- call to action per apertura/resume

### 3.4 Pagine auth

Prima iterazione desiderata:

- pagina login dedicata
- pagina register dedicata
- stato autenticato chiaro
- reset password coerente col flow locale gia' presente

### 3.5 Email di conferma in ambiente test

Per l'ambiente di test:

- le email usate in registrazione possono essere fittizie
- gli invii di conferma e verifica devono poter essere recapitati verso `moromike@gmail.com`

Nota:

- questa e' una policy di ambiente test e non una regola prodotto finale
- va implementata solo quando il sottosistema email verra' realmente introdotto
- fino ad allora deve restare esplicitamente documentata come requisito futuro e non simulata in modo ambiguo

## 4. Indicazioni operative per Mines

### 4.1 UX target

Lato player il gioco deve evolvere verso:

- shell piu' pulita
- focus sulla board
- CTA chiare
- recap mano
- storia delle mani
- info fairness leggibili

### 4.2 Cosa non mostrare al player

Da nascondere o tenere fuori dal percorso principale:

- strumenti di debug
- dettagli amministrativi
- informazioni non utili all'azione del giocatore

### 4.3 Mani / round report

Il giocatore deve poter consultare:

- round giocati
- esito
- importo puntato
- payout
- cronologia recente
- collegamento al dettaglio della mano

## 5. Indicazioni operative per il backoffice

### 5.1 Estratto conto generale

Direzione target:

- vista globale transazioni e mani
- sintesi del giocato e del vinto
- filtri temporali quando disponibili
- drill-down fino al dettaglio della singola mano o transazione

### 5.2 Vista giocatore

Ogni player deve avere un workspace admin con:

- dati account
- stato account
- wallet
- bonus / adjustment
- storico transazioni
- dettaglio delle giocate Mines

## 6. Ordine di esecuzione consigliato

Per restare coerenti con i vincoli gia' esistenti:

1. shell player e auth pages dedicate
2. promo/header/catalogo casino piu' credibili
3. rifinitura della shell Mines e apertura embedded-equivalent
4. estratto conto player e dettaglio mani
5. backoffice admin dedicato con dettaglio utente e reporting
6. delivery email reale di conferma quando il sottosistema notifiche verra' introdotto

## 7. Nota su RNG / provably fair

La comunicazione player-facing deve riflettere solo lo stato reale dell'implementazione.

Quindi:

- se esiste verifica interna con hash, seed e audit admin, si comunica quello
- non si dichiara un sistema `provably fair` completo lato player se non e' realmente esposto e verificabile da lui
- non si cita alcuna libreria esterna o vendor RNG se non effettivamente adottato nel codice

## 8. Conclusione

Questo documento chiarisce il salto di prodotto richiesto a CasinoKing:

- non solo motore corretto
- ma sito casino navigabile
- autenticazione credibile
- account leggibile
- Mines presentato come gioco reale
- backoffice utile per operare sui giocatori e leggere il business

Da qui in avanti le implementazioni devono usare questo documento come integrazione operativa del backlog di chiusura prodotto, senza indebolire i vincoli finanziari e server-authoritative gia' fissati dai documenti ufficiali.
