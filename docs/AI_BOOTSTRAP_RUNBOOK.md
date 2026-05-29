Status: ACTIVE
Last meaningful update: 2026-05-28

# CasinoKing AI Bootstrap Runbook

## Purpose

The root `README.md` is the remembered project entry point. This runbook is the
operational handoff document linked from that README for a fresh AI agent, Codex
Desktop session, Codex VS Code session, Codex CLI session, or human reviewer
entering the CasinoKing repository without reliable chat memory.

It does not replace the project source documents. It tells the agent what to
read, what to verify, what not to assume, and where to stop before code.

## Non-Negotiable Rule

Do not use `AGENTS.md` as the primary project rule source.

Shared rules live under `docs/`. `AGENTS.md` may point to those rules, but it is
not the authoritative location because not every AI client or tool reliably
shares or respects it.

## Required First Reading

Read these files before touching code:

1. `docs/SOURCE_OF_TRUTH.md`
2. `docs/TASK_EXECUTION_GUARDRAILS.md`
3. `docs/DOCUMENTATION_MAINTENANCE.md`
4. `docs/AI_CRITICAL_JUDGMENT_RULES.md`
5. `docs/ACTIVE_OPEN_LOOPS.md`

Then read only the domain documents required by the current task.

Do not claim a file was read if it was only discovered, searched, or listed.
Distinguish clearly between:

- files actually read;
- files only identified;
- files intentionally skipped because they were outside the task.

## Project In One Page

CasinoKing is a local-first casino platform and proprietary game system.

Main components:

- backend: FastAPI modular monolith;
- frontend-v3: Next.js public/player/admin application;
- frontend/: legacy source quarantine, not a Docker service in the local stack;
- database: PostgreSQL;
- cache/runtime infrastructure: Redis;
- local orchestration: Docker Compose under `infra/docker/`;
- official project rules and plans: `docs/`;
- proprietary games: Mines, BOXE, HI-LO, and future games such as COINS.

Core architecture principles:

- wallet snapshot is materialized;
- ledger is the accounting source of truth;
- financially sensitive endpoints require idempotency;
- games must preserve platform/game boundaries;
- demo mode uses dedicated demo state and must not write real ledger/platform
  round records;
- MVP communication is polling/request-response, not WebSocket.

## Current Operating State

As of 2026-05-28, use `docs/ACTIVE_OPEN_LOOPS.md` as the live operational
dashboard.

Important current direction:

- Site V3 WP5/WP6 technical work is closed locally. WP2 backend, WP3 admin
  builder, WP4 public renderer, WP-A CMS IA cleanup, WP-B theme tokens, asset
  workflow, lab cleanup and the local public edge are in place. Use
  `:3000` as the public Site V3 root and `:3000/admin/site-v3` for admin;
  `:3001` is the direct renderer. The V1 direct frontend service has been
  removed from the local Docker stack; `frontend/` remains only as quarantined
  legacy source until its remaining contracts are retired.
- COINS is not ready for implementation. Phase 0+1 product questions are closed,
  prerequisites are committed, and the next step is approval of the plan and
  production of final source inventory, decision map, 12-surface status, SPEC,
  MATH_SPEC, and ARCHITECTURE_MAPPING. Do not start COINS code before the
  documentation gate is closed.
- Platform error/logging/finance/settings MVP tranche is closed. Do not reopen
  it as a mega-work-package; residual gaps need dedicated WPs.
- Mines V1 baseline is accepted. Do not reopen BOOT-2A. Mines legacy browser
  smoke debt remains open but is separate from product polish unless it becomes
  blocking.

If this section conflicts with a later `docs/ACTIVE_OPEN_LOOPS.md`, the later
open-loops document wins.

## Local Environment Bootstrap

Authoritative detailed procedure:

- `docs/LOCAL_ENV_RESTART_PROCEDURE.md`

Compose file:

- `infra/docker/docker-compose.yml`

Environment template:

- `infra/docker/.env.example`

Local environment file:

- `infra/docker/.env`

If `infra/docker/.env` does not exist, create it from
`infra/docker/.env.example` before starting the stack.

Preferred PowerShell scripts:

```powershell
.\scripts\ck-up.ps1
.\scripts\ck-doctor.ps1
.\scripts\ck-down.ps1
```

PowerShell start command:

```powershell
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env up -d --build
```

PowerShell stop command:

```powershell
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env down
```

Expected local URLs:

- public website edge: `http://localhost:3000` (Site V3 root)
- Site V3 direct renderer: `http://localhost:3001`
- backend docs: `http://localhost:8000/docs`
- backend live health: `http://localhost:8000/api/v1/health/live`

## Required Runtime Verification

Do not declare the local environment ready until these checks are true or until
you explicitly report which checks could not be run.

Minimum checks:

1. Docker daemon is available.
2. Docker Compose services are up.
3. public edge responds on `http://localhost:3000`.
4. Site V3 direct renderer responds on `http://localhost:3001`.
5. backend live health responds on
   `http://localhost:8000/api/v1/health/live`.
6. Postgres accepts a real query inside the container.
7. Redis is healthy.
8. Docker Compose reports the expected services healthy.

Suggested commands:

```powershell
docker info
docker compose -f infra/docker/docker-compose.yml --env-file infra/docker/.env ps
```

For database verification, execute a real query inside Postgres, for example:

```sql
select now() as server_time, current_database() as db, current_user as db_user;
```

The command wrapper may evolve as the local scripts mature. The verification
requirements do not change.

Canonical local doctor script:

```powershell
.\scripts\ck-doctor.ps1
```

The doctor checks Docker daemon access, compose health for backend, frontend-v3,
edge, postgres and redis, public edge HTTP 200, backend live health HTTP 200, a
real Postgres query, and Redis `PONG`.

