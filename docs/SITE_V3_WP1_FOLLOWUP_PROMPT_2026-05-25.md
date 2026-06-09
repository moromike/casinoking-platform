Status: ACTIVE
Last meaningful update: 2026-05-25

# Site V3 - WP1 Follow-up Prompt per Codex

Prompt Codex per chiudere i 3 task post-decisioni CTO Site V3.

---

## PROMPT

Site V3 - WP1 follow-up post-approvazione CTO.

Contesto: CTO ha approvato Site V3 con 8 decisioni lockate. 3 task doc-only indipendenti prima di WP2 backend. Niente codice runtime in questo WP.

DECISIONI LOCKATE 2026-05-25 (Michele approved):

1. Parallel cleanup + Site V3 doc; codice WP2 parte dopo merge cleanup.
2. `frontend-v3/` nuova; `frontend-v2/` lab cestinato in WP6.
3. Nuove tabelle `site_v3_pages`, `site_v3_page_versions`, `site_v3_modules`; `cms_v2_*` dormienti.
4. Moduli MVP (7): `global_header`, `hero_banner`, `game_grid`, `featured_game`, `promo_band`, `rich_text_safe`, `global_footer`.
5. i18n: model con locale da subito; content MVP solo IT.
6. Login/account/cashier restano V1 con link/route.
7. Versioning: snapshot published + history list in admin; revert UI Fase 2.
8. Audit: riuso `admin_audit_events` con `source=site_v3`; no tabella dedicata.

TASK A - Aggiornare i 6 doc SITE_V3 (tutti sotto `docs/SITE_V3_*_2026-05-25.md`):

- in ogni tabella "Decisioni Aperte" / "Stop-Before-Code" / "Decision Brief Aperto", marcare le decisioni lockate con la scelta scelta (default Recommended) e rimuovere le opzioni alternative;
- aggiungere riga "Decisione lockata 2026-05-25 - Michele approved" sotto ogni tabella decisioni;
- aggiornare `SITE_V3_PRODUCT_CONTRACT_2026-05-25.md` sezione 8 e 9 per riflettere chiusura;
- aggiornare `SITE_V3_LIFECYCLE_API_SECURITY_PLAN_2026-05-25.md` per fissare snapshot+history (no revert UI), `site_v3_*` tabelle scelte, riuso `admin_audit_events`;
- aggiornare `SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md` per nominare WP1-FOLLOWUP come questo task e WP2 con stop-before-code Parte A;
- aggiornare `SITE_V3_SCOPE_AND_ARCHITECTURE_PLAN_2026-05-25.md` sezione 9 Open Questions chiudendole.

TASK B - .gitignore:

- aggiungere riga `frontend-v2/` con commento "Site V3 lab temporaneo, cestinato in WP6";
- aggiungere riga `frontend-v3/` con commento "Site V3 public renderer - WP4 ownership";
- assicurarsi che `.next/`, `node_modules/`, `out/`, `dist/` sotto qualsiasi sottocartella siano gia' coperti.

TASK C - docs/README.md + ACTIVE_OPEN_LOOPS.md:

- in `docs/README.md` aggiungere sezione "Site V3" dopo le sezioni esistenti, con elenco dei 6 doc baseline + questo prompt + link a `project_site_v3` memoria;
- in tabella "Da Fare Subito" aggiungere riga: `2026-05-25 | Site V3 - WP2 Backend MVP | brief Parte A approach da CTO | docs/SITE_V3_IMPLEMENTATION_WP_ROADMAP_2026-05-25.md`;
- in `docs/ACTIVE_OPEN_LOOPS.md` aggiungere Site V3 come iniziativa attiva con stato "WP1-FOLLOWUP in corso, WP2 in attesa di brief Parte A".

OUTPUT:

- branch `feature/site-v3-wp1-followup`;
- 3 commit separati (uno per task), messaggi `docs(site-v3): ...`;
- delivery report con: file toccati per task, conferma che V1 e codice runtime non sono stati toccati, conferma che `frontend-v2/` non e' stato modificato (solo gitignorato).

STOP-BEFORE-CODE:

- NON aprire WP2 backend MVP;
- NON creare tabelle SQL `site_v3_*`;
- NON creare route backend `/admin/site-v3/*` o `/site-v3/*`;
- NON modificare `cms_v2_*`;
- aspetta che CTO consegni il brief Parte A per WP2 prima di scrivere codice runtime.

Effort stimato: 2-3 prompt totale per i 3 task.

---

## Note per CTO

Questo prompt e' salvato qui per persistenza (session checkpoint protocol). Da consegnare a Codex nel prossimo turno di Michele.

Quando Codex consegna i 3 task, prossimo step: brief Parte A per WP2 Backend MVP che include:

- DDL completo `site_v3_pages` / `site_v3_page_versions` / `site_v3_modules`;
- API surface puntuale admin + public con URL exact, payload shape, error codes `SITEV3.*`;
- piano test/gate.
