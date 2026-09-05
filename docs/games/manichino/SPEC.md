# Manichino — SPEC

Il manichino **non e' un gioco**: nessuna grafica, nessuna regola, nessun
generatore casuale, nessun giocatore lo aprira' mai. E' la cavia contabile
della piattaforma.

## Perche' esiste

Decine di test della piattaforma non testano i giochi: usano un gioco per
produrre una transazione e poi verificano contabilita', sessioni, registro e
rotte. Il manichino muove soldi veri attraverso le tubature vere
(`platform_rounds`, `ledger_transactions`, wallet, sessioni tavolo) e l'esito
lo decide chi chiama.

## Contratto

- `POST /games/manichino/start` — trattiene `bet_amount` aprendo il round
  economico (giuntura `PlatformGameAdapter.open_round`).
- `POST /games/manichino/settle` — `esito: "vincita"` accredita
  `payout_amount` (`settle_win`); `esito: "perdita"` consuma la puntata
  (`settle_loss`).
- Idempotenza: stessa `Idempotency-Key` = nessuna doppia scrittura contabile.
- Deterministico per costruzione: niente `random`, niente `secrets`. L'id del
  round e' `uuid5` della chiave di idempotenza.

## Interruttore (MAN-05)

Attivo solo se `CK_MANICHINO` in (`1`, `true`, `si`) **e** `APP_ENV` non e'
`production`/`prod`. In produzione il modulo non si registra e le rotte non
esistono (404).

## Sicurezza

Il manichino non entra nel catalogo pubblico, non compare in lobby e non ha
titolo pubblicabile: il titolo tecnico `manichino_test` esiste solo per
soddisfare la foreign key di `platform_rounds.title_code` e va creato con lo
stesso meccanismo delle fixture di test.