## Windows / PowerShell Notes

Michele's active workstation path is Windows + PowerShell + Docker Desktop.

Use PowerShell commands when operating on this machine. Docker is the project
invariant; the host shell may differ across future machines.

Known local port-conflict pattern:

- Redis host port `56379` may conflict with Windows reserved ranges.
- Postgres host port `55432` may also conflict on some restarts.
- Existing local workaround may use `REDIS_PORT=56800` and
  `POSTGRES_PORT=56543` in `infra/docker/.env`.

Do not change container-internal ports or service URLs such as:

- `DATABASE_URL=postgresql://casinoking:casinoking@postgres:5432/casinoking`
- `REDIS_URL=redis://redis:6379/0`

Only adjust host port mappings when needed.

## Local State Classification

Repository-authoritative:

- `docs/`
- `backend/`
- `frontend/`
- `frontend-v3/`
- `games/`
- `infra/docker/docker-compose.yml`
- `infra/docker/.env.example`
- tests and committed source files

Local reproducible configuration:

- `infra/docker/.env`

Local generated runtime state:

- `var/`
- `backend/var/`
- Docker volumes
- local Postgres data
- local logs

Local secrets or sensitive notes:

- `.local/`
- generated admin passwords
- local credential notes
- AI-client auth files

AI-client state, not project truth:

- `~/.codex`
- Codex Desktop sessions
- Codex VS Code sessions
- Codex CLI logs
- other AI memories, caches, or local conversation history

Use AI-client state only as optional context when the user explicitly asks. Do
not treat it as more authoritative than repository documents.

## Codex Desktop / VS Code / CLI Handoff

When moving between Codex Desktop, Codex in VS Code, Codex CLI, or another AI
client:

1. Open the same repository path.
2. Read this runbook.
3. Read the required first-reading set.
4. Ignore previous chat memory unless the user explicitly provides or asks to
   use it.
5. Do not assume sessions, logs, plugin state, local memories, or `~/.codex`
   content are synchronized.
6. Confirm current work from `docs/ACTIVE_OPEN_LOOPS.md`, not from memory.

Recommended fresh-session prompt:

```text
You are entering CasinoKing fresh. Read the root README.md first, then follow
docs/AI_BOOTSTRAP_RUNBOOK.md and its required first-reading list. Do not use
AGENTS.md as the primary source. After reading, summarize current primary
workstreams, stop-before-code gates, and the minimum local verification steps
before proposing any change.
```

## Before Starting Any Task

Answer these internally before editing:

1. What exactly did Michele ask for?
2. Which domain does it touch?
3. Which required docs have I actually read?
4. Which domain docs are necessary?
5. What is explicitly out of scope?
6. Does this touch wallet, ledger, payout, replay, settlement, auth, production
   security, or game runtime?
7. Does this require CTO/product approval before code?
8. Will the user verify this on localhost?
9. Which service needs rebuild/restart after the change?
10. Which docs must be updated in the same task?

If the task crosses multiple layers, prepare a capability matrix before
declaring completion:

```text
Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Stato | Note
```

## Stop-Before-Code Gates

Stop and ask for approval, or produce a plan instead of code, when the task
would:

- change wallet, ledger, accounting, settlement, payout, RTP, RNG, fairness, or
  replay retention;
- start implementation for a new proprietary game before SPEC/MATH/architecture
  documents are approved;
- change production security assumptions;
- merge local creative assets into product runtime without asset registry or a
  documented pipeline;
- reopen a closed work package as a broad mega-WP;
- mix unrelated copy, layout, behavior, architecture, and data changes in one
  task;
- add UI helper text, badges, buttons, or sections that Michele did not ask for.

The correct behavior is not passive agreement. If the request is risky, explain
the risk and propose the minimal safer path.

## Documentation Update Rules

Before closing a task, re-check:

- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`

Update docs in the same task when behavior, architecture, mapping,
capabilities, admin UI, local environment procedure, or active work status
changes.

Common document targets:

- backoffice/admin capability change: `docs/BACKOFFICE_MANUAL.md`
- local Docker/environment change: `docs/LOCAL_ENV_RESTART_PROCEDURE.md`
- active workstream status change: `docs/ACTIVE_OPEN_LOOPS.md`
- new operational doc or reading path change: `docs/README.md`
- module ownership or flow change: relevant architecture atlas and Mermaid map

## Delivery Report Template

Use a concise final report that includes:

```text
Changed:
- ...

Read:
- actually read: ...
- identified only: ...
- skipped as out of scope: ...

Verified:
- ...

Docs:
- updated: ...
- not required because: ...

Out of scope:
- ...

Next step:
- ...
```

For very small tasks, compress this format, but do not omit failed or skipped
verification.

## Definition Of Bootstrapped

A session is bootstrapped when:

1. This runbook was read.
2. The required first-reading set was read.
3. The current active workstream and stop-before-code gates are known.
4. Local environment state is understood or explicitly marked not verified.
5. The agent knows which docs are authoritative for the task.
6. The agent can state what will and will not be changed.

Do not proceed to implementation until the session is bootstrapped for the
requested task.

## Local Bootstrap Scripts

Executable PowerShell scripts live in `scripts/`:

- `scripts/ck-up.ps1`
- `scripts/ck-down.ps1`
- `scripts/ck-doctor.ps1`
- `scripts/ck-test-smoke.ps1`

`ck-test-smoke.ps1` runs the canonical local smoke suite defined in
`docs/LOCAL_SMOKE_SUITE.md`. `docs/LOCAL_ENV_RESTART_PROCEDURE.md` remains the
detailed source for local restart and verification policy.
