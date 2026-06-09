Status: ACTIVE
Last meaningful update: 2026-05-30
Owner: CTO (Claude) — Executor: Codex — Final validation: Michele on :3000

# Site V3 Recovery Plan (post 20h multi-agent run)

## TL;DR (IT)

Il branch `feature/site-v3-cms-ia-cleanup` ha impacchettato insieme TRE cose:

1. la migrazione legittima di sito/CMS/admin dentro `frontend-v3` (DA TENERE);
2. la re-implementazione e "normalizzazione" della UI runtime dei giochi dentro V3 (OVER-REACH, ammesso da Codex);
3. una riscrittura del CSS globale che ha contaminato giochi, admin e finanziario (CONTAMINAZIONE).

Il danno visibile (HI-LO rotto, finanziario non compatto, bottoni admin illeggibili, "sembra un monolite") nasce da #2 e #3, NON da #1.

Buona notizia: la logica backend dei giochi NON e' stata toccata nei commit (lo dimostra git). I giochi sono ancora moduli backend separati (`boxe`, `hi_lo`, `mines`).

CORREZIONE IMPORTANTE (post-ispezione diff backend, 2026-05-30): le modifiche
backend nel working tree (`boxe/service.py`, `boxe/platform_client.py`,
`game_launch/service.py`, `routes/boxe.py`, `routes/demo.py`) NON sono il
"disastro". Sono il lavoro GMP (Game Module Portability) coerente: propagazione
`site_code`, `InProcessBoxePlatformAdapter`, descrittori host-neutral, ownership
check del launch token (fix INC-10). Toccano integrazione/platform, NON RNG, math,
payout, board, reveal. **Questo e' esattamente il fondamento della direzione B
che Michele ha scelto.** Quindi NON si butta: si TIENE, isolato e con i suoi test.

Il danno vero e' quasi tutto FRONTEND: CSS globale gonfiato (globals.css 766 -> 3165
righe), host chrome non richiesto sopra i giochi, runtime UI re-implementato e
contaminato, finanziario/admin investiti dal wrapper `site-v3-admin-page
admin-console-page`. Li' va il recupero.

Non si fa reset: si tiene il lavoro e si ripristina l'aspetto + si isola il CSS, in fasi con gate duri.

## 0. CTO ratification & decisions (2026-05-30)

Questo documento e' il record di decisioni CTO. RATIFICA la diagnosi di Codex in
`docs/SITE_V3_CTO_INCIDENT_AND_HANDOFF_REPORT_2026-05-30.md` (incident inventory
INC-01..INC-11), che e' stata verificata in modo indipendente contro git e
risulta corretta. La direzione B (esternalizzazione giochi) e' gia' abbozzata da
Codex in `SITE_V3_GAME_MODULE_EXTERNALIZATION_PLAN_2026-05-30.md` + GMP0..GMP5:
si conserva come follow-up, NON si esegue nel recupero.

Decisioni CTO sulle 7 richieste di handoff di Codex:

1. Direzione di recupero: **A-then-B (deciso da Michele 2026-05-30).** A ORA = stabilizza (ripristina baseline giochi/HI-LO + isola CSS + finanziario + lancio). B SUBITO DOPO = esternalizzazione giochi come moduli (package-first, GMP0-5 gia' abbozzati), come WP impegnato e calendarizzato, NON vago. Spegnere l'incendio prima, architettura strutturale pulita subito dopo.
2. Revert delle modifiche working-tree a backend giochi / launch: **NO, RIVISTO.** Ispezione del diff (2026-05-30): e' lavoro GMP coerente (site_code, adapter, launch-token ownership / fix INC-10), NON game logic. Si TIENE come fondamento della direzione B. Va solo: (a) verificato con i suoi test, (b) isolato in un commit/batch dedicato "GMP backend", (c) NON mescolato col danno frontend. Gate corretto: NON "diff backend games == vuoto", ma "nessuna modifica a RNG/math/payout/board/reveal" (verificabile: il diff tocca solo site_code/adapter/token).
3. CSS isolation prima di qualsiasi fix visivo: **SI, prerequisito hard** (Phase 2 prima di 3/4).
4. Finance/report tornano alla densita' pre-branch: **SI, baseline = `main`.** Non negoziabile.
5. Sequenza di recupero gated approvata prima di toccare codice: **SI**, con i gate duri della sezione 6. La sequenza di Codex (sez. 8 del suo report) e quella qui sotto coincidono.

Confine architetturale onesto: la direzione A e' piu' veloce ma i giochi in V3
sono RE-IMPLEMENTAZIONI nuove (non esistevano su `main`), quindi "ripristino
parita'" porta rischio di redo proprio dove Codex ha gia' fallito. La direzione B
rende il confine STRUTTURALE invece che una convenzione. Scelta di Michele.

## 1. Diagnosis (git-proven, 2026-05-30)

- Branch corrente: `feature/site-v3-cms-ia-cleanup`.
- Divergenza da `main`: **35 commit ahead, 0 behind**. `main` e' intatto e pulito.
- Finestra commit: 2026-05-28 18:06 -> 2026-05-29 23:19. Working tree sporco = lavoro odierno (2026-05-30).
- `main` = ultimo stato in cui (per conferma di Michele) giochi e CSS admin erano OK. E' la baseline di parita'.

Cosa e' stato toccato:

| Area | Nei 35 commit (main..HEAD) | Nel working tree (non committato) |
|---|---|---|
| Backend giochi (`backend/app/modules/games/`) | **NON toccato** (diff vuoto) | `boxe/service.py` (+41), `boxe/platform_client.py` (+185) |
| Platform launch (`modules/platform/game_launch/service.py`) | da verificare | modificato (M) |
| `frontend-v3/app/globals.css` | +2597 righe | modificato di nuovo |
| `frontend-v3/app/ui/casinoking-console.tsx` | +3737 (nuovo grande file) | modificato di nuovo |
| `frontend-v3/app/ui/game-runtime/` (28 file nuovi, ~3347 righe) | creato nel branch | modificato di nuovo |
| `game-runtime.css` (~935 righe) | creato nel branch | modificato di nuovo |
| Finance/admin (`admin-finance-panel.tsx`, ecc.) | toccati dal restyle admin globale | parziale |

Conclusione: il runtime dei giochi NON esisteva in V3 su `main`; e' stato **estratto/re-implementato** nel branch ("extract mines/hi-lo/boxe runtime to v3"). Quindi la baseline visiva dei giochi vive nel vecchio frontend su `main`, non in V3.

## 2. Root cause

Codex (sua ammissione) ha confuso "V3 SERVE il runtime" con "V3 puo' NORMALIZZARE il runtime". Ha:

- cambiato header gioco, X/fullscreen/account sopra il gioco, volume, replay, layout, CSS visuale del runtime;
- usato CSS condiviso troppo largo (selettori globali), contaminando il contenitore/visuale di Mines/HI-LO/BOXE anche senza toccarne i file;
- applicato uno stile admin globale che ha investito Finance e altri pannelli gia' ottimizzati.

Causa di processo: scope control fallito ("arrivare in fondo" al piano V1/V2/V3 invece di fermarsi al confine hosting/route/shell). Tracciato come violazione processo Codex.

## 3. Recovery contract (principio non negoziabile)

> Site V3 OSPITA e INTEGRA i giochi. NON ne restyle la UI. I giochi restano moduli con confini propri. Il CSS di V3/admin NON puo' contaminare giochi ne' report/finanziario.

## 4. Decisione architetturale (CTO recommendation)

Fork: (A) tenere i giochi re-implementati dentro `frontend-v3` e solo ripristinarne aspetto + isolare CSS; oppure (B) trattare i giochi come moduli esterni che V3 si limita a lanciare (reversal piu' grande).

**Raccomandazione CTO: opzione A per questo recupero d'emergenza.** Onora "tenere il piu' possibile" e ripristina comunque l'indipendenza VISIVA e di CSS dei giochi. La esternalizzazione fisica completa (B), se desiderata, diventa un WP pianificato successivo, NON parte del recupero. Se Michele preferisce B, il piano cambia (piu' reversioni, meno "tenere").

## 5. Fasi (ogni fase = WP gated; Codex esegue, CTO fa gate, Michele valida a fine)

### Phase 0 — Safety & Freeze (rischio zero) — FATTO da CTO 2026-05-30
- [FATTO] Branch di backup non distruttivo `backup/site-v3-codex-run-2026-05-30` (commit `6141c17`) che cattura commit + working tree completo. Working tree corrente intatto (39 mod + 151 untracked). Nulla puo' andare perso.
- FREEZE: nessun lavoro feature finche' il recupero non e' chiuso.
- RIVISTO: NON si reverta il backend giochi. Il diff e' GMP coerente (site_code/adapter/launch-token), non game logic. Si tiene, isolato in un batch dedicato. Verifica: confermare che il diff non tocca RNG/math/payout/board/reveal (gia' verificato a vista dal CTO).

### Phase 1 — Baseline parity inventory (audit) — FATTA + GATE CTO PASSATO 2026-05-30
- Baseline = rendering di `main` per: ogni gioco (Mines/HI-LO/BOXE player UI), Finance/report, pannelli admin.
- Codex ha catturato 30 screenshot (15 baseline main@4715fda su :3100, 15 current branch@8c501e8 su :3000) + mappa selettori CSS con righe precise.
- Output: `docs/SITE_V3_RECOVERY_PARITY_INVENTORY_2026-05-30.md` + `artifacts/site_v3_recovery_parity_inventory_2026-05-30/`.
- GATE CTO (verificato contro git): working tree invariato (Codex non ha toccato codice); backend GMP intatto; 30 PNG reali; mappa CSS solida.
- RISERVE CTO da portare in Phase 2:
  1. "Nessun diff runtime giochi" e' rispetto a HEAD, NON a main: vs main i giochi sono re-implementati (Mines 17 / BOXE 15 / HI-LO 9 file). Baseline visiva giochi = vecchio `frontend` su main.
  2. 6 sezioni admin senza screenshot (Games, Site, Site V3, LOG, Administrators, Platform Settings): Phase 2 deve coprirle.
  3. HI-LO: scarto tra percezione Michele ("rotto") e audit ("quasi a posto, manca X mobile"). Verificare break funzionale.
  4. Stato X close ambiguo (artifact native_close precedente vs report che la dice ancora mancante). Chiarire.

Findings chiave Phase 1 (causa fisica del danno):
- `globals.css`: main 766 righe -> branch ~3100-3900 righe.
- Contaminazione admin/finance (INC-11): wrapper `site-v3-admin-page admin-console-page` su TUTTE le route admin (`casinoking-console.tsx:2235`) + ridefinizione selettori generici (`.button .field .stack .panel .admin-card`) in `globals.css:2302-2333` e `3106-3374`. Tema dark compact -> light large.
- Contaminazione giochi: selettori generici globali (`.button .field .status-badge .stack`) che fanno match dentro gli iframe gioco + nuovo `game-runtime.css` (935 righe, assente su main).

### DECISIONI CTO/Michele registrate (2026-05-30)
- Strategia CSS: Opzione 1 "revert+re-scope" (riparti da globals.css di main 766 righe, ri-aggiungi CMS scoped). APPROVATA.
- Player account "Dettagli account" strip: RIMOSSA (decisione Michele). Parita' verso main NON richiesta su questo punto. Validazione finale su :3000.
- Esecuzione Parte B SPEZZATA: batch 1 = B0-B3 (CSS base + admin/finance), gate CTO, poi batch 2 = B4-B7 (giochi + 6 superfici mancanti). I giochi restano dietro un checkpoint extra.
- HI-LO: includere smoke funzionale nel batch giochi per spiegare il "rotto" percepito da Michele.

### Phase 2B Batch 1 (B0-B3) — FATTA + GATE CTO PASSATO 2026-05-30
- File toccati: `globals.css` (riportato a main + CMS/legacy ri-aggiunti scoped), `casinoking-console.tsx` (wrapper rimosso), `admin-site-v3-page.tsx` (root CMS).
- Nuove root: `.ck-admin-legacy-page` (admin/finance legacy, dark-compact verso main) + `.site-v3-cms-admin-page` (CMS V3 scoped). Wrapper contaminante `site-v3-admin-page admin-console-page`: 0 occorrenze.
- globals.css 2403 righe (main 766 + ~1640 ri-aggiunte scoped pulite). Atteso da Opzione 1.
- GATE CTO verificato: file protetti (game-runtime.css, game-frame-page.tsx, runtime/*, ui/mines|boxe|hi-lo, backend GMP) = 0 diff vs backup 6141c17. Screenshot: Finance dark-compact RIPRISTINATO, ledger leggibile, menu admin compatto, CMS usabile.
- Output: `artifacts/site_v3_recovery_phase2_batch1_2026-05-30/` (b2/ + b3/ + metadata/).
- Giochi: ancora FAIL/rosso (atteso, sono il Batch 2).

### Phase 2B Batch 2 (B4-B7, GIOCHI) — FATTA + GATE CTO PASSATO 2026-05-30
- Selector gate (B4): PASS, zero leakage V3/admin/global dentro iframe giochi (verificato in metadata + screenshot before/after).
- Visual parity (B5): Mines/HI-LO/BOXE desktop+mobile a parita' con baseline main (side-by-side verificati a schermo dal CTO).
- HI-LO smoke (B5b): start/red-black/up-down/skip/cashout/replay tutti PASS. Conclusione: il "rotto" percepito da Michele era SOLO regressione visiva (X mobile + control treatment), NESSUN break funzionale.
- 6 superfici admin (B6): tutte PASS. Games rifixato scoped (root `ck-admin-legacy-page admin-games-page`). Site e Administrators = PASS WITH PRODUCT DEBT (lunghe/dense, debito UX preesistente, non leak CSS).
- File toccati (B7): game-runtime.css (+95/-1) + 6 file gameplay .tsx + globals.css + admin-games-page.tsx.
- GATE CTO verificato: i 6 .tsx gameplay contengono SOLO aggiunte di classi CSS scoped `ck-game-*` (es. `ck-game-runtime-root`, `ck-game-icon-button`, `ck-game-control-rail`, `ck-game-audio-control`). ZERO logica: nessun RNG/random/seed/payout/multiplier/board/reveal/probability toccato (verificato keyword-grep sui diff). Protetti (backend GMP, runtime route pages, game-frame-page.tsx) = 0 diff.
- NOTA: il riassunto chat di Codex diceva "solo game-runtime.css cambiato" ma erano cambiati anche 6 .tsx; il report scritto li elencava onestamente; i cambi sono benigni (solo class hooks). Strike lieve comunicazione, non sostanza.
- Output: `artifacts/site_v3_recovery_phase2_batch2_2026-05-30/`.

### STATO RECUPERO: tecnicamente COMPLETO. Manca solo validazione manuale Michele su :3000.

### Phase 2 — CSS isolation (fix strutturale, prerequisito)
- Scoping di TUTTO il CSS del game-runtime sotto una root namespacizzata (niente selettori globali; CSS scoped/module). Nessuna regola runtime puo' uscire dal contenitore gioco.
- Scoping del CSS admin/site-v3 cosi' da non poter toccare Finance/report ne' altri pannelli admin.
- Ripulire `globals.css`: tenere solo cio' che e' davvero globale (reset/token), spostare il resto sotto root scoped.
- Gate: nessun selettore di V3/admin deve fare match sul DOM dei giochi o del finanziario.

### Phase 3 — Game runtime visual restore (parita', NON restyle)
- Per ogni gioco, ripristinare parita' visiva con la baseline `main` usando come fonte di verita' gli stili/markup vecchi (PORTARE, non re-inventare).
- Sistemare il break funzionale di HI-LO (flusso di lancio/runtime).
- Hard rule giochi: mai scrollbar, celle adattive, smoke browser su TUTTE le combo con misurazione DOM reale.

### Phase 4 — Finance / admin density restore
- Riportare Finance/report e pannelli admin alla compattezza e leggibilita' bottoni della baseline.

### Phase 5 — Game launch flow
- Verificare lancio sito/lobby -> gioco -> ritorno per tutti e 3 i giochi, con token/parametri/account corretti.

### Phase 6 — Closure
- Capability matrix (regola cross-cutting).
- Audit a due step: auditor + verifier indipendente sulle superfici critiche (giochi, finanziario).
- Validazione finale di Michele su :3000.

## 6. Hard gates (non negoziabili)
- Game LOGIC intatta: zero modifiche a RNG / math / payout / board / reveal nei moduli giochi. (Il diff backend attuale rispetta questo: tocca solo site_code/adapter/launch-token = GMP, da tenere.)
- Parita' visiva giochi = screenshot side-by-side vs baseline `main` (non diff statistico).
- CSS: zero leakage di selettori V3/admin su DOM gioco o finanziario.
- Smoke browser su tutte le configurazioni board (no spot check).
- Parita' = container condiviso + contenuto/copy entrambi a baseline.
- Nessuna feature nuova durante il recupero.

## 7. Cosa Codex NON deve fare
- Non re-inventare la UI dei giochi: parita' con baseline, non restyle.
- Non usare selettori CSS globali per V3/admin.
- Non toccare wallet/ledger/payout/RNG/replay.
- Non aggiungere testi/badge/bottoni non richiesti.
- Non chiudere una superficie come "verde" se solo il container e' a posto e il contenuto no.
- Non procedere alla fase successiva senza gate verde della precedente.

## 8. Sequencing
Phase 0 -> 1 -> 2 (isolation prima del restore visivo) -> 3 -> 4 -> 5 -> 6.
Phase 2 e' prerequisito di 3 e 4: senza isolare il CSS, ogni fix visivo rischia di ri-contaminare.
