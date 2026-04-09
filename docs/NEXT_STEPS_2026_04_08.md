# Next Steps: 8 Aprile 2026

## Completato in questa fase

1. **Risoluzione warning IDE / config locale**
   - fix import frontend e path condivisi
   - fix warning TypeScript su `ignoreDeprecations`
   - fix configurazione Pylance / typing test

2. **Estratto conto player**
   - tabella sessioni più leggibile
   - dettaglio mani espandibile
   - colonna delta lato player

3. **Backoffice Mines**
   - migliorato il workflow draft / publish
   - chiarito il significato operativo dei pulsanti
   - migliorata leggibilità CSS del backoffice

4. **Separazione login player / admin**
   - login player e login admin separati logicamente
   - storage frontend separato
   - blocco accessi cross-role sulle route sensibili

## TODO / Backlog prioritario concordato

1. **Revisione e pulizia codice generale**
   - ripassare il codice toccato negli ultimi cambiamenti
   - ridurre parti sporche / duplicate / accrocchi locali
   - migliorare coerenza tra frontend player, admin e Mines
   - approfondimento operativo:
     - rivedere i punti in cui shell player, shell admin e modulo Mines condividono ancora logica o stato in modo fragile
     - individuare helper, storage, side effects e funzioni duplicate o troppo accoppiate
     - distinguere pulizia strutturale, pulizia semantica e pulizia UX per non mischiare fix diversi nello stesso intervento
     - chiudere i residui introdotti come workaround locali durante i fix rapidi delle ultime sessioni

2. **Stabilizzazione finale gioco Mines**
   - review completa del flusso di gioco
   - pulizia del comportamento runtime
   - verifica UX desktop/mobile/embed
   - approfondimento operativo:
     - validare end-to-end start, reveal, cashout, resume, fairness, launch token e access session
     - verificare comportamento corretto su refresh, tab chiusa, sessione interrotta e token non valido
     - controllare che configurazione pubblicata e configurazione effettiva di gioco restino sempre coerenti
     - rifinire i punti in cui il gioco oggi appare ancora tecnico invece che naturale per l'utente finale

3. **Stabilizzazione finale backoffice admin / Mines**
   - rifinire workflow e comprensibilità lato operatore umano
   - verificare che draft, salvataggio e publish siano davvero intuitivi
   - continuare a togliere ambiguità operative
   - approfondimento operativo:
     - chiarire visivamente cosa è bozza attiva, cosa è bozza salvata e cosa è produzione live
     - verificare che ogni bottone produca un effetto esplicito, leggibile e prevedibile
     - rendere tutte le tab del backoffice utilizzabili da chi non conosce il modello dati o il codice
     - ridurre il numero di azioni interpretabili in più modi diversi

4. **Cambio password player**
   - rendere il flusso di cambio password del giocatore chiaro e completo nell'area account
   - approfondimento operativo:
     - decidere dove vive il cambio password nel percorso account player
     - chiarire messaggi di successo, errore, credenziali invalide e stato post-cambio
     - verificare coerenza tra login, reset password e cambio password ordinario
     - evitare qualunque contaminazione del percorso admin dentro il percorso player

5. **Profilo admin + cambio password admin**
   - creare una sezione admin dedicata alle informazioni del proprio account
   - aggiungere il cambio password per l'amministratore
   - approfondimento operativo:
     - definire una sezione `My Space` chiara, autonoma e non mischiata con la gestione giocatori
     - mostrare i dati minimi dell'admin autenticato in modo pulito
     - progettare il cambio password admin con messaggi chiari e flusso separato dal player
     - verificare che la nuova separazione auth player/admin resti coerente anche dopo il cambio password

