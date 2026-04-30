# CasinoKing - Beta Hosting Decision Memo

Scelta pratica per il primo ambiente Beta online, economico e sostenibile

## Stato del documento

- Documento operativo breve.
- Serve a chiudere il buco pratico rimasto aperto nei documenti precedenti:
  - dove hostare la Beta
  - se serve un dominio subito
  - quale stack di deploy e' piu' sensato per il progetto oggi
- Non sostituisce i documenti architetturali.
- Serve a prendere una decisione concreta prima o in parallelo a M1.

## 1. Il problema pratico

I documenti precedenti chiariscono bene:

- separazione `platform <-> game`
- workflow `Local -> Beta -> Production`

ma non rispondono ancora in modo abbastanza operativo a una domanda fondamentale:

`dove mettiamo online la prima Beta senza complicarci la vita e senza spendere troppo?`

Questa domanda e' reale e legittima.

Per un progetto didattico ma serio, non serve una soluzione enterprise.
Serve una soluzione:

- economica
- semplice da capire
- compatibile con `Next.js + FastAPI + Postgres + Docker`
- abbastanza stabile da permettere demo e test condivisi

## 2. Criteri di scelta

La piattaforma Beta va scelta usando criteri chiari.

### 2.1 Criteri tecnici

- supporto buono a Docker
- deploy semplice di backend e frontend
- supporto Postgres gestito o facilmente collegabile
- supporto variabili ambiente e secrets
- custom domain possibile
- HTTPS semplice

### 2.2 Criteri operativi

- costi bassi
- pannello comprensibile
- poca manutenzione sistemistica
- adatto a un solo developer / founder

### 2.3 Criteri di progetto

- non vogliamo diventare sysadmin
- non vogliamo bloccarci sull'infrastruttura
- vogliamo arrivare online senza tradire l'architettura futura

## 3. Opzioni considerate

## 3.1 Railway

### Pro

- molto semplice per side project e full-stack piccoli
- buon supporto a Docker
- deploy rapido
- domini provider disponibili subito
- custom domains e SSL gestiti
- adatto a chi vuole andare online velocemente

### Contro

- costi meno prevedibili di una piattaforma molto lineare
- puo' diventare meno simpatico se il progetto cresce in complessita'
- non e' il miglior posto se si vuole massimo controllo infrastrutturale

### Valutazione

Ottima scelta per la prima Beta.

## 3.2 Render

### Pro

- semplice
- costi piu' leggibili
- supporta Docker
- buon supporto a web services e Postgres
- custom domains e TLS gestiti

### Contro

- leggermente meno "snello" del flusso Railway per partire subito
- puo' costare un po' di piu' in configurazione minima completa

### Valutazione

Ottima alternativa se si privilegia prevedibilita' dei costi e una piattaforma un po' piu' ordinata.

## 3.3 Fly.io

### Pro

- molto potente
- ottimo controllo
- buono per app Dockerizzate

### Contro

- piu' infrastrutturale
- meno adatto come prima scelta per un founder non developer
- rischio di spendere energie mentali sull'hosting invece che sul prodotto

### Valutazione

Non consigliato come prima Beta del progetto.

## 3.4 Supabase

### Pro

- ottimo Postgres gestito
- utile per servizi database
- pannello pulito

### Contro

- non e' la soluzione naturale per hostare l'intero stack `Next.js + FastAPI`
- rischia di confondere database hosting con application hosting
- non risolve da solo il problema "porto online tutta la piattaforma"

### Valutazione

Utile eventualmente come database/servizio.
Non consigliato come risposta primaria al problema Beta hosting complessivo.

## 3.5 VPS tradizionale

### Pro

- massimo controllo
- costo potenzialmente basso

### Contro

- richiede piu' competenze sistemistiche
- piu' manutenzione
- piu' rischio di perdere tempo su ops

### Valutazione

Non consigliato per la prima Beta del progetto.

## 4. Raccomandazione finale

La mia raccomandazione concreta oggi e':

### Prima scelta

- `Railway` per la prima Beta

### Seconda scelta

- `Render` se preferisci maggiore leggibilita' dei costi e una piattaforma un po' piu' ordinata

### Non prima scelta

- `Supabase` come hosting principale dell'intero stack
- `Fly.io` come primo passo
- `VPS` manuale

## 5. Perche' Railway e' la scelta consigliata

Per il progetto CasinoKing oggi, Railway e' la scelta piu' pragmatica perche':

1. abbassa la soglia di accesso
2. funziona bene con stack moderni e Dockerizzati
3. permette di arrivare online senza costruire una mini-infrastruttura enterprise
4. e' abbastanza semplice da essere adatta a una Beta didattica ma seria

Detto in modo molto diretto:

`se vogliamo una Beta online vera in tempi ragionevoli senza perderci, Railway e' la strada piu' sensata`

## 6. Dominio: serve subito?

### Risposta breve

No, non serve subito.

### Risposta pratica

Per la prima Beta si puo' partire con:

- dominio provider tipo `*.up.railway.app`

Questo e' sufficiente per:

- deploy iniziale
- smoke test
- prime demo
- verifica base del routing e del TLS

### Quando conviene comprare il dominio

Conviene comprarlo quando:

- il brand e' abbastanza stabile
- vuoi una Beta piu' presentabile
- vuoi iniziare a ragionare come prodotto reale

### Raccomandazione

Io lo comprerei abbastanza presto, ma non lo renderei un prerequisito per partire con la Beta.

Quindi:

- `Beta v0`: senza dominio tuo
- `Beta v1`: con `beta.tuodominio.com`

## 7. Dove comprare il dominio

