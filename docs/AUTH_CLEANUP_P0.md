# Auth Cleanup (P0) - Login & Registrazione

Questo documento definisce il "design & flow" per la pulizia delle interfacce di Login e Registrazione (Player), rimuovendo l'aspetto da "console di debug" e implementando un vero flusso utente B2C.

## 1. Registrazione Player (`PlayerRegisterPage`)

Attualmente il wizard è diviso in "Dati Anagrafici" e "Email/Password". L'utente ha richiesto una struttura diversa, più aderente a un vero processo KYC.

### Nuovo Flusso Wizard
L'interfaccia deve guidare l'utente attraverso due macro-step logici:

#### Step 1: Dati Personali e Contatti
- **Campi Raggruppati:**
  - `Nome`, `Cognome`, `Codice Fiscale`, `Telefono`, `Email`, `Password` (tutti nello stesso step iniziale per non interrompere il flow).
- **Simulazione OTP Email:**
  - Accanto o sotto al campo Email, un bottone finto (mock) "Invia codice OTP".
  - Un campo aggiuntivo "Inserisci codice OTP".
  - *Comportamento Mock:* Per ora il sistema accetterà qualsiasi codice senza reale validazione lato backend, ma l'UI darà un feedback visivo positivo (es. spunta verde) per simulare l'esperienza finale.

#### Step 2: Upload Documento Identità (Soft-KYC)
- **Interfaccia:**
  - Un'area dedicata per l'upload di due file: **Fronte Documento** e **Retro Documento**.
  - Testo informativo (es. "Carica un documento d'identità valido per sbloccare i prelievi. Tipi accettati: Carta d'Identità, Passaporto, Patente.").
- **Comportamento Mock:** 
  - Il frontend userà tag `<input type="file" />` per permettere la selezione dei file dal dispositivo.
  - Al click su "Completa Registrazione", il frontend effettuerà la chiamata API `/auth/register` (inviando i dati dello Step 1), **ignorando temporaneamente l'invio dei file** (visto che il backend attuale non li supporta ancora). Mostrerà comunque un messaggio di successo all'utente ("Documenti acquisiti, in attesa di validazione").

#### Azione di Successo
- Alla corretta esecuzione della chiamata API di registrazione, il frontend eseguirà **automaticamente il Login** sotto il cofano, salverà il token, e reindirizzerà (redirect via router) l'utente direttamente alla Lobby `/` (o `/account`).

## 2. Login Player (`PlayerLoginPage`)

L'attuale pagina di login è grezza e mostra sempre in vista il form di reset password.

### Nuovo Flusso Login
- **Pulizia Layout e Copy:**
  - Rimozione testi tecnici ("Dedicated player login flow outside the legacy monolith").
  - Intestazione accogliente: "Bentornato su CasinoKing".
- **Azione di Successo:**
  - Invece di mostrare "Sign in completed", al successo della chiamata API l'utente verrà **automaticamente reindirizzato** alla Lobby `/` per poter iniziare subito a giocare.

### Nuovo Flusso Reset Password
- **Nascondere il Form:** 
  - Il blocco "Password reset" non deve essere visibile di default. 
  - Aggiungere un link discreto sotto il campo password: *"Hai dimenticato la password?"*.
  - Cliccando il link, il form di login scompare (o si espande un modale/pannello) per mostrare l'interfaccia di inserimento email e richiesta OTP di reset. Questo pulisce drasticamente la visuale primaria.

## 3. Review Tecnico (Next.js)
- Per le redirezioni si userà il modulo `next/navigation` (`useRouter().push('/')`).
- Il CSS utilizzerà le classi esistenti (`.panel`, `.stack`, `.field-grid`, `.button`) ma con spaziature migliorate per centrare i form nello schermo, imitando una vera schermata di autenticazione di un'app.