6. **Gestione utenti admin / superadmin**
   - introdurre una sezione dedicata nel backoffice per la gestione degli admin
   - definire il concetto di `superadmin` come unico soggetto che puo' creare altri admin
   - il superadmin deve poter creare un admin indicando:
     - email
     - password iniziale impostata dal superadmin
     - aree visibili / gestibili
   - per il primo step, le aree operative sono:
     - Finance
     - Gestione End-User
     - Mines
   - regola MVP: se un admin vede un'area, puo' fare tutto dentro quell'area
   - aggiungere anche una sezione `My Space` per ogni admin con:
     - info account admin
     - cambio password admin
   - nota: in futuro questa parte verra' evoluta con permessi piu' granulari, ma per ora il modello resta volutamente semplice
   - approfondimento operativo:
     - definire il modello dati minimo per superadmin, admin e aree autorizzate
     - chiarire chi può creare, modificare, sospendere o rimuovere altri admin
     - definire il flusso UI di creazione admin in modo lineare e non ambiguo
     - garantire che un admin non autorizzato non veda nemmeno le sezioni fuori perimetro

7. **Ripensamento totale area finanziaria**
   - analisi da zero
   - definizione corretta dei bisogni reali
   - disegno architetturale e UX prima di implementare qualunque schermata definitiva
   - approfondimento operativo:
     - distinguere reporting, riconciliazione, storico giocatore, ledger view e operatività finance
     - mappare i veri utenti interni della sezione finance e i loro bisogni concreti
     - costruire prima un linguaggio di prodotto comprensibile e solo dopo API / schermate
     - evitare di fare patch cosmetiche su una parte ancora non progettata seriamente
   - traduzione operativa richiesta dal PO:
     - pensare l'area finance come un **grande estratto conto giocatore applicato a tutti i giocatori**
     - il cuore della vista deve essere la lista delle **sessioni di gioco**
     - ogni sessione deve essere trattata come unità principale di lettura amministrativa, non come semplice elenco di transazioni sparse
     - la lista deve includere sessioni:
       - aperte
       - chiuse
       - con dettagli sintetici immediatamente leggibili
     - per ogni sessione devono essere esposti almeno i campi:
       - giocatore
       - gioco
       - data/ora inizio sessione
       - data/ora fine sessione
       - ingresso sessione
       - uscita sessione
       - delta
     - il **delta** in questa vista deve essere pensato **dal punto di vista del banco**, quindi con segno opposto rispetto alla vista player
     - i primi filtri richiesti sono:
       - filtro per giocatore
       - filtro per giorno / ora
       - filtro per importi maggiori di
       - filtro per importi minori di
     - deve esistere una futura **vista di sessione** dedicata dove l'operatore apre una singola sessione e vede:
       - il report/history delle mani della sessione
       - il dettaglio di ciò che ha visto il giocatore al momento della perdita o del ritiro
       - non serve la sequenza visuale del rendering schermo, ma serve il contenuto operativo della mano e dell'esito percepito dal giocatore
     - chi implementerà questa parte dovrà quindi progettare almeno 2 livelli distinti:
       - **livello 1: report sessioni aggregato** (vista banca)
       - **livello 2: drill-down della singola sessione** con history/report mani
     - questa parte va progettata come prodotto finance/read-model dedicato, non come semplice estensione improvvisata del ledger o del wallet detail

8. **Finalizzazione sito web player**
   - polishing visivo
   - coerenza generale del prodotto
   - obiettivo qualitativo: aspetto bello, pulito, presentabile, percezione “wow”
   - approfondimento operativo:
     - rifinire lobby, login, register, account e shell di gioco come esperienza unica coerente
     - eliminare l'effetto prototipo / pannello tecnico ancora percepibile in alcuni punti
     - lavorare su gerarchia visiva, spacing, contrasto, CTA e qualità percepita generale
     - arrivare a un risultato che sembri già pronto e professionale a colpo d'occhio

## Nota metodologica

Per le prossime fasi vale questa regola:
- prima analisi e chiarimento UX/architetturale
- poi validazione
- poi implementazione
- infine test utente e rifinitura
