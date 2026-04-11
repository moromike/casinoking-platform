# Analisi e Design: Area Finanziaria e Vista Banco (EPIC 4)

## Contesto
Questo documento definisce il design architetturale e il contratto API per il rifacimento dell'Area Finanziaria ("Vista Banco"). Attualmente l'area amministrativa mostra un mero elenco di transazioni ledger (`/admin/reports/ledger`). L'obiettivo è introdurre un modello aggregato per "Sessione di Gioco" (`game_access_sessions`), permettendo all'operatore finance di avere una visione chiara dei profitti/perdite (PNL) raggruppati per sessione utente.

## Obiettivi e Vincoli
1. **Regola Aurea Ledger-First**: Il report deve ricavare ogni centesimo dai posting contabili effettivi (`ledger_transactions` + `ledger_entries`). `platform_rounds` e `game_access_sessions` sono solo dimensioni logiche per il raggruppamento (GROUP BY) e l'arricchimento dei metadati.
2. **Vista Banco Deterministica e Delimitata**:
   - Il **Delta Banco** è la variazione netta dei conti aziendali (`HOUSE_CASH`, `HOUSE_BONUS`, `GAME_PNL_MINES`, `PROMO_RESERVE`).
   - Credito su conto house = Guadagno per il banco (es. bet piazzata).
   - Addebito su conto house = Perdita per il banco (es. payout erogato).
   - **Perimetro di calcolo**: Il report include esclusivamente le transazioni contabili collegate a un round (via `start_ledger_transaction_id` o `settlement_ledger_transaction_id` in `platform_rounds`). Sono esplicitamente **esclusi** admin adjustments, erogazioni bonus stand-alone e trasferimenti interni.
3. **Drill-down Separato per Contesto**: I numeri contabili appartengono al core platform. I dettagli testuali del gioco (es. griglia, mine rivelate) derivano da `mines_game_rounds` e servono unicamente come metadato descrittivo, non partecipano al calcolo.
4. **Retrocompatibilità Unassigned Deterministica**: I round legacy o le transazioni prive di `access_session_id` non andranno persi. Verranno raggruppati in un bucket pseudo-sessione generato deterministicamente per utente e per giorno solare UTC (es. `legacy-{user_id}-{YYYY-MM-DD}`).
   - **started_at**: coinciderà con il `min(ledger_transactions.created_at)` del bucket.
   - **ended_at**: coinciderà con il `max(ledger_transactions.created_at)` del bucket.
   - **status**: sempre `"closed"`.
5. **Transizione Sicura**: La vecchia vista raw (`get_ledger_report_for_admin()`) verrà mantenuta in parallelo come strumento di audit fino a consolidamento del nuovo modello.

---

## Modello Dati e Read-Model

Le tabelle coinvolte nella costruzione della view di Livello 1 (Lista Sessioni):
- **Core Numerico**: `ledger_entries` unito a `ledger_transactions` e `ledger_accounts`.
- **Relazione**: Le `ledger_transactions` sono mappate ai `platform_rounds` tramite `start_ledger_transaction_id` e `settlement_ledger_transaction_id`.
- **Raggruppamento**: I `platform_rounds` appartengono a `game_access_sessions` tramite `access_session_id`.

I round senza `access_session_id` seguiranno la logica del bucket giornaliero deterministico menzionata sopra.

---

## Contratto API

*Nota tecnica: I valori monetari vengono restituiti come decimal string neutre senza formattazione visiva (nessun segno "+" implicito). La colorazione e i segni saranno gestiti esclusivamente dal Frontend.*

### Livello 1: Lista Sessioni (Elenco Aggregato)
**Endpoint**: `GET /admin/reports/financial/sessions`

