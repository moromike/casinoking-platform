# CasinoKing - M1 File-by-File Execution Plan

Piano Operativo File-per-File per la Prima Milestone di Hardening del Boundary Platform/Game

## Stato del documento

- Documento operativo di esecuzione.
- Va letto insieme a:
  - [PLATFORM_GAME_SEPARATION_AND_ENVIRONMENTS_MASTERPLAN_2026_04.md](C:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/PLATFORM_GAME_SEPARATION_AND_ENVIRONMENTS_MASTERPLAN_2026_04.md)
  - [PLATFORM_GAME_CONTRACT_AND_ENVIRONMENTS_IMPLEMENTATION_BLUEPRINT_2026_04.md](C:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/PLATFORM_GAME_CONTRACT_AND_ENVIRONMENTS_IMPLEMENTATION_BLUEPRINT_2026_04.md)
  - [PLATFORM_GAME_M1_EXECUTION_PACKAGE_2026_04.md](C:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/PLATFORM_GAME_M1_EXECUTION_PACKAGE_2026_04.md)
- Scopo:
  - definire esattamente quali file toccare in M1
  - chiarire in quale ordine toccarli
  - limitare il perimetro di modifica
  - ridurre il rischio di regressioni

## 1. Obiettivo operativo di M1

M1 deve migliorare il boundary interno tra:

- dominio gioco Mines
- dominio platform finanziario

senza:

- cambiare il contratto pubblico del frontend player
- cambiare il routing esterno in modo rompente
- introdurre nuove feature utente
- introdurre migrazioni profonde non strettamente necessarie

In pratica:

`M1 = chiarire e rafforzare il confine, non ridisegnare l'intero sistema`

## 2. Strategia di intervento

La strategia corretta e' questa:

1. toccare prima il punto di confine
2. toccare poi l'orchestrazione gioco solo dove necessario
3. evitare di toccare il core finanziario salvo minimi adattamenti
4. non toccare il frontend nella prima fase
5. non toccare le route pubbliche se non strettamente necessario

Questo porta a un ordine molto preciso.

## 3. File da toccare in M1

## 3.1 File 1 - `backend/app/modules/games/mines/round_gateway.py`

### Ruolo del file

Questo e' il file piu' importante della milestone.

E' il punto in cui:

- il dominio gioco parla con il dominio platform
- il boundary puo' diventare davvero piu' esplicito

### Perche' va toccato

Perche' oggi il gateway esiste gia', ma deve diventare il confine ufficiale e leggibile della relazione `game -> platform`.

### Obiettivo specifico

Rendere il gateway piu' simile a un contratto esplicito e meno a un bridge implicito.

### Cosa vogliamo ottenere

- input chiari di dominio gioco
- output chiari di dominio platform
- nomenclatura meno ambigua
- esplicitazione di `platform_round_id` anche se oggi coincide ancora con l'ID della round gioco

### Tipi di modifica ammissibili

- refactor di naming interno
- chiarimento shape dei return object
- commenti strutturali succinti se servono a rendere il boundary leggibile
- eventuale introduzione di strutture dati piu' esplicite

### Cosa non dobbiamo fare qui

- non cambiare il comportamento economico
- non cambiare idempotenza
- non cambiare SQL finanziario
- non introdurre nuova logica di business lato game o lato ledger

### Rischio

Medio.

E' il file giusto da toccare, ma e' connesso a round opening e settlement.

### Verifica minima dopo la modifica

- import/backend sanity
- flow `start round`
- flow `cashout`
- idempotency non rotta

## 3.2 File 2 - `backend/app/modules/games/mines/service.py`

### Ruolo del file

E' l'orchestratore principale del gioco.

### Perche' va toccato

Perche' oggi conosce ancora troppo da vicino il sequencing del lifecycle economico.

### Obiettivo specifico

Ridurre il coupling verso la piattaforma facendo passare piu' chiaramente tutto cio' che e' finanziario attraverso il gateway.

### Cosa vogliamo ottenere

- servizio gioco piu' leggibile
- responsabilita' piu' pulite
- meno riferimenti impliciti a dettagli platform
- stessa surface pubblica

### Tipi di modifica ammissibili

- riorganizzazione locale del flusso start/settlement
- chiarimento delle variabili e degli oggetti scambiati con il gateway
- eventuale riduzione di dettagli platform maneggiati direttamente nel service

