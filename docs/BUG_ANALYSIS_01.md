# Analisi del Bug (Architect Mode)

## Sintomo
1. Il backend lancia errori `psycopg.OperationalError: failed to resolve host 'postgres': [Errno 11001] getaddrinfo failed`.
2. Il frontend, non potendo raggiungere il backend (riceve errore 500 sull'endpoint `/api/v1/games/mines/config`), effettua un fallback di sicurezza.
3. Questo fallback di sicurezza mostra solo la grid size di default (5x5) e fa sparire le altre opzioni.
4. I test automatizzati (pytest) sono bloccati (hanging) per lo stesso motivo di connessione.

## Causa Radice
La modalità Code precedente ha avviato il backend (`uvicorn`) e i test (`pytest`) direttamente sulla macchina host Windows (tramite i terminali di VSCode), e **non** all'interno dei container Docker.

Tuttavia, non ha configurato le variabili d'ambiente locali. Di conseguenza, l'applicazione sta usando il `DATABASE_URL` di default:
`postgresql://casinoking:casinoking@postgres:5432/casinoking`

L'host `postgres` esiste solo all'interno della rete Docker. Sulla macchina Windows, il database è esposto (tramite port mapping) su `localhost:55432`. Stessa cosa per Redis, che è esposto su `localhost:56379`.

## Soluzione Proposta
1. Terminare tutti i terminali correnti che fanno girare `uvicorn` e `pytest` con la configurazione errata.
2. Creare un file `backend/.env` (o esportare le variabili direttamente nei terminali) con:
   - `DATABASE_URL=postgresql://casinoking:casinoking@localhost:55432/casinoking`
   - `REDIS_URL=redis://localhost:56379/0`
3. Riavviare `uvicorn` assicurandosi che carichi il file `.env`.
4. Riavviare i test per confermare che l'intero sistema (DB compreso) funzioni correttamente.
5. Verificare dal browser che le opzioni (grid sizes e mines) siano riapparse.