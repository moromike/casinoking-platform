Status: ACTIVE
Last meaningful update: 2026-05-25 (round 2 chiuso, follow-up Codex aperti)

# COINS - Open Questions And Product Decision Checklist

## Contesto

Nuovo gioco proprietario in valutazione: **COINS** (riferimento Hacksaw Gaming, serie
Dare2Win). Analisi funzionale di partenza generata via skill Gemini su video + screenshot,
disponibile in:

`games/coins/COINS - analisi gemini funzionale_v01.md`

Source asset directory: `assets/Games/coins/`.

Il documento Gemini copre **bene**: math/RTP/payout matrix, regole win/loss, UI controlli,
geometria griglia, animazioni/timing, autoplay UI, esempio API.

Il documento Gemini **NON copre** (gate obbligatori dal `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`,
Fase 0 - blocchi 3, 5, 6, 7, 8, 9, 10, 11 + Rule 22/24/25 + 12-surface check):

- state machine backend
- idempotency contract
- demo/real/bonus modes
- max win cap
- replay/history contract
- disconnect/auto-settlement
- operator settings (Title Editor)
- lingue al lancio
- asset contract (formati/size)
- failure UX completa
- shell platform riuso vs custom
- mobile/embed/visual reference

Questo documento serve a chiudere le decisioni product mancanti **prima** di entrare in
Fase 1 (Architecture Mapping). Michele risponde con `Q1: ok` (= preferita) oppure
`Q1: alternativa` oppure scrive risposta libera.

Linee guida usate per le risposte preferite:
- riuso massimo platform Mines/BOXE/HI-LO (regola architettura pulita Michele)
- niente debito tecnico, niente "if game === coins" hardcoded (Rule 18 playbook)
- allineamento ai 3 giochi precedenti dove possibile

---

## A. ECONOMIA E MATH

### Q1 - Max win cap

Con N=12 e bet €200 il payout teorico è **€802.816**. Serve un tetto?

- **Preferita:** cap relativo a bet, **max win = 5.000× bet** (allineato a Mines/BOXE).
  Con bet €200 max payout = €1.000.000. Configurabile da admin via Title Editor.
- Alternativa: cap assoluto fisso €100.000.

### Q2 - N massimo monete supportate al lancio

Hacksaw originale arriva a 12 (prob 1/4096). Davvero teniamo 12?

- **Preferita:** **10 max al lancio** (prob 1/1024, payout 1003x). Mantiene la promessa
  del gioco ma riduce volatilità estrema. N=11/12 abilitabili via Title Editor in seconda
  battuta.
- Alternativa: tutti 12 come Hacksaw.

### Q3 - Currency

- **Preferita:** **EUR only** al lancio (come Mines/BOXE/HI-LO).

### Q4 - RTP variant configurabile

- **Preferita:** RTP **98% fisso** al lancio + slot in Title Editor predisposto per future
  varianti (97% / 99%) senza re-coding.
- Alternativa: solo 98% hardcoded.

---

## B. LIFECYCLE E MODES

### Q5 - Modes supportati al lancio

- **Preferita:** **tutti e 3 (demo + real cash + real bonus)**, come Mines/BOXE/HI-LO.
  Niente differimenti.
- Alternativa: demo + real cash al lancio, bonus in WP separata.

### Q6 - State machine backend

Anche se COINS è "single-shot" servono stati espliciti.

- **Preferita:** `IDLE → BET_PLACED → SPINNING → RESOLVED`. Round chiude in <2s. Autoplay
  = sequenza di N round indipendenti, no stato "session-level autoplay" lato backend.
- Alternativa: solo `OPEN → CLOSED` (più semplice, ma perdi tracciabilità).

### Q7 - Auto-settlement su close/disconnect (Rule 22 playbook)

- **Preferita:**
  - Stato `BET_PLACED` non ancora `SPINNING`: **refund automatico** della puntata.
  - Stato `SPINNING`: round si chiude naturalmente (RNG già lanciato server-side),
    settlement avviene comunque, payout accreditato.
  - Durante Autoplay, tra round: **stop autoplay**, nessuna nuova bet, balance corrente.

### Q8 - Idempotency

Se il client ritrasmette la bet (network retry)?

- **Preferita:** **idempotency_key generato dal client** (UUID), server riconosce duplicato
  entro **TTL 5 minuti** e restituisce stessa risposta (no doppia bet). Pattern Mines/BOXE.