### Cosa non dobbiamo fare qui

- non cambiare il contratto pubblico degli endpoint
- non cambiare il comportamento di reveal
- non fare refactor larghi del file fuori dal perimetro boundary
- non introdurre migliorie "nice to have" non richieste

### Rischio

Alto, se toccato troppo.
Medio, se toccato con disciplina e solo nei punti boundary.

### Verifica minima dopo la modifica

- `start`
- `reveal`
- `cashout`
- `get session`
- `get fairness`

## 3.3 File 3 - `backend/app/modules/platform/game_launch/service.py`

### Ruolo del file

Gestisce emissione e validazione del `game_launch_token`.

### Perche' potrebbe essere toccato

Non e' necessariamente il focus primario di M1, ma potrebbe richiedere un piccolo allineamento di naming e ownership.

### Obiettivo specifico

Solo se necessario:

- migliorare chiarezza concettuale
- rendere piu' leggibile il ruolo platform del launch token

### Tipi di modifica ammissibili

- piccoli rename interni
- commenti minimi di ownership
- chiarimenti sul payload se utili e non rompenti

### Cosa non dobbiamo fare qui

- non introdurre token consumption tracking in M1
- non riscrivere la security policy
- non cambiare il contratto esterno se non necessario

### Rischio

Basso se toccato poco.
Medio se lo si allarga troppo.

### Verifica minima dopo la modifica

- issue token
- validate token
- launch Mines autenticato

## 3.4 File 4 - `backend/app/api/routes/mines.py`

### Ruolo del file

Surface pubblica del gioco Mines.

### Perche' potrebbe essere toccato

Solo come file satellite, se serve riallineare naming, payload o mapping interno al gateway.

### Obiettivo specifico

Mantenere stabilita' della surface pubblica.

### Tipi di modifica ammissibili

- adeguamenti minimi non rompenti
- allineamento di nomi interni o shape di risposta se strettamente necessari

### Cosa non dobbiamo fare qui

- non cambiare i path pubblici
- non cambiare il flusso player-facing
- non fare redesign route

### Rischio

Medio, perche' tocca il boundary pubblico.

### Regola

Toccarlo solo se strettamente obbligatorio.

## 3.5 File 5 - `backend/app/modules/platform/rounds/service.py`

### Ruolo del file

Core economico della round.

### Perche' NON dovrebbe essere un focus di M1

Perche' e' una delle aree piu' sensibili del sistema.

### Obiettivo specifico

Toccarlo solo se emerge una necessita' minima e ben motivata dal boundary.

### Tipi di modifica ammissibili

- adattamenti minimi non invasivi
- nessuna ristrutturazione logica

### Cosa non dobbiamo fare qui

- non rifare il modello round
- non rifare ledger interaction
- non cambiare idempotenza
- non introdurre nuovi side effect

### Rischio

Alto.

### Decisione

Se possibile, lasciarlo intatto in M1.

## 3.6 File che NON devono entrare in M1

Questa lista e' importante quanto quella dei file da toccare.

### Non toccare in M1

- `frontend/app/ui/mines/mines-standalone.tsx`
- `frontend/app/ui/casinoking-console.tsx`
- `frontend/app/ui/player-lobby-page.tsx`
- `frontend/app/ui/player-account-page.tsx`
- file admin UI
- CSS
- Docker / infra deployment reali
- migrazioni DB profonde

### Perche'

Perche' M1 e' una milestone di chiarimento del boundary backend.

Se la mischiamo con frontend o ambienti, aumentiamo il rischio senza aumentare davvero la qualita' della decisione architetturale.

## 4. Ordine di esecuzione consigliato

## Step 1 - Preparazione tecnica

File:

- nessun file di produzione modificato subito

Attivita':

- rilettura dei documenti M1
- rilettura puntuale di `round_gateway.py` e dei call site in `mines/service.py`
- definizione del shape target degli oggetti scambiati

Output:

- perimetro confermato

## Step 2 - Intervento sul gateway

File:

- `backend/app/modules/games/mines/round_gateway.py`

Attivita':

- rendere piu' esplicita la semantica del boundary
- chiarire input/output

Output atteso:

- gateway piu' leggibile
- confine piu' ufficiale

