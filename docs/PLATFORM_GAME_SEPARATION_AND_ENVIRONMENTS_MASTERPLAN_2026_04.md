# CasinoKing - Masterplan Operativo

Separazione Piattaforma / Gioco e Strategia Ambienti Local / Beta / Production

## Stato del documento

- Documento operativo nuovo.
- Nasce per chiudere in modo maturo due temi sospesi:
  - separazione tra piattaforma CasinoKing e giochi integrati
  - strategia ambienti e workflow di sviluppo/prodotto
- Non sostituisce i documenti canonici.
- Interpreta e organizza operativamente le decisioni gia' presenti in:
  - `docs/SOURCE_OF_TRUTH.md`
  - `docs/TASK_EXECUTION_GUARDRAILS.md`
  - `docs/md/CasinoKing_Documento_02_Fondazioni_Architettura.md`
  - `docs/md/CasinoKing_Documento_03_Architettura_DB_API.md`
  - `docs/md/CasinoKing_Documento_05_v3_Wallet_Ledger_Fondamenta_Definitive.md`
  - `docs/md/CasinoKing_Documento_06_Mines_Prodotto_Stati_Matematica_API.md`
  - `docs/md/CasinoKing_Documento_11_v2_API_Contract_Allineato_v3.md`
  - `docs/md/CasinoKing_Documento_14_v2_Ambiente_Locale_Realtime_Policy.md`
  - `docs/md/CasinoKing_Documento_15_Piano_Implementazione.md`
  - `docs/md/CasinoKing_Documento_31_Contratto_Tra_Platform_Backend_E_Mines_Backend.md`
  - `docs/md/CasinoKing_Documento_35_Contratto_API_Operativo_Platform_Game_v1.md`
  - `docs/CTO_MINES_ANALYSIS_2026_03_30.md`

## 1. Perche' questo documento esiste

CasinoKing non e' solo "un sito con un gioco dentro". Il progetto, fin dall'inizio, e' stato pensato come una piattaforma casino con giochi proprietari separabili e con la possibilita' futura di integrare giochi esterni.

Questa visione genera due domande fondamentali:

1. Se domani un gioco non e' piu' sviluppato dentro CasinoKing ma su server separati, quale contratto deve esistere tra piattaforma e gioco?
2. Se oggi tutto gira in locale, quando e come si passa a un workflow Local / Beta / Production senza trasformare il progetto in qualcosa di inutilmente pesante?

Queste due domande non sono separate.

Sono in realta' la stessa domanda vista da due lati:

- da un lato c'e' il confine architetturale tra piattaforma e gioco
- dall'altro c'e' il confine operativo tra sviluppo locale, ambiente condiviso, e ambiente reale

Se il confine architetturale non e' chiaro:
- il codice si accoppia male
- i giochi diventano dipendenti dalla piattaforma in modo tossico
- i test diventano sempre piu' costosi
- ogni refactor aumenta il rischio di regressione

Se il confine operativo non e' chiaro:
- tutto resta "solo sulla macchina di Michele"
- non si testano mai davvero deploy, domini, proxy, HTTPS, sessioni, cookie, accessi remoti
- ogni passaggio verso l'online diventa traumatico

L'obiettivo di questo documento e' evitare entrambe le trappole.

## 2. Obiettivo di business e obiettivo tecnico

### 2.1 Obiettivo di business

CasinoKing deve diventare:

- una piattaforma riconoscibile
- capace di ospitare piu' giochi
- con proprieta' chiara di wallet, ledger, reporting e admin
- con la possibilita' futura di integrare giochi di terzi senza riscrivere le fondamenta

### 2.2 Obiettivo tecnico

L'obiettivo tecnico non e' "microservizi subito" o "fare enterprise".

L'obiettivo tecnico corretto e':

- definire un confine stabile tra `platform` e `game`
- mantenere la piattaforma come fonte di verita' economica
- permettere al gioco di restare specializzato sul proprio dominio
- costruire un workflow di delivery che consenta di testare bene senza esplodere in regressioni

## 3. Decisione architetturale di fondo

La decisione corretta, coerente con i documenti ufficiali e con il codice gia' presente, e':

