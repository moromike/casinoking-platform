# CasinoKing - Documento 33

Stato del progetto, analisi tecnica e guida di lettura per CTO

Stato del documento

- Documento operativo e di allineamento.
- Destinato a revisione tecnica approfondita.
- Va letto insieme ai Documenti 21, 22, 23, 30, 31 e 32.

## Aggiornamento operativo 2026-03-30

Questa fotografia riflette lo stato reale del repository al 30 marzo 2026.

### Stato reale aggiornato

- il backend platform contiene gia' i primi boundary espliciti sotto `backend/app/modules/platform/`
- Mines ha oggi anche un backoffice configurativo con bozza e pubblicazione live
- il renderer board del gioco e' stato estratto in `frontend/app/ui/mines-board.tsx`
- la route dedicata `/mines` esiste ed e' il punto corretto del prodotto gioco
- il frontend legacy del sito e dell'admin resta ancora ospitato nel contenitore condiviso `frontend/app/ui/casinoking-console.tsx`

### Rischio tecnico principale aggiornato

Il problema piu' delicato oggi non e' il backend finanziario ma la stabilita' del frontend Mines:

- `frontend/app/ui/mines-standalone.tsx` e' ancora troppo grande
- desktop, embed e mobile condividono ancora troppa logica nello stesso file
- il backoffice Mines vive ancora nella shell admin legacy

Quindi il progetto ha oggi due verita' contemporanee:

- lato backend la separazione platform/game e' iniziata nel verso corretto
- lato frontend la separazione e' avviata ma non ancora abbastanza profonda per evitare regressioni rapide

### Stato del backoffice Mines

Esiste gia' un flusso:

- `draft`
- `publish live`

per:

- regole HTML
- subset pubblicato di griglie e mine count
- label demo/real
- asset board `safe` e `mine`

Persistenza attuale:

- `backend/app/modules/games/mines/backoffice_config.py`
- migrazione `backend/migrations/sql/0011__mines_backoffice_draft_publish_assets.sql`

### Conclusione aggiornata

Il progetto non va buttato.

La direzione corretta e' confermata, ma il prossimo lavoro deve essere molto piu' conservativo sul frontend:

1. stabilizzare Mines come prodotto separato
2. separare il backoffice Mines dalla shell admin legacy
3. continuare il boundary backend platform/game senza reintrodurre coupling UI

## 1. Scopo del documento

Questo documento serve a spiegare in modo chiaro:

1. dove si trova oggi il progetto
2. cosa e' stato costruito davvero
3. quali problemi strutturali sono emersi
4. quali decisioni nuove sono state prese
5. come proseguire il lavoro senza ripetere gli errori di accoppiamento gia' emersi

Il documento e' scritto per un lettore tecnico che entra nel progetto a posteriori e ha bisogno di distinguere:

- stato reale del codice
- fondamenta corrette gia' presenti
- errori di impostazione architetturale emersi durante l'evoluzione UI
- target architecture approvata per il proseguimento

## 2. Executive summary

### 2.1 Cosa c'e' di buono

Il progetto non e' a zero. Esiste gia' una base forte lato piattaforma e lato motore:

- backend FastAPI con domini auth, wallet, ledger, admin e gioco
- modello finanziario non banale con ledger e wallet snapshot
- Mines con fairness, runtime config, reveal logic e cashout
- sito player con lobby/account/login/register
- backoffice admin in stato ancora acerbo ma gia' presente

### 2.2 Dove si e' verificato il problema

Il principale problema emerso non e' stato matematico o finanziario.

Il problema e' stato di boundary architetturale:

- `Mines` e' stato trattato troppo a lungo come una vista del sito
- sito, account, admin e gioco hanno condiviso troppo lo stesso contenitore frontend
- backend gioco e backend piattaforma sono rimasti troppo fusi

### 2.3 Decisione presa

La direzione ufficiale diventa:

1. `platform`
2. `game`
3. `aggregator`

con separazione esplicita tra:

- backend piattaforma
- backend gioco Mines
- frontend web/aggregatore
- frontend gioco Mines

## 3. Stato reale del codebase

## 3.1 Backend piattaforma attuale

Il backend attuale vive in:

- [backend/app](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app)

I domini principali gia' presenti sono:

- auth: [backend/app/api/routes/auth.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/api/routes/auth.py), [backend/app/modules/auth/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/auth/service.py)
- wallet: [backend/app/api/routes/wallets.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/api/routes/wallets.py), [backend/app/modules/wallet/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/wallet/service.py)
- ledger: [backend/app/api/routes/ledger.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/api/routes/ledger.py), [backend/app/modules/ledger/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/ledger/service.py)
- admin: [backend/app/api/routes/admin.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/api/routes/admin.py), [backend/app/modules/admin/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/admin/service.py)

### 3.1.1 Cosa fa gia' bene

- autenticazione player/admin
- bootstrap player con wallet iniziali
- ledger reporting
- bonus grant / adjustment / suspend
- owner-only access
- double-entry e snapshot wallet

### 3.1.2 Coupling da notare

Nel modulo auth, la creazione utente bootstrap include anche creazione ledger account, wallet account e signup credit:

- [backend/app/modules/auth/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/auth/service.py)

Questo e' coerente col dominio piattaforma.

## 3.2 Backend Mines attuale

I punti principali oggi sono:

- route API: [backend/app/api/routes/mines.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/api/routes/mines.py)
- service di gioco: [backend/app/modules/games/mines/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/service.py)
- fairness: [backend/app/modules/games/mines/fairness.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/fairness.py)
- runtime: [backend/app/modules/games/mines/runtime.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/runtime.py)
- randomness: [backend/app/modules/games/mines/randomness.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/randomness.py)

### 3.2.1 Cosa fa gia' bene

- configurazioni supportate del gioco
- fairness current / rotate / verify
- reveal logic server-authoritative
- payout runtime
- stato sessione di gioco
- metadati di audit della round

### 3.2.2 Dove il coupling e' troppo forte

Oggi [backend/app/modules/games/mines/service.py](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/backend/app/modules/games/mines/service.py) non fa solo logica di gioco.

In particolare:

- `start_session()` legge `wallet_accounts`, verifica saldo, crea `ledger_transactions`, scrive `ledger_entries`, aggiorna wallet e crea `game_sessions`
- `reveal_cell()` aggiorna lo stato round di gioco, che e' corretto
- `cashout_session()` crea posting ledger, aggiorna wallet e chiude la round

Questa e' la principale area di accoppiamento da risolvere.

In sintesi:

- fairness e RNG stanno gia' nel dominio corretto del gioco
- finanza e settlement stanno ancora dentro il service Mines, e questo non e' il target corretto

## 3.3 Frontend attuale

Il frontend attuale vive in:

- [frontend/app](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app)

### 3.3.1 Monolite web attuale

Le route seguenti montano ancora lo stesso contenitore:

- [frontend/app/page.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/page.tsx)
- [frontend/app/account/page.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/account/page.tsx)
- [frontend/app/login/page.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/login/page.tsx)
- [frontend/app/register/page.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/register/page.tsx)
- [frontend/app/admin/page.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/admin/page.tsx)

Tutte queste route usano ancora:

- [frontend/app/ui/casinoking-console.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/ui/casinoking-console.tsx)

Questo file e' stato il punto principale di coupling frontend.

### 3.3.2 Primo taglio corretto gia' fatto

La route `/mines` e' stata separata:

- [frontend/app/mines/page.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/mines/page.tsx)
- [frontend/app/ui/mines-standalone.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/ui/mines-standalone.tsx)

Questo e' il primo passo giusto per trattare Mines come prodotto separabile.

## 4. Problemi riscontrati durante il lavoro

## 4.1 Problema principale: confusione di dominio

Il dominio `web platform` e il dominio `game` sono stati mescolati.

Effetti concreti:

- login/register finivano troppo facilmente nel frame del gioco
- il gioco veniva rifinito come pagina del sito, non come prodotto autonomo
- ogni miglioramento grafico rischiava regressioni logiche

## 4.2 Problema frontend: contenitore unico

La presenza di un file monolitico come [casinoking-console.tsx](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/frontend/app/ui/casinoking-console.tsx) ha rallentato la chiarezza architetturale.

Conseguenze:

- toggle di vista multipli
- coupling tra route semanticamente diverse
- riapparizione di elementi non voluti
- difficolta' nel garantire che il gioco restasse davvero “esterno”

## 4.3 Problema backend: game service che fa anche settlement

La parte piu' delicata e' lato backend.

Il `service.py` di Mines oggi fa due lavori:

1. motore di gioco
2. motore finanziario della round

Questo e' il punto da rompere con attenzione, perche' qui non basta spostare file:

- vanno ripensati i contratti
- va introdotto il seamless wallet corretto
- va distinto il round lifecycle tecnico dal round lifecycle finanziario

## 4.4 Problema locale e operativo

Durante i test su Windows sono emerse anche difficolta' ambientali:

- mismatch di asset `_next` quando il frontend serviva build vecchie
- Docker Desktop non sempre attivo
- conflitto con un Postgres locale Windows gia' in ascolto su `5432`

Questo non e' il problema architetturale principale, ma ha aumentato il rumore operativo.

## 5. Decisioni nuove prese

## 5.1 Decisione 1 - separazione in prodotti

CasinoKing va trattato come insieme di prodotti:

1. `Platform`
2. `Game`
3. `Aggregator`

Riferimento:

- [Documento 30](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_30_Separazione_Prodotti_Piattaforma_Gioco_Aggregatore.md)

## 5.2 Decisione 2 - seamless wallet

Il wallet appartiene alla piattaforma.

Il gioco non deve piu':

- debitare direttamente il saldo
- accreditare direttamente le vincite
- scrivere direttamente su ledger

Riferimento:

- [Documento 31](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_31_Contratto_Tra_Platform_Backend_E_Mines_Backend.md)

## 5.3 Decisione 3 - distinzione tra due sessioni

Vanno distinti:

1. `play session`
2. `round session`

### 5.3.1 Play session

Da ingresso del player nel gioco a uscita dal gioco.

### 5.3.2 Round session

Da accettazione puntata a chiusura della partita.

Questa distinzione e' fondamentale per:

- auditing
- launch token
- settlement
- integrazione tra platform e game

## 5.4 Decisione 4 - token di handoff

Serve introdurre un token esplicito tra platform e game.

Il bearer piattaforma non e' sufficiente come modello target.

Serve un `game_launch_token` o equivalente.

## 6. Cosa va cambiato nel codice

## 6.1 Frontend

### Da fare

1. togliere definitivamente i residui Mines dal monolite web
2. lasciare `web platform` nel contenitore legacy solo in fase transitoria
3. portare il frontend Mines verso app propria nel monorepo

### Conseguenza

Il gioco puo' essere iterato senza trascinare sito/account/admin.

## 6.2 Backend

### Da fare

1. estrarre il settlement finanziario da `backend/app/modules/games/mines/service.py`
2. lasciare in Mines:
   - config
   - RNG
   - fairness
   - reveal
   - payout result
3. spostare in platform:
   - open round
   - debit initial bet
   - settle final payout
   - round accounting

## 6.3 API

### Da introdurre

1. launch token / handoff contract
2. platform -> game authorization
3. game -> platform round open
4. game -> platform round settle

## 7. Piano di esecuzione raccomandato

Riferimento operativo:

- [Documento 32](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_32_Piano_Migrazione_Da_Monolite_Frontend_A_Prodotti_Separati.md)

Ordine raccomandato:

1. consolidare separazione frontend di Mines
2. progettare contratti platform <-> game
3. introdurre token di handoff
4. spostare round settlement fuori da Mines service
5. solo dopo decidere se separare anche fisicamente repo o app

## 8. Conclusione

Il progetto ha fondamenta valide ma confini ancora incompleti.

La correzione non richiede buttare via tutto.

Richiede:

- riconoscere che esistono piu' prodotti
- formalizzare i confini
- migrare il codebase con priorita' architetturale prima che cosmetica

La decisione presa e' quindi netta:

- non trattare piu' Mines come vista del sito
- non trattare piu' il backend gioco come backend finanziario
- usare il lavoro fatto come base, ma cambiare il modello di integrazione per i prossimi step

## 9. Documenti operativi aggiuntivi da leggere subito

Per passare dall'analisi alla migrazione concreta, leggere anche:

- [Documento 36](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_36_CTO_Reading_Order_Esecutivo.md)
- [Documento 34](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_34_Contratto_API_Operativo_Platform_Mines_v1.md)
- [Documento 35](c:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/md/CasinoKing_Documento_35_Mappatura_Codebase_Attuale_E_Split_Target.md)

Il Documento 36 serve come porta di ingresso rapida per revisione CTO.

Il Documento 34 traduce il modello target in API e sequenze operative minime.

Il Documento 35 traduce l'analisi architetturale in mappatura esplicita dei file attuali e dei confini target di split.