## Step 3 - Adattamento minimo del service gioco

File:

- `backend/app/modules/games/mines/service.py`

Attivita':

- riallineare il flusso di start/settlement al gateway piu' esplicito
- ridurre coupling

Output atteso:

- servizio piu' pulito
- nessun breaking change esterno

## Step 4 - Eventuale ritocco satellite

File:

- `backend/app/modules/platform/game_launch/service.py`
- `backend/app/api/routes/mines.py`

Attivita':

- solo se necessario
- solo modifiche minime non rompenti

Output atteso:

- naming piu' coerente

## Step 5 - Verifica

Attivita':

- import/backend sanity
- smoke flow dei percorsi sensibili

Output atteso:

- conferma che il boundary e' migliorato e il comportamento pubblico e' stabile

## 5. Test e verifiche minime per ogni step

## 5.1 Dopo Step 2

- il gateway compila/importa correttamente
- `start` non e' rotto nei tipi e negli oggetti scambiati

## 5.2 Dopo Step 3

- avvio round
- reveal
- cashout
- recupero sessione
- fairness session

## 5.3 Dopo Step 4

- issue launch token
- validate launch token
- launch gioco autenticato

## 5.4 Build / sanity minima finale

- backend import sanity
- eventuale test suite mirata se disponibile sui moduli toccati

## 6. Rischi principali del piano

## 6.1 Rischio: toccare troppo `mines/service.py`

Mitigazione:

- limitare l'intervento alle funzioni boundary
- evitare refactor "pulizia generale"

## 6.2 Rischio: introdurre un nuovo linguaggio di naming ma senza vero vantaggio

Mitigazione:

- usare rename o wrapper solo se rendono piu' chiaro il confine

## 6.3 Rischio: toccare accidentalmente il core finanziario

Mitigazione:

- `platform/rounds/service.py` fuori scope salvo minima necessita'

## 6.4 Rischio: mescolare boundary e Beta

Mitigazione:

- nessun deploy Beta in M1
- Beta resta milestone successiva

## 7. Cosa significa "successo pulito"

M1 sara' pulita se:

- il codice e' piu' leggibile
- il gateway e' piu' esplicito
- il servizio gioco ragiona meno in termini finanziari
- il frontend non si accorge del cambiamento
- non abbiamo dovuto aprire una cascata di fix collaterali

## 8. Decisione operativa finale

Se si apre lo sviluppo, l'ordine corretto e':

1. `round_gateway.py`
2. `mines/service.py`
3. solo se serve `game_launch/service.py`
4. solo se obbligato `routes/mines.py`
5. evitare `platform/rounds/service.py` se non strettamente necessario

Questo e' il percorso che, ad oggi, considero piu' maturo e prudente.

## 9. Sintesi estrema

### File principali da toccare

- `round_gateway.py`
- `mines/service.py`

### File secondari solo se serve

- `game_launch/service.py`
- `routes/mines.py`

### File da non toccare

- frontend
- CSS
- admin UI
- infra beta/prod
- core finanziario sensibile, salvo minimi adattamenti

### Obiettivo

Rendere il confine `platform <-> game` piu' chiaro senza rompere il prodotto.

## 10. Stato esecuzione - 30 Aprile 2026

### Eseguito

File toccati:

- `backend/app/modules/games/mines/round_gateway.py`
- `backend/app/modules/games/mines/service.py`
- `backend/app/modules/platform/rounds/service.py`
- `backend/app/modules/platform/access_sessions/service.py`
- `tests/integration/test_financial_and_mines_flows.py`

Motivo dei due file platform:

- `platform/rounds/service.py` e' stato toccato in modo minimo per rendere stabile la risposta idempotente del cashout.
- `platform/access_sessions/service.py` e' stato toccato in modo minimo per valorizzare `settlement_ledger_transaction_id` anche nel percorso auto-cashout da timeout.

### Verifiche completate

- compile Python sui moduli toccati
- contract boundary tests
- financial and Mines integration tests
- Mines concurrency tests
- platform access session tests
- smoke API reale su ambiente locale

### Nota di continuita'

La milestone M1 non e' una separazione completa del dominio platform/game.
E' il primo hardening conservativo: il boundary e' piu' esplicito, ma la rimozione completa dei dettagli `platform_rounds` dal service Mines resta lavoro successivo.