`CasinoKing usa un modello seamless wallet, con piattaforma settlement authority e gioco motore di gameplay.`

Questo significa:

- la piattaforma possiede identita', sessione, wallet, ledger, promo, reporting, admin
- il gioco possiede config supportate, RNG, fairness, board generation, reveal, stato tecnico e payout teorico
- il gioco non possiede il saldo vero del player
- il gioco non deve essere autorizzato a muovere direttamente il ledger della piattaforma

In sintesi:

- `platform = financial and identity authority`
- `game = gameplay authority`

## 4. Regole non negoziabili

Queste regole derivano dai documenti canonici e non devono essere violate da nessuna soluzione futura.

### 4.1 Regole finanziarie

- Il ledger e' la fonte contabile primaria.
- Il wallet e' snapshot materializzato.
- Gli endpoint finanziariamente sensibili richiedono idempotenza.
- Il gioco non puo' bypassare wallet e ledger.
- Il gioco non puo' eseguire aggiornamenti diretti di saldo su dati "esterni" alla piattaforma.

### 4.2 Regole di dominio gioco

- Mines e' server-authoritative.
- Il frontend non decide outcome o payout.
- Il payout deriva dagli allegati runtime ufficiali.
- Per il MVP si usa request/response o polling leggero, non WebSocket.

### 4.3 Regole di integrazione futura

- I giochi futuri devono essere integrabili tramite contratto, non tramite accesso condiviso al database.
- Il gioco deve ricevere solo il minimo contesto necessario a giocare.
- La piattaforma deve poter riconciliare round, access session, movimenti ledger e reporting senza dipendere dalla tecnologia interna del gioco.

## 5. Stato attuale del progetto

Il progetto non parte da zero su questi temi.

Esistono gia' elementi molto utili:

- `game_code`
- `game_access_sessions`
- `game_launch_token`
- `X-Game-Launch-Token`
- route di accesso piattaforma
- route Mines separate
- primi documenti di contratto platform-game
- un backend che ha gia' avviato la separazione

Questo e' importante perche' significa che non dobbiamo "inventare la visione". Dobbiamo raffinarla, formalizzarla e portarla a un livello di maturita' che permetta sviluppo pulito.

### 5.1 Stato positivo

Nel codice gia' oggi si vede:

- la piattaforma emette e valida un `game launch token`
- il frontend Mines usa il token per il lancio
- esiste una `game_access_session`
- esiste il concetto di `game_code`
- esiste il boundary `platform rounds` / `game state`, anche se non ancora completato

### 5.2 Stato ancora transitorio

Il progetto e' ancora in mezzo al guado su alcuni punti:

- Mines e' ancora troppo vicino alla logica di settlement
- il confine tra round tecnica e round finanziaria non e' ancora completamente isolato
- alcune route di handoff stanno ancora sotto namespace Mines anche se sono concettualmente platform
- il frontend e' in una fase di ripulitura strutturale ma non e' ancora arrivato a una separazione di prodotto completa

Conclusione:

la direzione e' giusta, ma va completata con disciplina.

## 6. Il problema vero da evitare

Il rischio piu' grande non e' "non avere abbastanza test".

Il rischio piu' grande e':

- cambiare architettura senza confini chiari
- continuare a sviluppare feature mentre il confine e' ancora ambiguo
- accoppiare troppo gioco e piattaforma
- scoprire troppo tardi che ogni modifica richiede testare tutto

Quando dici "non voglio finire in 20000000 test di regressione", stai puntando al problema giusto.

La vera riduzione delle regressioni non arriva da test infiniti.

Arriva da:

- ownership chiara
- contratti piccoli e stabili
- componenti isolate
- deploy stages separati
- roadmap di migrazione a fasi

I test servono, ma non possono compensare un confine architetturale sbagliato.

## 7. Modello target: piattaforma e gioco come due prodotti distinti

La separazione corretta non e' "due repository subito".

La separazione corretta e':

- due domini
- due responsabilita'
- un contratto formale
- deployment potenzialmente indipendenti
- ma monorepo ancora accettabile in questa fase

### 7.1 Cosa appartiene alla piattaforma

