# CON-05 — VERDETTO: un rimborso non e' piu' una vincita

**10/09/2026** · contratto `CONTRATTO_CON05.md` · deciso da Michele
**`[GENERATO]`** dalle interrogazioni in `04-correzione-storico.txt`.

## IL PRIMA E IL DOPO

```
                                  PRIMA            DOPO
partite "vinte"                     559             125
partite "annullate"                   0             434
totale partite                      581             581
somma dei movimenti contabili  8010339.620200  8010339.620200
```

**La somma dei movimenti e' identica al centesimo.** Era il vincolo non negoziabile posto
da Michele il 3/09 e il primo criterio di arresto del contratto: questo lavoro tocca gli
**stati**, mai il **denaro**.

**Le partite vinte calano di esattamente 434**, che e' il numero delle righe corrette.
Nessuna riga estranea e' stata toccata: la correzione ha selezionato **solo** le partite con
`settlement_kind = 'refund_no_progress'`, non quelle che «sembravano» rimborsi per via
dell'importo.

## COSA VEDE IL GIOCATORE, ADESSO

Prima leggeva **«Vinto»** su 434 partite in cui non aveva vinto niente, e quegli importi
entravano nel suo **totale vinto**.

Adesso legge **«Annullato»**, e quelle partite sono escluse sia dal totale vinto sia dal
totale giocato — corretto, perche' la puntata gli e' stata restituita.

**Il frontend non e' stato toccato.** Gestiva gia' `cancelled` nel modo giusto, ed era il
criterio di arresto: *se serve toccare il frontend, la diagnosi era sbagliata*.

## IL NUMERO CHE CAMBIA, E PERCHE' CONTA

| | Prima | Adesso |
|---|---|---|
| tasso di vincita calcolato dallo stato | 559/581 = **96%** | 125/581 = **21,5%** |

Su una piattaforma di gioco il tasso di vincita e l'RTP non sono statistiche interne: sono
i numeri che chiede un regolatore.

## LE DUE TABELLE NON SI CONTRADDICONO PIU'

```
partite con gioco='cancelled' e piattaforma='won'   PRIMA: 420   DOPO: 0
```

**Era il difetto piu' grave e il meno visibile:** il sistema dichiarava due cose diverse su
se' stesso, e quella che il giocatore leggeva era la sbagliata.

## NON ERA UNA DECISIONE NUOVA

Il commit `0ec8fcf` dell'8/09/2026, scritto da Michele:

> *«Le liquidazioni d'ufficio sono CANCELLED, non WON: 278 vincite mai avvenute […] un
> rimborso tecnico non e' una vincita»*

Quella riparazione tocco' la tabella del **gioco**. Questa chiude la meta' mancante, quella
della **piattaforma**. **Stesso ragionamento, stessa parola, due giorni dopo.**

## I COLLAUDI CAMBIATI — quattro, e perche' non e' barare

| File | Perche' |
|---|---|
| `test_boxe_api.py:1284` | pretendeva `won` su un rimborso |
| `test_hi_lo_service.py:801` | idem |
| `test_platform_access_sessions.py:113` | scadenza con **zero mosse**, incasso = puntata |
| `test_platform_access_sessions.py:169` | idem |

**Riscrivere un collaudo perche' passi e' la malattia per cui esiste la Fase GATE.** Qui e'
l'opposto: quei quattro **codificavano il difetto**, e cambiarli era il lavoro. La
differenza sta in tre cose, tutte verificabili: e' stato **dichiarato prima**
(`.missione: sviluppo`), e' **ratificato nel commit**, e il **cricchetto lo vede**.

**Cinque altri collaudi che pretendono `won` NON sono stati toccati**, ed e' la prova che la
modifica e' mirata: sono incassi veri. Fra questi
`test_start_on_expired_access_session_...`, che scade come i due corretti ma ha **quattro
mosse** — c'e' progresso, quindi c'e' vincita. E' rimasto verde da solo.

## DUE COSE CHE HO SBAGLIATO, e sono nello stesso commit

1. **Avevo trovato solo due dei quattro collaudi.** Cercavo `platform_row["status"]`, e
   `test_platform_access_sessions.py` usa `round_row["status"]`. Li ha trovati la suite
   completa, non io. E' **la seconda volta oggi** che una mia ricerca e' troppo stretta: la
   prima fu cercare *chi calcola* e non *chi mostra*.
   **Il contratto ha retto:** diceva *«se un collaudo diverso dai due previsti diventa
   rosso, ci si ferma e si capisce perche' prima di toccarlo»*. Fermandomi ho verificato che
   erano rimborsi puri — puntata 5, incasso 5, zero mosse — invece di adeguare l'attesa.
2. **Il primo commit e' stato fermato dal cricchetto,** perche' il riferimento partiva prima
   della dichiarazione di sviluppo. Aveva ragione: dentro l'intervallo giudicato la missione
   era ancora `riparazione`.

## I CANCELLI DEL CONTRATTO

| | Cancello | Esito |
|---|---|---|
| 1 | il rosso di prima esiste, con la frase attesa | **VERDE** — `assert 'won' == 'cancelled'`, la stessa del guasto D2 |
| 2 | i collaudi del rimborso verdi dopo la modifica | **VERDE** |
| 3 | nessun rimborso resta in `won`, e i `won` calano esattamente | **VERDE** — 0 rimasti, −434 esatti |
| 4 | le due tabelle concordano | **VERDE** — 420 -> 0 |
| 5 | **la contabilita' non e' cambiata** | **VERDE** — somma identica |
| 6 | `ck-gate.sh --autotest` = 28/28 | **VERDE** |
| 7 | gate VERDE e collaudi raccolti non calati | **VERDE** — 692 eseguiti / **947** raccolti |
| 8 | `--collaudi-intoccabili` esce 0 | **VERDE** |

**Otto su otto.**

## COSA RESTA APERTO

- **CON-06:** nessuna prova che un rimborso **dovuto** venga sempre **creato**. Questo
  lavoro corregge l'etichetta dei rimborsi avvenuti, non la loro esistenza.
- **Le perdite** non hanno `settlement_ledger_transaction_id`: tracciabilita' a senso unico.
  Fuori scope dichiarato.
- **L'allarme** del PASSO 2B: decisione di prodotto.

## CHI DICHIARA LA CHIUSURA

**Non l'orchestratore, che ha scritto il codice.**
