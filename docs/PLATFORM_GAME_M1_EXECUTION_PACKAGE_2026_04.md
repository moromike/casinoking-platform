# CasinoKing - M1 Execution Package

Glossario ID, Mapping Endpoint e Perimetro della Prima Milestone di Implementazione

## Stato del documento

- Documento operativo di pre-esecuzione.
- Chiude il pacchetto analitico aperto con:
  - [PLATFORM_GAME_SEPARATION_AND_ENVIRONMENTS_MASTERPLAN_2026_04.md](C:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/PLATFORM_GAME_SEPARATION_AND_ENVIRONMENTS_MASTERPLAN_2026_04.md)
  - [PLATFORM_GAME_CONTRACT_AND_ENVIRONMENTS_IMPLEMENTATION_BLUEPRINT_2026_04.md](C:/Users/michelem.INSIDE/Downloads/Personale/Projects-personal/casinoking-platform/docs/PLATFORM_GAME_CONTRACT_AND_ENVIRONMENTS_IMPLEMENTATION_BLUEPRINT_2026_04.md)
- Scopo:
  - togliere ambiguita' residue
  - definire cosa entra e cosa non entra nella prima milestone di codice
  - ridurre il rischio di regressioni prima di iniziare a implementare

## 1. Obiettivo della Milestone 1

La Milestone 1 non deve:

- portare online Beta
- rendere Mines un provider esterno reale
- cambiare il contratto pubblico del frontend
- introdurre grandi migrazioni infrastrutturali

La Milestone 1 deve:

- chiarire definitivamente ownership e naming
- consolidare il boundary interno `game -> gateway -> platform`
- preparare il progetto per i passi successivi senza rompere i flussi esistenti

In sintesi:

`M1 = chiarezza e hardening interno, non rivoluzione esterna`

## 2. Criteri di successo di M1

M1 e' riuscita se, alla fine, possiamo dire:

1. gli identificatori sono descritti in modo univoco
2. il contratto interno e' piu' esplicito di oggi
3. il servizio gioco e' meno consapevole dei dettagli finanziari
4. il comportamento pubblico verso frontend non e' cambiato in modo rompente
5. il codice e' piu' pronto per M2 e per la progettazione Beta

## 3. Glossario ufficiale degli identificatori

Questa sezione serve a evitare uno dei problemi piu' subdoli del progetto: avere tanti ID sensati ma non abbastanza ben separati.

## 3.1 `player_id`

### Significato

Identificatore del player nella piattaforma.

### Ownership

- platform

### Dove nasce

- autenticazione / user model platform

### Dove si usa

- auth
- wallet
- ledger
- reporting
- launch token
- round open / settle

### Note

Il gioco puo' conoscerlo come claim o campo di contratto, ma non ne e' owner.

## 3.2 `platform_session_id`

### Significato

Identificatore della sessione applicativa della piattaforma legata al lancio gioco.

### Ownership

- platform

### Dove nasce

- `platform/game_launch/service.py`

### Dove si usa

- claims del `game_launch_token`
- audit di launch
- correlazione tra UI platform e ingresso gioco

### Note

Non e' la round e non e' l'access session.

## 3.3 `access_session_id`

### Significato

Sessione estesa di presenza del player nel gioco.

### Ownership

- platform

### Dove nasce

- `platform/access_sessions/service.py`

### Dove si usa

- audit
- analytics
- reporting sessioni
- gating del round start
- lifecycle player nel gioco

### Note

Questa non e' una round economica.
E' la permanenza del player nel gioco.

## 3.4 `play_session_id`

### Significato

Nel codice attuale e' un identificatore emesso nel launch token.

### Ownership

- platform, nello stato attuale

### Stato

- concetto esistente ma da chiarire meglio

### Decisione raccomandata

Nel breve periodo non va eliminato a forza.
Va pero' documentato come elemento di launch/handoff, non come round.

## 3.5 `game_play_session_id`

### Significato

Identificatore tecnico del lato gioco associato al launch.

### Ownership

- game, concettualmente

### Stato

- presente nel token attuale

### Decisione raccomandata

Va mantenuto solo se utile a distinguere davvero il lifecycle tecnico di presenza lato gioco.
Se resta, va spiegato bene.
Se non serve, in futuro si potra' semplificare.

## 3.6 `platform_round_id`

### Significato

Identificatore della round economica lato piattaforma.

### Ownership

- platform

### Dove nasce

- idealmente nel servizio/platform contract di apertura round

### Dove si usa

- ledger
- settlement
- reporting economico
- riconciliazione

### Stato attuale

- oggi coincide troppo con l'ID round/sessione usato dal gioco

### Decisione raccomandata

M1 deve almeno renderne esplicito il ruolo, anche se l'ID non viene ancora separato fisicamente.

