Status: ACTIVE
Last meaningful update: 2026-05-17

# Session Recovery Engine Design

## 1. Purpose

This document defines the target policy for recovering interrupted real-money game
sessions before BOXE reuses the same platform shell. The immediate resume bug for
Mines variants is handled separately by RESUME-FIX-1. This design covers the
remaining cases where a session is genuinely not resumable: timeout, device race,
backend inconsistency, wallet refusal during recovery, and future bonus-round
obligations.

The product rule is intentionally player-protective: the system must not make a
player lose money because the platform failed to recover state. When automatic
resolution is possible, prefer automatic resolution over losing the session. When
automatic resolution is not possible, quarantine the session in a visible
backoffice queue instead of hiding the problem.

## 2. Fixed Product Decisions

These decisions are already made and are not reopened by this design.

- Auto-resolve is preferred to "lost session" whenever the state can be resolved
  safely and idempotently.
- Every auto-resolve must be visible to the player in the statement with an
  explicit label, for example `Cashout automatico (sessione interrotta)`.
- Bonus rounds remaining are simulated with the same fair RNG rules as the real
  game and the resulting net outcome is credited. There is no
  `pending_obligations` or IOU table in this version.
- Non auto-resolvable cases go to a visible admin quarantine queue.
- Wallet, ledger, and round state consistency is more important than hiding
  operational complexity.

## 3. Existing Baseline

The current code already provides a partial recovery baseline:

- `backend/app/modules/platform/access_sessions/service.py` times out inactive
  access sessions after `ACCESS_SESSION_TIMEOUT`.
- Access-session close and timeout cascade into table-session close.
- Active Mines rounds are auto-cashed-out during access-session close/timeout via
  `_auto_cashout_active_mines_round`.
- The timeout cashout uses a deterministic idempotency key generated from
  `access_session_id` and `round_id`.
- Platform settlement goes through the normal double-entry ledger path in
  `backend/app/modules/platform/rounds/service.py`.
- RESUME-FIX-1 makes resume use the saved variant `title_code`, so variant
  sessions can be recovered in real mode instead of falling back to the master
  title.

The baseline is useful but not complete. It does not yet expose a dedicated
recovery log, a quarantine queue, future bonus simulation, or explicit player
statement labels for every auto-resolution type.

## 4. Scenario Matrix

| # | Scenario | Session state | Auto-action | Wallet effect | Reporting |
| --- | --- | --- | --- | --- | --- |
| 1 | Clean boot, no active session | clean | None | None | n/a |
| 2 | Active session, safe reveals, multiplier greater than 1 | safe-cashoutable | Auto cashout at current multiplier | Credit win | `Cashout automatico (sessione interrotta)` |
| 3 | Active session, bet placed, zero reveals | refundable | Refund bet | Reverse or compensate the initial debit | `Bet rimborsato (sessione annullata)` |
| 4 | Loss already committed but client missed the response | last action = loss | Confirm loss | None; initial bet remains consumed | `Esito loss confermato` |
| 5 | Bonus with free rounds remaining | bonus_rounds_remaining > 0 | Auto-play remaining rounds with fair RNG, then credit net result | Credit net outcome | `Round simulati dal sistema` plus simulated round list |
| 6 | Multi-device race | conflict | Winning device continues; losing device is rejected | None | `Sessione attiva altrove` |
| 7 | Session expired by inactivity | ambiguous | Resolve as #2 or #3 based on current round state | Depends on state | `Sessione scaduta - risolta in automatico` |
| 8 | DB inconsistency | corrupted | Quarantine and alert operations | No final wallet mutation until manual review | Critical log plus manual review ticket |
| 9 | Wallet refuses during auto-resolve | retry failed | Retry idempotently N times, then quarantine | No final wallet mutation until success/manual review | Critical log plus visible admin queue |
| 10 | Recovery action retried after partial success | idempotent replay | Return existing recovery result | No duplicate debit or credit | Original recovery label reused |
| 11 | Launch token or access context invalid but active round exists | auth/context mismatch | Do not start a new round; resolve or quarantine the existing round | Depends on state | Safety overlay plus recovery log |

## 5. Invariants

- Wallet and ledger remain consistent: no double-credit, no silent loss, no
  dangling active financial exposure.
- Every recovery operation is idempotent and replay-safe through a deterministic
  idempotency key.
- Recovery never mutates RNG/fairness history for already-decided outcomes.
- Bonus simulation, when implemented, must use the same fair RNG contract as the
  original game mode and must be auditable.
- Every quarantine item is visible in backoffice, assigned a status, and
  traceable to the player, game, title, access session, table session, and round.
- Player reporting must show the money movement and the recovery label.
- Recovery must not introduce hidden admin-only balance corrections.

## 6. Future Transaction Kinds

