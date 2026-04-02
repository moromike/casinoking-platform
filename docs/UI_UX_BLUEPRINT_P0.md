# CasinoKing - UI/UX Architectural Blueprint (Phase P0)

## Visione Generale
Questo documento definisce l'architettura frontend e il piano di sviluppo per la fase P0 (Shell Player, Lobby, Auth, Account). Le scelte strategiche sono state approvate dal Product Owner e uniscono il meglio dei moderni *Crypto-Casino* con l'affidabilità strutturale dei portali regolamentati italiani.

---

## Step 1: Visual System & Architettura della Shell
**Direzione Scelta:** Ibrido (Mobile-First + Stile Stake/Dark Mode).

- **Desktop (Stile "Opzione B"):**
  - Tema **Dark Mode** nativo: sfondi profondi (blu notte o nero) con testi chiari ad alto contrasto.
  - Navigazione tramite **Sidebar laterale sinistra** a scomparsa (per le categorie: Slot, Live, Originali).
  - Header superiore minimalista, con focus immediato sul saldo (Cassa) e accesso al profilo in alto a destra.
- **Mobile (Stile "Opzione C"):**
  - Esperienza "App-like": la sidebar scompare, sostituita da una **Bottom Navigation Bar** fissa in basso (Es: `[Lobby] [Cerca] [Cassa] [Menu]`), per garantire manovrabilità con una sola mano.
- **Colori e Tipografia:** Accenti di colore "neon" o vivaci (es. verde brillante per bottoni di deposito o "Gioca") su sfondo scuro per far risaltare le Call-to-Action. Numeri dei saldi in font monospace/sans-serif altamente leggibili.

---

## Step 2: La Lobby e la Vetrina Giochi
**Direzione Scelta:** Vetrina Scalabile (Predisposta per 50+ giochi).

- **Layout:** La Home Page sarà una griglia fluida di "Card" o Icone Gioco (stile sezione Slot di Admiral).
- **Il Gioco Mines:** Avrà la sua icona ad alta qualità (thumbnail) posizionata in evidenza. Cliccando l'icona si entra nella route `/mines`.
- **Scalabilità e Riempimento:** Visto l'obiettivo di collegare 50 giochi in futuro, la griglia verrà strutturata fin da subito per supportarli. Per non lasciare la pagina vuota, inseriremo temporaneamente delle *Card Placeholder/Fake* ("Coming Soon" o giochi dummy disabilitati) per dare subito l'impatto di un vero portale multi-gioco.

---

## Step 3: Registration Wizard (Onboarding)
**Direzione Scelta:** Wizard progressivo e Soft-KYC.

Per massimizzare il tasso di conversione (evitando un unico form gigante stile ministero), la registrazione sarà un wizard in 2/3 passaggi fluidi:

- **Fase 3.1 - Dati Anagrafici & Contatti:** 
  - Campi: Nome, Cognome, Codice Fiscale, Telefono, Email.
- **Fase 3.1.b - Verifica OTP (Mock):** 
  - Schermata di inserimento del codice numerico inviato via Email.
  - *Architettura MVP:* L'OTP sarà simulato (accetterà qualsiasi codice o un hardcoded es. "0000"). L'interfaccia UI sarà però definitiva e pronta per essere attaccata al servizio reale in futuro.
- **Fase 3.2 - Upload Documento d'Identità (KYC):** 
  - Interfaccia per caricamento Fronte + Retro.
  - *Architettura MVP:* Non ci saranno controlli OCR/Backend di validità sul file. Qualsiasi immagine caricata verrà accettata e lo stato utente passerà a "In attesa di validazione" (permettendo comunque di giocare, come nel "Soft-KYC" normativo che dà 30 giorni per la verifica).

---

## Step 4: Player Account & Dashboard
**Direzione Scelta:** Trasparenza bancaria ed empowerment dell'utente.

La sezione `/account` diventerà il vero cruscotto del giocatore, diviso in sottomenu logici:
1. **Riepilogo Profilo:** Una vista di sola lettura che riassume i dati anagrafici e i contatti forniti in fase di registrazione.
2. **Cassa (Wallet):** Interfaccia chiara per simulare Versamenti (Deposit) e Prelievi (Withdrawal), con visualizzazione netta tra *Saldo Reale* e *Saldo Bonus*.
3. **Estratto Conto (Storico Sessioni):** Una tabella rigorosa e inattaccabile. 
   - Colonne: Data/Ora, Gioco, ID Sessione, Importo Puntato, Vincita/Perdita, Saldo Finale.
   - Ogni riga sarà cliccabile per aprire il "dettaglio della partita" (utile per mostrare trasparenza e l'hash *Provably Fair* di Mines).

---
*Fine del Blueprint. In attesa di validazione dal CTO/Reviewer.*