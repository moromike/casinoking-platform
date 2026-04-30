# CasinoKing - Documentation Maintenance

Regole pratiche per mantenere la documentazione ordinata mentre il progetto evolve.

## Obiettivo

Evitare che codice, piani e documenti vadano in direzioni diverse.

Ogni task deve lasciare il repository in uno stato in cui:

- una nuova AI sa da dove partire
- i documenti attivi non contraddicono il codice
- i documenti storici restano consultabili ma non confondono
- ogni modifica importante ha un posto chiaro dove essere raccontata

## Regola base

Prima di scrivere codice:

1. leggere `docs/SOURCE_OF_TRUTH.md`
2. leggere `docs/TASK_EXECUTION_GUARDRAILS.md`
3. leggere `docs/README.md`
4. leggere l'atlas o il documento operativo del dominio coinvolto

Prima di chiudere un task:

1. rileggere `docs/TASK_EXECUTION_GUARDRAILS.md`
2. verificare se e' cambiato un comportamento, un flusso, un mapping file o una decisione
3. aggiornare i documenti indicati nella matrice sotto

## Matrice aggiornamento documenti

| Se modifichi... | Aggiorna/controlla almeno... |
| --- | --- |
| Mines frontend, layout, board, UI, modal, skin | `docs/ARCHITECTURE_ATLAS_MINES.md` se cambiano blocchi/file/responsabilita'. |
| Mines backend, start/reveal/cashout/session/fairness | `docs/ARCHITECTURE_ATLAS_MINES.md`; documenti Mines canonici se cambia comportamento ufficiale. |
| Payout runtime o RTP supportato | `docs/SOURCE_OF_TRUTH.md`, documenti Mines canonici, allegati runtime, `docs/ARCHITECTURE_ATLAS_MINES.md`. |
| RNG/fairness/seed/audit | Documenti Mines 09/10, `docs/ARCHITECTURE_ATLAS_MINES.md`, test fairness. |
| Round gateway o boundary platform/game | `docs/ARCHITECTURE_ATLAS_MINES.md`, `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`, documenti M1/platform-game se ancora pertinenti. |
| Wallet, ledger, accounting, reconciliation | `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`, Documento 05 v3, Documento 11 v2, Documento 12/13 se schema/API cambia. |
| Auth, register, login, password, ruoli | `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`, Documento 11 v2 se API cambia. |
| Dati player, PII, futura KYC/foto/documenti | `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`, schema DB/API relativi, nuovo documento operativo se la feature diventa reale. |
| Backoffice admin | `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`, eventuale piano admin/finance/Mines interessato. |
| Backoffice Mines config/draft/publish/assets | Entrambi gli atlas se cambia il confine tra config gioco e platform admin. |
| Database migration | `docs/ARCHITECTURE_ATLAS_PLATFORM_FRONTEND.md`, `docs/ARCHITECTURE_ATLAS_MINES.md` se riguarda Mines, Documento 12/13 se cambia il target schema. |
| Ambiente locale/Docker/porte/healthcheck | `docs/LOCAL_ENV_RESTART_PROCEDURE.md`, eventualmente `AGENTS.md`. |
| Nuovi piani operativi o milestone | `docs/README.md`; archiviare piani superati in `docs/archive/` quando non sono piu' attivi. |

## Quando aggiornare gli atlas

Aggiornare gli atlas solo se cambia almeno una di queste cose:

- nasce un nuovo blocco concettuale
- un file cambia responsabilita'
- un flusso viene spostato da un modulo a un altro
- un concetto diventa configurabile da backoffice
- un codice atlas non rappresenta piu' il sistema reale

Non aggiornarli per ogni piccolo fix interno.

## Quando aggiornare `docs/README.md`

Aggiornarlo quando:

- nasce un nuovo documento operativo importante
- un documento non e' piu' attivo e viene archiviato
- cambia il percorso di lettura raccomandato per AI/umani
- cambia il dominio principale del progetto

## Quando archiviare

Archiviare un documento se:

- e' una nota di sessione superata
- e' un prompt usato per una revisione passata
- e' un bug report gia' chiuso
- e' un piano sostituito da un piano piu' recente
- contiene decisioni superate da documenti piu' recenti

Non archiviare:

- `SOURCE_OF_TRUTH.md`
- `TASK_EXECUTION_GUARDRAILS.md`
- `docs/README.md`
- `docs/word/`
- `docs/runtime/`
- atlas attivi
- documenti operativi ancora usati

## Come archiviare

1. Spostare il file in una sottocartella di `docs/archive/`.
2. Aggiornare `docs/archive/README.md`.
3. Se il file era citato in `docs/README.md`, aggiornare il riferimento.
4. Non modificare il contenuto storico salvo correzioni minime necessarie.

## Regola per commit

Quando possibile, separare i commit:

- documentazione
- backend
- frontend
- migrazioni DB
- test
- infra

Se un task tocca piu' aree, usare commit piccoli e nominati in modo leggibile.

## Regola per nuove AI

Una nuova AI deve sempre lasciare una traccia chiara:

- cosa ha cambiato
- quali documenti ha letto
- quali documenti ha aggiornato
- quali verifiche ha eseguito
- cosa resta fuori scope