La piattaforma deve possedere:

- autenticazione player/admin
- sessione utente
- gestione ruoli e permessi
- wallet cash / bonus
- ledger double-entry
- promo, bonus, adjustment e riconciliazione
- reporting e admin
- autorizzazione al lancio gioco
- sessione di accesso al gioco
- round finanziaria
- settlement finale
- audit globale

### 7.2 Cosa appartiene al gioco

Il gioco deve possedere:

- regole del gioco
- configurazioni supportate
- runtime ufficiale
- fairness
- seed e hash
- generazione board
- reveal
- stato tecnico della partita
- payout teorico o finale secondo le regole del gioco
- UI e UX del gioco

### 7.3 Cosa non deve appartenere al gioco

Il gioco non deve possedere:

- ledger platform
- scrittura diretta wallet platform
- reporting economico ufficiale
- ruoli admin platform
- policy di promo platform
- logica di autorizzazione globale del player

## 8. Modello mentale corretto per i giochi futuri

Se domani un tuo amico sviluppa un gioco esterno, il modello corretto non e':

"gli diamo accesso ai nostri saldi"

Il modello corretto e':

"gli diamo un contratto di integrazione stretto e controllato"

L'amico che sviluppa il gioco deve poter dire:

- "ho ricevuto un player autorizzato a giocare"
- "ho ricevuto il game code"
- "posso aprire una round"
- "posso chiudere la round come persa o vinta"
- "posso mandare gli eventi tecnici necessari"

Ma non deve poter dire:

- "aggiorno io il saldo"
- "entro io nel database wallet"
- "decido io come contabilizzare"
- "scrivo io sul ledger"

Questa e' la distinzione che permette di passare da gioco first-party interno a provider esterno senza rifondare il core.

## 9. Contratto target tra platform e game provider

Questo e' il cuore del tema `H`.

Il contratto deve essere definito prima dello sviluppo grosso.

### 9.1 Obiettivi del contratto

Il contratto deve garantire:

- identita' del player
- autorizzazione a entrare nel gioco
- tracciamento di accesso al gioco
- apertura round finanziaria
- settlement corretto
- riconciliazione
- audit
- minimo accoppiamento tecnico

### 9.2 Concetti minimi del contratto

I concetti minimi da standardizzare sono questi:

#### A. `game_code`

Identifica il gioco in modo univoco.

Serve per:

- routing logico
- reporting
- access session
- regole di autorizzazione
- configurazioni runtime

#### B. `platform_session_id`

Identifica la sessione utente nella piattaforma.

Serve a evitare che il gioco lavori su un giocatore anonimo o scollegato dal contesto platform.

#### C. `game_launch_token`

Token firmato, a vita breve, emesso dalla piattaforma.

Serve per:

- autorizzare il lancio del gioco
- trasportare il contesto minimo
- impedire accessi arbitrari al backend gioco

#### D. `access_session_id`

Identifica la permanenza del player nel gioco.

Non e' ancora la round economica.

Serve per:

- audit
- analytics
- reporting sessioni
- resume / continuity

#### E. `platform_round_id`

Identifica la round economica in piattaforma.

Serve per:

- settlement
- ledger
- reporting economico
- riconciliazione

#### F. `game_round_id` o `game_session_id`

Identifica la round tecnica del gioco.

Serve per:

- stato tecnico
- fairness
- replay
- debug di gameplay

## 10. Flusso operativo target end-to-end

### 10.1 Entrata nel gioco

1. Il player si autentica sulla piattaforma.
2. La piattaforma verifica che il player possa accedere al gioco.
3. La piattaforma crea o aggiorna una `access_session`.
4. La piattaforma emette un `game_launch_token`.
5. Il frontend o container gioco avvia il gioco usando quel token.
6. Il backend gioco valida il token e apre la propria sessione tecnica.

### 10.2 Apertura round

1. Il player sceglie configurazione e puntata nel gioco.
2. Il frontend chiama il backend gioco.
3. Il backend gioco valida che la configurazione sia supportata.
4. Il backend gioco chiama la piattaforma per aprire la round finanziaria.
5. La piattaforma:
   - verifica saldo
   - applica regole wallet
   - scrive ledger
   - aggiorna wallet snapshot
   - crea `platform_round_id`