## 3.7 `game_round_id` o `game_session_id`

### Significato

Identificatore della round tecnica del gioco.

### Ownership

- game

### Dove si usa

- reveal
- fairness
- replay
- stato tecnico

### Stato attuale

- oggi e' molto accoppiato al `platform_round_id`

### Decisione raccomandata

In M1 non serve separarlo fisicamente per forza.
Serve separarlo concettualmente in modo inequivoco.

## 4. Regole di naming ufficiali proposte

Per ridurre la confusione futura, propongo queste regole.

### 4.1 Regola generale

Se un ID appartiene alla piattaforma, il nome deve dirlo.
Se appartiene al gioco, il nome deve dirlo.

### 4.2 Nomi raccomandati

- `player_id`
- `platform_session_id`
- `access_session_id`
- `platform_round_id`
- `game_round_id`
- `game_play_session_id`

### 4.3 Nomi da evitare nel futuro

- `session_id` generico senza contesto
- `round_id` generico senza ownership
- `play_id` senza dominio

### 4.4 Regola di transizione

Se nel codice attuale un nome generico non puo' essere eliminato subito:

- si documenta
- si wrappa
- si rende piu' esplicito nei boundary

Non si fa un rename massivo se non porta beneficio reale immediato.

## 5. Mapping endpoint attuale -> target

Questa e' la tabella pratica da usare quando inizieremo a toccare il codice.

## 5.1 Launch token issuance

### Attuale

- `POST /games/mines/launch-token`

### Ownership concettuale attuale

- platform logic esposta sotto namespace game

### Target

- `POST /platform/game-launch`
oppure
- `POST /internal/v1/platform/game-launch/issue`

### Decisione M1

- non spostare la route pubblica
- documentare che l'ownership e' platform
- preparare il terreno per M2

## 5.2 Launch token validation

### Attuale

- `POST /games/mines/launch/validate`

### Ownership concettuale

- validate lato game di un token platform

### Target

- `POST /internal/v1/games/mines/launch/validate`

### Decisione M1

- non cambiare contract pubblico
- chiarire il boundary nel documento e nel codice interno

## 5.3 Access session create

### Attuale

- `POST /access-sessions`

### Target

- invariato concettualmente

### Decisione M1

- nessun cambio importante

## 5.4 Access session ping

### Attuale

- `POST /access-sessions/{access_session_id}/ping`

### Target

- invariato concettualmente

### Decisione M1

- nessun cambio importante

## 5.5 Game start

### Attuale

- `POST /games/mines/start`

### Target concettuale

- public game start stabile
- internally routed through explicit platform round open contract

### Decisione M1

- mantenere API pubblica
- migliorare il contract interno e la chiarezza degli output

## 5.6 Reveal

### Attuale

- `POST /games/mines/reveal`

### Target

- invariato

### Decisione M1

- fuori scope

## 5.7 Cashout

### Attuale

- `POST /games/mines/cashout`

### Target concettuale

- public game API
- internal settle contract verso platform

### Decisione M1

- mantenere API pubblica
- nessun cambio pubblico
- boundary interno solo chiarito, non rivoluzionato

## 5.8 Session retrieval

### Attuale

- `GET /games/mines/session/{id}`
- `GET /games/mines/session/{id}/fairness`

### Target

- invariato come ownership gioco

### Decisione M1

- fuori scope

## 6. Mapping file attuale -> ruolo target

Questa sezione serve a evitare edit trasversali inutili.

## 6.1 `backend/app/api/routes/mines.py`

### Ruolo attuale

- surface pubblica del gioco
- contiene anche launch token issue/validate

### Ruolo target

- surface pubblica del gioco
- con meno preoccupazioni platform esposte direttamente

### Decisione M1

- toccare solo se necessario per commenti strutturali, naming o adapter
- non rivoluzionare le route

## 6.2 `backend/app/api/routes/platform_access.py`

### Ruolo attuale

- access session platform

### Ruolo target

- resta base platform per lifecycle di accesso

### Decisione M1

- probabilmente intoccato

## 6.3 `backend/app/modules/platform/game_launch/service.py`

### Ruolo attuale

- issue e validate del launch token

### Ruolo target

- modulo platform ufficiale di launch authorization

### Decisione M1

- possibile chiarimento naming/ownership
- nessun hardening security profondo ancora

## 6.4 `backend/app/modules/games/mines/round_gateway.py`

### Ruolo attuale

- adapter tra gioco e platform rounds

### Ruolo target

- boundary ufficiale tra game domain e financial platform domain

### Decisione M1

- file principale della milestone
- da rendere piu' esplicito e piu' "contratto" che semplice bridge implicito

## 6.5 `backend/app/modules/games/mines/service.py`