---

## C. REPLAY, FINANCE, REPORTING (Rule 24 playbook)

### Q9 - Replay storage minimo

- **Preferita:** `{coin_matrix, N, bet, multiplier, payout, mode, timestamp, idempotency_key}`.
  Il replay viewer rirenderizza l'animazione **deterministica** sugli stessi indici (no RNG
  re-roll). Pattern Mines.

### Q10 - Entry point Replay player-side (Rule 20)

- **Preferita:** **dentro il modal info (`i`)**, tab "Replay" accanto a Rules/Fairness.
  **No pulsante Replay sulla play surface**. Coerente con HI-LO Rule 20.

### Q11 - Account history + Admin finance

- **Preferita:** stesso pattern HI-LO. Registry/adapter (no "if game === coins" hardcoded
  — Rule 18 playbook: al quarto gioco serve registry).

---

## D. OPERATOR SETTINGS (Title Editor)

### Q12 - Cosa è configurabile da admin

- **Preferita** (allineata a Mines/BOXE/HI-LO):
  - Bet range (default €0.20 – €200.00)
  - N range monete (default 1–10)
  - Max win cap (default 5.000× bet)
  - Limiti autoplay (rounds, loss limit, win limit — già coperti nel doc Gemini)
  - Copy / Rules HTML (i18n IT+EN)
  - Asset moneta (skin) + sound
  - Theme tokens (palette neon)
- Alternativa: solo copy e asset configurabili, math hardcoded (meno flessibilità lancio).

### Q13 - Lingue al lancio

- **Preferita:** **IT + EN** (come Mines/BOXE/HI-LO).
- Alternativa: solo IT.

### Q14 - Visibilità lobby (CMS publication path)

- **Preferita:** stessa publication path di Mines/BOXE/HI-LO (admin pubblica variant →
  appare in `/games/library` → lobby card → Launch Cashier). Rule 19 obbligatoria.

---

## E. VISUAL E SHELL (12-surface check)

### Q15 - Shell platform riusata o custom?

Provider intro, How-to-play gate, Table balance gate, Short viewport gate, Embed mode.

- **Preferita:** **TUTTI riusati da GameRuntimeShell esistente, zero divergence.** Coerente
  con regola architettura pulita Michele e con pattern HI-LO. Solo board e payout sono
  game-specific.

### Q16 - Control rail (pannello sinistro)

COINS ha layout diverso da Mines (toggle Manual/Auto + griglia 1-12 invece di input mines).

- **Preferita:** **GameControlRail condiviso con schema adapter game-specific** (registry
  pattern). Niente "if game === coins" sparso nel codice (Rule 18).
- Alternativa: control rail completamente custom (debito tecnico — sconsigliato).

### Q17 - Theme / palette

COINS ha blu-notte + verde/ciano neon, diverso da Mines.

- **Preferita:** **variant del theme platform tramite advanced skin** (sistema Mines già lo
  supporta), no nuovo motore CSS. Palette COINS sta nel theme manifest configurabile da
  admin.

### Q18 - Mobile portrait + landscape-short gate

12 monete in portrait?

- **Preferita:** griglia 4×3 si adatta in portrait con cella adattiva (Rule 14 playbook:
  no scrollbar, no clipping). Landscape-short gate riusato come Mines/BOXE.

### Q19 - Embed mode (`?embed=1`)

- **Preferita:** **supportato** da subito (stesso contratto Mines/BOXE/HI-LO).

---

## F. ASSETS

### Q20 - Asset specifici COINS

- **Preferita:**
  - **Moneta:** PNG 256×256, 4 stati (idle, spin, H, X), max 100KB per file. Oppure
    sprite-sheet unico se preferito da art team.
  - **Background gameplay:** PNG 1920×1080, max 500KB (oppure gestito via theme).
  - **Sound:** 3 eventi (spin, win, lose) MP3 max 200KB ciascuno.
  - **Lobby card + icona engine:** stessi format Mines (PNG ottimizzati).
- Tutti caricabili da Title Editor con upload guidance esplicita (Fase 4B playbook).

### Q21 - Animazioni e reduced-motion

- **Preferita:** rispettare `prefers-reduced-motion` → spin diventa **fade in/out** (no
  rotazione 3D + motion blur). Accessibility standard, come Mines/BOXE.

---

## G. FAILURE UX

### Q22 - Errori standard da gestire (copy nel manifest, Rule 25)

