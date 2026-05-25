Status: SUPERSEDED
Last meaningful update: 2026-05-25 (superseded same day by broader WP)
Superseded by:
`docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md`
con CTO review in
`docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md`

# Prompt Codex - WP-FINANCE-REPLAY-ACCOUNT-REGISTRY (SUPERSEDED)

> **NOTA SCOPE-RECONCILIATION (CTO Claude, 2026-05-25 sera):**
>
> Questo prompt è stato creato come WP COINS-specific subset, ma sovrappone
> il WP platform più ampio `WP-FINANCE-REPLAY-REGISTRY-RETENTION` analizzato
> in `docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md`.
>
> Il WP platform copre TUTTO ciò che fa questo prompt + (a) settlement
> taxonomy 7-value, (b) forward-only metadata contract, (c) Mines admin
> replay parity, (d) BOXE wallet_type bug, (e) backend auto-settlement
> registry, (f) retention policy doc, (g) reconciliation report.
>
> **Usa quello, non questo.**
>
> Il contesto sotto rimane utile come visione COINS-centrica e per non
> perdere i puntatori `file:line` raccolti per Rule 18.

Workstream prerequisito a COINS. Chiude il debito hardcoded multi-game in
account history, admin finance, replay routing.

---

## Prompt da incollare in Codex

