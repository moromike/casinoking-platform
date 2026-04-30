# Analisi e Pianificazione: UI/UX & Paradigma Sessioni (P1)

Questo documento traccia l'analisi architetturale scaturita dai feedback del Product Owner, separando gli interventi di "Quick Win" UI dalla profonda revisione del modello di dominio (Sessioni vs Spin).

---

## 1. Quick Wins: UI e Formattazione

Questi interventi sono puramente a livello di React/Frontend e non toccano il database.

### 1.1. Gestione Visibilità Auth (Navigazione)
- **Problema:** I bottoni "Login" e "Register" compaiono anche per gli utenti loggati (nella Bottom Nav mobile e nella Hero Banner della Lobby).
- **Azione:** Sfruttare lo stato globale o il Context React dell'autenticazione (`authState.isAuthenticated`) per **nascondere dinamicamente** qualsiasi riferimento al Login/Registrazione se l'utente è già dentro. Nella Lobby, i bottoni verranno sostituiti da un generico "Benvenuto, [Nome]" o rimossi del tutto per favorire l'ingresso nei giochi. La navigazione mobile (`PLAYER_NAV_ITEMS`) verrà filtrata condizionalmente.

### 1.2. Formattazione Decimale dei Saldi
- **Problema:** I saldi (Balances) mostrano 4-6 decimali, creando un'esperienza visiva non "da consumatore finale" (es. `1000.000000`).
- **Azione:** In `frontend/app/lib/helpers.ts`, la funzione `formatChipAmount` verrà aggiornata per arrotondare a **2 decimali** (es. `value.toFixed(2)`).
- **Guardrail:** Il database PostgreSQL (`numeric(18,6)`) e le logiche di ledger backend continueranno a lavorare e salvare i dati a 6 decimali per la massima precisione contabile. L'arrotondamento è puramente estetico.

### 1.3. Paginazione ad Aree (Tabs) nell'Account
- **Problema:** La pagina dell'Estratto Conto (`/account`) mischia tutte le informazioni in un lungo scroll verticale.
- **Azione:** Riscrivere `player-account-page.tsx` inserendo una navigazione a Tabs orizzontali:
  1. **Profilo:** Dati anagrafici (Nome, Cognome, CF, ecc.).
  2. **Sicurezza:** Nuovo modulo per il Cambio Password dell'utente loggato.
  3. **Cassa:** Saldi, Bonus, simulazione Versamento e Prelievo.
  4. **Estratto Conto:** La tabella cronologica (Home Banking) delle sessioni di gioco.

---

## 2. Ristrutturazione Profonda: "Sessioni di Accesso" vs "Spin"

Questo è il punto architetturale più critico sollevato dal PO, che allinea il sistema al modello classico ADM (Monopoli di Stato Italiano).

### 2.1. L'As-Is (Il Modello Attuale)
Oggi, il nostro database tratta il singolo round di Mines (il singolo `Bet`) come una `platform_round` (che prima chiamavamo storicamente `game_sessions`). Non tracciamo "quanto tempo l'utente è stato dentro la pagina del gioco".

### 2.2. Il To-Be (Il Nuovo Modello Architetturale)
Il PO ha richiesto l'introduzione di una gerarchia a 3 livelli:
1. **Utente**
2. **Access Session (Sessione di Accesso al Gioco):** Il periodo di tempo che intercorre da quando il giocatore apre la finestra del gioco a quando la chiude (o va in timeout).
3. **Spin (La singola giocata/Round):** La singola puntata su Mines (che oggi mappiamo come `platform_round`).

**Impatto sul Backend (Database & API):**
- **Nuova Tabella `game_access_sessions`:** 
  - Campi: `id`, `user_id`, `game_code`, `started_at`, `last_activity_at`, `ended_at`, `status` (active, closed, timed_out).
- **Modifica a `platform_rounds`:**
  - Aggiungere una foreign key: `access_session_id REFERENCES game_access_sessions(id)`. Ogni singolo "Spin" saprà in quale Sessione di Accesso è stato giocato.
- **Logica di Timeout (3 Minuti):**
  - Il frontend di Mines dovrà inviare un *heartbeat/ping* API (es. ogni 30 secondi) all'endpoint della `game_access_session`. Questo aggiornerà `last_activity_at`.
  - Un worker di background (o una logica passiva al prossimo ping) verificherà se `last_activity_at` è più vecchio di 3 minuti. Se sì, imposta la sessione su `timed_out` e il frontend disconnette l'utente forzandolo a uscire dal gioco.

### 2.3. L'Impatto sul Backoffice Admin
Avendo la struttura gerarchica sopra descritta, le richieste del PO per il backoffice diventano realizzabili nativamente:
- **View 1 (Gerarchica):** L'admin vedrà la lista delle `game_access_sessions` (es. "L'utente Rossi ha giocato a Mines dalle 10:00 alle 10:15"). Cliccando sulla sessione a fisarmonica, si espanderà la lista dei 45 "Spin" (round) effettuati in quel lasso di tempo.
- **View 2 (Piatta):** L'admin potrà vedere un elenco cronologico puro e semplice di tutti i singoli "Spin" (come è attualmente).

---

## 3. Piano di Esecuzione Parallelo
Per ottimizzare i tempi, i lavori verranno parallelizzati:
- **Stream Frontend (Quick Wins):** Il programmatore Code procederà immediatamente a sistemare le Tabs, i 2 decimali, i bottoni Login, e l'integrazione del cambio password nella UI.
- **Stream Backend (Architettura Sessioni):** In parallelo, verrà preparato il DDL (migration SQL) per introdurre la tabella `game_access_sessions`, che verrà poi collegato agli endpoint di avvio gioco.