# MANDATO DELLA CORSA GOAL 01 — `ck-riproduci.sh`

**Leggi questo file per intero prima di fare qualunque cosa.** E' il tuo mandato:
definisce cosa devi ottenere, cosa NON puoi toccare, e a quali condizioni ti fermi
anche se non hai finito. Le condizioni di arresto valgono piu' dell'obiettivo.

Autorizzato da Michele il 7/09/2026. Motore: Codex in modalita' GOAL.
Ramo: `fase9/goal`, dentro il worktree usa-e-getta `wt-goal-fase9`.
**Non lavorare mai in `../casinoking-platform`: e' la copia viva.**

---

## 1. L'obiettivo, in una riga

Che esista `scripts/ck-riproduci.sh`, tredicesimo e ultimo comando del gate di Fase 9,
e che **si dimostri capace di fallire** quando deve.

## 2. Cosa deve fare lo script

E' specificato nel contratto — `../CONTRATTO_FASE_9_QUINTA_STESURA.md`, sezione
«Chi dichiara la chiusura — e chi fa il confronto». **Leggila: qui c'e' il riassunto,
li' c'e' la fonte, e se divergono vince la fonte.**

1. Rilancia i dodici comandi del gate che lo precedono.
2. Da ogni artefatto appena prodotto estrae il blocco fra `--- ESITO ---` e
   `--- FINE ESITO ---`, che contiene solo righe stabili: nome del caso, verdetto,
   importi, saldo prima, saldo dopo.
3. Applica la mascheratura dei campi volatili e confronta col blocco depositato.
4. Esce **0** solo se coincidono tutti.

### I due vincoli che non sono dettagli

**La mascheratura e' una lista CHIUSA.** Si possono mascherare solo identificativi
generati, marche temporali e durate. **Importi, saldi, valute, codici di esito e nomi
dei casi non sono mascherabili mai**, e lo script deve **fallire lui stesso** se
qualcuno li aggiunge alla lista. Motivo: una costante libera dentro uno script si
allarga in silenzio, e bastava aggiungerci «importo» per nascondere proprio la
divergenza economica che il confronto esiste per trovare.

**Ogni artefatto porta l'impronta del file di collaudo che lo ha generato**, e lo
script verifica che quel file sia ancora quello approvato. Senza questo, il comando
prova la stabilita' di un riassunto e non la riproduzione di un comportamento:
bastava indebolire un collaudo lasciandogli stampare lo stesso verdetto e gli stessi
importi, e tutto passava.

## 3. La cosa che rende vero il lavoro: i due collaudi dello script

**Uno script che non si e' mai visto fallire non e' un controllo, e' una promessa.**
`ck-rosso.sh` e `ck-censimento.sh` hanno entrambi i loro, e questo deve averli:

- **Prova A:** alterata **una sola riga non mascherata** di un artefatto depositato,
  `ck-riproduci.sh` deve **fallire** e **dire quale**.
- **Prova B:** **indebolito un file di collaudo** senza toccare l'artefatto,
  `ck-riproduci.sh` deve **fallire sull'impronta**.

Le prove girano in un repository finto usa-e-getta, come fa gia' `ck-gate.sh --autotest`.
**Guarda come lo fa lui e imita quella forma**: non inventarne una nuova.

Se non riesci a far fallire lo script su Prova A e Prova B, **non hai finito**, anche
se lo script gira e stampa verde.

## 4. Cosa puoi applicare e cosa no — leggi con attenzione

**PUOI CREARE E APPLICARE:**
- `scripts/ck-riproduci.sh`, che non esiste;
- collaudi nuovi sotto `tests/`;
- file nuovi di documentazione o di appoggio.

Il perimetro protetto (`scripts/perimetro-protetto.txt`) marca questi percorsi come
`MODIFICA`: **creare un file nuovo li' e' libero**, perche' un file nuovo puo' solo
aggiungere controlli.

**NON PUOI APPLICARE, MAI, nemmeno se ti sembra ovvio e piccolo:**
- modifiche a file **esistenti** del perimetro protetto: rotte, registro, adattatori,
  collaudi gia' presenti, `ck-gate.sh`, `ck-provenienza.sh`, `perimetro-protetto.txt`;
- **qualunque migrazione**, anche nuova: quelle sono in modo `SEMPRE`;
- il percorso del denaro sotto `backend/app/modules/platform/` e `backend/app/api/v1/seamless/`.

Per tutto cio' che ricade li', **produci un dossier e fermati**: un file
`missioni/2026-09-07-goal-riproduci/PROPOSTA.md` col testo integrale fra i marcatori
`--- INIZIO TESTO PROPOSTO: <percorso> ---` e `--- FINE TESTO PROPOSTO ---`, cosa
rompe e cosa no coi collaudi nominati uno per uno. **Non calcolare tu l'impronta:**
la calcola chi monta la catena, sui byte.

