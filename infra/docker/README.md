# Docker Bootstrap

Local development bootstrap aligned with Documento 14 v2 and Documento 15.

Included services:
- backend
- frontend
- postgres
- redis
- automatic backend SQL migration bootstrap

Intentionally excluded:
- websocket service
- production deployment configuration
- non-repository seed data beyond the canonical SQL migrations

## Windows note

On Windows workstations it is common to already have a local PostgreSQL service bound to `5432`.

When that happens, keep the public application ports unchanged and override only the infrastructure ports:

```powershell
$env:POSTGRES_PORT='55432'
$env:REDIS_PORT='56379'
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d --build
```

Expected application URLs remain:

- `http://localhost:3000`
- `http://localhost:8000`
