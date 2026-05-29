Status: ACTIVE
Last meaningful update: 2026-05-28

# CasinoKing Self-Bootstrap Audit

## Executive Summary

CasinoKing is partially self-bootstrapping today.

A fresh AI agent or CTO reviewer can understand the project rules, source
hierarchy, active workstreams, and documentation discipline from the repository
alone. The strongest foundations are already in place: `docs/README.md`,
`docs/SOURCE_OF_TRUTH.md`, `docs/TASK_EXECUTION_GUARDRAILS.md`,
`docs/DOCUMENTATION_MAINTENANCE.md`, `docs/AI_CRITICAL_JUDGMENT_RULES.md`,
`docs/ACTIVE_OPEN_LOOPS.md`, and `docs/LOCAL_ENV_RESTART_PROCEDURE.md`.

The repository is not yet fully self-bootstrapping because the operational path
from "fresh environment" to "verified local stack and correct next task" is
still distributed across multiple documents and local-machine assumptions. The
missing piece is not more project history. The missing piece is a short,
repeatable, executable bootstrap layer.

## Definition Of Self-Bootstrapping

CasinoKing should be considered self-bootstrapping when a fresh human or AI,
without relying on chat memory or a specific local Codex session, can:

1. Open or clone the repository.
2. Identify the authoritative project rules.
3. Understand the active workstream and stop-before-code gates.
4. Prepare the local environment without guessing hidden machine state.
5. Start the local stack.
6. Verify frontend, backend, database, Redis, and a minimal test surface.
7. Know what may be changed, what must not be changed, and what needs CTO or
   Michele approval before code.
8. Leave a clear delivery report with documents read, documents updated,
   verification performed, and out-of-scope items.

This definition intentionally excludes AI vendor memory, previous chat context,
and local tool state such as `~/.codex` sessions or logs.

## Current Strengths

### Source Hierarchy Exists

`docs/SOURCE_OF_TRUTH.md` defines the official document hierarchy and practical
precedence rules. It already separates canonical Word documents, runtime
attachments, operational docs, and documents that must not be used as reference.

### Agent Rules Are Centralized

The repository already states that `AGENTS.md` is not the primary rule source.
Shared rules live under `docs/`, especially:

- `docs/SOURCE_OF_TRUTH.md`
- `docs/TASK_EXECUTION_GUARDRAILS.md`
- `docs/DOCUMENTATION_MAINTENANCE.md`
- `docs/AI_CRITICAL_JUDGMENT_RULES.md`

This is a strong design choice because it avoids depending on a single AI tool's
instruction format.

### Active Work Is Tracked Outside Chat Memory

`docs/ACTIVE_OPEN_LOOPS.md` acts as a short operational dashboard. It records
open work that must not live only in one chat session.

As of 2026-05-28, the main visible open tracks include:

- Site V3 WP5 polish/product QA, with WP6 cleanup still future.
- COINS Phase 0+1 documentation approval before any implementation.
- Mines legacy browser smoke debt.
- Product QA items for Mines intro, How To Play gate, audio assets, and player
  finance/account surfaces.

This is exactly the kind of state a self-bootstrapping repository needs.

### Local Stack Is Containerized

`infra/docker/docker-compose.yml` defines the local stack:

- backend
- frontend
- frontend-v3
- edge
- postgres
- redis

The backend applies SQL migrations before startup, and Docker healthchecks exist
for the main services.

### Restart Procedure Is Explicit

`docs/LOCAL_ENV_RESTART_PROCEDURE.md` defines the required local restart and
verification flow. It already includes:

- Docker readiness check.
- Compose startup command.
- public edge verification on `http://localhost:3000`.
- Site V3 direct verification on `http://localhost:3001`.
- V1 direct frontend verification on `http://localhost:3002`.
- backend health verification on
  `http://localhost:8000/api/v1/health/live`.
- database query requirement.
- Redis health requirement.
- Windows port-conflict notes.

### Documentation Maintenance Rules Exist

