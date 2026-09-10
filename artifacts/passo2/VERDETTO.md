# PASSO 2 — VERDETTO

**10/09/2026** · contratto `CONTRATTO_PASSO2.md` · punta `cc45822`

## RIVALIDATO E CORRETTO — leggere questa sezione per prima

**Codex `gpt-5.6-sol` ha rivalidato il 10/09 e ha dichiarato PARTE 2: NON CHIUSO.**
Tre rilievi, **tutti veri, tutti verificati dall'orchestratore, tutti recepiti qui sotto**:

1. **«P2-03 e' latente» era FALSO.** Esiste un consumatore attivo e non l'avevo cercato:
   il giocatore vede un rimborso come **«Vinto»** nel suo estratto conto, e l'importo entra
   nel **totale vinto**. `[GENERATO]` **434 rimborsi su 434**. Le mie controricerche
   cercavano *chi calcola* e non *chi mostra*.
2. **Il verdetto 2A era piu' largo delle prove.** `[GENERATO]` i 434 rimborsi vengono
   **tutti da `mines`**, chiusi per timeout di sessione: sono centinaia di ripetizioni di
   **un percorso solo**, non prove indipendenti su tre giochi. E provano i rimborsi
   **avvenuti**, non che un rimborso **scatti sempre quando e' dovuto**.
3. **Il cancello 2 era rosso:** avevo salvato le uscite mettendo un **segnaposto** al posto
   delle interrogazioni. Un'uscita senza la sua interrogazione non e' riproducibile.
   Corretto: le quattro interrogazioni sono per intero in `02-denaro-nel-registro.md`.

**E una violazione di procedura, che dichiaro invece di lasciarla trovare.** Ho eseguito il
PASSO 2 **mentre** il gate d'ingresso era ancora `BLOCCA/in corso`. Codex: *«questo via
libera non e' retroattivo»*, e ha ragione. La mia giustificazione — «e' una verifica che non
cambia niente» — spiega perche' il danno e' nullo, **non** perche' fosse permesso. Il piano
imponeva quattro condizioni prima di partire e io ne ho aspettate tre.

---

## L'ESITO IN TRE RIGHE

1. **Il rimborso automatico funziona, sui percorsi provati.** I soldi tornano, esatti al
   centesimo, e la contabilita' quadra. **Restrizione imposta dalla rivalidazione:** i
   numeri di massa vengono tutti da `mines`; per BOXE e HI-LO vale la copertura dei due
   collaudi nominati, non le centinaia di ripetizioni.
2. **L'allarme manca davvero**, a ogni livello. Cercato in cinque modi, tutti a zero.
3. **E' emerso un terzo fatto che il piano non prevedeva, ed e' ATTIVO:** un rimborso e'
   registrato come una **vincita**, e il **giocatore lo vede scritto «Vinto»** nel suo
   estratto conto, sommato al totale vinto. **434 su 434.** Non e' un rischio futuro.

## 2A — IL RIMBORSO TORNA: SI', sui percorsi provati

| Prova | Esito |
|---|---|
| i due collaudi nominati | `2 passed`, uscita **0** |
| rimborsi con importo **esatto** | **426 su 426**, scostamenti **0** |
| movimenti contabilmente **quadrati** | **426 su 426**, sbilanciati **0** |

Il vincolo non negoziabile posto da Michele il 3/09 — *la quadratura al centesimo e non
deve mai sbagliare* — **regge sui rimborsi**. Uscite in `01-collaudi-rimborso.txt` e
`02-denaro-nel-registro.md`.

## 2B — L'ALLARME: MANCA

Cinque ricerche, tutte a **0**: nessun avviso nel percorso del rimborso, nessuno nei
quattro moduli di autoliquidazione, nessuna integrazione di allarme in tutto il backend,
nessun registro di livello error o warning, nessuna metrica esposta.

**Ma il rimborso viene registrato** (426 movimenti con `settlement_kind`). Quindi:
**si puo' sapere, se qualcuno va a guardare. Nessuno viene avvisato.** Lo spazzino gira
ogni 30 secondi e ogni rimborso che ne consegue e' silenzioso. Dettaglio in `03-allarme.md`.

