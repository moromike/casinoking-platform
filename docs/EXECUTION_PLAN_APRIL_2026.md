# Piano Esecutivo: Attività Aprile 2026

Questo documento traduce il backlog definito in `docs/NEXT_STEPS_2026_04_08.md` in task granulari, azionabili e ordinati per priorità e dipendenze. Rispetta rigorosamente i vincoli architetturali definiti in `docs/SOURCE_OF_TRUTH.md` e `docs/TASK_EXECUTION_GUARDRAILS.md`.

**Metodo di lavoro obbligatorio per ogni Epic:** Analisi -> Validazione (Ask) -> Implementazione (Code) -> Test Utente -> Rifinitura.

---

## Ordine di Esecuzione e Priorità Generale

1. **EPIC 1: Revisione e Pulizia Codice Generale** (Prerequisito fondamentale per la stabilità)
2. **EPIC 2: Identità e Profili (Player & Admin)** (Completamento logiche auth e ruoli)
3. **EPIC 3: Gestione Amministratori e Superadmin** (Dipende da Epic 2)
4. **EPIC 4: Ripensamento Totale Area Finanziaria** (Richiede validazione architetturale Ask)
5. **EPIC 5: Stabilizzazione Gioco Mines e Backoffice** (Core business game e configurazione)
6. **EPIC 6: Finalizzazione Sito Web Player** (Polishing finale basato su basi stabili)

---

# TODO List — EPIC 1: Revisione e Pulizia Codice Generale

## Contesto
Ripulire il debito tecnico accumulato nelle ultime sessioni (workaround, duplicazioni, stato fragile condiviso tra shell player, admin e Mines) per avere una base solida prima di introdurre nuove feature.

## Pre-condizioni
- Nessuna dipendenza esterna o epic bloccanti.
- Lettura di `docs/TASK_EXECUTION_GUARDRAILS.md` per evitare refactoring non richiesti.

## Task
### Task 1.1: Analisi e Disaccoppiamento Stato/Helper
- File: `frontend/app/lib/admin-storage.ts`, `frontend/app/lib/player-storage.ts`, `frontend/app/ui/casinoking-console.helpers.ts`
- Azione: Identificare helper, storage e side-effects duplicati o accoppiati male. Produrre un piano di refactoring strutturale pulito.
- Vincoli: Non modificare il backend. Non introdurre nuove feature UI o cambiare il design.
- Test: Verificare che login/logout di admin e player continuino a funzionare.
- Criterio di completamento: Documento di analisi e PR di refactoring completata senza regressioni sui flussi esistenti.

### Task 1.2: Pulizia Semantica e Residui
- File: Vari file in `frontend/app/ui/` e `frontend/app/(player)/`
- Azione: Rimuovere workaround locali, tipi `any` sparsi aggiunti di recente, e codice commentato inutile.
- Vincoli: Distinguere pulizia strutturale, semantica e UX, senza mischiare fix diversi nello stesso commit.
- Test: Esecuzione di `npm run lint` e compilazione type-safe senza errori.
- Criterio di completamento: Assenza di warning ESLint/TypeScript critici introdotti di recente.

## Ordine di esecuzione
- Eseguire Task 1.1 prima del Task 1.2 per separare la logica base dalla pulizia cosmetica/semantica.

