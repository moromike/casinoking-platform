# CasinoKing – Documento 06

Mines: Prodotto, Stati, Matematica, API e Integrazione Ledger

Versione sviluppatori / condivisibile con team tecnico

Scopo del documento
Definire il primo gioco della piattaforma CasinoKing: Mines. Il documento descrive il prodotto, i flussi utente, gli stati di gioco, la responsabilità tra frontend e backend, la matematica di base, le API candidate e i movimenti di ledger collegati a bet, reveal, loss e cashout.

## 1. Obiettivo del modulo Mines

Livello semplice

- Mines è il primo gioco reale della demo CasinoKing.
- Deve essere credibile come prodotto, semplice da capire e abbastanza ricco da far emergere i concetti core della piattaforma.
- Deve funzionare con chip finte, ma con architettura già adatta a un futuro contesto più rigoroso.

Livello tecnico

- Il gioco sarà server-authoritative: il frontend non decide né il layout delle mine né il risultato.
- Il modulo deve integrarsi con auth, wallet, ledger, reporting e admin.
- Il design deve essere riusabile in futuro per giochi aggiuntivi e per eventuale distribuzione esterna.

## 2. Scope di prodotto del gioco

| Area | Decisione | Nota |
| --- | --- | --- |
| Tipo gioco | Mines | Instant game |
| Grid size | 9, 16, 25, 36, 49 | Configurabile |
| Mine count | Scelta utente | Entro limiti consentiti |
| Bet | Importo inserito prima dello start | Una partita = una bet |
| Cashout | Manuale | Disponibile dopo reveal sicuri |
| Wallet | Cash + Bonus | Regole di priorità da definire a livello piattaforma |
| Modalità | Solo chip finte nel MVP | Architettura robusta da subito |

Nota: la priorità di consumo Cash/Bonus sarà definita a livello piattaforma; questo documento assume che il motore di gioco riceva una sorgente fondi già validata.

## 3. User flow principale

Livello semplice

1. Il player entra nella lobby e apre Mines.
2. Sceglie dimensione griglia, numero di mine e importo della bet.
3. Conferma lo start della partita.
4. Il backend crea la sessione e registra la bet.
5. Il player apre caselle una alla volta.
6. Se trova una mina, la partita termina in perdita.
7. Se apre solo caselle sicure, il moltiplicatore cresce.
8. In qualunque momento utile, il player può fare cashout.
9. Il backend chiude la partita e registra l’esito nel ledger.

Diagramma logico del flusso

```text
Lobby / UI
↓
Config partita (grid, mines, bet)
↓
POST /games/mines/start
↓
Sessione attiva lato backend
↓
Reveal 1..N oppure Cashout
↓
Loss oppure Win
↓
Ledger + reporting + risposta UI
```

## 4. Stati della partita

Livello semplice

- created: richiesta ricevuta ma non ancora confermata/avviata
- active: partita aperta e reveal consentiti
- won: chiusa con cashout valido
- lost: chiusa dopo reveal di una mina
- cancelled/void: stato tecnico eccezionale da usare con molta cautela

Livello tecnico

| Stato | Descrizione | Azioni permesse | Uscite possibili |
| --- | --- | --- | --- |
| created | Sessione inizializzata | Nessuna o solo conferma interna | active / cancelled |
| active | Gioco in corso | reveal, cashout | won / lost |
| won | Cashout completato | nessuna | finale |
| lost | Mina trovata | nessuna | finale |
| cancelled | Anomalia o timeout gestito | nessuna | finale |

## 5. Separazione responsabilità frontend / backend

| Area | Frontend | Backend |
| --- | --- | --- |
| UI | Rendering griglia, animazioni, input utente | N/A |
| Validazione formale | Controlli base su campi | Validazione definitiva |
| Scelta mine | Mai | Sempre |
| Outcome | Mai | Sempre |
| Payout | Solo visualizzazione | Calcolo effettivo |
| Persistenza | Nessuna fonte di verità | Database e ledger |
| Stato partita | Vista locale derivata | Fonte di verità |

Regola d’oro: il frontend non deve poter determinare né forzare il risultato della partita.

## 6. Modello applicativo del gioco

```text
Game UI (frontend)
Mines API controller
Mines service / state machine
Mines math / payout engine
Ledger + wallet + reporting
```

## 7. Dati principali della sessione Mines

| Campo | Tipo logico | Uso |
| --- | --- | --- |
| game_session_id | UUID | Identificatore univoco |
| user_id | UUID | Proprietario sessione |
| grid_size | int | 9/16/25/36/49 |
| mine_count | int | Numero mine |
| bet_amount | decimal | Bet iniziale |
| status | enum | created/active/won/lost/cancelled |
| safe_reveals_count | int | Caselle sicure aperte |
| revealed_cells | array/json | Storico caselle aperte |
| multiplier_current | decimal | Moltiplicatore attuale |
| payout_current | decimal | Valore cashout potenziale |
| seed/version info | text/json | Per fairness/audit futuri |
| created_at / closed_at | timestamp | Audit e reporting |

## 8. Matematica del gioco – impostazione iniziale

Livello semplice