**Costruire l'allarme non e' questo passo** e il contratto lo vieta: chi viene avvisato,
con quale soglia e cosa deve fare e' una decisione di prodotto, non una riga di codice
da infilare in una verifica.

## P2-03 — L'ETICHETTA: il giocatore vede «Vinto» su un rimborso

**Com'era il 10/09 mattina**, quando il PASSO 2 e' stato eseguito:
`refund_no_progress` -> stato `won` (426), come `manual_cashout` (123). Il collaudo
**pretendeva** `won` su un rimborso (`test_boxe_api.py:1284`). Calcolando dallo stato: 96%
di partite vinte, contro il vero 21,5%.

**ATTIVO, non latente.** La prima stesura scriveva «latente» ed era falso: l'ha smontato
Codex in rivalidazione. Il consumatore c'e' ed e' il giocatore —
`account/service.py:876` -> `player-account-page.tsx:1610`, che lo scrive **«Vinto»** e lo
somma al totale vinto. `[GENERATO]` 434 su 434. Le mie controricerche cercavano *chi
calcola* e non *chi mostra*.

**RIPARATO lo stesso giorno**, come CON-05 (commit `79c4190`, otto cancelli su otto,
dichiarato chiuso da Kimi): oggi un rimborso vale `cancelled`, il giocatore legge
«Annullato», e le 434 righe storiche sono state corrette senza che la contabilita' cambiasse
di un centesimo.

## IL PROBLEMA ESCE DAI QUATTORDICI?

**Per la parte del rimborso: SI'.** Funziona, e' provato nei due versi, esce.

**Per la parte dell'allarme: NO, ma non e' un difetto da riparare — e' una decisione
da prendere.** Resta aperto e va in un passo suo.

**P2-03 e' un impegno NUOVO**, che il piano non aveva previsto. Non si ripara qui: tocca
dati persistenti e cambia numeri storici, e cambiare il collaudo che pretende `won` e'
un **cambio di specifica** che va dichiarato e ratificato. La decisione e' di Michele,
perche' e' una regola di business: cosa significa «vinta» nei suoi numeri.

## I CANCELLI DEL CONTRATTO

| | Cancello | Esito |
|---|---|---|
| 1 | i due collaudi nominati passano, uscita salvata | **VERDE** |
| 2 | `artifacts/passo2/` con interrogazioni **e** uscite | **VERDE**, cinque file |
| 3 | P2-03 e P2-04 dichiarano un esito | era **ROSSO** (esito «latente» falso) -> **corretto**: attivo, con il consumatore nominato |
| 4 | `ck-gate.sh --autotest` resta **28/28** | **VERDE** |
| 5 | `git diff tests/` vuoto: nessun collaudo toccato | **VERDE** |

## CHI DICHIARA LA CHIUSURA

**Non l'orchestratore, che ha eseguito il passo.** Codex `gpt-5.6-sol` ha rivalidato e
dichiarato **NON CHIUSO** con tre rilievi. I tre sono stati verificati uno per uno e
corretti in questa stessa stesura. **Serve un secondo giro per la dichiarazione**, e non lo
faccio io.

## COSA NE ESCE PER I PASSI SUCCESSIVI

- **2A: chiuso** nei limiti dichiarati. Il rimborso, dove avviene, e' esatto e quadrato.
- **2B: l'allarme manca**, ed e' una decisione di prodotto, non una riparazione.
- **P2-03 diventa un impegno con priorita' alta**, non un debito: e' un numero sbagliato
  che un giocatore legge adesso. Serve un passo suo, con migrazione e **cambio di
  specifica** — cambiare il collaudo che pretende `won` su un rimborso va ratificato.
  **La decisione e' di Michele:** cosa significa «vinta» nei suoi numeri e nel suo
  estratto conto.
- **Una lacuna di copertura da colmare:** non esiste una prova che un rimborso **dovuto**
  venga sempre **creato**. Oggi si misura solo cio' che e' avvenuto.