- **Preferita** (lista standard allineata Mines/BOXE/HI-LO):
  - `insufficient_balance` → "Saldo insufficiente per questa puntata"
  - `table_expired` → "Sessione scaduta, riapri il gioco"
  - `network_error` → "Connessione persa, riprova" + retry button
  - `config_missing` → "Gioco temporaneamente non disponibile"
  - `malfunctioning` → "Round annullato, puntata rimborsata" (già nel doc Gemini)
  - `bet_out_of_range` → "Importo non valido"
- Nessuna stringa hardcoded nel runtime (Rule 25 playbook).

### Q23 - Autoplay edge cases

- **Preferita:**
  - `balance < bet` durante autoplay → auto-stop + dialog "Saldo insufficiente, autoplay
    terminato"
  - `loss_limit` raggiunto → auto-stop + dialog
  - `single_win_limit` raggiunto → auto-stop + dialog
  - disconnect → stop alla prossima resa, non avviare nuovo round

---

## H. FAIRNESS / CERTIFICAZIONE

### Q24 - RNG fairness

- **Preferita:** **server-side RNG** (mai client), seed deterministico archiviato per ogni
  round insieme a `coin_matrix`. Audit log persistente. Pattern Mines/BOXE certificabile.
- Alternativa: provably fair con client seed (più complesso, deferribile post-launch).

---

## I. DECISIONI DI SCOPE

### Q25 - Wave 1 scope (cosa entra al primo merge)

- **Preferita:** scope minimo per Product Owner walkthrough:
  - demo playable end-to-end
  - real cash + real bonus funzionanti
  - autoplay base (rounds + loss/win limit + custom)
  - Title Editor con config + copy + rules + asset upload
  - Lobby card + launch flow
  - Finance + replay funzionanti
  - IT + EN
- **Differito a Wave 2:** RTP variants (97/99), N=11/12 abilitabili, provably fair client-seed,
  theme advanced editing.

---

## J. Risposte Michele - Round 1 (2026-05-25 sera)

| Q | Topic | Risposta Michele | Note |
| --- | --- | --- | --- |
| Q1 | Max win cap | OK preferita (5.000× bet, configurabile admin) | |
| Q2 | N max monete | OK preferita: **N=10 max al lancio** | |
| Q3 | Currency | EUR al lancio, **multivaluta crypto** prevista per produzione **fase 2** (non fase 1) | Annotazione futura - vedi sezione M |
| Q4 | RTP variant | OK preferita (98% fisso + slot per varianti) | |
| Q5 | Demo/Real/Bonus | OK preferita: **come Mines, tutti e 3**. Michele: "queste domande nemmeno devi farle" | Trigger per playbook update |
| Q6 | State machine | OK preferita (IDLE → BET_PLACED → SPINNING → RESOLVED). Michele: "vedi te, la visione ce l'hai te" | |
| Q7 | Auto-settlement close | OK preferita | |
| Q8 | Idempotency | OK preferita | |
| Q9 | Replay storage | OK preferita | |
| Q10 | Replay entry point | OK preferita ("ovvio, nemmeno a chiedere"). **NUOVO TEMA APERTO: replay retention 30gg + routine storicizzazione** | Vedi sezione L |
| Q11 | Account history/finance | OK (Michele: "non ho capito ma ok se per te è ok") | Spiegazione dovuta a Michele - vedi sezione L |
| Q12 | Title Editor settings | OK preferita ("come gli altri, nemmeno a chiedere") | |
| Q13 | Lingue al lancio | NON 2 (IT+EN) ma **4 lingue come Hacksaw originale**. "sono 4, non 50, quelle 4 le voglio sempre" | Quali 4? Da decidere - vedi sezione L |
| Q14 | CMS publication path | OK preferita ("come gli altri, ti dirò io se lo voglio differente") | |
| Q15 | Shell platform riuso | OK preferita | |
| Q16 | Control rail | OK preferita | |
| Q17 | Theme/palette | OK preferita | |
| Q18 | Mobile + landscape | OK preferita. Michele: "il mobile io non lo testo, è responsabilità tua" | |
| Q19 | Embed mode | OK ma Michele non sa cosa sia | Spiegazione dovuta - vedi sezione L |
| Q20 | Asset specifici | OK preferita. **NUOVO TEMA APERTO: H/X sono immagini caricabili o caratteri editabili?** | Vedi sezione L |
| Q21 | Reduced-motion + animazioni | OK ma vuole **animazione minima tipo Hacksaw**, non solo fade. Chiede: subito o mini-progetto a parte? | Vedi sezione L |
| Q22 | Failure UX | OK preferita. **Nota**: c'è progetto parallelo codifica errori, il playbook dovrà tenerne conto un domani | Annotazione futura - vedi sezione M |
| Q23 | Autoplay edge cases | OK preferita "come Hacksaw" | |
| Q24 | RNG fairness | **Assolutamente OK**, no alternative. Provably fair da segnarsi per futuro probabile non certo | Annotazione futura - vedi sezione M |
| Q25 | Wave 1 scope | OK preferita **tranne theme advanced editing**: Michele chiede perché non subito? | Vedi sezione L |

