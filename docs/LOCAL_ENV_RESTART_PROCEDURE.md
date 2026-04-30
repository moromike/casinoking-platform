# CasinoKing Local Environment Restart Procedure

Questa procedura definisce il flusso operativo da seguire quando viene richiesto di avviare o riavviare l'ambiente locale del progetto.

## Quando usarla
- Quando l'utente chiede di avviare l'ambiente locale
- Quando l'utente chiede di riavviare i servizi
- Quando l'utente usa trigger brevi come:
  - `riavvia i servizi`
  - `alza l'ambiente locale`
  - `porta su lo stack CasinoKing`

## Obiettivo
Riportare online lo stack locale completo del progetto e dichiarare successo solo dopo verifiche reali su frontend, backend, database e Redis.

## Procedura obbligatoria
1. Verificare che Docker Desktop e il daemon Docker siano davvero pronti.
2. Controllare `infra/docker/.env`.
3. Avviare lo stack con:
   - `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d`
4. Se una porta host e' occupata o riservata da Windows:
   - identificare il conflitto reale
   - applicare la minima correzione locale necessaria in `infra/docker/.env`
   - non cambiare l'architettura del progetto
   - non cambiare host o porte interne usate dai container tra loro
5. Verificare realmente:
   - frontend su `http://localhost:3000`
   - backend su `http://localhost:8000/api/v1/health/live`
   - database con una query reale eseguita dentro Postgres
6. Verificare lo stato finale di:
   - frontend
   - backend
   - postgres
   - redis
7. Non dichiarare successo finche' tutti i controlli non sono verdi.

## Verifiche minime richieste

### Docker
- `docker info`
- `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env ps`

### Frontend
- Verificare che `http://localhost:3000` risponda `200`
- Verificare che il container frontend risulti `healthy`

### Backend
- Verificare che `http://localhost:8000/api/v1/health/live` risponda `200`
- Verificare che il container backend risulti `healthy`

### Database
- Eseguire una query reale dentro il container Postgres, ad esempio:

```sql
select now() as server_time, current_database() as db, current_user as db_user;
```

- Verificare che il container postgres risulti `healthy`

### Redis
- Verificare che il container redis risulti `healthy`

## Correzione locale gia' nota
Su questa macchina Windows la porta host Redis `56379` puo' entrare in conflitto con range riservati del sistema operativo dopo riavvii o update.

La correzione locale minima gia' adottata e':
- `REDIS_PORT=56800` in `infra/docker/.env`

Questa correzione:
- e' locale alla macchina
- non cambia la porta interna del servizio Redis nel network Docker
- non cambia `REDIS_URL=redis://redis:6379/0` usata dai container

## Regola di consegna
La procedura e' completata solo se:
- frontend risponde
- backend risponde
- la query su Postgres funziona
- tutti i container richiesti risultano `healthy`

Se anche uno solo di questi punti fallisce, non dichiarare l'ambiente pronto.
