# CasinoKing – Documento 09 v2

Mines – engine logico con testing strategy e concorrenza

## 1. Cosa cambia rispetto alla v1

- La testing strategy viene formalizzata.
- I test di concorrenza diventano requisito esplicito.
- Si distingue tra unit, integration, contract e concurrency tests.

## 2. Strategia di test obbligatoria

| Livello | Obiettivo | Esempi | Obbligatorietà |
| --- | --- | --- | --- |
| Unit | Regole pure | state machine, payout lookup, validators | Alta |
| Integration | DB+service | start/reveal/cashout reali | Alta |
| Contract | API behavior | status codes, payload, auth | Media/Alta |
| Concurrency | Race conditions | double cashout, duplicate reveal | Alta |

## 3. Casi di concorrenza minimi

1. Due cashout simultanei sulla stessa sessione → uno solo deve vincere.
2. Reveal simultanei sulla stessa cella → una sola request valida.
3. Reveal simultanei su celle diverse della stessa sessione → coerenza di stato garantita.
4. Start duplicato con stessa idempotency key → una sola game_session effettiva.

## 4. Testing ledger collegato al gioco

- Ogni start crea la transaction e i posting attesi.
- Ogni win crea posting coerenti e aggiorna lo snapshot saldo.
- Ogni loss non accredita impropriamente il player.
- Reconciliation test: wallet snapshot = aggregato ledger dopo ogni scenario.

## 5. Raccomandazioni implementative

- Usare test integration con Postgres reale in container.
- Eseguire test di concorrenza con richieste parallele vere.
- Evitare di considerare sufficienti i soli mock unitari.
