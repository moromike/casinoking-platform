# CasinoKing AI Entry Point

Claude agents working on this repository must use the shared project guide:

1. Read `docs/SOURCE_OF_TRUTH.md`.
2. Read `docs/TASK_EXECUTION_GUARDRAILS.md`.
3. Read `docs/README.md`.
4. Read `docs/DOCUMENTATION_MAINTENANCE.md`.
5. Read `AGENTS.md` for repository rules and non-negotiable constraints.
6. Read the architecture atlas or operational document for the domain being changed.

Use proportional reading: read the core documents first, then only the domain documents needed for the task. Do not read the whole documentation set for simple status, commit, or push tasks.

When reporting onboarding or task preparation, distinguish files actually read from files only discovered or mentioned. Do not claim a file was read if it was only listed or inferred.

Before closing any task, explicitly state whether documentation needed updates according to `docs/DOCUMENTATION_MAINTENANCE.md`.

Do not treat this file as an independent source of truth. It is only a pointer to the shared documentation system.

## Local dev shortcuts

When the user asks in natural language to launch a local dev tool — e.g. "lancia antigravity" / "avvia agy", or "lancia codex" / "lancia codex cli" — follow the instructions in `docs/LOCAL_DEV_SHORTCUTS.md` to open that tool in a new GUI terminal window the user can type into.