6. Il backend gioco crea `game_round_id` e lo associa a `platform_round_id`.

### 10.3 Evoluzione della round

1. Il frontend gioco invia azioni di gameplay al backend gioco.
2. Il backend gioco esegue reveal e aggiorna il proprio stato tecnico.
3. Non devono avvenire posting intermedi sul ledger per ogni reveal.

Questo punto e' importantissimo.

Se ogni reveal toccasse il ledger:

- aumenterebbe il rumore contabile
- aumenterebbe la complessita' idempotente
- aumenterebbe la fragilita' del sistema

Il ledger deve vedere gli eventi economici veri, non tutti gli step tecnici di gameplay.

### 10.4 Chiusura round persa

1. Il gioco rileva l'esito perso.
2. Il backend gioco invia esito finale alla piattaforma.
3. La piattaforma chiude la round come persa.
4. Nessun payout viene accreditato.

### 10.5 Chiusura round vinta

1. Il player incassa o il gioco arriva a uno stato di vincita cashout.
2. Il backend gioco calcola il payout finale secondo il runtime.
3. Il backend gioco chiama la piattaforma con payout finale e stato finale.
4. La piattaforma registra il payout, chiude la round e aggiorna wallet/ledger.

## 11. Che API dobbiamo "scambiarci" davvero

Questa e' la risposta piu' concreta alla tua domanda iniziale.

Se un tuo amico hosta il suo gioco su server propri, i sistemi devono parlarsi attraverso un set ristretto di API.

### 11.1 API platform -> game

Queste esistono per autorizzare e inizializzare il gioco:

- `launch/validate`
- `launch/open-play-session`
- opzionale `launch/heartbeat`
- opzionale `launch/close`

In pratica:

- la piattaforma non controlla il board
- ma controlla chi puo' entrare

### 11.2 API game -> platform

Queste esistono per l'economia:

- `round/open`
- `round/settle-lost`
- `round/settle-won`
- opzionale `round/abort`
- opzionale `player-left`

In pratica:

- il gioco non muove soldi
- chiede alla piattaforma di farlo

### 11.3 API di consultazione e audit

Queste possono essere:

- `GET round status`
- `GET launch validation`
- `GET session summary`
- `GET fairness evidence`

Non tutte devono essere pubbliche subito.

Ma vanno previste nel modello.

## 12. Dati minimi che il gioco deve ricevere

Il gioco deve ricevere il meno possibile, ma abbastanza per funzionare.

Set minimo consigliato:

- `player_id`
- `game_code`
- `access_session_id`
- `launch_token_nonce`
- `expires_at`
- eventuale `wallet_context_allowed`
- eventuale `currency_code`

Set da non esporre al gioco se non strettamente necessario:

- dettagli admin
- stato promo generale
- accesso al ledger
- dati personali non necessari

## 13. Sicurezza del contratto

La separazione platform-game ha senso solo se il contratto e' sicuro.

### 13.1 Requisiti minimi per MVP serio

- token firmato
- TTL breve
- ownership check
- game_code check
- session check
- idempotency key sugli endpoint economici
- audit log delle chiamate sensibili

### 13.2 Requisiti per una fase successiva piu' matura

- consumo singolo o bounded-use del launch token
- tracking `consumed_at`
- revoca o blacklist di launch token
- firma machine-to-machine tra game provider e platform
- allowlist origini/provider
- contract versioning

### 13.3 Decisione pratica

Per il progetto didattico oggi:

- JWT a TTL breve puo' bastare per il launch
- ma il documento deve gia' prevedere il passo successivo

Questo evita di confondere "MVP accettabile" con "modello definitivo".

## 14. Monorepo o repo separati

Questa domanda va affrontata con calma.

### 14.1 Oggi

Oggi il monorepo e' ancora la scelta giusta.

Perche':

- riduce attrito
- facilita refactor iniziali
- permette di vedere platform e game insieme
- aiuta una fase didattica/progettuale

### 14.2 Domani

Domani si potra' arrivare a:

- monorepo con deployment indipendenti
- oppure multi-repo

Ma separare i repository prima di separare bene il contratto sarebbe un errore.

Ordine corretto:

1. separare responsabilita'
2. formalizzare contratti
3. rendere indipendenti i deploy
4. solo dopo valutare repo distinti

## 15. Beta e Production: ha senso davvero?

Sì.

Ha senso anche in un progetto didattico.

Anzi: proprio perche' il progetto e' didattico ma ambizioso, creare ambienti separati ti insegna le cose giuste nel momento giusto.

### 15.1 Cosa succede se resti solo in locale

Se resti solo in locale troppo a lungo:

- non testi domini e routing reali
- non testi HTTPS
- non testi cookie e sessioni cross-origin
- non testi reverse proxy
- non testi deploy e rollback
- non testi la vita vera di un prodotto

### 15.2 Cosa succede se vai online troppo presto senza strategia

Se vai online senza ambienti separati:

- confondi test e demo
- mescoli esperimenti e versioni stabili
- non hai un posto "sicuro ma condivisibile"
- ogni cambiamento sembra una release definitiva

Quindi:

`Local / Beta / Production` non e' overengineering.

E' il minimo ciclo sano per un prodotto che vuole crescere.

## 16. Definizione dei tre ambienti

### 16.1 Local

Scopo:

- sviluppo quotidiano
- refactor
- test tecnici
- debugging rapido

Caratteristiche:

- Docker locale
- dati seed
- account test
- feature incomplete ammesse
- log piu' verbosi

Non deve essere:

- riferimento per demo esterne
- luogo in cui validare il comportamento finale di deploy

### 16.2 Beta

Scopo:

- ambiente condivisibile
- QA funzionale
- test manuale end-to-end
- review di prodotto
- prova di integrazione quasi reale

Caratteristiche:

- online
- protetto ma accessibile
- database dedicato non produzione
- migrazioni vere
- dominio o sottodominio dedicato
- configurazioni stabili

Deve essere:

- abbastanza stabile da essere affidabile
- abbastanza vicino alla produzione da essere significativo

Non deve essere:

- un ambiente anarchico dove si pushano feature mezze rotte

### 16.3 Production

Scopo:

- ambiente reale
- versione pubblica o semi-pubblica ufficiale

Caratteristiche:

- policy piu' rigide
- demo mode limitato o disabilitato secondo regole
- logging e backup piu' seri
- deploy deliberati
- rollback chiaro

## 17. Strategia raccomandata per gli ambienti

La strategia consigliata non e' complessa, ma deve essere disciplinata.

### 17.1 Regola base

- `local` per costruire
- `beta` per validare
- `production` per pubblicare

### 17.2 Regola di passaggio

Una cosa non dovrebbe andare in production se prima non e':

- passata da local
- passata da beta
- stata verificata sul comportamento reale toccato

### 17.3 Regola di maturita'

Beta non deve contenere tutto quello che esiste in locale.

Beta deve contenere solo cio' che sei disposto a far vedere e testare in modo ordinato.

## 18. Workflow di sviluppo consigliato

Qui la parola importante e' `semplice`.

Non serve processo pesante. Serve processo chiaro.

### 18.1 Branching

Modello consigliato:

- `main` = stato stabile del progetto
- branch feature piccoli
- merge verso `main` dopo build e smoke test
- deploy Beta da `main` o da branch release dedicato, in base alla disciplina che vorrai adottare

Per la fase attuale, la cosa piu' semplice e':

- lavorare a branch piccoli
- merge su `main` solo quando una porzione e' davvero pulita
- Beta allineata a `main`

### 18.2 Regola sui task

Ogni task deve dichiarare se appartiene a:

- platform
- game
- boundary contract
- infra/environment

Questo riduce enormemente il rischio di patch trasversali e regressioni.

### 18.3 Regola sui refactor

I refactor architetturali grossi devono essere:

- documentati prima
- spezzati in fasi
- verificati a ogni step

Questo e' esattamente il motivo per cui stiamo scrivendo questo documento prima di sviluppare.

## 19. Come evitare l'esplosione dei test di regressione

Questa sezione e' centrale.

