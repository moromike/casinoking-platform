# Piano di Refactoring: UI Area Finanziaria ("Vista Banco")

## Contesto
Il Product Owner ha rigettato l'attuale UI frammentata dell'area Finance (`adminSection === "casino_king"`). L'attuale dashboard piena di pulsanti "Carica..." e box separati (Panoramica, Riconciliazione, Sessioni Beta, Storico) deve essere completamente sostituita da un **singolo report tabellare**, caricato automaticamente, che si ispira all'estratto conto del giocatore (`player-account-page.tsx`).

## Obiettivi e Vincoli
1. **Unico Report Tabellare**: Rimuovere tutti i box pre-esistenti. L'intera area Finance conterrà solo filtri in alto e una tabella centrale.
2. **Caricamento Automatico**: Nessun pulsante "Carica". I dati vengono fetchati in automatico all'ingresso nell'area Finance.
3. **Filtri**: In alto alla tabella, barra dei filtri (Email, Wallet Type) che aggiorna automaticamente i dati.
4. **Colonne della Tabella**: 
   - Player (email)
   - Data/Ora (inizio-fine)
   - Gioco (game_code o "legacy")
   - Stato (status)
   - Totale Bet (bank_total_credit)
   - Totale Payout (bank_total_debit)
   - Delta Banco (bank_delta)
5. **Drill-down Accordion**: Cliccando su una riga della sessione, si espande una riga sottostante (`<tr>` con `colSpan`) che mostra i dettagli testuali degli eventi finanziari associati a quella sessione, richiamando dinamicamente l'API di dettaglio se necessario.

---

# TODO List — Task 4.4: Refactoring Singolo Report Finance

## Pre-condizioni
- Nessuna modifica al backend API (già validato e testato).
- Ripulire completamente il branch `adminSection === "casino_king"` in `frontend/app/ui/casinoking-console.tsx`.

## Task
### Task 4.4.1: Pulizia Stato e Rifiuti UI
- File: `frontend/app/ui/casinoking-console.tsx`
- Azione: 
  - Rimuovere dal render di `adminSection === "casino_king"` gli `article` relativi a "Panoramica finance", "Riconciliazione wallet", "Storico ledger recente", e i relativi pulsanti manuali "Carica report", "Carica storico".
  - Mantenere solo lo stato `adminFinancialSessionsReport` (e l'email filter). Rimuovere lo stato e la logica di `adminLedgerReport` e `adminLedgerTransactions` dal render di quella sezione, e ripulire i pulsanti non necessari.
- Vincoli: L'area deve diventare uno spazio vuoto pronto per accogliere la nuova tabella.
- Criterio di completamento: La sezione finance non mostra più i vecchi box.

### Task 4.4.2: Componente Report Tabellare (Livello 1)
- File: `frontend/app/ui/casinoking-console.tsx`
- Azione:
  - Implementare un `useEffect` che osserva `adminSection` (e i filtri) e lancia `handleLoadFinancialSessions()` in automatico quando l'area è `casino_king`.
  - Creare un layout `<table>` in stile `player-account-page.tsx`.
  - Intestazione (TH): Player, Data/Ora, Gioco, Stato, Totale Bet, Totale Payout, Delta Banco.
  - Corpo (TBODY): mappare le `sessions` del report. Formatizzare le valute in verde/rosso dove appropriato per il Delta.
  - Sopra la tabella: input per filtro email e select per `wallet_type` (Tutti, Cash, Bonus).
- Vincoli: Niente "Carica...". Lo stile della tabella deve usare larghezza 100% e `border-collapse: collapse` per essere pulito e professionale.
- Criterio di completamento: Tabella generata correttamente con dati dal backend.

### Task 4.4.3: Drill-down Espandibile (Livello 2)
- File: `frontend/app/ui/casinoking-console.tsx`
- Azione:
  - Aggiungere stato `expandedSessionId` (string | null).
  - Al click su un `<tr>` della tabella, impostare `expandedSessionId`. Se si espande e non abbiamo il dettaglio, chiamare `handleLoadFinancialSessionDetail(sessionId)`.
  - Sotto il `<tr>` della sessione espansa, renderizzare un secondo `<tr>` condizionale con `<td colSpan={7}>`.
  - All'interno della cella estesa, mostrare una mini-tabella o lista testuale degli `events` della sessione: `timestamp`, `transaction_type`, `wallet_type`, `bank_credit`, `bank_debit`, `delta`, e `game_enrichment`.
- Vincoli: UX ispirata a `player-account-page.tsx`. Niente pannelli separati o modali distaccati, l'audit visivo deve essere inline.
- Criterio di completamento: Cliccando su una riga si espande il dettaglio cronologico.

## Ordine di Esecuzione
Eseguire dal 4.4.1 al 4.4.3. Si consiglia di creare nuovi piccoli componenti separati all'interno di `casinoking-console.tsx` se il codice diventa troppo lungo, oppure scrivere il tutto in linea se più leggibile.

## Rischi e attenzioni
- Gestire il loading state (`busyAction`) in modo non intrusivo (es. opacity ridotta sulla tabella mentre ricarica) per evitare sfarfallii durante la digitazione nel filtro email.
- Gestire il debouncing per il filtro email se si usa `useEffect` per ricaricare, o un semplice pulsante "Applica filtri" affiancato se più semplice da implementare senza glitch. (Consigliato: un tasto "Filtra" per non impazzire coi debounce).