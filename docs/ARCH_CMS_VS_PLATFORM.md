# Architettura: Confine tra CMS Esterno (es. WordPress) e Piattaforma Core CasinoKing

## 1. La Sfida Architetturale
Il Product Owner ha indicato che, in futuro, la gestione dei contenuti (testi, banner, landing page) sarà affidata a un CMS di mercato (come WordPress o Strapi) per evitare di sviluppare un CMS proprietario da zero.

Questo richiede la definizione di un confine netto (Separation of Concerns) tra ciò che è puro "Contenuto Editoriale" e ciò che è "Transazione Finanziaria e di Gioco" (regolamentata e sicura).

## 2. Il Ragionamento: L'approccio "Headless"
La soluzione migliore (e standard nell'industria dell'iGaming) è usare un'architettura **Headless CMS**.
Il nostro frontend attuale in React/Next.js (CasinoKing Platform) rimarrà l'unica interfaccia visibile all'utente. Quando l'utente naviga la home page, Next.js chiederà via API a WordPress: *"Dammi le immagini dei banner promozionali di oggi e i testi del footer"*.

In questo modo, WordPress non gestisce mai sessioni utente, database o soldi, ma funge solo da "magazzino di immagini e testi".

## 3. Cosa MUST essere gestito dalla Piattaforma Core CasinoKing?
Tutte le logiche che coinvolgono il portafoglio dell'utente, l'identità legale e il gameplay **non devono mai toccare il CMS**. Appartengono alla nostra piattaforma:

1. **Autenticazione e Sicurezza (Auth):**
   - Gestione delle Password, Token JWT, Login, Recupero Password, 2FA (se prevista).
   - *Motivazione:* Il database utenti non deve mai vivere in un CMS attaccabile come WordPress per ragioni di sicurezza e compliance.

2. **Registrazione Wizard e KYC (Soft-KYC):**
   - L'acquisizione dei Dati Anagrafici (Nome, Cognome, CF).
   - Validazione OTP via Email/SMS.
   - Upload Sicuro del Documento d'Identità (Fronte/Retro).
   - *Motivazione:* Dati sensibili PII (Personally Identifiable Information) soggetti a GDPR e norme antiriciclaggio (AML).

3. **L'Account Giocatore (Area Riservata):**
   - Modifica dei limiti di Gioco Responsabile (se previsti).
   - Pagina Riepilogo Profilo.

4. **Il Core Finanziario (Cassa ed Estratto Conto):**
   - Il Wallet (Saldo Reale vs Saldo Bonus).
   - Interfacce e flussi di Deposito e Prelievo.
   - L'Estratto Conto: lo storico delle sessioni, le scommesse, i calcoli delle vincite e i log del Provably Fair.
   - *Motivazione:* È il cuore del Ledger double-entry, non esportabile.

5. **Motore dei Bonus (Bonus Engine):**
   - La logica (calcolo requisiti di puntata, sblocco bonus) risiede nel Core.
   - *Nota:* Il CMS può ospitare la "pagina pubblicitaria" del bonus ("Iscriviti e ricevi 100€"), ma il calcolo matematico lo fa la Piattaforma.

6. **L'Esecuzione del Gioco (Game Surface):**
   - Il caricamento di Mines (e dei futuri 50 giochi) tramite Iframe o container nativo, gestione del Game Launch Token e le API di puntata/risultato.

## 4. Cosa delegare al Futuro CMS (WordPress/Strapi)?
- **Homepage "Vetrina":** Banner Hero, promozioni in corso, landing page SEO.
- **Pagine Informative Statiche:** Chi Siamo, Termini e Condizioni, Privacy Policy, Regolamento dei Giochi.
- **Supporto & FAQ:** Articoli di aiuto o documentazione per l'utente.
- **Icone e Dati base dei Giochi:** Il CMS potrebbe fornire al Frontend l'immagine (thumbnail) di "Mines" e il suo titolo promozionale, ma il link "Gioca" punterà al Game Engine della Piattaforma.

## 5. Proposta Concreta per l'Sviluppo Attuale (Fase P0)
Per non bloccarci oggi in attesa del CMS, la nostra **Lobby (Step 1)** avrà i testi e i banner hardcoded (statici) dentro i componenti Next.js. 

Tuttavia, progetteremo i componenti React in modo che in futuro, invece di leggere un testo statico, basterà fargli fare una chiamata API (`fetch('wordpress.casinoking.com/wp-json/...')`) per caricare dinamicamente i contenuti marketing, lasciando la parte **Auth/Account/Mines** totalmente isolata e sicura nel nostro backend.