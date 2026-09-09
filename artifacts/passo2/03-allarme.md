# PASSO 2B — l'allarme: accertato, non supposto

**10/09/2026** `[GENERATO]`. Il piano marcava «l'allarme mancante» `[NON ASSERITO]`.
Qui viene accertato con dei comandi, e si dichiara **cosa si e' cercato** — perche' la
lezione della notte del 9/09 e' che *un rilievo non riprodotto non e' un difetto*:
tre rilievi su nove erano falsi.

## Cosa si e' cercato, e cosa si e' trovato

```
1) un avviso nel percorso del rimborso
   grep -rlnE 'alert|allarme|notify|webhook|sentry' backend/app/modules/platform/rounds/  ->  0
2) un avviso nei moduli di autoliquidazione dei quattro giochi  ->  0
3) qualunque integrazione di allarme in tutto il backend  ->  0
4) un logger con livello di allarme sul rimborso  ->  0
5) un contatore/metrica esposta (prometheus e simili)  ->  0
6) lo spazzino che chiude le sessioni: ogni quanto gira  ->  ACCESS_SESSION_SWEEP_INTERVAL_SECONDS = 30
7) il rimborso viene almeno REGISTRATO da qualche parte  ->  1
```

## Esito

**L'allarme manca davvero, e manca a ogni livello.** Non esiste nessun avviso, nessuna
metrica, nessun registro di livello error o warning quando scatta un rimborso
automatico. Cercato in cinque modi diversi, tutti a zero.

**Ma non e' un buco nero:** il rimborso **viene registrato** — in
`ledger_transactions.metadata_json` con `settlement_kind = 'refund_no_progress'`, e
`[GENERATO]` oggi ce ne sono **426**. L'informazione esiste e si puo' interrogare.

**La differenza, in una riga:** oggi **si puo' sapere**, se qualcuno va a guardare.
Nessuno viene avvisato. Uno spazzino chiude le sessioni ogni **30 secondi**
(`backend/app/main.py:19`) e ogni rimborso che ne consegue e' silenzioso.

## Cosa NON si fa qui, ed e' scritto nel contratto

**Costruire l'allarme non e' questo passo.** Questo passo accerta se manca, e manca.
Il perche' conta: un allarme e' una decisione di prodotto — chi viene avvisato, con
quale soglia, e cosa deve fare quando arriva. Non e' una riga di codice da aggiungere
di nascosto in una verifica.