Il divieto **non dipende dalla firma di Michele**. Anche a firma ottenuta,
l'applicazione sul percorso del denaro non la esegue un motore in modalita' autonoma.
E' REG-01, ed e' il punto per cui questa modalita' e' stata autorizzata affatto.

## 5. Le condizioni di arresto — ti fermi anche se non hai finito

### Limiti di risorsa
1. **Due ore di orologio.** Poi ti fermi, qualunque sia lo stato. Non e' un
   suggerimento e non ammette argomenti: la modalita' GOAL non ha tetto di spesa
   (`token_budget` e' spento nel prodotto), quindi il tetto e' questo.
2. **Tre turni consecutivi senza progresso** e ti fermi. Progresso vuol dire: un file
   creato, un dossier nuovo, o un collaudo che cambia colore. «Sto ancora analizzando»
   e' progresso al primo turno e stallo al terzo.
3. **Un lotto solo.** Questo mandato e' `ck-riproduci.sh`. Finito quello ti fermi e
   NON prosegui su altro, per quanto sia allettante e vicino.

### Limiti di condotta
4. **Serve modificare un file esistente del perimetro?** Dossier, e stop.
5. **Un collaudo verde diventa rosso: ti fermi, sempre.** Non c'e' l'eccezione «lo
   avevo previsto nel dossier»: prevederla non e' autorizzarla. Puoi **proporre** una
   regressione; farla ripartire richiede una persona.
   Il metro e' `missioni/2026-09-07-campi-obbligatori/MISURA-applicata-13-rossi.txt`:
   **663 verdi, 13 rossi**. Quei tredici erano gia' rossi. Se ne compare un
   quattordicesimo, ti fermi.
6. **Due giri di correzione gia' fatti sullo stesso problema.** Al terzo ti fermi: due
   giri falliti sono un problema di impostazione, non di esecuzione.
7. **Non riesci a eseguire il gate?** Consegna il lavoro dichiarandolo NON verificato.
   Un lavoro non verificato si consegna come non verificato, non come finito.

   **MA ATTENZIONE, ED E' MISURATO, NON SUPPOSTO.** Il 7/09/2026 e' stato provato:
   **tu a Docker non ci arrivi**, nemmeno da questa finestra interattiva. Lo abbiamo
   verificato mandandoti a lanciare un collaudo, e la controprova fuori dal tuo
   ambiente ha girato bene. Sta scritto in
   `missioni/2026-09-07-goal-riproduci/PROVE-DI-METODO.md`.

   **Questo NON ti assolve dal verificare.** I dodici comandi del gate hanno bisogno
   dei contenitori, e quelli non li lancerai. **Ma Prova A e Prova B della sezione 3
   girano in un repository FINTO usa-e-getta, e non toccano Docker per niente** —
   esattamente come `./scripts/ck-gate.sh --autotest`, che gira da solo e che puoi
   lanciare adesso per vedere come e' fatto.

   Quindi la riga di consegna e' questa, e non un'altra: **le due prove di fallimento
   le esegui e ne incolli l'output**; l'integrazione coi dodici comandi la dichiari
   non verificata e la misura la fa chi a Docker ci arriva. Dire «non posso verificare
   niente» sarebbe falso, e sarebbe il modo comodo di chiudere.

### E vale piu' di tutte
8. **Non uscire da questo worktree.** `../casinoking-platform` e' la copia viva su cui
   gira lo stack; `../m-and-m-games` e' un altro progetto. Se ti serve leggere qualcosa
   fuori, leggilo; scrivere fuori, mai.

## 6. Come si chiude

Non la dichiari tu marcando l'obiettivo completo. Scrivi in
`missioni/2026-09-07-goal-riproduci/ESITO.md`:

- cosa hai creato, con i percorsi;
- **l'output vero** di Prova A e Prova B, incollato, non riassunto;
- cosa hai lasciato aperto e perche';
- quali comandi hai lanciato e quali non sei riuscito a lanciare.

Poi il lavoro passa a un revisore indipendente che non sei tu. **Non marcare
l'obiettivo `complete` sulla base dell'intenzione, del progresso parziale o di una
risposta finale plausibile.** Il tuo stesso prodotto te lo dice; qui e' un ordine.

## 7. Se scopri che il mandato e' sbagliato

Fermati e scrivilo in `ESITO.md`. Hai gia' bloccato una stesura di questo mandato con
sei rilievi ed era la cosa piu' utile fatta quel giorno. **Un mandato sbagliato eseguito
bene resta lavoro buttato.**
