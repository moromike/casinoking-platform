# Next Steps - CasinoKing Platform

**Ultimo Aggiornamento:** 2 Aprile 2026 (Fine P0 - Shell Player & Auth Cleanup)

## Stato Attuale
Il frontend è stato smembrato dal monolite `casinoking-console.tsx` originale ed è stata creata un'architettura ibrida Mobile/Desktop con **Dark Mode Globale** attiva.
Le pagine Login e Registrazione presentano form ad alto contrasto. La registrazione è strutturata su due step (Dati e Upload Documento finto).
È stato identificato un bug ("Failed to fetch" in registrazione post-riavvio PC), documentato in `BUG_REGISTRATION_FAILED.md`.

## Priorità (To Do List per la prossima sessione)

### 1. Verifica Registration Flow (Sospeso)
- La risoluzione del bug "Failed to fetch" (applicando l'ultima migrazione DB) deve essere validata eseguendo una registrazione reale tramite browser. Questo è lo step bloccante primario della prossima giornata.
- Se fallisce ancora, aprire la console del browser e ispezionare l'error code esatto prima di modificare il codice.

### 2. P0.4: Account Dashboard ed Estratto Conto
- Navigando nella pagina dell'Account (`/account`), i dati sono visualizzati con formattazione basilare.
- **Task:** Riscrivere la pagina `player-account-page.tsx`.
- Strutturare l'Estratto Conto Giocate (Mines Sessions) in una tabella in stile "Home Banking" rigorosa: Data/Ora, Gioco (Mines), Importo Puntato, Vincita/Perdita, Saldo Finale.
- Strutturare la Cassa (Wallet) con due tab ben divisi "Versamento" e "Prelievo" simulati.
- Visualizzare chiaramente i Dati Anagrafici del giocatore (che ora includono First Name, Last Name, Fiscal Code, Phone).

### 3. P0.5: CMS Hero Banner
- Nella pagina della Lobby (`/`), aggiungere il placeholder per l'integrazione CMS futura (Hero Banner). Questo fungerà da slot per promozioni ("Welcome Bonus 100%") o notizie.

### 4. P0.6: Hardening Mines Game Surface
- Verificare la corretta impermeabilità visiva del gioco `Mines` all'interno della nuova shell Dark Mode.
- Accertarsi che il board layout rispetti i limiti di responsive design su iPhone Pro Max senza rotture del grid.