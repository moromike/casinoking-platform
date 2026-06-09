# CTO Handoff Brief — Cross-Game Bonifica (2026-06-06)

Subentri come **CTO ad interim** (Claude è ai limiti). Tu PIANIFICHI, DECIDI, GATI ragionando sull'evidenza. **Esecutore = KIMI** (single-chat). **Verifier read-only = Gemini** (modello diverso). Scrivi i prompt, gati le consegne, tieni l'ordine. Non eseguire codice se puoi delegarlo a KIMI.

## REGOLE DURE (non negoziabili — Michele le ha ripetute molte volte)
1. **Perfezione architetturale / scopo ACCADEMICO**: la pulizia È l'obiettivo. MAI proporre skip/defer di refactor pulito per ROI/effort/rischio. Il rischio si mitiga con **gate HARD zero-diff**, non si evita.
2. Zero divergenze cross-game; mai produzione con debito architetturale.
3. **DB disposable** (local/pre-beta): migration/rebuild OK; mai scegliere la soluzione meno pulita "per non rompere il DB".
4. Decisioni **tecniche/architetturali/processo: le DECIDI TU** per i principi noti e le comunichi. A Michele chiedi SOLO product/business/priorità/visual-desktop (è non-developer; non scaricargli scelte tecniche).
5. Michele valida **solo DESKTOP**. Il **MOBILE è compito tuo** (screenshot Playwright viewport mobile + reasoning).
6. **Money-flow**: prove-before-remove; il demo non tocca MAI `platform_rounds`/ledger reale; `platform_rounds` single-writer (solo `platform/rounds/service.py`); invarianti dure + evidenza nel gate.
7. **ORDINE, no LIFO**: ogni nuovo problema → triage ragionato nella master schedule; di' a Michele dove/perché.
8. **Clausola forzante evidenza in OGNI prompt esecutore**: "esplicita ciascuna evidenza nella risposta finale + auto-attestazione + se manca anche una evidenza = task FAILED a priori, non dire done". (Non si possono iniettare addendum a task in volo.)
9. **GATE = ragiona sull'evidenza, NON fidarti dei riepiloghi.** Verifica i claim "pre-esistente" (prova che fosse rosso PRIMA, es. run su branch base). Smaschera vacuous assert (`==0` non `>=0`) e mislabel: KIMI ha etichettato "pre-esistente" cose introdotte dal WP più volte (DIV-04, DIV-02).
10. **Verifier di modello DIVERSO (Gemini) read-only** sulle invarianti money dopo refactor grossi — ha già trovato 1 bug reale (DIV-06c).
11. Termini tecnici inglesi corretti (Michele impara). Niente "hai ragione" riflesso: sbaglia meno, correzioni asciutte.

## DOVE STA TUTTO
- **Master schedule (hub):** `docs/CROSS_GAME_BONIFICA_PROGRAM_2026-06-04.md` (tienila aggiornata ad ogni gate)
- Audit: `docs/CROSS_GAME_PARITY_AUDIT_2026-06-04.md` (backend) · `docs/CROSS_GAME_FRONTEND_PARITY_AUDIT_2026-06-05.md`
- Playbook v3.2 (learnings §16.2bis/16.2ter): `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`
- Branch: `feature/site-v3-cms-ia-cleanup`. Sub-branch: `feature/div-10-platform-adapter-unification` (KIMI DIV-10), `feature/test-residuals-fix` (fix test).
- Stack locale: `.\scripts\ck-up.ps1` (Docker). NB porta 5432 può essere occupata dal PostgreSQL nativo Windows (admin per fermarlo).

## FATTO (gatato + committato)
B3, DIV-01, DIV-03, DIV-04, DIV-05, DIV-06, DIV-06b, DIV-02, DIV-07, DIV-08, DIV-09 (merged 1ed469c). Frontend: F1a, F1b, F04, F05, F07, F08, F10. CLEANUP-1, CLEANUP-2 B1, item 10. Audit + Playbook v3.2.

## IN VOLO — DA GATARE (le 3 risposte in arrivo)
1. **KIMI DIV-10 Part-B** (typed adapter Mines/HI-LO, branch `feature/div-10-platform-adapter-unification`). Gate: gruppi verdi (Mines 242 + HI-LO + BOXE non-regression); **UNICI fail ammessi = gli 8 noti pre-esistenti** (1 integration `test_mines_recent_sessions_history` access-session 422 + 7 browser-smoke Playwright/dev-tools); **zero test-mod**; diff strutturale (adapter creati, `PlatformGameClient` custom rimosso, firme `round_gateway` invariate). Se solo gli 8 → **merge** in `feature/site-v3-cms-ia-cleanup`. Se altri fail → regressione, stop.
2. **Codex fix test-residuals** (branch `feature/test-residuals-fix`, dominio `tests/` only). Gate: 8 fail PRIMA/DOPO; NON deve aver toccato codice prodotto; NON mergiare ora → merge DOPO DIV-10.
3. **Gemini reachability DIV-06c**: ATTIVO o LATENTE del bug admin force-close → setta gravità.

## BUG MONEY-INTEGRITY APERTO → DIV-06c (PRIMA di B6)
`backend/app/modules/admin/session_force_close.py` fa `UPDATE mines_game_rounds` HARDCODED + `force_cancel_platform_round` → su round BOXE/HI-LO: `platform_rounds`=cancelled ma game-round resta `active` (stato incoerente, soldi invertiti). **Fix:** chiusura game-round per `game_code` via repository del gioco corretto. Money → invarianti dure + gate.

## ORDINE RIMANENTE
DIV-10 merge → **8b** (demo ANONIMO per tutti: estendere a BOXE/HI-LO, identità `anonymous_id`; design in `plans/`; NB il demo-no-login esiste già ovunque, 8b è cleanup dell'IDENTITÀ: BOXE/HI-LO oggi creano un utente throwaway in `users` via `/auth/demo`, target = `anonymous_id` come Mines) → **DIV-06c** (money) → **B2** (velocità/stabilità suite; diagnosi in CLEANUP-2 Part-A: split marker + xdist + DB-per-worker) → **B6** (regression finale real+demo, suite a GRUPPI perché intera va in timeout) → **B7** (chiusura Playbook, già v3.2). Poi: merge to main (decisione Michele), COINS gioco 4 (gate documentale 6 doc, niente codice prima), parcheggiati (redesign sito, externalization, production readiness, retention replay back-office, audio HI-LO).

## DECISIONI PRODUCT GIÀ PRESE (non ri-chiedere)
- Demo **anonimo (no-login) per tutti** i giochi.
- Decimali: **backend 6dp, frontend 2dp cliente**, bet input decimale.
- Audio HI-LO: **parcheggiato** (eventuale AI-gen).