Non esiste una soluzione magica, ma esiste una strategia che riduce molto il problema.

### 19.1 Causa profonda delle regressioni

Le regressioni esplodono quando:

- un file contiene troppe responsabilita'
- un modulo puo' toccare troppi contesti
- i confini non sono formali
- ogni patch e' trasversale

### 19.2 Soluzione architetturale

Per evitare "20000000 test di regressione" serve:

- separare ownership
- rendere il contratto platform-game stretto
- rendere il frontend per prodotto piu' isolato
- introdurre Beta come area di validazione reale

### 19.3 Soluzione di test

Non servono test infiniti.

Servono tre livelli:

#### A. Test di dominio critico

- wallet
- ledger
- idempotenza
- round settlement
- access session
- launch token

Questi devono essere forti.

#### B. Test di integrazione boundary

- launch
- open round
- settle lost
- settle won
- access session / ping / close

Questi sono pochi ma importantissimi.

#### C. Smoke test funzionali

- login
- lobby
- account
- launch Mines
- round base
- admin finance/player/admin management

Questi non devono coprire tutto il mondo. Devono dire se il prodotto e' ancora vivo e coerente.

### 19.4 Regola d'oro

Meno patch cross-domain fai, meno regressioni devi rincorrere.

## 20. Strategia di migrazione consigliata

Questa e' la roadmap raccomandata per affrontare `H` e `I` senza sporcare il codice.

### Fase 0 - Chiusura decisionale

Obiettivo:

- allineare il modello
- accettare questo documento come base operativa

Output:

- decisione ufficiale su separazione
- decisione ufficiale su Local/Beta/Production

### Fase 1 - Formalizzazione del contratto

Obiettivo:

- consolidare il contratto platform-game in documento e API target

Task:

- definire endpoint target
- definire payload minimi
- definire ownership campi
- definire policy token
- definire idempotenza e audit

Output:

- contract v1 stabile

### Fase 2 - Hardening del boundary senza riscrivere tutto

Obiettivo:

- completare il boundary backend senza big bang

Task:

- rendere esplicito il ruolo di `platform_rounds`
- limitare ulteriormente la conoscenza finanziaria nel servizio gioco
- spostare le route di handoff sotto area platform quando opportuno
- mantenere un gateway di transizione

Output:

- backend piu' coerente
- rischio regressioni contenuto

### Fase 3 - Separazione prodotto frontend

Obiettivo:

- far vivere il frontend gioco come prodotto autonomo pur dentro il monorepo

Task:

- rimuovere dipendenze inutili del gioco dalla shell platform
- isolare i moduli Mines
- chiarire il launcher e il lifecycle di ingresso/uscita

Output:

- frontend piu' pulito
- minor rischio UI cross-domain

### Fase 4 - Beta environment

Obiettivo:

- avere il primo ambiente condiviso serio

Task:

- deploy online semplice
- config beta dedicate
- database beta
- dominio beta
- pipeline base di deploy

Output:

- vero ambiente di validazione

### Fase 5 - Hardening pre-production

Obiettivo:

- preparare le condizioni per una production credibile

Task:

- rollout policy
- backup e rollback minimi
- hardening token
- review secrets e config
- smoke test definiti

Output:

- readiness ragionevole per produzione

## 21. Cosa NON fare

Per proteggere il progetto, queste mosse sono sconsigliate.

### 21.1 Non separare il repository prima del contratto

Se separi i repo prima di separare i confini:

- il caos si distribuisce, non si risolve

### 21.2 Non dare accesso diretto del gioco al database platform

Questo distruggerebbe la proprieta' del core finanziario.

### 21.3 Non mandare in Beta feature meta' finite

Beta deve validare. Non deve diventare il posto dei prototipi casuali.

### 21.4 Non fare un mega-refactor platform + game + infra insieme

Questo e' il modo perfetto per creare regressioni ingestibili.

### 21.5 Non confondere "didattico" con "senza metodo"

Un progetto didattico serio e' proprio il posto giusto dove allenare un metodo pulito.

## 22. Criteri decisionali per quando iniziare lo sviluppo

Hai detto una cosa molto sana:

