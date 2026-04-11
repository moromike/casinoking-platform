# Piano Esecutivo: Area Finanziaria "Vista Banco" (EPIC 4)

Questo documento fornisce la TODO list strettamente vincolante per l'implementazione dell'EPIC 4 (Task 4.2 e Task 4.3). L'agente in modalità Code deve seguire questi task pedissequamente, senza apportare modifiche architetturali autonome.

## Contesto
Implementazione del report finanziario aggregato per sessioni (`/admin/reports/financial/sessions`). L'approccio è "ledger-first", in sola lettura, e mantiene parallelamente l'esistente vista "Transazioni Raw" per sicurezza durante il transitorio.

## Pre-condizioni
- Lettura di `docs/FINANCIAL_AREA_DESIGN.md` per il contratto API.
- Nessuna scrittura a database è permessa nel codice di produzione/runtime (sola lettura su ledger e rounds per produrre report). **Nota bene:** La scrittura a DB è invece **obbligatoria e richiesta** nel setup dei test di integrazione per preparare i dataset reali.
- Mantenere le dipendenze esistenti per connessioni DB (`db_connection()`).

---

# TODO List — Task 4.2: Implementazione Backend API e Test

## Contesto
Creazione delle query SQL ledger-first, esposizione delle API e copertura tramite test di riconciliazione su database reale.

### Task 4.2.1: Definizione Modelli Pydantic
- File: `backend/app/api/routes/admin.py` (o nuovo file moduli se si preferisce separare, es. `backend/app/modules/reporting/models.py`)
- Azione: Creare i modelli Pydantic per la risposta dell'API di Livello 1 (Lista) e Livello 2 (Dettaglio), usando tipi stringa per i campi monetari (`bank_total_credit`, `bank_total_debit`, `bank_delta`, `delta`).
- Vincoli: Rispettare esattamente la struttura definita in `docs/FINANCIAL_AREA_DESIGN.md`. Non formattare visivamente gli importi (niente segni `+`).
- Criterio di completamento: Modelli pronti e type-safe.

### Task 4.2.2: Sviluppo Query Livello 1 (Elenco Sessioni)
- File: `backend/app/modules/admin/service.py` (creare funzione `get_financial_sessions_report`)
- Azione: Scrivere la query SQL che:
  1. Parte da `ledger_entries` filtrate sui conti `HOUSE_CASH`, `HOUSE_BONUS`, `GAME_PNL_MINES`, `PROMO_RESERVE`.
  2. Fa JOIN su `ledger_transactions`.
  3. Filtra rigorosamente il periodo usando `date_from` e `date_to` su `ledger_transactions.created_at` (tempo contabile).
  4. Restringe il perimetro contabile **solo ed esclusivamente** alle `ledger_transactions` associate a un round. Questo si ottiene facendo JOIN (o controllando la referenza) con `platform_rounds.start_ledger_transaction_id` o `platform_rounds.settlement_ledger_transaction_id`. Tutti i trasferimenti interni (es. admin adjustment) devono restare esclusi.
  5. Fa LEFT JOIN su `game_access_sessions`.
  6. Raggruppa per `access_session_id`. Se null, applica la logica deterministica di fallback legacy:
     - `session_id` = `legacy-{user_id}-{date(created_at)}`
     - `started_at` = `min(ledger_transactions.created_at)` del gruppo
     - `ended_at` = `max(ledger_transactions.created_at)` del gruppo
     - `status` = `"closed"`
  7. Calcola `SUM(amount) dove entry_side='credit'` (bank_credit) e `SUM(amount) dove entry_side='debit'` (bank_debit).
  8. Calcola `total_transactions` come conteggio delle sole transazioni contabili (house-side) incluse nel raggruppamento per calcolare i totali.
- Vincoli: Usare `psycopg` raw SQL con i parametri in sicurezza (`%s`). Calcolo rigoroso, nessun arrotondamento improprio a database.
- Criterio di completamento: La funzione ritorna il dict strutturato atteso dal Livello 1.

### Task 4.2.3: Sviluppo Query Livello 2 (Dettaglio Sessione)
- File: `backend/app/modules/admin/service.py` (creare funzione `get_financial_session_detail(session_id: str)`)
- Azione: Scrivere la query SQL che per una data sessione (vera o pseudo-legacy) estrae le singole transazioni collegate ai round (in base al perimetro definito in 4.2.2) e calcola il delta evento per evento. Fa LEFT JOIN con `mines_game_rounds` per preparare una stringa testuale minimale (`game_enrichment`).
- Vincoli: Il `delta` deve essere esposto riga per riga per audit. La JOIN con `mines_game_rounds` è puramente accessoria: se il record di gioco è mancante, la riga contabile **deve** essere comunque restituita (con `game_enrichment` vuoto o base) e non deve essere persa.
- Criterio di completamento: La funzione ritorna il dict atteso dal Livello 2.