### Ruolo attuale

- orchestration di gameplay e parte del sequencing transitorio platform

### Ruolo target

- service di gameplay che usa boundary pulito verso platform

### Decisione M1

- toccarlo con molta disciplina
- ridurre coupling
- non cambiare il comportamento pubblico

## 6.6 `backend/app/modules/platform/rounds/service.py`

### Ruolo attuale

- core economico delle round

### Ruolo target

- settlement authority platform

### Decisione M1

- non toccare a meno che serva minimo adattamento non rischioso
- questa parte e' troppo sensibile per refactor esplorativi

## 7. Scope M1: cosa entra

Entrano in M1 soltanto cambiamenti di chiarimento e boundary hardening a basso rischio.

### Entra

- documentazione ID e ownership
- miglior chiarezza del gateway
- migliore esplicitazione di `platform_round_id`
- migliore leggibilita' del contract tra game service e gateway
- eventuali nomi/adapter interni non rompenti

### Non entra

- deploy Beta
- refactor frontend importante
- spostamento massivo route
- token consumption tracking
- separazione fisica repo
- migrazioni schema profonde
- breaking changes API pubbliche

## 8. Deliverable attesi di M1

Se facciamo codice su M1, i deliverable dovrebbero essere:

1. documenti aggiornati/allineati
2. boundary contract interno piu' esplicito
3. codice gioco meno accoppiato ai dettagli platform
4. nessuna regressione pubblica evidente sui flow Mines

## 9. Verifiche minime richieste per M1

Per evitare lavoro sporco, le verifiche minime devono essere poche ma giuste.

### 9.1 Build e static checks

- backend import sanity
- frontend build se toccato qualche contratto condiviso

### 9.2 Smoke flow funzionali

- launch Mines autenticato
- access session create/ping
- start round
- reveal
- cashout
- load session e fairness

### 9.3 Focus dei controlli

Non serve testare tutto il prodotto.

Serve testare solo i flow attraversati dal boundary toccato.

## 10. Anti-regressione: regole operative

### Regola 1

Una sola area sensibile per volta.

### Regola 2

Nessun cambio contemporaneo di:

- naming pubblico
- contract pubblico
- schema DB
- UX frontend

### Regola 3

Ogni patch deve poter rispondere a questa domanda:

"Quale confine e' diventato piu' chiaro grazie a questa modifica?"

Se la risposta non e' chiara, la patch probabilmente non va fatta.

## 11. Decisione finale di readiness

Con i tre documenti preparati, per me il quadro e' ora sufficiente per iniziare M1 quando vorrai.

Non tutto e' stato implementato, ma la parte importante adesso e' vera:

- la visione e' chiara
- il target e' chiaro
- il boundary da toccare per primo e' chiaro
- cio' che non va ancora toccato e' chiaro

## 12. Sintesi finale del pacchetto

### Documento 1 - Masterplan

Spiega la visione:

- separazione platform/game
- senso di Local/Beta/Production
- ordine giusto delle decisioni

### Documento 2 - Blueprint

Traduce la visione in:

- analisi stato attuale
- contratto target
- roadmap tecnica

### Documento 3 - Execution Package

Chiude le ambiguita' residue:

- glossario ID
- mapping endpoint
- scope della prima milestone

## 13. Prossimo passo suggerito

Il prossimo passo corretto, se vuoi iniziare davvero lo sviluppo, e':

- aprire M1
- toccare solo `round_gateway.py` e i punti minimi necessari di `mines/service.py`
- lasciare invariata la surface pubblica
- verificare i flow Mines sensibili

Questo e' il modo piu' pulito che vedo per partire senza sporcare il progetto.

## 14. Stato implementazione - 30 Aprile 2026

La prima tranche di M1 e' stata implementata.

### Completato

- `round_gateway.py` espone risultati espliciti per apertura round, settlement win e settlement loss.
- Il service Mines usa il gateway con nomi di dominio piu' chiari (`game_round_id`, `platform_round_id`) senza cambiare le API pubbliche.
- Il replay idempotente del cashout restituisce un saldo stabile derivato dalla round, non dal wallet snapshot corrente dopo eventuali movimenti successivi.
- `platform_rounds.settlement_ledger_transaction_id` viene valorizzato sui percorsi di win/cashout.

### Verificato

- Smoke reale API: launch token, access session, start, reveal, cashout, session retrieval e fairness.
- Test mirati backend e Mines: `35 passed`.
- Nessun cambio di contratto pubblico frontend.

### Fuori scope rimasto per M2

- Spostare completamente la persistenza `platform_rounds` fuori dal service Mines.
- Separare fisicamente `game_round_id` e `platform_round_id`.
- Ridefinire route pubbliche o contratti esterni.
