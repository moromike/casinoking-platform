# PASSO 2A — il denaro torna davvero: la prova nel registro contabile

**10/09/2026** `[GENERATO]`. Interrogazioni e uscite, non riassunti.

## 1. Ogni rimborso restituisce ESATTAMENTE la puntata?

```
 rimborsi | importo_esatto | scostamenti 
----------+----------------+-------------
      426 |            426 |           0
(1 row)

```
**Zero scostamenti su 426.** E' il vincolo non negoziabile posto da Michele il 3/09:
la quadratura al centesimo. Sui rimborsi regge.

## 2. La partita doppia regge su quei movimenti?

```
 movimenti | quadrati | sbilanciati 
-----------+----------+-------------
       426 |      426 |           0
(1 row)

```

## 3. Come sono etichettati i movimenti, e qui sta il rilievo di P2-03

```
  settlement_kind   | stato_partita | count 
--------------------+---------------+-------
 refund_no_progress | won           |   426
 manual_cashout     | won           |   123
(2 rows)

```

## Come si rifa'

**Rilievo di Codex in rivalidazione, accolto:** la prima stesura metteva qui un segnaposto
invece delle interrogazioni. Un'uscita senza la sua interrogazione non e' riproducibile, e
il contratto pretende entrambe. Ecco le tre, per intero.

```bash
PG=casinoking-postgres-1
Q(){ docker exec $PG psql -U casinoking -d casinoking -c "$1"; }

# 1 -- ogni rimborso restituisce esattamente la puntata?
Q "select count(*) as rimborsi,
          count(*) filter (where pr.payout_amount = pr.bet_amount) as importo_esatto,
          count(*) filter (where pr.payout_amount <> pr.bet_amount) as scostamenti
   from ledger_transactions lt
   join platform_rounds pr on pr.settlement_ledger_transaction_id = lt.id
   where lt.metadata_json->>'settlement_kind' = 'refund_no_progress';"

# 2 -- la partita doppia regge su quei movimenti?
Q "select count(*) as movimenti,
          count(*) filter (where s.dare = s.avere) as quadrati,
          count(*) filter (where s.dare <> s.avere) as sbilanciati
   from (select lt.id,
                sum(le.amount) filter (where le.entry_side='debit')  as dare,
                sum(le.amount) filter (where le.entry_side='credit') as avere
         from ledger_transactions lt
         join ledger_entries le on le.transaction_id = lt.id
         where lt.metadata_json->>'settlement_kind' = 'refund_no_progress'
         group by lt.id) s;"

# 3 -- come sono etichettati
Q "select lt.metadata_json->>'settlement_kind' as settlement_kind,
          pr.status as stato_partita, count(*)
   from ledger_transactions lt
   join platform_rounds pr on pr.settlement_ledger_transaction_id = lt.id
   where lt.metadata_json ? 'settlement_kind'
   group by 1,2 order by 3 desc;"

# 4 -- da quali giochi arrivano i rimborsi (rilievo di Codex: NON sono prove indipendenti)
Q "select pr.game_code, count(*)
   from ledger_transactions lt
   join platform_rounds pr on pr.settlement_ledger_transaction_id = lt.id
   where lt.metadata_json->>'settlement_kind'='refund_no_progress' group by 1;"
```

**L'esito della quarta, che restringe la conclusione:** `[GENERATO]` **tutti** i rimborsi
vengono da **`mines`**. Non sono centinaia di prove indipendenti su tre giochi: sono
centinaia di ripetizioni di **un solo percorso**. La copertura di BOXE e HI-LO viene dai
due collaudi nominati, non da questi numeri.

**Nota sui numeri:** al primo rilancio erano 426, adesso 434. Cresce perche' ogni corsa
della suite gioca partite. Il rapporto — esatti su totali, quadrati su totali — resta
**tutti su tutti**.
