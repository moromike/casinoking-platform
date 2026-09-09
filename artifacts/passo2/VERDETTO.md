# PASSO 2 — VERDETTO

**10/09/2026** · contratto `CONTRATTO_PASSO2.md` · punta `cc45822`

## L'ESITO IN TRE RIGHE

1. **Il rimborso automatico funziona.** I soldi tornano, esatti al centesimo, e la
   contabilita' quadra. Su questo **non c'e' niente da riparare**.
2. **L'allarme manca davvero**, a ogni livello. Cercato in cinque modi, tutti a zero.
3. **E' emerso un terzo fatto che il piano non prevedeva:** un rimborso e' registrato
   come una **vincita**. Latente oggi, ma e' il genere di numero che chiede un regolatore.

## 2A — IL RIMBORSO TORNA: SI'

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

## P2-03 — L'ETICHETTA: un rimborso e' registrato come una vincita

`refund_no_progress` -> stato `won` (426). `manual_cashout` -> stato `won` (123).
Il collaudo lo **pretende** (`test_boxe_api.py:1284`).
Calcolando dallo stato: 96% di partite vinte. Il vero: **21,5%**.
**Latente:** nessun codice oggi calcola quei numeri da quello stato (controricerche in
`04-etichetta-rimborso.md`). L'informazione giusta c'e' gia' e non va ricostruita.

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
| 3 | P2-03 e P2-04 dichiarano un esito | **VERDE** |
| 4 | `ck-gate.sh --autotest` resta **28/28** | **VERDE** |
| 5 | `git diff tests/` vuoto: nessun collaudo toccato | **VERDE** |

## CHI DICHIARA LA CHIUSURA

**Non l'orchestratore, che ha eseguito il passo.** In attesa del revisore.
