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

```bash
PG=casinoking-postgres-1
docker exec $PG psql -U casinoking -d casinoking -c "<le interrogazioni qui sopra>"
```
