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

2. **Stabilizzazione finale gioco Mines**
   - review completa del flusso di gioco
   - pulizia del comportamento runtime
   - verifica UX desktop/mobile/embed

3. **Stabilizzazione finale backoffice admin / Mines**
   - rifinire workflow e comprensibilità lato operatore umano
   - verificare che draft, salvataggio e publish siano davvero intuitivi
   - continuare a togliere ambiguità operative

4. **Cambio password player**
   - rendere il flusso di cambio password del giocatore chiaro e completo nell'area account

5. **Profilo admin + cambio password admin**
   - creare una sezione admin dedicata alle informazioni del proprio account
   - aggiungere il cambio password per l'amministratore

6. **Ripensamento totale area finanziaria**
   - analisi da zero
   - definizione corretta dei bisogni reali
   - disegno architetturale e UX prima di implementare qualunque schermata definitiva

7. **Finalizzazione sito web player**
   - polishing visivo
   - coerenza generale del prodotto
   - obiettivo qualitativo: aspetto bello, pulito, presentabile, percezione “wow”

## Nota metodologica

Per le prossime fasi vale questa regola:
- prima analisi e chiarimento UX/architetturale
- poi validazione
- poi implementazione
- infine test utente e rifinitura