`docs/DOCUMENTATION_MAINTENANCE.md` defines when to update docs, atlas files,
README, archive entries, and operational references. This prevents the common
failure mode where code evolves but future agents read stale plans.

## Current Gaps

### Gap 1: No Single AI Bootstrap Runbook

The required knowledge exists, but it is spread across several files. A fresh AI
can eventually orient itself, but only after reading a broad set of documents.

Impact:

- Higher startup cost for every new Codex Desktop, CLI, VS Code, Claude, Gemini,
  or other AI session.
- Greater chance that an agent reads the wrong document first.
- Greater chance that the agent acts on chat memory or an old prompt instead of
  repository state.

Implemented fix:

- Make the root `README.md` the remembered project entry point.
- Link from root `README.md` to `docs/AI_BOOTSTRAP_RUNBOOK.md` as the detailed
  operational handoff document.

### Gap 2: No Single Doctor Command

Status after WP-BOOT-3: addressed by the initial PowerShell script set under
`scripts/` and the canonical smoke suite definition in
`docs/LOCAL_SMOKE_SUITE.md`.

At audit time, the restart procedure was documented but not yet executable
through one canonical local command.

Impact:

- Each agent may retype compose, curl, database, and Redis checks manually.
- Verification quality varies by session.
- Local environment failures are harder to compare over time.

Implemented fix:

- Added scripts:
  - `scripts/ck-up.ps1`
  - `scripts/ck-down.ps1`
  - `scripts/ck-doctor.ps1`
  - `scripts/ck-test-smoke.ps1`
- Added smoke suite definition:
  - `docs/LOCAL_SMOKE_SUITE.md`

These scripts wrap the existing Docker Compose file and the verification
requirements already defined in `docs/LOCAL_ENV_RESTART_PROCEDURE.md`.

### Gap 3: Local Machine State Is Not Fully Classified

Several local elements exist outside version control or should not be copied
between environments:

- `infra/docker/.env`
- `.local/`
- local Postgres data
- local runtime assets under `var/`
- local Codex state under the user's `~/.codex`
- credentials or generated login notes

Impact:

- A new machine or Codex Desktop session may appear to "miss context" even when
  the repository is correct.
- Agents may confuse local runtime state with product state.
- Sensitive local files could be treated as project inputs.

Recommended fix:

- Document a strict classification:
  - repository source of truth;
  - local reproducible configuration;
  - local generated runtime state;
  - local secrets;
  - AI-client state that must not be considered authoritative.

### Gap 4: Windows And Ubuntu Assumptions Need Reconciliation

`docs/SOURCE_OF_TRUTH.md` states local development on Ubuntu, while Michele's
current active environment is Windows + PowerShell + Docker Desktop.

Impact:

- A fresh AI may choose Linux commands that are inconvenient or wrong for the
  actual machine.
- A CTO reviewer may see ambiguity between target platform, historical baseline,
  and current workstation reality.

Recommended fix:

- Clarify that Dockerized local development is the project invariant.
- Document Windows/PowerShell commands as the active local operating path for
  Michele's workstation.
- Keep Linux/Ubuntu references only where they are truly architectural or
  production-relevant.

### Gap 5: Current Work Pointer Is Still Too Broad

`docs/ACTIVE_OPEN_LOOPS.md` is useful, but a fresh agent still needs to infer
which item is primary, which items are blocked, and which items are background
debt.

Impact:

- The agent may start COINS code before documentation approval.
- The agent may touch Site V3 cleanup before WP5 validation.
- The agent may mix unrelated workstreams in one task.

Recommended fix:

- Add a compact "Current Primary Workstream" section to the bootstrap runbook
  that points to `docs/ACTIVE_OPEN_LOOPS.md` for the full dashboard.

### Gap 6: Bootstrap Success Criteria Are Not Named As A Gate

The required checks exist, but the repository does not yet name a formal
"Definition of Bootstrapped".

Impact:

- Agents can claim the environment is ready after partial verification.
- Delivery reports may omit database, Redis, or route-specific checks.

Recommended fix:

- Adopt the definition in this audit and mirror the short version in
  `docs/AI_BOOTSTRAP_RUNBOOK.md`.

## Recommended Work Packages

### WP-BOOT-1: Bootstrap Audit

Status: this document.

Goal:

- Record current self-bootstrap maturity.
- Identify gaps without touching product code.
- Provide CTO-readable rationale for the bootstrap workstream.

Deliverables:

- `docs/SELF_BOOTSTRAP_AUDIT_2026-05-28.md`

### WP-BOOT-2: AI Bootstrap Runbook

Goal:

- Provide the detailed operational handoff document for a fresh AI or human
  operator, linked from the remembered root `README.md` entry point.

Deliverables:

- Root `README.md` pointer.
- `docs/AI_BOOTSTRAP_RUNBOOK.md`
- Index link from `docs/README.md`

### WP-BOOT-3: Local Doctor Scripts

Status: implemented initial PowerShell version on 2026-05-28.

Goal:

- Convert the existing written restart procedure into repeatable local commands.

Deliverables:

- `scripts/ck-up.ps1`
- `scripts/ck-down.ps1`
- `scripts/ck-doctor.ps1`
- `scripts/ck-test-smoke.ps1`
- `docs/LOCAL_SMOKE_SUITE.md`

Minimum checks:

- Docker daemon available.
- `infra/docker/.env` exists or clear instruction to create it from
  `infra/docker/.env.example`.
- Compose services start.
- public edge returns HTTP 200 on `http://localhost:3000`.
- Site V3 direct renderer returns HTTP 200 on `http://localhost:3001`.
- V1 direct frontend returns HTTP 200 on `http://localhost:3002`.
- backend live health returns HTTP 200.
- backend ready health validates database and Redis when applicable.
- Postgres accepts a real query.
- Redis responds to ping.
- Docker Compose service state is healthy.
- Canonical local smoke suite passes through `scripts/ck-test-smoke.ps1`.

### WP-BOOT-4: README Alignment

Goal:

- Make the root README and docs index point to the runbook without duplicating
  the entire procedure.

Proposed deliverables:

- Root `README.md` short pointer.
- `docs/README.md` required reading addition or dedicated bootstrap section.

### WP-BOOT-5: Codex Desktop / Tool Handoff Notes

Goal:

- Document what can and cannot be assumed when moving between Codex Desktop,
  Codex in VS Code, Codex CLI, and other AI clients.

Core rule:

- Repository documents are authoritative.
- Local AI-client state is helpful but not authoritative.

### WP-BOOT-6: Fresh-Agent Rehearsal

Goal:

- Validate the process by simulating a new agent with no chat memory.

Pass criteria:

- The agent reads the runbook.
- The agent identifies the required first-reading set.
- The agent starts or verifies the stack.
- The agent identifies the current primary workstream.
- The agent refuses or blocks implementation work that is gated by missing
  approval.

## CTO Review Questions

1. Should the root `README.md` remain the remembered first entry point for every
   fresh AI session, with `docs/AI_BOOTSTRAP_RUNBOOK.md` as the operational
   handoff document it links to?
2. Should Windows/PowerShell be documented as the current official local path
   for Michele's workstation while keeping Docker as the cross-platform
   invariant?
3. Should local doctor scripts be mandatory before every delivery that touches
   localhost behavior?
4. Should `docs/ACTIVE_OPEN_LOOPS.md` gain a one-line "Current Primary
   Workstream" field, or should that pointer live only in the bootstrap runbook?
5. Should Codex Desktop handoff explicitly ignore previous `~/.codex` sessions
   unless the user asks to inspect them?

## Recommended CTO Decision

WP-BOOT-2 and the initial WP-BOOT-3 script set are now in place and should be
reviewed as process hardening.

Any WP-BOOT-3 follow-up should stay limited to local tooling. It must not change
backend, frontend, wallet, ledger, game runtime, Site V3 behavior, or production
configuration.

Do not mix this bootstrap workstream with Site V3 WP5, COINS, Mines QA, or
financial/replay follow-ups.
