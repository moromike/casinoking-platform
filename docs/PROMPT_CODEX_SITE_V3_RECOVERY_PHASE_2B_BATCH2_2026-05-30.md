Status: ACTIVE
Last meaningful update: 2026-05-30

# Prompt Codex — Site V3 Recovery, Phase 2B BATCH 2 (B4-B7, GIOCHI)

Il CTO ha approvato il Batch 1 (B0-B3): admin/Finance tornati dark-compact verso
main, CMS scoped, file giochi intatti (0 diff vs backup). Gate visivo passato.

QUESTO E' IL BATCH PIU' DELICATO: e' la parte giochi, dove la run originale e'
fallita. Regola dura: **parita' verso la baseline `main` con screenshot
side-by-side, NON restyle, NON re-invenzione.**

## Decisioni CTO gia' prese (NON ridiscuterle)
- Baseline visiva giochi = vecchio `frontend` su `main` (commit 4715fda), screenshot Phase 1 in `artifacts/site_v3_recovery_parity_inventory_2026-05-30/baseline-main/`.
- Game logic INTOCCABILE: RNG, math, payout, board, reveal, replay. Zero diff.
- Backend GMP INTOCCABILE.
- Player account "Dettagli account": resta rimossa.

## Esegui B4-B7

### B4. Game iframe selector gate (audit prima del fix)
- Per Mines, BOXE, HI-LO: esegui il selector-match DENTRO l'iframe runtime
  (come la metadata Phase 1 `css-actual-selector-matches-v2.json`).
- Gate: NESSUN selettore V3/admin/globals deve fare match nel DOM iframe gioco.
  Solo selettori game-owned ammessi.
- Se trovi ancora leakage dal Batch 1, correggilo scoping il selettore (non
  toccando i file gioco). Riporta prima/dopo.

### B5. Game visual parity pass (il cuore)
- Cattura Mines, HI-LO, BOXE desktop + mobile sulle route pubbliche reali
  (`http://localhost:3000/mines`, `/boxe`, `/hi-lo`).
- Confronta SIDE-BY-SIDE con gli screenshot baseline main di Phase 1.
- Verifica esplicitamente per ogni gioco: X/close nativa, controllo audio/volume,
  compattezza, posizionamento board/contenuto, layout mobile, replay.
- Regola "no scrollbar / celle adattive": board mai con scrollbar, mai clipping.
- Se una regressione e' provata venire da `game-runtime.css`, fai la modifica
  scoped MINIMA solo a quel gruppo di selettori. Mai toccare game logic.
- Gate: parita' verso main accettata per superficie, o delta residuo classificato
  esplicitamente con file sospetto.

### B5b. HI-LO functional smoke (sciogliere l'ambiguita')
- Michele percepisce HI-LO come "rotto", l'audit Phase 1 lo dava quasi a posto.
- Esegui smoke funzionale: start round, scelta red/black + up/down, skip/cashout,
  apertura replay, switch lingua/i18n. SENZA toccare game logic.
- Riporta: e' solo regressione visiva (X mobile) o c'e' un break funzionale reale?

### B6. Superfici admin non catturate in Phase 1
- Cattura e verifica: Games, Site, Site V3, LOG, Administrators, Platform Settings.
- Gate: ognuna classificata pass / delta accettabile / regressione con file sospetto.
- Devono usare la root legacy scoped del Batch 1, non trapelare stile CMS.

### B7. Diff finale + report recovery
- Conferma file toccati limitati a CSS scoped (eventuale game-runtime.css minimo).
- Conferma protetti intatti: backend GMP + game logic = 0 diff.
- Conferma nessun RNG/math/payout/board/reveal/replay toccato.
- Produci report Phase 2B Batch 2 con path screenshot, pass/fail per superficie,
  e decisioni residue per Michele.

## Divieti (Batch 2)
- NON re-inventare la UI dei giochi: parita' verso main, non nuovo design.
- NON toccare game logic / RNG / math / payout / board / reveal / replay.
- NON toccare backend GMP.
- NON aggiungere host chrome / topbar / bottoni non presenti nella baseline main.
- NON chiudere una superficie "verde" se solo il container e' ok e il contenuto no.
- NON usare l'account admin personale di Michele.

## Stop conditions (fermati e chiedi al CTO)
- Se la parita' richiede di toccare game logic o backend GMP.
- Se il selector gate trova ancora match V3/admin dentro gli iframe dopo lo scoping.
- Se una regressione gioco non si risolve senza re-invenzione della UI.

## Consegna
Report esplicito + screenshot side-by-side per ogni gioco (desktop+mobile) +
esito HI-LO functional smoke + 6 superfici admin. Niente "fatto" ambiguo.
Poi STOP: gate CTO finale, poi validazione Michele su :3000.
