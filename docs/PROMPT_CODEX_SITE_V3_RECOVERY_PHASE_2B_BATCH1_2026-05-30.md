Status: ACTIVE
Last meaningful update: 2026-05-30

# Prompt Codex — Site V3 Recovery, Phase 2B BATCH 1 (B0-B3, admin/finance)

Il CTO ha approvato l'approccio Phase 2A
(`docs/SITE_V3_RECOVERY_PHASE2_APPROACH_2026-05-30.md`): strategia Opzione 1
"revert+re-scope". Buona proposta.

Phase 2B e' SPEZZATA in due batch con gate CTO in mezzo:
- BATCH 1 = QUESTO = B0, B1, B2, B3 (CSS base + admin/finance + ri-aggiunta CMS scoped).
- BATCH 2 = SOLO DOPO gate CTO = B4-B7 (giochi + 6 superfici mancanti).

I GIOCHI NON SI TOCCANO IN QUESTO BATCH. Niente fix visivo giochi, niente
game-runtime.css, niente route /runtime/*. Sono protetti dietro il gate CTO.

## Decisioni CTO gia' prese (NON ridiscuterle)
- Strategia: Opzione 1 revert+re-scope.
- Player account "Dettagli account" strip: RIMANE RIMOSSA. Non re-aggiungerla, non rimuoverne altro. Parita' verso main NON richiesta su quel blocco.
- Baseline visiva = `main` (commit 4715fda, screenshot in artifacts Phase 1).

## Esegui SOLO B0-B3

### B0. Pre-flight guard
- Conferma branch, file sporchi, file backend GMP protetti
  (`boxe/service.py`, `boxe/platform_client.py`, `game_launch/service.py`,
  `routes/boxe.py`, `routes/demo.py`) intatti.
- Conferma nessuna modifica a game logic / RNG / math / payout / board / reveal / replay.
- Ricontrolla il valore reale di righe attuale di `globals.css` nel working tree
  (Phase 2A ha notato discrepanza 3165 vs 3869: verifica prima di partire).
- Gate: report "nessun codice ancora cambiato" + lista file protetti intatti.

### B1. Baseline CSS anchor
- Riporta `frontend-v3/app/globals.css` alla baseline di `main` come ancora controllata.
- NON modificare `game-runtime.css` ne' i CSS dei giochi in questo step.
- Cattura screenshot: Finance filtri/report, admin shell, admin login,
  player login/account, e i 3 giochi desktop/mobile (per CONFERMARE che non
  peggiorano; non si fixano qui).
- Gate: elenca quali regressioni admin/finance migliorano e quali superfici CMS V3
  nuove perdono stile (atteso, verranno ri-aggiunte in B3).

### B2. Split radice legacy admin/Finance
- Togli la dipendenza di admin/Finance/player-admin legacy dal wrapper CMS V3
  (`site-v3-admin-page admin-console-page` in `casinoking-console.tsx:2235`).
- Ripristina il comportamento dark-compact admin/report verso `main`.
- Cattura: Finance filtri + bank session report, ledger report, round detail,
  admin shell/menu, admin login, My Space, player admin list.
- Gate: gli screenshot Finance/report/admin devono combaciare con `main` in tema,
  compattezza e leggibilita'; nessuno stile CMS V3 deve trapelare in questi report.

### B3. Ri-aggiungi CSS CMS V3 sotto radice scoped
- Re-introduci lo stile CMS/builder/Module Studio SOLO sotto una radice dedicata
  CMS (non condivisa con Finance/admin legacy).
- Tieni i selettori generici (`.admin-card`, `.field-grid`, `.button-secondary`,
  `.button-ghost`, `.field input`, `.field select`) scoped a CMS o riportati al
  comportamento legacy di main, secondo i casi.
- Cattura: `/admin/site-v3` dashboard, settings, composition, module library,
  Module Studio, preview live.
- Gate: CMS/builder usabile e coerente; gli screenshot Finance/admin di B2 restano
  INVARIATI.

## Divieti (Batch 1)
- NON toccare: giochi (ui/mines, ui/boxe, ui/hi-lo, runtime/*), game-runtime.css,
  runtime-base.css, game-frame-page.tsx (oltre a leggerlo).
- NON toccare game logic / RNG / math / payout / board / reveal / replay.
- NON toccare i file backend GMP (CTO-approved).
- NON re-aggiungere la striscia "Dettagli account".
- NON procedere a B4-B7 (giochi): si fermano al gate CTO.

## Gate finale Batch 1 (cosa il CTO verifichera')
- Diff limitato a: `globals.css`, eventuale nuovo file CSS CMS scoped, e
  `casinoking-console.tsx` (solo per il wrapper). NIENTE file giochi.
- Finance/report/admin a parita' dark-compact con main (screenshot).
- CMS V3 ancora usabile (screenshot).
- Giochi NON peggiorati (screenshot di conferma B1).
- Backend GMP + game logic intatti.

## Consegna
Report esplicito: file toccati / screenshot per superficie (path artifacts) /
pass-fail per superficie / conferma file protetti intatti / cosa resta per Batch 2.
Niente "fatto" ambiguo. Poi STOP: attendi gate CTO prima del batch giochi.
