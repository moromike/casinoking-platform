# Piano di Refactoring Report Finanziario

## Contesto e Obiettivo
Il report finanziario (storicamente "Report sessioni banco") richiede un potenziamento per fornire strumenti operativi all'amministratore, pur mantenendo la sua natura aggregata. Il report deve continuare a visualizzare **sessioni aggregate**, non le singole transazioni, fornendo una visione ad alto livello dell'andamento finanziario del banco.

I nuovi requisiti richiesti sono:
1.  **Granularità**: Mantenere la visualizzazione per sessioni aggregate.
2.  **Filtri Potenziati**:
    *   Data Inizio / Fine (basate sul tempo contabile).
    *   Tipo di transazione: inclusione di una sessione se contiene *almeno una* transazione del tipo specificato (es. scommessa, vincita).
    *   ID/Email Giocatore: supporto congiunto (user_id per navigazione, email testuale per ricerca), mantenendo l'email come identificativo primario esposto in UI.
    *   Importo Min/Max: filtro basato sul *Delta Banco* (profitto/perdita del banco) della sessione aggregata.
3.  **Visualizzazione Email Giocatore**: Esibire l'email del giocatore in modo prominente in UI, affiancandola o sostituendo parzialmente la sola esposizione dell'UUID.
4.  **Esclusione Sessioni Non Loggate (Legacy - Opzione A RIMOZIONE)**: Poiché il report è operativo sulle sessioni utente, le transazioni orfane (bonus, adjustments) o `access_session_id IS NULL` saranno **escluse di default**. Rimuoviamo il parametro `include_legacy` da questo endpoint, demandando l'analisi contabile pura e globale a `/admin/ledger`.
5.  **Layout e Paginazione**: 
    *   Implementare paginazione completa backend (limite, offset, totale).
    *   Aggiungere totale per pagina calcolato sul `Delta Banco` dei record visibili.
    *   Selezione righe per pagina (20/50/100/500, default 50).

---

## Stato Attuale vs Stato Target

| Feature | Stato Attuale | Stato Target |
| :--- | :--- | :--- |
| **Paginazione** | Nessuna, intero data set | Paginazione SQL via DB (Limit/Offset) con conteggio totale record |
| **Aggregazione** | Via codice Python in memoria | Nativamente in SQL (`GROUP BY access_session_id`) usando CTE `round_transaction_links` |
| **Filtri** | User ID, Email, Wallet, Date | + Tipo Transazione, + Importo Delta Banco, Filtri Date su `created_at` (Tempo Contabile) |
| **Dati Legacy** | Inclusi di default, fusi (bucket deterministico) | Totalmente esclusi da questa vista operativa (No `access_session_id IS NULL`) |
| **Totali** | Solo totale globale del periodo | Totale calcolato e visualizzato per la singola pagina caricata |

---

## Interpretazione Tecnica dei Filtri

- **Tempo Contabile (Filtri Data)**: I filtri `date_from` e `date_to` non agiscono sul tempo nominale della sessione (`started_at`), ma rigorosamente sul **tempo contabile** delle singole transazioni, ossia `ledger_transactions.created_at`. In questo modo la somma algebrica della pagina riflette esattamente il transato del periodo.
- **Filtro "Tipo transazione" su vista Sessione**: Una sessione viene inclusa nei risultati se la condizione restituisce VERO per *almeno una* delle transazioni che la compongono (es. filtro `HAVING bool_or(lt.transaction_type = %(tx_type)s)`).
- **Filtro "Importo" su vista Sessione**: Il filtro agisce sul **Delta Banco** aggregato, ovvero la somma degli incassi del banco (crediti su passività) meno i pagamenti (debiti su passività) all'interno della sessione.

---

## TODO List per il modo Code

### Task 1: [Backend] Modelli e Tipi di Dato (API)
- **File**: `backend/app/api/routes/admin.py`, o modulo `responses.py`.
- **Azione**:
  - Ridefinire in modo esplicito il contratto di `FinancialSessionsReportResponse`. Tutti i campi devono essere obbligatori per rimuovere ambiguità lato client.
  - Struttura target:
    ```python
    class PaginationMeta(BaseModel):
        page: int
        limit: int
        total_items: int
        total_pages: int

    class PageTotals(BaseModel):
        bank_delta: str # Formattato in Decimal per UI

    class FinancialSessionsReportResponse(BaseModel):
        sessions: list[FinancialSessionSummaryResponse]
        pagination: PaginationMeta
        page_totals: PageTotals
        summary: dict # O opzionale/nullabile, se mantenuto per compatibilità
    ```
- **Vincoli**: Assicurarsi che ogni record in `sessions` contenga `user_email`.