These names are the proposed future contract for recovery-ledger reporting. The
exact schema location is still an implementation decision: either a new
`transaction_kind` field or a typed value inside `ledger_transactions.metadata_json`.
The names themselves should remain stable.

| Transaction kind | Purpose |
| --- | --- |
| `auto_recovery_cashout` | Automatic cashout of a recoverable active round. |
| `auto_recovery_refund` | Automatic refund of a bet that never produced a reveal. |
| `auto_recovery_loss_confirmed` | Explicit confirmation that a committed loss was recovered as loss, with no additional wallet movement. |
| `auto_simulated_bonus_round` | Wallet movement produced by simulated remaining bonus rounds. |
| `session_recovery_quarantine` | Non-final accounting marker or audit marker for sessions that require manual review. |

If implementation chooses metadata-only first, the player statement and finance
drilldown must still expose these exact values as user-readable categories.

## 7. Future Capability Matrix

| Capability | DB | Backend | API | Admin | Player | CSS | Test | Docs | Status |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Session Recovery Engine - detection | `session_recovery_log` | Resolver service | webhook or poll | Quarantine queue UI | n/a | n/a | Unit + integration | This doc | DESIGNED |
| Session Recovery Engine - auto cashout | n/a | Idempotent cashout resolver | n/a | Log entry | Statement entry | n/a | Integration | This doc | DESIGNED |
| Session Recovery Engine - auto refund | n/a | Idempotent refund resolver | n/a | Log entry | Statement entry | n/a | Integration | This doc | DESIGNED |
| Session Recovery Engine - bonus simulation | `bonus_simulation_log` | RNG simulator | n/a | Log entry + simulated rounds list | Statement entry | n/a | Integration + fairness contract | This doc | DESIGNED |
| Session Recovery Engine - quarantine queue | `session_quarantine_queue` | Listing endpoint | `GET /admin/session-quarantine` | Admin queue panel | n/a | TBD | Integration | This doc | DESIGNED |
| Session Recovery Engine - player reporting | n/a | Statement serializer | Existing statement endpoints | Finance drilldown link | Statement labels | TBD | Integration + snapshot | This doc | DESIGNED |

## 8. Dependencies And Prerequisites

- Platform rounds tracking is available through `platform_rounds`.
- The double-entry ledger is the accounting source of truth.
- Access sessions and table sessions already persist `game_code`, `title_code`,
  `site_code`, status, close reason, and timeout lifecycle.
- Mines runtime resume flow is corrected by RESUME-FIX-1, including variant
  `title_code` recovery.
- Current access-session timeout close already demonstrates an idempotent
  auto-cashout path. The future engine should generalize this pattern instead of
  duplicating it.
- Admin audit log exists for operator-visible changes, but a dedicated quarantine
  workflow still needs schema and UI.

Prerequisites still missing for implementation:

- Dedicated recovery log schema.
- Dedicated quarantine queue schema and admin panel.
- Statement display contract for recovery labels.
- Fair RNG simulation contract for bonus residues.
- Exact retry/backoff policy for wallet refusal.

## 9. Future Implementation Effort

Prompt estimates are deliberately expressed as execution prompts, not calendar
days.

| Capability | Brief | Execution | Gate | Stop-and-Ask risk | Total estimate |
| --- | --- | --- | --- | --- | --- |
| Detection + `session_recovery_log` | 1 | 1-2 | 1 | Medium: schema fields | 3-5 |
| Auto cashout generalization | 1 | 1 | 1 | Low: current timeout path exists | 3 |
| Auto refund | 1 | 1-2 | 1 | Medium: refund ledger contract | 3-5 |
| Bonus simulation | 1 | 2-3 | 1 | High: fairness and reporting | 5-7 |
| Quarantine queue | 1 | 2 | 1 | Medium: admin workflow | 4 |
| Player statement labels | 1 | 1-2 | 1 | Medium: copy/reporting | 3-5 |

## 10. Open Decisions For Implementation

These are intentionally not decided here.

- Timeout threshold for scenario #7: how many minutes without ping before a
  session is considered expired.
- Retry count and backoff policy for scenario #9.
- Exact `session_recovery_log` fields: minimum operational log versus richer
  audit payload.
- Whether transaction kind becomes a first-class column or remains a typed value
  in `metadata_json` for the first implementation.
- Quarantine operator permissions and SLA.

## 11. Implementation Guardrails

- Do not change wallet, ledger, RNG, payout, fairness, or math behavior as part
  of documentation-only design work.
- Any implementation PR must include the capability matrix required by
  `docs/TASK_EXECUTION_GUARDRAILS.md`.
- Any payload extension must receive CTO Stop-and-Ask before implementation,
  even if additive.
- Any schema change requires migration up/down testing before merge.
- Any auto-resolve path must be tested for idempotent retry and concurrent
  cashout/reveal/timeout races.

