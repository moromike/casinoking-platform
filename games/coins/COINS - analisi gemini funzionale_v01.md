# COINS - ANALISI GEMINI FUNZIONALE V01
*Documento definitivo di Analisi Funzionale, Visiva e Matematica*

> [!NOTE]
> **Source Directory Asset:** Tutto il materiale sorgente da cui è stata derivata questa analisi (DOCX, Video Gameplay e Screenshot Regole) risiede in:
> `C:\Users\michelem.INSIDE\Downloads\Personale\Projects-personal\casinoking-platform\assets\Games\coins\`

---

## 1. OVERVIEW E LOGICA CENTRALE
**Titolo del Gioco:** COINS
**Riferimento Originale:** Hacksaw Gaming (Serie Dare2Win)
**Tipologia:** Gioco a vincita istantanea / Coin Flip / Mine-like (senza esplosione)

**Meccanica di Base:**
COINS è un gioco di pura fortuna (game of chance) il cui obiettivo è far atterrare le monete dal lato "Testa" (Heads up). Prima di piazzare la puntata, il giocatore configura il gioco scegliendo il numero di monete (da 1 a 12). Più alto è il numero di monete selezionate, maggiore è il potenziale payout.
Piazzando la scommessa, tutte le monete vengono lanciate. **Se e solo se TUTTE le monete atterrano su Testa ("H")**, il giocatore vince il payout totale associato a quel numero di monete.

---

## 2. RIFERIMENTI VISIVI E UI/UX (GALLERIA)

Per supportare l'interpretazione visiva del flow, ecco gli screenshot originali che illustrano la disposizione degli elementi.

````carousel
![Schermata Principale e Griglia (9 Monete)](C:\Users\michelem.INSIDE\Downloads\Personale\Projects-personal\casinoking-platform\assets\Games\coins\COINS SCREEN01.png)
<!-- slide -->
![Interfaccia di Autoplay](C:\Users\michelem.INSIDE\Downloads\Personale\Projects-personal\casinoking-platform\assets\Games\coins\COINS SCREEN02.png)
<!-- slide -->
![Regolamento Ufficiale Pagina 1](C:\Users\michelem.INSIDE\Downloads\Personale\Projects-personal\casinoking-platform\assets\Games\coins\COINS RULES 1 of 2.png)
<!-- slide -->
![Regolamento Ufficiale Pagina 2](C:\Users\michelem.INSIDE\Downloads\Personale\Projects-personal\casinoking-platform\assets\Games\coins\COINS RULES 2 of 2.png)
````

---

## 3. ENGINE MATEMATICO, PROBABILITÀ E PAYOUT MATRIX
Il backend del gioco implementa in modo rigido la seguente logica matematica, governata dall'RTP del 98%.

### 3.1 Formule Matematiche di Base
Ogni moneta ha esattamente due stati equiprobabili (p = 0.5 per la testa, q = 0.5 per la croce). I lanci sono statisticamente indipendenti.
- **Probabilità di Vincita Pura (P_win):** P_win(N) = 1 / (2^N)
- **Rapporto di Odds Visualizzato:** Odds(N) = 1 : 2^N
- **Calcolo del Moltiplicatore di Vincita (M):** M(N) = 0.98 * 2^N

### 3.2 Matrice dei Valori (Mapping Tabellare)
| Numero Monete (N) | Odds Mostrate | Calcolo Matematico | Moltiplicatore Output (M) |
| :--- | :--- | :--- | :--- |
| 1 | 1:2 | 0.98 * 2 | 1.96x |
| 2 | 1:4 | 0.98 * 4 | 3.92x |
| 3 | 1:8 | 0.98 * 8 | 7.84x |
| 4 | 1:16 | 0.98 * 16 | 15.68x |
| 5 | 1:32 | 0.98 * 32 | 31.36x |
| 6 | 1:64 | 0.98 * 64 | 62.72x |
| 7 | 1:128 | 0.98 * 128 | 125.44x |
| 8 | 1:256 | 0.98 * 256 | 250.88x |
| 9 | 1:512 | 0.98 * 512 | 501.76x |
| 10 | 1:1024 | 0.98 * 1024 | 1003.52x |
| 11 | 1:2048 | 0.98 * 2048 | 2007.04x |
| 12 | 1:4096 | 0.98 * 4096 | 4014.08x |

### 3.3 Valutazione e Regolamento (Win/Loss Evaluation)
- **CONDIZIONE DI VINCITA (WIN):** Tutti gli elementi dell'array sono uguali a 1 (Tutte Teste, "H"). Il server accredita `Bet * Moltiplicatore` sul saldo del giocatore.
- **CONDIZIONE DI PERDITA (LOSS):** Almeno un elemento dell'array è uguale a 0 (Almeno una Croce, "X"). La puntata viene incamerata dalla piattaforma.
- **Aggiornamento UI:** Il saldo (Balance) viene aggiornato visivamente e il gioco torna allo stato Idle o procede al round successivo di Autoplay.

---

## 4. INTERFACCIA UTENTE (UI), RESPONSIVENESS E GRIGLIE DINAMICHE
L'interfaccia utente è strutturata in un layout a due aree macroscopiche, ottimizzato per aspect ratio standard (16:9, 16:10) e scalabile per dispositivi mobile.

### 4.1 Pannello dei Controlli (Pannello Sinistro)
- **Selettore Modalità (Tab Manual/Auto):** Pulsanti toggle adiacenti. Lo stato attivo è verde brillante (`#4ade80`), inattivo grigio scuro.
- **Griglia di Selezione Monete:** Matrice di bottoni da 1 a 12. Il bottone selezionato si colora di verde.
- **Visualizzatore Saldo e Vincita (Footer):** Mostra `BALANCE` e `WIN`.
- **Selettore Valore Bet:** Campo centrale con frecce (da €0.20 a €200.00).
- **Pulsante di Azione:** Testo "BET" o "START AUTOPLAY" (diventa rosso/STOP durante l'uso).

### 4.2 Area di Visualizzazione Centrale (Il Campo di Gioco)
- **Sfondo:** Blu-notte scuro per esaltare i contrasti neon.
- **Header Informativo:**
  - **Badge Sinistro (Odds):** Sfondo scuro, testo verde (es. `1:8`).
  - **Badge Destro (Payout):** Sfondo scuro, testo verde (es. `7.84x`).

### 4.3 Geometria delle Monete
Il motore grafico instanzia e posiziona le monete in modo centrato assoluto:
- **N = 1:** Centro esatto.
- **N = 2, 3:** Una riga orizzontale.
- **N = 4:** Griglia 2x2.
- **N = 6:** Griglia 3x2.
- **N = 9:** Griglia 3x3 (vedi screenshot).
- **N = 12:** Griglia 4x3.

---

## 5. ANIMAZIONI, TIMINGS E FLUSSO VISIVO (TEAR-DOWN)

### 5.1 Stati Visivi delle Monete
- **Stato Neutro / Idle:** Colore viola scuro/indaco. Faccia iniziale opaca con una debole 'X'.
- **Stato Spin (Rotazione):** Rotazione rapida (asse Y) con motion blur direzionale e leggero popup 3D. Durata: 1-1.5 secondi.
- **Stato Risoluzione TESTA ("H"):** Colore ciano neon (`#00f0ff`) con lettera "H".
- **Stato Risoluzione CROCE ("X"):** Colore viola desaturato o grigio con "X" opaca. Sconfitta.

### 5.2 Timeline di Risoluzione Asincrona
L'atterraggio è **asincrono**:
`Landing_Time = Base_Time (es. 800ms) + (Index_Moneta * Random(30ms, 70ms))`

---

## 6. SISTEMA DI AUTOPLAY AVANZATO
L'Autoplay è deterministico. La UI (vedi screenshot 2) presenta:
- **Number of Rounds:** Pillole `[10, 25, 50, 75, 100, 500, 1000]`.
- **Loss Limit:** `[5X BET, 20X BET, 50X BET, NO LIMIT, CUSTOM]`.
- **Single Win Limit:** `[10X BET, 20X BET, 75X BET, NO LIMIT, CUSTOM]`.

Durante l'Autoplay i campi bet e configurazione sono disabilitati.

---

## 7. RETE E API
**Esempio Request (Client):**
```json
{  "action": "bet",  "game_id": "coins_hacksaw",  "bet_amount": 2.00,  "selected_coins": 9,  "mode": "manual",   "timestamp": 1779659227000}
```

**Esempio Response (Server):**
```json
{  "status": "success",  "tx_id": "TX-12345",  "balance_after_bet": 4979.68,  "result": {    "is_win": false,    "multiplier": 0.0,    "payout_amount": 0.0,    "coin_matrix": [1, 1, 1, 1, 0, 1, 1, 1, 1]   }}
```

### 7.1 Keybinds ed Errori
- `SPACE / ENTER`: Bet.
- **Clausola Malfunzionamento:** Voids all pays and plays. (Rimborso della puntata).
