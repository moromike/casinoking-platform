# Piano di Stabilizzazione Runtime Mines (EPIC 5)

## Contesto e Obiettivo
Questo piano declina i task previsti dall'**EPIC 5: Stabilizzazione Gioco Mines e Backoffice**. L'obiettivo è duplice:
1. **Frontend Player (Task 5.1)**: Rendere l'esperienza in-game solida, gestendo graceful degradation in caso di errori di rete, riprese di sessione (refresh pagina), token scaduti o timeout, e sostituendo i messaggi di errore tecnici delle API con testi comprensibili all'utente finale.
2. **Backoffice Admin (Task 5.2)**: Chiarire il workflow di pubblicazione nel pannello di amministrazione (Draft vs Live). Attualmente, l'operatore rischia di confondersi su cosa è salvato in bozza, cosa non è ancora salvato, e cosa è effettivamente live. Vanno introdotti indicatori visivi chiari e regole logiche per disabilitare bottoni (es. impedire il salvataggio se non ci sono modifiche, o impedire la pubblicazione se non c'è una bozza salvata).

## Documenti di Riferimento
- `docs/EXECUTION_PLAN_APRIL_2026.md` (Epic 5)
- `docs/word/CasinoKing_Documento_06_Mines_Prodotto_Stati_Matematica_API.docx`
- `docs/TASK_EXECUTION_GUARDRAILS.md`

---

## Stato Attuale vs Target

### 1. Player Game (Mines Standalone)
| Area | Stato Attuale | Stato Target |
| :--- | :--- | :--- |
| **Messaggi d'errore API** | Mostrati "as-is" in UI (es. "Reveal failed", "GAME_STATE_CONFLICT"). | Intercettati e tradotti in messaggi user-friendly. |
| **Ripresa Sessione** | In caso di refresh, se la sessione è attiva viene ricaricata tramite `X-Game-Launch-Token`. | Validare visivamente la transizione per l'utente, impedendo azioni zombie durante il ricaricamento e ripristinando correttamente lo stato dei bottoni (Bet vs Collect). |
| **Timeout Access Session** | Segnalato con errori generici quando scade il countdown. | Messaggi espliciti in UI (es. "Sessione inattiva scaduta, ricarica la pagina"). |

### 2. Workflow Backoffice (Draft vs Live)
| Area | Stato Attuale | Stato Target |
| :--- | :--- | :--- |
| **Stati (Unsaved / Saved / Live)** | Solo pillole generiche "Bozza diversa dal live". | Tre stati espliciti: 1) Modifiche non salvate, 2) Bozza salvata, 3) Bozza pubblicata (Live allineato). |
| **Pulsanti d'azione** | Spesso abilitati anche se non necessari. | Disabilitazione intelligente: "Salva bozza" attivo solo se ci sono *modifiche locali non salvate*. "Pubblica" attivo solo se la *bozza salvata differisce dal live*. |

---

## TODO List per il modo Code

### Task 5.1: Stabilizzazione Runtime (Player Game)
- **File**: `frontend/app/ui/mines/mines-standalone.tsx`, `frontend/app/lib/api.ts` (se necessario per mappare errori).
- **Azione**:
  1. Individuare tutti i blocchi `catch (error)` e le chiamate a `setStatus({ kind: "error" })`.
  2. Sostituire i messaggi tecnici in inglese o i codici di errore API nudi con testi amichevoli (es. invece di "Round launch failed" -> "Impossibile avviare la mano. Verifica la connessione e riprova.", invece di "Reveal failed" -> "Errore di comunicazione col server, la tua giocata è sicura. Riprova tra poco.").
  3. Gestire lo stato zombie: assicurarsi che durante il fetch iniziale (`loadSession` / `refreshAuthenticatedState`) l'UI mostri uno spinner o blocchi gli input per evitare che l'utente clicchi prima che lo stato sia allineato al backend.
  4. Per errori fatali come `GAME_STATE_CONFLICT` o token scaduto esplicitamente, forzare una dialog o un messaggio permanente che invita al refresh, bloccando la board.
- **Vincoli**: 
  - Non spostare validazioni (RNG, importi, mine_count) lato client. Server-authoritative sempre.
  - Non alterare i payload delle API. Modificare solo la gestione in UI dell'errore.
- **Test**: 
  - Avviare il server, lanciare una partita, spegnere il server e cliccare una mina (deve mostrare un errore pulito senza bloccarsi irrimediabilmente).
  - Refresh della pagina con partita in `active` state.
- **Criterio di completamento**: Qualunque fallimento di rete restituisce feedback comprensibili e il giocatore non rimane bloccato in caricamenti infiniti o stati corrotti.

### Task 5.2: Workflow Backoffice (Draft vs Live)
- **File**: `frontend/app/ui/mines/mines-backoffice-editor.tsx`
- **Azione**:
  1. Aggiungere uno stato locale `has_local_unsaved_changes` che diventa `true` ogni volta che si invoca `updateAdminMinesBackofficeDraft`.
  2. Dopo un `handleSaveAdminMinesBackofficeConfig` (Salvataggio in bozza) andato a buon fine, resettare `has_local_unsaved_changes` a `false`.
  3. Modificare l'abilitazione del pulsante **"Salva bozza"**: disabilitarlo se `!has_local_unsaved_changes`.
  4. Modificare l'abilitazione del pulsante **"Pubblica live"**: deve essere attivo **solo** se `has_local_unsaved_changes` è `false` (obbligo di salvare prima di pubblicare) **E** `adminMinesBackofficeState?.has_unpublished_changes` è `true` (la bozza salvata su DB è diversa dal live).
  5. Aggiungere un piccolo testo/badget esplicito in alto: "Stato Editor: [Modifiche non salvate | Bozza pronta | Pubblicato]".
- **Vincoli**: Non alterare i modelli o la logica di backend, lavorare esclusivamente sullo stato React e sulle label.
- **Test**:
  - Aprire la tab -> Cambiare un testo HTML -> Controllare che solo "Salva bozza" sia attivo.
  - Salvare -> Controllare che si attivi "Pubblica live" e si disabiliti "Salva bozza".
  - Pubblicare -> Controllare che entrambi i pulsanti siano disabilitati fino alla prossima modifica locale.
- **Criterio di completamento**: Flusso a prova di errore, l'operatore è guidato obbligatoriamente da Modifica -> Salva -> Pubblica senza ambiguità.

## Ordine di esecuzione
I task 5.1 e 5.2 operano su aree (Frontend Player e Frontend Admin) totalmente isolate. Possono essere eseguiti in qualsiasi ordine. Si consiglia:
1. Task 5.2 (Backoffice), in quanto molto specifico e veloce.
2. Task 5.1 (Player Game), che richiede simulazione di fallimenti di rete.

## Rischi e attenzioni
- Nel Task 5.1, attenzione a non nascondere eccezioni gravi (es. token scaduto irreversibile). I testi "naturali" non devono mentire all'utente sulla gravità dell'errore se è richiesta una nuova login.
- Nel Task 5.2, l'editor Backoffice ricarica i dati anche tramite "Carica da bozza" / "Carica da produzione". Quando si premono questi pulsanti, bisogna ricordarsi di resettare `has_local_unsaved_changes` a `false`.