"svilupperemo solo quando saremo confidenti che il lavoro potra' essere pulito a livello di codice"

Questa deve diventare una regola.

Lo sviluppo del tema `H/I` dovrebbe iniziare solo quando avremo:

1. ownership chiara tra platform e game
2. contratto target concordato
3. roadmap di migrazione in step piccoli
4. perimetro della prima implementazione ben limitato
5. criteri di successo chiari

Se anche uno di questi punti manca, e' meglio continuare a ragionare prima di toccare il codice.

## 23. Prima implementazione raccomandata

La prima implementazione non dovrebbe essere "portare Mines fuori".

Sarebbe troppo.

La prima implementazione raccomandata e':

### 23.1 Sul piano architetturale

- consolidare il contratto target `platform <-> game`
- mappare stato attuale vs target endpoint per endpoint

### 23.2 Sul piano backend

- completare il boundary transitorio
- chiarire i punti in cui Mines conosce ancora troppo del settlement

### 23.3 Sul piano ambienti

- progettare Beta
- non necessariamente deployarla il primo giorno
- ma definire gia' come esistera'

In altre parole:

prima si disegna la linea, poi si comincia a spostare i moduli.

## 24. Posizione finale raccomandata

La posizione finale che consiglio e' questa.

### 24.1 Sulla separazione platform / game

- Sì, va perseguita
- No, non come separazione fisica immediata dei repository
- Sì, come separazione rigorosa di contratto, ownership e deployability

### 24.2 Sugli ambienti

- Sì, ha senso introdurre Beta e Production
- No, non serve un'infrastruttura enterprise adesso
- Sì, serve un workflow disciplinato Local -> Beta -> Production

### 24.3 Sulla roadmap

Ordine corretto:

1. documento e ragionamento
2. contratto target
3. boundary hardening
4. product separation
5. beta environment
6. production hardening

Questo ordine minimizza regressioni e massimizza chiarezza.

## 25. Decisioni operative proposte

Propongo di adottare formalmente queste decisioni:

1. `CasinoKing platform` resta l'unica authority per wallet, ledger e settlement.
2. `Mines` e i futuri giochi devono essere trattati come prodotti separabili con contratto di integrazione.
3. Il contratto platform-game deve essere formalizzato e stabilizzato prima di refactor grandi.
4. Il monorepo resta accettabile in questa fase.
5. Va introdotta una strategia ambienti `local / beta / production`.
6. Beta deve nascere come ambiente condiviso di validazione, non come production mascherata.
7. Le prossime implementazioni devono essere piccole, sequenziali e orientate a ridurre il rischio regressioni.

## 26. Sintesi breve finale

### Messaggio chiave

CasinoKing deve evolvere come piattaforma con giochi integrabili, non come codice unico indistinto.

### Decisione chiave

- piattaforma = soldi, identita', audit, admin
- gioco = gameplay, fairness, stato tecnico

### Decisione ambienti

- local = costruzione
- beta = validazione
- production = pubblicazione

### Regola chiave

Prima si chiude bene il contratto.
Poi si sviluppa.
Non il contrario.

## 27. Schema finale

```text
PLAYER
  |
  v
PLATFORM FRONTEND / PLATFORM BACKEND
  - auth
  - wallet
  - ledger
  - admin
  - reporting
  - launch authorization
  - access session
  - financial round
  |
  |  game_launch_token + access_session_id + contract API
  v
GAME FRONTEND / GAME BACKEND
  - config
  - gameplay
  - fairness
  - board
  - reveal
  - technical game state
  - payout calculation
  |
  |  settle / round open-close via contract
  v
PLATFORM SETTLEMENT AUTHORITY
```

## 28. Prossimo passo suggerito

Il prossimo passo corretto non e' ancora sviluppo.

Il prossimo passo corretto e':

- produrre un secondo documento, piu' tecnico e ancora piu' concreto, che trasformi questo masterplan in:
  - mappa `stato attuale -> target`
  - contratto endpoint-by-endpoint
  - roadmap implementativa in milestone
  - perimetro della primissima fase di codice

Solo dopo quel passaggio conviene iniziare l'implementazione.
