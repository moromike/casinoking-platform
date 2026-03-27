# CasinoKing - Documento 23

Vincoli e priorita' operative del backend e della piattaforma

Stato del documento

- Questo documento e' operativo e vincolante per backend, piattaforma e API.
- Non sostituisce `docs/SOURCE_OF_TRUTH.md` o i documenti canonici backend/financial core.
- Va letto insieme a Documento 05 v3, Documento 11 v2, Documento 12 v3, Documento 13 v3 e Documento 15.

## 1. Obiettivo

Rendere esplicito l'ordine di priorita' backend, per evitare che scelte UX o scorciatoie frontend portino a compromettere il modello piattaforma.

## 2. Vincoli assoluti

1. Il ledger resta la fonte contabile primaria.
2. Il wallet resta snapshot materializzato del ledger.
3. Wallet e ledger non devono divergere in un commit riuscito.
4. Gli endpoint finanziariamente sensibili devono restare idempotenti e transazionalmente coerenti.
5. Mines resta server-authoritative.
6. Il frontend non deve richiedere eccezioni architetturali solo per ottenere una UX piu' rapida.

## 3. Ordine di priorita'

1. Integrita' finanziaria.
2. Coerenza del lifecycle di gioco.
3. Separazione dei domini piattaforma / gioco / admin.
4. Semplicita' dei flussi esterni appoggiati al backend.
5. Estensioni non essenziali.

## 4. Regole di servizio

### 4.1 Player

- il backend serve il player flow senza esporre strumenti admin
- il player puo' vedere solo dati owner-only o pubblici previsti

### 4.2 Admin

- il backend admin deve restare separato logicamente dal percorso player
- login backoffice, reporting e gestione giocatore non devono contaminare il modulo gioco

### 4.3 Mines

- le configurazioni runtime supportate derivano dai documenti e dagli allegati runtime
- la UX Mines non autorizza workaround backend arbitrari

## 5. No-go espliciti

- niente bypass del ledger
- niente saldo modificato direttamente dal frontend
- niente outcome client-side
- niente endpoint improvvisati solo per accomodare una scelta UI momentanea
- niente mescolanza concettuale tra API player e backoffice

## 6. Cosa fare in caso di dubbio

Se una richiesta UI porta a un rischio sul modello finanziario o server-authoritative, si ferma.

Se una richiesta di prodotto richiede nuove API, queste vanno introdotte solo se coerenti con i documenti canonici e con separazione di dominio chiara.
