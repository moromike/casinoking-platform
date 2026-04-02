# UI/UX Action Plan - Phase P0 (Player Experience)

## 1. Metodologia: Come ci approcciamo al Design?
Hai perfettamente ragione: il modo migliore di procedere è **step by step**, analizzando le best practice di mercato e prendendo decisioni mirate. Non inventiamo la ruota, ma la ottimizziamo per il nostro target.

Il mio approccio di "studio" si basa su due grandi mondi che uniremo per CasinoKing:

1. **Il mondo Regolamentato Italiano (Sisal, AdmiralBet, Betflag, Lottomatica):**
   - **Cosa prendiamo da loro:** La solidità formale. L'estratto conto giocatore chiarissimo, i limiti di gioco responsabile, i form di registrazione conformi alle normative (es. KYC, SPID), e la netta separazione tra cassa (wallet) e gioco.
2. **Il mondo Internazionale/Moderno (Stake.com, Roobet, Rollbit):**
   - **Cosa prendiamo da loro:** La velocità, l'interfaccia "Dark Mode" elegante, l'usabilità mobile-first fluida (senza troppi ricaricamenti di pagina) e il modo in cui presentano i loro "Original Games" (proprio come il nostro Mines).

---

## 2. Il Piano di Azione (La Roadmap per Step)

Questo è l'ordine cronologico con cui trasformeremo il frontend. Lavoreremo su un pezzo alla volta: io ti faccio le proposte, tu scegli, io implemento.

### Step 1: Il Visual System e la Lobby (Siamo Qui)
Prima di fare registrazione o estratto conto, dobbiamo definire la "casa" del giocatore: colori, font, header, e la home page (Lobby) dove ci sarà la card di "Mines".

**Opzioni di Design per la Shell (Scegli tu la direzione):**
- **Opzione A - "Classic Italy" (Stile Admiral/Sisal):** Tema chiaro/luminoso (sfondo bianco o grigio chiarissimo), grande menu orizzontale in alto con le categorie di gioco (Casino, Slot, Live, Originali). Rassicurante, tradizionale, ottimo per un pubblico adulto.
- **Opzione B - "Modern Crypto" (Stile Stake.com):** Tema Scuro (Dark Mode nativa) molto elegante, barra di navigazione laterale a scomparsa sulla sinistra (sidebar), header minimal con il saldo sempre visibile in alto a destra. Giovanile, veloce, tech-oriented.
- **Opzione C - "Mobile-First App":** Un ibrido dove su mobile c'è una "Bottom Navigation Bar" (come l'app di Instagram) con [Home], [Cassa], [Account], e su desktop un layout molto pulito e centrato.

### Step 2: Integrazione di Mines nella nuova Shell
Una volta scelta la veste grafica dello Step 1, rifiniremo il layout di `/mines` affinché si incastri perfettamente nella nuova grafica, senza sembrare un componente isolato.

### Step 3: Autenticazione (Login & Registrazione)
Passeremo poi all'ingresso del portale.
- **Proposte che valuteremo:** Un form "wizard" a più step (per non spaventare l'utente con 20 campi tutti insieme), e l'eventuale integrazione visiva di bottoni per login rapidi o SPID (se previsto).

### Step 4: Account Giocatore ed Estratto Conto (Il Backoffice del Player)
Creeremo un'area riservata (Dashboard) che includerà:
- Saldo disponibile (Cash vs Bonus).
- **Estratto Conto:** Una tabella chiara in stile bancario (Betflag/Sisal docet) che mostra: Data, Gioco (Mines), Importo Puntato, Vincita, e Saldo Finale.
- Funzioni di Cassa (Versamento simulato, Prelievo).

---

## 3. Come procediamo adesso?
Per il nostro **Step 1 (Lobby e Shell)**, dimmi quale delle tre opzioni grafiche (A, B, o C) si avvicina di più all'idea di business che hai in mente per CasinoKing. 

Appena mi dai la direzione (es. "Voglio lo stile Modern Crypto"), io passo subito in modalità **Code** e inizio a costruire l'header, i bottoni e i colori della nuova casa di CasinoKing!