- Il payout dipende da: dimensione griglia, numero di mine, numero di caselle sicure già aperte.
- Più mine si scelgono, maggiore è il rischio e maggiore è il payout potenziale.
- Ogni reveal sicuro aumenta il moltiplicatore.

Livello tecnico

- Per una griglia con N celle e M mine, al reveal k (con k reveal sicuri già effettuati), la probabilità di trovare ancora una safe cell al passo successivo è: (N - M - k) / (N - k).
- Il moltiplicatore teorico lordo può essere derivato dal prodotto inverso delle probabilità di sopravvivenza.
- Il moltiplicatore effettivo del gioco applicherà una house edge definita a livello di configurazione.
- La formula esatta dei payout sarà versionata e fissata in un documento matematico separato, così da mantenere auditabilità delle modifiche.

Schema concettuale payout

```text
N = celle totali
M = mine
k = safe reveals già completati

Probabilità safe al reveal successivo = (N - M - k) / (N - k)
Moltiplicatore lordo progressivo = prodotto inverso delle probabilità di sopravvivenza
Moltiplicatore finale = moltiplicatore lordo × (1 - house_edge)
```

Questo documento non congela ancora i payout finali numerici. Li congeleremo in un documento matematico dedicato, con tabelle per tutte le combinazioni consentite.

## 9. Regole di validazione

- La bet deve essere > 0 e dentro i limiti di piattaforma.
- La combinazione grid_size + mine_count deve essere consentita.
- Non si può fare reveal su una casella già aperta.
- Non si può fare cashout se la sessione non è active.
- Non si può fare reveal dopo win/loss/cancelled.
- Le richieste devono essere idempotenti dove serve, soprattutto su start e cashout.

## 10. API candidate del modulo Mines

| Metodo | Endpoint | Uso | Esito principale |
| --- | --- | --- | --- |
| POST | /games/mines/start | Crea partita e registra bet | session active |
| POST | /games/mines/reveal | Apre una cella | safe reveal o loss |
| POST | /games/mines/cashout | Chiude con vincita | won |
| GET | /games/mines/session/{id} | Recupera stato partita | session snapshot |
| GET | /games/mines/config | Recupera limiti e opzioni | config |

### 10.1 Payload concettuali

Start request

{ "grid_size": 25, "mine_count": 3, "bet_amount": "10.00" }

Reveal request

{ "game_session_id": "...", "cell_index": 7 }

Cashout request

{ "game_session_id": "..." }

## 11. Eventi ledger collegati al gioco

Livello semplice

- Start: il sistema registra la bet.
- Loss: nessun accredito aggiuntivo; la partita si chiude.
- Cashout: il sistema registra la vincita.
- Tutto deve restare tracciato in modo auditabile.

Livello tecnico

| Evento di gioco | Ledger | Quando | Nota |
| --- | --- | --- | --- |
| start | BET | alla creazione sessione | debita il wallet |
| reveal safe | nessun movimento | durante active | aggiorna solo stato e payout potenziale |
| reveal mine | nessun accredito | quando scoppia | chiusura in loss |
| cashout | WIN | alla chiusura vincente | accredito payout |
| admin void eccezionale | REVERSAL/ADJUSTMENT | solo casi speciali | strettamente controllato |

## 12. Concorrenza e sicurezza

- Reveal e cashout devono operare con controllo di stato e lock transazionale dove necessario.
- Due richieste quasi simultanee non devono poter chiudere la stessa sessione due volte.
- Il backend deve validare che la sessione appartenga all’utente autenticato.
- I dettagli sensibili del layout mine non devono essere esposti prima della chiusura, salvo quanto strettamente necessario alla UX.
- Ogni cambio di stato deve essere registrato con timestamp e metadati sufficienti per audit.

## 13. Reporting e analytics minimi

- Numero partite avviate
- Bet totale per configurazione
- Numero loss / win
- Distribuzione per grid size e mine count
- Payout totale
- GGR teorico del gioco nella modalità chip finte

## 14. Evoluzioni future già previste

- Tabella payout versionata per tutte le combinazioni consentite
- Auto bet / auto cashout
- Provably fair o meccanismo equivalente, se scelto
- Esposizione del gioco verso integrazioni esterne
- Estrazione del modulo in repository separata quando stabile

## 15. Decisioni prese finora

- Mines è il primo gioco della piattaforma.
- Il gioco deve essere leggermente evoluto, non minimale.
- Configurazioni iniziali previste: grid size 9, 16, 25, 36, 49.
- L’utente potrà scegliere il numero di mine.
- Architettura server-authoritative.
- Integrazione nativa con wallet e double-entry ledger robusto.

## 16. Punti aperti

- Range esatto consentito del mine_count per ciascuna griglia
- Tabella payout definitiva e house edge
- Regola precisa di consumo Cash vs Bonus
- Policy di reveal del board finale alla chiusura
- Meccanismo fairness / seed da adottare in futuro

Conclusione
Questo documento definisce Mines come primo modulo di gioco reale di CasinoKing. Il passo successivo consigliato è il Documento 07, dedicato alla matematica congelata del gioco: limiti, payout table, esempi numerici e test cases.