### Task 4.2.4: Esposizione Endpoints API
- File: `backend/app/api/routes/admin.py`
- Azione: Aggiungere le due route GET:
  - `GET /reports/financial/sessions`
  - `GET /reports/financial/sessions/{session_id}`
- Vincoli: Proteggere entrambe le route con il dependency `require_admin_area("finance")`.
- Criterio di completamento: Le API rispondono conformemente ai modelli definiti chiamate tramite client HTTP in test di integrazione, eseguendo le query su un database di test popolato in precedenza da dati reali/sintetici completi (no mock).

### Task 4.2.5: Matrice di Test Obbligatoria
- File: `tests/integration/test_admin_financial_reports.py` (da creare)
- Azione: Implementare i test definiti nella matrice:
  1. *Test di riconciliazione:* popolare DB con un dataset misto (round completi, round orfani, bonus, admin adjust). Il test calcola il delta banco totale tramite query SQL manuale (su `ledger_entries` filtrate al perimetro di round, tempo contabile) e asserisce che la somma matematica dei `bank_delta` restituiti dall'API per lo stesso periodo coincida esattamente.
  2. *Test Legacy:* generare transazioni di round nel ledger *senza* un `access_session_id` e verificare la corretta generazione deterministica della pseudo-sessione `legacy-...` (inclusi i campi temporali min/max e status closed).
  3. *Test Cash/Bonus:* verificare la netta separazione dei dati impostando i query params per filtrare i conti `HOUSE_CASH` e `HOUSE_BONUS`.
  4. *Test Ciclo di Vita:* test sui segni banco (addebito/accredito) simulando un round perso, vinto o annullato.
- Vincoli: Usa i meccanismi di fixture esistenti (`db_connection`, test_client). Nessun test mockato: setup DB con scritture e interazioni API reali.
- Criterio di completamento: Suite di test `test_admin_financial_reports.py` verde.

---

# TODO List — Task 4.3: Implementazione Frontend UI

## Contesto
Aggiungere la nuova tabella di aggregazione sessioni alla vista admin esistente (senza rimuovere la vecchia).

### Task 4.3.1: Configurazione Nuova Sub-Area Admin
- File: `frontend/app/ui/casinoking-console.tsx`
- Azione: Aggiungere un nuovo tab o sub-menu "Sessioni Finanziarie (Beta)" di fianco all'esistente report ledger in `adminSection === "casino_king"`.
- Vincoli: Visibile solo se `canAccessFinance` o `isSuperadmin`.
- Criterio di completamento: Pulsante di navigazione inserito coerentemente.

### Task 4.3.2: Componente Tabella Livello 1
- File: `frontend/app/ui/casinoking-console.tsx` (o nuovo file dedicato in `frontend/app/ui/admin/financial-sessions-table.tsx` se preferibile per ordine)
- Azione: Chiamare `GET /admin/reports/financial/sessions` e mostrare una tabella. Colonne: Utente, Inizio/Fine, Status, Transazioni, Bank Credit, Bank Debit, Delta Banco.
- Vincoli: Il backend invia solo stringhe non decorate ("10.00", "-5.00"). Tutta la formattazione visiva spetta a questo componente (aggiungere il segno e i colori: verde se vincita banco/positivo, rosso se perdita banco/negativo).
- Criterio di completamento: Tabella renderizzata correttamente con dati e formattazione.

### Task 4.3.3: Componente Drill-Down Livello 2
- File: `frontend/app/ui/casinoking-console.tsx` (o nuovo file in `frontend/app/ui/admin/financial-session-detail.tsx`)
- Azione: Al click su una riga di Livello 1, chiamare l'API `{session_id}` e mostrare un pannello interno o modale con l'elenco cronologico degli eventi. Mostrare il `delta` riga per riga e la stringa `game_enrichment`.
- Vincoli: Niente grafica o icone gioco: stile "audit/terminale" pulito.
- Criterio di completamento: Navigazione base Master-Detail funzionante.

## Ordine di esecuzione
I task vanno completati ed eseguiti sequenzialmente dal 4.2.1 al 4.3.3, garantendo ad ogni step il superamento dei test o linting, senza procedere se lo step precedente fallisce.

## Rischi e attenzioni
- Se in 4.2.2 la query SQL si complica troppo causando errori di GROUP BY, la mitigazione obbligatoria è usare CTE (Common Table Expressions) o dividere in due query separate da fondere via Python, garantendo leggibilità.
- In fase di setup dei dataset nei test, accertarsi di creare le transazioni in UTC e simulare l'attraversamento della mezzanotte per validare correttamente il bucket legacy.
