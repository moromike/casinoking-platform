Status: ACTIVE
Last meaningful update: 2026-05-10

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

## Regola di rilascio locale dopo un task
Quando un task modifica codice che l'utente verifica su `localhost`, il refresh del browser non e' una verifica sufficiente.

Regola:
- modifica frontend servita dal container: eseguire rebuild/restart mirato del servizio `frontend`;
- modifica Site V3 public renderer servita dal container: eseguire rebuild/restart mirato del servizio `frontend-v3`;
- modifica routing pubblico locale: eseguire rebuild/restart di `frontend`, `frontend-v3` ed `edge`;
- modifica backend servita dal container: verificare se basta il reload del volume montato o se serve rebuild, poi controllare health/API coinvolta;
- modifica Dockerfile, dipendenze, env o build-time config: eseguire rebuild del servizio coinvolto;
- consegnare solo dopo una prova runtime specifica sulla rotta, API o stringa toccata.

Per modifiche frontend-only usare:

```powershell
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d --build frontend
```

Per modifiche al renderer pubblico Site V3 usare:

```powershell
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d --build frontend-v3
```

Dopo il comando:
1. attendere che `frontend` risulti `healthy`;
2. attendere anche `frontend-v3` quando il task tocca Site V3 public renderer;
3. verificare `http://localhost:3000` come public edge Site V3;
4. verificare `http://localhost:3001` quando il task tocca Site V3 diretto;
5. verificare `http://localhost:3002` quando il task tocca V1 diretto;
6. verificare almeno una rotta o evidenza runtime della modifica;
7. comunicare all'utente cosa e' stato riallineato e cosa deve ritestare.

Se il riallineamento locale non viene eseguito, dichiararlo esplicitamente nella consegna. Non lasciare implicito che basti un refresh.

## Procedura obbligatoria
1. Verificare che Docker Desktop e il daemon Docker siano davvero pronti.
2. Controllare `infra/docker/.env`.
3. Avviare lo stack con lo script preferito:
   - `.\scripts\ck-up.ps1`
   Oppure, manualmente:
   - `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d`
4. Se una porta host e' occupata o riservata da Windows:
   - identificare il conflitto reale
   - applicare la minima correzione locale necessaria in `infra/docker/.env`
   - non cambiare l'architettura del progetto
   - non cambiare host o porte interne usate dai container tra loro
5. Verificare realmente:
   - public edge su `http://localhost:3000`
   - Site V3 direct renderer su `http://localhost:3001`
   - V1 frontend diretto su `http://localhost:3002`
   - backend su `http://localhost:8000/api/v1/health/live`
   - database con una query reale eseguita dentro Postgres
6. Verificare lo stato finale di:
   - frontend
   - frontend-v3
   - edge
   - backend
   - postgres
   - redis
7. Non dichiarare successo finche' tutti i controlli non sono verdi.

## Verifiche minime richieste

### Docker
- `docker info`
- `docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env ps`
- oppure `.\scripts\ck-doctor.ps1`, che esegue il set minimo di verifiche
  Docker/frontend/backend/Postgres/Redis.

### Frontend
- Verificare che `http://localhost:3000` risponda `200` e serva Site V3 tramite `edge`
- Verificare che il container `edge` risulti `healthy`
- Verificare che `http://localhost:3002` risponda `200`
- Verificare che il container `frontend` risulti `healthy`
- Verificare che `http://localhost:3001` risponda `200`
- Verificare che il container `frontend-v3` risulti `healthy`

### Backend
- Verificare che `http://localhost:8000/api/v1/health/live` risponda `200`
- Verificare che il container backend risulti `healthy`
- Da Fase 4 asset registry, il backend monta anche il volume locale
  `var/assets` su `/app/backend/var/assets` e serve gli asset da
  `/static/games/...`; da CMS-2D serve anche i banner sito da
  `/static/sites/...` nello stesso volume. Non e' un servizio separato, ma se
  il backend non parte controllare anche che il path asset sia
  creabile/scrivibile.

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
- `POSTGRES_PORT=56543` in `infra/docker/.env` quando `55432` cade in un range TCP riservato da Windows

Questa correzione:
- e' locale alla macchina
- non cambia le porte interne dei servizi nel network Docker
- non cambia `REDIS_URL=redis://redis:6379/0` o `DATABASE_URL=postgresql://casinoking:casinoking@postgres:5432/casinoking` usate dai container

## Regola di consegna
La procedura e' completata solo se:
- public edge risponde
- frontend V1 diretto risponde
- frontend-v3 risponde
- backend risponde
- la query su Postgres funziona
- tutti i container richiesti risultano `healthy`

Se anche uno solo di questi punti fallisce, non dichiarare l'ambiente pronto.

## Script locali

Gli script PowerShell canonici per Windows + Docker Desktop vivono in
`scripts/`:

- `.\scripts\ck-up.ps1`: avvia lo stack con rebuild usando
  `infra/docker/docker-compose.yml` e `infra/docker/.env`.
- `.\scripts\ck-down.ps1`: ferma lo stack con `docker compose down`.
- `.\scripts\ck-doctor.ps1`: verifica Docker daemon, servizi compose healthy,
  public edge `http://localhost:3000`, frontend V1 diretto
  `http://localhost:3002`, Site V3 direct renderer `http://localhost:3001`,
  backend live health, query reale Postgres e Redis `PONG`.
- `.\scripts\ck-test-smoke.ps1`: esegue la smoke suite locale canonica definita
  in `docs/LOCAL_SMOKE_SUITE.md`.