---

## L. Round 2 - Risposte Michele (2026-05-25 sera, chiuso)

### L1 - Replay retention (sollevato da Michele su Q10)

**Proposta Michele acquisita:** memorizzare replay ultimi 30 giorni online, routine
giornaliera storicizza i più vecchi per liberare risorse. Parte finanziaria persistente
sempre. Sensato (pattern industria hot/cold storage). Diventa M2 - non bloccante Wave 1
COINS. Allineato con `docs/ACTIVE_OPEN_LOOPS.md` P1 esistente "Replay retention".

### L2 - Q11 registry/adapter spiegato + decisione

**Risposta Michele 2026-05-25:** "che ci sia ancora un debito da qualche parte non mi
sta bene". **Decisione:** convertire i branch hardcoded `if game === "mines"/"boxe"/"hi_lo"`
in registry pattern **prima** di aggiungere COINS. Vedi prompt Codex Parte A nella
sezione N1.

### L3 - Q13 quali 4 lingue al lancio

**Risposta Michele 2026-05-25:** "stesse lingue di Mines/BOXE/HI-LO, cosa ti inventi".
Verificato in codice: `("it", "en", "de", "es")` (IT, EN, DE, ES) identiche tra i 3
giochi. **COINS = stesse 4 lingue.** Domanda chiusa, era inutile porla.

### L4 - Q19 embed mode + autonomia gioco

**Risposta Michele 2026-05-25:** "il gioco include la shell. Se un domani CasinoKing non
esisterà ma i giochi gireranno in un altro sito, dovrà esserci tutto a partire da DOPO
il pannello di ingresso coin/valuta: dal launch fino a tutto il gioco con il suo iframe
assegnato dal sito esterno. Il gioco include la shell, tutto".

**Stato attuale verificato in codice:**
- Mines: embed mode completo (CSS + postMessage handshake `close` + `fullscreen-state`).
- BOXE: parziale (CSS riusato da Mines, flag `isEmbeddedView` presente, manca postMessage
  handshake).
- HI-LO: parziale (CSS proprio, flag `isEmbeddedView` presente, manca postMessage
  handshake).

**Decisione:** chiudere il debito embed in BOXE + HI-LO prima di COINS. Vedi prompt Codex
Parte A nella sezione N2.

### L5 - Q20 H/X immagini o caratteri

**Risposta Michele 2026-05-25:** **alternativa B = entrambi**. Admin sceglie da Title
Editor se vuole immagini caricabili (PNG con guidance esplicita) o caratteri editabili
(testo + font/colore via theme). Asset di default forniti.

### L6 - Q21 animazione monete

**Risposta Michele 2026-05-25:** "per ora facciamo come proponi, poi teniamoci la
domanda se dobbiamo fare un nuovo progetto per migliorare l'animazione". **Decisione:**
Wave 1 con animazione base solida (Phase 3C playbook). Tema aperto M6: valutare
mini-progetto polish animazione COINS post-Wave 1. Michele "non se ne dimentica".

### L7 - Q25 theme advanced editing

**Risposta Michele 2026-05-25:** "ok deferirlo anche per questo, ma questi temi vanno
scritti da qualche parte". Conferma: theme advanced editing → Wave 2 / annotazione M7.
Già coperto da sezione M.

---

## M. Annotazioni future (registrate, non bloccanti Wave 1)

