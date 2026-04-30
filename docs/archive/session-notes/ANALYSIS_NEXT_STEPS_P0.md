# Architectural Analysis - Next Steps P0 (Apr 2026)

## Obiettivo
Eseguire gli ultimi 4 step definiti in `NEXT_STEPS_2026_04_02.md`, applicando metodo e rigore per completare la fase "P0" (Shell Player & Auth Cleanup) prima di procedere oltre. Questa analisi deve essere validata da `Ask` mode prima dell'implementazione `Code`.

---

## 1. Verifica Registration Flow (End-to-End)
### Problema Originario
Al termine dello Step 2 del wizard di registrazione, l'API `/auth/register` restituiva un Errore 500 (mascherato come "Failed to fetch") a causa dell'assenza delle colonne anagrafiche nel database post-riavvio.
### Architettura della Soluzione
L'implementazione richiederà semplicemente una verifica manuale (o simulata via script/browser) per confermare che l'utente venga effettivamente salvato e loggato, reindirizzando con successo verso `/account`. L'assenza di eccezioni convaliderà l'impermeabilità dell'ambiente locale appena riattivato.

---

## 2. P0.4: Account Dashboard ed Estratto Conto ("Home Banking")
### Stato Attuale
La pagina `/account` mostra dati grezzi e sparsi (Wallets, Sessions, Profilo).
### Proposta Architetturale (Componentizzazione UI)
1. **`PlayerProfileSummary`:** 
   - Una card di riepilogo visivo che estrae i dati (`first_name`, `last_name`, `fiscal_code`, `email`, `phone_number`) dallo stato del profilo appena scaricato da `/auth/me`.
2. **`PlayerCashier` (Cassa):**
   - Nuovo componente UI con due tab: **Versamento** e **Prelievo**.
   - Per l'MVP, l'azione di deposito sarà simulata (poiché l'endpoint di deposito diretto player non esiste, gli account nascono già con 1000 CHIP). La priorità è strutturare l'interfaccia utente (Input per importo + Metodo di pagamento "Finto" + CTA "Deposita").
3. **`PlayerAccountStatement` (Estratto Conto):**
   - Sostituire la lista di sessioni con una **Tabella HTML Rigorosa e Responsive**.
   - Colonne necessarie: `Data` (formato leggibile), `Gioco` (Hardcoded "Mines"), `Puntata` (bet_amount), `Esito` (Won/Lost/Active), `Vincita` (calcolata o restituita: Puntata * Moltiplicatore se Vinto).
   - Su mobile, la tabella dovrà collassare in un formato a "List Item" (Card per riga) per evitare lo scrolling orizzontale, garantendo una UX fluida.

---

## 3. P0.5: CMS Hero Banner (Lobby)
### Obiettivo
Preparare lo slot dove, in futuro, un CMS Headless (es. WordPress) inietterà le promozioni.
### Proposta Architetturale
- In `frontend/app/ui/player-lobby-page.tsx`, sostituiremo il generico testo "Lobby" con un componente `<CmsHeroBanner />`.
- **UI Design:** Un banner largo 100%, con un gradiente "premium" (es. Viola profondo/Oro), un titolo accattivante (es. "Welcome Bonus 100% - Fino a 500 CHIP") e un bottone "Reclama Ora" (che per ora punta a `/register` o `/deposit`).
- Il componente dovrà essere strutturato in modo che il testo e l'immagine siano passati via Props, preparandolo alla ricezione dati via `fetch()` dal futuro CMS.

---

## 4. P0.6: Hardening Mines Game Surface
### Obiettivo
Il Product Owner ha indicato che "se il gioco non lo tocchiamo non lo tocchiamo e deve funzionare". Il layout del sito è cambiato (Dark Mode + Top Header), quindi dobbiamo assicurarci che l'Iframe/Area del gioco Mines non si sia "rotta" (impermeabilità).
### Azione
- Testare visivamente la route `/mines` su viewport ristretto (iPhone Pro Max: larghezza max 430px).
- Assicurarci che la `.mines-board` sia centrata, che la griglia dei diamanti si ridimensioni correttamente senza debordare dallo schermo, e che i bottoni "Bet / Collect" siano a portata di pollice. Se ci sono conflitti ereditati dal nuovo `globals.css`, verranno sovrascritti selettivamente in `mines.css`.

---
**In attesa di validazione (ASK Mode) prima di procedere allo sviluppo Code.**