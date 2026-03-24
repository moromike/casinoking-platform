# CasinoKing – AGENTS.md

## Missione del progetto
Questo repository contiene il progetto CasinoKing, composto da:
1. piattaforma casino
2. giochi proprietari, con Mines come primo modulo

L'obiettivo non è produrre codice veloce o approssimativo, ma costruire una base robusta, coerente e scalabile.

## Regola fondamentale
Prima di proporre o scrivere codice, leggi sempre:

1. `docs/SOURCE_OF_TRUTH.md`

Poi segui i documenti indicati lì in base al tema:
- financial core → Documento 05 v3, 11 v2, 12 v3, 13 v3
- Mines → Documento 06, 07 v2, allegati runtime, 08 v2, 09 v2, 10
- infra → Documento 14 v2
- execution → Documento 15

## Gerarchia delle fonti
- I file Word in `docs/word/` sono i documenti canonici.
- I file in `docs/runtime/` sono allegati operativi vincolanti.
- Se in futuro esisteranno mirror `.md`, saranno versioni operative fedeli dei documenti Word, non riassunti liberi.
- Se due fonti sembrano in conflitto, vale la versione più recente e più specifica.

## Regole di comportamento
- Non inventare requisiti non presenti nei documenti ufficiali.
- Non semplificare il modello finanziario.
- Non bypassare wallet/ledger con aggiornamenti diretti di saldo.
- Non introdurre feature non richieste.
- Non modificare l’architettura senza motivazione esplicita.
- Non trattare i documenti metodologici come opzionali: sono parte del progetto.

## Regole finanziarie non negoziabili
- Il ledger è la fonte contabile primaria.
- Il wallet usa snapshot materializzato.
- Ledger e snapshot non possono divergere in un commit riuscito.
- Il modello è double-entry.
- Esiste un piano dei conti con `ledger_accounts`.
- Gli endpoint finanziariamente sensibili devono rispettare idempotenza e coerenza transazionale.

## Regole Mines non negoziabili
- Mines è server-authoritative.
- Il frontend non decide outcome, board o payout.
- I payout runtime devono derivare dagli allegati ufficiali in `docs/runtime/`.
- L'RTP deve restare sopra il 90% e sotto il 100% nelle configurazioni supportate.
- Per il MVP si usa polling / request-response, non WebSocket.

## Come lavorare
Quando ricevi una richiesta:
1. identifica il dominio coinvolto
2. leggi i documenti corretti
3. riassumi internamente le regole applicabili
4. proponi il minimo passo corretto
5. implementa solo ciò che è richiesto
6. segnala esplicitamente eventuali ambiguità o conflitti documentali

## Stile di implementazione
- Preferire codice chiaro, robusto e testabile
- Preferire task piccoli e incrementali
- Scrivere test per la logica critica
- Considerare obbligatori i test di concorrenza per le aree sensibili
- Mantenere separazione netta tra piattaforma e gioco

## Aree critiche
Le aree più sensibili del repository sono:
- wallet
- ledger
- idempotenza
- cashout
- game session state
- payout runtime
- riconciliazione

Su queste aree è meglio essere conservativi che “smart”.

## Cosa fare in caso di dubbio
Se una richiesta sembra confliggere con la documentazione:
- non scegliere arbitrariamente
- fermati
- indica quale documento o regola è in conflitto
- proponi l’opzione più coerente con `docs/SOURCE_OF_TRUTH.md`