Status: ACTIVE
Last meaningful update: 2026-05-30

# Prompt Codex — Site V3 Recovery, Phase 3A (stabilizzazione regressioni)

Michele ha validato su :3000 dopo Phase 2B. Tre regressioni RESIDUE introdotte
dal recovery stesso. Diagnosi CTO completa in
`docs/SITE_V3_RECOVERY_PHASE3_RESIDUAL_ANALYSIS_2026-05-30.md`.

Questo prompt = SOLO stabilizzazione (R1, R2, R3) + verifica replay. NIENTE
module building (e' Phase 3B separata). NIENTE re-design: ripristino verso
baseline, non reinvenzione.

## Decisioni CTO (non ridiscuterle)
- Baseline player pubblico = stato backup `6141c17` (pre-recovery, era accettabile).
- Baseline admin/finance/giochi = `main` (gia' verificata dal CTO).
- Game logic / RNG / payout / board / reveal / backend GMP: INTOCCABILI, 0 diff.

## R2 — Giochi "non ottimizzati" / finestra piu' grande dello schermo (FAI PRIMA, e' chirurgico)

Causa: nel Batch 2 sono state rimosse da mines/boxe/hi-lo standalone le righe che
applicavano l'ottimizzazione layout iframe. Le regole CSS `.mines-page-shell-embedded`
/ `.mines-product-shell-embedded` (e equivalenti boxe/hi-lo) ESISTONO ancora ma non
vengono piu' applicate.

Fix: ri-aggiungi, SOLO quando `isEmbeddedView`, le classi shell embedded a
page-shell e product-shell nei 3 standalone:
- `frontend-v3/app/ui/mines/mines-standalone.tsx`
- `frontend-v3/app/ui/boxe/boxe-standalone.tsx`
- `frontend-v3/app/ui/hi-lo/hi-lo-standalone.tsx`
VINCOLO: NON re-introdurre l'host topbar/chrome rimosso nel Batch 2. NON toccare
la X nativa (deve restare visibile). Solo le classi `*-page-shell-embedded` /
`*-product-shell-embedded`.
Verifica: gioco lanciato da :3000 sta DENTRO lo schermo, no scrollbar, layout
compatto come baseline, X presente.

## R1 — Login/header pubblico player rotti

Causa: il revert Batch 1 non ha ri-aggiunto le regole player pubbliche in
globals.css: `site-v3-player-panel` (7->0), `site-v3-player-form` (4->0),
`site-v3-text-link` (1->0), e ~85 regole `site-v3-player*` perse (210->125). I
componenti le usano ancora.

Fix: ri-porta dal backup `6141c17:frontend-v3/app/globals.css` SOLO le regole
player pubbliche mancanti (login panel/form/field-grid/form-actions, header
pubblico, text-link, e il delta site-v3-player necessario), sotto root player
scoped. NON ri-aggiungere stile admin/CMS (gia' presente). NON re-inventare.
Verifica: login + register + account player a parita' col backup pre-recovery.

## R3 — Admin polish (spacing/bottoni)

Sintomo: admin con spacing/posizionamento bottoni grezzi; builder Site V3 con
Publish/Validate/Archive mal posizionati.

Fix: pass di rifinitura CSS SCOPED (`.ck-admin-legacy-page` / `.site-v3-cms-admin-page`):
allineamento bottoni, densita', spazi. NON re-design, NON nuove sezioni/bottoni.
Riferimento = layout pre-disastro dove esisteva.
Cattura screenshot di: menu admin, Finance, Player admin, builder Site V3
(action bar), Module Studio.

## Replay — VERIFICA esplicita (Michele se li aspetta perfetti, non testati)

Testa apertura replay per Mines, BOXE, HI-LO:
- da runtime post-round (terminal),
- da account "Storico gioco",
- da Finance "Round detail" dove disponibile.
Riporta PASS/FAIL per ciascuno con screenshot. Se rotti, NON e' game logic: e'
CSS/container del Batch 2, fixabile scoped.

## B-final — Diff + report
- File toccati limitati a: 3 standalone giochi (poche righe), globals.css (player + admin polish scoped).
- Conferma 0 diff su: backend GMP, game logic, RNG/payout/board/reveal, runtime route pages, game-frame-page.tsx.
- Hash pre/post dei protetti.

## Divieti
- NIENTE module building/editing (Phase 3B).
- NIENTE re-design: parita' verso baseline.
- NIENTE host topbar sopra i giochi.
- NIENTE game logic / RNG / payout / board / reveal / backend GMP.
- NON usare account admin personale di Michele.

## Consegna
Report con: fix per R1/R2/R3, esito replay 3 giochi, screenshot side-by-side
(login/account/giochi/admin) vs baseline, conferma protetti 0 diff. Stop per gate
CTO, poi validazione Michele su :3000.