**Filtri supportati (Query Params)**:
- `user_id` / `email`: filtra per utente
- `wallet_type`: es. `cash`, `bonus` (per filtrare i conti PnL associati)
- `date_from` / `date_to`: range temporale basato sul **tempo contabile** (ovvero `ledger_transactions.created_at`, non l'inizio o la fine operativa della sessione). Questo garantisce che la somma economica del periodo sia esatta e inconfutabile.
- `include_legacy`: boolean, se mostrare anche le pseudo-sessioni "Unassigned"

**Risposta (Data array)**:
```json
{
  "success": true,
  "data": {
    "sessions": [
      {
        "session_id": "uuid", // Oppure "legacy-uuid-YYYY-MM-DD"
        "is_legacy": false,
        "user_id": "uuid",
        "user_email": "player@example.com",
        "game_code": "mines",
        "started_at": "2026-04-09T18:00:00Z",
        "ended_at": "2026-04-09T18:15:00Z",
        "status": "closed",
        "total_transactions": 30,
        "bank_total_credit": "150.00", 
        "bank_total_debit": "120.00",  
        "bank_delta": "30.00" // credit - debit (può essere negativo, es. "-15.00")
      }
    ],
    "summary": {
      "total_bank_delta_period": "30.00" 
    }
  }
}
```

### Livello 2: Drill-down Singola Sessione
**Endpoint**: `GET /admin/reports/financial/sessions/{session_id}`

**Risposta**:
```json
{
  "success": true,
  "data": {
    "session_id": "uuid",
    "user_email": "player@example.com",
    "bank_total_credit": "150.00",
    "bank_total_debit": "120.00",
    "bank_delta": "30.00",
    "events": [
      {
        "ledger_transaction_id": "uuid",
        "platform_round_id": "uuid",
        "timestamp": "2026-04-09T18:01:00Z",
        "transaction_type": "bet",
        "wallet_type": "cash",
        "bank_credit": "10.00",
        "bank_debit": "0.00",
        "delta": "10.00",
        "game_enrichment": "Mines: Griglia 25, 3 Mine (Bozza/Safe Reveals: 0)"
      },
      {
        "ledger_transaction_id": "uuid",
        "platform_round_id": "uuid",
        "timestamp": "2026-04-09T18:01:45Z",
        "transaction_type": "win",
        "wallet_type": "cash",
        "bank_credit": "0.00",
        "bank_debit": "5.00", // Payout 5 erogato
        "delta": "-5.00",
        "game_enrichment": "Mines: Cashout dopo 4 rivelazioni sicure"
      }
    ]
  }
}
```

---

## Matrice di Test Obbligatoria (Da implementare in Code mode)

Il superamento di questa EPIC è vincolato all'implementazione dei seguenti test di integrazione (`tests/integration/test_admin_financial_reports.py`):

1. **Riconciliazione (Report vs Ledger Totale)**: Creare una query ledger-first pura (solo `ledger_entries` filtrate sui conti PNL/House nel periodo, considerando solo le transazioni con referenza ai round). La somma matematica dei `bank_delta` restituiti dall'API Livello 1 per lo stesso periodo **deve** coincidere esattamente con il delta contabile reale.
2. **Contract Test**: Validazione rigorosa della struttura API (numeri restituiti come stringhe non formattate).
3. **Legacy/Null Session Link Deterministico**: Generare round nel ledger *senza* un `access_session_id` associato e verificare che vengano raggruppati correttamente nel bucket legacy giornaliero (`legacy-{user_id}-{date}`), e che le tempistiche (`started_at`, `ended_at`) e lo `status` vengano calcolati deterministicamente come definito nel design.
4. **Cash vs Bonus**: Assicurarsi che i filtri permettano di separare il delta PNL "Cash" da quello "Bonus", usando regole strette sul ledger account (es. `HOUSE_CASH` vs `HOUSE_BONUS`).
5. **Stati Ciclo di Vita Round**: Simulazione di scommesse, vincite e round cancellati, verificando il corretto calcolo del Delta Banco.

---

## TODO List - EPIC 4 - Implementazione Area Finanziaria

### Contesto
Implementare il nuovo report finanziario "Vista Banco" aggregato per sessioni, garantendo la correttezza contabile ledger-first e la solidità dei test di riconciliazione.

### Task 4.2: Implementazione Backend API
- File: `backend/app/api/routes/admin.py`, `backend/app/modules/admin/service.py`, `tests/integration/test_admin_financial_reports.py`
- Azione: Creare le due nuove GET API. Scrivere la query SQL di aggregazione usando JOIN rigorose tra `ledger_entries` e conti house/PNL per estrarre i numeri, raggruppando logicamente tramite `platform_rounds` e `game_access_sessions`.
- Vincoli: Read-only. Il calcolo si basa **solo** su `ledger_entries.amount`. Il perimetro è limitato ai movimenti legati ai round. Nessuna assunzione grafica/UI per i numeri nel backend.
- Test: Eseguire e validare l'intera **Matrice di Test Obbligatoria** usando una query di riconciliazione PNL custom.
- Criterio di completamento: API testata e coperta al 100% rispetto alla matrice, i conti tornano al centesimo.

### Task 4.3: Implementazione UI Admin
- File: `frontend/app/ui/casinoking-console.tsx`
- Azione: Aggiungere menu "Sessioni (Beta)" sotto Admin -> Finanza. Gestire il formato visivo dei delta restituiti dalle API (es. colorazione verde/rossa in base al segno + / -).
- Vincoli: UX adatta a operatore finance. Mantenere la tab "Transazioni Raw".
- Test: Navigazione fluida e filtri funzionanti.
- Criterio di completamento: Nuova tab utilizzabile.