### Task 2: [Backend] Service di Estrazione Dati (Refactoring SQL)
- **File**: `backend/app/modules/admin/service.py`
- **Azione**:
  - Riscrivere l'estrazione (`get_financial_sessions_report`) per usare una query di raggruppamento SQL (`GROUP BY rtl.access_session_id`).
  - La query deve riutilizzare il concetto della CTE `round_transaction_links` (cfr. riga 1084) per unire `platform_rounds pr` a `ledger_transactions lt` (tramite `start_ledger_transaction_id` o `reference_id` per win), prelevando `access_session_id` da `pr`.
  - **Filtri SQL**:
    - **Date (Tempo Contabile)**: `lt.created_at >= date_from` e `lt.created_at <= date_to`.
    - **Email/User**: `u.id = %(user_id)s` e `u.email ILIKE %(email_query)s`.
    - **Legacy**: `WHERE rtl.access_session_id IS NOT NULL` per escludere transazioni orfane. Rimuovere dal service logiche legacy e parametri `include_legacy`.
    - **Transaction Type**: Aggiungere `HAVING bool_or(lt.transaction_type = %(tx_type)s)` al raggruppamento sessioni se valorizzato.
    - **Importo Delta Banco**: Filtrare sull'aggregato `HAVING (SUM(crediti) - SUM(debiti)) BETWEEN %(min_delta)s AND %(max_delta)s`.
  - Implementare conteggio totale record su CTE filtrata, ed eseguire query principale con `LIMIT` e `OFFSET`.

### Task 3: [Backend] Endpoint API
- **File**: `backend/app/api/routes/admin.py`
- **Azione**:
  - Aggiornare l'endpoint `GET /admin/reports/financial/sessions`.
  - I parametri in query string devono includere congiuntamente `user_id` (str, opzionale, UUID) e `email` o `email_query` (str, opzionale).
  - Introdurre i nuovi parametri: `page` (default 1), `limit` (default 50), `transaction_type` (str), `min_delta` (str), `max_delta` (str).
  - Rimuovere dall'endpoint la gestione di `include_legacy`.

### Task 4: [Frontend] Gestione Stato e Filtri UI
- **File**: `frontend/app/ui/casinoking-console.tsx` (o equivalente report panel)
- **Azione**:
  - Aggiungere stato per filtri transazione (`adminTransactionTypeFilter`, `adminMinDeltaFilter`, `adminMaxDeltaFilter`) ed esporli visivamente.
  - Aggiungere stati `adminCurrentPage` (default 1) e `adminItemsPerPage` (default 50).
  - Predisporre controlli di input coerenti e robusti.

### Task 5: [Frontend] Tabella Sessioni e Paginazione
- **File**: `frontend/app/ui/casinoking-console.tsx`
- **Azione**:
  - Adattare la tabella per visualizzare "Email" in colonna prominente affiancata a (o in sostituzione di) "User ID".
  - Mostrare selettore righe pagina: 20/50/100/500 (default 50).
  - Mostrare i controlli di impaginazione ("Pagina Precedente", "Successiva", "Pagina X di Y").
  - In fondo alla pagina, mostrare visibilmente il **Totale Delta Banco Pagina** ricavato da `response.page_totals.bank_delta`.

### Task 6: [Test] Integrazione
- **File**: `tests/integration/test_admin_financial_reports.py`
- **Azione**:
  - Aggiungere/modificare i test backend verificando la paginazione, la struttura fissa di risposta API e l'esclusione legacy forzata.
  - Test per validare filtri: `user_id`, `email`, date su contabilità `created_at`, e vincoli di importo minimo/massimo delta bancario.
  - Testare il filtro logico combinato con `HAVING` (es: sessione che *include* una specifica transazione).
- **File**: *Test Cypress o Playwright per Frontend/Admin*
  - Aggiungere/Aggiornare test che confermino in UI:
    - Default `page-size` a 50 ed esistenza opzioni 20/50/100/500.
    - Presenza predominante dell'`email player` nella tabella reportistica.
    - Presenza a fine tabella del `totale delta pagina`.
    - Navigazione coerente tra pagine.
    - Assenza di record senza sessione nella lista operativa.

---

## Ordine di esecuzione
1. Task 1 (Modelli API) - Per blindare il contratto tra i livelli.
2. Task 2 (Service) - Cuore del refactoring SQL e logiche contabili/aggregative.
3. Task 3 (Endpoint) - Esposizione API e parametri input.
4. Task 6 (Test Backend) - Convalidare logicamente SQL e controller.
5. Task 4 & 5 (Frontend) - Implementazione layout UI e controlli paginazione.
6. Task 6 (Test UI) - Verifica E2E visualizzazione filtri e formattazioni.

## Rischi e attenzioni
- **Join Sessione/Round**: L'associazione contabile tra transazione e sessione *non* avviene su `lt.access_session_id` (che non esiste nativamente come FK sul transazionale puro), ma tramite la struttura `platform_rounds`. Usare tassativamente la logica `round_transaction_links` già presente per recuperare `rtl.access_session_id`.
- **Rimozione Legacy**: Scegliere l'Opzione A assicura pulizia operativa e rimuove rumore contabile "orfano" da questa vista di sessione. Tuttavia, ciò enfatizza che per riconciliazioni totali del casinò si deve usare il Ledger, perché questa view escluderà aggiustamenti e bonus liberi. È il comportamento voluto.
- **Rigorosità Temporale**: Filtrare la sessione basandosi su `lt.created_at` implica che se una sessione inizia il giorno 1 e termina il giorno 2, le transazioni avverranno in giorni diversi. L'interrogazione delle sessioni nel "giorno 1" considererà solo il parziale finanziario di quella sessione transato nel giorno 1. È l'approccio corretto per mantenere la coerenza contabile.