```
You are CTO assistant.

Parte A: validate approach, counter-propose if you see a gap.
Parte B: execution starts only after my approval of Parte A.

=== CONTEXT (current state, 2026-05-25) ===

Branch main. Mines, BOXE, HI-LO sono i 3 giochi proprietari deliverati. COINS
è in Fase 0 (decisioni product chiuse stasera, vedi
docs/games/coins/COINS_OPEN_QUESTIONS_2026-05-25.md).

Michele (product owner) ha imposto: architettura pulita, nessun debito tecnico
sopravvive all'aggiunta di COINS. Riferimento: feedback memory
"clean architecture priority" + Rule 18 NEW_GAME_INTEGRATION_PLAYBOOK.md.

=== DEBITO DA CHIUDERE ===

Rule 18 playbook (sezione 13.1) dice:

  "HI-LO proved that a third explicit game branch can be an acceptable bridge,
  but it also marks the expiry point for that pattern. After Mines, BOXE and
  HI-LO, new code must not add a fourth explicit game branch in account
  history, admin finance replay, launch routing, title-editor registration or
  runtime config selection when a registry/adapter can represent the same
  decision.

  Required action before game 4:
  - audit every `mines` / `boxe` / `hi_lo` conditional in player account,
    admin finance, replay, launch and title-editor code;
  - classify each as `keep game-specific`, `convert to registry now`, or
    `accepted temporary bridge`;
  - do not implement the next game by appending `else if new_game`."

Riferimento ulteriore:
docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md descrive il contratto
multi-game finance/replay/reporting. ACTIVE_OPEN_LOOPS.md ha riga P0 "Finance
menu giochi / replay backoffice" che traccia il debito esistente.

=== AREE DA AUDITARE (almeno queste, espandere se trovi altro) ===

Backend:
- backend/app/modules/platform/rounds/ — game-code dispatch
- backend/app/modules/platform/game_launch/ — launch routing
- backend/app/modules/platform/access_sessions/ — table session lifecycle
- backend/app/modules/players/account/history.py o equivalente — player account history
- backend/app/modules/platform/finance/ — admin finance drilldown
- backend/app/modules/games/<game>/replay.py — per ogni gioco
- backend/app/api/routes/admin.py + responses.py — endpoint routing

Frontend:
- frontend/app/ui/account/ — player account history viewer
- frontend/app/ui/admin/finance/ — admin finance drilldown
- frontend/app/ui/game-runtime/ — launch routing client-side
- frontend/app/ui/title-editor/ — engine registration
- frontend/app/ui/<game>/<game>-replay-viewer.tsx — per ogni gioco

Pattern da cercare con rg:
- rg "if.*game.*==.*[\"']mines[\"']"
- rg "if.*game.*==.*[\"']boxe[\"']"
- rg "if.*game.*==.*[\"']hi_lo[\"']" o "hilo"
- rg "engine_code.*==.*[\"']mines[\"']" e varianti
- rg "match.*case.*[\"']mines[\"']"
- rg "ALLOWED_GAME_CODES" e simili whitelist
- rg "elif.*game" backend
- rg "engineCode === " frontend

=== Parte A - OUTPUT ATTESO ===

Produrre un documento di audit in
docs/games/coins/PLATFORM_REGISTRY_AUDIT_<DATE>.md con:

1. **Inventario hardcoded conditionals.** Tabella file:line + tipo (account
   history / admin finance / replay routing / launch / title-editor / altro)
   + game branch presenti (mines, boxe, hi_lo) + se esiste già
   registry/adapter parziale.

2. **Classificazione per ogni voce:**
   - `keep game-specific` (con motivazione - es. math interno gioco)
   - `convert to registry now` (debito Rule 18, da risolvere)
   - `accepted temporary bridge` (con motivazione esplicita - non default)

3. **Piano di refactor proposto** per le voci `convert to registry now`:
   - quale registry creare (es. `GameRoundRendererRegistry`,
     `GameReplayAdapterRegistry`, `GameAccountHistoryRegistry`,
     `GameFinanceDrilldownRegistry`)
   - dove vive il registry (backend/frontend)
   - signature dell'adapter game-specific
   - come Mines/BOXE/HI-LO si "registrano" senza if hardcoded
   - test contract necessari per impedire regressione (es. test che fallisce
     se un nuovo gioco viene aggiunto via if-branch invece che registrazione)

4. **Rischi e blind spot identificati.** Counter-proposal se ritieni che il
   piano sopra abbia gap (es. retention policy che dipende dal game-code,
   migration data esistenti, ecc.).

5. **Stop-and-Ask** se trovi:
   - hardcoded conditionals che dipendono da product decisions non chiuse
   - assunzioni implicite sulla shape dei payload per gioco
   - finance/ledger invariants che il refactor potrebbe toccare

NON eseguire codice in Parte A. Solo audit e piano.

=== Parte B - SOLO DOPO APPROVAZIONE CTO ===

Implementazione del refactor secondo piano Parte A approvato:
- creare i registry
- migrare Mines/BOXE/HI-LO a registrazione tramite adapter
- aggiungere contract test che fallisce se un nuovo gioco è aggiunto via
  if-branch
- aggiornare docs/CODE_ARCHITECTURE_MERMAID_MAP_2026-05-22.md nello stesso PR
- aggiornare docs/GAME_FINANCE_REPLAY_REPORTING_CONTRACT_2026-05-24.md per
  riflettere il nuovo pattern
- aggiornare ACTIVE_OPEN_LOOPS.md riga P0 "Finance menu giochi / replay
  backoffice" come chiusa

=== CAPABILITY MATRIX ATTESA (Parte B) ===

| Capability | DB | Backend | API payload | Admin UI | Player UI | CSS | Test | Docs | Status | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Game registry pattern - account history | n/a | REFACTOR | unchanged | n/a | REFACTOR | n/a | NEW | UPDATE | TBD | |
| Game registry pattern - admin finance | n/a | REFACTOR | unchanged | REFACTOR | n/a | n/a | NEW | UPDATE | TBD | |
| Game registry pattern - replay routing | n/a | REFACTOR | unchanged | REFACTOR | REFACTOR | n/a | NEW | UPDATE | TBD | |
| Contract test "no fourth if-branch" | n/a | n/a | n/a | n/a | n/a | n/a | NEW | UPDATE | TBD | |

=== VINCOLI HARD ===

- Mines, BOXE, HI-LO devono continuare a funzionare identici post-refactor
  (zero behavior change visibile, solo struttura interna). Smoke browser deve
  restare verde sui 3 giochi.
- Nessuna modifica a wallet/ledger/RNG/payout/fairness/math invariants.
- I round già esistenti in DB devono restare leggibili (no migration
  distruttive).

=== INIZIA CON Parte A ===

Esegui l'audit e produci il documento di piano. Stop-and-Ask quando incontri
un gap che richiede decisione CTO o product owner.
```
