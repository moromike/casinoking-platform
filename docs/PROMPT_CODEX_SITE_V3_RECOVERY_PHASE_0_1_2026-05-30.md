Status: ACTIVE
Last meaningful update: 2026-05-30

# Prompt Codex — Site V3 Recovery, Phase 0 + Phase 1 (ONLY)

Contesto: la run precedente ha causato regressioni cross-cutting (incident
inventory in `docs/SITE_V3_CTO_INCIDENT_AND_HANDOFF_REPORT_2026-05-30.md`,
INC-01..INC-11). Il CTO ha ratificato la tua diagnosi e ha scritto il piano in
`docs/SITE_V3_RECOVERY_PLAN_2026-05-30.md`. Direzione decisa: **A-then-B**.

Questo prompt autorizza SOLO Phase 1. NIENTE fix visivo, NIENTE CSS,
NIENTE feature finche' non ho approvato l'output.

## Phase 0 — Safety & Freeze — GIA' FATTA dal CTO

- Backup non distruttivo creato: branch `backup/site-v3-codex-run-2026-05-30`,
  commit `6141c17` (commit + intero working tree). Working tree intatto.
- FREEZE dichiarato: nessun lavoro feature, nessun GMP-5C, nessun restyle.
- DECISIONE CTO sul backend: le modifiche backend nel working tree
  (`boxe/service.py`, `boxe/platform_client.py`, `game_launch/service.py`,
  `routes/boxe.py`, `routes/demo.py`) NON vanno revertate. Sono lavoro GMP
  coerente (site_code, adapter in-process, launch-token ownership / fix INC-10),
  NON game logic. Si TENGONO come fondamento della direzione B. In Phase 1
  vanno solo isolate concettualmente (mappate come "batch GMP backend"), non
  toccate.

## Phase 1 — Baseline parity inventory (audit, NO fix)

Baseline di verita' = rendering di `main` (il vecchio frontend serviva :3000 su
main; i giochi/admin in V3 sono re-implementazioni nuove di questo branch).

1. In un worktree separato basato su `main`, fai partire lo stack e cattura
   screenshot baseline di: Mines, HI-LO, BOXE (player desktop + mobile),
   Finance (filtri + ledger report + bank session report + round detail),
   admin shell, login/account.
2. Dal branch corrente cattura gli stessi screenshot nello stato attuale.
3. Produci un inventario regressioni SIDE-BY-SIDE per superficie, con:
   - superficie | baseline (main) | attuale (branch) | tipo regressione
     (container / contenuto / funzionale) | file CSS/TSX sospetti | severita';
   - per il CSS: elenca i selettori GLOBALI introdotti in
     `frontend-v3/app/globals.css` e in `game-runtime.css` che fanno match su
     DOM di giochi o finanziario (questa e' la mappa della contaminazione).
4. Mappa quali sezioni admin passano per `CasinoKingConsole` con wrapper
   `site-v3-admin-page admin-console-page` (INC-11): elenco esplicito delle
   superfici a rischio.

Output Phase 1 atteso (documento, non codice):
- `docs/SITE_V3_RECOVERY_PARITY_INVENTORY_2026-05-30.md` con la tabella
  side-by-side e gli screenshot referenziati negli `artifacts/`;
- la lista dei selettori CSS globali contaminanti;
- la lista delle sezioni admin investite dal wrapper.

## Divieti (validi in Phase 0 e 1)
- NON toccare wallet/ledger/payout/RNG/replay logic.
- NON modificare CSS o UI dei giochi in questa fase (solo audit).
- NON re-inventare UI: la parita' sara' verso baseline `main`, non un nuovo
  design.
- NON usare l'account admin personale di Michele per gli smoke.
- NON procedere a Phase 2 (CSS isolation) finche' non approvo l'inventario.

## Comunicazione di consegna
Report esplicito: cosa fatto / branch+hash backup / esito gate backend vuoto /
file prodotti / cosa NON fatto perche' fuori scope / next step proposto.
Niente "fatto" ambiguo: stato per ogni superficie.