| # | Tema | Quando affrontarlo |
| --- | --- | --- |
| M1 | **Multivaluta + crypto** (da Q3) | Produzione fase 2, non fase 1. Da progettare quando piattaforma andrà online con crypto. |
| M2 | **Replay retention policy + routine storicizzazione** (da Q10) | Prima di produzione, come parametro di sistema configurabile. Allineato con `docs/ACTIVE_OPEN_LOOPS.md` P1 esistente. |
| M3 | **Progetto codifica errori parallelo** (da Q22) | Quando partirà, aggiornare playbook con il nuovo contratto error mapping. Già tracciato in `docs/PLATFORM_ERROR_CODE_REGISTRY_PLAN_2026-05-24.md`. |
| M4 | **Provably fair RNG con client seed** (da Q24) | Futuro probabile non certo. Da progettare se requisito di certificazione lo richiederà. |
| M5 | **Playbook regola: domande "come Mines/HI-LO" non vanno poste** (da Q5, Q12, Q14, L3) | Riflesso in feedback memory. Default = pattern reference, domanda solo se divergenza. |
| M6 | **Animazione COINS - mini-progetto polish** (da L6) | Valutare post-Wave 1, dopo aver visto COINS girare. Animazione base Wave 1 segue Phase 3C playbook. Michele "non se ne dimentica". |
| M7 | **Theme advanced editing COINS** (da L7) | Wave 2 post-lancio Wave 1. Wave 1 ha theme base (palette + asset upload) sufficiente per personalizzare. |

---

## K. Prossimi step (dopo risposte Michele)

1. **Aggiornare questo documento** con le risposte definitive per ogni Q.
2. **Sistemare il documento Gemini** `games/coins/COINS - analisi gemini funzionale_v01.md`:
   integrare le decisioni product nelle sezioni mancanti (state machine, idempotency,
   asset contract, failure UX, ecc.) o creare un documento SPEC dedicato in
   `docs/games/coins/SPEC.md` seguendo il pattern HI-LO/BOXE.
3. **Riscrivere la skill Gemini** (richiesta esplicita Michele 2026-05-25 sera): la prossima
   volta che Michele darà in pasto un video di un nuovo gioco, la skill dovrà includere
   nell'analisi tutti gli 11 blocchi della Fase 0 playbook + 12-surface check + Rule 22/24/25.
   Output atteso: analisi funzionale + lista di domande product mirate (formato Q1..QN con
   risposta preferita), non solo l'analisi funzionale base.
4. **Solo dopo** entrare in Fase 1 (Architecture Mapping COINS) seguendo il playbook
   `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md`.

---

## N. Prompt Codex - Prerequisiti platform prima di COINS

I due WP sotto NON sono COINS-specific. Sono platform debt da chiudere prima di
aggiungere il quarto gioco. Decisione Michele 2026-05-25: "architettura pulita,
nessun debito".

### N1 - WP-FINANCE-REPLAY-REGISTRY-RETENTION (chiude debito Rule 18 playbook + finance contract)

**Aggiornato 2026-05-25 sera:** il prompt COINS-specific iniziale
`docs/games/coins/PROMPT_CODEX_WP_FINANCE_REPLAY_REGISTRY_2026-05-25.md` è stato
**superseded** dal WP platform più ampio analizzato in
`docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25.md`
con CTO review in
`docs/PLATFORM_FINANCIAL_TRACEABILITY_PRE_IMPLEMENTATION_ANALYSIS_2026-05-25_CTOREVIEW.md`.

Il WP platform copre tutto il subset COINS + settlement taxonomy + forward
metadata + Mines admin replay parity + BOXE wallet bug + backend
auto-settlement registry + retention doc + reconciliation report.

**Usa il WP platform, non il prompt COINS subset.**

### N2 - WP-EMBED-MODE-PARITY-BOXE-HILO (chiude debito autonomia gioco in iframe)

Vedi prompt completo in: `docs/games/coins/PROMPT_CODEX_WP_EMBED_MODE_PARITY_2026-05-25.md`

---

## Riferimenti

- `games/coins/COINS - analisi gemini funzionale_v01.md` — analisi Gemini di partenza
- `docs/NEW_GAME_INTEGRATION_PLAYBOOK.md` — playbook nuovi giochi
- `docs/NEW_GAME_BRIEF_TEMPLATE.md` — template brief product
- `docs/games/hi-lo/HI_LO_OPEN_QUESTIONS_2026-05-22.md` — pattern open-questions HI-LO
- `docs/NEXT_GAME_REPLICATION_BRIEF_FROM_HI_LO_2026-05-23.md` — replication brief HI-LO