## Rischi e attenzioni
- Regressioni nei flussi di auth e di gioco se si tocca lo storage. Testare SEMPRE incroci di sessione (player loggato in una tab, admin nell'altra).

---

# TODO List — EPIC 2: Identità e Profili (Player & Admin)

## Contesto
Definire e implementare chiaramente il cambio password per il player e creare la sezione "My Space" per l'admin con relativa gestione password.

## Pre-condizioni
- Completamento EPIC 1 per avere storage auth pulito.
- Modelli backend `User` e `Admin` in `backend/app/modules/users/` e `backend/app/modules/admin/`.

## Task
### Task 2.1: Endpoint Cambio Password (Backend)
- File: `backend/app/api/routes/auth.py` o nuove route dedicate in `users` / `admin`.
- Azione: Aggiungere endpoint per cambio password separati per player e admin (o uno unificato con RBAC rigido), richiedendo "old password" e "new password".
- Vincoli: Validazione hash sicura. Non invalidare altre sessioni attive senza previa validazione in Ask mode.
- Test: Test di validazione old password (sia corretto che errato).
- Criterio di completamento: Endpoint funzionante con test positivi e negativi.

### Task 2.2: UI Cambio Password Player
- File: `frontend/app/account/page.tsx`, `frontend/app/ui/player-account-page.tsx`
- Azione: Aggiungere form di cambio password. Gestire messaggi di successo/errore e loading state.
- Vincoli: Evitare contaminazioni con lo storage admin. Mantenere lo stile player coerente.
- Test: Eseguire cambio password via UI e verificare login immediato con nuova password.
- Criterio di completamento: Form funzionante e integrato visivamente nella shell account player.

### Task 2.3: UI Profilo Admin "My Space"
- File: `frontend/app/admin/page.tsx`, nuova componente `admin-my-space.tsx`
- Azione: Creare tab `My Space` nel backoffice. Mostrare info account (email) e form di cambio password.
- Vincoli: Nessuna commistione con la gestione giocatori. Totalmente separato.
- Test: Cambio password admin da UI e ri-autenticazione.
- Criterio di completamento: My Space operativo e non interferisce con le tab operative esistenti.

## Ordine di esecuzione
- Task 2.1 (Backend API) -> Task 2.2 (Frontend Player) -> Task 2.3 (Frontend Admin).

## Rischi e attenzioni
- Possibile desincronizzazione della sessione corrente. È necessario definire (tramite Ask) se forzare logout dopo il cambio password. Non creare confusione tra percorsi utente e admin.

---

# TODO List — EPIC 3: Gestione Amministratori e Superadmin

## Contesto
Introduzione dei ruoli (Admin e Superadmin) e gestione permessi per le macro-aree: Finance, End-User, Mines.

## Pre-condizioni
- Completamento EPIC 2 (per evitare conflitti nella gestione admin).
- Lettura schema database target `docs/word/CasinoKing_Documento_12_v3_Schema_Database_Definitivo.docx`.

## Task
### Task 3.1: Modello Dati e Migrations
- File: `backend/migrations/sql/` (nuovo file es. `0017__admin_roles_and_permissions.sql`), `backend/app/db/`
- Azione: Scrivere migration per espandere la tabella admin con `is_superadmin` (boolean) e un array `areas` (Finance, Gestione End-User, Mines). Aggiornare i Pydantic models.
- Vincoli: Rispettare approccio SQL puro. Nessun uso di ORM migration tools (es. Alembic non supportato per questo task).
- Test: Eseguire la migration senza causare perdite di dati sui record esistenti.
- Criterio di completamento: Schema DB aggiornato, bootstrap del primo superadmin funzionante.

### Task 3.2: Middleware e RBAC backend
- File: `backend/app/api/dependencies.py`
- Azione: Aggiornare il controllo permessi sulle route protette per verificare l'area richiesta contro l'array `areas` dell'admin. `is_superadmin=true` bypassa ogni controllo.
- Vincoli: Seguire la regola MVP: l'accesso a un'area dà permessi totali al suo interno, nessuna granularità ulteriore per ora.
- Test: Eseguire chiamate non autorizzate verificando la risposta `403 Forbidden`.
- Criterio di completamento: Route backend blindate in base ai permessi utente.

### Task 3.3: UI Gestione Admin (Solo Superadmin)
- File: Nuova componente `frontend/app/ui/admin/admin-management.tsx`
- Azione: Aggiungere sezione `Amministratori` nel Backoffice. Form creazione con campi: email, password iniziale impostata da superadmin, checkbox aree.
- Vincoli: Sezione nascosta se l'utente connesso non è superadmin. Menu dinamicamente generato in base alle `areas` possedute.
- Test: Creazione admin, login con admin ristretto, verifica visibilità menu.
- Criterio di completamento: UI funzionante per il governo delle utenze di backoffice.

## Ordine di esecuzione
- Task 3.1 (Migration/Models) -> Task 3.2 (RBAC Backend) -> Task 3.3 (UI Frontend).

## Rischi e attenzioni
- Gestione corretta della navigazione frontend: un admin base non deve poter forzare via URL l'apertura di un pannello che non gli compete.

---

# TODO List — EPIC 4: Ripensamento Totale Area Finanziaria

## Contesto
Sostituire il semplice elenco transazioni con una vera "Vista Banco": un report aggregato per sessioni di gioco.

## Pre-condizioni
- Documento `docs/word/CasinoKing_Documento_05_v3_Wallet_Ledger_Fondamenta_Definitive.docx`.
- L'Epic necessita profonda validazione architetturale tramite Ask prima del codice.

## Task
### Task 4.1: Analisi e Design API (Richiede Ask)
- File: `docs/FINANCIAL_AREA_DESIGN.md` (da creare)
- Azione: Progettare l'aggregazione dei dati ledger. Definire le API per Livello 1 (Lista Sessioni) e Livello 2 (Drill-down singola sessione).
- Vincoli: Nessuna scrittura codice backend/frontend in questa fase. Solo documento e validazione. Il delta deve avere segno opposto al player (ottica banco).
- Test: N/A.
- Criterio di completamento: Documento approvato dal PO (via Ask).

### Task 4.2: Implementazione Read-Model e API Backend
- File: `backend/app/modules/reporting/` o `backend/app/api/routes/ledger.py`
- Azione: Costruire le view/query SQL che raggruppano le entry del ledger in sessioni, fornendo ingressi, uscite e delta. Esporre i dati con filtri (giocatore, date, importi).
- Vincoli: Assoluto divieto di alterare la struttura base del ledger o i flussi double-entry attivi. Read-only.
- Test: Verifica quadratura calcoli su dataset dummy.
- Criterio di completamento: API funzionanti ed esposte per l'uso frontend.

### Task 4.3: UI Finanziaria - Vista Banco e Dettaglio
- File: Componenti in `frontend/app/admin/` e `frontend/app/ui/admin/`
- Azione: Creare la tabella sessioni (Livello 1) con relativi filtri. Sviluppare il drill-down (Livello 2) che mostri la storia testuale delle mani giocate.
- Vincoli: Progettare UX per operatore finance reale. Niente rendering grafico del gioco, solo log operativi.
- Test: Navigazione tra le viste. Filtraggio funzionante in UI.
- Criterio di completamento: Nuova area finance pronta all'uso, completamente slegata da vecchi accrocchi visivi.

## Ordine di esecuzione
- Task 4.1 (Design & Ask) -> Task 4.2 (API Backend) -> Task 4.3 (Frontend).

## Rischi e attenzioni
- Elevatissimo rischio di incomprensione del "delta banco". Una perdita per il player è un guadagno per il banco (+). Una vincita player è una spesa per il banco (-). Da incrociare attentamente con i conti ledger. **Area Sensibile**.

---

# TODO List — EPIC 5: Stabilizzazione Gioco Mines e Backoffice

## Contesto
Rendere l'esperienza in-game fluida e naturale e stabilizzare il flusso di pubblicazione nel backoffice, rimuovendo ambiguità.

## Pre-condizioni
- `docs/word/CasinoKing_Documento_06_Mines_Prodotto_Stati_Matematica_API.docx`.

## Task
### Task 5.1: Stabilizzazione Runtime (Player Game)
- File: `frontend/app/ui/mines/mines-standalone.tsx`, hook e API associate.
- Azione: Validare end-to-end riprese sessione, token non validi o timeout. Sostituire messaggi "tecnici" con testi naturali per l'utente.
- Vincoli: Non spostare alcuna logica (RNG, validazione stato) sul frontend. Server-authoritative sempre.
- Test: Interruzioni anomale, tab chiuse e refresh simulati manualmente.
- Criterio di completamento: Player non rimane mai bloccato a causa di edge case non gestiti a livello visivo.

### Task 5.2: Workflow Backoffice (Draft vs Live)
- File: `frontend/app/ui/mines/mines-backoffice-editor.tsx` e file annessi.
- Azione: Identificare chiaramente Bozza non salvata, Bozza salvata su DB e Configurazione Pubblicata. Aggiungere disabilitazione intelligente dei pulsanti.
- Vincoli: Non aggiungere feature non richieste. Rendere esplicito solo ciò che già c'è.
- Test: Flusso completo di editing configurazione verificando l'assenza di equivoci.
- Criterio di completamento: Nessuna confusione per l'operatore tra stato in canna e stato live.

## Ordine di esecuzione
- Task indipendenti, eseguibili in parallelo.

## Rischi e attenzioni
- Eventuali fix sulla validazione token non devono compromettere la sicurezza (le fairness rule di backend non devono essere rilassate).

---

# TODO List — EPIC 6: Finalizzazione Sito Web Player

## Contesto
Polishing visivo per rimuovere l'effetto "prototipo" e ottenere la percezione finale qualitativa (aspetto bello e coerente).

## Pre-condizioni
- EPIC 1, 2 e 5 completati, onde evitare di fare polishing su componenti destinati a scomparire o cambiare.

## Task
### Task 6.1: Gerarchia Visiva e Uniformità CSS
- File: `frontend/app/globals.css`, vari layout in `frontend/app/(player)/`
- Azione: Revisione spazi, contrasti, font, bordi e shadows per uniformare l'estetica.
- Vincoli: Solo modifiche estetiche. Vietato introdurre nuove funzionalità.
- Test: Verifica responsive incrociata Desktop/Tablet/Mobile.
- Criterio di completamento: Look and feel coerente ed elegante.

### Task 6.2: CTA e Loader State
- File: Tutte le form/pulsanti player.
- Azione: Standardizzare bottoni e l'handling dei caricamenti (API pending).
- Vincoli: Rispettare l'attuale DOM il più possibile.
- Test: Nessuno scatto fastidioso dell'UI durante fetch o post API.
- Criterio di completamento: Sensazione di un'app matura e reattiva.

## Ordine di esecuzione
- Dopo gli epic funzionali.

## Rischi e attenzioni
- Il CSS potrebbe rompere layout chiusi. Usare Tailwind in modo mirato e non generico sui tag base (se non in globals.css per typography e reset).