Scelte consigliate:

- Cloudflare Registrar
- Porkbun

### Cloudflare

Pro:

- ottimo DNS
- pricing generalmente buono
- molto adatto a gestione dominio + DNS

### Porkbun

Pro:

- semplice
- economico
- adatto a piccoli progetti

## 8. Configurazione Beta minima raccomandata

La Beta minima non deve essere perfetta.
Deve essere sufficiente.

### Componenti minimi

- `frontend` Next.js
- `backend` FastAPI
- `postgres`

### Componenti non necessari al primo giorno

- observability avanzata
- scaling sofisticato
- multi-region
- HA complessa
- CDN fine-tuning

### Obiettivo

Una Beta capace di:

- autenticare utenti
- servire lobby/account/admin
- lanciare Mines
- usare DB vero
- farci testare il prodotto da fuori macchina

## 9. Costi indicativi

I costi cambiano nel tempo, quindi qui non va preso come listino definitivo.

Il punto e' l'ordine di grandezza.

### Railway

Aspettativa iniziale:

- costo basso di ingresso
- adatto a una Beta piccola

### Render

Aspettativa iniziale:

- costo un po' piu' leggibile e spesso piu' "da listino"
- web service + database possono portarti rapidamente a una spesa mensile piu' definita

### Dominio

Ordine di grandezza:

- costo basso annuale per `.com` o estensioni comuni

### Decisione pratica

Per un progetto come questo il costo del dominio non e' il vero problema.
Il problema vero e' scegliere una piattaforma dove non ti blocchi.

## 10. Decisione operativa raccomandata

Propongo questa decisione:

1. scegliere `Railway` come target Beta iniziale
2. non rendere il dominio un prerequisito
3. comprare il dominio poco dopo, quando la Beta inizia a stabilizzarsi
4. usare `beta.<dominio>` come destinazione del primo ambiente condiviso serio

## 11. Relazione con M1

Il tuo CTO ha ragione su un punto importante:

M1 non ha output utente visibile.

Questo significa che M1 ha senso solo se:

- sappiamo perche' lo facciamo
- sappiamo dove stiamo andando dopo

La decisione Beta hosting serve proprio a questo:

- da' un contesto reale al lavoro interno
- evita che M1 sembri "refactor per refactor"

Detto bene:

`M1 rende il boundary piu' pulito; la decisione Beta rende chiaro per quale futuro concreto lo stiamo ripulendo`

## 12. Commento sulla critica del CTO

Il giudizio del CTO, per me, e' sostanzialmente corretto.

### 12.1 Dove ha ragione

- c'e' davvero overlap con documenti 30/31/34/35
- la parte Beta era ancora troppo di principio
- M1 da sola non produce output visibile
- quattro documenti nuovi per due temi sono tanti

### 12.2 Dove aggiungo una sfumatura

Anche se il CTO ha ragione sul rischio di over-documentation, i documenti creati non sono inutili:

- hanno rimesso insieme visione, stato attuale e milestone in una forma coerente con il codice reale
- hanno chiarito il primo intervento prudente

Il problema non e' che esistano.
Il problema sarebbe continuare ad aggiungere documenti senza trasformarli in decisioni operative.

### 12.3 Conclusione

Il CTO ha colto il punto chiave:

`ora basta analisi astratta; serve una decisione concreta sulla Beta`

Questa osservazione e' giusta.

## 13. Come pulirei il quadro documentale

Dal punto di vista documentale, io procederei cosi':

### Fase A - Non cancellare nulla adesso

Per ora non cancellerei i documenti appena creati.

Perche':

- sono freschi
- sono coerenti
- possono ancora guidare il lavoro

### Fase B - Stabilire i documenti "attivi"

Io considererei attivi questi:

- Documento 30
- Documento 31
- Documento 35
- `PLATFORM_GAME_M1_EXECUTION_PACKAGE_2026_04.md`
- `PLATFORM_GAME_M1_FILE_BY_FILE_EXECUTION_PLAN_2026_04.md`
- questo memo Beta hosting

### Fase C - Segnare gli altri come "ponte di analisi"

I documenti nuovi piu' lunghi che fanno da sintesi ragionata:

- `PLATFORM_GAME_SEPARATION_AND_ENVIRONMENTS_MASTERPLAN_2026_04.md`
- `PLATFORM_GAME_CONTRACT_AND_ENVIRONMENTS_IMPLEMENTATION_BLUEPRINT_2026_04.md`

io non li cancellerei, ma li tratterei come:

- documenti ponte
- utili per motivazione e continuita'
- non il primo punto da rileggere ogni volta

### Fase D - In futuro

Quando M1 e la scelta Beta saranno assorbite davvero nel lavoro:

- si potra' accorpare o archiviare
- lasciando piu' snelli i documenti attivi

## 14. Decisione finale proposta

Se dovessi proporti una decisione secca oggi, sarebbe questa:

1. approviamo `Railway` come scelta Beta iniziale
2. non rendiamo il dominio un blocco iniziale
3. teniamo M1 come prima milestone tecnica
4. subito dopo M1 apriamo il pacchetto operativo di Beta setup

## 15. Sintesi estrema

### Scelta hosting

- consigliato: `Railway`
- alternativa seria: `Render`

### Dominio

- non obbligatorio subito
- consigliato poco dopo

### CTO feedback

- corretto nella sostanza
- utile per riportare il lavoro dalla teoria alla decisione pratica

### Quadro documentale

- non cancellare ora
- distinguere tra documenti attivi e documenti ponte

### Next step

- M1 backend boundary
- poi Beta setup concreto
